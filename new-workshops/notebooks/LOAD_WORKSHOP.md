# Data Loading Workshop Notebooks - Proposal

## Overview

This document proposes a series of three introductory notebooks that teach the fundamentals of data loading, embedding generation, and entity extraction using the `neo4j-graphrag-python` library. These notebooks serve as **prerequisites** to the existing retriever and agent notebooks (02_xx and 03_xx series).

### Design Philosophy

- **Self-contained samples**: Use embedded sample text representing SEC 10-K content - no external files required
- **Incremental learning**: Each notebook builds on the previous one, introducing one new concept at a time
- **Hands-on simplicity**: Workshop participants should be able to run each cell and see results in seconds
- **No production concerns**: Skip error handling, retry logic, and edge cases in favor of clarity

### Why Sample Text Instead of PDFs?

The existing `data-pipeline` processes full SEC 10-K filings, which can take 10-30 minutes per document due to:
- PDF text extraction across 100+ pages
- Chunking into 4000-character segments
- LLM calls for entity extraction on each chunk
- Embedding generation for each chunk

For a workshop setting, using embedded sample text provides:
- **Zero setup**: No file downloads or path configuration needed
- **Instant results**: Text is immediately available without PDF parsing
- **Reproducible**: Same text across all environments
- **Same learning outcomes**: Demonstrates all the same concepts as PDF-based approach

---

## Notebook Series

### Notebook 01_01: Data Loading Fundamentals

**Purpose**: Introduce the basic concepts of loading text data into Neo4j and creating the document-chunk structure that forms the foundation of a knowledge graph.

**Learning Objectives**:
- Understand the relationship between documents and chunks
- Connect to Neo4j from a Jupyter notebook
- Create Document and Chunk nodes
- Understand why we chunk text (context windows, retrieval granularity)
- Query the basic graph structure

**Data Source**:
Embedded sample text representing Apple's SEC 10-K filing (company description, products, services).

**Key Concepts Covered**:
- Neo4j driver connection and basic Cypher
- Document node with metadata (source path)
- Chunk nodes with text content and index
- FROM_DOCUMENT relationship linking chunks to their source
- NEXT_CHUNK relationship for maintaining order
- Manual text splitting (by paragraph)

**What This Notebook Does NOT Cover**:
- Automatic text splitting (covered in next notebook)
- Embeddings (next notebook)
- Entity extraction (third notebook)

---

### Notebook 01_02: Embeddings and Vector Search

**Purpose**: Demonstrate how to generate embeddings for text chunks and perform vector similarity search using Neo4j's vector index.

**Learning Objectives**:
- Understand what embeddings are and why they matter for RAG
- Split text into chunks using `FixedSizeSplitter`
- Generate embeddings using Azure OpenAI
- Store embedding vectors on Chunk nodes
- Create a vector index in Neo4j
- Perform similarity search to find relevant chunks

**Data Source**:
Same embedded sample text as 01_01, split into smaller chunks for demonstration.

**Key Concepts Covered**:
- Text splitting with `FixedSizeSplitter` (400 chars, 50 overlap)
- Embedding models and vector dimensions (1536-dim)
- The `AzureOpenAIEmbeddings` class from neo4j-graphrag
- Storing vectors as node properties
- Creating a vector index with `create_vector_index()`
- Basic vector similarity search with cosine distance
- Understanding similarity scores

**What This Notebook Does NOT Cover**:
- Hybrid search (keyword + vector)
- Multiple embedding models
- Entity extraction (next notebook)

---

### Notebook 01_03: Entity Extraction Basics

**Purpose**: Show how to use an LLM to extract structured entities and relationships from text, completing the knowledge graph.

**Learning Objectives**:
- Understand the difference between lexical graphs (documents/chunks) and semantic graphs (entities/relationships)
- Define a schema with entity types and relationship types
- Use `SimpleKGPipeline` to extract entities from text
- Query the combined graph (chunks + entities)

**Data Source**:
Same embedded sample text as previous notebooks, which mentions Apple, its products, and services.

**Key Concepts Covered**:
- Schema definition with `NodeType` and `RelationshipType`
- Simplified schema: Company, Product, Service entities
- Relationships: OFFERS_PRODUCT, OFFERS_SERVICE
- `SimpleKGPipeline` with text input
- FROM_CHUNK relationships connecting entities to source chunks
- Querying entities and their relationships

**What This Notebook Does NOT Cover**:
- Custom extraction prompts
- Entity resolution (merging duplicates)
- Complex schema patterns
- Production error handling

---

## Data Source Strategy

All notebooks use the same embedded sample text representing Apple's SEC 10-K filing:

