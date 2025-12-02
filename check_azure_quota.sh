#!/bin/bash
# Script to find Azure OpenAI resources consuming quota across subscription

set -e

echo "=== Azure Subscription Quota Investigation ==="
echo ""

# Get current subscription
echo "1. Current Subscription:"
az account show --query "{Name:name, ID:id, State:state}" -o table
echo ""

# List all resource groups
echo "2. All Resource Groups:"
az group list --query "[].{Name:name, Location:location, State:properties.provisioningState}" -o table
echo ""

# Find all Cognitive Services accounts (includes Azure OpenAI)
echo "3. All Cognitive Services / Azure OpenAI Resources:"
az cognitiveservices account list --query "[].{Name:name, ResourceGroup:resourceGroup, Kind:kind, Location:location, SKU:sku.name}" -o table
echo ""

# For each Azure OpenAI resource, list deployments
echo "4. Model Deployments per Resource:"
echo "-----------------------------------"

for resource in $(az cognitiveservices account list --query "[?kind=='OpenAI'].name" -o tsv); do
    rg=$(az cognitiveservices account list --query "[?name=='$resource'].resourceGroup" -o tsv)
    echo ""
    echo "Resource: $resource (RG: $rg)"
    echo "Deployments:"
    az cognitiveservices account deployment list \
        --name "$resource" \
        --resource-group "$rg" \
        --query "[].{Name:name, Model:properties.model.name, Version:properties.model.version, Capacity:sku.capacity, SKU:sku.name}" \
        -o table 2>/dev/null || echo "  (No deployments or access denied)"
done

echo ""
echo "5. Checking Quota Usage for Text-Embedding-Ada-002:"
echo "----------------------------------------------------"

# List all locations where OpenAI resources exist
locations=$(az cognitiveservices account list --query "[?kind=='OpenAI'].location" -o tsv | sort -u)

for location in $locations; do
    echo ""
    echo "Location: $location"
    az cognitiveservices usage list --location "$location" \
        --query "[?contains(name.value, 'Embedding') || contains(name.value, 'embedding')]" \
        -o table 2>/dev/null || echo "  (Could not retrieve usage)"
done

echo ""
echo "6. Role Assignments on Cognitive Services:"
echo "-------------------------------------------"
for resource in $(az cognitiveservices account list --query "[].id" -o tsv); do
    echo ""
    echo "Resource: $(basename $resource)"
    az role assignment list --scope "$resource" --query "[].{Principal:principalName, Role:roleDefinitionName}" -o table 2>/dev/null | head -20
done

echo ""
echo "=== Investigation Complete ==="
echo ""
echo "If you don't see the resources consuming quota, check:"
echo "1. Other subscriptions: az account list -o table"
echo "2. Soft-deleted resources: az cognitiveservices account list-deleted"
echo "3. Regional quota: az cognitiveservices account list-usage --name <resource> --resource-group <rg>"
