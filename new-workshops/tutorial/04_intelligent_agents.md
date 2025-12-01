# Module 4: Intelligent Agents

## Overview

Welcome to the most exciting module! Here you'll build AI agents that can use tools to solve complex problems. Unlike the retrievers you've built so far, agents can make decisions about *which* tools to use and *when* to use them.

**What you'll learn:**
- Core concepts of the Microsoft Agent Framework
- Creating and registering tools with agents
- Building single-tool and multi-tool agents
- Understanding agent decision-making and orchestration

**Estimated Time:** 120 minutes

**Reference Materials:**
- Notebooks: `new-workshops/notebooks/02_01_simple_agent.ipynb`, `02_02_*.ipynb`, `02_03_*.ipynb`
- Solutions: `new-workshops/solutions/02_01_simple_agent.py`, `02_02_*.py`, `02_03_*.py`

---

## Lab 4.1: Simple Schema Agent

### Understanding Agents vs. Retrievers

**Retrievers:** You control the flow (Query → Retrieve → Return)
**Agents:** Agent controls the flow (Query → Agent Decides → Tool(s) → Answer)

### Creating Your First Tool

Tools are Python functions with clear docstrings:

```python
def get_graph_schema() -> str:
    """Get the schema of the graph database including node labels, relationships, and properties."""
    return get_schema(driver)
```

> **💡 Tip:** The docstring is crucial! The agent reads it to understand what the tool does.

### Complete Agent Implementation

```python
import asyncio
from neo4j_graphrag.schema import get_schema
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import AzureCliCredential
from config import get_neo4j_driver, get_agent_config

def create_schema_tool(driver):
    def get_graph_schema() -> str:
        """Get the schema of the graph database including node labels, relationships, and properties."""
        return get_schema(driver)
    return get_graph_schema

async def run_agent(query: str):
    config = get_agent_config()
    
    with get_neo4j_driver() as driver:
        get_graph_schema = create_schema_tool(driver)
        
        async with AzureCliCredential() as credential:
            client = AzureAIAgentClient(
                project_endpoint=config.project_endpoint,
                model_deployment_name=config.model_name,
                async_credential=credential,
            )
            
            async with client.create_agent(
                name="schema-agent",
                instructions="You are a helpful assistant that can answer questions about a graph database schema.",
                tools=[get_graph_schema],
            ) as agent:
                thread = agent.get_new_thread()
                
                print(f"User: {query}\n")
                print("Assistant: ", end="")
                
                async for update in agent.run_stream(query, thread=thread):
                    if update.text:
                        print(update.text, end="", flush=True)
                
                print("\n")

# Run it
asyncio.run(run_agent("Summarise the schema of the graph database."))
```

### How It Works

1. **Tool Creation**: `create_schema_tool()` wraps the driver for dependency injection
2. **Agent Client**: `AzureAIAgentClient` connects to Azure AI Foundry
3. **Agent Creation**: `client.create_agent()` registers the tool
4. **Thread**: `get_new_thread()` creates conversation state
5. **Execution**: `run_stream()` streams the response

### Exercises

**Exercise 1:** Run the agent with different queries:
- "What types of entities are in the database?"
- "How are Products related to Companies?"
- "Explain the document structure"

**Exercise 2:** Observe when the agent calls the tool:
- Try: "What is 2+2?" (should NOT call tool)
- Try: "What's in the database?" (should call tool)

---

## Lab 4.2: Vector-Graph Hybrid Agent

### Building Multi-Tool Agents

Agents can have multiple tools and choose which to use:

```python
tools = [
    get_graph_schema,      # Tool 1: Schema info
    search_documents,      # Tool 2: Vector search
]
```

### Complete Implementation

```python
from neo4j_graphrag.retrievers import VectorRetriever

def create_search_tool(driver, embedder):
    """Create vector search tool."""
    retriever = VectorRetriever(
        driver=driver,
        index_name="chunkEmbeddings",
        embedder=embedder,
        return_properties=["text"]
    )
    
    def search_documents(query: str, top_k: int = 5) -> str:
        """Search for documents related to the query using semantic similarity.
        
        Args:
            query: The search query
            top_k: Number of results to return (default 5)
        """
        results = retriever.search(query_text=query, top_k=top_k)
        
        output = []
        for i, item in enumerate(results.items, 1):
            score = item.metadata.get("score", 0)
            text_preview = item.content[:200] if item.content else ""
            output.append(f"{i}. (Score: {score:.4f}) {text_preview}...")
        
        return "\n\n".join(output)
    
    return search_documents

# Create agent with both tools
async with client.create_agent(
    name="hybrid-agent",
    instructions="""You are a helpful assistant with access to:
    1. Graph schema information
    2. Document search capabilities
    Use the appropriate tool based on the user's question."""
    tools=[get_graph_schema, search_documents],
) as agent:
    # Use the agent...
```

### Agent Decision-Making

The agent will automatically choose which tool(s) to use:

**Query: "What's in the database?"**
→ Calls `get_graph_schema()` (structural question)

**Query: "What risks does Apple face?"**
→ Calls `search_documents("Apple risks")` (content question)

**Query: "Search for AI companies and explain what entities exist"**
→ Calls BOTH tools (complex question)

### Exercises

**Exercise 1:** Create the hybrid agent and test with:
- "Summarize the database structure"
- "What do companies say about supply chain?"
- "List the entity types, then search for risk factors"

**Exercise 2:** Track agent behavior:
- Which tool does it call for each query?
- Does it ever call multiple tools?
- Can you force it to use a specific tool?

---

## Lab 4.3: Natural Language Query Agent

### Adding Text2Cypher Capability

Let's add a third tool for structured graph queries:

