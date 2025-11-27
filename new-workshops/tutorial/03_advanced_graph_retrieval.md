# Module 3: Advanced Graph Retrieval

## Overview

Vector search is powerful, but it only looks at individual chunks. Real-world questions often require understanding *relationships* between entities. In this module, you'll learn how to combine vector search with graph traversal and how to generate structured queries from natural language.

**What you'll learn:**
- Enriching context with graph relationships
- Building Vector + Cypher hybrid retrievers
- Generating Cypher queries from natural language
- Comparing and choosing retrieval strategies

**Estimated Time:** 90 minutes

## Prerequisites

- Completed Modules 1 & 2
- Understanding of vector search
- Basic knowledge of Cypher (helpful but not required)

**Reference Materials:**
- Notebook: `new-workshops/notebooks/01_02_vector_cypher_retriever.ipynb`
- Notebook: `new-workshops/notebooks/01_03_text2cypher_retriever.ipynb`
- Solutions: `new-workshops/solutions/01_02_*.py` and `01_03_*.py`

---

## Part 1: Vector + Cypher Retriever

### Theory: Why Graphs Enhance Retrieval

Vector search finds similar text chunks, but it doesn't understand the **connections** between entities. Let's see why this matters.

**Example Query:** "What risks does Apple face?"

**Vector Search Result:**
```
Chunk 1 (Score: 0.85):
"Supply chain disruptions could impact operations. Dependence on 
manufacturing partners in Asia creates vulnerability..."

Chunk 2 (Score: 0.82):
"Regulatory compliance across multiple jurisdictions requires significant
resources. Changes in data privacy laws could affect..."
```

**What's Missing:**
- Which specific risk categories these fall under
- How these risks compare to other companies
- The structured relationship: (Apple)-[:FACES_RISK]->(RiskFactor)

### Enriching Context with Graph Relationships

The **VectorCypherRetriever** combines vector similarity with graph traversal:

```
1. Find similar chunks (vector search)
        ↓
2. Traverse graph to enrich context (Cypher)
        ↓
3. Return enhanced results
```

**Architecture:**

```
Query: "Apple's AI risks"
        ↓
┌───────────────────────┐
│  Vector Search        │  Find chunks about Apple + AI + risks
│  (chunkEmbeddings)    │
└───────┬───────────────┘
        │ Returns: Chunk nodes
        ▼
┌───────────────────────┐
│  Custom Cypher Query  │  MATCH (chunk)-[:FROM_DOCUMENT]->(doc)
│  (Graph Traversal)    │        -[:FILED]-(company:Company)
│                       │        -[:FACES_RISK]->(risk:RiskFactor)
└───────┬───────────────┘
        │ Returns: chunk.text + company.name + risk.name
        ▼
   Enriched Context with Relationships
```

> **💡 Key Insight:** We use vector search to find *where* to look, then use Cypher to enrich *what* we return.

### Building Your First Vector + Cypher Retriever

Let's implement a retriever that finds chunks and adds company + risk factor context.

#### Step 1: Define the Retrieval Query

```python
"""
This Cypher query runs for each chunk found by vector search.
The 'node' variable represents the chunk from vector search.
"""

COMPANY_RISK_QUERY = """
MATCH (node)-[:FROM_DOCUMENT]-(doc:Document)
      -[:FILED]-(company:Company)
      -[:FACES_RISK]->(risk:RiskFactor)
RETURN 
    company.name AS company, 
    collect(DISTINCT risk.name) AS risks, 
    node.text AS context
"""
```

**What This Does:**

1. Starts from the `node` (chunk found by vector search)
2. Traverses to the Document that contains it
3. Finds the Company that filed the document
4. Collects all RiskFactors the company faces
5. Returns company name, risk list, and original chunk text

**Graph Pattern:**

```
(node:Chunk)-[:FROM_DOCUMENT]->(doc:Document)
       ↓
(company:Company)-[:FILED]->(doc)
       ↓
(company)-[:FACES_RISK]->(risk:RiskFactor)
```

#### Step 2: Create the Retriever

```python
from neo4j_graphrag.retrievers import VectorCypherRetriever

def create_vector_cypher_retriever(
    driver, 
    embedder, 
    retrieval_query: str
) -> VectorCypherRetriever:
    """Create a VectorCypherRetriever with custom retrieval query."""
    return VectorCypherRetriever(
        driver=driver,
        index_name="chunkEmbeddings",
        embedder=embedder,
        retrieval_query=retrieval_query,
    )
```

