# Azure CLI Guide

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
