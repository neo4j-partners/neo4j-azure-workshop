#!/bin/bash
# Setup script for Neo4j + Azure AI Workshop
# This script installs dependencies and configures the Jupyter kernel

set -e

echo "=========================================="
echo "Neo4j + Azure AI Workshop Setup"
echo "=========================================="
echo

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    echo "uv installed successfully"
else
    echo "uv is already installed"
fi
echo

# Sync dependencies
echo "Installing Python dependencies..."
uv sync --prerelease=allow
echo "Dependencies installed successfully"
echo

# Register Jupyter kernel
echo "Registering Jupyter kernel..."
uv run python -m ipykernel install --user --name neo4j-workshops --display-name 'Neo4j AI Workshop (uv)'
echo "Jupyter kernel registered successfully"
echo

echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo
echo "Next steps:"
echo "  1. Ensure you have a .env file in the project root with:"
echo "     - NEO4J_URI"
echo "     - NEO4J_USERNAME"
echo "     - NEO4J_PASSWORD"
echo "     - AZURE_AI_PROJECT_ENDPOINT"
echo "     - AZURE_AI_MODEL_NAME"
echo "     - AZURE_AI_EMBEDDING_NAME"
echo
echo "  2. Open notebooks in VS Code and select 'New Workshops (uv)' kernel"
echo
echo "  3. Or run notebooks with: uv run jupyter notebook notebooks/"
echo

# Test connections
echo "=========================================="
echo "Testing connections..."
echo "=========================================="
echo
uv run python solutions/test_connection.py
