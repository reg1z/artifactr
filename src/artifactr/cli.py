"""CLI interface for Artifactr.

This module provides the command-line interface using argparse.
Program logic is decoupled from CLI invocations to allow for future GUI development.
"""

import argparse
import sys
from typing import Any

from . import __version__
from .catalog import (
    add_vaults,
    get_default_tool,
    get_default_vault,
    get_vault_by_name_or_path,
    get_vault_hierarchy,
    list_tools_info,
    list_vaults,
    name_vault,
    remove_vaults,
    select_default,
    select_default_tool,
)
from .importer import copy_with_prompt, import_artifacts, import_artifacts_global
from .scanner import discover_artifacts, extract_description, load_import_cache
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
    import_parser.add_argument(
        "target", nargs="?", default=None, help="Path to target git repository"
    )
    import_parser.add_argument(
        "--vault", help="Vault to import from (default: default vault)"
    )
    import_parser.add_argument(
        "--tools",
        help=f"Comma-separated list of tools to import ({', '.join(get_supported_tools())})",
    )
    import_parser.add_argument(
        "--link",
        "-l",
        action="store_true",
        help="Symlink vault contents instead of copying",
    )
    import_parser.add_argument(
        "--artifacts",
        help="Comma-separated list of artifact names to import",
    )
    import_parser.add_argument(
        "--global",
        "-g",
        action="store_true",
        dest="global_import",
        help="Import into global config directories instead of a local repo",
    )
    import_parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite existing files without prompting",
    )

    # vault command with subcommands
    vault_parser = subparsers.add_parser("vault", help="Manage vaults")
    vault_subparsers = vault_parser.add_subparsers(dest="vault_command")

    # vault add
    vault_add = vault_subparsers.add_parser("add", help="Add vaults to catalog")
    vault_add.add_argument("paths", nargs="+", help="Vault paths to add")
    vault_add.add_argument(
        "--name", help="Name for the vault (only when adding a single vault)"
    )

    # vault rm
    vault_rm = vault_subparsers.add_parser("rm", help="Remove vaults from catalog")
    vault_rm.add_argument("paths", nargs="+", help="Vault paths to remove")

    # vault name
    vault_name = vault_subparsers.add_parser("name", help="Set or change a vault's name")
    vault_name.add_argument("vault", help="Vault name or path to rename")
    vault_name.add_argument("name", help="New name for the vault")

    # vault select
    vault_select = vault_subparsers.add_parser("select", help="Set default vault")
    vault_select.add_argument("path", help="Vault name or path to set as default")

    # vault list
    vault_list = vault_subparsers.add_parser("list", help="List all vaults")
    vault_list.add_argument(
        "-a", "--all", action="store_true", dest="show_all",
        help="Show full vault hierarchy with artifacts",
    )

    # tool command with subcommands
    tool_parser = subparsers.add_parser("tool", help="Manage tool selection")
    tool_subparsers = tool_parser.add_subparsers(dest="tool_command")

    # tool select
    tool_select = tool_subparsers.add_parser("select", help="Set default tool")
    tool_select.add_argument(
        "name", help=f"Tool name ({', '.join(get_supported_tools())})"
    )

    # tool list
    tool_subparsers.add_parser("list", help="List supported tools")

    # spelunk command
    spelunk_parser = subparsers.add_parser(
        "spelunk", help="Discover artifacts in a target directory"
    )
    spelunk_parser.add_argument("target", help="Path to directory to probe")

    # store command
    store_parser = subparsers.add_parser(
        "store", help="Store artifacts from a directory into a vault"
    )
    store_parser.add_argument("target_dir", help="Path to directory containing artifacts")
    store_parser.add_argument(
        "--vault", help="Vault to store into (default: default vault)"
    )

    return parser


