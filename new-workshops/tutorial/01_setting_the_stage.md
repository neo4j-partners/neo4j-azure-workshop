# Module 1: Setting the Stage

## Overview

Welcome to the first module of this workshop! Before we dive into code, we need to understand *why* we're building what we're building, and *what* tools we'll use. This module sets the foundation for everything that follows.

**What you'll learn:**
- Why traditional search falls short for complex document analysis
- How graphs enhance AI with connected data
- The role of each technology in our stack
- How to set up and verify your development environment

**Estimated Time:** 45 minutes

## Prerequisites

Before starting, ensure you have:
- Azure account with AI Foundry access
- Neo4j database (AuraDB or self-hosted)
- Python 3.11+ installed
- Basic understanding of REST APIs and Python

---

## Understanding the Problem Domain

### The Challenge of Intelligent Document Analysis

Imagine you're analyzing hundreds of financial documents—SEC 10-K filings from major companies. You need to answer questions like:

- "What risks does Apple face regarding supply chain disruptions?"
- "Which companies mention AI in their product strategy?"
- "How are Microsoft's cloud products related to their executive team?"
- "Compare the risk profiles of tech companies in the semiconductor space"

These aren't simple keyword searches. They require:
1. **Semantic understanding**: "supply chain disruptions" vs "logistics challenges"
2. **Relationship traversal**: Products → Companies → Executives
3. **Contextual reasoning**: Understanding how pieces of information connect
4. **Structured queries**: Sometimes you need precise graph patterns

### Why Traditional Search Fails

Traditional full-text search has limitations:

```
❌ Keyword Matching Only
   Query: "AI risks"
   Finds: Exact phrase "AI risks"
   Misses: "artificial intelligence challenges", "machine learning concerns"

❌ No Relationship Awareness
   Query: "Microsoft products"
   Finds: Documents mentioning both words
   Misses: The graph structure connecting Product → Company → Executive

❌ No Reasoning
   Query: "Compare risk profiles"
   Finds: Documents with "risk" and "profile"
   Misses: The comparative analysis and structured comparison
```

### The Graph Advantage

Graph databases like Neo4j store data as **nodes** (entities) and **relationships** (connections), perfectly matching how information naturally connects:

```
(Company)-[:OFFERS]->(Product)
(Company)-[:HAS_EXECUTIVE]->(Executive)
(Company)-[:FILED]->(Document)-[:HAS_CHUNK]->(Chunk)
(Company)-[:FACES]->(RiskFactor)
```

This structure enables:
- **Semantic search** with vector embeddings on chunks
- **Relationship traversal** to enrich context
- **Graph queries** for precise pattern matching
- **Hybrid approaches** combining all three

### The Financial Document Use Case

We use SEC 10-K filings because they:
- Contain rich, structured information
- Have clear entities (companies, products, executives)
- Include relationships (ownership, risk factors)
- Represent real-world document intelligence challenges

**Our Graph Schema:**

```
┌─────────────┐      ┌──────────┐      ┌───────────┐
│   Company   │─────>│ Product  │      │ Executive │
│  (Apple)    │      │ (iPhone) │      │ (Tim Cook)│
└─────────────┘      └──────────┘      └───────────┘
      │                                       │
      │ FILED                      HAS_EXECUTIVE
      ▼                                       │
┌─────────────┐                              │
│  Document   │◄─────────────────────────────┘
│  (10-K)     │
└─────────────┘
      │
      │ HAS_CHUNK
      ▼
┌─────────────┐
│    Chunk    │ ← Contains text + vector embeddings
│  (Section)  │
└─────────────┘
      │
      │ MENTIONS
      ▼
┌─────────────┐
│ RiskFactor  │
│ (Supply)    │
└─────────────┘
```

> **💡 Tip:** This schema is simplified. The actual graph includes more relationships and properties. We'll explore the full schema during setup.

---

## Technology Stack Overview

