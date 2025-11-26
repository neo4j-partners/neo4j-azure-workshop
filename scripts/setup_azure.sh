#!/bin/bash
# Configure Azure region for workshop
# Run this after: az login --use-device-code && azd auth login --use-device-code

set -e

echo ""
echo "Azure AI Foundry Agent Service requires one of these regions:"
echo "  1) East US 2 (eastus2)"
echo "  2) Sweden Central (swedencentral)"
echo "  3) West US 2 (westus2)"
echo ""
read -p "Select a region [1-3]: " choice

case $choice in
    1) REGION="eastus2" ;;
    2) REGION="swedencentral" ;;
    3) REGION="westus2" ;;
    *)
        echo "❌ Invalid choice. Please enter 1, 2, or 3."
        exit 1
        ;;
esac

# Initialize azd environment if needed
if ! azd env list 2>/dev/null | grep -q "workshop"; then
    echo "Creating azd environment..."
    azd init -e workshop 2>/dev/null || true
fi

azd env set AZURE_LOCATION "$REGION"
azd env set SKIP_ROLE_ASSIGNMENTS true

echo ""
echo "✅ Azure configured: $REGION"
echo ""
echo "Ready to deploy! Run:"
echo "   azd up"