**Parameters:**
- `driver`: Neo4j connection
- `index_name`: Same vector index as before
- `embedder`: Embedding model
- `retrieval_query`: Custom Cypher to enrich results

#### Step 3: Use with GraphRAG

```python
def demo_retriever(llm, retriever, query: str) -> None:
    """Demo retriever with RAG."""
    print(f"Query: {query}\n")
    
    rag = GraphRAG(llm=llm, retriever=retriever)
    
    # retriever_config passes options to the retriever
    response = rag.search(
        query, 
        retriever_config={"top_k": 5},
        return_context=True  # Include retrieved items in response
    )
    
    print(f"Answer: {response.answer}\n")
    print(f"Context items retrieved: {len(response.retriever_result.items)}")
```

**Run It:**

```python
with get_neo4j_driver() as driver:
    embedder = get_embedder()
    llm = get_llm()
    
    retriever = create_vector_cypher_retriever(
        driver, 
        embedder, 
        COMPANY_RISK_QUERY
    )
    
    demo_retriever(
        llm,
        retriever,
        "What are the top risk factors that Apple faces?"
    )
```

**Expected Output:**

```
Query: What are the top risk factors that Apple faces?

Answer: Apple faces several significant risk factors according to their SEC filings:

1. Supply Chain Risks: Heavy dependence on manufacturing partners in Asia, particularly Taiwan and China, creates vulnerability to geopolitical tensions and disruptions.

2. Regulatory Risks: Compliance with data privacy laws (GDPR, CCPA) and antitrust scrutiny in multiple jurisdictions.

3. Competition Risks: Intense competition in smartphone market from Samsung, Google, and Chinese manufacturers.

4. Technology Risks: Rapid technological changes requiring continuous innovation and significant R&D investment.

5. Cybersecurity Risks: Protecting customer data and defending against sophisticated cyber attacks.

Context items retrieved: 5
```

> **💡 Notice:** The answer now includes structured risk categories and specific mentions of regulatory frameworks, showing the enriched context from graph traversal.

### More Complex Retrieval Queries

#### Query 2: Asset Manager Context

Find chunks and include information about which asset managers own shares in the company:

```python
ASSET_MANAGER_QUERY = """
MATCH (node)-[:FROM_DOCUMENT]-(doc:Document)
      -[:FILED]-(company:Company)
      -[:OWNS]-(manager:AssetManager)
RETURN 
    company.name AS company, 
    manager.managerName AS asset_manager, 
    node.text AS context
"""
```

**Use Case:** "Which institutional investors own Apple stock?"

#### Query 3: Shared Risks Between Companies

Find companies that face similar risks:

```python
SHARED_RISKS_QUERY = """
WITH node
MATCH (node)-[:FROM_DOCUMENT]-(doc:Document)
      -[:FILED]-(c1:Company)
MATCH (c1)-[:FACES_RISK]->(risk:RiskFactor)
      <-[:FACES_RISK]-(c2:Company)
WHERE c1 <> c2
RETURN
    c1.name AS source_company,
    collect(DISTINCT c2.name) AS related_companies,
    collect(DISTINCT risk.name) AS shared_risks
LIMIT 10
"""
```

**Use Case:** "Which companies face similar supply chain risks as NVIDIA?"

### Comparing Simple vs. Graph-Enhanced Results

Let's compare side-by-side:

**Query:** "What products does Microsoft offer?"

**VectorRetriever (Simple):**
```
Returns: Text chunks mentioning Microsoft products
Context: Just the chunk text

"Microsoft offers Azure cloud platform..."
"Office 365 subscription service..."
"Surface devices including laptops..."
```

**VectorCypherRetriever (Enhanced):**
```
Returns: Text chunks + product nodes + relationships
Context: Chunk text + structured product list + categories

Chunk: "Microsoft offers Azure cloud platform..."
Products: [Azure, Azure AI, Azure OpenAI Service]
Category: Cloud Services
Company: Microsoft

Chunk: "Office 365 subscription service..."
Products: [Office 365, Microsoft 365, Teams]
Category: Productivity
Company: Microsoft
```

**Result:**
- ✅ Richer context for LLM
- ✅ Structured information alongside text
- ✅ Better understanding of relationships
- ✅ More accurate and complete answers

---

## Part 2: Text-to-Cypher Retriever

### Natural Language to Cypher Translation

Sometimes users ask questions that map naturally to graph patterns:

- "Which executives work at Apple?" → Graph pattern
- "Show me companies that offer cloud products" → Graph pattern
- "What risks do tech companies share?" → Graph pattern