def handle_import(args: argparse.Namespace) -> int:
    """Handle the import command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    global_import = getattr(args, "global_import", False)
    force = getattr(args, "force", False)

    # Validate: need either --global or a target
    if not global_import and args.target is None:
        print(
            "Error: A target repository is required unless --global is used.\n"
            "Usage: art import <target> or art import --global",
            file=sys.stderr,
        )
        return 1

    # Parse tools if provided, otherwise use default tool
    tools_list: list[str]
    if args.tools:
        tools_list = [t.strip() for t in args.tools.split(",")]
    else:
        tools_list = [get_default_tool()]

    # Parse artifacts if provided
    artifacts_list = None
    if getattr(args, "artifacts", None):
        artifacts_list = [a.strip() for a in args.artifacts.split(",")]

    if global_import:
        result = import_artifacts_global(
            vault=args.vault,
            tools=tools_list,
            link=args.link,
            artifacts=artifacts_list,
            force=force,
        )
    else:
        result = import_artifacts(
            target=args.target,
            vault=args.vault,
            tools=tools_list,
            link=args.link,
            artifacts=artifacts_list,
            force=force,
        )

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
    name = getattr(args, "name", None)
    if name and len(args.paths) > 1:
        print("Error: --name can only be used when adding a single vault.", file=sys.stderr)
        return 1

    result = add_vaults(args.paths, name=name)

    # Print results
    for path in result["added"]:
        vault_label = f"{name} ({path})" if name and path == result["added"][0] else path
        print(f"Added vault: {vault_label}")

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
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success).
    """
    info = list_vaults()

    if not info["vaults"]:
        print("No vaults registered. Use 'art vault add <path>' to add a vault.")
        return 0

    vault_names = info["vault_names"]
    show_all = getattr(args, "show_all", False)

    print("Registered vaults:")
    for vault_path in info["vaults"]:
        name = vault_names.get(vault_path)
        default_marker = " (default)" if vault_path == info["default"] else ""
        prefix = "  * " if vault_path == info["default"] else "    "

        if name:
            vault_label = f"{name} ({vault_path})"
        else:
            vault_label = vault_path

        if show_all:
            hierarchy = get_vault_hierarchy(vault_path)
            if hierarchy is None:
                print(f"{prefix}{vault_label} (path not found){default_marker}")
            else:
                print(f"{prefix}{vault_label}{default_marker}")
                for art_type, items in hierarchy.items():
                    if not items:
                        continue
                    print(f"      {art_type}/")
                    for item_name in items:
                        if art_type == "skills":
                            print(f"        {item_name}/")
                        else:
                            print(f"        {item_name}")
        else:
            print(f"{prefix}{vault_label}{default_marker}")

    return 0


def handle_vault_name(args: argparse.Namespace) -> int:
    """Handle the vault name command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    result = name_vault(args.vault, args.name)

    if result["success"]:
        print(f"Vault '{result['vault_path']}' named: {args.name}")
        return 0
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 1


def handle_tool_select(args: argparse.Namespace) -> int:
    """Handle the tool select command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    supported_tools = get_supported_tools()
    if select_default_tool(args.name, supported_tools):
        print(f"Default tool set to: {args.name}")
        return 0
    else:
        print(
            f"Error: Unsupported tool: {args.name}. "
            f"Supported tools: {', '.join(supported_tools)}",
            file=sys.stderr,
        )
        return 1


def handle_tool_list(args: argparse.Namespace) -> int:
    """Handle the tool list command.

    Args:
        args: Parsed command-line arguments (unused).

    Returns:
        Exit code (0 for success).
    """
    _ = args  # unused
    supported_tools = get_supported_tools()
    info = list_tools_info(supported_tools)

    print("Supported tools:")
    for tool_name in info["tools"]:
        if tool_name == info["default"]:
            print(f"  * {tool_name} (default)")
        else:
            print(f"    {tool_name}")

    return 0


def parse_selection(selection: str, max_val: int) -> list[int]:
    """Parse a user selection string into a list of 0-based indices.

    Supports: individual numbers, comma-separated, ranges, "all", and combinations.

    Args:
        selection: User input string (e.g., "1,3-5,7" or "all").
        max_val: Maximum valid value (1-based).

    Returns:
        Sorted list of unique 0-based indices.
    """
    selection = selection.strip().lower()
    if selection == "all":
        return list(range(max_val))

    indices = set()
    for part in selection.split(","):
        part = part.strip()
        if "-" in part:
            start_str, end_str = part.split("-", 1)
            try:
                start = int(start_str.strip())
                end = int(end_str.strip())
                for i in range(start, end + 1):
                    if 1 <= i <= max_val:
                        indices.add(i - 1)
            except ValueError:
                continue
        else:
            try:
                val = int(part)
                if 1 <= val <= max_val:
                    indices.add(val - 1)
            except ValueError:
                continue

    return sorted(indices)


