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
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Optional

# Default Azure region for Microsoft Foundry
DEFAULT_REGION = "eastus2"

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

    region = DEFAULT_REGION
    subscription = args.subscription or get_subscription_id()
    if not subscription:
        print("Error: Could not determine Azure subscription.")
        return 1

    print(f"\n{'=' * 60}")
    print(f"PREPARING {args.count} ENVIRONMENT(S)")
    print(f"{'=' * 60}")
    print(f"  Prefix:       {args.prefix}")
    print(f"  Region:       {region}")
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
            "region": region,
            "subscription": subscription,
            "status": "prepared",
            "created_at": datetime.now().isoformat(),
        }

        # Create resource group
        print(f"  Creating resource group: {resource_group}")
        if not create_resource_group(resource_group, region):
            status["status"] = "failed"
            status["error"] = "Failed to create resource group"
            save_env_status(env_name, status)
            summary["environments"][env_name] = status
            save_summary(summary)
            continue

        # Purge any soft-deleted Cognitive Services
        purge_soft_deleted_cognitive_services(resource_group, region)

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
            ("AZURE_LOCATION", region),
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
        region = env_status.get("region", "eastus2")

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

        # Purge soft-deleted Cognitive Services for this resource group
        if rg:
            purge_soft_deleted_cognitive_services(rg, region)

        del summary["environments"][env_name]
        save_summary(summary)

        print(f"  ✓ Destroyed: {env_name}")

    print(f"\n{'=' * 60}")
    print(f"DESTRUCTION COMPLETE")
    print(f"{'=' * 60}")

    return 0


def parse_env_file(env_file: Path) -> dict:
    """Parse a .env file and return as dict merged with current environment."""
    env_vars = os.environ.copy()
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            # Remove quotes if present
            value = value.strip().strip('"').strip("'")
            env_vars[key.strip()] = value
    return env_vars


def run_single_test(
    env_name: str, env_file: Path, solution: str, log_dir: Path
) -> tuple[str, bool, float, str, list[str]]:
    """
    Run test for a single environment.

    Returns: (env_name, success, duration_seconds, output, solutions_run)
    """
    env_vars = parse_env_file(env_file)
    # Set TOKEN_USAGE_ENV so each process writes to its own file
    env_vars["TOKEN_USAGE_ENV"] = env_name
    start_time = time.time()

    # Create log file for this environment
    log_file = log_dir / f"{env_name}.log"

    with open(log_file, "w") as f:
        f.write(f"=== {env_name} started at {datetime.now().isoformat()} ===\n")
        f.write(f"Solution: {solution}\n")
        f.write(f"{'=' * 60}\n\n")
        f.flush()

        # Use PYTHONUNBUFFERED to get real-time output
        env_vars["PYTHONUNBUFFERED"] = "1"

        result = subprocess.run(
            ["uv", "run", "python", "new-workshops/main.py", solution],
            cwd=PROJECT_ROOT,
            env=env_vars,
            stdout=f,
            stderr=subprocess.STDOUT,
            text=True,
        )

    duration = time.time() - start_time

    # Read the log file for output
    output = log_file.read_text()

    # Append completion status
    with open(log_file, "a") as f:
        f.write(f"\n{'=' * 60}\n")
        status = "SUCCESS" if result.returncode == 0 else "FAILED"
        f.write(f"=== {env_name} {status} in {duration:.1f}s ===\n")

    # Extract which solutions were run from output
    solutions_run = []
    for line in output.splitlines():
        if line.startswith(">>> Running:"):
            sol_name = line.replace(">>> Running:", "").strip()
            solutions_run.append(sol_name)

    return (env_name, result.returncode == 0, duration, output, solutions_run)


def merge_token_usage_files() -> None:
    """Merge per-environment token usage files into the main token_usage.json."""
    token_usage_dir = PROJECT_ROOT / "new-workshops" / "solutions" / "token_usage"
    token_usage_file = PROJECT_ROOT / "new-workshops" / "solutions" / "token_usage.json"

    if not token_usage_dir.exists():
        return

    # Load existing main file or create empty structure
    if token_usage_file.exists():
        try:
            merged = json.loads(token_usage_file.read_text())
        except (json.JSONDecodeError, OSError):
            merged = {"sessions": [], "totals": {"llm_input": 0, "llm_output": 0, "embedding": 0}}
    else:
        merged = {"sessions": [], "totals": {"llm_input": 0, "llm_output": 0, "embedding": 0}}

    # Merge each environment file
    env_files = list(token_usage_dir.glob("*.json"))
    if not env_files:
        return

    print(f"\nMerging token usage from {len(env_files)} environment(s)...")

    for env_file in env_files:
        try:
            env_data = json.loads(env_file.read_text())
            # Add environment name to each session
            env_name = env_file.stem
            for session in env_data.get("sessions", []):
                session["environment"] = env_name
                merged["sessions"].append(session)
            # Add totals
            env_totals = env_data.get("totals", {})
            merged["totals"]["llm_input"] += env_totals.get("llm_input", 0)
            merged["totals"]["llm_output"] += env_totals.get("llm_output", 0)
            merged["totals"]["embedding"] += env_totals.get("embedding", 0)
            # Remove the per-environment file after merging
            env_file.unlink()
        except (json.JSONDecodeError, OSError) as e:
            print(f"  Warning: Could not merge {env_file.name}: {e}")

    # Save merged file
    token_usage_file.write_text(json.dumps(merged, indent=2))

    # Remove directory if empty
    try:
        token_usage_dir.rmdir()
    except OSError:
        pass  # Directory not empty, that's fine

    print(f"  Merged into: {token_usage_file}")


