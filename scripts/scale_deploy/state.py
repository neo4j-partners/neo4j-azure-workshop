"""
Deployment state management - loading and saving environment status.
"""

import json
from datetime import datetime
from pathlib import Path

from .config import DEPLOYMENTS_DIR


def load_summary() -> dict:
    """Load deployment summary from JSON file."""
    summary_file = DEPLOYMENTS_DIR / "summary.json"
    if summary_file.exists():
        try:
            return json.loads(summary_file.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"environments": {}, "created_at": None, "updated_at": None}


def save_summary(summary: dict) -> None:
    """Save deployment summary to JSON file."""
    DEPLOYMENTS_DIR.mkdir(parents=True, exist_ok=True)
    summary["updated_at"] = datetime.now().isoformat()
    summary_file = DEPLOYMENTS_DIR / "summary.json"
    summary_file.write_text(json.dumps(summary, indent=2))


def load_env_status(env_name: str) -> dict:
    """Load status for a specific environment."""
    status_file = DEPLOYMENTS_DIR / env_name / "status.json"
    if status_file.exists():
        try:
            return json.loads(status_file.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"status": "unknown", "env_name": env_name}


def save_env_status(env_name: str, status: dict) -> None:
    """Save status for a specific environment."""
    env_dir = DEPLOYMENTS_DIR / env_name
    env_dir.mkdir(parents=True, exist_ok=True)
    status["updated_at"] = datetime.now().isoformat()
    status_file = env_dir / "status.json"
    status_file.write_text(json.dumps(status, indent=2))


def get_deployed_environments() -> list[str]:
    """Get list of deployed environment names."""
    summary = load_summary()
    return [
        name for name, status in summary["environments"].items()
        if status.get("status") == "deployed"
    ]


def get_env_file_path(env_name: str) -> Path:
    """Get the .env file path for an environment."""
    return DEPLOYMENTS_DIR / env_name / ".env"


def parse_env_file(env_file: Path) -> dict:
    """Parse a .env file and return as dict merged with current environment."""
    import os
    env_vars = os.environ.copy()
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            # Remove quotes if present
            value = value.strip().strip('"').strip("'")
            env_vars[key.strip()] = value
    return env_vars