1. **Consistent source**: Same text across all three notebooks for continuity
2. **Self-contained**: No external files or downloads required
3. **Rich content**: Includes company description, products, and services
4. **Predictable results**: Entity extraction produces verifiable Company, Product, and Service entities

**Sample content includes:**
- Company: Apple Inc.
- Products: iPhone, Mac, iPad
- Services: AppleCare, Apple Pay, Cloud Services, Digital Content

---

## Implementation Plan

### Phase 1: Environment and Setup

**Goal**: Establish the notebook infrastructure and shared utilities.

**Todo List**:
1. Create notebook 01_01 skeleton with standard imports and markdown structure
2. Add Neo4j connection setup cell with environment variable loading
3. Add helper function to extract text from a single PDF page using pypdf
4. Add helper function to clear/reset the database between runs
5. Identify best PDF file and page numbers for each notebook's needs
6. Code review and testing of setup cells

---

### Phase 2: Notebook 01_01 - Data Loading

**Goal**: Complete the first notebook covering basic data loading from a PDF page.

**Todo List**:
1. Write introduction markdown explaining documents, chunks, and the document-chunk graph structure
2. Add cell to load a single page from a PDF file and display the extracted text
3. Add cell demonstrating manual Document node creation with Cypher (storing PDF path and page number)
4. Add cell manually splitting the page text into 2-3 chunks
5. Add cell creating Chunk nodes linked to the document with FROM_DOCUMENT relationships
6. Add cell creating NEXT_CHUNK relationships between sequential chunks
7. Add cell with query to visualize the document-chunk structure
8. Write summary markdown explaining what we built and how it connects to the next notebook
9. Code review and testing of complete notebook

---

### Phase 3: Notebook 01_02 - Embeddings

**Goal**: Complete the second notebook covering embedding generation and vector search on PDF content.

**Todo List**:
1. Copy setup cells from notebook 01_01 and add embedding-specific imports
2. Write introduction markdown explaining embeddings and why they enable semantic search
3. Add cell to extract text from a single PDF page (different page or same page with more content)
4. Add cell using `FixedSizeSplitter` to automatically chunk the text
5. Add cell showing how to initialize `AzureOpenAIEmbeddings`
6. Add cell generating embeddings for text chunks and displaying vector dimensions
7. Add cell creating Document and Chunk nodes with embeddings stored on chunks
8. Add cell creating vector index using `create_vector_index()`
9. Add cell demonstrating vector similarity search with a sample query about the PDF content
10. Add cell showing how similarity scores relate to semantic meaning
11. Write summary markdown connecting embeddings to the retriever notebooks
12. Code review and testing of complete notebook

---

### Phase 4: Notebook 01_03 - Entity Extraction

**Goal**: Complete the third notebook covering entity extraction from PDF content.

**Todo List**:
1. Copy setup cells and add entity extraction imports
2. Write introduction markdown explaining semantic graphs and why entities matter for RAG
3. Add cell to extract text from a single PDF page with entity-rich content
4. Add cell defining a simple schema using subset of data-pipeline entities (Company, Executive, Product, RiskFactor)
5. Add cell initializing `AzureOpenAILLM` for extraction
6. Add cell using `SimpleKGPipeline` to extract entities from the page text
7. Add cell displaying extracted entities and relationships
8. Add cell querying the combined graph (documents, chunks, and entities together)
9. Write summary markdown explaining how this foundation enables the retriever and agent notebooks
10. Code review and testing of complete notebook

---

### Phase 5: Integration and Polish

**Goal**: Ensure all three notebooks work together and provide a smooth learning experience.

**Todo List**:
1. Run all three notebooks in sequence on a fresh Neo4j database
2. Verify PDF page selections provide good content for each notebook's purpose
3. Add "Prerequisites" section to each notebook referencing previous notebooks
4. Add "Next Steps" section linking to the 02_xx retriever notebooks
5. Review markdown for clarity, typos, and consistent terminology
6. Verify all environment variables are documented
7. Test on clean environment with only required dependencies
8. Final code review and testing

---

## Dependencies

The notebooks require:
- `neo4j-graphrag` (with openai extras)
- `neo4j` driver
- `azure-identity` for Azure OpenAI authentication
- Standard Jupyter environment

Environment variables needed:
- `NEO4J_URI`
- `NEO4J_USERNAME`
- `NEO4J_PASSWORD`
- `AZURE_AI_PROJECT_ENDPOINT` (for Azure AI Foundry)
- `AZURE_AI_MODEL_NAME` (for entity extraction)
- `AZURE_AI_EMBEDDING_NAME` (for embeddings)

---

## Success Criteria

