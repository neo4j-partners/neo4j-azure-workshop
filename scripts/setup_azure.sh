#!/bin/bash
# Setup script for Azure AI Foundry workshop
# Creates an azd environment with a supported region

set -e

echo ""
echo "=== Azure AI Foundry Workshop Setup ==="
echo ""

# Check if azd is installed
if ! command -v azd &> /dev/null; then
    echo "Error: Azure Developer CLI (azd) is not installed."
    echo "Install it from: https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd"
    exit 1
fi

# Check if logged in
if ! azd auth login --check-status &> /dev/null; then
    echo "You need to log in to Azure first."
    echo "Running: azd auth login --use-device-code"
    echo ""
    azd auth login --use-device-code
fi

# Get environment name
echo "Enter a name for your environment (e.g., mydev, workshop1):"
read -p "> " ENV_NAME

if [ -z "$ENV_NAME" ]; then
    echo "Error: Environment name cannot be empty."
    exit 1
fi

# Select region
echo ""
echo "Select a region for Azure AI Foundry:"
echo ""
echo "  1) East US 2      (eastus2)       - Recommended"
echo "  2) Sweden Central (swedencentral)"
echo "  3) West US 2      (westus2)"
echo ""
read -p "Enter choice [1-3]: " REGION_CHOICE

case $REGION_CHOICE in
    1)
        REGION="eastus2"
        ;;
    2)
        REGION="swedencentral"
        ;;
    3)
        REGION="westus2"
        ;;
    *)
        echo "Invalid choice. Defaulting to eastus2."
        REGION="eastus2"
        ;;
esac

# Resource group option
echo ""
echo "Resource group setup:"
echo ""
echo "  1) Create a new resource group (azd will prompt for name)"
echo "  2) Use an existing resource group"
echo ""
read -p "Enter choice [1-2]: " RG_CHOICE

RESOURCE_GROUP=""
if [ "$RG_CHOICE" = "2" ]; then
    echo ""
    echo "Enter the existing resource group name:"
    read -p "> " RESOURCE_GROUP
    if [ -z "$RESOURCE_GROUP" ]; then
        echo "Error: Resource group name cannot be empty."
        exit 1
    fi
fi

echo ""
echo "Creating environment '$ENV_NAME' in region '$REGION'..."
echo ""

# Create environment
azd env new "$ENV_NAME"

# Set the region
azd env set AZURE_LOCATION "$REGION"

# Set resource group if specified
if [ -n "$RESOURCE_GROUP" ]; then
    azd env set AZURE_RESOURCE_GROUP "$RESOURCE_GROUP"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Environment:     $ENV_NAME"
echo "Region:          $REGION"
if [ -n "$RESOURCE_GROUP" ]; then
echo "Resource Group:  $RESOURCE_GROUP"
else
echo "Resource Group:  (will be created during deploy)"
fi
echo ""
echo "Next step - deploy to Azure:"
echo "  azd up"
echo ""
