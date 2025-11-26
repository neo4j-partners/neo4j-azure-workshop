# Server Overview

This document covers the FastAPI server, its endpoints, and testing options.

## Running the Server

```bash
uv run uvicorn api.main:create_app --factory --reload
```

The API will be available at `http://localhost:8000`.

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

## Example API Calls

```bash
# Get agent status
curl http://localhost:8000/agent

# Chat with the agent
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, what can you help me with?"}'

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

## Testing the API

Use the included test script to verify the API is working.

### Run All Tests

```bash
uv run python src/test_server.py all
```

This runs agent, streaming, memory, semantic search, and entity search tests.

### Individual Test Options

| Command | Description |
|---------|-------------|
| `uv run python src/test_server.py basic` | Check agent status and send a simple message |
| `uv run python src/test_server.py stream` | Test the streaming endpoint |
| `uv run python src/test_server.py memory` | Test conversation memory across multiple messages |
| `uv run python src/test_server.py semantic` | Test semantic/vector search (requires Neo4j + embeddings) |
| `uv run python src/test_server.py entities` | Test entity listing and relationship queries (requires Neo4j) |

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
