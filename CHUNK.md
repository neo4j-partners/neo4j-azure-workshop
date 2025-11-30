# Adding Fulltext Index on Chunk Text

This document describes how to add a fulltext index on `Chunk` nodes for use with the Neo4j Context Provider's fulltext search capability.

## Verification Results (2025-11-30)

Ran `scripts/check_chunks.py` to verify database state:

```
Chunk nodes: 390
Chunks with text property: 390

Sample text lengths: ~4000 chars each (financial document excerpts)

Existing Fulltext Indexes:
  - search_entities: ['Company', 'Product', 'RiskFactor'] on ['name']

✗ search_chunks index NOT found - needs to be created
```

**Conclusion**: The proposal is viable. All 390 Chunk nodes have text content suitable for fulltext indexing.

## Background

The current `restore_neo4j.py` script creates a fulltext index called `search_entities` on entity names (Company, Product, RiskFactor). This is useful for direct entity lookups but doesn't work well with the context provider which expects to search chunk text.

The context provider's default retrieval query expects `node.text`:
```cypher
RETURN node.text AS text, score
ORDER BY score DESC
```

## Solution: Add Chunk Text Fulltext Index

### Step 1: Update restore_neo4j.py

In the `create_fulltext_indexes()` function (around line 177), add a second index to the `fulltext_indexes` list:

```python
# Define fulltext indexes to create
fulltext_indexes = [
    {
        "name": "search_entities",
        "labels": ["Company", "Product", "RiskFactor"],
        "properties": ["name"],
    },
    {
        "name": "search_chunks",  # For context provider fulltext search
        "labels": ["Chunk"],
        "properties": ["text"],
    },
]
```

### Step 2: Update .env

Add or update the fulltext index name environment variable:

```bash
NEO4J_FULLTEXT_INDEX_NAME=search_chunks
```

### Step 3: Re-run Restore (or create index manually)

Either re-run the restore script:
```bash
uv run python scripts/restore_neo4j.py --force
```

Or create the index manually in Neo4j Browser:
```cypher
CREATE FULLTEXT INDEX search_chunks IF NOT EXISTS
FOR (n:Chunk) ON EACH [n.text]
```

Wait for the index to come online:
```cypher
CALL db.awaitIndexes(300)
```

## Verifying the Index

Check that both indexes exist:
```cypher
SHOW FULLTEXT INDEXES
```

Expected output should include:
- `search_entities` - on Company, Product, RiskFactor names
- `search_chunks` - on Chunk text

Test the chunk search:
```cypher
CALL db.index.fulltext.queryNodes("search_chunks", "revenue growth")
YIELD node, score
RETURN node.text AS text, score
LIMIT 5
```

## Using with Context Provider

The `Neo4jContextProvider` can now use fulltext search on chunk text:

```python
from neo4j_provider import Neo4jContextProvider

provider = Neo4jContextProvider(
    index_name="search_chunks",  # or use NEO4J_FULLTEXT_INDEX_NAME env var
    index_type="fulltext",
    top_k=5,
)
```

## Index Comparison

| Index | Labels | Property | Use Case |
|-------|--------|----------|----------|
| `search_entities` | Company, Product, RiskFactor | name | API entity lookup, direct name search |
| `search_chunks` | Chunk | text | Context provider fulltext search |
| `chunkEmbeddings` | Chunk | embedding | Context provider vector/semantic search |

## Sample Code

See the `neo4j-maf-provider` project for working samples:
- `src/samples/context_provider_basic.py` - Fulltext search with ChatAgent
- `src/samples/context_provider_vector.py` - Vector search with ChatAgent
