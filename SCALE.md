# Scaling Workshop Deployments

This document proposes an approach for deploying multiple Azure environments in parallel for load testing, workshop provisioning, or stress testing token limits.

## Status

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Sequential deployment with status tracking | **Implemented** |
| Phase 2 | Parallel deployment with batching | Planned |
| Phase 3 | Test orchestration | Planned |
| Phase 4 | CI/CD integration | Planned |

## Quick Start

```bash
# Deploy 3 environments
uv run python scripts/scale_deploy.py deploy --count 3 --prefix workshop --region eastus2

# Check status
uv run python scripts/scale_deploy.py status

# Run tests on all deployed environments
uv run python scripts/scale_deploy.py test --all

# Destroy all environments
uv run python scripts/scale_deploy.py destroy --all --yes
```

## Use Cases

1. **Workshop Provisioning** - Pre-create N environments for workshop participants
2. **Load Testing** - Deploy multiple environments to test aggregate token consumption
3. **CI/CD Testing** - Spin up isolated environments for parallel test runs

## Proposed Architecture

### Resource Naming Convention

Each environment gets a unique identifier:

```
Environment: workshop-{index}
Resource Group: rg-neo4j-workshop-{index}
AI Project: proj-{unique-suffix}
```

### Deployment Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    scale_deploy.py                          │
│                                                             │
│  Input: --count 5 --prefix workshop --region eastus2        │
│                                                             │
│  1. Validate Azure authentication                           │
│  2. Check subscription quotas                               │
│  3. Create resource groups (parallel)                       │
│  4. Deploy azd environments (parallel with rate limiting)   │
│  5. Generate .env files per environment                     │
│  6. Output summary report                                   │
└─────────────────────────────────────────────────────────────┘
```

### Parallelization Strategy

Azure has rate limits and quota constraints. The script should:

1. **Batch deployments** - Deploy in batches of 3-5 to avoid throttling
2. **Stagger starts** - Add 30-60 second delays between batch starts
3. **Use git worktrees** - Each deployment needs its own `.azure/` directory
4. **Track progress** - Write status to a JSON file for monitoring

### Directory Structure

```
deployments/
├── workshop-01/
│   ├── .azure/           # azd environment
│   ├── .env              # Environment variables
│   └── status.json       # Deployment status
├── workshop-02/
│   └── ...
└── summary.json          # Overall deployment summary
```

## Script Interface

### Deploy Multiple Environments

```bash
# Deploy 5 environments with prefix "workshop" in eastus2
uv run python scripts/scale_deploy.py deploy \
    --count 5 \
    --prefix workshop \
    --region eastus2 \
    --subscription "My Subscription"

# Deploy with existing resource groups (workshop scenario)
uv run python scripts/scale_deploy.py deploy \
    --count 10 \
    --resource-groups rg-user-01,rg-user-02,...,rg-user-10
```

### Check Status

```bash
# Check deployment status
uv run python scripts/scale_deploy.py status

# Output:
# workshop-01: deployed (proj-abc123)
# workshop-02: deployed (proj-def456)
# workshop-03: deploying...
# workshop-04: pending
# workshop-05: failed (quota exceeded)
```

### Run Tests Across Environments

```bash
# Run token counting across all deployed environments
uv run python scripts/scale_deploy.py test --all

# Run specific workshop solutions
uv run python scripts/scale_deploy.py test --solution 12  # batch run
```

### Cleanup

```bash
# Destroy all environments
uv run python scripts/scale_deploy.py destroy --all

# Destroy specific environment
uv run python scripts/scale_deploy.py destroy --env workshop-03
```

## Implementation Phases

### Phase 1: Basic Multi-Deploy

- Create N resource groups
- Deploy azd environments sequentially
- Generate per-environment .env files
- Basic status tracking

### Phase 2: Parallel Deployment

- Use asyncio/subprocess for parallel deployments
- Implement batching with rate limiting
- Add retry logic for transient failures
- Progress reporting

### Phase 3: Test Orchestration

- Run workshop solutions across environments
- Aggregate token usage reports
- Compare performance across deployments

### Phase 4: CI/CD Integration

- GitHub Actions workflow for automated testing
- Matrix strategy for parallel environment testing
- Automatic cleanup after test completion

## Azure Quota Considerations

### Default Quotas (per subscription)

| Resource | Default Limit | Notes |
|----------|---------------|-------|
| Resource Groups | 980 | Rarely a limit |
| AI Foundry Projects | Varies | Check subscription |
| OpenAI TPM (gpt-4o-mini) | 450K | Shared across deployments |
| OpenAI TPM (embeddings) | 350K | Shared across deployments |
| Storage Accounts | 250 | Per region |

### Quota Strategy

- **TPM is shared** - 10 environments with 5K TPM each = 50K TPM total from quota
- **Request quota increase** before large-scale testing
- **Use different regions** to distribute load (eastus2, swedencentral, westus2)

## Configuration File

Optional `scale-config.yaml` for complex deployments:

```yaml
deployments:
  count: 10
  prefix: workshop
  region: eastus2

  # Per-environment overrides
  environments:
    - name: workshop-01
      tpm_chat: 10
      tpm_embedding: 10
    - name: workshop-02
      tpm_chat: 5
      tpm_embedding: 5

  # Batching
  batch_size: 3
  batch_delay_seconds: 60

  # Neo4j (shared across all)
  neo4j:
    uri: ${NEO4J_URI}
    username: ${NEO4J_USERNAME}
    password: ${NEO4J_PASSWORD}
```

## Token Usage Aggregation

After running tests across multiple environments:

```bash
# Aggregate token reports from all environments
uv run python scripts/scale_deploy.py aggregate-tokens

# Output:
# ══════════════════════════════════════════════════════════════
# AGGREGATE TOKEN USAGE (10 environments)
# ══════════════════════════════════════════════════════════════
#
# Total LLM Input:      124,500 tokens
# Total LLM Output:      32,800 tokens
# Total Embedding:       89,200 tokens
# ────────────────────────────────────
# GRAND TOTAL:          246,500 tokens
#
# Per-Environment Average: 24,650 tokens
# Estimated Cost: $0.037 (gpt-4o-mini) + $0.013 (embeddings) = $0.05
```

## Next Steps

1. Review this proposal and provide feedback
2. Confirm Azure quota limits for target subscription
3. Decide on Phase 1 scope (sequential vs parallel)
4. Implement `scripts/scale_deploy.py`