Instead of searching text, we can translate natural language to **Cypher queries** and execute them directly against the graph.

### How Text2Cypher Works

```
User Question: "Which companies offer cloud products?"
        ↓
┌────────────────────────┐
│  LLM (GPT-4o)         │  Generates Cypher based on:
│  + Schema Context     │  - Database schema
│  + Examples          │  - Question semantics
└────────┬───────────────┘  - Example queries
        │
        ▼
   Generated Cypher Query
        │
        ▼
┌────────────────────────┐
│  Neo4j Database       │  MATCH (c:Company)-[:OFFERS]->(p:Product)
│                       │  WHERE p.name CONTAINS 'cloud'
└────────┬───────────────┘  RETURN c.name, collect(p.name)
        │
        ▼
   Structured Results
        │
        ▼
┌────────────────────────┐
│  LLM Synthesis        │  Formats results into natural language
└────────┬───────────────┘
        │
        ▼
   "Microsoft and Amazon offer cloud products:
    Microsoft: Azure, Azure AI Services
    Amazon: AWS, EC2, S3"
```

### Building a Text2Cypher Retriever

The `Text2CypherRetriever` handles the translation:

```python
from neo4j_graphrag.retrievers import Text2CypherRetriever
from neo4j_graphrag.schema import get_schema

# Get database schema for context
schema = get_schema(driver)

retriever = Text2CypherRetriever(
    driver=driver,
    llm=llm,  # LLM for Cypher generation
    neo4j_schema=schema,  # Schema context
)
```

**Parameters:**
- `driver`: Neo4j connection
- `llm`: LLM to generate Cypher
- `neo4j_schema`: Database schema string (nodes, relationships, properties)

### Complete Example

```python
from neo4j_graphrag.retrievers import Text2CypherRetriever
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.schema import get_schema

def demo_text2cypher(driver, llm, query: str) -> None:
    """Demo Text2Cypher retrieval."""
    print(f"\nQuery: {query}\n")
    
    # Get schema for context
    schema = get_schema(driver)
    
    # Create retriever
    retriever = Text2CypherRetriever(
        driver=driver,
        llm=llm,
        neo4j_schema=schema,
    )
    
    # Use with GraphRAG
    rag = GraphRAG(llm=llm, retriever=retriever)
    response = rag.search(query, return_context=True)
    
    print(f"Answer: {response.answer}\n")
    
    # Show generated Cypher (if available in metadata)
    if response.retriever_result.items:
        print("Generated Cypher queries executed successfully")
```

**Run It:**

```python
with get_neo4j_driver() as driver:
    llm = get_llm()
    
    demo_text2cypher(
        driver,
        llm,
        "Which executives work at Apple?"
    )
```

**Expected Output:**

```
Query: Which executives work at Apple?

Answer: Based on the database, the following executives work at Apple:

1. Tim Cook - CEO
2. Luca Maestri - CFO
3. Jeff Williams - COO
4. Katherine Adams - General Counsel
5. Deirdre O'Brien - Senior VP of Retail

These executives hold key leadership positions in the company.

Generated Cypher queries executed successfully
```

### Behind the Scenes

The LLM generated something like:

```cypher
MATCH (c:Company {name: "Apple"})-[:HAS_EXECUTIVE]->(e:Executive)
RETURN e.name, e.title
```

Then formatted the results into natural language.

### Handling Complex Graph Patterns

Text2Cypher excels at complex relationships:

**Query:** "Which companies share risk factors with NVIDIA?"

**Generated Cypher:**
```cypher
MATCH (c1:Company {name: "NVIDIA"})-[:FACES_RISK]->(r:RiskFactor)
      <-[:FACES_RISK]-(c2:Company)
WHERE c1 <> c2
RETURN DISTINCT c2.name AS company, 
       collect(DISTINCT r.name) AS shared_risks
```

**Query:** "What products are offered by companies that also offer AI services?"

**Generated Cypher:**
```cypher
MATCH (c:Company)-[:OFFERS]->(p1:Product)
WHERE p1.name CONTAINS 'AI'
MATCH (c)-[:OFFERS]->(p2:Product)
RETURN c.name AS company, 
       collect(DISTINCT p2.name) AS all_products
```

### Error Handling and Validation

Text2Cypher can generate invalid queries. The library handles this:

```python
try:
    response = rag.search(query)
    print(response.answer)
except Exception as e:
    print(f"Query failed: {e}")
    print("Try rephrasing your question.")
```

**Common Issues:**

1. **Ambiguous Questions**: "Tell me about Apple"
   - Solution: Be more specific

