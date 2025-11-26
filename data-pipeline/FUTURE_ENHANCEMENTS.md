# Future Enhancements

This document outlines potential improvements to the data pipeline using neo4j-graphrag-python best practices.

---

## BUG: Neo4j Insertion Fails on Duplicate Entities

**Priority:** Critical
**Status:** Needs Fix

When re-processing files or processing files that reference existing entities, the pipeline fails with:

```
IndexEntryConflictException{propertyValues=( String("APPLE INC") ), addedEntityId=-1, existingEntityId=2}
```

**Problem:** The `apoc.create.addLabels` procedure fails when a node with the same unique property already exists. Even though `perform_entity_resolution=True` is set, the APOC procedure fails before entity resolution can run.

**Impact:** Entities and relationships in the failed batch are lost (silently skipped when `on_error="IGNORE"`).

**Potential Solutions:**
1. Clear the database before re-processing the same files
2. Investigate why `SimpleKGPipeline` entity resolution doesn't handle this case
3. Add MERGE-based upsert logic instead of CREATE
4. Pre-check for existing entities before insertion

---

## 1. Fulltext Index for Hybrid Search

**Priority:** High
**Files:** `main.py`, `search.py`, `config.py`

Add a fulltext index alongside the vector index to enable hybrid search combining keyword matching with semantic similarity.

### Implementation

**In `main.py`:**
```python
from neo4j_graphrag.indexes import create_fulltext_index

def ensure_fulltext_index(driver: Driver, settings: PipelineSettings) -> None:
    """Create fulltext index on Chunk text for hybrid search."""
    try:
        create_fulltext_index(
            driver,
            name=settings.neo4j.fulltext_index_name,
            label="Chunk",
            node_properties=["text"],
        )
        logger.info("fulltext_index_created", name=settings.neo4j.fulltext_index_name)
    except Exception as e:
        if "already exists" in str(e).lower():
            logger.debug("fulltext_index_exists")
        else:
            logger.warning("fulltext_index_error", error=str(e))
```

**In `config.py`:**
```python
class Neo4jSettings(BaseSettings):
    fulltext_index_name: str = Field(
        default="chunkFulltext",
        validation_alias="NEO4J_FULLTEXT_INDEX_NAME",
        description="Name of the fulltext index for chunk text",
    )
```

### Benefits
- Better results for exact keyword matches
- Combines strengths of keyword and semantic search
- Useful when users search for specific terms

---

## 2. Hybrid Search in Search Client

**Priority:** High
**Files:** `search.py`

Replace or augment `VectorCypherRetriever` with `HybridCypherRetriever` for combined fulltext + vector search.

### Implementation

```python
from neo4j_graphrag.retrievers import HybridCypherRetriever

HYBRID_RETRIEVAL_QUERY = """
MATCH (chunk)-[:FROM_DOCUMENT]->(doc:Document)
OPTIONAL MATCH (entity)-[:FROM_CHUNK]->(chunk)
WHERE entity IS NULL OR (NOT entity:Document AND NOT entity:Chunk)
WITH chunk, doc, score,
     collect(DISTINCT {type: labels(entity)[0], name: entity.name}) AS entities
RETURN chunk.text AS text,
       doc.path AS document,
       score,
       [e IN entities WHERE e.name IS NOT NULL] AS related_entities
ORDER BY score DESC
"""

def search_chunks_hybrid(
    query: str,
    limit: int = 5,
    alpha: float = 0.7,  # weight: 0.7 vector, 0.3 fulltext
) -> None:
    """Search using hybrid vector + fulltext retrieval."""
    settings = get_settings()
    driver = create_neo4j_driver(settings)
    embedder = create_embedder(settings)

    retriever = HybridCypherRetriever(
        driver=driver,
        vector_index_name=settings.neo4j.vector_index_name,
        fulltext_index_name=settings.neo4j.fulltext_index_name,
        retrieval_query=HYBRID_RETRIEVAL_QUERY,
        embedder=embedder,
        neo4j_database=settings.neo4j.database,
    )

    result = retriever.search(
        query_text=query,
        top_k=limit,
        alpha=alpha,  # Balance between vector and fulltext
    )
```

### CLI Addition
```bash
uv run python -m pipeline.search "risk factors" --hybrid --alpha 0.7
```

---

## 3. Enhanced Entity Resolution with FuzzyMatchResolver

**Priority:** Medium
**Files:** `main.py`

Use `FuzzyMatchResolver` for better entity deduplication when exact name matching isn't sufficient.

### Implementation

```python
from neo4j_graphrag.experimental.components.resolver import FuzzyMatchResolver

async def run_fuzzy_resolution(driver: Driver, settings: PipelineSettings) -> None:
    """Run fuzzy entity resolution after pipeline processing."""
    resolver = FuzzyMatchResolver(
        driver=driver,
        resolve_properties=["name"],
        similarity_threshold=0.85,  # 85% similarity threshold
        neo4j_database=settings.neo4j.database,
    )

    stats = await resolver.run()
    logger.info(
        "fuzzy_resolution_complete",
        nodes_resolved=stats.number_of_nodes_to_resolve,
        nodes_created=stats.number_of_created_nodes,
    )
```

### Requirements
```bash
uv add "neo4j-graphrag[fuzzy-matching]"
```

### Benefits
- Merges entities like "Apple Inc" and "Apple Inc."
- Handles minor spelling variations
- Reduces duplicate nodes in the graph

---

## 4. Explicit LexicalGraphConfig

**Priority:** Low
**Files:** `main.py`

Make the lexical graph configuration explicit for better maintainability and customization.

### Implementation

