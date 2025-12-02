# Scale Testing Guide

This guide explains how to deploy multiple Azure environments and run tests across them to measure token usage and validate workshop content.

## Prerequisites

- Azure CLI authenticated: `az login`
- Azure Developer CLI authenticated: `azd auth login`
- Neo4j database with workshop data (shared across all environments)

## Quick Start

```bash
# 1. Prepare 3 environments (creates resource groups and azd envs)
uv run python scripts/scale_deploy.py prepare --count 3 --prefix workshop

# 2. Open 3 terminal windows and run azd up in each:
#    Terminal 1: azd up -e workshop-01
#    Terminal 2: azd up -e workshop-02
#    Terminal 3: azd up -e workshop-03

# 3. After all deployments complete, generate .env files
uv run python scripts/scale_deploy.py generate-env --all

# 4. Check deployment status
uv run python scripts/scale_deploy.py status

# 5. Run tests on all environments
uv run python scripts/scale_deploy.py test --all

# 6. View token usage report
uv run python new-workshops/solutions/token_report.py

# 7. Cleanup when done
uv run python scripts/scale_deploy.py destroy --all --yes
```

## Commands

### Prepare Environments

```bash
# Prepare N environments with default settings (eastus2)
uv run python scripts/scale_deploy.py prepare --count 5 --prefix workshop

# Prepare for a specific region
uv run python scripts/scale_deploy.py prepare --count 3 --prefix test --region swedencentral

# Skip resource group creation (use existing)
uv run python scripts/scale_deploy.py prepare --count 3 --prefix workshop --skip-rg

# Supported regions: eastus2, swedencentral, westus2
```

**What happens during preparation:**
1. Creates resource group `rg-{prefix}-{NN}` for each environment
2. Purges any soft-deleted Cognitive Services that would block deployment
3. Creates azd environment with variables set
4. Saves status to `deployments/{env}/status.json`

### Deploy Each Environment

After preparation, open separate terminal windows and run `azd up` for each environment:

```bash
# Terminal 1
cd /path/to/neo4j-azure-workshop
azd up -e workshop-01

# Terminal 2
cd /path/to/neo4j-azure-workshop
azd up -e workshop-02

# Terminal 3
cd /path/to/neo4j-azure-workshop
azd up -e workshop-03
```

Each deployment takes 5-10 minutes. Running them in parallel saves time.

### Generate .env Files

After all `azd up` commands complete:

```bash
# Generate .env files for all environments
uv run python scripts/scale_deploy.py generate-env --all

# Generate for a specific environment
uv run python scripts/scale_deploy.py generate-env --env workshop-01
```

### Check Status

```bash
uv run python scripts/scale_deploy.py status
```

**Sample output:**
```
======================================================================
DEPLOYMENT STATUS
======================================================================
Created: 2024-01-15T10:30:00
Updated: 2024-01-15T10:45:00
======================================================================

Environment          Status       Resource Group            Region
----------------------------------------------------------------------
workshop-01          deployed     rg-workshop-01            eastus2
workshop-02          deployed     rg-workshop-02            eastus2
workshop-03          prepared     rg-workshop-03            eastus2
----------------------------------------------------------------------
Total: 3 | Deployed: 2 | Prepared: 1 | Failed: 0

💡 Tip: Run 'azd up -e ENV_NAME' for each prepared environment
```

### Run Tests

```bash
# Run batch test (solutions 4-11) on ALL deployed environments
uv run python scripts/scale_deploy.py test --all

# Run on a specific environment
uv run python scripts/scale_deploy.py test --env workshop-01

# Run a specific solution
uv run python scripts/scale_deploy.py test --env workshop-01 --solution 4
```

**How testing works:**
1. Backs up your current `.env` file
2. Swaps in the target environment's `.env`
3. Runs the specified solution(s)
4. Restores your original `.env`

### View Token Usage

```bash
# Show token usage report
uv run python new-workshops/solutions/token_report.py

# Reset token counts before a fresh test run
uv run python new-workshops/solutions/token_report.py --reset

# Export raw JSON data
uv run python new-workshops/solutions/token_report.py --json
```

### Destroy Environments

```bash
# Destroy all environments (with confirmation)
uv run python scripts/scale_deploy.py destroy --all

# Destroy all environments (skip confirmation)
uv run python scripts/scale_deploy.py destroy --all --yes

# Destroy a specific environment
uv run python scripts/scale_deploy.py destroy --env workshop-01
```

## Solution Reference

