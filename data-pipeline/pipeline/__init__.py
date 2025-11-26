"""Document processing pipeline using neo4j-graphrag-python.

This package provides tools for processing PDF documents into a Neo4j
knowledge graph using SimpleKGPipeline for entity extraction and embeddings.
"""

from pipeline.config import (
    EmbeddingSettings,
    LLMSettings,
    Neo4jSettings,
    PipelineSettings,
    get_settings,
)
from pipeline.logging import configure_logging
from pipeline.models import (
    ALLOWED_ENTITY_LABELS,
    ENTITY_TYPES,
    GRAPH_SCHEMA,
    PATTERNS,
    RELATIONSHIP_TYPES,
    create_graph_schema,
)
from pipeline.prompts import (
    create_extraction_template,
    get_default_template,
)

__all__ = [
    # Configuration
    "EmbeddingSettings",
    "LLMSettings",
    "Neo4jSettings",
    "PipelineSettings",
    "get_settings",
    # Logging
    "configure_logging",
    # Schema (Pydantic-based)
    "ALLOWED_ENTITY_LABELS",
    "ENTITY_TYPES",
    "GRAPH_SCHEMA",
    "PATTERNS",
    "RELATIONSHIP_TYPES",
    "create_graph_schema",
    # Prompts
    "create_extraction_template",
    "get_default_template",
]
