# Module 5: Production Application

## Overview

In previous modules, you built retrievers and agents in notebooks and scripts. Now it's time to see how these concepts come together in a production-ready application. This module walks through the complete FastAPI application in the `src/` directory.

**What you'll learn:**
- Production application architecture
- Configuration management with Pydantic
- Agent lifecycle management
- FastAPI integration patterns
- Deployment best practices

**Estimated Time:** 90 minutes

**Reference Materials:**
- Source code: `src/` directory
- Main files: `src/api/main.py`, `src/agent.py`, `src/neo4j_client.py`, `src/api/routes.py`

---

## Application Architecture

### High-Level Overview

```
┌────────────────────────────────────────────┐
│        FastAPI Application                 │
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │  Lifespan Manager (main.py)          │ │
│  │  - Load environment                   │ │
│  │  - Create agent client                │ │
│  │  - Initialize Neo4j                   │ │
│  │  - Setup monitoring                   │ │
│  └──────────────────────────────────────┘ │
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │  API Routes (routes.py)               │ │
│  │  - GET  /agent                        │ │
│  │  - POST /chat                         │ │
│  │  - POST /chat/stream                  │ │
│  │  - POST /search/semantic              │ │
│  └──────────────────────────────────────┘ │
│                                            │
└────────────────────────────────────────────┘
         │                    │
         │                    │
         ▼                    ▼
┌──────────────┐    ┌──────────────────┐
│  Azure AI    │    │  Neo4j Database  │
│  Foundry     │    │                  │
└──────────────┘    └──────────────────┘
```

### Core Components

1. **`agent.py`**: Agent configuration and factory functions
2. **`neo4j_client.py`**: Neo4j connection and schema management
3. **`vector_search.py`**: Vector search client implementation
4. **`api/main.py`**: FastAPI app factory with lifespan management
5. **`api/routes.py`**: REST API endpoints
6. **`gunicorn.conf.py`**: Production server configuration

---

## Agent Management (`src/agent.py`)

### Production-Ready Configuration

```python
from pydantic import Field
from pydantic_settings import BaseSettings

class AgentConfig(BaseSettings):
    \"\"\"Agent configuration loaded from environment variables.\"\"\"
    
    model_config = SettingsConfigDict(
        env_prefix="",
        extra="ignore",
    )
    
    name: str = Field(
        default="arches-agent",
        validation_alias="AZURE_AI_AGENT_NAME",
    )
    model: str = Field(
        default="gpt-4o",
        validation_alias="AZURE_AI_MODEL_NAME",
    )
    instructions: str = Field(
        default="You are a helpful API assistant.",
    )
    project_endpoint: str | None = Field(
        default=None,
        validation_alias="AZURE_AI_PROJECT_ENDPOINT",
    )
```

**Key Features:**
- **Pydantic Settings**: Type-safe configuration from environment
- **Validation Aliases**: Map env vars to field names
- **Defaults**: Sensible fallbacks
- **Extra Ignore**: Ignore unknown env vars

### Agent Client Factory Pattern

```python
def create_agent_client(config: AgentConfig, credential: AzureCliCredential):
    \"\"\"Create an AzureAIAgentClient configured for Foundry.\"\"\"
    client_kwargs = {"async_credential": credential}
    
    if config.project_endpoint:
        client_kwargs["project_endpoint"] = config.project_endpoint
    
    if config.model:
        client_kwargs["model_deployment_name"] = config.model
    
    logger.info(f"Creating AzureAIAgentClient for project: {config.project_endpoint}")
    return AzureAIAgentClient(**client_kwargs)
```

**Benefits:**
- Centralized agent creation logic
- Easy to test and mock
- Configuration validation
- Consistent logging

### Agent Context Manager

```python
def create_agent_context(client: AzureAIAgentClient, config: AgentConfig):
    \"\"\"Create an agent context manager from the client.\"\"\"
    logger.info(f"Creating agent '{config.name}' with model '{config.model}'...")
    return client.create_agent(
        name=config.name,
        instructions=config.instructions,
    )
```