Our stack combines graph databases, vector search, and agentic AI. Let's understand each component.

### Neo4j: Graph Database for Connected Data

**What is Neo4j?**

Neo4j is a native graph database optimized for storing and querying connected data. Unlike relational databases that use tables and joins, Neo4j stores data as nodes and relationships.

**Why Neo4j?**

1. **Natural data modeling**: Entities and their connections match real-world structures
2. **Vector search built-in**: Native support for embedding-based similarity search
3. **Cypher query language**: Intuitive pattern-matching for graph queries
4. **Performance at scale**: Optimized for relationship traversal

**Key Concepts:**

- **Nodes**: Entities like Company, Product, Document, Chunk
- **Relationships**: Typed connections like FILED, HAS_CHUNK, MENTIONS
- **Properties**: Key-value data on nodes and relationships
- **Labels**: Types/categories for nodes (e.g., :Company, :Product)

**Example Cypher Query:**

```cypher
// Find products offered by companies that mention "AI"
MATCH (c:Company)-[:OFFERS]->(p:Product)
WHERE c.name CONTAINS "AI"
RETURN c.name, collect(p.name) as products
```

> **📚 Learn More:** [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/)

### Azure AI Foundry: Cloud-Native AI Platform

**What is Azure AI Foundry?**

Azure AI Foundry (formerly Azure AI Studio) is Microsoft's comprehensive platform for building, deploying, and managing AI applications. It provides:

- **Model hosting**: Deploy and scale LLMs (GPT-4o, embeddings)
- **Unified inference endpoint**: OpenAI-compatible API for models
- **Project management**: Organize resources, connections, and deployments
- **Monitoring**: Track usage, costs, and performance

**Why Azure AI Foundry?**

1. **Enterprise-ready**: Security, compliance, and governance built-in
2. **Integrated auth**: Azure CLI credentials, Managed Identity support
3. **Unified platform**: Models, agents, and tools in one place
4. **Scalability**: Auto-scaling inference endpoints

**Key Components:**

- **Project**: Container for all your AI resources
- **Deployments**: Hosted models (gpt-4o, text-embedding-ada-002)
- **Connections**: Managed credentials for external services
- **Inference Endpoint**: OpenAI-compatible API for model access

> **📚 Learn More:** [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-studio/)

### Microsoft Agent Framework: Modern Agentic AI

**What is the Microsoft Agent Framework?**

The Microsoft Agent Framework (`@microsoft/agent-framework` for TypeScript, `agent-framework` for Python) is a modern framework for building AI agents that can:

- Use tools to interact with external systems
- Make decisions about which tools to use
- Maintain conversation state across turns
- Execute complex multi-step workflows

**Why Agent Framework?**

1. **Service-managed**: Agents run in Azure AI Foundry, not your code
2. **Persistent threads**: Conversation history managed by the service
3. **Tool orchestration**: Framework handles tool calling and execution
4. **Production-ready**: Built for reliability and scale

**Core Concepts:**

#### 1. Agents

An agent is an AI model (like GPT-4o) equipped with:
- **Instructions**: System prompt defining behavior
- **Tools**: Functions the agent can call
- **Model**: The underlying LLM powering decisions

```python
from agent_framework.azure import AzureAIAgentClient

async with AzureAIAgentClient(
    project_endpoint=endpoint,
    model_deployment_name="gpt-4o",
    async_credential=credential
) as client:
    async with client.create_agent(
        name="my-agent",
        instructions="You are a helpful assistant.",
        tools=[get_schema, search_documents]
    ) as agent:
        # Agent is ready to use
        pass
```

#### 2. Tools

Tools are Python functions that agents can call. The framework:
- Inspects function signatures and docstrings
- Generates JSON schema for tool definitions
- Handles serialization/deserialization
- Executes tools and returns results to the agent

```python
def get_graph_schema() -> str:
    """Get the schema of the graph database including node labels, relationships, and properties."""
    return get_schema(driver)
```

