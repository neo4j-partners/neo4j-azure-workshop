# Data Loading Workshop Notebooks - Proposal

## Overview

This document proposes a series of three introductory notebooks that teach the fundamentals of data loading, embedding generation, and entity extraction using the `neo4j-graphrag-python` library. These notebooks serve as **prerequisites** to the existing retriever and agent notebooks (02_xx and 03_xx series).

### Design Philosophy

- **Real data, limited scope**: Use actual SEC 10-K PDF files from the `data-pipeline`, but extract only a single page to keep execution fast
- **Incremental learning**: Each notebook builds on the previous one, introducing one new concept at a time
- **Hands-on simplicity**: Workshop participants should be able to run each cell and see results in under a minute
- **No production concerns**: Skip error handling, retry logic, and edge cases in favor of clarity

### Why Single-Page Processing?

The existing `data-pipeline` processes full SEC 10-K filings, which can take 10-30 minutes per document due to:
- PDF text extraction across 100+ pages
- Chunking into 4000-character segments
- LLM calls for entity extraction on each chunk
- Embedding generation for each chunk

For a workshop setting, processing a single page of real PDF data provides authentic experience while keeping execution time under 60 seconds. Participants work with real financial filings, not contrived examples.

---

## Notebook Series

### Notebook 01_01: Data Loading Fundamentals

**Purpose**: Introduce the basic concepts of loading text data into Neo4j and creating the document-chunk structure that forms the foundation of a knowledge graph.

**Learning Objectives**:
- Understand the relationship between documents and chunks
- Connect to Neo4j from a Jupyter notebook
- Load and extract text from a single PDF page
- Create Document and Chunk nodes
- Understand why we chunk text (context windows, retrieval granularity)
- Query the basic graph structure

**Data Source**:
A single page extracted from one of the SEC 10-K filings in `financial-data/form10k-sample/`. The first substantive page with company description text works well.

**Key Concepts Covered**:
- Neo4j driver connection and basic Cypher
- PDF text extraction using pypdf (single page)
- Document node with metadata (source path, page number)
- Chunk nodes with text content and index
- FROM_DOCUMENT relationship linking chunks to their source
- NEXT_CHUNK relationship for maintaining order

**What This Notebook Does NOT Cover**:
- Full PDF processing
- Automatic text splitting (manual chunking for clarity)
- Embeddings (next notebook)
- Entity extraction (third notebook)

---

### Notebook 01_02: Embeddings and Vector Search

**Purpose**: Demonstrate how to generate embeddings for text chunks extracted from a real PDF and perform vector similarity search using Neo4j's vector index.

**Learning Objectives**:
- Understand what embeddings are and why they matter for RAG
- Extract text from a single PDF page
- Split text into chunks using the neo4j-graphrag text splitter
- Generate embeddings using Azure OpenAI
- Store embedding vectors on Chunk nodes
- Create a vector index in Neo4j
- Perform similarity search to find relevant chunks

**Data Source**:
A single page from an SEC 10-K filing containing substantive business description or risk factor content. This provides enough text to create 2-4 meaningful chunks for demonstrating similarity search.

**Key Concepts Covered**:
- PDF single-page text extraction
- Text splitting with `FixedSizeSplitter` (smaller chunks for demo)
- Embedding models and vector dimensions
- The `AzureOpenAIEmbeddings` class from neo4j-graphrag
- Storing vectors as node properties
- Creating a vector index with `create_vector_index()`
- Basic vector similarity search with cosine distance
- Understanding similarity scores

**What This Notebook Does NOT Cover**:
- Hybrid search (keyword + vector)
- Multiple embedding models
- Full document processing
- Entity extraction (next notebook)

---

### Notebook 01_03: Entity Extraction Basics

**Purpose**: Show how to use an LLM to extract structured entities and relationships from real PDF text, completing the knowledge graph.

**Learning Objectives**:
- Understand the difference between lexical graphs (documents/chunks) and semantic graphs (entities/relationships)
- Define a schema with entity types and relationship types relevant to SEC filings
- Extract text from a single PDF page
- Use `SimpleKGPipeline` to extract entities from the text
- Write extracted entities to Neo4j
- Query the combined graph (chunks + entities)

**Data Source**:
A single page from an SEC 10-K filing that mentions company names, executives, products, or financial metrics. The "Business Overview" or "Risk Factors" sections typically contain rich entity content.

**Key Concepts Covered**:
- Schema definition with `NodeType` and `RelationshipType`
- Using a subset of the data-pipeline schema (Company, Executive, Product, RiskFactor)
- The extraction prompt and how the LLM interprets it
- `SimpleKGPipeline` with text input (extracted from PDF page)
- FROM_CHUNK relationships connecting entities to their source chunks
- Querying entities and their relationships

**What This Notebook Does NOT Cover**:
- Custom extraction prompts
- Entity resolution (merging duplicates)
- Full document processing
- Production error handling

---

## Data Source Strategy

All notebooks use the same SEC 10-K PDF files from `financial-data/form10k-sample/`:

1. **Consistent source**: Real SEC filings provide authentic financial/business content
2. **Single-page extraction**: Extract only one page per notebook to keep processing fast
3. **Page selection guidance**: Each notebook specifies which type of page content works best
4. **Predictable results**: SEC filings have consistent structure, making entity extraction verifiable

**Recommended PDF**: Apple's 10-K filing (`0000320193-23-000106.pdf`) is a good default because:
- Well-structured content
- Clear company/executive/product mentions
- Representative of typical SEC filing format

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
- `pypdf` for PDF text extraction
- Standard Jupyter environment

Environment variables needed:
- `NEO4J_URI`
- `NEO4J_USERNAME`
- `NEO4J_PASSWORD`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_AI_MODEL_NAME` (for entity extraction)
- `AZURE_AI_EMBEDDING_NAME` (for embeddings)

Data files needed:
- SEC 10-K PDFs in `financial-data/form10k-sample/` directory

---

## Success Criteria

Each notebook should:
- Execute completely in under 60 seconds
- Use real PDF data from the existing data-pipeline source
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
