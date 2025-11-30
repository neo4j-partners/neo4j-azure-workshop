# Reference Documentation

This file consolidates all external documentation references from the project's markdown files.

---

## Microsoft Agent Framework

### Official Documentation
- [Agent Framework Overview](https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview)
- [Azure AI Foundry Agent](https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-types/azure-ai-foundry-agent)
- [Agent Types Reference](https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-types/)
- [Microsoft Learn Training Path](https://learn.microsoft.com/en-us/training/paths/develop-ai-agents-on-azure/)

### GitHub and SDK
- [Microsoft Agent Framework GitHub](https://github.com/microsoft/agent-framework)
- [AI Agents for Beginners](https://github.com/microsoft/ai-agents-for-beginners)

### Blog Posts
- [Introducing Microsoft Agent Framework (Azure Blog)](https://azure.microsoft.com/en-us/blog/introducing-microsoft-agent-framework/)
- [Microsoft Foundry Blog Announcement](https://devblogs.microsoft.com/foundry/introducing-microsoft-agent-framework-the-open-source-engine-for-agentic-ai-apps/)

---

## Azure AI Foundry

### Overview and Getting Started
- [What is Azure AI Foundry](https://learn.microsoft.com/en-us/azure/ai-foundry/what-is-azure-ai-foundry?view=foundry)
- [Get Started with Code (Python SDK)](https://learn.microsoft.com/en-us/azure/ai-foundry/quickstarts/get-started-code?view=foundry&tabs=python)
- [Azure AI Foundry Portal](https://learn.microsoft.com/en-us/azure/ai-foundry/)

### Agents and Hosted Agents
- [Hosted Agents Concepts](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/concepts/hosted-agents?view=foundry)

### Agent Tools
- [File Search Tool](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/file-search?view=foundry)
- [Code Interpreter Tool](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/code-interpreter?view=foundry)
- [MCP Server Tools](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/mcp-servers?view=foundry)

### Reference
- [Region Support](https://learn.microsoft.com/en-us/azure/ai-foundry/reference/region-support?view=foundry)

---

## Azure Authentication

### Azure Identity
- [DefaultAzureCredential Overview](https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.defaultazurecredential)
- [Azure Identity Best Practices](https://learn.microsoft.com/en-us/python/api/overview/azure/identity-readme)

### Docker Authentication
- [Using Azure CLI Auth in Containers](https://endjin.com/blog/2022/09/using-azcli-authentication-within-local-containers)
- [Obtain Azure Token from Docker](https://dev.to/oskarm93/obtain-azure-access-token-from-a-local-docker-container-35df)

---

## Azure Developer CLI

- [Azure Developer CLI Overview](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/)
- [Install Azure Developer CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd)

---

## Azure CLI

- [Install Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli)

---

## Development Tools

- [uv - Python Package Installer](https://github.com/astral-sh/uv)

---

## Neo4j GraphRAG Python Package

### Official Documentation
- [Neo4j GraphRAG Python - User Guide RAG](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_rag.html) - Comprehensive guide for RAG with retrievers
- [Neo4j GraphRAG API Documentation](https://neo4j.com/docs/neo4j-graphrag-python/current/api.html) - Full API reference
- [GitHub Repository](https://github.com/neo4j/neo4j-graphrag-python) - Source code and examples

### Hybrid Search
- [Hybrid Retrieval for GraphRAG Applications](https://neo4j.com/blog/developer/hybrid-retrieval-graphrag-python-package/) - Blog post explaining hybrid search concepts
- [HybridCypherRetriever Example](https://github.com/neo4j/neo4j-graphrag-python/blob/main/examples/retrieve/hybrid_cypher_retriever.py) - Official code example
- [Hybrid Retrieval with Graph Traversal (GraphAcademy)](https://graphacademy.neo4j.com/courses/genai-workshop-graphrag/2-neo4j-graphrag/5-hybrid-cypher-retriever/) - Interactive course

### How Hybrid Search Works
1. Query executes against both vector and fulltext indexes simultaneously
2. Each index returns results with relevance scores
3. Scores undergo normalization to ensure comparability
4. Normalized scores are combined into a unified result set
5. Merged results are ranked by consolidated score
6. Top-ranked items are returned

### Key Parameters
| Parameter | Description |
|-----------|-------------|
| `vector_index_name` | Name of the vector index for semantic search |
| `fulltext_index_name` | Name of the fulltext index for keyword search |
| `alpha` | Weight for vector score (0-1). Fulltext gets `1-alpha` |
| `top_k` | Number of results to return |
| `retrieval_query` | Cypher query for graph traversal (HybridCypherRetriever only) |

### Reranking
- [Cohere Reranker with Neo4j Full-Text Index](https://medium.com/@m.maguga-darbinian/exploring-the-combination-of-full-text-index-with-coheres-reranker-for-rag-over-a-knowledge-graph-e0a54e89a177) - Using Cohere reranker as post-processing step
- [Cohere Rerank Product Page](https://cohere.com/rerank) - About Cohere's reranking service

---

## Neo4j Indexes

### Fulltext Indexes
- [Fulltext Search in Neo4j - Knowledge Base](https://neo4j.com/developer/kb/fulltext-search-in-neo4j/)
- [Full-text indexes - Cypher Manual](https://neo4j.com/docs/cypher-manual/current/indexes-for-full-text-search/)

### Vector Indexes
- [Neo4j Vector Index and Search](https://neo4j.com/labs/genai-ecosystem/vector-search/)
- [Vector indexes - Cypher Manual](https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/)

---

## Framework Integrations

- [LangChain Neo4j Integration](https://neo4j.com/labs/genai-ecosystem/langchain/)
- [LlamaIndex Neo4j Integration](https://neo4j.com/labs/genai-ecosystem/llamaindex/)
