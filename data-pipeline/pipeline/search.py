"""Search client using neo4j-graphrag retrievers for vector similarity search.

Uses VectorCypherRetriever from neo4j-graphrag-python for enhanced search
that combines vector similarity with graph traversal.

Run from the data-pipeline directory:
    uv run python -m pipeline.search "What are Apple's risk factors?"
    uv run python -m pipeline.search "revenue growth" --limit 5
    uv run python -m pipeline.search --entities Company
    uv run python -m pipeline.search --relationships "Apple"
"""

import argparse
import sys

import structlog
from neo4j_graphrag.retrievers import VectorCypherRetriever

from pipeline.azure import create_embedder, create_neo4j_driver
from pipeline.config import get_settings
from pipeline.logging import configure_logging
from pipeline.models import ALLOWED_ENTITY_LABELS

# Configure structured logging
configure_logging()

logger = structlog.get_logger(__name__)

# Retrieval query for VectorCypherRetriever
# Enriches chunk results with document path and related entities
CHUNK_RETRIEVAL_QUERY = """
MATCH (chunk)-[:FROM_DOCUMENT]->(doc:Document)
OPTIONAL MATCH (entity)-[:FROM_CHUNK]->(chunk)
WHERE entity IS NULL OR (NOT entity:Document AND NOT entity:Chunk)
WITH chunk, doc, score,
     collect(DISTINCT {type: labels(entity)[0], name: entity.name}) AS entities
WHERE score >= $threshold
RETURN chunk.text AS text,
       doc.path AS document,
       score,
       [e IN entities WHERE e.name IS NOT NULL] AS related_entities
ORDER BY score DESC
"""


def search_chunks(
    query: str,
    limit: int = 5,
    threshold: float = 0.7,
) -> None:
    """Search for chunks similar to the query using VectorCypherRetriever.

    Uses neo4j-graphrag's VectorCypherRetriever to combine vector similarity
    search with graph traversal for enriched results including related entities.

    Args:
        query: Search query text.
        limit: Maximum number of results to return.
        threshold: Minimum similarity score (0-1).
    """
    settings = get_settings()

    logger.info("search_starting", query=query, limit=limit, threshold=threshold)

    driver = create_neo4j_driver(settings)
    embedder = create_embedder(settings)

    try:
        # Create VectorCypherRetriever for enhanced search
        retriever = VectorCypherRetriever(
            driver=driver,
            index_name=settings.neo4j.vector_index_name,
            retrieval_query=CHUNK_RETRIEVAL_QUERY,
            embedder=embedder,
            neo4j_database=settings.neo4j.database,
        )

        logger.info("retriever_initialized", index=settings.neo4j.vector_index_name)

        # Execute search with threshold parameter
        result = retriever.search(
            query_text=query,
            top_k=limit,
            query_params={"threshold": threshold},
        )

        logger.info("search_complete", result_count=len(result.items))

        # Display results
        if not result.items:
            print("\nNo matching chunks found.")
            print(f"Try lowering the threshold (current: {threshold})")
            return

        print(f"\n{'='*80}")
        print(f"Found {len(result.items)} matching chunks for: \"{query}\"")
        print(f"{'='*80}\n")

        for i, item in enumerate(result.items, 1):
            metadata = item.metadata or {}
            score = float(metadata.get("score", 0))
            document = str(metadata.get("document") or "Unknown")
            text = str(metadata.get("text") or item.content or "")
            entities = metadata.get("related_entities", [])

            # Truncate content for display
            display_text = text[:500] + "..." if len(text) > 500 else text

            print(f"[{i}] Score: {score:.4f} | Document: {document}")
            print(f"    {'-'*70}")
            print(f"    {display_text}")

            # Show related entities if found
            if entities:
                entity_strs = [f"{e['type']}: {e['name']}" for e in entities if e.get("name")]
                if entity_strs:
                    print(f"\n    Related: {', '.join(entity_strs[:5])}")
                    if len(entity_strs) > 5:
                        print(f"             ...and {len(entity_strs) - 5} more")
            print()

    finally:
        driver.close()