**Usage in Application:**
```python
# In lifespan manager
client = create_agent_client(config, credential)
agent = await stack.enter_async_context(create_agent_context(client, config))
app.state.agent = agent
```

---

## Neo4j Client Implementation (`src/neo4j_client.py`)

### Configuration

```python
class Neo4jConfig(BaseSettings):
    \"\"\"Neo4j configuration loaded from environment variables.\"\"\"
    
    uri: str | None = Field(default=None, validation_alias="NEO4J_URI")
    username: str | None = Field(default=None, validation_alias="NEO4J_USERNAME")
    password: str | None = Field(default=None, validation_alias="NEO4J_PASSWORD")
    
    @property
    def is_configured(self) -> bool:
        \"\"\"Check if all required Neo4j settings are provided.\"\"\"
        return all([self.uri, self.username, self.password])
```

### Async Context Manager Pattern

```python
class Neo4jClient:
    \"\"\"Async Neo4j client for managing database connections and queries.\"\"\"
    
    async def __aenter__(self) -> Neo4jClient:
        \"\"\"Enter async context and establish connection.\"\"\"
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        \"\"\"Exit async context and close connection.\"\"\"
        await self.close()
    
    async def connect(self) -> None:
        \"\"\"Establish connection to Neo4j database.\"\"\"
        self._driver = AsyncGraphDatabase.driver(
            self._config.uri,
            auth=(self._config.username, self._config.password),
        )
        await self._driver.verify_connectivity()
```

**Usage:**
```python
async with Neo4jClient(config) as client:
    schema = await client.get_schema()
    results = await client.execute_query(query)
```

### Schema Retrieval

```python
async def get_schema(self) -> GraphSchema:
    \"\"\"Retrieve the graph database schema.\"\"\"
    schema = GraphSchema()
    
    async with self.driver.session() as session:
        # Get node labels
        result = await session.run("CALL db.labels()")
        records = await result.data()
        schema.node_labels = [record["label"] for record in records]
        
        # Get relationship types
        result = await session.run("CALL db.relationshipTypes()")
        records = await result.data()
        schema.relationship_types = [record["relationshipType"] for record in records]
        
        # Get properties for each label...
    
    return schema
```

---

## FastAPI Application (`src/api/`)

### Application Factory Pattern

```python
def create_app() -> fastapi.FastAPI:
    \"\"\"Create and configure the FastAPI application.\"\"\"
    app = fastapi.FastAPI(lifespan=lifespan)
    app.include_router(routes.router)
    return app
```

**Benefits:**
- Easy to test (create app instances)
- Can create with different configurations
- Standard FastAPI pattern

### Lifespan Management

```python
@contextlib.asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    \"\"\"FastAPI lifespan manager for startup and shutdown.\"\"\"
    
    # Startup
    load_environment()
    config = AgentConfig()
    
    async with contextlib.AsyncExitStack() as stack:
        # Enter credential context
        credential = await stack.enter_async_context(AzureCliCredential())
        
        # Create client and agent
        client = create_agent_client(config, credential)
        agent = await stack.enter_async_context(create_agent_context(client, config))
        app.state.agent = agent
        
        # Initialize Neo4j (optional)
        neo4j_client, schema = await initialize_neo4j(stack)
        app.state.neo4j_client = neo4j_client
        app.state.graph_schema = schema
        
        # Initialize vector search
        vector_search_client = initialize_vector_search(neo4j_client)
        app.state.vector_search_client = vector_search_client
        
        yield  # Application runs here
        
        # Shutdown handled automatically by AsyncExitStack
```

**Key Points:**
- **AsyncExitStack**: Manages multiple async context managers
- **app.state**: Store resources for access in routes
- **Automatic cleanup**: Stack handles __aexit__ calls

### API Routes

#### Agent Status Endpoint

```python
@router.get("/agent")
async def get_agent(request: Request):
    \"\"\"Return details about the current agent.\"\"\"
    if not hasattr(request.app.state, "agent"):
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    config = request.app.state.config
    return {
        "name": config.name,
        "model": config.model,
        "instructions": config.instructions,
    }
```

#### Chat Endpoint

