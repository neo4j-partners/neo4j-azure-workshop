# Dev Containers & Codespaces Quick Start Guide

## Option 1: GitHub Codespaces (Fastest)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/neo4j-partners/neo4j-azure-workshop)

### Setup Steps

1. **Click the badge above** (or go to repo → Code → Codespaces → New)

2. **Resource Group prompt appears:**
   - **Workshop participants:** Enter your assigned resource group (find it at [Azure Portal](https://portal.azure.com) → search "Resource groups")
   - **Individual users:** Leave blank - you can create one during `azd up`

3. **Wait for container to build** (~3 minutes)

4. **Run in terminal:**
   ```bash
   # Authenticate with Azure
   az login --use-device-code
   azd auth login --use-device-code

   # Deploy
   azd up
   ```

5. **Follow the prompts:**
   ```
   ? Enter a unique environment name: mydev
   ? Select an Azure Subscription: 1. Your Subscription
   ? Pick a resource group to use:
     1. Create a new resource group
   > 2. your-existing-resource-group
   ```
   - **Environment name:** Any word (e.g., `mydev`, `workshop`)
   - **Resource group:** Select your existing RG, or choose "Create a new resource group"

---

## Option 2: Local Dev Container

### Prerequisites
- Docker Desktop running
- VS Code with Dev Containers extension

### Setup Steps

1. **Open in Dev Container**
   - Open project in VS Code
   - Click "Reopen in Container" when prompted (or `Cmd+Shift+P` → "Reopen in Container")
   - Wait ~3 minutes for container to build

2. **Run in terminal:**
   ```bash
   # Authenticate with Azure
   az login
   azd auth login

   # Deploy
   azd up
   ```

3. **Follow the prompts:**
   - `Enter a unique environment name:` → Any word (e.g., `mydev`)
   - `Select an Azure Subscription:` → Pick yours
   - `Pick a resource group:` → Select existing or "Create a new resource group"

4. **Setup and run:**
   ```bash
   uv run setup_env.py
   uv run uvicorn api.main:create_app --factory --reload
   ```

5. **Test API:**
   ```bash
   curl http://localhost:8000/agent
   ```

### Expected Results
- `azd up` should complete without permission errors
- All Azure resources deploy to your specified resource group
- API responds with agent metadata at `/agent`

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

## For Workshop Organizers

### Pre-create Resource Groups

```bash
# Create resource group for a participant
az group create --name rg-workshop-user1 --location eastus

# Grant Contributor access
az role assignment create \
  --assignee user1@example.com \
  --role Contributor \
  --scope /subscriptions/<subscription-id>/resourceGroups/rg-workshop-user1
```

### Provide to Participants
- Resource group name
- Subscription ID (for `az login`)
- This guide

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
- eastus
- eastus2
- swedencentral
- westus
- westus3

---

## Troubleshooting

### "RoleAssignmentExists" Error

**Cause**: You're redeploying and role assignments already exist from a previous deployment.

**Fix**: Skip role assignments on redeployment:
```bash
azd env set SKIP_ROLE_ASSIGNMENTS true
azd up
```

This is safe because the roles were already assigned on your first deployment. This skips all 10 role assignments across the infrastructure.

### "AuthorizationFailed" Error

**Cause**: You don't have Contributor access on the resource group.

**Fix**: Ask your admin to grant access, or create your own resource group if you have subscription access.

### "Resource group not found"

**Cause**: The resource group doesn't exist or you mistyped the name.

**Fix**:
```bash
# List your resource groups
az group list --output table

# Set the correct name
azd env set AZURE_RESOURCE_GROUP <correct-name>
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
