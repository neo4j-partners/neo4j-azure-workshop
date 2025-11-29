# Proposal: Knowledge Graph Pipeline Performance & Capability Upgrade

This proposal outlines a phased approach to upgrading the data pipeline to support higher throughput, better search accuracy, and improved reliability.

## Objectives
1.  **Increase Ingestion Speed:** Reduce the time required to process document batches by utilizing parallel processing and optimized drivers.
2.  **Enhance Search Quality:** Implement hybrid search to combine the semantic understanding of vectors with the precision of keyword matching.
3.  **Improve Reliability:** Resolve critical bugs related to duplicate entity insertion and ensure robust error handling.

---

## Implementation Plan

### Phase 1: Foundation & Performance
**Goal:** Optimize the underlying infrastructure and dependencies for maximum speed without changing the core logic.

*   [ ] **Upgrade Neo4j Driver:** Replace the standard Python driver with the high-performance Rust extension to accelerate data serialization and network communication.
*   [ ] **Implement Explicit Indexing:** Create a startup routine that verifies and creates database indexes for all entity names (e.g., Company, Executive) to speed up deduplication and insertion.
*   [ ] **Enable Concurrent Processing:** Refactor the main processing loop to handle multiple PDF files simultaneously, maximizing the utilization of network and API limits.
*   [ ] **Code Review & Testing:** Verify that faster processing does not introduce race conditions or rate-limit errors.

### Phase 2: Advanced Search Capabilities
**Goal:** Enable "Hybrid Search" to allow users to find information using both exact keywords and conceptual similarity.

*   [ ] **Create Fulltext Index:** Configure the database to maintain a full-text index on document chunks, enabling standard text search features.
*   [ ] **Implement Hybrid Retriever:** Update the search client to use a hybrid retrieval strategy that weights and combines results from both vector search and text search.
*   [ ] **Expose Tuning Parameters:** Add CLI arguments to allow users to adjust the balance (alpha) between vector and keyword results at runtime.
*   [ ] **Code Review & Testing:** Validate that search results are more relevant and that the new index stays synchronized.

### Phase 3: Reliability & Quality Assurance
**Goal:** Fix known ingestion bugs and improve the quality of the extracted graph.

*   [ ] **Fix Duplicate Entity Bug:** Implement a robust "upsert" (update or insert) strategy to handle cases where an entity already exists, preventing pipeline crashes.
*   [ ] **Defer Entity Resolution:** Move the entity deduplication step to run *after* all files have been processed, rather than during ingestion, to improve stability and speed.
*   [ ] **Add Schema Validation:** Ensure that the graph schema is strictly enforced and that any deviations are logged clearly for debugging.
*   [ ] **Code Review & Testing:** Run the pipeline against the full dataset to ensure 100% completion without crashes.

### Phase 4: Final Polish & Documentation
**Goal:** Ensure the system is maintainable and easy to use.

*   [ ] **Update Documentation:** usage guides to reflect the new concurrency options and search features.
*   [ ] **Performance Benchmarking:** Measure and record the time taken to process the sample dataset before and after changes.
*   [ ] **Final Code Review:** Conduct a comprehensive review of all changes.
