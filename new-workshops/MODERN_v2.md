# Proposal: Switch Simple Agent Notebook to AzureAIClient (V2)

## Overview

This proposal outlines the switch from `AzureAIAgentClient` to `AzureAIClient` in the workshop notebook to align with the newer Azure AI Projects SDK (V2) and current Microsoft documentation.

---

## Understanding the Architecture Layers

There are two distinct layers when building agents with Azure AI Foundry:

### Layer 1: Azure SDKs (Low-Level)

These are Microsoft's official Python packages that provide direct access to Azure AI Foundry APIs.

**azure-ai-agents (V1)**
- Focused specifically on the Agents API
- Uses the thread/message/run model (similar to OpenAI Assistants)
- Requires manual management of agent lifecycle, threads, and tool outputs
- Direct control over every API call

**azure-ai-projects (V2)**
- Newer, broader Azure AI Projects SDK
- Agents are one capability within the larger project concept
- Uses the "Responses" API pattern
- Aligns with current Microsoft documentation and portal experience
- Recommended path going forward

### Layer 2: Microsoft Agent Framework (High-Level)

This is a productivity layer built ON TOP of the Azure SDKs. It provides:

- Automatic agent lifecycle management (create and cleanup)
- Simple Python functions as tools (no JSON schema definition needed)
- Built-in streaming support via run_stream method
- Thread and conversation management abstraction
- Middleware and observability hooks
- Multi-provider support (Azure, OpenAI, Anthropic, etc.)

**The Agent Framework offers two Azure AI clients:**

| Client | Wraps | SDK Version |
|--------|-------|-------------|
| AzureAIAgentClient | azure.ai.agents.AgentsClient | V1 |
| AzureAIClient | azure.ai.projects.AIProjectClient | V2 |

Both clients register agents in Azure AI Foundry portal. The difference is which underlying SDK they use.

---

## Why Switch to V2

1. **Documentation alignment** - Microsoft's current quickstart documentation uses azure-ai-projects
2. **Portal integration** - V2 SDK aligns better with the Azure AI Foundry portal experience
3. **Future direction** - V2 represents Microsoft's recommended path forward
4. **Broader capabilities** - Access to project-level features beyond just agents

---

## References

### Code References

| Reference | Location |
|-----------|----------|
| AzureAIClient source (V2) | /Users/ryanknight/projects/azure/agent-framework/python/packages/azure-ai/agent_framework_azure_ai/_client.py |
| AzureAIAgentClient source (V1) | /Users/ryanknight/projects/azure/agent-framework/python/packages/azure-ai/agent_framework_azure_ai/_chat_client.py |
| V2 samples directory | /Users/ryanknight/projects/azure/agent-framework/python/samples/getting_started/agents/azure_ai/ |
| V1 samples directory | /Users/ryanknight/projects/azure/agent-framework/python/samples/getting_started/agents/azure_ai_agent/ |
| Basic V2 example | /Users/ryanknight/projects/azure/agent-framework/python/samples/getting_started/agents/azure_ai/azure_ai_basic.py |
| Agent samples README | /Users/ryanknight/projects/azure/agent-framework/python/samples/getting_started/agents/README.md |

### Documentation References

| Reference | URL |
|-----------|-----|
| Azure AI Foundry Quickstart | https://learn.microsoft.com/en-us/azure/ai-foundry/quickstarts/get-started-code |
| Agent Framework MS Learn | https://learn.microsoft.com/agent-framework/overview/agent-framework-overview |
| Agent Framework GitHub | https://github.com/microsoft/agent-framework |

---

## Requirements

### Functional Requirements

1. The notebook must use AzureAIClient instead of AzureAIAgentClient
2. The notebook must maintain the same user-facing behavior (schema retrieval and summarization)
3. The notebook must continue to use the Agent Framework (not drop down to raw SDK)
4. All existing tools (get_graph_schema) must continue to work without modification
5. Streaming output must continue to work

### Non-Functional Requirements

1. The change should be minimal - only import and client instantiation changes
2. Documentation comments in the notebook should reflect the V2 terminology
3. The solutions file must be updated to match the notebook

---

## What Changes

### Changes Required

1. Import statement changes from AzureAIAgentClient to AzureAIClient
2. Client instantiation (same parameters, different class name)
3. Markdown explanations updated to reference V2 SDK

### What Stays the Same

1. Tool definitions (simple Python functions)
2. Agent creation pattern (create_agent context manager)
3. Streaming pattern (run_stream async iteration)
4. Neo4j connection and configuration
5. Overall notebook structure and flow

---

## Implementation Plan

### Phase 1: Research and Validation

**Objective:** Confirm V2 client works with existing patterns

**Todo List:**
- [ ] Review azure_ai_basic.py sample to confirm API compatibility
- [ ] Review AzureAIClient source to understand any parameter differences
- [ ] Verify azure-ai-projects package is already in project dependencies
- [ ] Identify any breaking changes between V1 and V2 client APIs

### Phase 2: Update Dependencies

**Objective:** Ensure correct package versions are available

**Todo List:**
- [ ] Check pyproject.toml for azure-ai-projects dependency
- [ ] Verify minimum version requirements from Agent Framework
- [ ] Run uv sync to ensure environment is current
- [ ] Document any version constraints discovered