```python
from neo4j_graphrag.experimental.components.types import LexicalGraphConfig

def create_pipeline(
    driver: Driver,
    llm: AzureOpenAILLM,
    embedder: AzureOpenAIEmbeddings,
    strict_mode: bool = False,
) -> SimpleKGPipeline:
    """Create pipeline with explicit lexical graph config."""

    lexical_config = LexicalGraphConfig(
        document_node_label="Document",
        chunk_node_label="Chunk",
        chunk_to_document_relationship_type="FROM_DOCUMENT",
        next_chunk_relationship_type="NEXT_CHUNK",
        node_to_chunk_relationship_type="FROM_CHUNK",
        chunk_text_property="text",
        chunk_embedding_property="embedding",
    )

    return SimpleKGPipeline(
        driver=driver,
        llm=llm,
        embedder=embedder,
        schema=GRAPH_SCHEMA,
        prompt_template=get_default_template(),
        on_error="RAISE" if strict_mode else "IGNORE",
        perform_entity_resolution=True,
        lexical_graph_config=lexical_config,
    )
```

### Benefits
- Self-documenting configuration
- Easy to customize node/relationship names
- Ensures vector index matches chunk properties

---

## 5. Concurrent File Processing

**Priority:** Medium
**Files:** `main.py`

Process multiple PDF files concurrently with controlled parallelism for faster throughput.

### Implementation

```python
import asyncio

async def run_pipeline_concurrent(
    pdf_files: list[Path],
    settings: PipelineSettings,
    strict_mode: bool = False,
    max_concurrent: int = 3,
) -> tuple[int, int]:
    """Run pipeline with concurrent file processing."""
    driver = create_neo4j_driver(settings)

    try:
        validate_neo4j_connection(driver, settings)
        llm = create_llm(settings)
        embedder = create_embedder(settings)
        ensure_vector_index(driver, settings)

        pipeline = create_pipeline(driver, llm, embedder, strict_mode)

        # Semaphore for controlled concurrency
        sem = asyncio.Semaphore(max_concurrent)

        async def process_with_limit(pdf_file: Path) -> bool:
            async with sem:
                return await process_file(pipeline, pdf_file, strict_mode)

        # Process all files concurrently (up to max_concurrent at a time)
        results = await asyncio.gather(
            *[process_with_limit(f) for f in pdf_files],
            return_exceptions=True,
        )

        processed = sum(1 for r in results if r is True)
        failed = sum(1 for r in results if r is not True)

        return processed, failed

    finally:
        driver.close()
```

### CLI Addition
```bash
uv run python -m pipeline.main --concurrent 3
```

### Considerations
- Monitor Neo4j connection pool usage
- Azure OpenAI rate limits may require tuning
- Already uses `RetryRateLimitHandler` for rate limiting

---

## 6. Schema Serialization and Versioning

**Priority:** Low
**Files:** `models.py`

Save schema to file for versioning and documentation.

### Implementation

```python
from pathlib import Path

def save_schema(output_path: Path) -> None:
    """Save the graph schema to a JSON file."""
    GRAPH_SCHEMA.save(output_path, overwrite=True)

def load_schema(input_path: Path) -> GraphSchema:
    """Load a graph schema from file."""
    return GraphSchema.from_file(input_path)
```

### CLI Addition
```bash
# Export schema
uv run python -c "from pipeline.models import GRAPH_SCHEMA; GRAPH_SCHEMA.save('schema.json')"

# Or add to main.py
uv run python -m pipeline.main --export-schema schema.json
```

### Benefits
- Version control for schema changes
- Documentation of graph structure
- Share schema between projects

---

## 7. Text2CypherRetriever for Natural Language Queries

**Priority:** Low
**Files:** `search.py`

Add natural language to Cypher query capability for flexible graph exploration.

### Implementation

```python
from neo4j_graphrag.retrievers import Text2CypherRetriever
from neo4j_graphrag.llm import AzureOpenAILLM

def search_natural_language(query: str) -> None:
    """Convert natural language to Cypher and execute."""
    settings = get_settings()
    driver = create_neo4j_driver(settings)
    llm = create_llm(settings)

    # Generate schema description from GRAPH_SCHEMA
    schema_description = generate_schema_description()

    retriever = Text2CypherRetriever(
        driver=driver,
        llm=llm,
        neo4j_schema=schema_description,
        examples=[
            "USER: Which companies face supply chain risks? "
            "QUERY: MATCH (c:Company)-[:FACES_RISK]->(r:RiskFactor) "
            "WHERE r.name CONTAINS 'supply chain' RETURN c.name, r.name",
        ],
        neo4j_database=settings.neo4j.database,
    )

    result = retriever.search(query_text=query)
```

### CLI Addition
```bash
uv run python -m pipeline.search --natural "What risks does Apple face?"
```

---

## Implementation Priority

| Enhancement | Priority | Effort | Impact |
|-------------|----------|--------|--------|
| Fulltext Index | High | Low | High |
| Hybrid Search | High | Medium | High |
| FuzzyMatchResolver | Medium | Low | Medium |
| Concurrent Processing | Medium | Medium | High |
| LexicalGraphConfig | Low | Low | Low |
| Schema Serialization | Low | Low | Low |
| Text2CypherRetriever | Low | Medium | Medium |

## References

- [neo4j-graphrag-python Documentation](https://neo4j.com/docs/neo4j-graphrag-python/current/)
- [Neo4j Vector Search](https://neo4j.com/docs/cypher-manual/current/indexes-for-vector-search/)
- [Neo4j Fulltext Indexes](https://neo4j.com/docs/cypher-manual/current/indexes-for-full-text-search/)