```python
@router.post("/chat")
async def chat(request: Request, chat_request: ChatRequest):
    \"\"\"Send a message to the agent using Agent Framework.\"\"\"
    agent = request.app.state.agent
    
    # Get or create thread for conversation tracking
    conversation_id = chat_request.conversation_id
    if conversation_id and conversation_id in _threads:
        thread = _threads[conversation_id]
    else:
        thread = agent.get_new_thread()
        conversation_id = str(uuid.uuid4())
        _threads[conversation_id] = thread
    
    result = await agent.run(chat_request.message, thread=thread)
    
    return {
        "response": result.text,
        "conversation_id": conversation_id,
    }
```

#### Streaming Chat Endpoint

```python
@router.post("/chat/stream")
async def chat_stream(request: Request, chat_request: ChatRequest):
    \"\"\"Send a message to the agent with streaming response.\"\"\"
    agent = request.app.state.agent
    thread = get_or_create_thread(chat_request.conversation_id)
    
    response_content = ""
    async for update in agent.run_stream(chat_request.message, thread=thread):
        if update.text:
            response_content += update.text
    
    return {
        "response": response_content,
        "conversation_id": conversation_id,
    }
```

---

## End-to-End Integration

### Request/Response Flow

```
Client Request: POST /chat
    {"message": "What companies are in the database?"}
        │
        ▼
┌───────────────────────────┐
│  FastAPI Route Handler    │
│  (routes.py::chat)        │
└───────────┬───────────────┘
            │
            ▼
┌───────────────────────────┐
│  Get Agent from app.state │
│  Get/Create Thread        │
└───────────┬───────────────┘
            │
            ▼
┌───────────────────────────┐
│  agent.run(message)       │
│  Sends to Azure Foundry   │
└───────────┬───────────────┘
            │
            ▼
┌───────────────────────────┐
│  Agent Decision-Making    │
│  (May call tools)         │
└───────────┬───────────────┘
            │
            ▼
┌───────────────────────────┐
│  Return RagResult         │
│  Extract text             │
└───────────┬───────────────┘
            │
            ▼
Client Response:
    {"response": "...", "conversation_id": "..."}
```

### Running Locally

```bash
# Development mode with auto-reload
uv run uvicorn api.main:create_app --factory --reload

# Access at http://localhost:8000
```

### Testing the Application

```bash
# Test agent status
curl http://localhost:8000/agent

# Test chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is in the database?"}'

# Test with conversation
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me more", "conversation_id": "abc-123"}'
```

---

## Production Server Configuration (Gunicorn)

### Configuration (`src/gunicorn.conf.py`)

```python
import multiprocessing

# Server socket
bind = "0.0.0.0:50505"

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Startup validation
def on_starting(server):
    \"\"\"Validate environment before starting.\"\"\"
    required_vars = ["AZURE_AI_PROJECT_ENDPOINT"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {missing}")
```

### Running with Gunicorn

```bash
# Production mode
uv run gunicorn -c src/gunicorn.conf.py "api.main:create_app()"

# With custom workers
uv run gunicorn -c src/gunicorn.conf.py -w 4 "api.main:create_app()"
```

---

## Production Best Practices

### 1. Configuration Management

**✅ Use Environment Variables:**
```python
# .env file
AZURE_AI_PROJECT_ENDPOINT=https://...
AZURE_AI_MODEL_NAME=gpt-4o
NEO4J_URI=neo4j+s://...
```

**✅ Validate on Startup:**
```python
if not config.project_endpoint:
    logger.error("Missing AZURE_AI_PROJECT_ENDPOINT")
    sys.exit(1)
```

**❌ Avoid Hardcoding:**
```python
# Bad
endpoint = "https://my-project.api.azureml.ms"

# Good
endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
```

### 2. Logging and Monitoring

**Structured Logging:**
```python
logger.info(
    "Agent query processed",
    extra={
        "conversation_id": conv_id,
        "query_length": len(query),
        "response_time_ms": elapsed
    }
)
```

**Azure Monitor Integration:**
```python
if os.getenv("ENABLE_AZURE_MONITOR_TRACING") == "true":
    from azure.monitor.opentelemetry import configure_azure_monitor
    configure_azure_monitor(connection_string=conn_str)
```