The agent sees:
```json
{
  "name": "get_graph_schema",
  "description": "Get the schema of the graph database including node labels, relationships, and properties.",
  "parameters": {
    "type": "object",
    "properties": {}
  }
}
```

> **💡 Tip:** Clear docstrings are crucial! The agent uses them to understand when and how to use tools.

#### 3. Agent Architecture

Here's how agents work:

```
┌─────────────────────────────────────────────────────┐
│                   Azure AI Foundry                   │
│  ┌────────────────────────────────────────────────┐ │
│  │                    Agent                        │ │
│  │                                                 │ │
│  │  Instructions: "You are a helpful assistant"   │ │
│  │  Model: gpt-4o                                 │ │
│  │  Tools: [get_schema, search_docs, ...]        │ │
│  └─────────────────┬──────────────────────────────┘ │
│                    │                                 │
│                    │ Thread (Conversation State)     │
│                    ▼                                 │
│         ┌──────────────────────┐                    │
│         │  Message History     │                    │
│         │  - User: "question"  │                    │
│         │  - Assistant: "..."  │                    │
│         │  - Tool calls/results│                    │
│         └──────────────────────┘                    │
└─────────────────────────────────────────────────────┘
         │                     │
         │ 1. Send message     │ 3. Return response
         │                     │
    ┌────▼─────────────────────▼────┐
    │      Your Application          │
    │                                │
    │  2. Execute tool calls         │
    │     (get_schema, etc.)         │
    └────────────────────────────────┘
```

**Workflow:**

1. **User sends message**: "What's in the database?"
2. **Agent decides**: "I should use the get_schema tool"
3. **Framework executes**: Calls your Python function
4. **Agent receives result**: Schema information
5. **Agent responds**: "The database contains Companies, Products, ..."

#### 4. Persistent vs. Ephemeral Agents

**Persistent Agents** (What we use):
- Created once in Azure AI Foundry
- Reused across requests
- Configuration stored in the service
- Better for production (cost-effective, faster)

**Ephemeral Agents**:
- Created per-request
- Configuration in your code
- Better for testing/development

```python
# Persistent agent (created once in lifespan)
async with client.create_agent(
    name="my-agent",
    instructions="...",
    tools=[...]
) as agent:
    # Agent persists in Foundry
    # Reuse for multiple conversations
    result1 = await agent.run("Query 1", thread=thread1)
    result2 = await agent.run("Query 2", thread=thread2)
```

#### 5. Tool-Calling Paradigm

The agent framework uses **function calling** (tool calling):

1. **Agent analyzes** the user's message
2. **Agent decides** which tool(s) to use (if any)
3. **Framework executes** the tool(s) in your application
4. **Results return** to the agent
5. **Agent synthesizes** final response

**Example Flow:**

```
User: "What companies are in the database?"

Agent thinks: "I need the schema to know what's available"
  → Calls: get_graph_schema()
  → Receives: "Node labels: Company, Product, ..."

Agent thinks: "Now I can answer"
  → Returns: "The database contains Company, Product, Executive, ..."
```

> **⚠️ Warning:** Agents make autonomous decisions. Sometimes they may not call tools you expect, or call them in unexpected order. This is normal agent behavior!

#### 6. Integration with Azure AI Foundry

The framework provides `AzureAIAgentClient` for seamless integration:

```python
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import AzureCliCredential

credential = AzureCliCredential()
client = AzureAIAgentClient(
    project_endpoint="https://<your-project>.api.azureml.ms",
    model_deployment_name="gpt-4o",
    async_credential=credential
)
```

Benefits:
- **Automatic authentication**: Uses Azure credentials
- **Service management**: Agents run in Foundry
- **Thread management**: Conversation state in the service
- **Observability**: Integrates with Azure Monitor

