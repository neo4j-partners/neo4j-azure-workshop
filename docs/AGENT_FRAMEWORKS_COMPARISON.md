# Agent Frameworks Comparison: Microsoft Agent Framework vs Strands Agents SDK

## Executive Summary

This tutorial provides an in-depth comparison between two powerful agent frameworks for building AI applications: **Microsoft Agent Framework** and **Strands Agents SDK**. Both frameworks enable developers to create sophisticated AI agents, but they differ significantly in their architecture, design philosophy, and ideal use cases.

**Why This Comparison Matters for Azure + Neo4j Projects:**
- Understanding the trade-offs between enterprise-grade orchestration and lightweight development
- Choosing the right framework based on your technical requirements and constraints
- Leveraging the strengths of each framework for specific use cases
- Integrating with Neo4j graph databases for GraphRAG applications

**What This Document Covers:**
1. Quick comparison table highlighting key differences
2. Decision guide to help you choose the right framework
3. Deep dive into 10 key dimensions of comparison
4. Side-by-side code examples
5. Use case recommendations for Neo4j + Azure projects

---

## Quick Comparison Table

| Dimension | Microsoft Agent Framework | Strands Agents SDK |
|-----------|---------------------------|-------------------|
| **Primary Language Support** | .NET + Python (full parity) | Python only |
| **Architecture** | Workflow-based with ExecutorBindings | Event Loop-based |
| **Multi-Agent Patterns** | Sequential/Concurrent/Handoffs/Graph | Swarm with dynamic handoffs |
| **State Management** | Checkpointing & workflow state | Session management |
| **Observability** | Built-in OpenTelemetry | Custom tracing & callbacks |
| **Model Providers** | Azure OpenAI (primary), OpenAI, Anthropic | Multi-cloud (Bedrock, Anthropic, OpenAI, Gemini, etc.) |
| **Complexity** | Enterprise-grade workflows | Lightweight & flexible |
| **Best For** | Complex orchestration & enterprise | Quick prototyping & flexibility |

---

## Decision Guide

### Choose Microsoft Agent Framework if:

✅ You need **.NET support** alongside Python  
✅ **Complex workflow orchestration** is required (graph-based execution)  
✅ **Enterprise Azure integration** is a priority  
✅ You need **time-travel debugging** and checkpointing capabilities  
✅ Strong typing and protocol descriptors are important  
✅ Built-in OpenTelemetry observability is valuable  

### Choose Strands Agents SDK if:

✅ **Python-only** environment is sufficient  
✅ **Simple, fast agent development** is a priority  
✅ You prefer **event loop architecture** over workflow graphs  
✅ **Multi-cloud model providers** are needed (AWS, GCP, etc.)  
✅ **Swarm-style collaboration** patterns are preferred  
✅ Lightweight dependencies and minimal complexity  
✅ Rapid prototyping and iteration speed matter most  

---

## Deep Dive Sections

### 1. Architecture & Design Philosophy

#### Microsoft Agent Framework

**Workflow-Based Architecture:**
- Graph-based orchestration using nodes (executors) and edges (transitions)
- **ExecutorBindings** define how executors connect and communicate
- **Protocol descriptors** provide type safety across executor boundaries
- **StateManager** maintains workflow state across execution steps
- Designed for complex, long-running enterprise workflows
- Consistent APIs across .NET and Python

**Key Design Principles:**
- Declarative workflow definition
- Type-safe communication between components
- Checkpointing and recovery for reliability
- Built-in observability with OpenTelemetry

#### Strands Agents SDK

**Event Loop-Based Architecture:**
- Simple agent invocation model with minimal boilerplate
- **Callback-driven events** for real-time updates
- **Conversation manager** handles context and history
- Model-driven approach with flexible provider support
- Designed for rapid development and iteration

**Key Design Principles:**
- Imperative, straightforward agent creation
- Event-driven asynchronous patterns
- Minimal abstractions and lightweight dependencies
- Maximum flexibility in model provider selection

---

### 2. Agent Execution Models

#### Microsoft Agent Framework - Workflow Execution

