"""Azure OpenAI utilities for the pipeline.

Provides factory functions for creating Azure OpenAI LLM and embedder
instances with Azure AD authentication.
"""

from collections.abc import Callable

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from neo4j import Driver, GraphDatabase
from neo4j_graphrag.embeddings import AzureOpenAIEmbeddings
from neo4j_graphrag.llm import AzureOpenAILLM
from neo4j_graphrag.utils.rate_limit import RetryRateLimitHandler

from pipeline.config import PipelineSettings

# Type alias for the token provider callable
TokenProvider = Callable[[], str]


def create_rate_limit_handler() -> RetryRateLimitHandler:
    """Create a rate limit handler for Azure OpenAI.

    Configured with longer waits and more retries than default
    to handle Azure OpenAI rate limits gracefully.

    Returns:
        Configured RetryRateLimitHandler instance.
    """
    return RetryRateLimitHandler(
        max_attempts=5,
        min_wait=5.0,
        max_wait=120.0,
        multiplier=2.0,
        jitter=True,
    )


def get_token_provider() -> TokenProvider:
    """Create Azure AD token provider for Azure OpenAI authentication.

    Returns:
        A callable that returns bearer tokens for Azure Cognitive Services.
    """
    credential = DefaultAzureCredential()
    return get_bearer_token_provider(
        credential, "https://cognitiveservices.azure.com/.default"
    )


def create_llm(settings: PipelineSettings) -> AzureOpenAILLM:
    """Create an Azure OpenAI LLM for entity extraction.

    Args:
        settings: Pipeline settings containing Azure OpenAI configuration.

    Returns:
        Configured AzureOpenAILLM instance with rate limit handling.
    """
    return AzureOpenAILLM(
        model_name=settings.llm.deployment_name,
        azure_endpoint=settings.llm.endpoint,
        api_version=settings.llm.api_version,
        azure_ad_token_provider=get_token_provider(),
        rate_limit_handler=create_rate_limit_handler(),
    )


def create_embedder(settings: PipelineSettings) -> AzureOpenAIEmbeddings:
    """Create an Azure OpenAI embedder for chunk embeddings.

    Args:
        settings: Pipeline settings containing Azure OpenAI configuration.

    Returns:
        Configured AzureOpenAIEmbeddings instance with rate limit handling.
    """
    return AzureOpenAIEmbeddings(
        model=settings.embedding.deployment_name,
        azure_endpoint=settings.llm.endpoint,
        api_version=settings.llm.api_version,
        azure_ad_token_provider=get_token_provider(),
        rate_limit_handler=create_rate_limit_handler(),
    )


def create_neo4j_driver(settings: PipelineSettings) -> Driver:
    """Create a Neo4j driver.

    Args:
        settings: Pipeline settings containing Neo4j configuration.

    Returns:
        Configured Neo4j driver.
    """
    return GraphDatabase.driver(
        settings.neo4j.uri,
        auth=(settings.neo4j.username, settings.neo4j.password),
    )
