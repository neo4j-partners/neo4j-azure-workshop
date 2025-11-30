# Neo4j GraphRAG Guide

This guide provides a comprehensive overview of the Neo4j GraphRAG framework, its role in modern AI applications, and a detailed walkthrough of how it is implemented in this workshop for processing financial data.

## What is Neo4j GraphRAG?

The `neo4j-graphrag-python` library is an official, open-source framework developed by Neo4j to simplify the creation of Graph-Augmented Generation (GraphRAG) applications. It provides a set of Python tools and abstractions that allow developers to orchestrate the flow of data between Large Language Models (LLMs), vector indexes, and the Neo4j graph database without writing complex, low-level code.

The framework serves as a bridge, translating unstructured text into structured knowledge and enabling sophisticated retrieval strategies that go beyond simple similarity matches. It is designed to be modular, allowing you to swap out different components—like the LLM provider, embedding model, or retrieval strategy—while maintaining a consistent workflow.

## The "Graph" in GraphRAG

Standard RAG (Retrieval-Augmented Generation) typically relies on **Vector Search**. It chunks documents, creates numerical embeddings, and retrieves chunks that are mathematically similar to a user's query. While powerful, this approach treats information as isolated fragments. It often struggles with questions that require reasoning across different documents or understanding complex relationships (e.g., "How do the risk factors of Company A compare to Company B?").

**GraphRAG** enhances this by adding a **Knowledge Graph**. A knowledge graph organizes data as nodes (entities like People, Companies, or Concepts) and relationships (connections like WORKS_FOR, LOCATED_IN, or FACES_RISK).

By combining these two approaches, the framework allows an AI application to:
1.  **Find** relevant text using vector search (Semantic Retrieval).
2.  **Traverse** relationships to find connected facts that might not use the same keywords (Graph Traversal).
3.  **Reason** about the structure of the data to provide more accurate and comprehensive answers.

## Key Capabilities

The framework provides several core capabilities that are utilized in this project:

### 1. Knowledge Graph Construction (The "Builder")
The framework includes pipelines for ingesting unstructured text. It uses an LLM to "read" the text and extract specific entities and relationships defined by your schema. This process automatically turns a folder of PDF documents into a rich, interconnected graph database. It handles the complexities of chunking text, prompting the LLM for extraction, and writing the results to Neo4j.

### 2. Hybrid Retrieval
Retrieval is the process of finding data to send to the LLM to answer a question. The framework supports **Hybrid Retrieval**, which combines:
*   **Vector Search:** Finding text based on meaning.
*   **Keyword Search:** Finding text based on exact matches (BM25).
*   **Graph Traversal:** Finding data based on relationships.

This multi-pronged approach ensures that the system doesn't miss important information just because it didn't use the exact right words or because the semantic similarity was slightly off.

### 3. Text-to-Cypher
For users who want to ask questions in plain English that require database queries (e.g., "List all companies with revenue over $1B"), the framework provides a **Text-to-Cypher** translator. It uses an LLM to convert natural language directly into Cypher, the query language for Neo4j, allowing for precise, analytical answers from the graph.

### 4. Entity Resolution
Real-world data is messy. A company might be referred to as "Apple", "Apple Inc.", or "Apple Computer, Inc.". The framework includes components for **Entity Resolution**, which helps identify and merge these duplicate records to ensure the knowledge graph remains clean and accurate.

---

## Implementation Overview

In this workshop, the library is used to process financial documents (SEC 10-K filings), extracting companies, executives, risks, and financial metrics to build a queryable knowledge base. The data processing pipeline transforms raw PDF documents into a rich knowledge graph through a series of orchestrated steps.

1.  **Document Loading**: The system reads PDF files from a specified directory.
2.  **Text Chunking**: Large documents are split into smaller, manageable text segments (chunks).
3.  **Embedding Generation**: Each text chunk is converted into a numerical vector (embedding) that represents its semantic meaning.
4.  **Entity Extraction**: An LLM analyzes each chunk to identify specific entities (like "Apple Inc" or "Tim Cook") and the relationships between them (like "Apple Inc HAS_EXECUTIVE Tim Cook").
5.  **Graph Construction**: These entities and relationships are structured according to a predefined schema and stored in the Neo4j database.
6.  **Resolution**: Duplicate entities (e.g., "Apple" and "Apple Inc.") are resolved to ensure a clean graph.

