#!/usr/bin/env python3
"""
Scale Deployment Script - Simplified

Prepares multiple Azure environments for workshop provisioning.
Creates resource groups and azd environments, then you run `azd up` manually
in separate terminal windows.

Usage:
    uv run python scripts/scale_deploy.py prepare --count 3 --prefix workshop
    uv run python scripts/scale_deploy.py status
    uv run python scripts/scale_deploy.py destroy --all
    uv run python scripts/scale_deploy.py test --env workshop-01
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Supported Azure regions for Microsoft Foundry
SUPPORTED_REGIONS = ["eastus2", "swedencentral", "westus2"]

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Deployments directory
DEPLOYMENTS_DIR = PROJECT_ROOT / "deployments"


def run_command(
    cmd: list[str],
    cwd: Optional[Path] = None,
    env: Optional[dict] = None,
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
    else:
        return subprocess.run(cmd, cwd=cwd, env=full_env)


def check_azure_auth() -> bool:
    """Check if user is authenticated with Azure CLI."""
    result = run_command(["az", "account", "show"], capture=True)
    if result.returncode != 0:
        print("Error: Not logged into Azure CLI. Run: az login")
        return False

    result = run_command(["azd", "auth", "login", "--check-status"], capture=True)
    if result.returncode != 0:
        print("Error: Not logged into Azure Developer CLI. Run: azd auth login")
        return False

    return True


def get_subscription_id() -> Optional[str]:
    """Get current Azure subscription ID."""
    result = run_command(
        ["az", "account", "show", "--query", "id", "-o", "tsv"],
        capture=True,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def load_summary() -> dict:
    """Load deployment summary from JSON file."""
    summary_file = DEPLOYMENTS_DIR / "summary.json"
    if summary_file.exists():
        return json.loads(summary_file.read_text())
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
        return json.loads(status_file.read_text())
    return {"status": "unknown", "env_name": env_name}


def save_env_status(env_name: str, status: dict) -> None:
    """Save status for a specific environment."""
    env_dir = DEPLOYMENTS_DIR / env_name
    env_dir.mkdir(parents=True, exist_ok=True)
    status["updated_at"] = datetime.now().isoformat()
    status_file = env_dir / "status.json"
    status_file.write_text(json.dumps(status, indent=2))


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


def delete_resource_group(name: str) -> bool:
    """Delete an Azure resource group."""
    print(f"  Deleting resource group: {name}...")
    result = run_command(
        ["az", "group", "delete", "--name", name, "--yes", "--no-wait"],
        capture=True,
    )
    return result.returncode == 0


def cmd_prepare(args: argparse.Namespace) -> int:
    """Prepare multiple environments (create RGs and azd envs, but don't deploy)."""
    if not check_azure_auth():
        return 1

    if args.region not in SUPPORTED_REGIONS:
        print(f"Error: Region '{args.region}' not supported.")
        print(f"Supported regions: {', '.join(SUPPORTED_REGIONS)}")
        return 1

    subscription = args.subscription or get_subscription_id()
    if not subscription:
        print("Error: Could not determine Azure subscription.")
        return 1

    print(f"\n{'=' * 60}")
    print(f"PREPARING {args.count} ENVIRONMENT(S)")
    print(f"{'=' * 60}")
    print(f"  Prefix:       {args.prefix}")
    print(f"  Region:       {args.region}")
    print(f"  Subscription: {subscription[:8]}...")
    print(f"{'=' * 60}\n")

    summary = load_summary()
    if summary["created_at"] is None:
        summary["created_at"] = datetime.now().isoformat()

    environments = []

    for i in range(1, args.count + 1):
        env_name = f"{args.prefix}-{i:02d}"
        resource_group = f"rg-{args.prefix}-{i:02d}"

        print(f"[{i}/{args.count}] Preparing: {env_name}")

        status = {
            "env_name": env_name,
            "resource_group": resource_group,
            "region": args.region,
            "subscription": subscription,
            "status": "prepared",
            "created_at": datetime.now().isoformat(),
        }

        # Create resource group
        if not args.skip_rg:
            print(f"  Creating resource group: {resource_group}")
            if not create_resource_group(resource_group, args.region):
                status["status"] = "failed"
                status["error"] = "Failed to create resource group"
                save_env_status(env_name, status)
                summary["environments"][env_name] = status
                save_summary(summary)
                continue

        # Purge any soft-deleted Cognitive Services
        purge_soft_deleted_cognitive_services(resource_group, args.region)

        # Create azd environment (or use existing)
        print(f"  Creating azd environment: {env_name}")
        result = run_command(
            ["azd", "env", "new", env_name, "--no-prompt"],
            cwd=PROJECT_ROOT,
            capture=True,
        )

        # Check if environment already exists (message could be in stdout or stderr)
        output = (result.stdout or "") + (result.stderr or "")
        if result.returncode != 0 and "already exists" not in output.lower():
            print(f"  Error: {output.strip() or 'Unknown error'}")
            status["status"] = "failed"
            status["error"] = "Failed to create azd environment"
            save_env_status(env_name, status)
            summary["environments"][env_name] = status
            save_summary(summary)
            continue

        if "already exists" in output.lower():
            print(f"  (environment already exists, reusing)")
        else:
            print(f"  (created new environment)")

        # Set environment variables
        print(f"  Setting azd environment variables")
        env_vars = [
            ("AZURE_LOCATION", args.region),
            ("AZURE_RESOURCE_GROUP", resource_group),
            ("AZURE_SUBSCRIPTION_ID", subscription),
        ]

        for var_name, var_value in env_vars:
            result = run_command(
                ["azd", "env", "set", var_name, var_value, "-e", env_name],
                cwd=PROJECT_ROOT,
                capture=True,
            )
            if result.returncode != 0:
                print(f"  Warning: Failed to set {var_name}")

        # Create deployments directory for this environment
        env_dir = DEPLOYMENTS_DIR / env_name
        env_dir.mkdir(parents=True, exist_ok=True)

        save_env_status(env_name, status)
        summary["environments"][env_name] = status
        save_summary(summary)

        environments.append(env_name)
        print(f"  ✓ Ready for deployment")

    print(f"\n{'=' * 60}")
    print(f"PREPARATION COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Prepared: {len(environments)}")
    print(f"{'=' * 60}")

    if environments:
        print(f"\n📋 NEXT STEPS:")
        print(f"   Open {len(environments)} terminal window(s) and run:\n")
        for env_name in environments:
            print(f"   Terminal {environments.index(env_name) + 1}:")
            print(f"     cd {PROJECT_ROOT}")
            print(f"     azd up -e {env_name}")
            print()

        print(f"   After all deployments complete, generate .env files:")
        print(f"     uv run python scripts/scale_deploy.py generate-env --all")

    return 0


def cmd_generate_env(args: argparse.Namespace) -> int:
    """Generate .env files from deployed azd environments."""
    summary = load_summary()

    if not summary["environments"]:
        print("No environments found.")
        return 0

    if args.all:
        targets = list(summary["environments"].keys())
    elif args.env:
        if args.env not in summary["environments"]:
            print(f"Error: Environment '{args.env}' not found.")
            return 1
        targets = [args.env]
    else:
        print("Error: Specify --all or --env ENV_NAME")
        return 1

    print(f"\n{'=' * 60}")
    print(f"GENERATING .env FILES")
    print(f"{'=' * 60}\n")

    for env_name in targets:
        print(f"[{env_name}] Getting environment values...")

        result = run_command(
            ["azd", "env", "get-values", "-e", env_name],
            cwd=PROJECT_ROOT,
            capture=True,
        )

        if result.returncode != 0:
            print(f"  ✗ Failed (is the environment deployed?)")
            continue

        env_content = result.stdout

        # Add Neo4j settings from main .env if they exist
        main_env = PROJECT_ROOT / ".env"
        if main_env.exists():
            main_content = main_env.read_text()
            neo4j_lines = [
                line for line in main_content.splitlines()
                if line.startswith("NEO4J_") and "=" in line
            ]
            if neo4j_lines:
                env_content += "\n# Neo4j settings\n"
                env_content += "\n".join(neo4j_lines) + "\n"

        env_dir = DEPLOYMENTS_DIR / env_name
        env_dir.mkdir(parents=True, exist_ok=True)
        env_file = env_dir / ".env"
        env_file.write_text(env_content)

        # Update status
        status = load_env_status(env_name)
        status["status"] = "deployed"
        status["env_file"] = str(env_file)
        save_env_status(env_name, status)

        summary["environments"][env_name] = status
        save_summary(summary)

        print(f"  ✓ Created: {env_file}")

    print(f"\n{'=' * 60}")
    print(f"DONE")
    print(f"{'=' * 60}")
    print(f"\nRun tests: uv run python scripts/scale_deploy.py test --all")

    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Show deployment status."""
    summary = load_summary()

    if not summary["environments"]:
        print("No deployments found.")
        print("Run: uv run python scripts/scale_deploy.py prepare --count N --prefix PREFIX")
        return 0

    print(f"\n{'=' * 70}")
    print(f"DEPLOYMENT STATUS")
    print(f"{'=' * 70}")
    print(f"Created: {summary.get('created_at', 'N/A')}")
    print(f"Updated: {summary.get('updated_at', 'N/A')}")
    print(f"{'=' * 70}\n")

    print(f"{'Environment':<20} {'Status':<12} {'Resource Group':<25} {'Region'}")
    print("-" * 70)

    for env_name, env_status in sorted(summary["environments"].items()):
        status = env_status.get("status", "unknown")
        rg = env_status.get("resource_group", "N/A")
        region = env_status.get("region", "N/A")

        # Color-code status
        if status == "deployed":
            status_str = f"\033[92m{status}\033[0m"  # Green
        elif status == "failed":
            status_str = f"\033[91m{status}\033[0m"  # Red
        elif status == "prepared":
            status_str = f"\033[93m{status}\033[0m"  # Yellow
        else:
            status_str = status

        print(f"{env_name:<20} {status_str:<21} {rg:<25} {region}")

    # Summary counts
    deployed = sum(1 for e in summary["environments"].values() if e.get("status") == "deployed")
    prepared = sum(1 for e in summary["environments"].values() if e.get("status") == "prepared")
    failed = sum(1 for e in summary["environments"].values() if e.get("status") == "failed")

    print("-" * 70)
    print(f"Total: {len(summary['environments'])} | Deployed: {deployed} | Prepared: {prepared} | Failed: {failed}")

    if prepared > 0:
        print(f"\n💡 Tip: Run 'azd up -e ENV_NAME' for each prepared environment")

    return 0


def cmd_destroy(args: argparse.Namespace) -> int:
    """Destroy deployments."""
    summary = load_summary()

    if not summary["environments"]:
        print("No deployments found.")
        return 0

    if args.all:
        targets = list(summary["environments"].keys())
    elif args.env:
        if args.env not in summary["environments"]:
            print(f"Error: Environment '{args.env}' not found.")
            return 1
        targets = [args.env]
    else:
        print("Error: Specify --all or --env ENV_NAME")
        return 1

    print(f"\n{'=' * 60}")
    print(f"DESTROYING {len(targets)} ENVIRONMENT(S)")
    print(f"{'=' * 60}")

    if not args.yes:
        print(f"\nThis will delete the following resource groups:")
        for env_name in targets:
            rg = summary["environments"][env_name].get("resource_group", "N/A")
            print(f"  - {rg}")

        confirm = input("\nType 'yes' to confirm: ")
        if confirm.lower() != "yes":
            print("Aborted.")
            return 1

    for env_name in targets:
        env_status = summary["environments"][env_name]
        rg = env_status.get("resource_group")

        print(f"\nDestroying: {env_name}")

        if rg:
            delete_resource_group(rg)

        # Remove azd environment
        run_command(
            ["azd", "env", "delete", env_name, "--force", "--no-prompt"],
            cwd=PROJECT_ROOT,
            capture=True,
        )

        # Remove local files
        env_dir = DEPLOYMENTS_DIR / env_name
        if env_dir.exists():
            shutil.rmtree(env_dir)

        del summary["environments"][env_name]
        save_summary(summary)

        print(f"  ✓ Destroyed: {env_name}")

    print(f"\n{'=' * 60}")
    print(f"DESTRUCTION COMPLETE")
    print(f"{'=' * 60}")

    return 0


def cmd_test(args: argparse.Namespace) -> int:
    """Run tests on deployed environments."""
    summary = load_summary()

    if args.env:
        if args.env not in summary["environments"]:
            print(f"Error: Environment '{args.env}' not found.")
            return 1
        targets = [args.env]
    elif args.all:
        targets = [
            name for name, status in summary["environments"].items()
            if status.get("status") == "deployed"
        ]
    else:
        print("Error: Specify --all or --env ENV_NAME")
        return 1

    if not targets:
        print("No deployed environments to test.")
        print("Run 'generate-env --all' after deployments complete.")
        return 0

    print(f"\n{'=' * 60}")
    print(f"RUNNING TESTS ON {len(targets)} ENVIRONMENT(S)")
    print(f"{'=' * 60}")

    solution = args.solution or "12"  # Default to batch run
    main_env_file = PROJECT_ROOT / ".env"
    main_env_backup = PROJECT_ROOT / ".env.backup"

    for env_name in targets:
        env_dir = DEPLOYMENTS_DIR / env_name
        env_file = env_dir / ".env"

        if not env_file.exists():
            print(f"\n[{env_name}] Skipping - no .env file found")
            continue

        print(f"\n[{env_name}] Running solution {solution}...")

        # Backup main .env and swap with environment's .env
        if main_env_file.exists():
            shutil.copy(main_env_file, main_env_backup)

        shutil.copy(env_file, main_env_file)

        try:
            result = run_command(
                ["uv", "run", "python", "new-workshops/main.py", solution],
                cwd=PROJECT_ROOT,
            )

            if result.returncode == 0:
                print(f"[{env_name}] ✓ Tests completed successfully")
            else:
                print(f"[{env_name}] ✗ Tests failed")
        finally:
            # Restore original .env
            if main_env_backup.exists():
                shutil.copy(main_env_backup, main_env_file)
                main_env_backup.unlink()

    print(f"\n{'=' * 60}")
    print(f"TESTING COMPLETE")
    print(f"{'=' * 60}")
    print(f"\nRun token report: uv run python new-workshops/solutions/token_report.py")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Scale deployment script for Azure workshop environments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Prepare 5 environments (creates RGs and azd envs):
    uv run python scripts/scale_deploy.py prepare --count 5 --prefix workshop

  Then open 5 terminals and run:
    azd up -e workshop-01
    azd up -e workshop-02
    ... etc

  After all deployments complete, generate .env files:
    uv run python scripts/scale_deploy.py generate-env --all

  Check status:
    uv run python scripts/scale_deploy.py status

  Run tests on all environments:
    uv run python scripts/scale_deploy.py test --all

  Destroy all environments:
    uv run python scripts/scale_deploy.py destroy --all --yes
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Prepare command (replaces deploy)
    prepare_parser = subparsers.add_parser("prepare", help="Prepare environments (create RGs and azd envs)")
    prepare_parser.add_argument(
        "--count", "-n", type=int, required=True,
        help="Number of environments to prepare",
    )
    prepare_parser.add_argument(
        "--prefix", "-p", type=str, default="workshop",
        help="Prefix for environment names (default: workshop)",
    )
    prepare_parser.add_argument(
        "--region", "-r", type=str, default="eastus2",
        help=f"Azure region (default: eastus2). Supported: {', '.join(SUPPORTED_REGIONS)}",
    )
    prepare_parser.add_argument(
        "--subscription", "-s", type=str,
        help="Azure subscription ID (default: current subscription)",
    )
    prepare_parser.add_argument(
        "--skip-rg", action="store_true",
        help="Skip resource group creation (use existing)",
    )

    # Generate-env command
    gen_env_parser = subparsers.add_parser("generate-env", help="Generate .env files from deployed environments")
    gen_env_parser.add_argument(
        "--all", action="store_true",
        help="Generate for all environments",
    )
    gen_env_parser.add_argument(
        "--env", type=str,
        help="Generate for specific environment",
    )

    # Status command
    subparsers.add_parser("status", help="Show deployment status")

    # Destroy command
    destroy_parser = subparsers.add_parser("destroy", help="Destroy deployments")
    destroy_parser.add_argument(
        "--all", action="store_true",
        help="Destroy all environments",
    )
    destroy_parser.add_argument(
        "--env", type=str,
        help="Destroy specific environment",
    )
    destroy_parser.add_argument(
        "--yes", "-y", action="store_true",
        help="Skip confirmation prompt",
    )

    # Test command
    test_parser = subparsers.add_parser("test", help="Run tests on environments")
    test_parser.add_argument(
        "--all", action="store_true",
        help="Test all deployed environments",
    )
    test_parser.add_argument(
        "--env", type=str,
        help="Test specific environment",
    )
    test_parser.add_argument(
        "--solution", type=str,
        help="Solution number to run (default: 12 for batch)",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    if args.command == "prepare":
        return cmd_prepare(args)
    elif args.command == "generate-env":
        return cmd_generate_env(args)
    elif args.command == "status":
        return cmd_status(args)
    elif args.command == "destroy":
        return cmd_destroy(args)
    elif args.command == "test":
        return cmd_test(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
