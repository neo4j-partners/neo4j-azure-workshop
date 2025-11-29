# Microsoft Agent Framework and Azure SDK Architecture

This document explains how the Microsoft Agent Framework and Azure AI SDKs work together to create AI agents that run on Azure AI Foundry.

## Two Layer Architecture

Building agents with Azure AI Foundry involves two distinct layers:

1. **Azure SDKs (Low Level)**: Direct access to Azure AI Foundry APIs
2. **Microsoft Agent Framework (High Level)**: Productivity layer built on top of the Azure SDKs

Both layers register agents in the Azure AI Foundry portal. The difference is the level of abstraction and convenience features provided.

## Layer 1: Azure SDKs

The Azure SDKs provide direct access to Azure AI Foundry APIs. There are two versions:

### azure-ai-agents (V1)

The original Agents SDK focused specifically on the Agents API.

- Uses the thread/message/run model (similar to OpenAI Assistants)
- Requires manual management of agent lifecycle
- Requires manual handling of tool calls and outputs
- Package: `azure-ai-agents`

### azure-ai-projects (V2)

The newer Azure AI Projects SDK that includes agents as part of a broader project concept.

- Uses the Responses API pattern
- Provides project level features beyond just agents
- Recommended path going forward
- Package: `azure-ai-projects`

When using these SDKs directly you must:

- Create agents manually with JSON tool definitions
- Create and manage threads explicitly
- Poll for run completion
- Handle tool calls by parsing JSON and submitting outputs
- Clean up agents when done

## Layer 2: Microsoft Agent Framework

The Microsoft Agent Framework is a productivity layer built on top of the Azure SDKs. It provides:

**Automatic Agent Lifecycle Management**

The framework creates agents when you enter an async context and cleans them up when you exit. You do not need to track agent IDs or call delete methods.

**Simple Tool Definitions**

Tools can be defined as plain Python functions with docstrings. The framework automatically converts them to the JSON schema format required by the API.

**Built-in Streaming**

The `run_stream()` method provides async iteration over response chunks without manual SSE parsing.

**Thread Management**

The framework handles thread creation internally for simple cases. For multi-turn conversations you can use `get_new_thread()` and pass the thread to subsequent calls.

**Multi-Provider Support**

The same framework patterns work across Azure AI Foundry, OpenAI, Anthropic, and other providers.

### Framework Clients for Azure

The framework provides two client classes for Azure AI Foundry:

| Client | Wraps | SDK Version |
|--------|-------|-------------|
| `AzureAIAgentClient` | `azure.ai.agents.AgentsClient` | V1 |
| `AzureAIClient` | `azure.ai.projects.AIProjectClient` | V2 |

This project uses `AzureAIClient` (V2) which aligns with current Microsoft documentation.

## How Agents Get Registered

Both layers register agents in the Azure AI Foundry portal through the same underlying APIs. The registration happens when:

1. You call the agent creation method (either directly via SDK or through the framework)
2. The SDK sends a request to Azure AI Foundry
3. Azure AI Foundry creates the agent and returns an agent ID
4. The agent appears in the Azure AI Foundry portal under your project

The framework handles steps 1-3 automatically when you enter the `create_agent()` context manager.

## Code References

### Framework Usage (This Project)

The API uses the Microsoft Agent Framework with `AzureAIClient`:

**Agent Configuration and Client Creation**

See `src/agent.py` lines 54-76:

```python
def create_agent_client(config: AgentConfig, credential: AzureCliCredential) -> AzureAIClient:
    client_kwargs = {"async_credential": credential}
    if config.project_endpoint:
        client_kwargs["project_endpoint"] = config.project_endpoint
    if config.model:
        client_kwargs["model_deployment_name"] = config.model
    return AzureAIClient(**client_kwargs)
```

**Agent Context Creation**

See `src/agent.py` lines 79-94:

```python
def create_agent_context(client: AzureAIClient, config: AgentConfig):
    return client.create_agent(
        name=config.name,
        instructions=config.instructions,
    )
```

**Running the Agent with Streaming**

See `src/api/routes.py` lines 93-96:

```python
async for update in agent.run_stream(chat_request.message, thread=thread, store=False):
    if update.text:
        response_content += update.text
```

### Workshop Examples

The workshop notebooks demonstrate the same patterns:

**Simple Agent**

See `new-workshops/solutions/02_01_simple_agent.py` lines 38-55:

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

**Tool Definition**

Tools are simple Python functions. See `new-workshops/solutions/02_01_simple_agent.py` lines 21-27:

```python
def create_schema_tool(driver):
    def get_graph_schema() -> str:
        """Get the schema of the graph database including node labels, relationships, and properties."""
        return get_schema(driver)
    return get_graph_schema
```

The framework reads the function name and docstring to create the tool definition that gets sent to Azure AI Foundry.

## Thread Management Patterns

### Single Turn (No Thread Needed)

For simple one-shot queries the framework creates a thread automatically:

```python
async for update in agent.run_stream(query):
    print(update.text)
```

### Multi-Turn Conversations

For conversations that span multiple requests you create and reuse a thread:

```python
thread = agent.get_new_thread()

# First message
result1 = await agent.run("Hello", thread=thread, store=False)

# Follow-up message (same thread maintains context)
result2 = await agent.run("Tell me more", thread=thread, store=False)
```

The `store=False` parameter keeps messages in memory only. Use `store=True` (default) to persist messages to the Azure service.

See `src/api/routes.py` lines 51-62 for the API implementation of multi-turn conversations.

## Framework Source References

For deeper understanding of the framework internals:

| Component | Location |
|-----------|----------|
| AzureAIClient source | `/Users/ryanknight/projects/azure/agent-framework/python/packages/azure-ai/agent_framework_azure_ai/_client.py` |
| V2 samples | `/Users/ryanknight/projects/azure/agent-framework/python/samples/getting_started/agents/azure_ai/` |
| Framework documentation | https://learn.microsoft.com/agent-framework/overview/agent-framework-overview |

## Summary

The Microsoft Agent Framework provides a clean abstraction over the Azure AI SDKs:

- **You write**: Simple Python functions and high level configuration
- **Framework handles**: JSON schemas, API calls, lifecycle management, streaming
- **Azure AI Foundry**: Hosts and runs your agents

This separation allows you to focus on agent behavior rather than API plumbing while still having full access to Azure AI Foundry capabilities.