### 3. Error Handling

**Graceful Degradation:**
```python
try:
    neo4j_client, schema = await initialize_neo4j(stack)
except ConnectionError as e:
    logger.warning(f"Neo4j unavailable: {e}")
    neo4j_client, schema = None, None
    # Continue without Neo4j features
```

**User-Friendly Errors:**
```python
@router.post("/chat")
async def chat(request: Request, chat_request: ChatRequest):
    try:
        result = await agent.run(chat_request.message)
        return {"response": result.text}
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred processing your request. Please try again."
        )
```

### 4. Security Best Practices

**Never Log Secrets:**
```python
# Bad
logger.info(f"Connecting with password: {password}")

# Good
logger.info("Connecting to Neo4j...")
```

**Validate Inputs:**
```python
class ChatRequest(BaseModel):
    message: str = Field(..., max_length=4000)
    conversation_id: str | None = Field(None, max_length=100)
```

**Use Environment for Secrets:**
```bash
# Use Azure Key Vault or similar for production
export NEO4J_PASSWORD=$(az keyvault secret show ...)
```

### 5. Scaling Considerations

**Connection Pooling:**
```python
# Neo4j driver handles pooling automatically
driver = AsyncGraphDatabase.driver(
    uri,
    auth=(username, password),
    max_connection_pool_size=50
)
```

**Worker Configuration:**
```python
# gunicorn.conf.py
workers = min(cpu_count() * 2, 8)  # Cap at 8 workers
```

**Rate Limiting:**
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@router.post("/chat")
@limiter.limit("10/minute")
async def chat(request: Request, ...):
    ...
```

---

## Deployment Architecture

### Azure Container App Deployment

```
┌─────────────────────────────────────────┐
│      Azure Container App                │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  Docker Container                  │ │
│  │  - FastAPI App                     │ │
│  │  - Gunicorn Workers               │ │
│  │  - Python 3.11                    │ │
│  └───────────────────────────────────┘ │
│                                         │
│  Auto-scaling: 1-10 instances          │
│  Health check: GET /agent              │
└─────────────────────────────────────────┘
         │                    │
         │                    │
         ▼                    ▼
┌──────────────┐    ┌──────────────────┐
│  Azure AI    │    │  Neo4j AuraDB    │
│  Foundry     │    │                  │
└──────────────┘    └──────────────────┘
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --prerelease=allow

# Copy application code
COPY src/ src/

# Expose port
EXPOSE 50505

# Run with gunicorn
CMD ["uv", "run", "gunicorn", "-c", "src/gunicorn.conf.py", "api.main:create_app()"]
```

### Deploy with Azure Developer CLI

```bash
# Deploy infrastructure + app
azd up

# Update app code only
azd deploy

# View logs
azd logs --follow
```

---

## Summary

Excellent work! You've learned how to build production-ready AI applications. Let's recap:

### Key Concepts

✅ **Application Architecture**
- FastAPI with lifespan management
- Dependency injection via app.state
- Async context managers for resources

✅ **Configuration Management**
- Pydantic Settings for type-safe config
- Environment variable validation
- Sensible defaults

✅ **Agent Integration**
- Factory pattern for agent creation
- Persistent agents in Azure Foundry
- Thread management for conversations

✅ **Production Practices**
- Structured logging
- Graceful error handling
- Security best practices
- Scalability patterns

### What's Next

In [**Module 6: Summary and Next Steps**](06_summary_and_next_steps.md), you'll:
- Review everything you've learned
- Explore advanced topics
- Find community resources
- Chart your learning path forward

### Quick Reference

**Run Application:**
```bash
# Development
uv run uvicorn api.main:create_app --factory --reload

# Production
uv run gunicorn -c src/gunicorn.conf.py "api.main:create_app()"

# Docker
docker build -t my-app .
docker run -p 8000:50505 --env-file .env my-app
```

**Deploy to Azure:**
```bash
azd up      # Full deployment
azd deploy  # App only
```

---

Ready to wrap up? Continue to [**Module 6: Summary and Next Steps**](06_summary_and_next_steps.md)!
