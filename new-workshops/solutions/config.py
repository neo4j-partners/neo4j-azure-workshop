"""
Shared configuration and utilities for workshop solutions.

This module provides common functionality for Neo4j connections,
Microsoft Foundry integration, and configuration management.
"""

import json
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

import tiktoken
from azure.identity import AzureCliCredential, DefaultAzureCredential
from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.llm import LLMResponse, OpenAILLM
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env from project root (parent of new-workshops/)
_root_env = Path(__file__).parent.parent.parent / ".env"
load_dotenv(_root_env)


class Neo4jConfig(BaseSettings):
    """Neo4j configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    uri: str = Field(validation_alias="NEO4J_URI")
    username: str = Field(validation_alias="NEO4J_USERNAME")
    password: str = Field(validation_alias="NEO4J_PASSWORD")


class AgentConfig(BaseSettings):
    """Agent configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    project_endpoint: str = Field(validation_alias="AZURE_AI_PROJECT_ENDPOINT")
    model_name: str = Field(default="gpt-4o-mini", validation_alias="AZURE_AI_MODEL_NAME")
    embedding_name: str = Field(
        default="text-embedding-ada-002",
        validation_alias="AZURE_AI_EMBEDDING_NAME",
    )

    @computed_field
    @property
    def inference_endpoint(self) -> str:
        """Get the model inference endpoint from project endpoint."""
        if "/api/projects/" in self.project_endpoint:
            base = self.project_endpoint.split("/api/projects/")[0]
            return f"{base}/models"
        return self.project_endpoint


@contextmanager
def get_neo4j_driver():
    """Context manager for Neo4j driver connection."""
    config = Neo4jConfig()
    driver = GraphDatabase.driver(
        config.uri,
        auth=(config.username, config.password),
    )
    try:
        yield driver
    finally:
        driver.close()


def get_agent_config() -> AgentConfig:
    """Get agent configuration from environment."""
    return AgentConfig()


def _get_azure_token() -> str:
    """
    Get Azure token for cognitive services.

    Tries AzureCliCredential first (for Dev Containers after 'az login'),
    then falls back to DefaultAzureCredential for other environments.

    If authentication fails, provides a helpful error message.
    """
    scope = "https://cognitiveservices.azure.com/.default"

    # Try Azure CLI first (most common in Dev Containers)
    try:
        credential = AzureCliCredential()
        token = credential.get_token(scope)
        return token.token
    except Exception:
        pass

    # Fall back to DefaultAzureCredential
    try:
        credential = DefaultAzureCredential()
        token = credential.get_token(scope)
        return token.token
    except Exception as e:
        raise RuntimeError(
            "Azure authentication failed. Please run:\n"
            "  1. az login --use-device-code\n"
            "  2. Restart your Jupyter kernel (Kernel → Restart)\n\n"
            f"Original error: {e}"
        ) from e


def get_embedder() -> OpenAIEmbeddings:
    """
    Get embedder using Microsoft Foundry's OpenAI-compatible endpoint.

    Uses Azure CLI credentials to authenticate with the inference endpoint.
    """
    config = get_agent_config()
    token = _get_azure_token()

    return OpenAIEmbeddings(
        model=config.embedding_name,
        base_url=config.inference_endpoint,
        api_key=token,
    )


def get_llm() -> OpenAILLM:
    """
    Get LLM using Microsoft Foundry's OpenAI-compatible endpoint.

    Uses Azure CLI credentials to authenticate with the inference endpoint.
    """
    config = get_agent_config()
    token = _get_azure_token()

    return OpenAILLM(
        model_name=config.model_name,
        base_url=config.inference_endpoint,
        api_key=token,
    )


# =============================================================================
# Token Counting
# =============================================================================

# Path to token usage JSON file (in solutions directory)
TOKEN_USAGE_FILE = Path(__file__).parent / "token_usage.json"