| Solution | Menu # | Description | API Calls |
|----------|--------|-------------|-----------|
| 01_01_data_loading | 1 | Data Loading | None (Neo4j only) |
| 01_02_embeddings | 2 | Embeddings | Embedding |
| 01_03_entity_extraction | 3 | Entity Extraction | LLM + Embedding |
| 02_01_vector_retriever | 4 | Vector Retriever | LLM + Embedding |
| 02_02_vector_cypher_retriever | 5 | Vector Cypher Retriever | LLM + Embedding |
| 02_03_text2cypher_retriever | 6 | Text2Cypher Retriever | LLM |
| 03_01_simple_agent | 7 | Simple Agent | LLM (Agent Framework) |
| 03_02_vector_graph_agent | 8 | Vector Graph Agent | LLM + Embedding |
| 03_03_text2cypher_agent | 9 | Text2Cypher Agent | LLM + Embedding |
| 05_01_fulltext_search | 10 | Fulltext Search | None (Neo4j only) |
| 05_02_hybrid_search | 11 | Hybrid Search | Embedding |
| **Batch (4-11)** | **12** | **All 02+ solutions** | **All** |

## Directory Structure

After deployment, files are organized as:

```
deployments/
├── workshop-01/
│   ├── .env              # Azure + Neo4j environment variables
│   └── status.json       # Deployment status and metadata
├── workshop-02/
│   ├── .env
│   └── status.json
├── workshop-03/
│   ├── .env
│   └── status.json
└── summary.json          # Overall deployment summary
```

## Example: Full Test Run

```bash
# Reset token counter
uv run python new-workshops/solutions/token_report.py --reset

# Prepare 3 environments
uv run python scripts/scale_deploy.py prepare --count 3 --prefix loadtest

# Open 3 terminals and run azd up -e loadtest-01, azd up -e loadtest-02, etc.
# Wait for all to complete...

# Generate .env files
uv run python scripts/scale_deploy.py generate-env --all

# Run tests on all
uv run python scripts/scale_deploy.py test --all

# View aggregated token usage
uv run python new-workshops/solutions/token_report.py

# Sample output:
# ======================================================================
# TOKEN USAGE REPORT
# ======================================================================
#
# OVERALL TOTALS
# ----------------------------------------
#   LLM Input Tokens:          37,350
#   LLM Output Tokens:          9,840
#   Embedding Tokens:          26,760
#   ────────────────────────────
#   TOTAL TOKENS:              73,950
#
# USAGE BY SCRIPT
# ----------------------------------------------------------------------
# Script                              LLM In     LLM Out      Embed
# ----------------------------------------------------------------------
# 02_01_vector_retriever               3,600       1,350      3,300
# 02_02_vector_cypher_retriever        6,300       1,860      4,200
# ...

# Cleanup
uv run python scripts/scale_deploy.py destroy --all --yes
```

## Azure Quota Considerations

### Default Model Settings

| Model | TPM (per deployment) |
|-------|---------------------|
| gpt-4o-mini | 10K |
| text-embedding-ada-002 | 5K |

### Subscription Limits

TPM quota is **shared across all deployments** in a subscription:
- 3 environments × 10K TPM = 30K TPM used from quota
- 10 environments × 10K TPM = 100K TPM used from quota

If you hit rate limits:
1. Reduce number of concurrent environments
2. Request quota increase in Azure Portal
3. Spread deployments across multiple regions

### Checking Quota

```bash
# View current OpenAI quota usage
az cognitiveservices account list -g <resource-group> -o table
```

## Troubleshooting

### Deployment Fails

```bash
# Check status for error details
uv run python scripts/scale_deploy.py status

# View specific environment status
cat deployments/workshop-01/status.json
```

### Soft-Deleted Resources Block Deployment

If you see an error about soft-deleted resources, the `prepare` command automatically purges them. If needed manually:

```bash
# List soft-deleted Cognitive Services
az cognitiveservices account list-deleted -o table

# Purge a specific account
az cognitiveservices account purge \
  --name <account-name> \
  --resource-group <resource-group> \
  --location <location>
```

### Rate Limiting During Tests

If tests fail due to rate limiting:

1. Run tests sequentially instead of batch:
   ```bash
   uv run python scripts/scale_deploy.py test --env workshop-01 --solution 4
   uv run python scripts/scale_deploy.py test --env workshop-01 --solution 5
   # ... etc
   ```

2. Add delays between environments (manual):
   ```bash
   uv run python scripts/scale_deploy.py test --env workshop-01
   sleep 60
   uv run python scripts/scale_deploy.py test --env workshop-02
   ```

### .env Not Restored

If something goes wrong and your `.env` isn't restored:

```bash
# Check for backup
ls -la .env.backup

# Restore manually if needed
cp .env.backup .env
```

## See Also

- [SCALE.md](SCALE.md) - Architecture proposal and future phases
- [README.md](README.md) - Main project documentation
- [new-workshops/README.md](new-workshops/README.md) - Workshop guide