```python
from agent_framework import WorkflowBuilder, Executor
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential

# Define executors (workflow steps)
class DataCollectorExecutor(Executor):
    async def execute(self, input_data):
        # Collect data logic
        return {"data": "collected"}

class DataProcessorExecutor(Executor):
    async def execute(self, input_data):
        # Process data logic
        return {"processed": input_data["data"]}

# Create workflow with executors
workflow = WorkflowBuilder(starting_executor=DataCollectorExecutor())
    .add_edge(DataCollectorExecutor(), DataProcessorExecutor())
    .build()

# Run workflow
async for event in workflow.run(input_data={"query": "process data"}):
    print(f"Workflow event: {event}")
```

#### Strands Agents - Event Loop

```python
from strands import Agent
from strands.tools import tool

@tool
def calculator(a: float, b: float, operation: str) -> float:
    """Calculate mathematical expressions safely"""
    ops = {"+": lambda x, y: x + y, "-": lambda x, y: x - y,
           "*": lambda x, y: x * y, "/": lambda x, y: x / y}
    return ops[operation](a, b)

# Simple agent creation
agent = Agent(
    model="bedrock",
    tools=[calculator],
    system_prompt="You are a helpful math assistant."
)

# Direct invocation
result = agent("What is 25 * 4?")
print(result.message)
```

---

### 3. Multi-Agent Orchestration

#### Microsoft Agent Framework

**Sequential Workflows:**
```python
from agent_framework import AgentWorkflowBuilder

# Sequential agent chain
workflow = AgentWorkflowBuilder.BuildSequential(
    workflowName="translation-chain",
    agents=[
        french_translation_agent,
        spanish_translation_agent,
        english_translation_agent
    ]
)

result = await workflow.run("Translate this text")
```

**Concurrent Workflows:**
```python
# Parallel agent execution
workflow = AgentWorkflowBuilder.BuildConcurrent(
    workflowName="parallel-analysis",
    agents=[
        sentiment_analyzer,
        entity_extractor,
        topic_classifier
    ]
)

results = await workflow.run("Analyze this document")
```

**Handoff Patterns:**
```python
from agent_framework import HandoffsWorkflowBuilder

# Agent handoffs with routing logic
workflow = HandoffsWorkflowBuilder()
    .add_agent(triage_agent)
    .add_handoff(triage_agent, technical_agent, condition="is_technical")
    .add_handoff(triage_agent, sales_agent, condition="is_sales")
    .build()
```

#### Strands Agents

**Swarm Orchestration:**
```python
from strands.multiagent import Swarm
from strands import Agent

# Define specialized agents
researcher = Agent(
    model="bedrock",
    system_prompt="You are a research specialist."
)

writer = Agent(
    model="bedrock",
    system_prompt="You are a content writer."
)

reviewer = Agent(
    model="bedrock",
    system_prompt="You are a quality reviewer."
)

# Create swarm with dynamic handoffs
swarm = Swarm(
    agents=[researcher, writer, reviewer],
    max_iterations=10
)

result = await swarm.execute("Research and write an article about AI agents")
```

**Agent-to-Agent Transfer:**
```python
from strands import Agent

def transfer_to_specialist():
    """Transfer to specialist agent"""
    return specialist_agent

generalist = Agent(
    model="bedrock",
    tools=[transfer_to_specialist],
    system_prompt="Transfer complex queries to specialist."
)
```

---

### 4. Tool Integration

#### Microsoft Agent Framework

```python
from agent_framework import tool
from agent_framework.azure import AzureOpenAIResponsesClient

@tool
def get_weather(location: str) -> str:
    """Get current weather for a location"""
    # Weather API call
    return f"Weather in {location}: Sunny, 72°F"

@tool
def search_database(query: str) -> dict:
    """Search the knowledge base"""
    # Database query logic
    return {"results": ["result1", "result2"]}

# Create agent with tools
agent = AzureOpenAIResponsesClient(
    credential=AzureCliCredential()
).create_agent(
    name="Assistant",
    instructions="You are a helpful assistant with access to tools.",
    tools=[get_weather, search_database]
)

response = await agent.run("What's the weather in Seattle?")
```

#### Strands Agents

