#!/bin/bash
# Auto-detect resource group and location for workshop accounts
# Run this after: az login --use-device-code && azd auth login --use-device-code

set -e

echo "Detecting Azure resource groups..."

# Get list of resource groups as JSON
RG_JSON=$(az group list --query "[].{name:name, location:location}" -o json 2>/dev/null)

if [ -z "$RG_JSON" ] || [ "$RG_JSON" == "[]" ]; then
    echo "❌ No resource groups found. Are you logged in?"
    echo "   Run: az login --use-device-code"
    exit 1
fi

# Count resource groups
RG_COUNT=$(echo "$RG_JSON" | jq length)

if [ "$RG_COUNT" -eq 1 ]; then
    # Only one resource group - auto-configure
    RG_NAME=$(echo "$RG_JSON" | jq -r '.[0].name')
    RG_LOCATION=$(echo "$RG_JSON" | jq -r '.[0].location')

    echo "✅ Found single resource group: $RG_NAME (location: $RG_LOCATION)"

    # Initialize azd environment if needed
    if ! azd env list 2>/dev/null | grep -q "default"; then
        echo "Creating azd environment..."
        azd init -e workshop 2>/dev/null || true
    fi

    azd env set AZURE_RESOURCE_GROUP "$RG_NAME"
    azd env set AZURE_LOCATION "$RG_LOCATION"
    azd env set SKIP_ROLE_ASSIGNMENTS true

    echo ""
    echo "✅ Azure configured! Settings:"
    echo "   AZURE_RESOURCE_GROUP=$RG_NAME"
    echo "   AZURE_LOCATION=$RG_LOCATION"
    echo ""
    echo "Ready to deploy! Run:"
    echo "   azd up"
else
    # Multiple resource groups - show options
    echo "Found $RG_COUNT resource groups:"
    echo ""
    echo "$RG_JSON" | jq -r '.[] | "  - \(.name) (\(.location))"'
    echo ""
    echo "Please set manually:"
    echo "   azd env set AZURE_RESOURCE_GROUP <name>"
    echo "   azd env set AZURE_LOCATION <location>"
fi
