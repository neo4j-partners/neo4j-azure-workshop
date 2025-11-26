# Simple AI Agents (API Only)

This is an API-only implementation of an AI Agent using Python, FastAPI, and the **Microsoft Agent Framework (2025)** with **Azure AI Foundry**. It demonstrates how to build AI agents with conversation memory.

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/neo4j-partners/neo4j-azure-workshop)
[![Open in Dev Containers](https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/neo4j-partners/neo4j-azure-workshop)

## Quick Start

For GitHub Codespaces or Local Dev Container setup, see **[GUIDE_DEV_CONTAINERS.md](GUIDE_DEV_CONTAINERS.md)**.

## Prerequisites (Manual Setup)

*   **[uv](https://github.com/astral-sh/uv):** An extremely fast Python package installer and resolver.
*   **[Azure Developer CLI (azd)](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd):** For infrastructure provisioning (`azd login`).
*   **[Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli):** For authentication (`az login`).
*   **Git**

## Getting Started

### 1. Configure Azure Region
Run the setup script to select your Azure region and initialize the environment:

```bash
./scripts/setup_azure.sh
```

> **Note:** This script clears the `.azure/` directory and Azure-related settings from `.env` to ensure `azd up` creates a fresh environment. Neo4j settings in `.env` are preserved. See [docs/AZ_CLI_GUIDE.md](docs/AZ_CLI_GUIDE.md) for details on environment management.

> **Supported Regions:** `eastus2`, `swedencentral`, or `westus2`

### 2. Provision Infrastructure
Deploy the Azure AI resources:

```bash
azd up
```

> **Note:** For full deployment options (including Container App), see [docs/AZURE_DEPLOY_GUIDE.md](docs/AZURE_DEPLOY_GUIDE.md).

### 3. Install Dependencies
Use `uv` to sync dependencies defined in `pyproject.toml`.

```bash
uv sync --prerelease=allow
```

### 4. Setup Environment Variables
Run the helper script to pull environment variables from `azd` and create a local `.env` file.

```bash
uv run setup_env.py
```

### 5. Restore Neo4j Database (Optional)

> **Note:** If you're using a pre-provisioned workshop Neo4j database, this step is not needed—the data is already loaded.

To restore the financial graph data to your own Neo4j instance:

```bash
uv run python scripts/restore_neo4j.py
```

This streams and restores the backup from GitHub, creating:
- **Nodes:** `AssetManager`, `Company`, `Document`, `Chunk`
- **Relationships:** `OWNS`, `FILED`, `HAS_CHUNK`

The script reads Neo4j credentials (`NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`) from `.env` automatically.

### 6. Choose Your Path

**Path A: Workshop (Guided Notebooks)**
Follow the step-by-step workshop guide in [`new-workshops/`](new-workshops/README.md)

**Path B: Full Server (API Development)**
Run the complete API server:

```bash
uv run uvicorn api.main:create_app --factory --reload
```

The API will be available at `http://localhost:8000`.

## Testing the API

Run all tests to verify the API is working:

```bash
uv run python src/test_server.py all
```

For individual test options and API endpoint details, see [docs/SERVER_OVERVIEW.md](docs/SERVER_OVERVIEW.md).


## Additional Documentation

| Document | Description |
|----------|-------------|
| [GUIDE_DEV_CONTAINERS.md](GUIDE_DEV_CONTAINERS.md) | GitHub Codespaces and Dev Container setup |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Detailed architecture and design decisions |
| [AGENT_FRAMEWORK.md](AGENT_FRAMEWORK.md) | Microsoft Agent Framework integration notes |
| [docs/AZURE_DEPLOY_GUIDE.md](docs/AZURE_DEPLOY_GUIDE.md) | Azure deployment options (workshop vs full) |
| [docs/SERVER_OVERVIEW.md](docs/SERVER_OVERVIEW.md) | API endpoints, testing options, environment variables |
| [docs/AZ_CLI_GUIDE.md](docs/AZ_CLI_GUIDE.md) | Azure CLI reference commands |
| [docs/observability.md](docs/observability.md) | Monitoring and observability setup |