### Phase 3: Update Solutions File

**Objective:** Update solutions file first since it is easier to test as standalone Python

**Todo List:**
- [ ] Update import in solutions/02_01_simple_agent.py
- [ ] Update client instantiation in solutions file
- [ ] Update any docstrings or comments
- [ ] Run solutions file to verify it works before touching notebook

### Phase 4: Update Notebook

**Objective:** Apply same changes to notebook after solutions file is validated

**Todo List:**
- [ ] Update import statement in the imports cell
- [ ] Update client instantiation to use AzureAIClient
- [ ] Update markdown cell explaining the client to reference V2/azure-ai-projects
- [ ] Update any comments that reference V1 or AzureAIAgentClient
- [ ] Verify experiment cell uses same pattern

### Phase 5: Testing

**Objective:** Verify everything works correctly

**Todo List:**
- [ ] Run notebook from top to bottom in fresh kernel
- [ ] Verify agent creation succeeds
- [ ] Verify tool execution (get_graph_schema) works
- [ ] Verify streaming output displays correctly
- [ ] Verify experiment cell works with different queries
- [ ] Check Azure AI Foundry portal to confirm agent appears
- [ ] Run solutions file standalone to verify it works

### Phase 6: Code Review and Final Verification

**Objective:** Ensure quality and correctness

**Todo List:**
- [ ] Review all changes against this proposal
- [ ] Verify no V1 references remain in updated files
- [ ] Check markdown explanations are accurate
- [ ] Confirm notebook renders correctly in Jupyter
- [ ] Final end-to-end test with clean environment
- [ ] Document any issues or learnings discovered

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| V2 API differences cause issues | Low | Medium | Both clients share similar Agent Framework interface |
| Missing package dependency | Low | Low | Check dependencies before starting |
| Portal behavior differences | Low | Low | Both register agents; V2 may show more features |

---

## Success Criteria

1. Notebook runs successfully with AzureAIClient
2. Agent appears in Azure AI Foundry portal
3. Schema tool executes and returns results
4. Streaming output works correctly
5. No references to V1/AzureAIAgentClient remain in updated files
6. Solutions file matches notebook implementation

---

## Implementation Progress

### Phase 1: Research and Validation - COMPLETED

**Status:** Done

**Findings:**

1. **API Compatibility Confirmed**
   - Both clients accept identical parameters: `project_endpoint`, `model_deployment_name`, `async_credential`
   - Both support `create_agent()` with `name`, `instructions`, `tools`
   - Both support `run_stream()` with same interface
   - `get_new_thread()` method works identically (it's part of ChatAgent, not the client)

2. **Parameter Differences Identified**
   - `AzureAIClient` (V2) has additional optional parameters: `agent_version`, `use_latest_version`
   - These are not needed for basic usage - can be ignored

3. **Underlying SDK Difference**
   - V2 uses `azure.ai.projects.aio.AIProjectClient`
   - V1 uses `azure.ai.agents.aio.AgentsClient`

4. **Breaking Changes**
   - None identified for our use case
   - The change is a simple import and class name swap

**Reference Samples Reviewed:**
- `/Users/ryanknight/projects/azure/agent-framework/python/samples/getting_started/agents/azure_ai/azure_ai_basic.py`
- `/Users/ryanknight/projects/azure/agent-framework/python/samples/getting_started/agents/azure_ai/azure_ai_with_thread.py`

### Phase 2: Update Dependencies - COMPLETED

**Status:** Done

**Actions Taken:**
- Deleted .venv and recreated with fresh packages
- Ran `uv sync --prerelease=allow`
- Verified `AzureAIClient` import works

**Installed Versions:**
- agent-framework-azure-ai: 1.0.0b251120
- agent-framework-core: 1.0.0b251120
- azure-ai-projects: 2.0.0b2
- azure-ai-agents: 1.2.0b5

**Conclusion:** No changes to pyproject.toml needed. The `azure-ai-projects` package is a transitive dependency of `agent-framework-azure-ai`.

### Phase 3: Update Solutions File - COMPLETED

**Status:** Done

**Changes Made:**
1. Updated import: `AzureAIAgentClient` → `AzureAIClient`
2. Updated client instantiation: `AzureAIAgentClient(...)` → `AzureAIClient(...)`
3. Updated docstring to reference V2 SDK (azure-ai-projects)

**Verification:**
- Syntax check: PASSED
- Import check: PASSED
- Runtime test: Code executed correctly up to Azure API call (DNS failure is infrastructure issue, not code issue - Azure endpoint not accessible in test environment)

**File:** `solutions/02_01_simple_agent.py`

**Summary of Changes:**
```
Line 5-6: Added "(V2 SDK - azure-ai-projects)" to docstring
Line 15:  Changed import from AzureAIAgentClient to AzureAIClient
Line 39:  Changed client instantiation from AzureAIAgentClient to AzureAIClient
```

---

## Next Steps (Phase 4-6)

Phase 4, 5, and 6 remain to be implemented:
- Phase 4: Update Notebook
- Phase 5: Testing (requires Azure infrastructure)
- Phase 6: Code Review and Final Verification
