# Proposal: Knowledge Graph Pipeline Performance & Capability Upgrade

This proposal outlines a phased approach to upgrading the data pipeline to support higher throughput, better search accuracy, and improved reliability.

## Objectives
1.  **Increase Ingestion Speed:** Reduce the time required to process document batches by utilizing parallel processing, optimized drivers, and better batching strategies.
2.  **Enhance Search Quality:** Implement hybrid search to combine the semantic understanding of vectors with the precision of keyword matching.
3.  **Improve Reliability:** Resolve critical bugs related to duplicate entity insertion and ensure robust error handling.

---

## Implementation Plan

### Phase 1: Foundation & Performance
**Goal:** Optimize the underlying infrastructure and dependencies for maximum speed without changing the core logic.

*   [ ] **Upgrade Neo4j Driver:** Replace the standard Python driver with the high-performance Rust extension (`neo4j-rust-ext`) to accelerate data serialization.
*   [ ] **Optimize Pipeline Configuration:**
    *   Inject a custom `Neo4jWriter` with `batch_size=5000`.
    *   Disable inline entity resolution (`perform_entity_resolution=False`).
*   [ ] **Implement Explicit Indexing:** Create a startup routine that verifies and creates database indexes for all entity names (e.g., Company, Executive) to speed up deduplication.
*   [ ] **Enable Concurrent Processing:** Refactor the main processing loop to handle multiple PDF files simultaneously (e.g., `asyncio.gather` with a Semaphore), maximizing network and API utilization.
*   [ ] **Global Entity Resolution:** Implement a standalone resolution step to run once at the end of the batch ingestion.
*   [ ] **Code Review & Testing:** Verify that faster processing does not introduce race conditions or rate-limit errors.

### Phase 2: Advanced Search Capabilities
**Goal:** Enable "Hybrid Search" to allow users to find information using both exact keywords and conceptual similarity.

*   [ ] **Create Fulltext Index:** Configure the database to maintain a full-text index on document chunks.
*   [ ] **Implement Hybrid Retriever:** Update the search client to use `HybridCypherRetriever`, combining vector search and text search scores.
*   [ ] **Expose Tuning Parameters:** Add CLI arguments to allow users to adjust the balance (alpha) between vector and keyword results.
*   [ ] **Code Review & Testing:** Validate that search results are more relevant.

### Phase 3: Reliability & Quality Assurance
**Goal:** Fix known ingestion bugs and improve the quality of the extracted graph.

*   [ ] **Fix Duplicate Entity Bug:** Ensure the `Neo4jWriter` or upstream logic handles pre-existing entities gracefully (often resolved by the explicit indexing in Phase 1 and global resolution).
*   [ ] **Add Schema Validation:** Ensure that the graph schema is strictly enforced.
*   [ ] **Code Review & Testing:** Run the pipeline against the full dataset to ensure 100% completion without crashes.

### Phase 4: Final Polish & Documentation
**Goal:** Ensure the system is maintainable and easy to use.

*   [ ] **Update Documentation:** Update usage guides to reflect the new concurrency options and search features.
*   [ ] **Performance Benchmarking:** Measure and record the time taken to process the sample dataset before and after changes.
*   [ ] **Final Code Review:** Conduct a comprehensive review of all changes.