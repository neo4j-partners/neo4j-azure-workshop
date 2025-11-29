# Performance Improvement Recommendations

Based on a review of the `@data-pipeline` codebase and `neo4j-graphrag-python` documentation, the following recommendations are proposed to improve the performance, scalability, and retrieval quality of the Knowledge Graph pipeline.

## 1. Concurrent File Processing (High Impact)

**Current State:**
The pipeline processes PDF files sequentially in a loop (`pipeline/main.py`). This underutilizes available network bandwidth and LLM concurrency limits, making the ingestion of large datasets significantly slower than necessary.

**Recommendation:**
Refactor the `run_pipeline` function to process multiple files in parallel using `asyncio`.
- Use `asyncio.gather` or `asyncio.Semaphore` to control the level of concurrency (e.g., process 3-5 files at a time).
- This allows the application to chunk and embed one file while waiting for LLM extraction on another.

## 2. Neo4j Driver Optimization

**Current State:**
The project uses the standard Python `neo4j` driver.

**Recommendation:**
Switch to the `neo4j-rust-ext` driver.
- This is a drop-in replacement that uses Rust for the underlying Bolt protocol implementation.
- It can offer significant speedups (3x-10x) for serialization/deserialization, which is critical when moving large amounts of vector and graph data.

## 3. Explicit Indexing Strategy

**Current State:**
The pipeline relies on `SimpleKGPipeline` to manage some indexes, but explicit control ensures critical paths are optimized.

**Recommendation:**
- **Entity Indexes:** Explicitly create `RANGE` or `TEXT` indexes on the `name` property for all entity labels (`Company`, `Executive`, etc.) *before* ingestion starts. This speeds up the `MERGE` (deduplication) operations during writing.
- **Fulltext Index:** Implement the Fulltext index on `Chunk(text)` to enable Hybrid Search.
- **Vector Index:** Ensure the vector index is pre-created with the correct dimensions.

## 4. Optimized Entity Resolution

**Current State:**
`SimpleKGPipeline` runs entity resolution (simple name matching) inline after every file if `perform_entity_resolution=True` (default). This causes repeated, expensive global graph scans.

**Recommendation:**
- **Disable Inline Resolution:** Set `perform_entity_resolution=False` in the `SimpleKGPipeline` constructor.
- **Global Resolution:** Run a single, global entity resolution step *once* after the entire batch of files has been processed. This eliminates redundant deduplication passes.
- **Fuzzy Matching:** Adopt the `FuzzyMatchResolver` for the global resolution step to handle minor spelling variations (e.g. "Apple" vs "Apple Inc").

## 5. Pipeline Component Configuration (Batching)

**Current State:**
The code uses `SimpleKGPipeline` with default settings. The default `Neo4jWriter` uses a `batch_size` of 1000, which is often too small for high-throughput ingestion.

**Recommendation:**
Inject a custom `Neo4jWriter` with an increased batch size to reduce network round-trips.

```python
from neo4j_graphrag.experimental.components.kg_writer import Neo4jWriter

# Create a custom writer
kg_writer = Neo4jWriter(
    driver=driver,
    batch_size=5000,  # Increase from default 1000 to 5000
    on_error="IGNORE"
)

# Inject into pipeline
pipeline = SimpleKGPipeline(
    ...,
    kg_writer=kg_writer,
    perform_entity_resolution=False  # Defer resolution
)
```

## 6. Hybrid Search Implementation

**Current State:**
Search uses `VectorCypherRetriever` (vector only).

**Recommendation:**
Implement `HybridCypherRetriever`.
- Combine vector scores with fulltext BM25 scores.
- This improves "zero-shot" performance for domain-specific acronyms or exact phrases that vector models might miss.