class TokenCounter:
    """
    Thread-safe token counter that persists usage to JSON.

    Tracks:
    - LLM input tokens (prompts)
    - LLM output tokens (completions)
    - Embedding tokens

    Usage is appended to a JSON file for later analysis.
    """

    def __init__(self, output_file: Path = TOKEN_USAGE_FILE):
        self.output_file = output_file
        self._lock = threading.Lock()
        self._encoder = tiktoken.get_encoding("cl100k_base")  # GPT-4/ada-002

    def count_tokens(self, text: str) -> int:
        """Count tokens in a string."""
        if not text:
            return 0
        return len(self._encoder.encode(text))

    def _load_usage(self) -> dict:
        """Load existing usage data from JSON."""
        if self.output_file.exists():
            try:
                return json.loads(self.output_file.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return {"sessions": [], "totals": {"llm_input": 0, "llm_output": 0, "embedding": 0}}

    def _save_usage(self, data: dict) -> None:
        """Save usage data to JSON."""
        self.output_file.write_text(json.dumps(data, indent=2))

    def record_llm_call(
        self,
        script: str,
        input_text: str,
        output_text: str,
        model: str,
        duration_ms: float | None = None,
    ) -> dict:
        """Record an LLM call with token counts and timing."""
        input_tokens = self.count_tokens(input_text)
        output_tokens = self.count_tokens(output_text)

        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "llm",
            "script": script,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }

        if duration_ms is not None:
            entry["duration_ms"] = duration_ms

        with self._lock:
            data = self._load_usage()
            data["sessions"].append(entry)
            data["totals"]["llm_input"] += input_tokens
            data["totals"]["llm_output"] += output_tokens
            self._save_usage(data)

        return entry

    def record_embedding_call(
        self,
        script: str,
        texts: list[str],
        model: str,
    ) -> dict:
        """Record an embedding call with token counts."""
        total_tokens = sum(self.count_tokens(t) for t in texts)

        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "embedding",
            "script": script,
            "model": model,
            "num_texts": len(texts),
            "tokens": total_tokens,
        }

        with self._lock:
            data = self._load_usage()
            data["sessions"].append(entry)
            data["totals"]["embedding"] += total_tokens
            self._save_usage(data)

        return entry

    def get_totals(self) -> dict:
        """Get current token totals."""
        with self._lock:
            data = self._load_usage()
            return data["totals"]

    def reset(self) -> None:
        """Reset all token counts."""
        with self._lock:
            self._save_usage({
                "sessions": [],
                "totals": {"llm_input": 0, "llm_output": 0, "embedding": 0},
            })


# Global token counter instance
token_counter = TokenCounter()


class TrackedLLM(OpenAILLM):
    """
    OpenAILLM wrapper that tracks token usage.

    Automatically records all LLM calls to the token usage JSON file.
    """

    def __init__(self, *args, script_name: str = "unknown", **kwargs):
        super().__init__(*args, **kwargs)
        self._script_name = script_name

    def invoke(
        self,
        input: str,
        message_history: Any = None,
        system_instruction: str | None = None,
    ) -> LLMResponse:
        """Invoke LLM and track tokens and timing."""
        start_time = time.perf_counter()
        response = super().invoke(
            input,
            message_history=message_history,
            system_instruction=system_instruction,
        )
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Include system_instruction in token count if provided
        full_input = input
        if system_instruction:
            full_input = system_instruction + "\n" + input
        token_counter.record_llm_call(
            script=self._script_name,
            input_text=full_input,
            output_text=response.content,
            model=self.model_name,
            duration_ms=duration_ms,
        )
        return response

    async def ainvoke(
        self,
        input: str,
        message_history: Any = None,
        system_instruction: str | None = None,
    ) -> LLMResponse:
        """Async invoke LLM and track tokens and timing."""
        start_time = time.perf_counter()
        response = await super().ainvoke(
            input,
            message_history=message_history,
            system_instruction=system_instruction,
        )
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Include system_instruction in token count if provided
        full_input = input
        if system_instruction:
            full_input = system_instruction + "\n" + input
        token_counter.record_llm_call(
            script=self._script_name,
            input_text=full_input,
            output_text=response.content,
            model=self.model_name,
            duration_ms=duration_ms,
        )
        return response


class TrackedEmbeddings(OpenAIEmbeddings):
    """
    OpenAIEmbeddings wrapper that tracks token usage.

    Automatically records all embedding calls to the token usage JSON file.
    """

    def __init__(self, *args, script_name: str = "unknown", **kwargs):
        super().__init__(*args, **kwargs)
        self._script_name = script_name

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query and track tokens."""
        result = super().embed_query(text)
        token_counter.record_embedding_call(
            script=self._script_name,
            texts=[text],
            model=self.model,
        )
        return result


def get_tracked_llm(script_name: str) -> TrackedLLM:
    """
    Get a token-tracking LLM using Microsoft Foundry's endpoint.

    Args:
        script_name: Name of the calling script (for tracking purposes)

    Returns:
        TrackedLLM instance that logs all token usage
    """
    config = get_agent_config()
    token = _get_azure_token()

    return TrackedLLM(
        model_name=config.model_name,
        base_url=config.inference_endpoint,
        api_key=token,
        script_name=script_name,
    )


def get_tracked_embedder(script_name: str) -> TrackedEmbeddings:
    """
    Get a token-tracking embedder using Microsoft Foundry's endpoint.

    Args:
        script_name: Name of the calling script (for tracking purposes)

    Returns:
        TrackedEmbeddings instance that logs all token usage
    """
    config = get_agent_config()
    token = _get_azure_token()

    return TrackedEmbeddings(
        model=config.embedding_name,
        base_url=config.inference_endpoint,
        api_key=token,
        script_name=script_name,
    )
