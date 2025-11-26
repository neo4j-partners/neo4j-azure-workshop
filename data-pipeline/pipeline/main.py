"""Main entry point for the document processing pipeline.

Uses neo4j-graphrag-python's SimpleKGPipeline to process PDF documents,
extract entities and relationships, and store them in Neo4j.

Run from the data-pipeline directory:
    uv run python -m pipeline.main
    uv run python -m pipeline.main --limit 3
    uv run python -m pipeline.main --file X.pdf
    uv run python -m pipeline.main --strict  # Fail on first error
"""

import argparse
import asyncio
import sys
from pathlib import Path

import nest_asyncio
import structlog
from neo4j import Driver
from neo4j.exceptions import AuthError, ServiceUnavailable
from neo4j_graphrag.embeddings import AzureOpenAIEmbeddings
from neo4j_graphrag.exceptions import (
    LLMGenerationError,
    Neo4jInsertionError,
    SchemaValidationError,
)
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.indexes import create_vector_index
from neo4j_graphrag.llm import AzureOpenAILLM
from pydantic import ValidationError

from pipeline.azure import create_embedder, create_llm, create_neo4j_driver
from pipeline.config import PipelineSettings, get_settings
from pipeline.logging import configure_logging
from pipeline.models import GRAPH_SCHEMA
from pipeline.prompts import get_default_template

# Enable nested async for environments that already have an event loop
nest_asyncio.apply()

# Configure structured logging
configure_logging()

logger = structlog.get_logger(__name__)


class PipelineError(Exception):
    """Base exception for pipeline errors."""

    pass


class ConnectionError(PipelineError):
    """Raised when Neo4j connection fails."""

    pass


class ConfigurationError(PipelineError):
    """Raised when configuration is invalid."""

    pass


def validate_neo4j_connection(driver: Driver, settings: PipelineSettings) -> None:
    """Validate Neo4j connection before processing.

    Args:
        driver: Neo4j driver instance.
        settings: Pipeline settings.

    Raises:
        ConnectionError: If connection fails.
    """
    try:
        driver.verify_connectivity()
        logger.info(
            "neo4j_connected",
            uri=settings.neo4j.uri,
            database=settings.neo4j.database,
        )
    except AuthError as e:
        logger.error(
            "neo4j_auth_failed",
            uri=settings.neo4j.uri,
            error=str(e),
        )
        raise ConnectionError(f"Neo4j authentication failed: {e}") from e
    except ServiceUnavailable as e:
        logger.error(
            "neo4j_unavailable",
            uri=settings.neo4j.uri,
            error=str(e),
        )
        raise ConnectionError(f"Neo4j service unavailable: {e}") from e


def ensure_vector_index(driver: Driver, settings: PipelineSettings) -> None:
    """Create the vector index for chunk embeddings if it doesn't exist.

    Uses neo4j-graphrag-python's create_vector_index utility.

    Args:
        driver: Neo4j driver instance.
        settings: Pipeline settings containing index configuration.
    """
    try:
        create_vector_index(
            driver,
            name=settings.neo4j.vector_index_name,
            label="Chunk",
            embedding_property="embedding",
            dimensions=settings.embedding.dimensions,
            similarity_fn="cosine",
        )
        logger.info(
            "vector_index_created",
            name=settings.neo4j.vector_index_name,
            dimensions=settings.embedding.dimensions,
        )
    except Exception as e:
        # Index may already exist - this is expected
        if "already exists" in str(e).lower():
            logger.debug("vector_index_exists", name=settings.neo4j.vector_index_name)
        else:
            logger.warning("vector_index_error", error=str(e))


def create_pipeline(
    driver: Driver,
    llm: AzureOpenAILLM,
    embedder: AzureOpenAIEmbeddings,
    strict_mode: bool = False,
) -> SimpleKGPipeline:
    """Create the SimpleKGPipeline with all components.

    Uses the pre-validated GRAPH_SCHEMA (Pydantic-based) for type-safe
    entity and relationship extraction.

    Args:
        driver: Neo4j driver instance.
        llm: Azure OpenAI LLM for entity extraction.
        embedder: Azure OpenAI embedder for chunk embeddings.
        strict_mode: If True, raise on first error. If False, skip failed chunks.

    Returns:
        Configured SimpleKGPipeline instance.
    """
    prompt_template = get_default_template()

    return SimpleKGPipeline(
        driver=driver,
        llm=llm,
        embedder=embedder,
        schema=GRAPH_SCHEMA,
        prompt_template=prompt_template,
        on_error="RAISE" if strict_mode else "IGNORE",
        perform_entity_resolution=True,
    )


