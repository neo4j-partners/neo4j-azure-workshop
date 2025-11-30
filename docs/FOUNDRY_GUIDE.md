# Azure AI Foundry Setup Guide

After provisioning your Azure infrastructure with `azd up` (as described in the main [README.md](../README.md)), open [https://ai.azure.com/](https://ai.azure.com/) to configure your AI Foundry project.

## Verify Model Deployments

When you open Azure AI Foundry, you will see that it has registered two models:
- **gpt-4o** - The large language model for chat and reasoning
- **text-embedding-ada-002** - The embedding model for vector search

![Models Section](../images/models_section.png)

## CRITICAL: Increase Azure AI Token Quota

Before running the workshops, you **must** increase the token rate limits for your Azure AI model deployments, or you will encounter rate limiting errors.

1. Go to [https://ai.azure.com/](https://ai.azure.com/)
2. Click **Build** in the top navigation bar
3. Select your project and click **Models** in the left sidebar
4. Click on **gpt-4o** in the model list
5. Click the **Details** tab
6. Click **Edit** to open the deployment settings
7. Find the **Tokens per Minute Rate Limit** slider and set it to the maximum available
8. Click **Save** to apply the changes

![Token Limits](../images/token_limits.png)

Repeat the same steps for **text-embedding-ada-002**:
1. Click on **text-embedding-ada-002** in the model list
2. Go to the **Details** tab
3. Click **Edit**
4. Set the **Tokens per Minute Rate Limit** to the maximum available
5. Click **Save**

Once both models have their token limits increased, you're ready to proceed with the workshops.
