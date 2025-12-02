"""
Azure CLI utilities for resource management.
"""

import json
import os
import subprocess
from pathlib import Path

from .config import PROJECT_ROOT


def run_command(
    cmd: list[str],
    cwd: Path | None = None,
    env: dict | None = None,
    capture: bool = False,
) -> subprocess.CompletedProcess:
    """Run a shell command with optional environment."""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)

    if capture:
        return subprocess.run(
            cmd,
            cwd=cwd,
            env=full_env,
            capture_output=True,
            text=True,
        )
    return subprocess.run(cmd, cwd=cwd, env=full_env)


def check_azure_auth() -> bool:
    """Check if user is authenticated with Azure CLI and azd."""
    result = run_command(["az", "account", "show"], capture=True)
    if result.returncode != 0:
        print("Error: Not logged into Azure CLI. Run: az login")
        return False

    result = run_command(["azd", "auth", "login", "--check-status"], capture=True)
    if result.returncode != 0:
        print("Error: Not logged into Azure Developer CLI. Run: azd auth login")
        return False

    return True


def get_subscription_id() -> str | None:
    """Get current Azure subscription ID."""
    result = run_command(
        ["az", "account", "show", "--query", "id", "-o", "tsv"],
        capture=True,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def create_resource_group(name: str, location: str) -> bool:
    """Create an Azure resource group."""
    result = run_command(
        ["az", "group", "create", "--name", name, "--location", location, "-o", "none"],
        capture=True,
    )
    if result.returncode != 0:
        print(f"  Error creating resource group: {result.stderr}")
        return False
    return True


def delete_resource_group(name: str) -> bool:
    """Delete an Azure resource group (async)."""
    print(f"  Deleting resource group: {name}...")
    result = run_command(
        ["az", "group", "delete", "--name", name, "--yes", "--no-wait"],
        capture=True,
    )
    return result.returncode == 0


def purge_soft_deleted_cognitive_services(resource_group: str, location: str) -> None:
    """Purge any soft-deleted Cognitive Services in the resource group."""
    result = run_command(
        ["az", "cognitiveservices", "account", "list-deleted", "-o", "json"],
        capture=True,
    )

    if result.returncode != 0 or not result.stdout:
        return

    try:
        deleted = json.loads(result.stdout)
    except json.JSONDecodeError:
        return

    for account in deleted:
        account_id = account.get("id", "")
        account_name = account.get("name", "")
        account_location = account.get("location", "")

        if f"/resourceGroups/{resource_group}/" in account_id:
            print(f"  Purging soft-deleted resource: {account_name}")
            run_command(
                [
                    "az", "cognitiveservices", "account", "purge",
                    "--name", account_name,
                    "--resource-group", resource_group,
                    "--location", account_location,
                ],
                capture=True,
            )


def create_azd_environment(env_name: str) -> tuple[bool, str]:
    """
    Create an azd environment.

    Returns: (success, message)
    """
    result = run_command(
        ["azd", "env", "new", env_name, "--no-prompt"],
        cwd=PROJECT_ROOT,
        capture=True,
    )

    output = (result.stdout or "") + (result.stderr or "")

    if result.returncode != 0 and "already exists" not in output.lower():
        return False, output.strip() or "Unknown error"

    if "already exists" in output.lower():
        return True, "already_exists"

    return True, "created"


def set_azd_env_var(env_name: str, var_name: str, var_value: str) -> bool:
    """Set an environment variable in an azd environment."""
    result = run_command(
        ["azd", "env", "set", var_name, var_value, "-e", env_name],
        cwd=PROJECT_ROOT,
        capture=True,
    )
    return result.returncode == 0


def delete_azd_environment(env_name: str) -> bool:
    """Delete an azd environment."""
    result = run_command(
        ["azd", "env", "delete", env_name, "--force", "--no-prompt"],
        cwd=PROJECT_ROOT,
        capture=True,
    )
    return result.returncode == 0


def get_azd_env_values(env_name: str) -> str | None:
    """Get environment values from an azd environment."""
    result = run_command(
        ["azd", "env", "get-values", "-e", env_name],
        cwd=PROJECT_ROOT,
        capture=True,
    )
    if result.returncode == 0:
        return result.stdout
    return None
