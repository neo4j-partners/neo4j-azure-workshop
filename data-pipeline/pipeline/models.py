"""Schema definitions for the document processing pipeline.

Uses neo4j-graphrag-python's official Pydantic-based schema classes:
- NodeType: Defines entity types with labels, descriptions, and properties
- RelationshipType: Defines relationship types between entities
- PropertyType: Defines properties on nodes and relationships
- GraphSchema: Immutable container for the complete schema

All classes are Pydantic models with validation, serialization, and type safety.
"""

from neo4j_graphrag.experimental.components.schema import (
    GraphSchema,
    NodeType,
    PropertyType,
    RelationshipType,
    SchemaBuilder,
)

# Entity types for SEC financial filings
# Each NodeType is a Pydantic model with validation
ENTITY_TYPES: tuple[NodeType, ...] = (
    NodeType(
        label="Company",
        description="A publicly traded company filing SEC reports",
        properties=[
            PropertyType(
                name="name",
                type="STRING",
                description="Official company name as it appears in SEC filings",
                required=True,
            ),
        ],
    ),
    NodeType(
        label="Executive",
        description="A company executive or officer mentioned in filings",
        properties=[
            PropertyType(
                name="name",
                type="STRING",
                description="Full name of the executive",
                required=True,
            ),
        ],
    ),
    NodeType(
        label="Product",
        description="A product or service offered by the company",
        properties=[
            PropertyType(
                name="name",
                type="STRING",
                description="Product or service name",
                required=True,
            ),
        ],
    ),
    NodeType(
        label="FinancialMetric",
        description="A financial metric or KPI (revenue, profit, etc.)",
        properties=[
            PropertyType(
                name="name",
                type="STRING",
                description="Name of the financial metric",
                required=True,
            ),
        ],
    ),
    NodeType(
        label="RiskFactor",
        description="A business risk disclosed in SEC filings",
        properties=[
            PropertyType(
                name="name",
                type="STRING",
                description="Description of the risk factor",
                required=True,
            ),
        ],
    ),
    NodeType(
        label="StockType",
        description="A type of stock issued by the company",
        properties=[
            PropertyType(
                name="name",
                type="STRING",
                description="Stock type (common, preferred, etc.)",
                required=True,
            ),
        ],
    ),
    NodeType(
        label="Transaction",
        description="A significant business transaction or deal",
        properties=[
            PropertyType(
                name="name",
                type="STRING",
                description="Transaction description",
                required=True,
            ),
        ],
    ),
    NodeType(
        label="TimePeriod",
        description="A fiscal period (quarter, year) referenced in filings",
        properties=[
            PropertyType(
                name="name",
                type="STRING",
                description="Time period description (e.g., 'Q4 2023', 'FY 2023')",
                required=True,
            ),
        ],
    ),
)

# Relationship types between entities
RELATIONSHIP_TYPES: tuple[RelationshipType, ...] = (
    RelationshipType(
        label="HAS_METRIC",
        description="Company has a financial metric",
    ),
    RelationshipType(
        label="FACES_RISK",
        description="Company faces a risk factor",
    ),
    RelationshipType(
        label="ISSUED_STOCK",
        description="Company issued a type of stock",
    ),
    RelationshipType(
        label="MENTIONS",
        description="Company mentions a product",
    ),
    RelationshipType(
        label="HAS_EXECUTIVE",
        description="Company has an executive",
    ),
    RelationshipType(
        label="COMPLETED_TRANSACTION",
        description="Company completed a transaction",
    ),
    RelationshipType(
        label="REPORTED_IN",
        description="Metric was reported in a time period",
    ),
)

# Valid relationship patterns (source, relationship, target)
PATTERNS: tuple[tuple[str, str, str], ...] = (
    ("Company", "HAS_METRIC", "FinancialMetric"),
    ("Company", "FACES_RISK", "RiskFactor"),
    ("Company", "ISSUED_STOCK", "StockType"),
    ("Company", "MENTIONS", "Product"),
    ("Company", "HAS_EXECUTIVE", "Executive"),
    ("Company", "COMPLETED_TRANSACTION", "Transaction"),
    ("FinancialMetric", "REPORTED_IN", "TimePeriod"),
)


def create_graph_schema() -> GraphSchema:
    """Create the complete GraphSchema for SEC filings.

    Uses SchemaBuilder to create an immutable, validated GraphSchema
    from the entity types, relationship types, and patterns.

    Returns:
        GraphSchema: Validated schema for the knowledge graph.
    """
    return SchemaBuilder.create_schema_model(
        node_types=ENTITY_TYPES,
        relationship_types=RELATIONSHIP_TYPES,
        patterns=PATTERNS,
    )


# Pre-built schema instance for direct use
# This is validated at import time, catching schema errors early
GRAPH_SCHEMA: GraphSchema = create_graph_schema()


def get_entity_labels() -> frozenset[str]:
    """Get all entity labels defined in the schema.

    Returns:
        Frozenset of entity label strings.
    """
    return frozenset(node.label for node in ENTITY_TYPES)


# Export for backwards compatibility with search.py
ALLOWED_ENTITY_LABELS = get_entity_labels()