2. **Non-existent Relationships**: "Show me Apple's suppliers"
   - Solution: Check schema, rephrase if relationship doesn't exist

3. **Complex Logic**: "Compare Q1 to Q2 revenue growth rates"
   - Solution: Break into simpler queries

> **💡 Tip:** Text2Cypher works best for well-structured questions about relationships. Use vector search for semantic/conceptual queries.

---

## Hands-On Exercises: Comparing Retrieval Strategies

Now let's compare all three approaches.

### Exercise 1: Side-by-Side Comparison

**Task:** Compare VectorRetriever, VectorCypherRetriever, and Text2CypherRetriever on the same query.

```python
from neo4j_graphrag.retrievers import (
    VectorRetriever,
    VectorCypherRetriever,
    Text2CypherRetriever
)
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.schema import get_schema

def compare_retrievers(query: str):
    """Compare all three retriever types."""
    
    with get_neo4j_driver() as driver:
        embedder = get_embedder()
        llm = get_llm()
        schema = get_schema(driver)
        
        # 1. Vector Retriever
        print("=== VectorRetriever ===")
        retriever1 = VectorRetriever(
            driver=driver,
            index_name="chunkEmbeddings",
            embedder=embedder,
            return_properties=["text"]
        )
        rag1 = GraphRAG(llm=llm, retriever=retriever1)
        response1 = rag1.search(query)
        print(f"Answer: {response1.answer}\n")
        
        # 2. Vector Cypher Retriever
        print("=== VectorCypherRetriever ===")
        cypher_query = """
        MATCH (node)-[:FROM_DOCUMENT]-(doc:Document)
              -[:FILED]-(company:Company)
        RETURN company.name AS company, node.text AS context
        """
        retriever2 = VectorCypherRetriever(
            driver=driver,
            index_name="chunkEmbeddings",
            embedder=embedder,
            retrieval_query=cypher_query
        )
        rag2 = GraphRAG(llm=llm, retriever=retriever2)
        response2 = rag2.search(query)
        print(f"Answer: {response2.answer}\n")
        
        # 3. Text2Cypher Retriever
        print("=== Text2CypherRetriever ===")
        retriever3 = Text2CypherRetriever(
            driver=driver,
            llm=llm,
            neo4j_schema=schema
        )
        rag3 = GraphRAG(llm=llm, retriever=retriever3)
        response3 = rag3.search(query)
        print(f"Answer: {response3.answer}\n")

# Test it
compare_retrievers("What products does Apple offer?")
```

**Analyze:**
- Which retriever gave the most accurate answer?
- Which included the most detail?
- Which was most appropriate for this question?

### Exercise 2: Choose the Right Retriever

For each query below, identify which retriever type is most appropriate:

```python
queries = [
    "What are the main risks Apple discusses in their filings?",
    # Answer: VectorRetriever or VectorCypherRetriever
    # Reason: Semantic search in text
    
    "Which companies have Tim Cook as an executive?",
    # Answer: Text2CypherRetriever
    # Reason: Direct relationship query
    
    "Compare Microsoft and Google's AI strategies",
    # Answer: VectorRetriever or VectorCypherRetriever
    # Reason: Semantic comparison of strategies
    
    "Show me all products offered by tech companies",
    # Answer: Text2CypherRetriever
    # Reason: Structured query for all products
    
    "What do companies say about climate change?",
    # Answer: VectorRetriever
    # Reason: Semantic search for concept
]
```

**Success Criteria:**
- You understand when to use each retriever type
- You can justify your choices
- You know the strengths and limitations of each

### Exercise 3: Custom Retrieval Query

**Task:** Create your own VectorCypherRetriever query.

**Scenario:** You want to find chunks about products and also include:
- The company that offers the product
- The product category
- Any executives associated with the product line

```python
# TODO: Write the Cypher query
CUSTOM_QUERY = """
# Your query here
"""

# TODO: Create retriever
# TODO: Test with a query
# TODO: Evaluate results
```

<details>
<summary>💡 Hint</summary>

```python
CUSTOM_QUERY = """
MATCH (node)-[:FROM_DOCUMENT]-(doc:Document)
      -[:FILED]-(company:Company)
MATCH (company)-[:OFFERS]->(product:Product)
OPTIONAL MATCH (company)-[:HAS_EXECUTIVE]->(exec:Executive)
RETURN 
    company.name AS company,
    collect(DISTINCT product.name) AS products,
    collect(DISTINCT exec.name) AS executives,
    node.text AS context
"""
```
</details>

