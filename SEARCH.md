# Search Capabilities

This document describes the search indexes and query patterns available in the Neo4j knowledge graph.

## Available Indexes

### Vector Index

| Index Name | Label | Property | Dimensions | Similarity |
|------------|-------|----------|------------|------------|
| `chunkEmbeddings` | `Chunk` | `embedding` | 1536 | COSINE |

Used for semantic similarity search over document chunks.

### Fulltext Index

| Index Name | Labels | Property |
|------------|--------|----------|
| `search_entities` | `Company`, `Product`, `RiskFactor` | `name` |

Used for keyword-based entity search. Created with `--full-text` flag:

```bash
uv run python scripts/restore_neo4j.py --full-text
```

## Fulltext Search Syntax

### Basic Queries

```cypher
-- Simple keyword search
CALL db.index.fulltext.queryNodes('search_entities', 'Apple')
YIELD node, score
RETURN node.name, labels(node), score

-- Case insensitive by default
CALL db.index.fulltext.queryNodes('search_entities', 'apple')
```

### Fuzzy Matching

Handle typos with the `~` operator:

```cypher
-- Fuzzy search (edit distance 1-2)
CALL db.index.fulltext.queryNodes('search_entities', 'Aplle~')
YIELD node, score
RETURN node.name, score

-- Specify edit distance (0, 1, or 2)
CALL db.index.fulltext.queryNodes('search_entities', 'Microsft~1')
```

### Wildcards

```cypher
-- Prefix matching with *
CALL db.index.fulltext.queryNodes('search_entities', 'Micro*')

-- Single character wildcard with ?
CALL db.index.fulltext.queryNodes('search_entities', 'App?e')
```

### Boolean Operators

```cypher
-- AND: Both terms must match
CALL db.index.fulltext.queryNodes('search_entities', 'supply AND chain')

-- OR: Either term matches
CALL db.index.fulltext.queryNodes('search_entities', 'Apple OR Microsoft')

-- NOT: Exclude term
CALL db.index.fulltext.queryNodes('search_entities', 'risk NOT financial')

-- Required term with +
CALL db.index.fulltext.queryNodes('search_entities', '+supply chain')

-- Excluded term with -
CALL db.index.fulltext.queryNodes('search_entities', 'supply -shortage')
```

### Phrase Search

```cypher
-- Exact phrase matching
CALL db.index.fulltext.queryNodes('search_entities', '"supply chain"')
```

### Search Options

```cypher
-- Pagination with skip and limit
CALL db.index.fulltext.queryNodes('search_entities', 'risk', {skip: 10, limit: 5})
YIELD node, score
RETURN node.name, score
```

## Common Search Patterns

### Find Company and Related Documents

```cypher
CALL db.index.fulltext.queryNodes('search_entities', 'Nvidia')
YIELD node, score
WHERE 'Company' IN labels(node)
WITH node AS company, score
LIMIT 1

MATCH (company)-[:FILED]->(doc:Document)
RETURN company.name, COLLECT(DISTINCT doc.path) AS documents
```

### Find Risk Factors for a Company

```cypher
CALL db.index.fulltext.queryNodes('search_entities', 'Apple')
YIELD node, score
WHERE 'Company' IN labels(node)
WITH node AS company
LIMIT 1

MATCH (company)-[:FACES_RISK]->(risk:RiskFactor)
RETURN company.name, COLLECT(DISTINCT risk.name) AS risk_factors
```

### Hybrid Search: Keyword + Graph Context

```cypher
-- Find chunks where a company was extracted
CALL db.index.fulltext.queryNodes('search_entities', 'Amazon')
YIELD node AS entity, score
WHERE 'Company' IN labels(entity)
WITH entity, score
LIMIT 1

MATCH (entity)-[:FROM_CHUNK]->(chunk:Chunk)
RETURN entity.name AS company, score, chunk.text
LIMIT 10
```

## Vector vs Fulltext Search

| Feature | Vector Search | Fulltext Search |
|---------|--------------|-----------------|
| **Use Case** | Semantic similarity | Keyword matching |
| **Query Type** | Natural language questions | Known entity names |
| **Matching** | Conceptual | Lexical |
| **Example** | "What risks does the company face?" | "Apple" |
| **Scoring** | Cosine similarity | Lucene relevance |

### When to Use Each

**Use Vector Search when:**
- Asking natural language questions
- Finding conceptually similar content
- The exact wording is unknown

**Use Fulltext Search when:**
- Searching for known entity names
- Filtering by specific keywords
- Building autocomplete/typeahead features

**Use Hybrid (both) when:**
- Maximum recall is needed
- Combining keyword precision with semantic understanding

## Performance Considerations

1. **Fulltext indexes are fast** for keyword lookups but don't understand semantics
2. **Vector indexes excel** at finding similar content but require embedding computation
3. **Combine both** by using fulltext to filter entities, then vector for semantic ranking
4. **Use LIMIT** early in queries to avoid processing unnecessary results
5. **Graph traversal** after search leverages Neo4j's strength in relationship queries
