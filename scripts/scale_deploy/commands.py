"""
CLI command handlers for scale deployment operations.
"""

import argparse
import shutil
from datetime import datetime

from .azure import (
    check_azure_auth,
    create_azd_environment,
    create_resource_group,
    delete_azd_environment,
    delete_resource_group,
    get_azd_env_values,
    get_subscription_id,
    purge_soft_deleted_cognitive_services,
    set_azd_env_var,
)
from .config import DEFAULT_REGION, DEPLOYMENTS_DIR, PROJECT_ROOT
from .state import (
    get_env_file_path,
    load_env_status,
    load_summary,
    save_env_status,
    save_summary,
)
from .testing import (
    merge_token_usage_files,
    print_test_summary,
    run_parallel_tests,
)


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

        # Create azd environment
        print(f"  Creating azd environment: {env_name}")
        success, message = create_azd_environment(env_name)

        if not success:
            print(f"  Error: {message}")
            status["status"] = "failed"
            status["error"] = "Failed to create azd environment"
            save_env_status(env_name, status)
            summary["environments"][env_name] = status
            save_summary(summary)
            continue

        if message == "already_exists":
            print("  (environment already exists, reusing)")
        else:
            print("  (created new environment)")

        # Set environment variables
        print("  Setting azd environment variables")
        env_vars = [
            ("AZURE_LOCATION", region),
            ("AZURE_RESOURCE_GROUP", resource_group),
            ("AZURE_SUBSCRIPTION_ID", subscription),
        ]

        for var_name, var_value in env_vars:
            if not set_azd_env_var(env_name, var_name, var_value):
                print(f"  Warning: Failed to set {var_name}")

        # Create deployments directory for this environment
        env_dir = DEPLOYMENTS_DIR / env_name
        env_dir.mkdir(parents=True, exist_ok=True)

        save_env_status(env_name, status)
        summary["environments"][env_name] = status
        save_summary(summary)

        environments.append(env_name)
        print("  ✓ Ready for deployment")

    print(f"\n{'=' * 60}")
    print("PREPARATION COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Prepared: {len(environments)}")
    print(f"{'=' * 60}")

    if environments:
        print("\n📋 NEXT STEPS:")
        print(f"   Open {len(environments)} terminal window(s) and run:\n")
        for idx, env_name in enumerate(environments):
            print(f"   Terminal {idx + 1}:")
            print(f"     cd {PROJECT_ROOT}")
            print(f"     azd up -e {env_name}")
            print()

        print("   After all deployments complete, generate .env files:")
        print("     uv run python scripts/scale_deploy.py generate-env --all")

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
    print("GENERATING .env FILES")
    print(f"{'=' * 60}\n")

    for env_name in targets:
        print(f"[{env_name}] Getting environment values...")

        env_content = get_azd_env_values(env_name)
        if env_content is None:
            print("  ✗ Failed (is the environment deployed?)")
            continue

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
    print("DONE")
    print(f"{'=' * 60}")
    print("\nRun tests: uv run python scripts/scale_deploy.py test --all")

    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Show deployment status."""
    summary = load_summary()

    if not summary["environments"]:
        print("No deployments found.")
        print("Run: uv run python scripts/scale_deploy.py prepare --count N --prefix PREFIX")
        return 0

    print(f"\n{'=' * 70}")
    print("DEPLOYMENT STATUS")
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
        print("\n💡 Tip: Run 'azd up -e ENV_NAME' for each prepared environment")

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
        print("\nThis will delete the following resource groups:")
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
        delete_azd_environment(env_name)

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
    print("DESTRUCTION COMPLETE")
    print(f"{'=' * 60}")

    return 0


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
        env_file = get_env_file_path(env_name)
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

    results = run_parallel_tests(test_jobs, solution, max_workers)
    print_test_summary(results)

    # Merge per-environment token usage files
    merge_token_usage_files()

    print(f"\n{'=' * 60}")
    print("Run token report: uv run python new-workshops/solutions/token_report.py")

    failed = sum(1 for r in results if not r.success)
    return 0 if failed == 0 else 1
