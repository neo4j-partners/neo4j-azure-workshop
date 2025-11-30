# Fulltext Search Guide

This guide covers fulltext search capabilities in Neo4j and the indexes created by the restore script.

## Indexes Created by restore_neo4j.py

The `scripts/restore_neo4j.py` script creates the following fulltext indexes:

| Index Name | Labels | Property | Purpose |
|------------|--------|----------|---------|
| `search_entities` | `Company`, `Product`, `RiskFactor` | `name` | Keyword search for entities |
| `search_chunks` | `Chunk` | `text` | Fulltext search over document content |

These indexes are always created during restore, regardless of whether the backup includes them.

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

### Pagination

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

### Search Document Chunks

```cypher
CALL db.index.fulltext.queryNodes('search_chunks', 'revenue growth')
YIELD node AS chunk, score
MATCH (chunk)-[:FROM_DOCUMENT]->(doc:Document)
RETURN chunk.text, doc.path, score
ORDER BY score DESC
LIMIT 10
```

### Hybrid: Keyword + Graph Context

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

## When to Use Fulltext vs Vector Search

| Feature | Fulltext Search | Vector Search |
|---------|----------------|---------------|
| **Use Case** | Keyword matching | Semantic similarity |
| **Query Type** | Known entity names | Natural language questions |
| **Matching** | Lexical | Conceptual |
| **Example** | "Apple" | "What risks does the company face?" |
| **Scoring** | Lucene relevance | Cosine similarity |

**Use Fulltext Search when:**
- Searching for known entity names
- Filtering by specific keywords
- Building autocomplete/typeahead features

**Use Vector Search when:**
- Asking natural language questions
- Finding conceptually similar content
- The exact wording is unknown

## Performance Tips

1. **Use LIMIT early** to avoid processing unnecessary results
2. **Filter by label** after the fulltext query to narrow results
3. **Combine with graph traversal** to enrich results with related data
4. **Use phrase search** for multi-word entity names