```python
from strands import Agent, tool
from strands.tools.mcp import MCPClient
from mcp import StdioServerParameters, stdio_client

@tool
def calculator(a: float, b: float, operation: str) -> float:
    """Calculate mathematical expressions safely"""
    ops = {"+": lambda x, y: x + y, "-": lambda x, y: x - y,
           "*": lambda x, y: x * y, "/": lambda x, y: x / y}
    return ops[operation](a, b)

@tool  
def web_search(query: str) -> list:
    """Search the web for information"""
    # Search API logic
    return ["result1", "result2"]

# MCP (Model Context Protocol) Support
server_params = StdioServerParameters(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
)

mcp_client = MCPClient(lambda: stdio_client(server_params))

# Create agent with tools and MCP
agent = Agent(
    model="bedrock",
    tools=[calculator, web_search] + mcp_client.list_tools_sync(),
    system_prompt="You are a helpful assistant with various tools."
)

result = agent("Calculate 15 * 23 and search for AI agents")
```

---

### 5. State Management & Checkpointing

#### Microsoft Agent Framework

**Workflow Checkpointing:**
```python
from agent_framework import WorkflowBuilder, CheckpointManager
from agent_framework.state import StateManager

# Setup checkpoint manager for workflow recovery
checkpoint_manager = CheckpointManager(storage_path="./checkpoints")

workflow = WorkflowBuilder(starting_executor)
    .add_edge(executor1, executor2)
    .add_edge(executor2, executor3)
    .build()

# Create agent with checkpointing
agent = workflow.as_agent(
    checkpoint_manager=checkpoint_manager,
    enable_time_travel=True
)

# Execute with automatic checkpointing
result = await agent.run(input_data)

# Resume from checkpoint
restored_agent = agent.restore_from_checkpoint(checkpoint_id="abc123")
```

**State Management:**
```python
from agent_framework.state import StateManager

# Scoped state management
state_manager = StateManager()

# Set workflow state
await state_manager.set("user_context", {"user_id": "123"})
await state_manager.set("session_data", {"started_at": "2025-01-01"})

# Get state in executor
user_context = await state_manager.get("user_context")
```

#### Strands Agents

**Session Management:**
```python
from strands import Agent, AgentState
from strands.session import SessionManager

# Session-based state persistence
session_manager = SessionManager(storage_path="./sessions")

agent = Agent(
    model="bedrock",
    session_manager=session_manager,
    agent_id="customer-support-agent",
    state=AgentState(
        user_context={"user_id": "123"},
        preferences={"language": "en"}
    )
)

# State persists across invocations
result1 = agent("Hello!")
result2 = agent("What did we discuss?")  # Has conversation history
```

**Conversation History:**
```python
from strands import Agent

agent = Agent(
    model="bedrock",
    conversation_history=[
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi! How can I help?"}
    ]
)

# Continue conversation
result = agent("Tell me more about agents")
```

---

### 6. Observability

#### Microsoft Agent Framework

**Built-in OpenTelemetry:**
```python
from agent_framework.observability import setup_observability
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Setup distributed tracing
setup_observability(
    service_name="my-agent-workflow",
    exporter="otlp",  # or "console", "jaeger"
    endpoint="http://localhost:4317"
)

# Automatic span creation for executors
workflow = WorkflowBuilder(starting_executor)
    .add_edge(executor1, executor2)
    .build()

# All executor calls are automatically traced
result = await workflow.run(input_data)

# Custom spans
tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("custom-operation"):
    # Your code here
    pass
```

**Workflow Spans:**
- Automatic span creation for each executor
- Parent-child span relationships
- Distributed tracing across services
- Integration with Azure Monitor, Jaeger, Zipkin

#### Strands Agents

**Custom Tracer Integration:**
```python
from strands import Agent

def custom_handler(**event):
    """Handle agent events for observability"""
    if "data" in event:
        print(f"Stream data: {event['data']}")
    if "tool_call" in event:
        print(f"Tool called: {event['tool_call']}")
    if "error" in event:
        print(f"Error occurred: {event['error']}")

agent = Agent(
    model="bedrock",
    callback_handler=custom_handler
)

result = agent("Process this request")
```

