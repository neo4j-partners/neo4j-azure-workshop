#!/usr/bin/env python3
"""
Neo4j Database Restore Script

Streams and restores the Neo4j database from GitHub.

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

import httpx
from dotenv import load_dotenv
from neo4j import AsyncGraphDatabase
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# GitHub LFS media URL for backup file
GITHUB_URL = "https://media.githubusercontent.com/media/neo4j-partners/workshop-financial-data/main/snapshot/financial_backup.json"


class RestoreConfig(BaseSettings):
    """Configuration for Neo4j restore loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    uri: str | None = Field(default=None, validation_alias="NEO4J_URI")
    username: str | None = Field(default=None, validation_alias="NEO4J_USERNAME")
    password: str | None = Field(default=None, validation_alias="NEO4J_PASSWORD")

    @property
    def is_configured(self) -> bool:
        return all([self.uri, self.username, self.password])


def get_project_root() -> Path:
    return Path(__file__).parent.parent


async def stream_and_restore(config: RestoreConfig) -> dict:
    """Stream backup from GitHub and restore to Neo4j."""
    print(f"Streaming from {GITHUB_URL}...")

    driver = AsyncGraphDatabase.driver(config.uri, auth=(config.username, config.password))
    nodes = []
    relationships = []
    bytes_read = 0

    try:
        await driver.verify_connectivity()
        print(f"Connected to Neo4j at {config.uri}")

        # Stream and parse
        async with httpx.AsyncClient(timeout=600.0, follow_redirects=True) as client:
            async with client.stream("GET", GITHUB_URL) as response:
                response.raise_for_status()

                buffer = ""
                async for chunk in response.aiter_text():
                    bytes_read += len(chunk.encode("utf-8"))
                    buffer += chunk

                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        if not line.strip():
                            continue

                        try:
                            item = json.loads(line)
                            if item.get("type") == "node":
                                nodes.append({
                                    "id": item.get("id"),
                                    "labels": item.get("labels", []),
                                    "properties": item.get("properties", {}),
                                })
                            elif item.get("type") == "relationship":
                                relationships.append({
                                    "type": item.get("label"),
                                    "startId": item.get("start", {}).get("id"),
                                    "endId": item.get("end", {}).get("id"),
                                    "properties": item.get("properties", {}),
                                })
                        except json.JSONDecodeError:
                            continue

                    if bytes_read % (10 * 1024 * 1024) < len(chunk.encode("utf-8")):
                        print(f"  Streamed {bytes_read / (1024 * 1024):.1f} MB...")

        print(f"  Total: {bytes_read / (1024 * 1024):.1f} MB")
        print(f"  Parsed {len(nodes)} nodes, {len(relationships)} relationships")

        # Restore
        async with driver.session() as session:
            print("Clearing existing data...")
            await session.run("MATCH (n) DETACH DELETE n")

            print(f"Restoring {len(nodes)} nodes...")
            for i, node in enumerate(nodes):
                props = node["properties"].copy()
                props["_backup_id"] = str(node["id"])
                label_str = ":" + ":".join(node["labels"]) if node["labels"] else ""
                await session.run(f"CREATE (n{label_str} $props)", {"props": props})
                if (i + 1) % 500 == 0:
                    print(f"  {i + 1} nodes...")

            print(f"Restoring {len(relationships)} relationships...")
            for i, rel in enumerate(relationships):
                if not rel["type"] or not rel["startId"] or not rel["endId"]:
                    continue
                await session.run(
                    f"MATCH (a {{_backup_id: $startId}}) "
                    f"MATCH (b {{_backup_id: $endId}}) "
                    f"CREATE (a)-[r:`{rel['type']}`]->(b) "
                    f"SET r = $props",
                    {"startId": str(rel["startId"]), "endId": str(rel["endId"]), "props": rel["properties"]},
                )
                if (i + 1) % 500 == 0:
                    print(f"  {i + 1} relationships...")

            print("Cleaning up temporary IDs...")
            await session.run("MATCH (n) WHERE n._backup_id IS NOT NULL REMOVE n._backup_id")

        return {"nodes": len(nodes), "relationships": len(relationships)}
    finally:
        await driver.close()


async def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Neo4j Database Restore from GitHub")
    parser.add_argument("--force", "-f", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    env_path = get_project_root() / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    config = RestoreConfig()
    if not config.is_configured:
        print("Error: NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD required in .env")
        return 1

    print("=== Neo4j Database Restore ===")
    print()
    print("WARNING: This will DELETE ALL EXISTING DATA!")
    print(f"Database: {config.uri}")
    print()

    if not args.force:
        response = input("Continue? [y/N]: ").strip().lower()
        if response not in ("y", "yes"):
            print("Cancelled.")
            return 0

    print()

    try:
        result = await stream_and_restore(config)
        print()
        print("=== Restore Complete ===")
        print(f"Nodes: {result['nodes']}")
        print(f"Relationships: {result['relationships']}")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
