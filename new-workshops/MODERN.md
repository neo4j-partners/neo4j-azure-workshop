# Proposal: Modernizing the Simple Agent Notebook

## Overview

This proposal evaluates updating `02_01_simple_agent.ipynb` to align with the latest Azure AI Foundry SDK patterns documented at [Microsoft's quickstart guide](https://learn.microsoft.com/en-us/azure/ai-foundry/quickstarts/get-started-code).

## Current Architecture

The notebook currently uses the **Microsoft Agent Framework** (`agent-framework-azure-ai`):

```python
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import AzureCliCredential

client = AzureAIAgentClient(
    project_endpoint=config.project_endpoint,
    model_deployment_name=config.model_name,
    async_credential=credential,
)

async with client.create_agent(
    name="schema-agent",
    instructions="...",
    tools=tools,
) as agent:
    async for update in agent.run_stream(query, thread=thread):
        print(update.text, end="")
```

**Key characteristics:**
- Uses `AzureAIAgentClient` wrapper from `agent_framework_azure_ai`
- Internally uses `azure.ai.agents.aio.AgentsClient`
- Automatic agent lifecycle management (create/cleanup)
- High-level streaming abstraction via `run_stream()`
- Tools defined as simple Python functions with docstrings

## New Azure AI Foundry SDK Approach

The Microsoft documentation shows a more direct approach using `azure-ai-projects`:

```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

project = AIProjectClient(
    endpoint="https://your-resource.ai.azure.com/api/projects/project-name",
    credential=DefaultAzureCredential(),
)

# Agents v1 API
agent = project.agents.create_agent(
    model="gpt-4o",
    name="my-agent",
    instructions="..."
)

thread = project.agents.threads.create()
message = project.agents.messages.create(
    thread_id=thread.id,
    role="user",
    content="..."
)

run = project.agents.runs.create_and_process(
    thread_id=thread.id,
    agent_id=agent.id
)
```

## Analysis

### Option A: Switch to Native Azure AI Projects SDK

**Pros:**
- Direct alignment with Microsoft's official documentation
- Fewer abstraction layers (no Agent Framework dependency)
- Clearer visibility into the underlying API calls
- More granular control over agent/thread lifecycle
- Better for educational purposes (workshop attendees see real Azure APIs)

**Cons:**
- Loss of streaming abstraction (`run_stream()` convenience)
- More boilerplate code for streaming responses
- Manual agent cleanup required
- Tool definition requires OpenAI function-calling format (not simple Python functions)
- Breaks consistency with other notebooks (02_02, 02_03) that use Agent Framework

### Option B: Keep Microsoft Agent Framework

**Pros:**
- Cleaner, more readable code
- Automatic resource management
- Tools can be simple Python functions
- Consistent with other workshop notebooks
- Built-in streaming support

**Cons:**
- Additional abstraction layer hides Azure AI Foundry concepts
- Dependency on preview/beta package (`agent-framework-azure-ai`)
- Workshop attendees may not recognize the underlying Azure APIs
- Framework may diverge from official Microsoft patterns

### Option C: Hybrid Approach (Recommended)

**Pros:**
- Demonstrates both approaches side-by-side
- Teaches fundamental Azure AI Foundry concepts first
- Then shows the Agent Framework as a productivity enhancement
- Best educational value for workshop attendees

**Cons:**
- Longer notebook
- Slightly more complex to maintain

## Recommendation: Option C (Hybrid)

The notebook should be restructured into two parts:

### Part 1: "Understanding Azure AI Foundry" (Native SDK)

Show the direct Azure AI Projects SDK approach:

```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

# Connect to Azure AI Foundry
project = AIProjectClient(
    endpoint=config.project_endpoint,
    credential=DefaultAzureCredential(),
)

# Create agent with function tool
agent = project.agents.create_agent(
    model="gpt-4o",
    name="schema-agent",
    instructions="You are a helpful assistant...",
    tools=[{
        "type": "function",
        "function": {
            "name": "get_graph_schema",
            "description": "Get the schema of the graph database...",
            "parameters": {"type": "object", "properties": {}}
        }
    }]
)

# Create thread and message
thread = project.agents.threads.create()
message = project.agents.messages.create(
    thread_id=thread.id,
    role="user",
    content="Summarise the schema of the graph database."
)

# Run with manual tool handling
run = project.agents.runs.create(thread_id=thread.id, agent_id=agent.id)

# Poll for completion and handle tool calls
while run.status in ["queued", "in_progress", "requires_action"]:
    if run.status == "requires_action":
        tool_outputs = []
        for tool_call in run.required_action.submit_tool_outputs.tool_calls:
            if tool_call.function.name == "get_graph_schema":
                result = get_graph_schema()
                tool_outputs.append({"tool_call_id": tool_call.id, "output": result})
        run = project.agents.runs.submit_tool_outputs(
            thread_id=thread.id,
            run_id=run.id,
            tool_outputs=tool_outputs
        )
    run = project.agents.runs.get(thread_id=thread.id, run_id=run.id)

# Get response
messages = project.agents.messages.list(thread_id=thread.id)
print(messages.data[0].content[0].text.value)

# Cleanup
project.agents.delete_agent(agent.id)
```

This demonstrates:
- How Azure AI Foundry agents work at a fundamental level
- The thread/message/run lifecycle
- Manual tool call handling
- Resource management responsibilities

### Part 2: "Simplifying with Agent Framework" (Current Approach)

Then show how the Agent Framework abstracts this:

```python
from agent_framework.azure import AzureAIAgentClient

# Same result, cleaner code
async with client.create_agent(
    name="schema-agent",
    instructions="...",
    tools=[get_graph_schema],  # Simple Python function!
) as agent:
    async for update in agent.run_stream(query, thread=thread):
        print(update.text, end="")
```

Key teaching points:
- Agent Framework handles tool serialization automatically
- Streaming is built-in
- Resource cleanup is automatic
- Same underlying Azure AI Foundry APIs

## Implementation Considerations

### Package Dependencies

The hybrid approach requires:
```
azure-ai-projects>=1.0.0
azure-identity
agent-framework-azure-ai  # for Part 2
```

### Authentication

Both approaches support `DefaultAzureCredential`, but the current notebook uses `AzureCliCredential` specifically. Consider standardizing on `DefaultAzureCredential` for broader environment support (managed identity, environment variables, etc.).

### Environment Setup

The notebook should clearly explain:
1. Azure AI Foundry project setup
2. Model deployment requirements
3. Environment variable configuration (`AZURE_AI_PROJECT_ENDPOINT`)

### Cleanup Implications

The native SDK approach requires explicit cleanup. Workshop attendees running multiple iterations could accumulate orphaned agents. Consider:
- Adding prominent cleanup instructions
- Using try/finally blocks
- Adding a "cleanup all agents" utility cell

## Questions for Discussion

1. **Depth vs. breadth**: Should the workshop prioritize understanding Azure AI Foundry fundamentals or focus on productivity with the Agent Framework?

2. **Consistency**: Should all three agent notebooks (02_01, 02_02, 02_03) follow the same pattern, or can 02_01 be the "educational foundation" while others use the framework?

3. **Maintenance burden**: Is maintaining two approaches in one notebook worth the educational value?

4. **Target audience**: Are workshop attendees primarily interested in learning Azure AI Foundry concepts, or in building agents quickly?

## Next Steps

If this proposal is approved:

1. Restructure notebook into Part 1 (Native SDK) and Part 2 (Agent Framework)
2. Update config.py to support both sync and async credential patterns
3. Add a cleanup utility cell
4. Update the solutions file to match
5. Test both approaches end-to-end
6. Update documentation to explain the two-part structure