**Event-Based Monitoring:**
```python
from strands import Agent
import logging

# Setup logging for monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def monitoring_callback(**event):
    logger.info(f"Agent event: {event.get('type')}")
    if event.get('type') == 'tool_call':
        logger.info(f"Tool: {event['tool_name']}, Args: {event['args']}")

agent = Agent(
    model="bedrock",
    callback_handler=monitoring_callback,
    tools=[my_tool]
)
```

---

### 7. Language & Platform Support

#### Microsoft Agent Framework

**Python Support:**
```python
# Full async/await support
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential

agent = AzureOpenAIResponsesClient(
    credential=AzureCliCredential()
).create_agent(
    name="Assistant",
    instructions="You are helpful."
)

response = await agent.run("Hello!")
```

**.NET Support (C#):**
```csharp
using Microsoft.AgentFramework;
using Azure.Identity;

// Full feature parity with Python
var agent = new AzureOpenAIResponsesClient(
    new DefaultAzureCredential()
).CreateAgent(
    name: "Assistant",
    instructions: "You are helpful."
);

var response = await agent.RunAsync("Hello!");
```

**Key Features:**
- Consistent APIs across Python and .NET
- Same workflow patterns in both languages
- Shared concepts and terminology
- Enterprise integration patterns (Azure, Active Directory)

#### Strands Agents

**Python 3.10+ Only:**
```python
from strands import Agent
from strands.models import BedrockModel

# Python-only with modern async support
agent = Agent(
    model=BedrockModel(model_id="us.amazon.nova-pro-v1:0"),
    system_prompt="You are helpful."
)

result = agent("Hello!")

# Async support
async for event in agent.stream_async("Tell me a story"):
    print(event)
```

**Key Features:**
- Modern Python with type hints
- Async-first design
- Lightweight, minimal dependencies
- Fast development cycle

---

### 8. Model Provider Support

#### Microsoft Agent Framework

**Primary: Azure OpenAI**
```python
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import DefaultAzureCredential

client = AzureOpenAIResponsesClient(
    credential=DefaultAzureCredential(),
    endpoint="https://your-resource.openai.azure.com/",
    model_deployment="gpt-4"
)

agent = client.create_agent(
    name="Assistant",
    instructions="You are helpful."
)
```

**OpenAI:**
```python
from agent_framework.openai import OpenAIResponsesClient

client = OpenAIResponsesClient(
    api_key="your-api-key",
    model="gpt-4"
)

agent = client.create_agent(
    name="Assistant",
    instructions="You are helpful."
)
```

**Anthropic:**
```python
from agent_framework.anthropic import AnthropicClient

client = AnthropicClient(
    api_key="your-api-key",
    model="claude-3-opus-20240229"
)

agent = client.create_agent(
    name="Assistant",
    instructions="You are helpful."
)
```

#### Strands Agents

**Multi-Cloud Provider Support:**
```python
from strands import Agent
from strands.models import (
    BedrockModel,      # AWS Bedrock
    AnthropicModel,    # Anthropic Claude
    OpenAIModel,       # OpenAI
    GeminiModel,       # Google Gemini
    OllamaModel,       # Local Ollama
    LiteLLMModel,      # LiteLLM proxy
    LlamaCppModel,     # llama.cpp
    SageMakerModel,    # AWS SageMaker
    WriterModel,       # Writer
    CohereModel        # Cohere
)

# AWS Bedrock (default)
agent = Agent(
    model=BedrockModel(model_id="us.amazon.nova-pro-v1:0")
)

# Anthropic
agent = Agent(
    model=AnthropicModel(model_id="claude-3-5-sonnet-20241022")
)

# OpenAI
agent = Agent(
    model=OpenAIModel(model_id="gpt-4")
)

# Google Gemini
agent = Agent(
    model=GeminiModel(model_id="gemini-2.0-flash-exp")
)

# Local Ollama
agent = Agent(
    model=OllamaModel(model_id="llama3.2")
)
```

**Highly Extensible:**
- Easy to add custom providers
- Unified interface across all providers
- Automatic credential management
- Support for local and hosted models

---

### 9. Code Examples: Side-by-Side

#### Example 1: Creating a Simple Agent

**Microsoft Agent Framework:**
```python
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential

# Create agent using Azure OpenAI
agent = AzureOpenAIResponsesClient(
    credential=AzureCliCredential(),
    endpoint="https://your-resource.openai.azure.com/"
).create_agent(
    name="Assistant",
    instructions="You are a helpful assistant."
)

# Run agent
response = await agent.run("Hello! Tell me about AI agents.")
print(response)
```

**Strands Agents:**
```python
from strands import Agent
from strands.models import BedrockModel

# Create agent using AWS Bedrock
agent = Agent(
    model=BedrockModel(model_id="us.amazon.nova-pro-v1:0"),
    system_prompt="You are a helpful assistant."
)

# Run agent
result = agent("Hello! Tell me about AI agents.")
print(result.message)
```

---

#### Example 2: Streaming Responses

**Microsoft Agent Framework:**
```python
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential

agent = AzureOpenAIResponsesClient(
    credential=AzureCliCredential()
).create_agent(
    name="Assistant",
    instructions="You are helpful."
)

# Stream responses
messages = [{"role": "user", "content": "Tell me a long story"}]
async for update in agent.run_streaming(messages):
    if update.content:
        print(update.content, end="", flush=True)
```

**Strands Agents:**
```python
from strands import Agent
from strands.models import BedrockModel

agent = Agent(
    model=BedrockModel(model_id="us.amazon.nova-pro-v1:0"),
    system_prompt="You are helpful."
)

# Stream responses
async for event in agent.stream_async("Tell me a long story"):
    if "data" in event:
        print(event["data"], end="", flush=True)
```

---

#### Example 3: Agent with Tools

**Microsoft Agent Framework:**
```python
from agent_framework import tool
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential
import neo4j

@tool
def query_neo4j(cypher: str) -> list:
    """Execute a Cypher query against Neo4j"""
    driver = neo4j.GraphDatabase.driver(
        "neo4j://localhost:7687",
        auth=("neo4j", "password")
    )
    with driver.session() as session:
        result = session.run(cypher)
        return [record.data() for record in result]

agent = AzureOpenAIResponsesClient(
    credential=AzureCliCredential()
).create_agent(
    name="Neo4jAssistant",
    instructions="You can query Neo4j databases.",
    tools=[query_neo4j]
)

response = await agent.run("Show me all companies in the database")
```

**Strands Agents:**
```python
from strands import Agent, tool
from strands.models import BedrockModel
import neo4j

@tool
def query_neo4j(cypher: str) -> list:
    """Execute a Cypher query against Neo4j"""
    driver = neo4j.GraphDatabase.driver(
        "neo4j://localhost:7687",
        auth=("neo4j", "password")
    )
    with driver.session() as session:
        result = session.run(cypher)
        return [record.data() for record in result]

agent = Agent(
    model=BedrockModel(model_id="us.amazon.nova-pro-v1:0"),
    tools=[query_neo4j],
    system_prompt="You can query Neo4j databases."
)

result = agent("Show me all companies in the database")
print(result.message)
```

---

#### Example 4: Multi-Agent Workflow

**Microsoft Agent Framework:**
```python
from agent_framework import AgentWorkflowBuilder
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential

client = AzureOpenAIResponsesClient(credential=AzureCliCredential())

# Create specialized agents
researcher = client.create_agent(
    name="Researcher",
    instructions="You research topics thoroughly."
)

writer = client.create_agent(
    name="Writer",
    instructions="You write clear, engaging content."
)

editor = client.create_agent(
    name="Editor",
    instructions="You edit and improve content."
)

# Build sequential workflow
workflow = AgentWorkflowBuilder.BuildSequential(
    workflowName="content-creation",
    agents=[researcher, writer, editor]
)

# Execute workflow
result = await workflow.run("Write an article about AI agents")
```

**Strands Agents:**
```python
from strands import Agent
from strands.multiagent import Swarm
from strands.models import BedrockModel

# Create specialized agents
researcher = Agent(
    model=BedrockModel(model_id="us.amazon.nova-pro-v1:0"),
    system_prompt="You research topics thoroughly."
)

writer = Agent(
    model=BedrockModel(model_id="us.amazon.nova-pro-v1:0"),
    system_prompt="You write clear, engaging content."
)

editor = Agent(
    model=BedrockModel(model_id="us.amazon.nova-pro-v1:0"),
    system_prompt="You edit and improve content."
)

# Create swarm
swarm = Swarm(
    agents=[researcher, writer, editor],
    max_iterations=10
)

# Execute swarm
result = await swarm.execute("Write an article about AI agents")
```

---

### 10. Use Cases & Recommendations

#### Use Microsoft Agent Framework When:

✅ **Building Enterprise Applications**
- Complex, multi-step workflows with branching logic
- Need for .NET integration alongside Python
- Requirements for time-travel debugging and checkpointing
- Enterprise Azure integration (Active Directory, Azure services)

✅ **Complex Orchestration Requirements**
- Graph-based execution flows with conditional routing
- Long-running workflows that need recovery capabilities
- Multiple agents with sophisticated handoff patterns
- Strong typing and protocol descriptors are valuable

✅ **Azure-First Architecture**
- Primary cloud provider is Azure
- Deep integration with Azure AI Foundry
- Leveraging Azure OpenAI as primary model provider
- Need for Azure-native observability (Azure Monitor)

✅ **Regulated Industries**
- Financial services, healthcare, government
- Strong audit trail requirements
- Workflow reproducibility and compliance
- Enterprise-grade security and governance

**Example Use Cases:**
- Financial document processing pipelines
- Healthcare patient data workflows
- Multi-step customer support automation
- Complex data transformation pipelines
- Enterprise knowledge management systems

---

#### Use Strands Agents When:

✅ **Rapid Prototyping & Development**
- Quick iteration on agent designs
- Experimental features and ideas
- Proof of concepts and demos
- Startup environments with fast-moving requirements

✅ **Simple to Moderate Complexity**
- Straightforward agent logic without complex orchestration
- Event-driven architectures
- Single-agent or simple multi-agent scenarios
- Swarm-style collaboration is sufficient

✅ **Multi-Cloud Model Flexibility**
- Using AWS Bedrock, Anthropic, OpenAI, Gemini
- Need to switch between providers easily
- Cost optimization across different model providers
- Hybrid cloud or multi-cloud strategy

✅ **Python-Centric Teams**
- No .NET requirements
- Python expertise and preferences
- Modern Python async patterns
- Lightweight, minimal dependencies preferred

**Example Use Cases:**
- Research and content creation tools
- Interactive chatbots and assistants
- Data analysis and reporting agents
- Code generation and review tools
- Educational and learning applications

---

#### For Neo4j + Azure Projects:

**Microsoft Agent Framework:**
- **Better For:** Complex enterprise workflows with deep Azure integration
- **Strengths:** 
  - Robust workflow orchestration for multi-step graph queries
  - Checkpointing for long-running graph traversals
  - Enterprise security and compliance
  - .NET integration if needed alongside Python

**Strands Agents:**
- **Better For:** Rapid development and multi-cloud scenarios
- **Strengths:**
  - Quick iteration on graph query patterns
  - Flexible model provider selection
  - Simple agent-to-Neo4j integrations
  - Lightweight and fast development cycle

**Both Frameworks Support Neo4j Integration:**
```python
# Custom tool for Neo4j access (works with both frameworks)
@tool
def neo4j_query(cypher: str) -> list:
    """Execute Cypher query against Neo4j"""
    driver = neo4j.GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        result = session.run(cypher)
        return [record.data() for record in result]
```

**Recommendation:**
- Start with **Strands Agents** for rapid prototyping and exploration
- Migrate to **Microsoft Agent Framework** when complexity grows or enterprise features are needed
- Consider **Microsoft Agent Framework** from the start if .NET support or complex workflows are anticipated

---

## Conclusion

Both **Microsoft Agent Framework** and **Strands Agents SDK** are powerful tools for building AI agent applications, but they serve different needs:

### Microsoft Agent Framework
**Excels At:**
- Complex, enterprise-grade workflow orchestration
- Strong typing and multi-language support (.NET + Python)
- Checkpointing, time-travel, and recovery capabilities
- Deep Azure integration and enterprise features
- Graph-based agent collaboration patterns

**Best For:**
- Large enterprises with complex requirements
- Multi-language development teams
- Azure-first architectures
- Regulated industries needing audit trails
- Long-running, mission-critical workflows

### Strands Agents SDK
**Excels At:**
- Rapid development and prototyping
- Flexible, lightweight agent architecture
- Multi-cloud model provider support
- Simple event-driven patterns
- Swarm-style agent collaboration

**Best For:**
- Startups and fast-moving teams
- Python-only environments
- Multi-cloud or provider flexibility needs
- Simple to moderate complexity use cases
- Quick iteration and experimentation

### Making the Choice

**Start Simple, Scale Up:**
1. Begin with **Strands Agents** for initial prototyping
2. Evaluate complexity as your project grows
3. Migrate to **Microsoft Agent Framework** if you need:
   - Complex orchestration
   - .NET support
   - Enterprise features
   - Checkpointing/recovery

**Choose Based on Your Requirements:**
- **Technical Stack:** .NET needed? → Microsoft Agent Framework
- **Cloud Provider:** Azure-only? → Microsoft Agent Framework; Multi-cloud? → Strands Agents
- **Complexity:** Simple agents? → Strands Agents; Complex workflows? → Microsoft Agent Framework
- **Team Velocity:** Rapid prototyping? → Strands Agents; Enterprise pace? → Microsoft Agent Framework

Both frameworks integrate well with Neo4j through custom tools, so your graph database queries and GraphRAG patterns will work regardless of your choice.

---

## Additional Resources

### Microsoft Agent Framework

**Official Documentation:**
- [Agent Framework Overview](https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview)
- [Azure AI Foundry Agent](https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-types/azure-ai-foundry-agent)
- [Microsoft Learn Training Path](https://learn.microsoft.com/en-us/training/paths/develop-ai-agents-on-azure/)

**GitHub and Samples:**
- [GitHub Repository](https://github.com/microsoft/agent-framework)
- [Python Samples](https://github.com/microsoft/agent-framework/tree/main/python/samples)
- [.NET Samples](https://github.com/microsoft/agent-framework/tree/main/dotnet/samples)
- [AI Agents for Beginners](https://github.com/microsoft/ai-agents-for-beginners)

**Blog Posts:**
- [Introducing Microsoft Agent Framework (Azure Blog)](https://azure.microsoft.com/en-us/blog/introducing-microsoft-agent-framework/)
- [Microsoft Foundry Blog Announcement](https://devblogs.microsoft.com/foundry/introducing-microsoft-agent-framework-the-open-source-engine-for-agentic-ai-apps/)

### Strands Agents SDK

**Official Documentation:**
- [Strands Agents Homepage](https://strandsagents.com/)
- [API Reference](https://strandsagents.com/latest/api-reference/agent/)
- [Examples](https://strandsagents.com/latest/examples/)

**GitHub:**
- [GitHub Repository](https://github.com/strands-agents/sdk-python)
- [Example Projects](https://github.com/strands-agents/sdk-python/tree/main/examples)

**Additional Resources:**
- [Getting Started Guide](https://strandsagents.com/latest/getting-started/)
- [Multi-Agent Systems](https://strandsagents.com/latest/multi-agent/)
- [Tool Integration Guide](https://strandsagents.com/latest/tools/)

### Neo4j Resources

- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [Neo4j GraphRAG](https://neo4j.com/docs/graph-data-science/current/algorithms/graph-rag/)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)
- [Neo4j + LLMs Guide](https://neo4j.com/developer-blog/knowledge-graphs-llms-multi-hop-question-answering/)

### Azure Resources

- [Azure AI Foundry](https://learn.microsoft.com/en-us/azure/ai-foundry/)
- [Azure OpenAI Service](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Azure Identity SDK](https://learn.microsoft.com/en-us/python/api/overview/azure/identity-readme)
