# Module 2: Simple Retrieval

## Overview

Now that you understand the fundamentals, let's build your first retrieval system! In this module, you'll learn how vector embeddings enable semantic search and how to combine it with language models for question answering.

**What you'll learn:**
- How vector embeddings represent semantic meaning
- Building VectorRetriever for similarity search
- Implementing GraphRAG patterns
- Evaluating and improving retrieval quality

**Estimated Time:** 60 minutes

## Prerequisites

- Completed Module 1 (environment setup)
- Neo4j database with loaded data
- Basic understanding of embeddings (we'll review)

**Reference Materials:**
- Notebook: `new-workshops/notebooks/01_01_vector_retriever.ipynb`
- Solution: `new-workshops/solutions/01_01_vector_retriever.py`

---

## Introduction to Vector-Based Semantic Search

### What Are Vector Embeddings?

Vector embeddings are numerical representations of text that capture semantic meaning. Similar concepts are close together in vector space, even if they use different words.

**Example:**

```
Text: "Apple releases new iPhone"
Embedding: [0.23, -0.15, 0.87, ..., 0.42]  # 1536 dimensions

Text: "Apple announces latest smartphone"
Embedding: [0.25, -0.14, 0.89, ..., 0.41]  # Very similar!

Text: "Cat sits on mat"
Embedding: [-0.67, 0.32, -0.15, ..., 0.89]  # Very different
```

**Key Properties:**

1. **Semantic Similarity**: Similar meaning → similar vectors
2. **High Dimensional**: Typically 384-1536 dimensions
3. **Dense**: Most values are non-zero
4. **Learned**: Created by neural networks trained on massive text corpora

### How Vector Search Works

1. **Indexing** (done once):
   ```python
   for chunk in document_chunks:
       embedding = model.embed(chunk.text)
       store_in_database(chunk, embedding)
   ```

2. **Querying** (at search time):
   ```python
   query = "What are Apple's AI products?"
   query_embedding = model.embed(query)
   
   # Find most similar chunks using cosine similarity
   results = vector_index.search(
       query_embedding,
       top_k=10
   )
   ```

3. **Similarity Calculation**:
   ```
   Cosine Similarity = (A · B) / (||A|| × ||B||)
   
   Range: -1 (opposite) to 1 (identical)
   Typical threshold: > 0.7 for relevant results
   ```

**Visual Representation:**

```
Vector Space (simplified to 2D)

              Query: "AI risks"
                     ✶
                    /|\
                   / | \
                  /  |  \
    "AI concerns" ●  |   ● "machine learning challenges"
                     |
              "supply chain" ●
                              \
                               ● "cloud products"
                               
Closer = More similar
```

### Why Vector Search Beats Keywords

**Query:** "What risks does Apple face with AI?"

**Keyword Search:**
```
❌ Matches: Exact text containing "risks", "Apple", "AI"
❌ Misses: "challenges", "concerns", "artificial intelligence"
❌ No ranking by relevance
```

**Vector Search:**
```
✅ Finds: Semantically similar content
✅ Matches: "AI challenges", "machine learning concerns", "algorithmic risks"
✅ Ranks by similarity score
✅ Works across paraphrasing
```

> **💡 Tip:** Vector search is particularly powerful for:
> - Questions vs. statements ("What is X?" matches "X is...")
> - Synonyms and paraphrasing
> - Multilingual search (with multilingual models)
> - Conceptual similarity

---

## Building Your First VectorRetriever

Let's build a retrieval system using the `neo4j-graphrag` library.

### Understanding the VectorRetriever

The `VectorRetriever` from `neo4j-graphrag` provides a simple interface for vector search:

```python
from neo4j_graphrag.retrievers import VectorRetriever

retriever = VectorRetriever(
    driver=neo4j_driver,           # Neo4j connection
    index_name="chunkEmbeddings",  # Vector index name
    embedder=embedder,             # Embedding model
    return_properties=["text"]     # Properties to return
)
```

**Components:**

1. **Driver**: Neo4j connection for queries
2. **Index**: Pre-built vector index on `Chunk.embedding`
3. **Embedder**: Model to convert query text to vectors
4. **Return Properties**: Which node properties to retrieve

### Step-by-Step Implementation

Let's build a complete example. Follow along in the notebook or create a new Python file.

#### Step 1: Import Dependencies

```python
"""
Vector Retriever Demo

This workshop demonstrates basic semantic search using VectorRetriever
and GraphRAG from neo4j-graphrag-python.
"""

from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.retrievers import VectorRetriever

from config import get_embedder, get_llm, get_neo4j_driver
```

#### Step 2: Create the Retriever

```python
def create_vector_retriever(driver, embedder) -> VectorRetriever:
    """Create a VectorRetriever for semantic search."""
    return VectorRetriever(
        driver=driver,
        index_name="chunkEmbeddings",
        embedder=embedder,
        return_properties=["text"],
    )
```

**What's happening:**
- `index_name`: Points to the Neo4j vector index on `Chunk` nodes
- `embedder`: Azure OpenAI embedding model (text-embedding-ada-002)
- `return_properties`: We want the chunk text, not just IDs

> **📝 Note:** The index "chunkEmbeddings" was created during database restore. It indexes the `embedding` property of `Chunk` nodes.

#### Step 3: Perform Vector Search

```python
def demo_vector_search(retriever: VectorRetriever, query: str) -> None:
    """Demo direct vector search without LLM."""
    print(f"\n--- Direct Vector Search ---")
    print(f"Query: {query}\n")
    
    # Search returns a RetrieverResult object
    results = retriever.search(query_text=query, top_k=10)
    
    # Iterate through items
    for item in results.items:
        # Get similarity score
        score = item.metadata.get("score", 0)
        
        # Get first 100 chars of content
        content_preview = item.content[:100] if item.content else ""
        
        print(f"Score: {score:.4f}, Content: {content_preview}...")
```

**What's happening:**
1. Call `retriever.search()` with query text and top_k
2. Get back `RetrieverResult` with items
3. Each item has:
   - `content`: The chunk text
   - `metadata`: Dict with score, node info, etc.

**Run it:**

```python
with get_neo4j_driver() as driver:
    embedder = get_embedder()
    retriever = create_vector_retriever(driver, embedder)
    
    demo_vector_search(retriever, "What are the risks that Apple faces?")
```

**Expected Output:**
```
--- Direct Vector Search ---
Query: What are the risks that Apple faces?

Score: 0.8523, Content: Apple faces significant risks related to supply chain disruptions. The company's reliance...
Score: 0.8234, Content: Competition in the smartphone market poses risks to Apple's iPhone business. Market share...
Score: 0.8156, Content: Regulatory challenges in multiple jurisdictions could impact Apple's operations. The compan...
...
```

> **💡 Tip:** Scores above 0.80 typically indicate highly relevant results. Below 0.70 may be less relevant.

---

## Implementing GraphRAG for Q&A

Direct vector search returns chunks, but users want *answers*. GraphRAG combines retrieval with generation.

### What is GraphRAG?

**GraphRAG = Graph-based Retrieval Augmented Generation**

It's a pattern that:
1. **Retrieves** relevant information from a graph
2. **Augments** the LLM's context with retrieved data
3. **Generates** a natural language answer

```
Query: "What AI products does Microsoft offer?"
              │
              ▼
      ┌───────────────┐
      │ VectorRetriever│
      └───────┬───────┘
              │ Returns chunks mentioning Microsoft + AI
              ▼
    "Microsoft offers Azure AI..."
    "Copilot is integrated in Office..."
    "Azure OpenAI Service provides..."
              │
              ▼
      ┌───────────────┐
      │   LLM (GPT-4o)│
      └───────┬───────┘
              │ Synthesizes answer from chunks
              ▼
    "Microsoft offers several AI products:
     1. Azure AI Services...
     2. Microsoft Copilot...
     3. Azure OpenAI Service..."
```

### Implementing GraphRAG

The `neo4j-graphrag` library provides a `GraphRAG` class:

```python
from neo4j_graphrag.generation import GraphRAG

rag = GraphRAG(
    llm=llm,              # Language model for generation
    retriever=retriever   # Retriever for context
)

response = rag.search(query)
print(response.answer)
```

**Complete Example:**

```python
def demo_rag_search(llm, retriever: VectorRetriever, query: str) -> None:
    """Demo RAG search with LLM answer generation."""
    print(f"\n--- RAG Search ---")
    print(f"Query: {query}\n")
    
    # Create GraphRAG with LLM + retriever
    rag = GraphRAG(llm=llm, retriever=retriever)
    
    # Search returns a RagResultModel
    response = rag.search(query)
    
    # Access the generated answer
    print(f"Answer: {response.answer}")
```

**Run it:**

```python
with get_neo4j_driver() as driver:
    embedder = get_embedder()
    llm = get_llm()
    retriever = create_vector_retriever(driver, embedder)
    
    demo_rag_search(
        llm, 
        retriever, 
        "What companies mention AI in their filings?"
    )
```

**Expected Output:**
```
--- RAG Search ---
Query: What companies mention AI in their filings?

Answer: Based on the financial filings in the database, several companies mention artificial intelligence (AI) in their reports:

1. Microsoft: Discusses AI extensively in Azure AI Services and Copilot integration
2. Apple: References machine learning in product development and Siri improvements
3. Amazon: Mentions AI in AWS services and Alexa development
4. Google (Alphabet): Covers AI research, DeepMind, and integration across products
5. NVIDIA: Focuses on AI computing platforms and data center GPUs

These companies view AI as a strategic priority for product development and competitive advantage.
```

> **💡 Tip:** The LLM synthesizes information from multiple chunks, providing a coherent answer that no single chunk contains.

### How GraphRAG Works Internally

Let's peek under the hood:

```python
# Simplified pseudocode of what GraphRAG does

def search(query):
    # 1. Retrieve relevant chunks
    retriever_results = retriever.search(query, top_k=10)
    
    # 2. Format as context
    context = "\n\n".join([
        f"Chunk {i}: {item.content}"
        for i, item in enumerate(retriever_results.items)
    ])
    
    # 3. Create prompt with context
    prompt = f"""
    Answer the question based on the following context.
    
    Context:
    {context}
    
    Question: {query}
    
    Answer:
    """
    
    # 4. Generate answer
    response = llm.invoke(prompt)
    
    return response.content
```

**Key Points:**

- **Context Window**: Limited by LLM (e.g., 128k tokens for GPT-4o)
- **Top K**: More chunks = more context but higher cost
- **Ranking**: Better retrieval = better answers
- **Synthesis**: LLM combines information across chunks

---

## Testing Retrieval Quality with Diagnostic Queries

Good retrieval is crucial for good answers. Let's test our system.

### Diagnostic Query Suite

Create diverse queries to test different aspects:

```python
diagnostic_queries = [
    # Factual queries
    "What products does Apple offer?",
    "Who are Microsoft's executives?",
    
    # Risk analysis
    "What supply chain risks does NVIDIA face?",
    "What regulatory challenges affect Amazon?",
    
    # Comparison queries
    "Compare Google and Microsoft's AI strategies",
    
    # Specific details
    "What is Apple's revenue from iPhone sales?",
    
    # Abstract concepts
    "How do tech companies view sustainability?",
]
```

### Evaluation Criteria

For each query, evaluate:

1. **Relevance**: Do retrieved chunks relate to the query?
2. **Coverage**: Do chunks contain information to answer fully?
3. **Ranking**: Are most relevant chunks ranked highest?
4. **Diversity**: Do chunks come from different sources?

### Running Diagnostic Tests

```python
def evaluate_retrieval(retriever: VectorRetriever, queries: list[str]) -> None:
    """Evaluate retrieval quality across multiple queries."""
    for query in queries:
        print(f"\nQuery: {query}")
        print("-" * 60)
        
        results = retriever.search(query_text=query, top_k=5)
        
        for i, item in enumerate(results.items, 1):
            score = item.metadata.get("score", 0)
            preview = item.content[:80] if item.content else ""
            
            # Simple relevance indicator
            relevance = "🟢" if score > 0.8 else "🟡" if score > 0.7 else "🔴"
            
            print(f"{relevance} {i}. Score: {score:.4f}")
            print(f"   {preview}...")
```

**Example Output:**
```
Query: What supply chain risks does NVIDIA face?
------------------------------------------------------------
🟢 1. Score: 0.8734
   NVIDIA's supply chain is heavily dependent on Taiwan-based manufacturers...
🟢 2. Score: 0.8523
   The company faces risks from semiconductor shortages that could impact...
🟡 3. Score: 0.7856
   Global logistics challenges affect the distribution of NVIDIA products...
🟡 4. Score: 0.7645
   Competition in the GPU market poses challenges for maintaining market...
🔴 5. Score: 0.6892
   NVIDIA's financial performance in Q4 showed strong growth in datacenter...
```

**Analysis:**
- ✅ Top 2 results highly relevant (supply chain focus)
- ✅ Result 3 relevant but broader (logistics)
- ⚠️ Result 4 tangentially relevant (competition, not supply chain)
- ❌ Result 5 not relevant (financial performance, not risks)

> **💡 Tip:** If you see low scores (< 0.7) in top results, consider:
> - Adjusting query phrasing
> - Increasing top_k to get more candidates
> - Using hybrid search (Module 3)

### Common Retrieval Issues

**Issue 1: Query-Chunk Mismatch**

```python
# Query uses different terms than documents
query = "What are NVIDIA's AI chips?"
# Chunks say "GPUs" or "data center processors"
# Solution: Rephrase or use multiple queries
```

**Issue 2: Too Broad**

```python
# Query is too general
query = "Tell me about Apple"
# Returns random chunks from various sections
# Solution: Be more specific
```

**Issue 3: Too Specific**

```python
# Query asks for detail not in chunks
query = "What was Apple's Q3 2023 iPhone revenue in Japan?"
# Chunks might have yearly data, or US data, but not that specific
# Solution: Ask progressively or use multiple queries
```

### Best Practices

1. **Start Broad, Then Narrow**: 
   - First: "What products does Apple offer?"
   - Then: "Tell me more about the iPhone"

2. **Use Natural Language**: Write queries as you'd ask a person

3. **Iterate on Query Phrasing**: Try synonyms if results aren't good

4. **Check Scores**: Consistently low scores indicate query issues

5. **Balance Top K**: 
   - Too few (k=3): Might miss relevant info
   - Too many (k=20): Adds noise and cost

---

## Hands-On Exercises

Now it's your turn! Complete these exercises to reinforce your learning.

### Exercise 1: Basic Retrieval

**Task:** Create a retriever and test with custom queries.

```python
# TODO: Import necessary modules

# TODO: Create Neo4j driver

# TODO: Create embedder

# TODO: Create VectorRetriever

# TODO: Test with 3 queries of your choice

# TODO: Print results with scores
```

**Success Criteria:**
- Retriever successfully returns results
- Scores are reasonable (> 0.7 for relevant)
- You understand what each result contains

<details>
<summary>💡 Hint</summary>

```python
from config import get_embedder, get_neo4j_driver
from neo4j_graphrag.retrievers import VectorRetriever

with get_neo4j_driver() as driver:
    embedder = get_embedder()
    retriever = VectorRetriever(
        driver=driver,
        index_name="chunkEmbeddings",
        embedder=embedder,
        return_properties=["text"]
    )
    
    query = "Your query here"
    results = retriever.search(query_text=query, top_k=5)
    
    for item in results.items:
        print(f"Score: {item.metadata.get('score'):.4f}")
        print(f"Text: {item.content[:100]}...")
        print()
```
</details>

### Exercise 2: GraphRAG Q&A

**Task:** Build a complete Q&A system with GraphRAG.

```python
# TODO: Create LLM instance

# TODO: Create VectorRetriever

# TODO: Create GraphRAG instance

# TODO: Ask 3 questions and print answers

# TODO: Compare answers to direct retrieval results
```

**Questions to Try:**
1. "What risks do semiconductor companies face?"
2. "Which companies invest heavily in cloud infrastructure?"
3. "How do tech companies approach data privacy?"

**Success Criteria:**
- GraphRAG generates coherent answers
- Answers cite information from multiple chunks
- Answers are more complete than any single chunk

<details>
<summary>💡 Hint</summary>

```python
from neo4j_graphrag.generation import GraphRAG
from config import get_embedder, get_llm, get_neo4j_driver

with get_neo4j_driver() as driver:
    embedder = get_embedder()
    llm = get_llm()
    retriever = VectorRetriever(...)
    
    rag = GraphRAG(llm=llm, retriever=retriever)
    
    response = rag.search("Your question")
    print(response.answer)
```
</details>

### Exercise 3: Query Optimization

**Task:** Test how query phrasing affects retrieval.

Test these variations:
```python
queries = [
    "Apple risks",
    "What risks does Apple face?",
    "Tell me about challenges and concerns for Apple Inc.",
    "Apple company risk factors and potential problems"
]
```

**For each query:**
1. Run retrieval with top_k=5
2. Note the average score
3. Check if the same chunks appear
4. Assess which query works best

**Success Criteria:**
- You understand how query phrasing impacts results
- You can identify which query style works best
- You know when to rephrase queries

### Exercise 4: Retrieval Evaluation

**Task:** Create your own diagnostic queries and evaluate them.

```python
# TODO: Create 5 queries covering different topics

# TODO: For each query:
#   - Run retrieval
#   - Check scores
#   - Assess relevance
#   - Note any issues

# TODO: Summarize findings
```

**Topics to Cover:**
- Company information
- Product details
- Risk factors
- Financial metrics
- Executive information

**Success Criteria:**
- You can identify good vs. poor retrieval
- You understand when vector search works well
- You know the limitations of this approach

---

## Summary

Congratulations! You've built your first semantic search and RAG system. Let's recap:

### Key Concepts

✅ **Vector Embeddings**
- Represent text as high-dimensional vectors
- Capture semantic meaning, not just keywords
- Enable similarity search in vector space

✅ **VectorRetriever**
- Converts queries to embeddings
- Searches vector index in Neo4j
- Returns ranked results by similarity

✅ **GraphRAG Pattern**
- Retrieves relevant context from graph
- Augments LLM with retrieved information
- Generates comprehensive answers

✅ **Evaluation**
- Test with diverse diagnostic queries
- Check relevance scores and ranking
- Iterate on query phrasing

### Limitations of Vector-Only Search

While powerful, vector search alone has limitations:

1. **No Relationship Awareness**: Doesn't leverage graph structure
2. **Chunk Boundaries**: Information split across chunks is harder to find
3. **No Structured Queries**: Can't express precise graph patterns
4. **Limited Context**: Only retrieves individual chunks

**Good news:** Module 3 addresses these by enhancing retrieval with graph relationships!

### What's Next

In [**Module 3: Advanced Graph Retrieval**](03_advanced_graph_retrieval.md), you'll learn:
- How to enrich context with graph traversal
- Building Vector + Cypher hybrid retrievers
- Generating Cypher queries from natural language
- When to use each retrieval strategy

### Quick Reference

**Create VectorRetriever:**
```python
from neo4j_graphrag.retrievers import VectorRetriever

retriever = VectorRetriever(
    driver=driver,
    index_name="chunkEmbeddings",
    embedder=embedder,
    return_properties=["text"]
)
```

**Perform Search:**
```python
results = retriever.search(query_text="...", top_k=10)
for item in results.items:
    print(item.content)
    print(item.metadata["score"])
```

**GraphRAG:**
```python
from neo4j_graphrag.generation import GraphRAG

rag = GraphRAG(llm=llm, retriever=retriever)
response = rag.search("Your question")
print(response.answer)
```

---

Ready to enhance retrieval with graph structure? Continue to [**Module 3: Advanced Graph Retrieval**](03_advanced_graph_retrieval.md)!
