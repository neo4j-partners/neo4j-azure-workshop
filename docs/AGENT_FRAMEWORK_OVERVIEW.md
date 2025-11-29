# Microsoft Agent Framework

This document provides an overview of the Microsoft Agent Framework, its architecture, capabilities, and how it integrates with Azure AI Foundry for agent registration, management, and observability.

## What is the Microsoft Agent Framework?

The Microsoft Agent Framework is a comprehensive Python and .NET framework for building, orchestrating, and deploying AI agents and multi-agent systems. It is designed for production use with features for observability, state management, error handling, and distributed agent communication.

The framework is **not** just a wrapper around Azure SDKs. It is a complete agent framework that can operate independently with any supported LLM provider. When used with Azure AI Foundry, it leverages the `azure-ai-projects` SDK to register and manage agents, enabling the monitoring and evaluation features available in the Azure AI Foundry portal.

## Core Capabilities

### Agent Abstractions

The framework provides a protocol-based agent system using Python structural typing. Any class that implements the agent protocol can function as an agent without requiring inheritance from a base class.

**Key agent types:**

- **ChatAgent**: A simple text-based agent for straightforward conversational use cases
- **BaseAgent**: An abstract base with lifecycle hooks for custom implementations
- **Custom agents**: Any class implementing the `AgentProtocol` interface

Agents support both synchronous (`run()`) and streaming (`run_stream()`) execution modes. The streaming mode provides real-time updates as the agent processes a request.

### Tool System

Tools are defined as plain Python functions using docstrings and type hints. The framework automatically converts these to JSON schemas for LLM function calling.

**Built-in tool types:**

- **AIFunction**: Decorator-based function tools (`@ai_function`)
- **HostedCodeInterpreterTool**: Code execution in sandboxed environments
- **HostedFileSearchTool**: File search across uploaded documents
- **HostedWebSearchTool**: Web search integration
- **MCPTool**: Model Context Protocol server integration

The framework handles tool invocation, timeout management, error recovery, and result formatting automatically.

### Multi-Agent Orchestration

The framework includes a graph-based workflow engine for orchestrating complex multi-agent scenarios.

**Orchestration patterns:**

- **Sequential**: Agents run in order, passing results between steps
- **Concurrent**: Parallel execution with fan-in/fan-out patterns
- **Group Chat**: Multi-agent discussion with AI-powered speaker selection
- **Handoff**: Agent-to-agent transfers based on conversation context
- **Magentic**: Advanced planning with task decomposition and dynamic routing

Workflows support checkpointing for state persistence, event streaming for monitoring, and resumable execution.

### Memory and Context

The framework provides mechanisms for persistent memory and dynamic context injection.

**Components:**

- **AgentThread**: Persistent conversation context across requests
- **ChatMessageStore**: Interface for message persistence (in-memory, Redis, file-based)
- **ContextProvider**: Dynamic injection of instructions, messages, and tools before agent execution
- **AggregateContextProvider**: Combines multiple context providers

### Middleware Pipeline

Three middleware types allow interception and modification at different points in the execution flow:

- **AgentMiddleware**: Intercepts `agent.run()` calls
- **ChatMiddleware**: Intercepts chat client requests to the LLM
- **FunctionMiddleware**: Intercepts tool execution

Middleware can modify requests, filter responses, add logging, or terminate execution early.

### Observability

The framework has built-in OpenTelemetry integration for distributed tracing, metrics, and logging.

**Features:**

- Automatic span creation using GenAI semantic conventions
- Token usage histograms and operation duration metrics
- Chat message logging with timestamps
- Pluggable exporters (OTLP, Azure Monitor, custom backends)

When using Azure AI Foundry, traces and metrics flow to Application Insights for visualization in the portal.

### Human-in-the-Loop

The framework supports approval workflows for sensitive tool executions.

**Content types:**

- **FunctionApprovalRequestContent**: Agent requests user approval before executing a tool
- **FunctionApprovalResponseContent**: User response (approve/reject)

This enables interactive agent execution where humans can review and approve actions before they happen.

## Provider Support

The framework supports multiple LLM providers through a pluggable architecture.

| Provider | Package | Description |
|----------|---------|-------------|
| OpenAI | `agent-framework` (core) | GPT models via OpenAI API |
| Azure OpenAI | `agent-framework` (core) | GPT models via Azure endpoints |
| Azure AI Foundry | `agent-framework-azure-ai` | Service-managed agents with portal integration |
| Anthropic | `agent-framework-anthropic` | Claude models |
| Copilot Studio | `agent-framework-copilotstudio` | Published copilots from Power Platform |
| Agent-to-Agent | `agent-framework-a2a` | Microsoft Graph protocol for distributed agents |

The same agent code works across providers with minimal changes. Switching from OpenAI to Azure AI Foundry requires only changing the client class.

## Azure AI Foundry Integration

When the framework is used with Azure AI Foundry, it leverages the `azure-ai-projects` SDK (V2) to provide additional capabilities:

- **Agent Registration**: Agents appear in the Azure AI Foundry portal under your project
- **Lifecycle Management**: The framework handles agent creation and cleanup automatically
- **Server-Side State**: Threads and messages can be persisted to the Azure service
- **Monitoring**: Traces and metrics flow to Application Insights
- **Evaluation**: Agent runs can be analyzed using Azure AI evaluation tools

