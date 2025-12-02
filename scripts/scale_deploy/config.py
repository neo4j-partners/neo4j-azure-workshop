"""
Configuration constants and paths for scale deployment.
"""

from pathlib import Path

# Default Azure region for Microsoft Foundry
DEFAULT_REGION = "eastus2"

# Project root directory (two levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Deployments directory for environment state and logs
DEPLOYMENTS_DIR = PROJECT_ROOT / "deployments"

# Token usage paths
TOKEN_USAGE_DIR = PROJECT_ROOT / "new-workshops" / "solutions" / "token_usage"
TOKEN_USAGE_FILE = PROJECT_ROOT / "new-workshops" / "solutions" / "token_usage.json"
