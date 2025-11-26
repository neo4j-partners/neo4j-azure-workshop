#!/usr/bin/env python3
"""
Neo4j Database Restore Script

Restores the Neo4j database from a JSON backup file in the financial-data/snapshot folder.

Usage:
    uv run python scripts/restore_neo4j.py
    uv run python scripts/restore_neo4j.py --force  # Skip confirmation
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from neo4j import AsyncGraphDatabase
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RestoreConfig(BaseSettings):
    """Configuration for Neo4j restore loaded from environment variables."""

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


async def get_database_stats(config: RestoreConfig) -> dict:
    """Get database statistics for verification."""
    driver = AsyncGraphDatabase.driver(config.uri, auth=(config.username, config.password))

    stats = {"nodes": 0, "relationships": 0, "embeddings": 0}

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
                            count_result = await session.run(
                                f"MATCH (n:`{labels[0]}`) WHERE n.`{props[0]}` IS NOT NULL "
                                "RETURN count(n) AS count"
                            )
                            count_record = await count_result.single()
                            stats["embeddings"] = count_record["count"]
                except Exception:
                    pass

        return stats
    finally:
        await driver.close()


async def drop_all_schema(config: RestoreConfig) -> dict:
    """Drop all indexes and constraints from the database."""
    driver = AsyncGraphDatabase.driver(config.uri, auth=(config.username, config.password))
    dropped = {"indexes": 0, "constraints": 0}

    try:
        await driver.verify_connectivity()

        async with driver.session() as session:
            result = await session.run("SHOW CONSTRAINTS YIELD name RETURN name")
            records = await result.data()
            for record in records:
                await session.run(f"DROP CONSTRAINT `{record['name']}` IF EXISTS")
                dropped["constraints"] += 1

            result = await session.run(
                "SHOW INDEXES YIELD name, type WHERE type <> 'LOOKUP' RETURN name"
            )
            records = await result.data()
            for record in records:
                await session.run(f"DROP INDEX `{record['name']}` IF EXISTS")
                dropped["indexes"] += 1

        return dropped
    finally:
        await driver.close()


async def recreate_schema(config: RestoreConfig, schema: dict) -> dict:
    """Recreate indexes and constraints from schema definition."""
    driver = AsyncGraphDatabase.driver(config.uri, auth=(config.username, config.password))
    created = {"indexes": 0, "constraints": 0, "errors": []}

    try:
        await driver.verify_connectivity()

        async with driver.session() as session:
            for constraint in schema.get("constraints", []):
                try:
                    cypher = build_constraint_cypher(constraint)
                    if cypher:
                        await session.run(cypher)
                        created["constraints"] += 1
                        print(f"  Created constraint: {constraint['name']}")
                except Exception as e:
                    created["errors"].append(f"Constraint {constraint['name']}: {e}")

            for index in schema.get("indexes", []):
                try:
                    cypher = build_index_cypher(index)
                    if cypher:
                        await session.run(cypher)
                        created["indexes"] += 1
                        print(f"  Created index: {index['name']}")
                except Exception as e:
                    created["errors"].append(f"Index {index['name']}: {e}")

        return created
    finally:
        await driver.close()


def build_constraint_cypher(constraint: dict) -> str | None:
    """Build Cypher statement to create a constraint."""
    name = constraint["name"]
    constraint_type = constraint["type"]
    labels = constraint.get("labels", [])
    properties = constraint.get("properties", [])

    if not labels or not properties:
        return None

    label = labels[0]
    prop_list = ", ".join(f"n.`{p}`" for p in properties)

    if constraint_type == "UNIQUENESS":
        return f"CREATE CONSTRAINT `{name}` IF NOT EXISTS FOR (n:`{label}`) REQUIRE ({prop_list}) IS UNIQUE"
    elif constraint_type == "NODE_PROPERTY_EXISTENCE":
        return f"CREATE CONSTRAINT `{name}` IF NOT EXISTS FOR (n:`{label}`) REQUIRE n.`{properties[0]}` IS NOT NULL"
    elif constraint_type == "NODE_KEY":
        return f"CREATE CONSTRAINT `{name}` IF NOT EXISTS FOR (n:`{label}`) REQUIRE ({prop_list}) IS NODE KEY"

    return None


def build_index_cypher(index: dict) -> str | None:
    """Build Cypher statement to create an index."""
    name = index["name"]
    index_type = index["type"]
    labels = index.get("labels", [])
    properties = index.get("properties", [])
    options = index.get("options", {})

    if not labels or not properties:
        return None

    label = labels[0]
    prop_list = ", ".join(f"n.`{p}`" for p in properties)

    if index_type == "RANGE":
        return f"CREATE INDEX `{name}` IF NOT EXISTS FOR (n:`{label}`) ON ({prop_list})"
    elif index_type == "TEXT":
        return f"CREATE TEXT INDEX `{name}` IF NOT EXISTS FOR (n:`{label}`) ON (n.`{properties[0]}`)"
    elif index_type == "FULLTEXT":
        props_str = ", ".join(f"n.`{p}`" for p in properties)
        return f"CREATE FULLTEXT INDEX `{name}` IF NOT EXISTS FOR (n:`{label}`) ON EACH [{props_str}]"
    elif index_type == "VECTOR":
        index_config = options.get("indexConfig", {})
        dimensions = index_config.get("vector.dimensions", 1536)
        similarity = index_config.get("vector.similarity_function", "cosine")
        return (
            f"CREATE VECTOR INDEX `{name}` IF NOT EXISTS FOR (n:`{label}`) ON (n.`{properties[0]}`) "
            f"OPTIONS {{indexConfig: {{`vector.dimensions`: {dimensions}, `vector.similarity_function`: '{similarity}'}}}}"
        )

    return None


def detect_and_parse_backup(content: str) -> dict:
    """Detect backup format and parse accordingly."""
    try:
        data = json.loads(content)
        if "nodes" in data and "relationships" in data:
            print("Detected Cypher fallback backup format")
            return {"nodes": data["nodes"], "relationships": data["relationships"]}
    except json.JSONDecodeError:
        pass

    print("Detected APOC JSON lines backup format")
    nodes = []
    relationships = []

    for line in content.strip().split("\n"):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
            item_type = item.get("type")
            if item_type == "node":
                nodes.append({
                    "id": item.get("id"),
                    "labels": item.get("labels", []),
                    "properties": item.get("properties", {}),
                })
            elif item_type == "relationship":
                relationships.append({
                    "id": item.get("id"),
                    "type": item.get("label"),
                    "startId": item.get("start", {}).get("id"),
                    "endId": item.get("end", {}).get("id"),
                    "properties": item.get("properties", {}),
                })
        except json.JSONDecodeError:
            continue

    return {"nodes": nodes, "relationships": relationships}


async def restore_database(config: RestoreConfig, backup_file: Path) -> dict:
    """Restore the Neo4j database from a backup file."""
    with open(backup_file, "r", encoding="utf-8") as f:
        content = f.read()

    backup_data = detect_and_parse_backup(content)

    driver = AsyncGraphDatabase.driver(config.uri, auth=(config.username, config.password))

    try:
        await driver.verify_connectivity()
        print(f"Connected to Neo4j at {config.uri}")

        async with driver.session() as session:
            print("Clearing existing data...")
            await session.run("MATCH (n) DETACH DELETE n")

            node_count = await restore_nodes(session, backup_data["nodes"])
            rel_count = await restore_relationships(session, backup_data["relationships"])

            return {"nodes": node_count, "relationships": rel_count}
    finally:
        await driver.close()


async def restore_nodes(session, nodes: list) -> int:
    """Restore nodes to the database."""
    print(f"Restoring {len(nodes)} nodes...")
    count = 0

    for node in nodes:
        labels = node.get("labels", [])
        properties = node.get("properties", {})
        old_id = node.get("id")

        if old_id:
            properties["_backup_id"] = str(old_id)

        label_str = ":" + ":".join(labels) if labels else ""
        await session.run(f"CREATE (n{label_str} $props)", {"props": properties})
        count += 1

        if count % 100 == 0:
            print(f"  Restored {count} nodes...")

    return count


async def restore_relationships(session, relationships: list) -> int:
    """Restore relationships to the database."""
    print(f"Restoring {len(relationships)} relationships...")
    count = 0

    for rel in relationships:
        rel_type = rel.get("type")
        start_id = str(rel.get("startId"))
        end_id = str(rel.get("endId"))
        properties = rel.get("properties", {})

        if not rel_type or not start_id or not end_id:
            continue

        await session.run(
            f"MATCH (a {{_backup_id: $startId}}) "
            f"MATCH (b {{_backup_id: $endId}}) "
            f"CREATE (a)-[r:`{rel_type}`]->(b) "
            f"SET r = $props",
            {"startId": start_id, "endId": end_id, "props": properties},
        )
        count += 1

        if count % 100 == 0:
            print(f"  Restored {count} relationships...")

    return count


async def cleanup_backup_ids(config: RestoreConfig) -> None:
    """Remove temporary _backup_id properties from all nodes."""
    driver = AsyncGraphDatabase.driver(config.uri, auth=(config.username, config.password))

    try:
        async with driver.session() as session:
            print("Cleaning up temporary backup IDs...")
            await session.run("MATCH (n) WHERE n._backup_id IS NOT NULL REMOVE n._backup_id")
    finally:
        await driver.close()


def verify_restore(expected: dict, actual: dict) -> tuple[bool, list[str]]:
    """Verify restore counts match expected values."""
    errors = []

    if actual["nodes"] != expected["nodes"]:
        errors.append(f"Node count mismatch: expected {expected['nodes']}, got {actual['nodes']}")

    if actual["relationships"] != expected["relationships"]:
        errors.append(f"Relationship count mismatch: expected {expected['relationships']}, got {actual['relationships']}")

    if expected.get("embeddings", 0) > 0:
        if actual.get("embeddings", 0) != expected["embeddings"]:
            errors.append(f"Embeddings count mismatch: expected {expected['embeddings']}, got {actual.get('embeddings', 0)}")

    return len(errors) == 0, errors


async def main() -> int:
    """Main entry point for the restore script."""
    parser = argparse.ArgumentParser(description="Neo4j Database Restore")
    parser.add_argument("--force", "-f", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    env_path = get_project_root() / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded environment from {env_path}")
    else:
        print(f"Warning: {env_path} not found")

    config = RestoreConfig()
    if not config.is_configured:
        print("Error: Neo4j configuration incomplete.")
        print("Required: NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD")
        return 1

    snapshot_dir = get_snapshot_dir()
    backup_file = snapshot_dir / "financial_backup.json"
    checksum_file = snapshot_dir / "financial_backup.checksum.json"

    if not backup_file.exists():
        print(f"Error: Backup file not found: {backup_file}")
        return 1

    print("=== Neo4j Database Restore ===")
    print(f"Source: {backup_file}")
    print()
    print("WARNING: This will DELETE ALL EXISTING DATA, INDEXES, and CONSTRAINTS!")
    print(f"Database: {config.uri}")
    print()

    if not args.force:
        response = input("Are you sure you want to continue? [y/N]: ").strip().lower()
        if response not in ("y", "yes"):
            print("Restore cancelled.")
            return 0

    print()

    expected_stats = None
    schema_to_restore = None

    if checksum_file.exists():
        with open(checksum_file, "r", encoding="utf-8") as f:
            expected_stats = json.load(f)
        print(f"Found checksum file: {checksum_file}")
        print(f"  Expected nodes: {expected_stats['nodes']}")
        print(f"  Expected relationships: {expected_stats['relationships']}")
        if expected_stats.get("embeddings", 0) > 0:
            print(f"  Expected embeddings: {expected_stats['embeddings']}")
        if expected_stats.get("schema"):
            schema_to_restore = expected_stats["schema"]
            print(f"  Indexes to restore: {len(schema_to_restore.get('indexes', []))}")
            print(f"  Constraints to restore: {len(schema_to_restore.get('constraints', []))}")
        print()
    else:
        print("Warning: No checksum file found, restore verification will be skipped")
        print()

    try:
        print("Dropping existing indexes and constraints...")
        dropped = await drop_all_schema(config)
        print(f"  Dropped {dropped['constraints']} constraints")
        print(f"  Dropped {dropped['indexes']} indexes")
        print()

        result = await restore_database(config, backup_file)
        await cleanup_backup_ids(config)

        if schema_to_restore:
            print()
            print("Recreating indexes and constraints...")
            created = await recreate_schema(config, schema_to_restore)
            print(f"  Created {created['constraints']} constraints")
            print(f"  Created {created['indexes']} indexes")
            if created["errors"]:
                print(f"  Warnings: {len(created['errors'])} schema items could not be created")

        print()
        print("=== Restore Complete ===")
        print(f"Nodes restored: {result['nodes']}")
        print(f"Relationships restored: {result['relationships']}")
        if schema_to_restore:
            print(f"Indexes created: {created['indexes']}")
            print(f"Constraints created: {created['constraints']}")

        if expected_stats:
            print()
            print("Verifying restore...")
            actual_stats = await get_database_stats(config)

            success, errors = verify_restore(expected_stats, actual_stats)
            if success:
                print("Verification PASSED: All counts match expected values")
            else:
                print("Verification FAILED:")
                for error in errors:
                    print(f"  - {error}")
                return 1

        return 0

    except Exception as e:
        print(f"Error: Restore failed - {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