Once the graph is built, it supports advanced retrieval strategies that combine vector similarity with graph traversals.

## Implementation Guide

This project implements a specific pipeline tailored for financial data. Below is a guide to the key components and where to find them in the codebase.

### 1. Pipeline Configuration
The pipeline requires configuration for the Neo4j database connection, Azure OpenAI services (for LLM and embeddings), and file paths. This is managed through a centralized settings module that reads from environment variables.

*   **View the configuration logic**: [data-pipeline/pipeline/config.py](../data-pipeline/pipeline/config.py)

### 2. Schema Definition
Unlike a schema-less approach, this implementation defines a strict schema for the knowledge graph. This ensures that the LLM extracts specific types of nodes (e.g., Company, RiskFactor) and relationships (e.g., FACES_RISK). This schema is defined using Python objects that map directly to the graph structure.

*   **View the schema definitions**: [data-pipeline/pipeline/models.py](../data-pipeline/pipeline/models.py)

### 3. The Extraction Pipeline
The core of the ingestion process is the `SimpleKGPipeline`. This component orchestrates the LLM and the database driver. It takes the schema and the document as input and handles the complexity of prompting the LLM and parsing its response into graph elements.

*   **View the pipeline initialization and execution**: [data-pipeline/pipeline/main.py](../data-pipeline/pipeline/main.py)

### 4. Vector and Graph Search
The search functionality goes beyond simple keyword matching. It uses a "Retriever" pattern. specifically the `VectorCypherRetriever`. This allows the system to first find relevant text chunks using vector similarity and then traverse the graph to find related entities, providing a richer context for answering user queries.

*   **View the search implementation**: [data-pipeline/pipeline/search.py](../data-pipeline/pipeline/search.py)

## Performance Optimizations

To handle large datasets effectively, several performance improvements are recommended. These range from changing how files are processed to optimizing the database driver itself.

### 1. Concurrent File Processing
By default, files might be processed one after another. A high-impact optimization is to process multiple files simultaneously. This takes advantage of the time spent waiting for network responses from the LLM or database, significantly increasing the overall throughput of the pipeline.

*   **See recommendations on concurrency**: [IMPROVE_GRAPH.md](../IMPROVE_GRAPH.md)
*   **View current processing loop**: [data-pipeline/pipeline/main.py](../data-pipeline/pipeline/main.py)

### 2. Neo4j Driver Optimization
The standard Python driver for Neo4j is efficient, but for high-throughput data ingestion, switching to a Rust-backed extension can offer substantial speed improvements. This optimizes the serialization and deserialization of data moving between the application and the database.

*   **See driver recommendations**: [IMPROVE_GRAPH.md](../IMPROVE_GRAPH.md)

### 3. Strategic Indexing
Creating indexes is crucial for performance. Beyond the standard vector index, you should explicitly create indexes for entity names. This speeds up the process of checking if a node already exists before creating a new one, which is a frequent operation during data ingestion.

*   **See indexing strategies**: [IMPROVE_GRAPH.md](../IMPROVE_GRAPH.md)

### 4. Entity Resolution Strategy
Entity resolution—merging "Apple" and "Apple Inc"—can be expensive if done after every single document. A more performant approach is to defer this process. You can disable inline resolution during the ingestion phase and run a global resolution process once all data has been loaded. Additionally, using "fuzzy matching" can help identify and merge entities with slight spelling variations.

*   **See resolution strategies**: [IMPROVE_GRAPH.md](../IMPROVE_GRAPH.md)

### 5. Batching and Writing
The size of the data batches sent to the database impacts performance. If batches are too small, the network overhead becomes a bottleneck. Using a custom writer component allows you to increase the batch size, reducing the number of round-trips to the database.

*   **See batching recommendations**: [IMPROVE_GRAPH.md](../IMPROVE_GRAPH.md)

### 6. Hybrid Search
To improve retrieval quality, you can implement "Hybrid Search." This combines the semantic understanding of vector search with the precision of keyword matching (BM25). This is particularly useful for domain-specific terms or exact phrases that might be missed by vector models alone.

*   **See hybrid search details**: [IMPROVE_GRAPH.md](../IMPROVE_GRAPH.md)
*   **View current search logic**: [data-pipeline/pipeline/search.py](../data-pipeline/pipeline/search.py)