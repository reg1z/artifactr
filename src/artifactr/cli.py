"""CLI interface for Artifactr.

This module provides the command-line interface using argparse.
Program logic is decoupled from CLI invocations to allow for future GUI development.
"""

import argparse
import sys
from typing import Any

from . import __version__
from .catalog import add_vaults, list_vaults, remove_vaults, select_default
from .importer import import_artifacts
from .tools import get_supported_tools


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="art",
        description="Manage AI project artifacts across repositories",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # import command
    import_parser = subparsers.add_parser(
        "import", help="Import artifacts into a git repo"
    )
    import_parser.add_argument("target", help="Path to target git repository")
    import_parser.add_argument(
        "--vault", help="Vault to import from (default: default vault)"
    )
    import_parser.add_argument(
        "--tools",
        help=f"Comma-separated list of tools to import ({', '.join(get_supported_tools())})",
    )

    # vault command with subcommands
    vault_parser = subparsers.add_parser("vault", help="Manage vaults")
    vault_subparsers = vault_parser.add_subparsers(dest="vault_command")

    # vault add
    vault_add = vault_subparsers.add_parser("add", help="Add vaults to catalog")
    vault_add.add_argument("paths", nargs="+", help="Vault paths to add")

    # vault rm
    vault_rm = vault_subparsers.add_parser("rm", help="Remove vaults from catalog")
    vault_rm.add_argument("paths", nargs="+", help="Vault paths to remove")

    # vault select
    vault_select = vault_subparsers.add_parser("select", help="Set default vault")
    vault_select.add_argument("path", help="Vault path to set as default")

    # vault list
    vault_subparsers.add_parser("list", help="List all vaults")

    return parser


def handle_import(args: argparse.Namespace) -> int:
    """Handle the import command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    # Parse tools if provided
    tools_list: list[str] | None = None
    if args.tools:
        tools_list = [t.strip() for t in args.tools.split(",")]

    # Perform import
    result = import_artifacts(target=args.target, vault=args.vault, tools=tools_list)

    if not result["success"]:
        for error in result["errors"]:
            print(error, file=sys.stderr)
        return 1

    # Print success summary
    print_import_summary(result)
    return 0


def print_import_summary(result: dict[str, Any]) -> None:
    """Print a summary of the import operation."""
    imported = result["imported"]
    skipped = result["skipped"]

    total_imported = 0
    for tool_name, counts in imported.items():
        tool_total = sum(counts.values())
        if tool_total > 0:
            print(f"\n{tool_name}:")
            for artifact_type, count in counts.items():
                if count > 0:
                    print(f"  {artifact_type}: {count}")
                    total_imported += count

    if total_imported == 0:
        print("No artifacts to import.")
    else:
        print(f"\nTotal: {total_imported} artifact(s) imported")

    if skipped > 0:
        print(f"Skipped: {skipped} file(s) (user declined overwrite)")


def handle_vault_add(args: argparse.Namespace) -> int:
    """Handle the vault add command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    result = add_vaults(args.paths)

    # Print results
    for path in result["added"]:
        print(f"Added vault: {path}")

    for path in result["skipped"]:
        print(f"Vault already registered: {path}")

    for error in result["errors"]:
        print(error, file=sys.stderr)

    # If the first vault was added, it becomes the default
    if result["added"]:
        info = list_vaults()
        if info["default"] and info["default"] in result["added"]:
            print(f"Set as default vault: {info['default']}")

    return 1 if result["errors"] else 0


def handle_vault_rm(args: argparse.Namespace) -> int:
    """Handle the vault rm command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success).
    """
    result = remove_vaults(args.paths)

    for path in result["removed"]:
        print(f"Removed vault: {path}")

    for path in result["not_found"]:
        print(f"Warning: Vault not in catalog: {path}", file=sys.stderr)

    return 0


def handle_vault_select(args: argparse.Namespace) -> int:
    """Handle the vault select command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    if select_default(args.path):
        print(f"Default vault set to: {args.path}")
        return 0
    else:
        print(f"Error: Vault not in catalog: {args.path}", file=sys.stderr)
        return 1


def handle_vault_list(args: argparse.Namespace) -> int:
    """Handle the vault list command.

    Args:
        args: Parsed command-line arguments (unused).

    Returns:
        Exit code (0 for success).
    """
    _ = args  # unused
    info = list_vaults()

    if not info["vaults"]:
        print("No vaults registered. Use 'art vault add <path>' to add a vault.")
        return 0

    print("Registered vaults:")
    for vault_path in info["vaults"]:
        if vault_path == info["default"]:
            print(f"  * {vault_path} (default)")
        else:
            print(f"    {vault_path}")

    return 0


def main() -> int:
    """Main entry point for the CLI.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "import":
        return handle_import(args)

    if args.command == "vault":
        if args.vault_command is None:
            # Print vault subcommand help
            parser.parse_args(["vault", "--help"])
            return 0

        if args.vault_command == "add":
            return handle_vault_add(args)
        if args.vault_command == "rm":
            return handle_vault_rm(args)
        if args.vault_command == "select":
            return handle_vault_select(args)
        if args.vault_command == "list":
            return handle_vault_list(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
