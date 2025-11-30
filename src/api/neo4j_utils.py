"""
Neo4j utility functions for entity and relationship queries.

These functions provide high-level graph operations used by the API routes.
"""

from typing import Any

from neo4j_client import Neo4jClient


async def list_entities_by_type(
    client: Neo4jClient,
    entity_type: str,
    limit: int = 20,
) -> list[dict[str, str]]:
    """List entities of a specific type.

    Args:
        client: Connected Neo4jClient instance.
        entity_type: The entity label (must be validated by caller).
        limit: Maximum number of entities to return.

    Returns:
        List of entities with id and name.
    """
    # Use coalesce to fallback to elementId if e.id is not set
    # Filter NULL names before sorting per Cypher best practices
    query = f"""
    MATCH (e:{entity_type})
    WHERE e.name IS NOT NULL
    RETURN coalesce(e.id, elementId(e)) AS id, e.name AS name
    ORDER BY e.name
    LIMIT $limit
    """

    async with client.driver.session() as session:
        result = await session.run(query, {"limit": limit})
        data = await result.data()
        return [
            {"id": str(record["id"]), "name": record["name"]}
            for record in data
        ]


async def get_entity_relationships(
    client: Neo4jClient,
    entity_name: str,
    limit: int = 20,
) -> list[dict[str, str]]:
    """Get relationships for an entity by name.

    Args:
        client: Connected Neo4jClient instance.
        entity_name: The entity name to search for (case-insensitive contains).
        limit: Maximum number of relationships to return.

    Returns:
        List of relationships with source, relationship type, and target.
    """
    # Use modern label expressions (NOT :Label1|Label2) per Cypher best practices
    # Use coalesce for label extraction to handle edge case of no matching labels
    query = """
    MATCH (source)-[r]->(target)
    WHERE source.name IS NOT NULL
      AND target.name IS NOT NULL
      AND toLower(source.name) CONTAINS toLower($entity_name)
      AND NOT source:Document|Chunk
      AND NOT target:Document|Chunk
    RETURN source.name AS source,
           type(r) AS relationship,
           target.name AS target,
           coalesce([label IN labels(source) WHERE NOT label STARTS WITH '__'][0], 'Unknown') AS source_type,
           coalesce([label IN labels(target) WHERE NOT label STARTS WITH '__'][0], 'Unknown') AS target_type
    LIMIT $limit
    """

    async with client.driver.session() as session:
        result = await session.run(
            query,
            {"entity_name": entity_name, "limit": limit},
        )
        data = await result.data()
        return [
            {
                "source": record["source"],
                "source_type": record["source_type"],
                "relationship": record["relationship"],
                "target": record["target"],
                "target_type": record["target_type"],
            }
            for record in data
        ]
