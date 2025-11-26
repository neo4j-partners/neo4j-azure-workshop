#!/bin/bash
# Configure Azure region for workshop
# Run this after: az login --use-device-code && azd auth login --use-device-code

set -e

ENV_FILE=".env"

# Function to clean stale Azure config from .env
clean_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        return
    fi

    # Check if there are Azure/Service settings to clean
    if grep -qE '^(AZURE_|SERVICE_|EMBEDDING_)' "$ENV_FILE" 2>/dev/null; then
        echo ""
        echo "Found existing Azure configuration in .env that may conflict with new deployment."

        # Check for Neo4j settings
        if grep -qE '^NEO4J_' "$ENV_FILE" 2>/dev/null; then
            echo ""
            echo "WARNING: Your .env file contains Neo4j settings that will be preserved:"
            grep '^NEO4J_' "$ENV_FILE" | sed 's/=.*/=***/' | sed 's/^/  /'
            echo ""
            read -p "Remove Azure config but KEEP Neo4j settings? [Y/n]: " keep_neo4j
            keep_neo4j=${keep_neo4j:-Y}

            if [[ "$keep_neo4j" =~ ^[Yy]$ ]]; then
                # Extract Neo4j settings
                grep '^NEO4J_' "$ENV_FILE" > "$ENV_FILE.neo4j.tmp"
                # Extract any comments at the top (user config section)
                head -n 10 "$ENV_FILE" | grep '^#' > "$ENV_FILE.header.tmp" || true

                # Rebuild .env with only Neo4j settings
                cat > "$ENV_FILE" << 'EOF'
# ============================================
# User Configuration
# ============================================
# Neo4j Connection (configure these manually)

EOF
                cat "$ENV_FILE.neo4j.tmp" >> "$ENV_FILE"
                rm -f "$ENV_FILE.neo4j.tmp" "$ENV_FILE.header.tmp"

                echo "Removed stale Azure config from .env (Neo4j settings preserved)"
            else
                read -p "Remove ALL settings from .env including Neo4j? [y/N]: " remove_all
                if [[ "$remove_all" =~ ^[Yy]$ ]]; then
                    rm -f "$ENV_FILE"
                    echo "Removed .env file"
                else
                    echo "Keeping .env unchanged - deployment may fail if resource group doesn't exist"
                fi
            fi
        else
            # No Neo4j settings, safe to clean Azure config
            echo "Cleaning stale Azure configuration from .env..."
            grep -vE '^(AZURE_|SERVICE_|EMBEDDING_)' "$ENV_FILE" > "$ENV_FILE.tmp" || true
            mv "$ENV_FILE.tmp" "$ENV_FILE"
            echo "Done"
        fi
    fi
}

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
        echo "Invalid choice. Please enter 1, 2, or 3."
        exit 1
        ;;
esac

# Clean stale Azure config from .env before azd init
clean_env_file

# Remove existing azd environment to start fresh
if [ -d ".azure" ]; then
    echo "Removing existing .azure directory..."
    rm -rf .azure
fi

# Initialize new azd environment
echo "Initializing azd environment..."
azd init -e workshop

azd env set AZURE_LOCATION "$REGION"

echo ""
echo "Azure configured: $REGION"
echo ""
echo "Ready to deploy! Run:"
echo "   azd up"