The framework provides two client classes for Azure:

| Client | SDK | Use Case |
|--------|-----|----------|
| `AzureAIAgentClient` | `azure-ai-agents` (V1) | Legacy Agents API |
| `AzureAIClient` | `azure-ai-projects` (V2) | Current recommended path |

This project uses `AzureAIClient` (V2) which aligns with current Microsoft documentation.

### How Registration Works

When you create an agent using the framework with Azure AI Foundry:

1. You call `client.create_agent()` which returns an async context manager
2. Entering the context sends a creation request to Azure AI Foundry
3. Azure AI Foundry creates the agent and returns an agent ID
4. The agent appears in the portal under your project
5. Exiting the context automatically deletes the agent (cleanup)

You do not need to manage agent IDs or call delete methods manually.

## Project Code Examples

### Agent Client Creation

The API creates an `AzureAIClient` connected to Azure AI Foundry.

See `src/agent.py:54-76`:

```python
def create_agent_client(config: AgentConfig, credential: AzureCliCredential) -> AzureAIClient:
    client_kwargs = {"async_credential": credential}
    if config.project_endpoint:
        client_kwargs["project_endpoint"] = config.project_endpoint
    if config.model:
        client_kwargs["model_deployment_name"] = config.model
    return AzureAIClient(**client_kwargs)
```

### Agent Context Creation

Agents are created using an async context manager that handles lifecycle.

See `src/agent.py:79-94`:

```python
def create_agent_context(client: AzureAIClient, config: AgentConfig):
    return client.create_agent(
        name=config.name,
        instructions=config.instructions,
    )
```

### Streaming Execution

The agent processes requests and streams responses.

See `src/api/routes.py:93-96`:

```python
async for update in agent.run_stream(chat_request.message, thread=thread, store=False):
    if update.text:
        response_content += update.text
```

### Tool Definition

Tools are Python functions with docstrings. The framework extracts the function name and docstring to create the tool schema.

See `new-workshops/solutions/02_01_simple_agent.py:21-27`:

```python
def create_schema_tool(driver):
    def get_graph_schema() -> str:
        """Get the schema of the graph database including node labels, relationships, and properties."""
        return get_schema(driver)
    return get_graph_schema
```

### Workshop Agent Pattern

The workshop examples demonstrate a complete agent pattern.

See `new-workshops/solutions/02_01_simple_agent.py:38-55`:

```python
async with AzureCliCredential() as credential:
    client = AzureAIClient(
        project_endpoint=config.project_endpoint,
        model_deployment_name=config.model_name,
        async_credential=credential,
    )

    async with client.create_agent(
        name="schema-agent",
        instructions="You are a helpful assistant...",
        tools=[get_graph_schema],
    ) as agent:
        async for update in agent.run_stream(query):
            if update.text:
                print(update.text, end="", flush=True)
```

## Thread Management

### Single Turn (Automatic Thread)

For simple one-shot queries the framework creates a thread automatically:

```python
async for update in agent.run_stream(query):
    print(update.text)
```

### Multi-Turn Conversations

For conversations spanning multiple requests, create and reuse a thread:

```python
thread = agent.get_new_thread()

# First message
result1 = await agent.run("Hello", thread=thread, store=False)

# Follow-up maintains context
result2 = await agent.run("Tell me more", thread=thread, store=False)
```

The `store=False` parameter keeps messages in memory only. Use `store=True` (default) to persist messages to Azure AI Foundry.

See `src/api/routes.py:51-62` for the API implementation of multi-turn conversations.

## Framework Source References

| Component | Location |
|-----------|----------|
| Core agents | `/Users/ryanknight/projects/azure/agent-framework/python/packages/core/agent_framework/_agents.py` |
| Tool system | `/Users/ryanknight/projects/azure/agent-framework/python/packages/core/agent_framework/_tools.py` |
| Workflow engine | `/Users/ryanknight/projects/azure/agent-framework/python/packages/core/agent_framework/_workflows/` |
| Azure AI client | `/Users/ryanknight/projects/azure/agent-framework/python/packages/azure-ai/agent_framework_azure_ai/_client.py` |
| Observability | `/Users/ryanknight/projects/azure/agent-framework/python/packages/core/agent_framework/observability.py` |
| V2 samples | `/Users/ryanknight/projects/azure/agent-framework/python/samples/getting_started/agents/azure_ai/` |
| Documentation | https://learn.microsoft.com/agent-framework/overview/agent-framework-overview |

## Summary

The Microsoft Agent Framework is a production-ready framework for building AI agents. It provides:

- **Protocol-based agents**: Flexible agent implementations without inheritance requirements
- **Automatic tool handling**: Python functions become LLM tools automatically
- **Multi-agent orchestration**: Graph-based workflows for complex scenarios
- **Built-in observability**: OpenTelemetry tracing and metrics
- **Multi-provider support**: Same code works across OpenAI, Azure, Anthropic, and more

When used with Azure AI Foundry, the framework leverages the `azure-ai-projects` SDK for agent registration, lifecycle management, and monitoring. The framework does not require Azure AI Foundry to operate. It can be used standalone with any supported LLM provider.
