"""Tests for schema definitions in pipeline.models.

Tests the Pydantic-based schema classes from neo4j-graphrag-python.
"""

import pytest
from neo4j_graphrag.experimental.components.schema import (
    GraphSchema,
    NodeType,
    PropertyType,
    RelationshipType,
)

from pipeline.models import (
    ALLOWED_ENTITY_LABELS,
    ENTITY_TYPES,
    GRAPH_SCHEMA,
    PATTERNS,
    RELATIONSHIP_TYPES,
    create_graph_schema,
)


class TestEntityTypes:
    """Tests for entity type definitions."""

    def test_entity_types_count(self):
        """Test that we have the expected number of entity types."""
        assert len(ENTITY_TYPES) == 8

    def test_entity_types_are_pydantic(self):
        """Test that entity types are Pydantic NodeType instances."""
        for entity in ENTITY_TYPES:
            assert isinstance(entity, NodeType)
            assert hasattr(entity, "model_dump")

    def test_entity_types_have_labels(self):
        """Test that all entity types have labels."""
        for entity in ENTITY_TYPES:
            assert entity.label
            assert isinstance(entity.label, str)

    def test_entity_types_have_descriptions(self):
        """Test that all entity types have descriptions."""
        for entity in ENTITY_TYPES:
            assert entity.description
            assert isinstance(entity.description, str)

    def test_entity_types_have_properties(self):
        """Test that all entity types have at least one property."""
        for entity in ENTITY_TYPES:
            assert len(entity.properties) > 0
            for prop in entity.properties:
                assert isinstance(prop, PropertyType)
                assert prop.name == "name"
                assert prop.type == "STRING"
                assert prop.required is True

    def test_entity_type_labels(self):
        """Test that all expected entity labels are present."""
        labels = {entity.label for entity in ENTITY_TYPES}
        expected = {
            "Company",
            "Executive",
            "Product",
            "FinancialMetric",
            "RiskFactor",
            "StockType",
            "Transaction",
            "TimePeriod",
        }
        assert labels == expected


class TestRelationshipTypes:
    """Tests for relationship type definitions."""

    def test_relationship_types_count(self):
        """Test that we have the expected number of relationship types."""
        assert len(RELATIONSHIP_TYPES) == 7

    def test_relationship_types_are_pydantic(self):
        """Test that relationship types are Pydantic RelationshipType instances."""
        for rel in RELATIONSHIP_TYPES:
            assert isinstance(rel, RelationshipType)
            assert hasattr(rel, "model_dump")

    def test_relationship_types_have_labels(self):
        """Test that all relationship types have labels."""
        for rel in RELATIONSHIP_TYPES:
            assert rel.label
            assert isinstance(rel.label, str)

    def test_relationship_types_have_descriptions(self):
        """Test that all relationship types have descriptions."""
        for rel in RELATIONSHIP_TYPES:
            assert rel.description
            assert isinstance(rel.description, str)

    def test_relationship_type_labels(self):
        """Test that all expected relationship labels are present."""
        labels = {rel.label for rel in RELATIONSHIP_TYPES}
        expected = {
            "HAS_METRIC",
            "FACES_RISK",
            "ISSUED_STOCK",
            "MENTIONS",
            "HAS_EXECUTIVE",
            "COMPLETED_TRANSACTION",
            "REPORTED_IN",
        }
        assert labels == expected


class TestPatterns:
    """Tests for relationship pattern definitions."""

    def test_patterns_count(self):
        """Test that we have the expected number of patterns."""
        assert len(PATTERNS) == 7

    def test_patterns_structure(self):
        """Test that patterns are tuples of (source, rel, target)."""
        for pattern in PATTERNS:
            assert isinstance(pattern, tuple)
            assert len(pattern) == 3
            source, rel, target = pattern
            assert isinstance(source, str)
            assert isinstance(rel, str)
            assert isinstance(target, str)

    def test_patterns_reference_valid_entities(self):
        """Test that patterns reference defined entity types."""
        entity_labels = {entity.label for entity in ENTITY_TYPES}
        for source, _, target in PATTERNS:
            assert source in entity_labels, f"Unknown source: {source}"
            assert target in entity_labels, f"Unknown target: {target}"

    def test_patterns_reference_valid_relationships(self):
        """Test that patterns reference defined relationship types."""
        rel_labels = {rel.label for rel in RELATIONSHIP_TYPES}
        for _, rel, _ in PATTERNS:
            assert rel in rel_labels, f"Unknown relationship: {rel}"


class TestGraphSchema:
    """Tests for the complete GraphSchema."""

    def test_graph_schema_is_pydantic(self):
        """Test that GRAPH_SCHEMA is a Pydantic GraphSchema instance."""
        assert isinstance(GRAPH_SCHEMA, GraphSchema)
        assert hasattr(GRAPH_SCHEMA, "model_dump")

    def test_graph_schema_is_frozen(self):
        """Test that GraphSchema is immutable."""
        with pytest.raises(Exception):  # ValidationError or AttributeError
            GRAPH_SCHEMA.node_types = ()

    def test_graph_schema_node_types(self):
        """Test that schema contains all node types."""
        assert len(GRAPH_SCHEMA.node_types) == 8
        for node in GRAPH_SCHEMA.node_types:
            assert isinstance(node, NodeType)

    def test_graph_schema_relationship_types(self):
        """Test that schema contains all relationship types."""
        assert len(GRAPH_SCHEMA.relationship_types) == 7
        for rel in GRAPH_SCHEMA.relationship_types:
            assert isinstance(rel, RelationshipType)

    def test_graph_schema_patterns(self):
        """Test that schema contains all patterns."""
        assert len(GRAPH_SCHEMA.patterns) == 7

    def test_graph_schema_lookup_methods(self):
        """Test schema lookup helper methods."""
        # Node type lookup
        company = GRAPH_SCHEMA.node_type_from_label("Company")
        assert company is not None
        assert company.label == "Company"

        # Relationship type lookup
        has_metric = GRAPH_SCHEMA.relationship_type_from_label("HAS_METRIC")
        assert has_metric is not None
        assert has_metric.label == "HAS_METRIC"

        # Non-existent lookups return None
        assert GRAPH_SCHEMA.node_type_from_label("NonExistent") is None
        assert GRAPH_SCHEMA.relationship_type_from_label("NonExistent") is None

    def test_graph_schema_serialization(self):
        """Test that schema can be serialized to dict/JSON."""
        data = GRAPH_SCHEMA.model_dump()
        assert "node_types" in data
        assert "relationship_types" in data
        assert "patterns" in data
        assert len(data["node_types"]) == 8
        assert len(data["relationship_types"]) == 7


class TestCreateGraphSchema:
    """Tests for the create_graph_schema function."""

    def test_create_graph_schema_returns_valid_schema(self):
        """Test that create_graph_schema returns a valid GraphSchema."""
        schema = create_graph_schema()
        assert isinstance(schema, GraphSchema)
        assert len(schema.node_types) == 8
        assert len(schema.relationship_types) == 7
        assert len(schema.patterns) == 7


class TestAllowedEntityLabels:
    """Tests for the ALLOWED_ENTITY_LABELS export."""

    def test_allowed_labels_matches_entity_types(self):
        """Test that ALLOWED_ENTITY_LABELS matches ENTITY_TYPES labels."""
        entity_labels = {entity.label for entity in ENTITY_TYPES}
        assert ALLOWED_ENTITY_LABELS == entity_labels

    def test_allowed_labels_is_frozenset(self):
        """Test that ALLOWED_ENTITY_LABELS is immutable."""
        assert isinstance(ALLOWED_ENTITY_LABELS, frozenset)
