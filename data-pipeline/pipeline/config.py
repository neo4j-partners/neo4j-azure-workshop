"""Configuration for the document processing pipeline.

Uses pydantic-settings for environment-based configuration.
Loads .env from the project root (parent of data-pipeline).
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_project_root() -> Path:
    """Get the project root directory (parent of data-pipeline)."""
    # config.py -> pipeline/ -> data-pipeline/ -> neo4j-azure-workshop/
    return Path(__file__).parent.parent.parent


def get_env_file_path() -> Path:
    """Get the path to the .env file in the project root."""
    return get_project_root() / ".env"


class EmbeddingSettings(BaseSettings):
    """Configuration for Azure OpenAI embeddings."""

    model_config = SettingsConfigDict(
        env_file=get_env_file_path(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    deployment_name: str = Field(
        default="text-embedding-ada-002",
        validation_alias="AZURE_AI_EMBEDDING_NAME",
        description="Name of the embedding model deployment",
    )
    dimensions: int = Field(
        default=1536,
        validation_alias="EMBEDDING_DIMENSIONS",
        description="Embedding vector dimensions (1536 for ada-002, 3072 for text-embedding-3-large)",
    )


class Neo4jSettings(BaseSettings):
    """Configuration for Neo4j database connection.

    Loads credentials from environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=get_env_file_path(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    uri: str = Field(
        validation_alias="NEO4J_URI",
        description="Neo4j connection URI",
    )
    username: str = Field(
        validation_alias="NEO4J_USERNAME",
        description="Neo4j username",
    )
    password: str = Field(
        validation_alias="NEO4J_PASSWORD",
        description="Neo4j password",
    )
    vector_index_name: str = Field(
        default="chunkEmbeddings",
        validation_alias="NEO4J_VECTOR_INDEX_NAME",
        description="Name of the vector index for chunk embeddings",
    )
    database: str = Field(
        default="neo4j",
        description="Neo4j database name",
    )


class LLMSettings(BaseSettings):
    """Configuration for Azure OpenAI LLM.

    Used for entity extraction via SimpleKGPipeline.
    Uses Azure OpenAI endpoint with GPT models.
    """

    model_config = SettingsConfigDict(
        env_file=get_env_file_path(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    endpoint: str = Field(
        validation_alias="AZURE_OPENAI_ENDPOINT",
        description="Azure OpenAI endpoint",
    )

    deployment_name: str = Field(
        default="gpt-4o-mini",
        validation_alias="AZURE_AI_MODEL_NAME",
        description="Name of the chat model deployment",
    )

    api_version: str = Field(
        default="2024-10-21",
        description="Azure OpenAI API version",
    )


class PipelineSettings(BaseSettings):
    """Main pipeline configuration.

    Loads settings from environment variables and .env file in project root.
    """

    model_config = SettingsConfigDict(
        env_file=get_env_file_path(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    pdf_directory: Path = Field(
        default_factory=lambda: get_project_root() / "financial-data" / "form10k-sample",
        description="Directory containing PDF files to process",
    )

    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )

    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    neo4j: Neo4jSettings = Field(default_factory=Neo4jSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)


def get_settings() -> PipelineSettings:
    """Create and return pipeline settings.

    Factory function for consistent settings access.
    """
    return PipelineSettings()
