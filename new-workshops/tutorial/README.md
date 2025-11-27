# The Complete Guide to Intelligent Document Q&A with Neo4j, Azure AI and the Microsoft Agent Framework

Welcome to this comprehensive workshop tutorial! This guide will take you on a journey from understanding the fundamentals of graph-powered AI to building and deploying production-ready intelligent agents.

## Workshop Overview

This workshop teaches you how to build sophisticated document intelligence applications by combining the power of graph databases, vector search, and modern AI agents. You'll work with real financial documents (SEC 10-K filings) to create a system that can answer complex questions about companies, their products, risks, and relationships.

### What You'll Build

By the end of this workshop, you'll understand how to:
- Perform semantic search over documents using vector embeddings
- Enhance retrieval with graph relationships and structure
- Build intelligent agents that use tools to answer complex questions
- Deploy production-ready applications with FastAPI and Azure AI Foundry
- Apply best practices for configuration, logging, and monitoring

### Technology Stack

- **Neo4j**: Graph database for storing connected document data
- **Azure AI Foundry**: Cloud-native AI platform for hosting models and agents
- **Microsoft Agent Framework**: Modern framework for building agentic AI systems
- **neo4j-graphrag-python**: Library for GraphRAG patterns and retrievers
- **FastAPI**: Modern Python web framework for API development

## Workshop Modules

### Module 1: Setting the Stage (45 minutes)
[**01_setting_the_stage.md**](01_setting_the_stage.md)

Understand the problem domain, technology stack, and set up your development environment.

**Learning Objectives:**
- Understand why graphs matter for document intelligence
- Learn about the Microsoft Agent Framework architecture
- Set up Neo4j and Azure AI Foundry
- Explore the financial document graph schema

### Module 2: Simple Retrieval (60 minutes)
[**02_simple_retrieval.md**](02_simple_retrieval.md)

Learn the basics of semantic search and GraphRAG patterns.

**Learning Objectives:**
- Understand vector embeddings and semantic search
- Build your first VectorRetriever
- Implement GraphRAG for question answering
- Evaluate retrieval quality

### Module 3: Advanced Graph Retrieval (90 minutes)
[**03_advanced_graph_retrieval.md**](03_advanced_graph_retrieval.md)

Enhance retrieval with graph structure and natural language query generation.

**Learning Objectives:**
- Enrich context with graph relationships
- Build Vector + Cypher hybrid retrievers
- Generate Cypher queries from natural language
- Compare retrieval strategies

### Module 4: Intelligent Agents (120 minutes)
[**04_intelligent_agents.md**](04_intelligent_agents.md)

Build agents that use tools to solve complex problems.

**Learning Objectives:**
- Understand the Microsoft Agent Framework
- Create tools and register them with agents
- Build multi-tool agents with orchestration
- Debug and refine agent behavior

### Module 5: Production Application (90 minutes)
[**05_production_application.md**](05_production_application.md)

Learn how to build and deploy production-ready applications.

**Learning Objectives:**
- Understand production application architecture
- Implement proper configuration management
- Build REST APIs with FastAPI
- Apply monitoring and observability
- Deploy to Azure

### Module 6: Summary and Next Steps (30 minutes)
[**06_summary_and_next_steps.md**](06_summary_and_next_steps.md)

Review what you've learned and explore advanced topics.

**Learning Objectives:**
- Recap key concepts and patterns
- Explore advanced topics
- Discover community resources

## Prerequisites

### Required Knowledge
- **Python**: Intermediate level (classes, async/await, context managers)
- **REST APIs**: Basic understanding of HTTP and JSON
- **Command Line**: Comfortable with terminal/shell commands

### Nice to Have
- Graph databases (concepts like nodes, relationships)
- Vector embeddings and semantic search
- Azure cloud platform basics

