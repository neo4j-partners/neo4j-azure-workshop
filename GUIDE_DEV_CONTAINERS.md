# Dev Containers & Codespaces Quick Start Guide

## GitHub Codespaces (Cloud) or Local Dev Container (Local Setup)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/neo4j-partners/neo4j-azure-workshop)

### Setup Steps

1. **Click the badge above** (or go to repo → Code → Codespaces → New)

2. **Wait for container to build** (~3 minutes)

3. **Run in terminal:**
   ```bash
   # Authenticate with Azure
   az login --use-device-code
   azd auth login --use-device-code

   # Auto-detect resource group and location (workshop accounts)
   ./scripts/setup_azure.sh

   # Deploy
   azd up
   ```

4. **Follow the prompts:**
   ```
   ? Enter a unique environment name: mydev
   ? Select an Azure Subscription: 1. Your Subscription
   ? Pick a resource group to use:
     1. Create a new resource group
   > 2. your-existing-resource-group
   ```
   - **Environment name:** Any word (e.g., `mydev`, `workshop`)
   - **Resource group:** Select your existing RG, or choose "Create a new resource group"

5. **Restore Neo4j database (non-workshop only):**
   If you're not in a workshop with a pre-populated Neo4j database, restore the sample data:
   ```bash
   uv run scripts/restore_neo4j.py
   ```

6. **Choose your path:**

   **Path A: Workshop (Guided Notebooks)**
   Follow the step-by-step workshop guide in [`new-workshops/`](new-workshops/README.md)

   **Path B: Full Server (API Development)**
   Continue with steps 7-8 below to run the complete API server.

7. **Setup and run:**
   ```bash
   uv run setup_env.py
   uv run uvicorn api.main:create_app --factory --reload
   ```

8. **Test API:**
   ```bash
   # Basic test - check agent status
   uv run python src/test_server.py basic

   # Run all tests (agent, streaming, memory, semantic search, entities)
   uv run python src/test_server.py all
   ```

---

## Overview

This project uses **resource-group-scoped deployment** - all Azure resources deploy into a pre-existing resource group. This enables:

- **Workshop scenarios**: Participants only need Contributor access on their assigned resource group
- **Codespaces support**: Limited-permission accounts work seamlessly
- **Simpler cleanup**: Delete the resource group to remove everything

### What Gets Deployed

```
Your Resource Group
├── Azure AI Foundry Project (AI Hub + Project)
├── Azure OpenAI Service (gpt-5 + text-embedding-ada-002)
├── Storage Account
├── Container Registry
├── Container Apps Environment
├── Container App (API)
├── Log Analytics Workspace
├── Application Insights
└── Managed Identity + Role Assignments
```

---

## For Individual Users

### Create Your Own Resource Group

```bash
# Login first
az login

# Create resource group
az group create --name rg-my-agents --location eastus

# Set it for azd
azd env set AZURE_RESOURCE_GROUP rg-my-agents

# Deploy
azd up
```

### Supported Regions

Azure AI Foundry only works in these regions:
- eastus2 (Recommended)
- swedencentral
- westus2

---

## Troubleshooting

### Region Not Supported Error

**Cause**: `AZURE_LOCATION` is not set or set to an unsupported region.

**Fix**:
```bash
# For workshop accounts, run the setup script (auto-detects from your resource group)
./scripts/setup_azure.sh

# Or set manually
azd env set AZURE_LOCATION eastus2
azd up
```

### Previous Environment Cached

**Cause**: `.azure/` folder has stale settings from a previous user/subscription.

**Fix**:
```bash
rm -rf .azure/
az login
azd env set AZURE_RESOURCE_GROUP <your-rg>
azd up
```

### API Won't Start

**Cause**: Environment variables not loaded.

**Fix**:
```bash
uv run setup_env.py  # Re-pull from azd
uv run uvicorn api.main:create_app --factory --reload
```

---

## Architecture Notes

### Deployment Scope

The Bicep templates deploy at **resource group scope** (not subscription scope):

- No `targetScope = 'subscription'` declaration
- Resource group must exist before deployment
- Location defaults to resource group's location
- User only needs Contributor on the resource group

### Key Files

| File | Purpose |
|------|---------|
| `infra/main.bicep` | Main deployment template |
| `infra/main.parameters.json` | Parameter values from azd env |
| `azure.yaml` | Azure Developer CLI configuration |
| `.devcontainer/devcontainer.json` | Dev Container settings |

### Environment Flow

```
azd env set AZURE_RESOURCE_GROUP <name>
         ↓
    azd up (deploys to RG)
         ↓
  uv run setup_env.py (pulls outputs to .env)
         ↓
    uvicorn (reads .env, starts API)
```
