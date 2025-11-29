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
The pipeline relies on `SimpleKGPipeline` to manage some indexes, but explicit control ensures critical paths are optimized. The `FUTURE_ENHANCEMENTS.md` notes a need for fulltext indexes.

**Recommendation:**
- **Entity Indexes:** Explicitly create `RANGE` or `TEXT` indexes on the `name` property for all entity labels (`Company`, `Executive`, etc.) *before* ingestion starts. This speeds up the `MERGE` (deduplication) operations during writing.
- **Fulltext Index:** Implement the Fulltext index on `Chunk(text)` to enable Hybrid Search.
- **Vector Index:** Ensure the vector index is pre-created with the correct dimensions (already largely handled, but verifying configuration is key).

## 4. Optimized Entity Resolution

**Current State:**
`SimpleKGPipeline` runs entity resolution (simple name matching) effectively. `FUTURE_ENHANCEMENTS.md` notes a critical bug with duplicate entities causing crashes.

**Recommendation:**
- **Defer Resolution:** If possible, disable per-file resolution and run a global resolution step at the end of the batch. This reduces the overhead of constantly checking for duplicates during high-concurrency insertion.
- **Fuzzy Matching:** Adopt the `FuzzyMatchResolver` (as planned) for better quality, but run it as a post-processing job, not inline, to avoid slowing down ingestion.

## 5. Pipeline Component Configuration

**Current State:**
The code uses `SimpleKGPipeline` which abstracts away many settings.

**Recommendation:**
If `SimpleKGPipeline` allows passing `batch_size` to the underlying `Neo4jWriter`, increase it (e.g., to 1000 or 5000) to reduce network round-trips to the database. If the abstraction prevents this, consider "ejecting" to the component-level API (composing `PdfLoader`, `LLMExtractor`, `Neo4jWriter` manually) for fine-grained control over:
- `max_concurrency` for LLM calls.
- `batch_size` for writes.

## 6. Hybrid Search Implementation

**Current State:**
Search uses `VectorCypherRetriever` (vector only).

**Recommendation:**
Implement `HybridCypherRetriever`.
- Combine vector scores with fulltext BM25 scores.
- This improves "zero-shot" performance for domain-specific acronyms or exact phrases that vector models might miss.