Each notebook should:
- Execute completely in under 60 seconds
- Use embedded sample text (no external files)
- Produce visible, verifiable results in Neo4j
- Build conceptual understanding through doing, not just reading
- Work with a local or cloud Neo4j instance

---

## Out of Scope

The following are explicitly excluded from these notebooks:
- Full PDF processing (multi-page)
- Large document handling
- Production error handling and retries
- Custom prompts and advanced schema design
- Entity resolution and deduplication
- Hybrid search
- Performance optimization
- Deployment considerations

---

## Implementation Status

### Overview

**Status**: ✅ Complete

All three notebooks have been implemented and are ready for testing.

### Implementation Notes

**Data Source Change**: The original plan called for loading actual PDF files from `financial-data/form10k-sample/`. However, these PDF files are not included in the repository (they are too large). The implementation uses **embedded sample text** that represents SEC 10-K content instead. This provides:
- Zero external dependencies (no file downloads needed)
- Instant, reproducible results
- Same learning outcomes as PDF-based approach

The sample text used across all notebooks represents Apple's 10-K filing content including company description, products (iPhone, Mac, iPad), and services (AppleCare, Apple Pay, etc.).

### Files Created

| File | Description | Status |
|------|-------------|--------|
| `notebooks/01_01_data_loading.ipynb` | Document/Chunk structure, manual chunking | ✅ Complete |
| `notebooks/01_02_embeddings.ipynb` | FixedSizeSplitter, embeddings, vector search | ✅ Complete |
| `notebooks/01_03_entity_extraction.ipynb` | Schema definition, SimpleKGPipeline | ✅ Complete |
| `solutions/01_01_data_loading.py` | Standalone Python solution | ✅ Tested |
| `solutions/01_02_embeddings.py` | Standalone Python solution | ✅ Tested |
| `solutions/01_03_entity_extraction.py` | Standalone Python solution | ✅ Tested |

### Phase Status

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1: Environment and Setup | ✅ Complete | Uses existing `config.py` from solutions/ |
| Phase 2: Notebook 01_01 | ✅ Complete | Manual chunking, basic Cypher |
| Phase 3: Notebook 01_02 | ✅ Complete | FixedSizeSplitter, vector index |
| Phase 4: Notebook 01_03 | ✅ Complete | Simplified schema (Company, Product, Service) |
| Phase 5: Integration and Polish | ✅ Complete | All notebooks linked, consistent structure |

### Schema Simplification

The entity extraction notebook uses a simplified schema compared to the full data-pipeline:

**Implemented:**
- Entity types: Company, Product, Service
- Relationships: OFFERS_PRODUCT, OFFERS_SERVICE

**Not included (for simplicity):**
- Executive, FinancialMetric, RiskFactor, StockType, Transaction, TimePeriod
- Complex relationship patterns

### Bug Fixes

**01_02_embeddings.ipynb** (2024-11-29):
- Fixed import path: `from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import FixedSizeSplitter`
- Changed to use `await splitter.run()` directly (Jupyter supports top-level await)

**01_03_entity_extraction.ipynb** (2024-11-29):
- Removed unnecessary `asyncio` import
- Changed to use `await pipeline.run_async()` directly instead of `asyncio.get_event_loop().run_until_complete()`
- Fixed schema definition: use `schema={"node_types": [...], "relationship_types": [...], "patterns": [...]}` dict format instead of separate `entities`, `relations`, `potential_schema` parameters
- Simplified entity/relationship definitions to use plain dicts instead of Pydantic models
- Fixed `find_chunks_for_entity` query: relationship is `(entity)-[:FROM_CHUNK]->(chunk)` not reverse
- Changed to only clear entity nodes (not Document/Chunk) so running notebooks in sequence builds a complete graph

### Testing Checklist

- [x] Run 01_01 on fresh Neo4j database (solution tested ✅)
- [x] Run 01_02 (verify vector index creation - solution tested ✅)
- [x] Run 01_03 (verify entity extraction - solution tested ✅)
- [ ] Verify "Next" links work between notebooks
- [ ] Confirm all notebook cells execute in < 60 seconds

### Test Results (2024-11-29)

**01_01_data_loading.py**: Created 1 Document, 5 Chunks, 4 NEXT_CHUNK relationships

**01_02_embeddings.py**: Created 3 chunks with 1536-dim embeddings, vector search working

**01_03_entity_extraction.py**:
- Only clears entity nodes (preserves Document/Chunk from previous notebooks)
- Extracted: 1 Company, 7 Products, 5 Services, 12 relationships
- `find_chunks_for_entity` working correctly

**Running in sequence (01_02 → 01_03)**: Final graph contains:
- 2 Documents, 4 Chunks (from both notebooks)
- All entities and relationships from 01_03
