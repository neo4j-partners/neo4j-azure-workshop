#!/usr/bin/env python3
"""
Neo4j Database Backup Script

Backs up the Neo4j database to a JSON file in the financial-data/snapshot folder.
Uses APOC streaming export to retrieve all nodes and relationships.

Usage:
    uv run python scripts/backup_neo4j.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from neo4j import AsyncGraphDatabase
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BackupConfig(BaseSettings):
    """Configuration for Neo4j backup loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    uri: str | None = Field(default=None, validation_alias="NEO4J_URI")
    username: str | None = Field(default=None, validation_alias="NEO4J_USERNAME")
    password: str | None = Field(default=None, validation_alias="NEO4J_PASSWORD")
    vector_index_name: str | None = Field(default=None, validation_alias="NEO4J_VECTOR_INDEX_NAME")

    @property
    def is_configured(self) -> bool:
        return all([self.uri, self.username, self.password])


def get_project_root() -> Path:
    return Path(__file__).parent.parent


def get_snapshot_dir() -> Path:
    return get_project_root() / "financial-data" / "snapshot"


async def get_database_stats(config: BackupConfig) -> dict:
    """Get database statistics including node count, relationship count, and embeddings."""
    driver = AsyncGraphDatabase.driver(config.uri, auth=(config.username, config.password))

    stats = {
        "nodes": 0,
        "relationships": 0,
        "embeddings": 0,
        "vector_index_name": config.vector_index_name,
    }

    try:
        await driver.verify_connectivity()

        async with driver.session() as session:
            result = await session.run("MATCH (n) RETURN count(n) AS count")
            record = await result.single()
            stats["nodes"] = record["count"]

            result = await session.run("MATCH ()-[r]->() RETURN count(r) AS count")
            record = await result.single()
            stats["relationships"] = record["count"]

            if config.vector_index_name:
                try:
                    result = await session.run(
                        "SHOW INDEXES YIELD name, type, labelsOrTypes, properties "
                        "WHERE name = $index_name AND type = 'VECTOR' "
                        "RETURN labelsOrTypes, properties",
                        {"index_name": config.vector_index_name},
                    )
                    record = await result.single()

                    if record:
                        labels = record["labelsOrTypes"]
                        props = record["properties"]
                        if labels and props:
                            label = labels[0]
                            prop = props[0]
                            count_result = await session.run(
                                f"MATCH (n:`{label}`) WHERE n.`{prop}` IS NOT NULL "
                                "RETURN count(n) AS count"
                            )
                            count_record = await count_result.single()
                            stats["embeddings"] = count_record["count"]
                    else:
                        print(f"Warning: Vector index '{config.vector_index_name}' not found")
                except Exception as e:
                    print(f"Warning: Could not get embeddings count: {e}")

        return stats
    finally:
        await driver.close()


async def get_database_schema(config: BackupConfig) -> dict:
    """Export all indexes and constraints from the database."""
    driver = AsyncGraphDatabase.driver(config.uri, auth=(config.username, config.password))

    schema = {"indexes": [], "constraints": []}

    try:
        await driver.verify_connectivity()

        async with driver.session() as session:
            result = await session.run(
                "SHOW INDEXES YIELD name, type, labelsOrTypes, properties, options "
                "WHERE type <> 'LOOKUP' "
                "RETURN name, type, labelsOrTypes, properties, options"
            )
            records = await result.data()

            for record in records:
                schema["indexes"].append({
                    "name": record["name"],
                    "type": record["type"],
                    "labels": record["labelsOrTypes"],
                    "properties": record["properties"],
                    "options": record["options"],
                })

            result = await session.run(
                "SHOW CONSTRAINTS YIELD name, type, labelsOrTypes, properties "
                "RETURN name, type, labelsOrTypes, properties"
            )
            records = await result.data()

            for record in records:
                schema["constraints"].append({
                    "name": record["name"],
                    "type": record["type"],
                    "labels": record["labelsOrTypes"],
                    "properties": record["properties"],
                })

        return schema
    finally:
        await driver.close()