> **📚 Learn More:** [Microsoft Agent Framework Repository](https://github.com/microsoft/agent-framework)

---

## Environment Setup

Now let's set up your development environment and verify everything works.

### Prerequisites Checklist

Before proceeding, ensure you have:

- [ ] **Python 3.11+**: `python --version`
- [ ] **uv installed**: `uv --version` ([install guide](https://github.com/astral-sh/uv))
- [ ] **Azure CLI**: `az --version` ([install guide](https://learn.microsoft.com/cli/azure/install-azure-cli))
- [ ] **Git**: `git --version`
- [ ] **Azure subscription**: With AI Foundry access
- [ ] **Neo4j instance**: AuraDB or self-hosted

### Step 1: Clone and Navigate

```bash
git clone https://github.com/neo4j-partners/neo4j-azure-workshop.git
cd neo4j-azure-workshop
```

### Step 2: Configure Azure Region

```bash
./scripts/setup_azure.sh
```

This script:
- Prompts for your preferred Azure region
- Clears any existing Azure configuration
- Prepares for fresh `azd up` deployment

**Supported regions:**
- `eastus2` (recommended for most users)
- `swedencentral` (EU data residency)
- `westus2` (US West Coast)

> **💡 Tip:** Choose the region closest to your Neo4j database for lower latency.

### Step 3: Provision Azure Infrastructure

```bash
azd up
```

This command:
1. Creates an Azure AI Foundry project
2. Deploys GPT-4o and text-embedding-ada-002 models
3. Configures managed identities and role assignments
4. Outputs connection information

**Expected output:**
```
SUCCESS: Your application was provisioned in Azure in X minutes Y seconds.
You can view the resources created under the resource group rg-neo4j-azure-workshop in Azure Portal:
https://portal.azure.com/...
```

> **⏱️ Note:** This takes ~10-15 minutes. Good time for a coffee break!

### Step 4: Install Dependencies

```bash
uv sync --prerelease=allow
```

The `--prerelease=allow` flag is **required** because the Microsoft Agent Framework is in preview.

This installs:
- `agent-framework`: Microsoft Agent Framework
- `neo4j`: Neo4j Python driver
- `neo4j-graphrag`: GraphRAG patterns and retrievers
- `fastapi`: Web framework for APIs
- `azure-identity`: Azure authentication
- Other dependencies from `pyproject.toml`

### Step 5: Setup Environment Variables

```bash
uv run setup_env.py
```

This script:
- Reads configuration from `azd` deployment
- Creates `.env` file in project root
- Populates Azure and Neo4j credentials

**Generated `.env` contains:**
```bash
# Azure AI Foundry
AZURE_AI_PROJECT_ENDPOINT=https://your-project.api.azureml.ms
AZURE_AI_MODEL_NAME=gpt-4o
AZURE_AI_EMBEDDING_NAME=text-embedding-ada-002

# Neo4j
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password

# Agent Config
AZURE_AI_AGENT_NAME=arches-agent
```

> **🔒 Security:** Never commit `.env` files to version control! The `.gitignore` already excludes them.

### Step 6: Authenticate with Azure

```bash
az login
```

This opens a browser for authentication. The Microsoft Agent Framework uses these credentials to access Azure AI Foundry.

### Step 7: Restore Neo4j Database

If using your own Neo4j instance:

```bash
uv run python scripts/restore_neo4j.py
```

This script:
- Downloads backup from GitHub
- Streams data to your Neo4j instance
- Creates indexes and constraints
- Loads ~50MB of financial document data

**What gets loaded:**
- Companies: Apple, Microsoft, Google, Amazon, etc.
- Documents: SEC 10-K filings
- Chunks: Text sections with vector embeddings
- Entities: Products, Executives, Risk Factors
- Relationships: Connecting everything

> **⏱️ Note:** Takes ~5-10 minutes depending on connection speed.

### Step 8: Verify Workshop Setup

```bash
cd new-workshops
./setup.sh
```

This script:
1. Installs Jupyter kernel for notebooks
2. Tests Neo4j connection
3. Tests Azure AI Foundry connection
4. Verifies vector embeddings work

**Expected output:**
```
✓ Neo4j connection successful
✓ Azure AI connection successful
✓ Embedding generation successful
✓ Vector search working

Setup complete! You're ready to start the workshops.
```

> **⚠️ Important:** If using Codespaces/Dev Containers, refresh your browser after running `setup.sh` for VS Code to detect the new Jupyter kernel.

---

## Schema Exploration and Understanding Your Graph

Now that setup is complete, let's explore what's in the database.

### Connecting to Neo4j Browser

1. Open your Neo4j database URL in a browser
   - AuraDB: Console → Open with → Browser
   - Self-hosted: `http://localhost:7474`

2. Authenticate with credentials from `.env`

3. Run exploratory queries

### Exploring the Schema

#### View All Node Labels

```cypher
CALL db.labels()
```

**Result:**
```
Company
Product
Executive
Document
Chunk
RiskFactor
FinancialMetric
StockType
Transaction
TimePeriod
```

#### View All Relationship Types

```cypher
CALL db.relationshipTypes()
```

**Result:**
```
OFFERS
HAS_EXECUTIVE
FILED
HAS_CHUNK
MENTIONS
FACES
HAS_METRIC
```

#### Sample Data Exploration

**Find a company and its products:**
```cypher
MATCH (c:Company {name: "Apple"})-[:OFFERS]->(p:Product)
RETURN c.name, collect(p.name) as products
LIMIT 1
```

**Explore document chunks:**
```cypher
MATCH (c:Company)-[:FILED]->(d:Document)-[:HAS_CHUNK]->(chunk:Chunk)
RETURN c.name, d.title, chunk.text
LIMIT 3
```

**View risk factors:**
```cypher
MATCH (c:Company)-[:FACES]->(r:RiskFactor)
RETURN c.name, r.name, r.description
LIMIT 5
```

### Understanding Vector Embeddings

Some nodes (like `Chunk`) have vector embeddings for semantic search:

```cypher
MATCH (chunk:Chunk)
RETURN chunk.text, chunk.embedding
LIMIT 1
```

The `embedding` property contains a 1536-dimension vector (for text-embedding-ada-002).

**Vector Index:**
```cypher
SHOW INDEXES
```

Look for: `chunkEmbeddings` - This enables fast similarity search.

> **💡 Tip:** Vector indexes are like B-tree indexes for traditional databases, but for similarity search instead of exact matches.

### Testing Vector Search

Let's verify vector search works:

```cypher
// This requires the APOC library
CALL db.index.vector.queryNodes(
  'chunkEmbeddings',
  10,
  [0.1, 0.2, ...] // 1536-dim vector
)
YIELD node, score
RETURN node.text, score
```

> **📝 Note:** We'll use the `neo4j-graphrag` library in code for vector search instead of manual Cypher queries.

---

## Verification Steps

Let's verify everything is working correctly.

### Test 1: Neo4j Connection

```bash
cd new-workshops/solutions
uv run python -c "
from config import get_neo4j_driver
with get_neo4j_driver() as driver:
    result = driver.execute_query('RETURN \"Connected!\" as message')
    print(result.records[0]['message'])
"
```

**Expected:** `Connected!`

### Test 2: Azure AI Foundry

```bash
uv run python -c "
from config import get_llm
llm = get_llm()
response = llm.invoke('Say hello!')
print(response.content)
"
```

**Expected:** A greeting from the model.

### Test 3: Vector Embeddings

```bash
uv run python -c "
from config import get_embedder
embedder = get_embedder()
vector = embedder.embed_query('test')
print(f'Embedding dimension: {len(vector)}')
"
```

**Expected:** `Embedding dimension: 1536`

### Test 4: Agent Creation

```bash
cd ../../src
uv run python -c "
import asyncio
from agent import AgentConfig, create_agent_client, create_agent_context
from azure.identity.aio import AzureCliCredential

async def test():
    config = AgentConfig()
    async with AzureCliCredential() as credential:
        client = create_agent_client(config, credential)
        async with create_agent_context(client, config) as agent:
            print(f'Agent created: {config.name}')

asyncio.run(test())
"
```

**Expected:** `Agent created: arches-agent`

### Troubleshooting

**Issue: Neo4j Connection Failed**
- Verify credentials in `.env`
- Check firewall rules (AuraDB: add your IP)
- Test connection in Neo4j Browser

**Issue: Azure Authentication Failed**
- Run `az login` again
- Verify subscription access: `az account show`
- Check project endpoint in `.env`

**Issue: Import Errors**
- Run `uv sync --prerelease=allow` again
- Verify Python version: `python --version` (needs 3.11+)
- Check virtual environment: `which python`

**Issue: Vector Search Not Working**
- Verify index exists: `SHOW INDEXES` in Neo4j Browser
- Check if embeddings loaded: `MATCH (c:Chunk) RETURN count(c)`
- Re-run restore script if needed

---

## Summary

Congratulations! You've completed Module 1. Let's recap what you've learned:

### Key Concepts

✅ **Problem Domain**
- Document intelligence requires semantic understanding + relationships
- Traditional search can't traverse connections or reason about structure
- Graphs naturally model connected document data

✅ **Neo4j Graph Database**
- Stores data as nodes (entities) and relationships (connections)
- Built-in vector search for semantic similarity
- Cypher query language for pattern matching

✅ **Azure AI Foundry**
- Cloud platform for hosting models and agents
- Unified inference endpoint (OpenAI-compatible)
- Enterprise security and scalability

✅ **Microsoft Agent Framework**
- Build agents that use tools to solve problems
- Service-managed agents in Azure AI Foundry
- Tool orchestration and decision-making
- Persistent conversation threads

✅ **Environment Setup**
- Azure infrastructure provisioned
- Dependencies installed
- Neo4j database loaded and verified
- Agent creation tested

### What's Next

In [**Module 2: Simple Retrieval**](02_simple_retrieval.md), you'll:
- Build your first VectorRetriever for semantic search
- Understand how embeddings enable similarity search
- Implement GraphRAG for question answering
- Test and evaluate retrieval quality

### Quick Reference

**Useful Commands:**
```bash
# Start workshop notebooks
cd new-workshops
uv run jupyter notebook notebooks/

# Run solution scripts
cd new-workshops/solutions
uv run python 01_01_vector_retriever.py

# Start API server
cd ../../
uv run uvicorn api.main:create_app --factory --reload

# View logs
tail -f app.log
```

**Key Files:**
- Configuration: `.env` in project root
- Notebooks: `new-workshops/notebooks/`
- Solutions: `new-workshops/solutions/`
- Production code: `src/`

---

## Hands-On Exercise

Before moving to Module 2, try exploring the graph:

1. **Find interesting relationships:**
   ```cypher
   MATCH path = (c:Company)-[*1..2]-(x)
   WHERE c.name = "Microsoft"
   RETURN path
   LIMIT 25
   ```

2. **Analyze the data:**
   - How many companies? `MATCH (c:Company) RETURN count(c)`
   - How many products? `MATCH (p:Product) RETURN count(p)`
   - How many document chunks? `MATCH (c:Chunk) RETURN count(c)`

3. **Read a chunk:**
   ```cypher
   MATCH (chunk:Chunk)
   RETURN chunk.text
   LIMIT 1
   ```

> **💡 Challenge:** Can you find which company has the most risk factors? (Hint: use `FACES` relationship and `count()`)

---

Ready to build your first retriever? Let's move to [**Module 2: Simple Retrieval**](02_simple_retrieval.md)!
