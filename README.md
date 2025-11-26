# Simple AI Agents (API Only)

This is an API-only implementation of an AI Agent using Python, FastAPI, and the **Microsoft Agent Framework (2025)** with **Azure AI Foundry**. It demonstrates how to build AI agents with conversation memory.

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/neo4j-partners/neo4j-azure-workshop)
[![Open in Dev Containers](https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/neo4j-partners/neo4j-azure-workshop)

## Quick Start

For GitHub Codespaces or Local Dev Container setup, see **[GUIDE_DEV_CONTAINERS.md](GUIDE_DEV_CONTAINERS.md)**.

## Prerequisites (Manual Setup)

*   **[uv](https://github.com/astral-sh/uv):** An extremely fast Python package installer and resolver.
*   **[Azure Developer CLI (azd)](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd):** For infrastructure provisioning.
*   **[Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli):** For authentication (`az login`).
*   **Git**

## Getting Started

### 1. Create Environment and Set Region
Create an azd environment and set the region. Azure AI Foundry Agent Service only supports select regions.

```bash
# Create a new environment
azd env new mydev

# Set region (REQUIRED)
azd env set AZURE_LOCATION eastus2
```

> **Supported Regions:** `eastus2`, `swedencentral`, or `westus2`

### 2. Set Up Resource Group (Optional)
This project can deploy to an existing resource group or create a new one. You need Contributor access on the resource group (not the entire subscription).

```bash
# Option A: Use an existing resource group (workshop scenario)
azd env set AZURE_RESOURCE_GROUP <your-existing-rg-name>

# Option B: Let azd create a new resource group (will prompt during azd up)
```

### 3. Provision Infrastructure
Deploy the Azure resources (AI Foundry Project, Container App, Managed Identity) into your resource group.

```bash
azd up
```

### Managing Multiple Environments

```bash
azd env list              # List all environments
azd env select <name>     # Switch to a different environment
azd env get-values        # Show current environment's variables
azd env new <name>        # Create a new environment
```

#### Load Financial Data into Neo4j (Optional)
Load structured CSV data into Neo4j to enable graph-based queries:

```bash
./scripts/load_data.sh
```

This loads `financial-data/Asset_Manager_Holdings.csv` and `financial-data/Company_Filings.csv` into Neo4j, creating:
- **Nodes:** `AssetManager`, `Company`, `Document`
- **Relationships:** `OWNS` (AssetManager → Company), `FILED` (Company → Document)

The script reads Neo4j credentials from `.env` automatically. Requires `cypher-shell` CLI (`brew install cypher-shell`).

### 4. Install Dependencies
Use `uv` to sync dependencies defined in `pyproject.toml`.

```bash
uv sync --prerelease=allow
```

### 5. Setup Environment Variables
Run the helper script to pull environment variables from `azd` and create a local `.env` file.

```bash
uv run setup_env.py
```

### 6. Run Locally

#### Run using uv (recommended for development)
```bash
uv run uvicorn api.main:create_app --factory --reload
```

The API will be available at `http://localhost:8000`.

## Testing the API

Use the included test script to verify the API is working:

### Basic Test
Check agent status and send a simple message:
```bash
uv run python src/test_server.py basic
```

### Streaming Test
Test the streaming endpoint:
```bash
uv run python src/test_server.py stream
```

### Memory Test (default)
Test conversation memory across multiple messages:
```bash
uv run python src/test_server.py memory
```

### Semantic Search Test
Test semantic/vector search over the graph database (requires Neo4j + Azure OpenAI):
```bash
uv run python src/test_server.py semantic
```

### Entity Search Test
Test entity listing and relationship queries (requires Neo4j):
```bash
uv run python src/test_server.py entities
```

### Run All Tests
Run all tests including agent, streaming, memory, semantic search, and entity search:
```bash
uv run python src/test_server.py all
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agent` | GET | Get agent status and configuration |
| `/chat` | POST | Send a message to the agent |
| `/chat/stream` | POST | Send a message with streaming response |
| `/search/schema` | GET | Get the graph database schema |
| `/search/semantic` | POST | Perform semantic/vector search |
| `/search/entities/types` | GET | Get available entity types |
| `/search/entities/{type}` | GET | List entities of a specific type |
| `/search/entities/{name}/relationships` | GET | Get relationships for an entity |

### Example API Calls

```bash
# Get entity types
curl http://localhost:8000/search/entities/types

# List companies
curl "http://localhost:8000/search/entities/Company?limit=10"

# Get relationships for an entity
curl "http://localhost:8000/search/entities/Apple/relationships?limit=10"

# Semantic search
curl -X POST http://localhost:8000/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the risk factors?", "top_k": 5}'
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_AI_PROJECT_ENDPOINT` | Yes | Azure AI Foundry project endpoint |
| `AZURE_AI_MODEL_NAME` | No | Model deployment name |
| `AZURE_AI_EMBEDDING_NAME` | No | Embedding model deployment (default: text-embedding-ada-002) |
| `AZURE_AI_AGENT_NAME` | No | Agent name (default: arches-agent) |
| `NEO4J_URI` | No | Neo4j connection URI (for graph features) |
| `NEO4J_USERNAME` | No | Neo4j username |
| `NEO4J_PASSWORD` | No | Neo4j password |
| `NEO4J_VECTOR_INDEX_NAME` | No | Neo4j vector index name (default: chunkEmbeddings) |

**Note:** Semantic search uses Azure AI Foundry embeddings with Azure CLI credentials (`az login`). No API keys required.

## Project Structure

*   `src/`: Python source code
    *   `api/`: FastAPI application and routes
    *   `agent.py`: Agent configuration and creation
    *   `test_server.py`: API test script
*   `infra/`: Azure Bicep infrastructure files
*   `scripts/`: Helper scripts
    *   `setup_azure.sh`: Interactive setup for Azure environment and region
    *   `load_data.sh`: Load structured CSV data into Neo4j
*   `financial-data/`: Sample financial data for Neo4j graph
    *   `Asset_Manager_Holdings.csv`: Asset manager stock holdings
    *   `Company_Filings.csv`: Company SEC filing metadata
*   `pyproject.toml`: Python dependency configuration
*   `ARCHITECTURE.md`: Detailed architecture documentation
*   `AGENT_FRAMEWORK.md`: Agent Framework migration notes
