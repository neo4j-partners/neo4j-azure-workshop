"""
Neo4j client module for graph database connectivity.

This module provides configuration and connection management for Neo4j,
including schema retrieval for validation and tool usage.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from neo4j import AsyncGraphDatabase, AsyncDriver
from neo4j.exceptions import ServiceUnavailable, AuthError
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from logging_config import configure_logging

logger = configure_logging(os.getenv("APP_LOG_FILE", ""))


class Neo4jConfig(BaseSettings):
    """
    Neo4j configuration loaded from environment variables.

    Attributes:
        uri: Neo4j connection URI (NEO4J_URI)
        username: Neo4j username (NEO4J_USERNAME)
        password: Neo4j password (NEO4J_PASSWORD)
    """

    model_config = SettingsConfigDict(
        env_prefix="",
        extra="ignore",
    )

    uri: str | None = Field(
        default=None,
        validation_alias="NEO4J_URI",
    )
    username: str | None = Field(
        default=None,
        validation_alias="NEO4J_USERNAME",
    )
    password: SecretStr | None = Field(
        default=None,
        description="Neo4j password",
    )

    @property
    def is_configured(self) -> bool:
        """Check if all required Neo4j settings are provided."""
        return all([self.uri, self.username, self.password])


@dataclass
class GraphSchema:
    """
    Represents the schema of a Neo4j graph database.

    Attributes:
        node_labels: List of node labels in the database
        relationship_types: List of relationship types in the database
        node_properties: Dictionary mapping node labels to their properties
        relationship_properties: Dictionary mapping relationship types to their properties
    """

    node_labels: list[str] = field(default_factory=list)
    relationship_types: list[str] = field(default_factory=list)
    node_properties: dict[str, list[str]] = field(default_factory=dict)
    relationship_properties: dict[str, list[str]] = field(default_factory=dict)

    def summary(self) -> str:
        """Return a human-readable summary of the schema."""
        return (
            f"Schema: {len(self.node_labels)} node labels, "
            f"{len(self.relationship_types)} relationship types"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert schema to dictionary representation."""
        return {
            "node_labels": self.node_labels,
            "relationship_types": self.relationship_types,
            "node_properties": self.node_properties,
            "relationship_properties": self.relationship_properties,
        }


class Neo4jClient:
    """
    Async Neo4j client for managing database connections and queries.

    Use as an async context manager to ensure proper resource cleanup:

        async with Neo4jClient(config) as client:
            schema = await client.get_schema()
    """

    def __init__(self, config: Neo4jConfig) -> None:
        """
        Initialize the Neo4j client.

        Args:
            config: Neo4j configuration with connection details.

        Raises:
            ValueError: If required configuration is missing.
        """
        if not config.is_configured:
            raise ValueError(
                "Neo4j configuration incomplete. "
                "Required: NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD"
            )
        self._config = config
        self._driver: AsyncDriver | None = None

    async def __aenter__(self) -> Neo4jClient:
        """Enter async context and establish connection."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context and close connection."""
        await self.close()

    async def connect(self) -> None:
        """
        Establish connection to Neo4j database.

        Raises:
            ConnectionError: If connection fails.
        """
        try:
            self._driver = AsyncGraphDatabase.driver(
                self._config.uri,
                auth=(self._config.username, self._config.password),
            )
            # Verify connectivity
            await self._driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {self._config.uri}")
        except AuthError as e:
            logger.error(f"Neo4j authentication failed: {e}")
            raise ConnectionError(f"Neo4j authentication failed: {e}") from e
        except ServiceUnavailable as e:
            logger.error(f"Neo4j service unavailable: {e}")
            raise ConnectionError(f"Neo4j service unavailable: {e}") from e
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise ConnectionError(f"Failed to connect to Neo4j: {e}") from e

    async def close(self) -> None:
        """Close the Neo4j driver connection."""
        if self._driver:
            await self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")

    @property
    def driver(self) -> AsyncDriver:
        """Get the Neo4j driver, raising if not connected."""
        if not self._driver:
            raise RuntimeError("Neo4j client not connected. Use as async context manager.")
        return self._driver

    async def get_schema(self) -> GraphSchema:
        """
        Retrieve the graph database schema.

        Returns:
            GraphSchema containing node labels, relationship types, and properties.

        Raises:
            RuntimeError: If not connected to the database.
        """
        schema = GraphSchema()

        async with self.driver.session() as session:
            # Get node labels
            result = await session.run("CALL db.labels()")
            records = await result.data()
            schema.node_labels = [record["label"] for record in records]

            # Get relationship types
            result = await session.run("CALL db.relationshipTypes()")
            records = await result.data()
            schema.relationship_types = [record["relationshipType"] for record in records]

            # Get node properties per label
            for label in schema.node_labels:
                result = await session.run(
                    f"MATCH (n:`{label}`) "
                    "WITH n LIMIT 100 "
                    "UNWIND keys(n) AS key "
                    "RETURN DISTINCT key"
                )
                records = await result.data()
                schema.node_properties[label] = [record["key"] for record in records]

            # Get relationship properties per type
            for rel_type in schema.relationship_types:
                result = await session.run(
                    f"MATCH ()-[r:`{rel_type}`]->() "
                    "WITH r LIMIT 100 "
                    "UNWIND keys(r) AS key "
                    "RETURN DISTINCT key"
                )
                records = await result.data()
                schema.relationship_properties[rel_type] = [record["key"] for record in records]

        logger.info(f"Retrieved schema: {schema.summary()}")
        return schema

    async def execute_query(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """
        Execute a Cypher query and return results.

        Args:
            query: Cypher query string.
            parameters: Optional query parameters.

        Returns:
            List of result records as dictionaries.
        """
        async with self.driver.session() as session:
            result = await session.run(query, parameters or {})
            return await result.data()