def handle_spelunk(args: argparse.Namespace) -> int:
    """Handle the spelunk command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    from pathlib import Path

    target = Path(args.target).resolve()

    if not target.exists() or not target.is_dir():
        print(f"Error: Target directory does not exist: {args.target}", file=sys.stderr)
        return 1

    artifacts = discover_artifacts(target)

    if not artifacts:
        print(f"No artifacts found in {args.target}")
        return 0

    # Load import cache
    import_cache = load_import_cache(target)

    # Build table rows
    rows = []
    for art in artifacts:
        name_col = art["name"]

        # Check import cache
        if art["name"] in import_cache:
            vault_names = ", ".join(import_cache[art["name"]])
            name_col += f" (imported: {vault_names})"

        description = extract_description(art)
        tool_label = art["config_dir"].lstrip(".")
        rows.append((name_col, art["type"], tool_label, description))

    # Calculate column widths
    headers = ("NAME", "TYPE", "TOOL", "DESCRIPTION")
    widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(val))

    # Print table
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    for row in rows:
        print(fmt.format(*row))

    return 0


def handle_store(args: argparse.Namespace) -> int:
    """Handle the store command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    from pathlib import Path

    target = Path(args.target_dir).resolve()

    if not target.exists() or not target.is_dir():
        print(f"Error: Target directory does not exist: {args.target_dir}", file=sys.stderr)
        return 1

    # Resolve vault
    vault_identifier = getattr(args, "vault", None)
    if vault_identifier:
        vault_path_str = get_vault_by_name_or_path(vault_identifier)
        if vault_path_str is None:
            print(f"Error: Vault not in catalog: {vault_identifier}", file=sys.stderr)
            return 1
    else:
        vault_path_str = get_default_vault()
        if vault_path_str is None:
            print("Error: No default vault set. Use 'art vault add' to add a vault.", file=sys.stderr)
            return 1

    vault_path = Path(vault_path_str)

    # Get vault display name
    vault_info = list_vaults()
    vault_display_name = vault_info["vault_names"].get(vault_path_str, vault_path.name)

    # Discover artifacts
    artifacts = discover_artifacts(target)

    if not artifacts:
        print(f"No artifacts found in {args.target_dir}")
        return 0

    # Display numbered list
    print(f"Discovered artifacts in {target}:")
    for i, art in enumerate(artifacts, 1):
        rel_path = art["path"].relative_to(target)
        print(f"  {i}. {art['name']} ({art['type']}) - {rel_path}")

    # Prompt for selection
    try:
        selection = input(f"\nSelect artifacts to store [1-{len(artifacts)}, all]: ")
    except EOFError:
        return 0

    indices = parse_selection(selection, len(artifacts))
    if not indices:
        return 0

    stored_count = 0
    for idx in indices:
        art = artifacts[idx]
        dest = vault_path / art["type_plural"] / (art["path"].name if art["type"] == "skill" else art["path"].name)
        result = copy_with_prompt(art["path"], dest)
        if result["copied"] > 0:
            print(f"Stored: {art['name']} ({art['type']}) -> {dest}")
            stored_count += 1

    print(f"\n{stored_count} artifact(s) stored to vault: {vault_display_name}")
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
        if args.vault_command == "name":
            return handle_vault_name(args)
        if args.vault_command == "select":
            return handle_vault_select(args)
        if args.vault_command == "list":
            return handle_vault_list(args)

    if args.command == "tool":
        if args.tool_command is None:
            # Print tool subcommand help
            parser.parse_args(["tool", "--help"])
            return 0

        if args.tool_command == "select":
            return handle_tool_select(args)
        if args.tool_command == "list":
            return handle_tool_list(args)

    if args.command == "spelunk":
        return handle_spelunk(args)

    if args.command == "store":
        return handle_store(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