### Required Tools
- **Python 3.11+**: Modern Python runtime
- **uv**: Fast Python package manager ([install guide](https://github.com/astral-sh/uv))
- **Azure CLI**: For authentication ([install guide](https://learn.microsoft.com/cli/azure/install-azure-cli))
- **Git**: Version control
- **VS Code** (recommended): With Python and Jupyter extensions

### Azure Resources
You'll need access to:
- Azure AI Foundry project with deployed models (gpt-4o, text-embedding-ada-002)
- Neo4j database instance (AuraDB or self-hosted)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/neo4j-partners/neo4j-azure-workshop.git
cd neo4j-azure-workshop
```

### 2. Configure Azure Region

```bash
./scripts/setup_azure.sh
```

Choose your region: `eastus2`, `swedencentral`, or `westus2`

### 3. Provision Azure Infrastructure

```bash
azd up
```

This creates your Azure AI Foundry project, deploys models, and provisions resources.

### 4. Install Dependencies

```bash
uv sync --prerelease=allow
```

The `--prerelease=allow` flag is required for the Microsoft Agent Framework.

### 5. Setup Environment Variables

```bash
uv run setup_env.py
```

This creates a `.env` file in the project root with all required credentials.

### 6. Restore Neo4j Database

If you're using your own Neo4j instance:

```bash
uv run python scripts/restore_neo4j.py
```

This loads the pre-processed financial document graph.

### 7. Verify Setup

Navigate to the workshop directory:

```bash
cd new-workshops
./setup.sh
```

This installs Jupyter kernel and tests connections.

## Workshop Structure

Each module contains:
- **Concept explanations**: Clear descriptions of what you're learning
- **Code examples**: Complete, runnable code with detailed comments
- **Hands-on exercises**: Challenges to apply what you've learned
- **Tips and best practices**: Insights from production experience
- **References**: Links to notebooks and source code

## Learning Path

### Recommended Flow (6-7 hours total)
Follow modules 1-6 in sequence for comprehensive understanding.

### Fast Track (3-4 hours)
- Module 1: Quick setup (skip deep-dives)
- Module 2: Core retrieval concepts
- Module 4: Agent basics (Lab 4.1 and 4.2)
- Module 5: Production overview (skip deployment)

### Focus Areas

**For Data Scientists:**
Focus on Modules 2-4 to understand retrieval patterns and agent behavior.

**For Application Developers:**
Focus on Modules 1, 4-5 to understand the full application stack.

**For DevOps/Platform Engineers:**
Focus on Modules 1, 5 for deployment and operations.

## Getting Help

### During the Workshop
- Review the example notebooks in `new-workshops/notebooks/`
- Check solution scripts in `new-workshops/solutions/`
- Reference the production code in `src/`

### Documentation
- [Neo4j GraphRAG Python Docs](https://neo4j.com/docs/neo4j-graphrag-python/)
- [Microsoft Agent Framework Docs](https://github.com/microsoft/agent-framework)
- [Azure AI Foundry Docs](https://learn.microsoft.com/azure/ai-studio/)

### Community
- [Neo4j Community Forum](https://community.neo4j.com/)
- [Azure AI Community](https://techcommunity.microsoft.com/t5/ai-azure-ai-services/ct-p/Azure-AI-Services)

## Repository Structure

```
neo4j-azure-workshop/
├── new-workshops/
│   ├── tutorial/              # This workshop guide
│   │   ├── README.md          # This file
│   │   ├── 01_setting_the_stage.md
│   │   ├── 02_simple_retrieval.md
│   │   ├── 03_advanced_graph_retrieval.md
│   │   ├── 04_intelligent_agents.md
│   │   ├── 05_production_application.md
│   │   └── 06_summary_and_next_steps.md
│   ├── notebooks/             # Jupyter notebooks
│   └── solutions/             # Python solution scripts
├── src/                       # Production application code
│   ├── api/                   # FastAPI application
│   ├── agent.py              # Agent management
│   ├── neo4j_client.py       # Neo4j integration
│   └── vector_search.py      # Vector search implementation
└── data-pipeline/             # Document processing pipeline

```

## What Makes This Workshop Different

1. **Real-World Focus**: Uses actual SEC financial filings, not toy datasets
2. **Production-Ready**: Learn patterns used in real applications
3. **Modern Stack**: Latest Microsoft Agent Framework with Azure AI Foundry
4. **Hands-On**: Build working systems, not just read about them
5. **Complete**: From basics to deployment

## Ready to Start?

Begin with [**Module 1: Setting the Stage**](01_setting_the_stage.md) to understand the problem domain and set up your environment.

## Additional Resources

- **Project README**: [../../../README.md](../../../README.md)
- **Workshop Notebooks**: [../README.md](../README.md)
- **Architecture Guide**: [../../../ARCHITECTURE.md](../../../ARCHITECTURE.md)
- **Agent Framework Notes**: [../../../AGENT_FRAMEWORK.md](../../../AGENT_FRAMEWORK.md)

---

**Happy Learning!** 🚀

If you find this workshop helpful, please star the repository and share it with others!
