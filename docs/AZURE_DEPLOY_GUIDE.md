# Azure Deployment Guide

This guide covers deployment options for the Neo4j Azure Workshop infrastructure.

## Default Deployment (Workshop Mode)

By default, `azd up` deploys only the core AI infrastructure without the Container App. This is faster and sufficient for local development during workshops.

```bash
azd up
```

**What gets deployed:**
- Azure AI Foundry Project
- Azure AI Services (GPT-4o + Embeddings)
- Storage Account
- Log Analytics & Application Insights
- Role assignments for your user

**What is NOT deployed:**
- Container Apps Environment
- Container Registry
- Container App (API)

## Full Deployment (With Container App)

To deploy the complete infrastructure including the Container App for production hosting:

```bash
azd up --parameter deployContainerApp=true
```

**Additional resources deployed:**
- Azure Container Apps Environment
- Azure Container Registry
- Container App (`ca-api-*`) running the FastAPI application
- Managed Identity for the Container App
- Role assignments for the Container App identity

### Setting as Default

To always deploy the Container App, add to your `azd` environment:

```bash
azd env set deployContainerApp true
```

Or edit `infra/main.parameters.json`:

```json
{
  "parameters": {
    "deployContainerApp": {
      "value": true
    }
  }
}
```

## Redeployment Notes

### Skipping Role Assignments

If you encounter `RoleAssignmentExists` errors on redeployment:

```bash
azd up --parameter skipRoleAssignments=true
```

### Deploying Container App Later

If you initially deployed without the Container App and want to add it later:

```bash
azd up --parameter deployContainerApp=true
```

The existing AI infrastructure will be preserved and only the Container App resources will be added.

## Environment Variables After Deployment

After deployment, run the setup script to create your local `.env` file:

```bash
uv run setup_env.py
```

This pulls all necessary environment variables from `azd` for local development.