### Exercise 4: Text2Cypher Edge Cases

**Task:** Test Text2Cypher with challenging queries.

```python
challenging_queries = [
    "Show me everything",  # Too vague
    "Which companies have the most products?",  # Requires aggregation
    "Find products with 'AI' in the name",  # String matching
    "Which executives manage cloud products?",  # Complex relationship
]

# For each query:
# 1. Try with Text2CypherRetriever
# 2. Note if it succeeds or fails
# 3. If it fails, suggest a better phrasing
# 4. Determine if vector search would be better
```

**Success Criteria:**
- You understand Text2Cypher limitations
- You can identify queries that won't work well
- You know when to use alternative approaches

---

## Decision Framework: Which Retriever to Use?

Use this framework to choose the right retriever:

```
┌─────────────────────────────────────┐
│  Start: User Query                  │
└────────────┬────────────────────────┘
             │
             ▼
    ┌────────────────────┐
    │ Is the query about │  YES ──> Text2CypherRetriever
    │ specific entities  │          "Which executives at Apple?"
    │ or relationships?  │          "Show me all products"
    └────────┬───────────┘
             │ NO
             ▼
    ┌────────────────────┐
    │ Does the query     │  YES ──> VectorCypherRetriever
    │ benefit from graph │          "Apple's supply chain risks"
    │ relationships?     │          "Microsoft's cloud offerings"
    └────────┬───────────┘
             │ NO
             ▼
    ┌────────────────────┐
    │ Is it a semantic   │  YES ──> VectorRetriever
    │ or conceptual      │          "How do companies view AI?"
    │ question?          │          "Compare risk philosophies"
    └────────────────────┘
```

**Quick Reference Table:**

| Query Type | Best Retriever | Example |
|------------|----------------|---------|
| Specific entities | Text2Cypher | "Who are Apple's executives?" |
| Relationship patterns | Text2Cypher | "Which companies share risks?" |
| Semantic search | VectorRetriever | "What is Apple's AI strategy?" |
| Context + relationships | VectorCypherRetriever | "Apple's product risks with context" |
| Comparisons | VectorRetriever | "Compare Google vs Microsoft" |
| Counts/aggregations | Text2Cypher | "How many products does Apple have?" |

---

## Summary

Excellent work! You've mastered advanced retrieval strategies. Let's recap:

### Key Concepts

✅ **VectorCypherRetriever**
- Combines vector similarity with graph traversal
- Enriches chunks with relationship context
- Custom Cypher queries for flexible enrichment
- Best for semantic search + structured context

✅ **Text2CypherRetriever**
- Translates natural language to Cypher queries
- Executes structured queries against the graph
- Best for specific entity/relationship questions
- Requires clear, well-structured questions

✅ **Choosing the Right Retriever**
- Understand query intent and structure
- Match retriever capabilities to query type
- Consider hybrid approaches for complex needs

### Limitations and Trade-offs

**VectorRetriever:**
- ✅ Great for semantic search
- ❌ Doesn't leverage graph structure
- ❌ Limited to chunk boundaries

**VectorCypherRetriever:**
- ✅ Rich context from relationships
- ✅ Flexible with custom queries
- ❌ Requires Cypher knowledge
- ❌ More complex to configure

**Text2CypherRetriever:**
- ✅ Direct graph queries
- ✅ Precise results for structured questions
- ❌ Requires clear entity/relationship questions
- ❌ Can generate invalid queries
- ❌ Doesn't work well for semantic concepts

### What's Next

In [**Module 4: Intelligent Agents**](04_intelligent_agents.md), you'll learn:
- Building agents with Microsoft Agent Framework
- Creating and registering tools
- Multi-tool orchestration
- Agent decision-making and debugging

This is where things get really exciting—agents that can choose the right retrieval strategy automatically!

### Quick Reference

**VectorCypherRetriever:**
```python
QUERY = """
MATCH (node)-[:RELATIONSHIP]-(other)
RETURN node.text AS context, other.property AS data
"""

retriever = VectorCypherRetriever(
    driver=driver,
    index_name="chunkEmbeddings",
    embedder=embedder,
    retrieval_query=QUERY
)
```

**Text2CypherRetriever:**
```python
from neo4j_graphrag.schema import get_schema

schema = get_schema(driver)
retriever = Text2CypherRetriever(
    driver=driver,
    llm=llm,
    neo4j_schema=schema
)
```

---

Ready to build intelligent agents? Continue to [**Module 4: Intelligent Agents**](04_intelligent_agents.md)!