def list_entities(entity_type: str, limit: int = 20) -> None:
    """List entities of a specific type.

    Args:
        entity_type: The entity type (Company, Executive, Product, etc.).
        limit: Maximum number of entities to return.
    """
    if entity_type not in ALLOWED_ENTITY_LABELS:
        print(f"\nError: Invalid entity type: {entity_type}")
        print(f"Available entity types: {', '.join(sorted(ALLOWED_ENTITY_LABELS))}")
        return

    settings = get_settings()
    logger.info("listing_entities", entity_type=entity_type, limit=limit)

    driver = create_neo4j_driver(settings)

    try:
        # Label is validated above, safe to use in f-string
        query = f"""
        MATCH (e:{entity_type})
        RETURN e.name AS name
        ORDER BY e.name
        LIMIT $limit
        """

        with driver.session(database=settings.neo4j.database) as session:
            result = session.run(query, {"limit": limit})
            results = list(result)

        if not results:
            print(f"\nNo {entity_type} entities found.")
            return

        print(f"\n{'='*80}")
        print(f"Found {len(results)} {entity_type} entities")
        print(f"{'='*80}\n")

        for i, record in enumerate(results, 1):
            print(f"[{i}] {record['name']}")

    finally:
        driver.close()


def get_relationships(entity_name: str, limit: int = 20) -> None:
    """Get relationships for an entity.

    Args:
        entity_name: The entity name to search for.
        limit: Maximum number of relationships to return.
    """
    settings = get_settings()
    logger.info("getting_relationships", entity_name=entity_name, limit=limit)

    driver = create_neo4j_driver(settings)

    try:
        query = """
        MATCH (source)-[r]->(target)
        WHERE source.name IS NOT NULL
          AND target.name IS NOT NULL
          AND toLower(source.name) CONTAINS toLower($entity_name)
          AND NOT source:Document
          AND NOT source:Chunk
          AND NOT target:Document
          AND NOT target:Chunk
        RETURN source.name AS source,
               type(r) AS relationship,
               target.name AS target,
               labels(source)[0] AS source_type,
               labels(target)[0] AS target_type
        LIMIT $limit
        """

        with driver.session(database=settings.neo4j.database) as session:
            result = session.run(
                query,
                {"entity_name": entity_name, "limit": limit},
            )
            results = list(result)

        if not results:
            print(f"\nNo relationships found for entity containing: \"{entity_name}\"")
            return

        print(f"\n{'='*80}")
        print(f"Found {len(results)} relationships for: \"{entity_name}\"")
        print(f"{'='*80}\n")

        for i, record in enumerate(results, 1):
            source = record["source"]
            source_type = record["source_type"]
            relationship = record["relationship"]
            target = record["target"]
            target_type = record["target_type"]

            print(f"[{i}] ({source_type}) {source}")
            print(f"    --[{relationship}]-->")
            print(f"    ({target_type}) {target}")
            print()

    finally:
        driver.close()


def main() -> int:
    """Main entry point for the search client."""
    parser = argparse.ArgumentParser(
        description="Search for similar chunks, list entities, or explore relationships",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Vector similarity search (uses VectorCypherRetriever)
  uv run python -m pipeline.search "What are the risk factors?"
  uv run python -m pipeline.search "revenue growth" --limit 10
  uv run python -m pipeline.search "executive officers" --threshold 0.5

  # List entities by type
  uv run python -m pipeline.search --entities Company
  uv run python -m pipeline.search --entities Executive --limit 10

  # Get entity relationships
  uv run python -m pipeline.search --relationships "Apple"
  uv run python -m pipeline.search --relationships "Tim Cook" --limit 5
        """,
    )
    parser.add_argument(
        "query",
        type=str,
        nargs="?",
        help="Search query text (for vector similarity search)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of results (default: 5)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        help="Minimum similarity score 0-1 (default: 0.7, for vector search only)",
    )
    parser.add_argument(
        "--entities",
        type=str,
        metavar="TYPE",
        help="List entities of a type (Company, Executive, Product, etc.)",
    )
    parser.add_argument(
        "--relationships",
        type=str,
        metavar="NAME",
        help="Get relationships for an entity by name",
    )

    args = parser.parse_args()

    try:
        # Handle entity listing
        if args.entities:
            list_entities(entity_type=args.entities, limit=args.limit)
            return 0

        # Handle relationship query
        if args.relationships:
            get_relationships(entity_name=args.relationships, limit=args.limit)
            return 0

        # Handle vector similarity search (requires query)
        if not args.query:
            parser.error("query is required for vector search (or use --entities/--relationships)")

        search_chunks(
            query=args.query,
            limit=args.limit,
            threshold=args.threshold,
        )
        return 0
    except Exception as e:
        logger.error("search_failed", error=str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