async def process_file(
    pipeline: SimpleKGPipeline,
    file_path: Path,
    strict_mode: bool = False,
) -> bool:
    """Process a single PDF file through the pipeline.

    Args:
        pipeline: The SimpleKGPipeline instance.
        file_path: Path to the PDF file.
        strict_mode: If True, re-raise exceptions after logging.

    Returns:
        True if successful, False otherwise.
    """
    logger.info("processing_file", file=file_path.name, size_kb=file_path.stat().st_size // 1024)

    try:
        result = await pipeline.run_async(file_path=str(file_path))
        logger.info(
            "file_processed",
            file=file_path.name,
            result_type=type(result).__name__,
        )
        return True

    except LLMGenerationError as e:
        logger.error(
            "llm_extraction_failed",
            file=file_path.name,
            error=str(e),
            error_type="LLMGenerationError",
        )
        if strict_mode:
            raise
        return False

    except Neo4jInsertionError as e:
        logger.error(
            "neo4j_insertion_failed",
            file=file_path.name,
            error=str(e),
            error_type="Neo4jInsertionError",
        )
        if strict_mode:
            raise
        return False

    except SchemaValidationError as e:
        logger.error(
            "schema_validation_failed",
            file=file_path.name,
            error=str(e),
            error_type="SchemaValidationError",
        )
        if strict_mode:
            raise
        return False

    except Exception as e:
        logger.error(
            "file_failed",
            file=file_path.name,
            error=str(e),
            error_type=type(e).__name__,
        )
        if strict_mode:
            raise
        return False


async def run_pipeline(
    pdf_files: list[Path],
    settings: PipelineSettings,
    strict_mode: bool = False,
) -> tuple[int, int]:
    """Run the pipeline on all PDF files.

    Args:
        pdf_files: List of PDF file paths to process.
        settings: Pipeline settings.
        strict_mode: If True, stop on first error.

    Returns:
        Tuple of (processed_count, failed_count).

    Raises:
        ConnectionError: If Neo4j connection fails.
        PipelineError: If strict_mode and a file fails.
    """
    driver = create_neo4j_driver(settings)

    try:
        # Validate connection before processing
        validate_neo4j_connection(driver, settings)

        llm = create_llm(settings)
        embedder = create_embedder(settings)

        # Ensure vector index exists before processing
        ensure_vector_index(driver, settings)

        pipeline = create_pipeline(driver, llm, embedder, strict_mode)
        logger.info(
            "pipeline_initialized",
            strict_mode=strict_mode,
            schema_nodes=len(GRAPH_SCHEMA.node_types),
            schema_relationships=len(GRAPH_SCHEMA.relationship_types),
        )

        processed = 0
        failed = 0

        for i, pdf_file in enumerate(pdf_files, 1):
            logger.info("processing_progress", current=i, total=len(pdf_files))
            success = await process_file(pipeline, pdf_file, strict_mode)
            if success:
                processed += 1
            else:
                failed += 1
                if strict_mode:
                    logger.warning("stopping_due_to_strict_mode")
                    break

        return processed, failed

    finally:
        driver.close()
        logger.info("neo4j_connection_closed")


def main() -> int:
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(
        description="Process PDF documents into a Neo4j knowledge graph",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python -m pipeline.main                    # Process all PDFs
  uv run python -m pipeline.main --limit 3          # Process first 3 PDFs
  uv run python -m pipeline.main --file X.pdf       # Process specific file
  uv run python -m pipeline.main --strict           # Stop on first error
        """,
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of files to process",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Process a specific file by name",
    )
    parser.add_argument(
        "--directory",
        type=str,
        default=None,
        help="Override PDF directory path",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Stop processing on first error (default: skip failed files)",
    )

    args = parser.parse_args()

    # Load and validate settings
    try:
        settings = get_settings()
    except ValidationError as e:
        logger.error("configuration_invalid", error=str(e))
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1

    pdf_dir = Path(args.directory) if args.directory else settings.pdf_directory

    logger.info(
        "pipeline_starting",
        pdf_directory=str(pdf_dir),
        llm_model=settings.llm.deployment_name,
        embedding_model=settings.embedding.deployment_name,
        strict_mode=args.strict,
    )

    # Verify directory exists
    if not pdf_dir.exists():
        logger.error("directory_not_found", path=str(pdf_dir))
        print(f"Directory not found: {pdf_dir}", file=sys.stderr)
        return 1

    # Get PDF files
    if args.file:
        pdf_files = [pdf_dir / args.file]
        if not pdf_files[0].exists():
            logger.error("file_not_found", file=args.file)
            print(f"File not found: {args.file}", file=sys.stderr)
            return 1
    else:
        pdf_files = sorted(pdf_dir.glob("*.pdf"))

    if not pdf_files:
        logger.warning("no_pdf_files_found", directory=str(pdf_dir))
        print(f"No PDF files found in: {pdf_dir}", file=sys.stderr)
        return 0

    # Apply limit
    if args.limit:
        pdf_files = pdf_files[: args.limit]

    logger.info("files_to_process", count=len(pdf_files))

    # Run the async pipeline
    try:
        processed, failed = asyncio.run(
            run_pipeline(pdf_files, settings, strict_mode=args.strict)
        )
    except ConnectionError as e:
        logger.error("pipeline_connection_error", error=str(e))
        print(f"Connection error: {e}", file=sys.stderr)
        return 1
    except PipelineError as e:
        logger.error("pipeline_error", error=str(e))
        print(f"Pipeline error: {e}", file=sys.stderr)
        return 1

    # Summary
    logger.info(
        "pipeline_complete",
        processed=processed,
        failed=failed,
        success_rate=f"{processed / len(pdf_files) * 100:.1f}%" if pdf_files else "N/A",
    )

    if failed > 0:
        print(f"Completed with {failed} failures. Check logs for details.", file=sys.stderr)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
