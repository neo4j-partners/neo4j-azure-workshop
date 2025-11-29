# Proposal: Update src/ API to AzureAIClient (V2)

## Overview

This proposal outlines updating the FastAPI application in `/Users/ryanknight/projects/workshops/neo4j-azure-workshop/src/` to use `AzureAIClient` (V2) instead of `AzureAIAgentClient` (V1).

## Files to Update

| File | Current State | Changes Required |
|------|---------------|------------------|
| `src/agent.py` | Uses `AzureAIAgentClient` | Change to `AzureAIClient` |
| `src/api/main.py` | References `AzureAIAgentClient` in comments | Update comments |
| `src/api/routes.py` | Uses thread management for conversations | Keep threads, update for V2 pattern |

## Key Difference from Workshop Updates

**The API uses threads intentionally** for multi-turn conversation tracking:

```
routes.py:57    thread = agent.get_new_thread()
routes.py:62    result = await agent.run(chat_request.message, thread=thread)
routes.py:94    async for update in agent.run_stream(chat_request.message, thread=thread):
```

This is a legitimate use case - the API maintains conversation state across multiple HTTP requests using in-memory thread storage. Unlike the simple workshop examples (single-turn), this API needs to preserve conversation context.

**V2 Pattern for Multi-Turn:**
```python
# V2 with thread persistence (in-memory)
thread = agent.get_new_thread()
result = await agent.run(message, thread=thread, store=False)

# V2 with server persistence
thread = agent.get_new_thread()
result = await agent.run(message, thread=thread)  # store=True is default
```

## Detailed Changes

### 1. src/agent.py

**Current:**
```python
from agent_framework.azure import AzureAIAgentClient
...
return AzureAIAgentClient(**client_kwargs)
```

**Change to:**
```python
from agent_framework.azure import AzureAIClient
...
return AzureAIClient(**client_kwargs)
```

**Lines to update:**
- Line 10: Import statement
- Line 55: Docstring reference
- Line 64: Return type reference
- Line 74: Logger message
- Line 75: Class instantiation
- Line 78: Type hint in function signature

### 2. src/api/main.py

**Current:**
```python
# Line 180: Creates AzureAIAgentClient
```

**Change to:**
- Line 180: Update comment to reference `AzureAIClient`

### 3. src/api/routes.py

**Current (V1 pattern):**
```python
thread = agent.get_new_thread()
result = await agent.run(chat_request.message, thread=thread)
```

**Change to (V2 pattern):**
```python
thread = agent.get_new_thread()
result = await agent.run(chat_request.message, thread=thread, store=False)
```

The `store=False` parameter tells V2 to keep messages in-memory only, matching the V1 behavior where threads are managed locally.

**Lines to update:**
- Line 62: Add `store=False` to `agent.run()`
- Line 94: Add `store=False` to `agent.run_stream()`

## Implementation Plan

### Phase 1: Update agent.py

**Todo List:**
- [ ] Change import from `AzureAIAgentClient` to `AzureAIClient`
- [ ] Update docstring in `create_agent_client()` function
- [ ] Update return type reference in docstring
- [ ] Update logger message
- [ ] Update class instantiation
- [ ] Update type hint in `create_agent_context()` function signature

### Phase 2: Update api/main.py

**Todo List:**
- [ ] Update comment on line 180 referencing `AzureAIAgentClient`

### Phase 3: Update api/routes.py

**Todo List:**
- [ ] Add `store=False` to `agent.run()` call in `/chat` endpoint
- [ ] Add `store=False` to `agent.run_stream()` call in `/chat/stream` endpoint

### Phase 4: Testing

**Todo List:**
- [ ] Verify syntax with Python AST parser
- [ ] Test `/agent` endpoint returns agent info
- [ ] Test `/chat` endpoint with single message
- [ ] Test `/chat` endpoint with conversation continuation (same conversation_id)
- [ ] Test `/chat/stream` endpoint

### Phase 5: Code Review

**Todo List:**
- [ ] Verify no V1 references remain in code
- [ ] Verify thread management still works for multi-turn conversations
- [ ] Review changes against this proposal

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Thread behavior changes | Low | Medium | Test multi-turn conversations explicitly |
| `store=False` changes behavior | Low | Low | This matches V1 in-memory pattern |
| API breaks | Low | High | Test all endpoints after changes |

## References

| Reference | Location |
|-----------|----------|
| V2 thread sample | `/Users/ryanknight/projects/azure/agent-framework/python/samples/getting_started/agents/azure_ai/azure_ai_with_thread.py` |
| V2 basic sample | `/Users/ryanknight/projects/azure/agent-framework/python/samples/getting_started/agents/azure_ai/azure_ai_basic.py` |
| Workshop V2 update | `new-workshops/MODERN_v2.md` |

## Success Criteria

1. All endpoints work correctly after update
2. Multi-turn conversations maintain context
3. No `AzureAIAgentClient` references remain in code
4. Syntax validation passes

---

## Implementation Progress

### Phase 1: Update src/agent.py - COMPLETED

**Status:** Done

**Changes Made:**
- Line 5-6: Updated docstring to reference V2 SDK (azure-ai-projects)
- Line 11: Changed import from `AzureAIAgentClient` to `AzureAIClient`
- Line 54: Added return type hint `-> AzureAIClient`
- Line 56: Updated docstring function description
- Line 65: Updated docstring return description
- Line 75: Updated logger message
- Line 76: Changed class instantiation to `AzureAIClient`
- Line 79: Updated type hint in `create_agent_context()` signature
- Line 84: Updated docstring parameter description

### Phase 2: Update src/api/main.py - COMPLETED

**Status:** Done

**Changes Made:**
- Line 180: Updated comment from `AzureAIAgentClient` to `AzureAIClient (V2)`

### Phase 3: Update src/api/routes.py - COMPLETED

**Status:** Done

**Changes Made:**
- Line 62: Added `store=False` to `agent.run()` call in `/chat` endpoint
- Line 94: Added `store=False` to `agent.run_stream()` call in `/chat/stream` endpoint

**Verification:**
- Syntax check: All 3 files pass (`agent.py`, `main.py`, `routes.py`)
- No `AzureAIAgentClient` references remain in src/

---

## Summary

All phases complete. The src/ API has been updated to V2:

| File | Status |
|------|--------|
| `src/agent.py` | ✓ Updated to AzureAIClient |
| `src/api/main.py` | ✓ Comments updated |
| `src/api/routes.py` | ✓ Added store=False for V2 thread pattern |

**Next Steps:** Phase 4 (Testing) and Phase 5 (Code Review) when ready.