```python
def create_text2cypher_tool(driver, llm, schema):
    """Create text-to-Cypher tool."""
    
    def query_graph(question: str) -> str:
        """Execute a natural language query against the graph database.
        
        This tool converts your question into a Cypher query and executes it.
        Best for questions about specific entities and relationships.
        
        Args:
            question: Natural language question about the graph data
        """
        from neo4j_graphrag.retrievers import Text2CypherRetriever
        
        retriever = Text2CypherRetriever(
            driver=driver,
            llm=llm,
            neo4j_schema=schema
        )
        
        try:
            results = retriever.search(query_text=question, top_k=10)
            
            if not results.items:
                return "No results found for this query."
            
            output = []
            for item in results.items:
                output.append(str(item.content))
            
            return "\n".join(output)
        except Exception as e:
            return f"Query failed: {str(e)}. Try rephrasing your question."
    
    return query_graph
```

### Three-Tool Agent

```python
# Create all three tools
get_graph_schema = create_schema_tool(driver)
search_documents = create_search_tool(driver, embedder)
query_graph = create_text2cypher_tool(driver, llm, schema)

# Create agent with all tools
async with client.create_agent(
    name="multi-tool-agent",
    instructions="""You are a helpful assistant with three capabilities:
    
    1. get_graph_schema: Learn about database structure
    2. search_documents: Semantic search in document text
    3. query_graph: Execute structured queries for specific entities/relationships
    
    Choose the right tool(s) for each question:
    - Schema questions → get_graph_schema
    - Semantic/concept questions → search_documents  
    - Specific entity/relationship questions → query_graph
    
    You can use multiple tools if needed.""",
    tools=[get_graph_schema, search_documents, query_graph],
) as agent:
    # Use the agent...
```

### Tool Selection Strategy

The agent will choose based on question type:

| Question | Tool(s) Used | Reason |
|----------|--------------|--------|
| "What's in the database?" | `get_graph_schema` | Structural info |
| "What AI risks exist?" | `search_documents` | Semantic search |
| "Who are Apple's executives?" | `query_graph` | Specific entities |
| "Explain the schema, then find risks" | `get_graph_schema` + `search_documents` | Multi-step |

### Exercises

**Exercise 1:** Test the three-tool agent:
```python
queries = [
    "What types of data are available?",
    "What do companies say about AI?",
    "Which executives work at Microsoft?",
    "First show me the schema, then search for product information",
]
```

**Exercise 2:** Observe tool orchestration:
- Does the agent call tools in a logical order?
- How does it handle ambiguous questions?
- Can it recover from tool failures?

**Exercise 3:** Create custom instructions:
- Make the agent prefer `query_graph` over `search_documents`
- Make it always call `get_graph_schema` first
- Add guardrails for safety

---

## Understanding Agent Decision-Making

### How Agents Choose Tools

The LLM considers:
1. **Tool descriptions** (from docstrings)
2. **Instructions** (system prompt)
3. **Query semantics** (what the user is asking)
4. **Previous context** (conversation history)

### Debugging Agent Behavior

**Problem:** Agent doesn't call expected tool

**Solutions:**
1. Improve tool docstring clarity
2. Adjust instructions to guide tool selection
3. Rephrase user query to be more specific
4. Check if tool parameters are clear

**Example:**

```python
# Bad docstring (vague)
def search(q: str) -> str:
    """Search for stuff."""
    ...

# Good docstring (specific)
def search_documents(query: str, top_k: int = 5) -> str:
    """Search for documents related to the query using semantic similarity.
    
    Use this when the user asks about content, concepts, or themes in documents.
    Best for questions like 'What do companies say about X?'
    
    Args:
        query: The search query describing what to find
        top_k: Number of results to return (default 5, max 20)
    
    Returns:
        Relevant document excerpts with similarity scores
    """
    ...
```

### Best Practices

1. **Clear Tool Names**: `get_graph_schema` > `tool1`
2. **Detailed Docstrings**: Explain when and how to use the tool
3. **Good Instructions**: Guide the agent's behavior
4. **Error Handling**: Tools should return helpful error messages
5. **Testing**: Try diverse queries to understand behavior

---

## Summary

Congratulations! You've built intelligent agents with the Microsoft Agent Framework. Let's recap:

### Key Concepts

✅ **Agent Architecture**
- Instructions define behavior
- Model (LLM) makes decisions
- Tools provide capabilities

✅ **Tool Creation**
- Python functions with docstrings
- Automatic JSON schema generation
- Dependency injection for resources

✅ **Multi-Tool Agents**
- Agents choose which tool(s) to use
- Can call multiple tools per query
- Orchestration handled by framework

✅ **Decision-Making**
- Based on instructions, tool descriptions, and query
- Non-deterministic (agent has autonomy)
- Can be guided through clear instructions

### What's Next

In [**Module 5: Production Application**](05_production_application.md), you'll learn:
- Building production-ready FastAPI applications
- Agent management and lifecycle
- Configuration and observability
- Deployment to Azure

You'll see how all these concepts come together in a real application!

### Quick Reference

**Create Simple Agent:**
```python
async with AzureAIAgentClient(...) as client:
    async with client.create_agent(
        name="my-agent",
        instructions="You are helpful...",
        tools=[func1, func2]
    ) as agent:
        thread = agent.get_new_thread()
        result = await agent.run(query, thread=thread)
```

**Tool Function:**
```python
def my_tool(param: str) -> str:
    """Clear description of what this tool does.
    
    Args:
        param: What this parameter means
    
    Returns:
        What gets returned
    """
    return result
```

---

Ready to build production applications? Continue to [**Module 5: Production Application**](05_production_application.md)!