async def backup_database(config: BackupConfig) -> dict:
    """Back up the Neo4j database using APOC streaming export."""
    driver = AsyncGraphDatabase.driver(config.uri, auth=(config.username, config.password))

    try:
        await driver.verify_connectivity()
        print(f"Connected to Neo4j at {config.uri}")

        async with driver.session() as session:
            try:
                result = await session.run("RETURN apoc.version() AS version")
                record = await result.single()
                print(f"APOC version: {record['version']}")
            except Exception:
                print("Warning: APOC not available, using Cypher-based export")
                return await backup_via_cypher(session)

            print("Starting APOC streaming export...")
            result = await session.run(
                "CALL apoc.export.json.all(null, {useTypes: true, stream: true}) "
                "YIELD file, nodes, relationships, properties, data "
                "RETURN nodes, relationships, properties, data"
            )
            record = await result.single()

            return {
                "nodes": record["nodes"],
                "relationships": record["relationships"],
                "properties": record["properties"],
                "data": record["data"],
            }
    finally:
        await driver.close()


async def backup_via_cypher(session) -> dict:
    """Fallback backup method using plain Cypher queries."""
    print("Exporting nodes...")
    nodes_result = await session.run(
        "MATCH (n) "
        "RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS properties"
    )
    nodes = await nodes_result.data()

    print("Exporting relationships...")
    rels_result = await session.run(
        "MATCH (a)-[r]->(b) "
        "RETURN elementId(r) AS id, type(r) AS type, "
        "elementId(a) AS startId, elementId(b) AS endId, "
        "properties(r) AS properties"
    )
    relationships = await rels_result.data()

    backup_data = {"nodes": nodes, "relationships": relationships}

    return {
        "nodes": len(nodes),
        "relationships": len(relationships),
        "properties": sum(len(n.get("properties", {})) for n in nodes),
        "data": json.dumps(backup_data, indent=2, default=str),
    }


def write_checksum_file(checksum_path: Path, stats: dict, schema: dict) -> None:
    """Write database statistics and schema to a checksum file."""
    checksum_data = {
        "timestamp": datetime.now().isoformat(),
        "nodes": stats["nodes"],
        "relationships": stats["relationships"],
        "embeddings": stats["embeddings"],
        "vector_index_name": stats["vector_index_name"],
        "schema": schema,
    }
    with open(checksum_path, "w", encoding="utf-8") as f:
        json.dump(checksum_data, f, indent=2)


async def main() -> int:
    """Main entry point for the backup script."""
    env_path = get_project_root() / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded environment from {env_path}")
    else:
        print(f"Warning: {env_path} not found")

    config = BackupConfig()
    if not config.is_configured:
        print("Error: Neo4j configuration incomplete.")
        print("Required: NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD")
        return 1

    snapshot_dir = get_snapshot_dir()
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    backup_file = snapshot_dir / "financial_backup.json"
    checksum_file = snapshot_dir / "financial_backup.checksum.json"

    print("=== Neo4j Database Backup ===")
    print(f"Target: {backup_file}")
    print()

    try:
        print("Getting database statistics...")
        stats = await get_database_stats(config)
        print(f"  Nodes: {stats['nodes']}")
        print(f"  Relationships: {stats['relationships']}")
        if config.vector_index_name:
            print(f"  Embeddings ({config.vector_index_name}): {stats['embeddings']}")
        print()

        print("Exporting schema...")
        schema = await get_database_schema(config)
        print(f"  Indexes: {len(schema['indexes'])}")
        print(f"  Constraints: {len(schema['constraints'])}")
        print()

        result = await backup_database(config)

        with open(backup_file, "w", encoding="utf-8") as f:
            f.write(result["data"])

        write_checksum_file(checksum_file, stats, schema)

        print()
        print("=== Backup Complete ===")
        print(f"Nodes: {result['nodes']}")
        print(f"Relationships: {result['relationships']}")
        print(f"Properties: {result['properties']}")
        print(f"Indexes: {len(schema['indexes'])}")
        print(f"Constraints: {len(schema['constraints'])}")
        print(f"Backup saved to: {backup_file}")
        print(f"Checksum saved to: {checksum_file}")
        return 0

    except Exception as e:
        print(f"Error: Backup failed - {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
