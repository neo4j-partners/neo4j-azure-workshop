#!/usr/bin/env python3
"""
Scale Deployment Script

Manages multiple Azure workshop environments for scale testing.
Creates resource groups and azd environments, then you run `azd up` manually
in separate terminal windows.

Usage:
    uv run python scripts/scale_deploy.py prepare --count 3 --prefix workshop
    uv run python scripts/scale_deploy.py status
    uv run python scripts/scale_deploy.py generate-env --all
    uv run python scripts/scale_deploy.py test --all
    uv run python scripts/scale_deploy.py destroy --all
"""

import argparse
import sys

from scale_deploy.commands import (
    cmd_destroy,
    cmd_generate_env,
    cmd_prepare,
    cmd_status,
    cmd_test,
)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser with all subcommands."""
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

    # Prepare command
    prepare_parser = subparsers.add_parser(
        "prepare",
        help="Prepare environments (create RGs and azd envs)",
    )
    prepare_parser.add_argument(
        "--count", "-n",
        type=int,
        required=True,
        help="Number of environments to prepare",
    )
    prepare_parser.add_argument(
        "--prefix", "-p",
        type=str,
        default="workshop",
        help="Prefix for environment names (default: workshop)",
    )
    prepare_parser.add_argument(
        "--subscription", "-s",
        type=str,
        help="Azure subscription ID (default: current subscription)",
    )

    # Generate-env command
    gen_env_parser = subparsers.add_parser(
        "generate-env",
        help="Generate .env files from deployed environments",
    )
    gen_env_parser.add_argument(
        "--all",
        action="store_true",
        help="Generate for all environments",
    )
    gen_env_parser.add_argument(
        "--env",
        type=str,
        help="Generate for specific environment",
    )

    # Status command
    subparsers.add_parser("status", help="Show deployment status")

    # Destroy command
    destroy_parser = subparsers.add_parser("destroy", help="Destroy deployments")
    destroy_parser.add_argument(
        "--all",
        action="store_true",
        help="Destroy all environments",
    )
    destroy_parser.add_argument(
        "--env",
        type=str,
        help="Destroy specific environment",
    )
    destroy_parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompt",
    )

    # Test command
    test_parser = subparsers.add_parser("test", help="Run tests on environments")
    test_parser.add_argument(
        "--all",
        action="store_true",
        help="Test all deployed environments",
    )
    test_parser.add_argument(
        "--env",
        type=str,
        help="Test specific environment",
    )
    test_parser.add_argument(
        "--solution",
        type=str,
        help="Solution number to run (default: 12 for batch)",
    )
    test_parser.add_argument(
        "--parallel", "-p",
        type=int,
        default=None,
        help="Max parallel tests (default: all at once)",
    )

    return parser


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    commands = {
        "prepare": cmd_prepare,
        "generate-env": cmd_generate_env,
        "status": cmd_status,
        "destroy": cmd_destroy,
        "test": cmd_test,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
