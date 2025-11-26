# Azure CLI Guide

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
