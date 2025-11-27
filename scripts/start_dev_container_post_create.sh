#!/bin/bash
# Post-create script for Dev Container / Codespaces
# This runs once when the container is first created

set -e

echo "=========================================="
echo "Dev Container Post-Create Setup"
echo "=========================================="

# Install uv
echo "Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Sync root project dependencies
echo "Installing root project dependencies..."
uv sync --prerelease=allow

# Sync new-workshops dependencies and register Jupyter kernel
echo "Setting up new-workshops..."
cd new-workshops
uv sync --prerelease=allow

echo "Registering Jupyter kernel..."
uv run python -m ipykernel install --user --name neo4j-jupyter-kernel --display-name 'neo4j-jupyter-kernel'

echo "=========================================="
echo "Post-create setup complete!"
echo "=========================================="
