# Azure CLI Guide

## Environment Setup and Initialization

### How `azd init` Works

When you run `azd init`, it automatically imports `AZURE_*` prefixed variables from any `.env` file in the project root. This can cause issues if you have stale configuration from a previous deployment (e.g., referencing a deleted resource group).

**The setup script handles this automatically:**

```bash
./scripts/setup_azure.sh
```

This script:
1. Clears `AZURE_*`, `SERVICE_*`, and `EMBEDDING_*` variables from `.env`
2. Preserves your Neo4j settings (`NEO4J_*` variables)
3. Removes the `.azure/` directory for a clean start
4. Runs `azd init` with a fresh environment

### Manual Environment Reset

If you need to manually reset your environment:

```bash
# Remove Azure config from .env (keeps Neo4j settings)
./scripts/setup_azure.sh


# Remove azd environment directory
rm -rf .azure

# Initialize fresh
azd init -e myenv
azd env set AZURE_LOCATION eastus2
azd up
```

### Why This Matters

The `.env` file serves two purposes:
1. **Local development:** Provides credentials for running the app locally
2. **azd initialization:** Seeds new environments with existing values

After a deployment, `setup_env.py` writes Azure outputs (endpoints, resource names) to `.env`. If you later delete the Azure resources but keep the `.env`, the next `azd init` will try to use the old resource group name, causing deployment failures.

---

## Managing Multiple Environments

```bash
azd env list              # List all environments
azd env select <name>     # Switch to a different environment
azd env get-values        # Show current environment's variables
azd env new <name>        # Create a new environment
```

### Using an Existing Resource Group

For workshop scenarios where resource groups are pre-created:

```bash
azd env set AZURE_RESOURCE_GROUP <your-existing-rg-name>
```

---

## For Workshop Organizers

### Pre-create Resource Groups

```bash
# Create resource group for a participant
az group create --name rg-workshop-user1 --location eastus2

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

## Supported Regions

Azure AI Foundry only works in the following regions:

1. East US 2 (eastus2) - Recommended
2. Sweden Central (swedencentral)
3. West US 2 (westus2)
