#!/usr/bin/env python3
"""Check if Chunk nodes exist with text properties in Neo4j."""

import asyncio
from pathlib import Path

from dotenv import load_dotenv
from neo4j import AsyncGraphDatabase
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Neo4jConfig(BaseSettings):
    """Neo4j connection config."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    uri: str | None = Field(default=None, validation_alias="NEO4J_URI")
    username: str | None = Field(default=None, validation_alias="NEO4J_USERNAME")
    password: str | None = Field(default=None, validation_alias="NEO4J_PASSWORD")


async def check_chunks() -> None:
    """Check Chunk nodes in the database."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    config = Neo4jConfig()
    if not all([config.uri, config.username, config.password]):
        print("Error: NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD required")
        return

    driver = AsyncGraphDatabase.driver(config.uri, auth=(config.username, config.password))

    try:
        await driver.verify_connectivity()
        print(f"Connected to Neo4j at {config.uri}\n")

        async with driver.session() as session:
            # Count Chunk nodes
            result = await session.run("MATCH (c:Chunk) RETURN count(c) AS count")
            record = await result.single()
            chunk_count = record["count"]
            print(f"Chunk nodes: {chunk_count}")

            if chunk_count == 0:
                print("\nNo Chunk nodes found in database.")
                return

            # Check for text property
            result = await session.run(
                "MATCH (c:Chunk) WHERE c.text IS NOT NULL RETURN count(c) AS count"
            )
            record = await result.single()
            with_text = record["count"]
            print(f"Chunks with text property: {with_text}")

            # Sample some chunk text
            if with_text > 0:
                print("\n--- Sample Chunk Text ---")
                result = await session.run(
                    """
                    MATCH (c:Chunk)
                    WHERE c.text IS NOT NULL
                    RETURN c.text AS text, size(c.text) AS length
                    LIMIT 3
                    """
                )
                records = await result.data()
                for i, rec in enumerate(records, 1):
                    text = rec["text"]
                    length = rec["length"]
                    preview = text[:200] + "..." if len(text) > 200 else text
                    print(f"\n[{i}] Length: {length} chars")
                    print(f"    {preview}")

            # Check for existing fulltext indexes
            print("\n--- Existing Fulltext Indexes ---")
            result = await session.run(
                "SHOW FULLTEXT INDEXES YIELD name, labelsOrTypes, properties"
            )
            records = await result.data()
            if records:
                for rec in records:
                    print(f"  - {rec['name']}: {rec['labelsOrTypes']} on {rec['properties']}")
            else:
                print("  (none)")

            # Check if search_chunks index exists
            result = await session.run(
                """
                SHOW FULLTEXT INDEXES
                YIELD name
                WHERE name = 'search_chunks'
                RETURN count(*) AS exists
                """
            )
            record = await result.single()
            if record["exists"] > 0:
                print("\n✓ search_chunks index already exists")
            else:
                print("\n✗ search_chunks index NOT found - needs to be created")

    finally:
        await driver.close()


if __name__ == "__main__":
    asyncio.run(check_chunks())