def cmd_test(args: argparse.Namespace) -> int:
    """Run tests on deployed environments (parallel by default)."""
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

    solution = args.solution or "12"  # Default to batch run
    max_workers = args.parallel if args.parallel else len(targets)

    # Filter to only environments with .env files
    test_jobs = []
    for env_name in targets:
        env_file = DEPLOYMENTS_DIR / env_name / ".env"
        if env_file.exists():
            test_jobs.append((env_name, env_file))
        else:
            print(f"[{env_name}] Skipping - no .env file found")

    if not test_jobs:
        print("No environments with .env files to test.")
        return 0

    parallel_str = "parallel" if len(test_jobs) > 1 else "sequential"
    print(f"\n{'=' * 60}")
    print(f"RUNNING TESTS ON {len(test_jobs)} ENVIRONMENT(S) ({parallel_str})")
    print(f"{'=' * 60}")
    print(f"Solution: {solution} | Max parallel: {max_workers}")
    print(f"{'=' * 60}\n")

    # Create log directory
    log_dir = DEPLOYMENTS_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Clean old logs
    for old_log in log_dir.glob("*.log"):
        old_log.unlink()

    print(f"Logs: {log_dir}/")
    print(f"  Monitor progress: tail -f {log_dir}/*.log")
    print(f"  Or watch one:     tail -f {log_dir}/workshop-01.log\n")

    results: list[tuple[str, bool, float, str, list[str]]] = []
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(run_single_test, env_name, env_file, solution, log_dir): env_name
            for env_name, env_file in test_jobs
        }

        # Track which environments are still running
        running = set(env_name for env_name, _ in test_jobs)
        completed = 0

        for future in as_completed(futures):
            completed += 1
            env_name = futures[future]
            running.discard(env_name)
            try:
                result = future.result()
                results.append(result)
                status = "✓" if result[1] else "✗"
                color = "\033[92m" if result[1] else "\033[91m"
                reset = "\033[0m"
                solutions_str = f" [{len(result[4])} solutions]" if result[4] else ""
                elapsed = time.time() - start_time
                print(f"  {color}{status}{reset} [{completed}/{len(test_jobs)}] {env_name} ({result[2]:.1f}s){solutions_str} [elapsed: {elapsed:.0f}s]")
                if running and len(running) <= 5:
                    print(f"      Still running: {', '.join(sorted(running))}")
            except Exception as e:
                results.append((env_name, False, 0.0, str(e), []))
                print(f"  \033[91m✗\033[0m [{completed}/{len(test_jobs)}] {env_name} error: {e}")

    total_time = time.time() - start_time

    # Sort results by environment name for consistent display
    results.sort(key=lambda x: x[0])

    # Summary
    passed = sum(1 for r in results if r[1])
    failed = len(results) - passed

    print(f"\n{'=' * 60}")
    print(f"RESULTS")
    print(f"{'=' * 60}")

    for env_name, success, duration, output, solutions_run in results:
        status = "✓" if success else "✗"
        color = "\033[92m" if success else "\033[91m"
        reset = "\033[0m"
        solutions_count = f"[{len(solutions_run)} solutions]" if solutions_run else ""
        print(f"  {color}{status}{reset} {env_name:<20} ({duration:.1f}s) {solutions_count}")

    # Show which solutions were run (from first successful result)
    all_solutions = set()
    for r in results:
        all_solutions.update(r[4])
    if all_solutions:
        print(f"\nSolutions tested: {', '.join(sorted(all_solutions))}")

    print(f"\n{'-' * 60}")
    print(f"PASSED: {passed} | FAILED: {failed} | Total time: {total_time:.1f}s")

    # Show failure details
    failures = [r for r in results if not r[1]]
    if failures:
        for env_name, _, _, output, solutions_run in failures:
            print(f"\n{'=' * 60}")
            print(f"FAILURE DETAILS: {env_name}")
            if solutions_run:
                print(f"Solutions completed before failure: {', '.join(solutions_run)}")
            print(f"{'=' * 60}")
            # Show last 30 lines of output
            lines = output.strip().split("\n")
            if len(lines) > 30:
                print("... (truncated)")
                lines = lines[-30:]
            for line in lines:
                print(f"  {line}")

    # Merge per-environment token usage files
    merge_token_usage_files()

    print(f"\n{'=' * 60}")
    print(f"Run token report: uv run python new-workshops/solutions/token_report.py")

    return 0 if failed == 0 else 1


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
        "--subscription", "-s", type=str,
        help="Azure subscription ID (default: current subscription)",
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
    test_parser.add_argument(
        "--parallel", "-p", type=int, default=None,
        help="Max parallel tests (default: all at once)",
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
