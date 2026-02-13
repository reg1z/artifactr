"""CLI interface for Artifactr.

This module provides the command-line interface using argparse.
Program logic is decoupled from CLI invocations to allow for future GUI development.
"""

import argparse
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .catalog import (
    add_vaults,
    get_default_tool,
    get_default_vault,
    get_vault_by_name_or_path,
    get_vault_hierarchy,
    init_vault,
    list_tools_info,
    list_vaults,
    name_vault,
    remove_vaults,
    select_default,
    select_default_tool,
)
from .config import (
    load_active_vault_tools,
    load_all_vault_tools,
    load_cwd_vault_tools,
    load_global_tools,
    load_vault_metadata,
    save_global_tools,
    save_vault_metadata,
)
from .creator import create_artifact, create_skill, resolve_edit_target, resolve_project_target, resolve_vault_target
from .importer import copy_with_prompt, import_artifacts, import_artifacts_global
from .scanner import discover_artifacts, extract_description, load_import_cache
from .tools import (
    BUILTIN_TOOLS,
    get_aliases_for_tool,
    get_supported_tools,
    get_tool,
    get_tool_source,
    resolve_tool_name,
)


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
        help="Comma-separated list of tools to import",
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
    vault_add.add_argument(
        "--set-default", action="store_true",
        help="Set the added vault as the default",
    )

    # vault init
    vault_init = vault_subparsers.add_parser(
        "init", help="Initialize a new vault directory"
    )
    vault_init.add_argument("target_dir", help="Path to the vault directory")
    vault_init.add_argument(
        "--name", help="Name for the vault",
    )
    vault_init.add_argument(
        "--set-default", action="store_true",
        help="Set the initialized vault as the default",
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
    tool_parser = subparsers.add_parser("tool", help="Manage tools")
    tool_subparsers = tool_parser.add_subparsers(dest="tool_command")

    # tool select
    tool_select = tool_subparsers.add_parser("select", help="Set default tool")
    tool_select.add_argument("name", help="Tool name")

    # tool list
    tool_list = tool_subparsers.add_parser("list", help="List supported tools")
    tool_list.add_argument("--vault", help="Use tools from this vault instead of the default vault")

    # tool add
    tool_add = tool_subparsers.add_parser("add", help="Add a custom tool definition")
    tool_add.add_argument("name", help="Tool identifier")
    tool_add.add_argument("--skills", help="Repo-relative path for skills")
    tool_add.add_argument("--commands", help="Repo-relative path for commands")
    tool_add.add_argument("--agents", help="Repo-relative path for agents")
    tool_add.add_argument("--global-skills", help="Absolute path for global skills")
    tool_add.add_argument("--global-commands", help="Absolute path for global commands")
    tool_add.add_argument("--global-agents", help="Absolute path for global agents")
    tool_add.add_argument(
        "--alias", action="append", default=[], dest="aliases",
        help="Tool alias (repeatable)",
    )
    tool_add.add_argument("--vault", help="Store in vault's metadata instead of global config")
    tool_add.add_argument(
        "-g", "--global", action="store_true", dest="global_config",
        help="Explicitly store in global config (default behavior)",
    )

    # tool rm
    tool_rm = tool_subparsers.add_parser("rm", help="Remove a custom tool definition")
    tool_rm.add_argument("name", help="Tool identifier to remove")
    tool_rm.add_argument("--vault", help="Remove from vault's metadata instead of global config")
    tool_rm.add_argument(
        "-g", "--global", action="store_true", dest="global_config",
        help="Explicitly remove from global config (default behavior)",
    )

    # tool info
    tool_info = tool_subparsers.add_parser("info", help="Show tool information and catalog")
    tool_info.add_argument("name", nargs="?", help="Tool identifier to display (omit for catalog view)")
    tool_info.add_argument(
        "--vault", nargs="?", const=True, default=None,
        help="Filter to vault tools (no value = default vault, with value = specific vault)",
    )
    tool_info.add_argument(
        "-g", "--global", action="store_true", dest="global_filter",
        help="Filter to global config tools only",
    )

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

    # edit command
    edit_parser = subparsers.add_parser("edit", help="Edit an artifact in your editor")
    edit_parser.add_argument(
        "artifact_type", choices=["skill", "agent", "command"],
        help="Type of artifact to edit",
    )
    edit_parser.add_argument(
        "artifact_name", help="Name of the artifact to edit",
    )
    edit_parser.add_argument(
        "--vault", help="Target vault (name or path)",
    )
    edit_parser.add_argument(
        "-H", "--here", action="store_true",
        help="Edit in current project instead of vault",
    )
    edit_parser.add_argument(
        "--tools",
        help="Comma-separated tool list (used with --here)",
    )

    # create command with subcommands
    create_parser = subparsers.add_parser("create", help="Create new artifacts")
    create_subparsers = create_parser.add_subparsers(dest="create_command")

    # create skill
    create_skill_parser = create_subparsers.add_parser(
        "skill", help="Create a new skill"
    )
    create_skill_parser.add_argument(
        "skill_name", help="Skill identifier (directory name)"
    )
    create_skill_parser.add_argument(
        "-n", "--name", dest="display_name",
        help="Override the frontmatter display name",
    )
    create_skill_parser.add_argument(
        "-d", "--description", help="Skill description",
    )
    create_skill_parser.add_argument(
        "-c", "--content", help="Markdown body content",
    )
    create_skill_parser.add_argument(
        "-D", "--field", action="append", default=[],
        help="Additional frontmatter field as key=value (repeatable)",
    )
    create_skill_parser.add_argument(
        "-H", "--here", action="store_true",
        help="Create in current project instead of vault",
    )
    create_skill_parser.add_argument(
        "--vault", help="Target vault (name or path)",
    )
    create_skill_parser.add_argument(
        "--tools",
        help="Comma-separated tool list (used with --here)",
    )

    # create command
    create_command_parser = create_subparsers.add_parser(
        "command", help="Create a new command"
    )
    create_command_parser.add_argument(
        "command_name", help="Command identifier (filename)"
    )
    create_command_parser.add_argument(
        "-d", "--description", help="Command description",
    )
    create_command_parser.add_argument(
        "-c", "--content", help="Markdown body content",
    )
    create_command_parser.add_argument(
        "-D", "--field", action="append", default=[],
        help="Additional frontmatter field as key=value (repeatable)",
    )
    create_command_parser.add_argument(
        "-H", "--here", action="store_true",
        help="Create in current project instead of vault",
    )
    create_command_parser.add_argument(
        "--vault", help="Target vault (name or path)",
    )
    create_command_parser.add_argument(
        "--tools",
        help="Comma-separated tool list (used with --here)",
    )

    # create agent
    create_agent_parser = create_subparsers.add_parser(
        "agent", help="Create a new agent"
    )
    create_agent_parser.add_argument(
        "agent_name", help="Agent identifier"
    )
    create_agent_parser.add_argument(
        "-d", "--description", help="Agent description",
    )
    create_agent_parser.add_argument(
        "-c", "--content", help="Markdown body content",
    )
    create_agent_parser.add_argument(
        "-D", "--field", action="append", default=[],
        help="Additional frontmatter field as key=value (repeatable)",
    )
    create_agent_parser.add_argument(
        "-H", "--here", action="store_true",
        help="Create in current project instead of vault",
    )
    create_agent_parser.add_argument(
        "--vault", help="Target vault (name or path)",
    )
    create_agent_parser.add_argument(
        "--tools",
        help="Comma-separated tool list (used with --here)",
    )

    return parser


def handle_import(args: argparse.Namespace) -> int:
    """Handle the import command."""
    from .tools import reload_registry

    global_import = getattr(args, "global_import", False)
    force = getattr(args, "force", False)

    if not global_import and args.target is None:
        print(
            "Error: A target repository is required unless --global is used.\n"
            "Usage: art import <target> or art import --global",
            file=sys.stderr,
        )
        return 1

    # Load vault tool definitions for three-tier resolution
    global_tools = load_global_tools()
    vault_tools: dict[str, dict] = {}
    vault_identifier = getattr(args, "vault", None)
    if vault_identifier:
        vault_path = get_vault_by_name_or_path(vault_identifier)
        if vault_path:
            meta = load_vault_metadata(vault_path)
            vault_tools = meta.get("tools", {})
    else:
        default_vault = get_default_vault()
        if default_vault:
            meta = load_vault_metadata(default_vault)
            vault_tools = meta.get("tools", {})

    # Reload registry with all tiers so import functions see custom tools
    reload_registry(global_tools=global_tools, vault_tools=vault_tools)

    tools_list: list[str]
    if args.tools:
        tools_list = [t.strip() for t in args.tools.split(",")]
    else:
        tools_list = [get_default_tool()]

    artifacts_list = None
    if getattr(args, "artifacts", None):
        artifacts_list = [a.strip() for a in args.artifacts.split(",")]

    try:
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
    finally:
        # Reset registry back to defaults
        reload_registry()

    if not result["success"]:
        for error in result["errors"]:
            print(error, file=sys.stderr)
        return 1

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
    """Handle the vault add command."""
    name = getattr(args, "name", None)
    set_default = getattr(args, "set_default", False)

    if name and len(args.paths) > 1:
        print("Error: --name can only be used when adding a single vault.", file=sys.stderr)
        return 1

    result = add_vaults(args.paths, name=name)
    assigned_names = result.get("names", {})

    for path in result["added"]:
        vault_name = assigned_names.get(path, name)
        if vault_name:
            print(f"Added vault: {vault_name} ({path})")
            if not name:
                print(f"  To rename this vault: art vault name {vault_name} <new-name>")
        else:
            print(f"Added vault: {path}")

    for path in result["skipped"]:
        print(f"Vault already registered: {path}")

    for error in result["errors"]:
        print(error, file=sys.stderr)

    if result["added"]:
        info = list_vaults()
        if info["default"] and info["default"] in result["added"]:
            print(f"Set as default vault: {info['default']}")

    if set_default and result["added"]:
        select_default(result["added"][0])
        print(f"Set as default vault: {result['added'][0]}")

    return 1 if result["errors"] else 0


def handle_vault_init(args: argparse.Namespace) -> int:
    """Handle the vault init command."""
    name = getattr(args, "name", None)
    set_default = getattr(args, "set_default", False)

    result = init_vault(args.target_dir, name=name)
    assigned_names = result.get("names", {})

    if result["errors"]:
        for error in result["errors"]:
            print(error, file=sys.stderr)
        return 1

    if result["added"]:
        path = result["added"][0]
        vault_name = assigned_names.get(path, name or "")
        action = "Initialized" if result.get("created") else "Registered"
        print(f"{action} vault: {vault_name} ({path})")
        print(f"  To rename this vault: art vault name {vault_name} <new-name>")

        # Write vault name to vault.yaml if --name was provided
        if name and result.get("created"):
            save_vault_metadata(path, {"name": name})

        if set_default:
            select_default(path)
            print(f"Set as default vault: {path}")
    elif result["skipped"]:
        print(f"Vault already registered: {result['skipped'][0]}")

    return 0


def handle_vault_rm(args: argparse.Namespace) -> int:
    """Handle the vault rm command."""
    result = remove_vaults(args.paths)

    for path in result["removed"]:
        print(f"Removed vault: {path}")

    for path in result["not_found"]:
        print(f"Warning: Vault not in catalog: {path}", file=sys.stderr)

    return 0


def handle_vault_select(args: argparse.Namespace) -> int:
    """Handle the vault select command."""
    if select_default(args.path):
        print(f"Default vault set to: {args.path}")
        return 0
    else:
        print(f"Error: Vault not in catalog: {args.path}", file=sys.stderr)
        return 1


def handle_vault_list(args: argparse.Namespace) -> int:
    """Handle the vault list command."""
    info = list_vaults()

    if not info["vaults"]:
        print("No vaults registered. Use 'art vault add <path>' to add a vault.")
        return 0

    vault_names = info["vault_names"]
    show_all = getattr(args, "show_all", False)

    # Check vault.yaml for names (precedence over config vault_names)
    effective_names = dict(vault_names)
    for vault_path in info["vaults"]:
        meta = load_vault_metadata(vault_path)
        if meta.get("name"):
            effective_names[vault_path] = meta["name"]

    print("Registered vaults:")
    for vault_path in info["vaults"]:
        name = effective_names.get(vault_path)
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
    """Handle the vault name command."""
    result = name_vault(args.vault, args.name)

    if result["success"]:
        print(f"Vault '{result['vault_path']}' named: {args.name}")
        return 0
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 1


def handle_tool_select(args: argparse.Namespace) -> int:
    """Handle the tool select command."""
    global_tools = load_global_tools()
    vault_tools, _ = load_active_vault_tools()
    supported_tools = get_supported_tools(global_tools=global_tools, vault_tools=vault_tools)
    resolved = resolve_tool_name(args.name, extra_tools=global_tools, vault_tools=vault_tools)
    if select_default_tool(resolved, supported_tools):
        print(f"Default tool set to: {resolved}")
        return 0
    else:
        print(
            f"Error: Unsupported tool: {args.name}. "
            f"Supported tools: {', '.join(supported_tools)}",
            file=sys.stderr,
        )
        return 1


def handle_tool_list(args: argparse.Namespace) -> int:
    """Handle the tool list command."""
    global_tools = load_global_tools()

    vault_identifier = getattr(args, "vault", None)
    if vault_identifier:
        vault_path = get_vault_by_name_or_path(vault_identifier)
        if vault_path is None:
            print(f"Error: Vault not found: {vault_identifier}", file=sys.stderr)
            return 1
        meta = load_vault_metadata(vault_path)
        vault_tools = meta.get("tools", {})
        vault_name = meta.get("name")
    else:
        vault_tools, vault_name = load_active_vault_tools()

    supported_tools = get_supported_tools(global_tools=global_tools, vault_tools=vault_tools)
    info = list_tools_info(supported_tools)

    # Build table rows
    rows = []
    for tool_name in info["tools"]:
        adapter = get_tool(tool_name, global_tools=global_tools, vault_tools=vault_tools)
        if adapter is None:
            continue

        source = get_tool_source(tool_name, global_tools=global_tools, vault_tools=vault_tools, vault_name=vault_name)
        skills_col = "yes" if "skills" in adapter.supported_types else "-"
        commands_col = "yes" if "commands" in adapter.supported_types else "-"
        agents_col = "yes" if "agents" in adapter.supported_types else "-"
        aliases = get_aliases_for_tool(tool_name, extra_tools=global_tools, vault_tools=vault_tools)
        alias_col = ", ".join(aliases) if aliases else "-"

        default_marker = " *" if tool_name == info["default"] else ""
        rows.append((tool_name + default_marker, source, skills_col, commands_col, agents_col, alias_col))

    headers = ("NAME", "SOURCE", "SKILLS", "COMMANDS", "AGENTS", "ALIASES")
    widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(val))

    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    for row in rows:
        print(fmt.format(*row))

    return 0


def handle_tool_add(args: argparse.Namespace) -> int:
    """Handle the tool add command."""
    tool_name = args.name

    # Build tool definition from flags
    tool_def: dict[str, Any] = {}
    if args.skills:
        tool_def["skills"] = args.skills
    if args.commands:
        tool_def["commands"] = args.commands
    if args.agents:
        tool_def["agents"] = args.agents
    if getattr(args, "global_skills", None):
        tool_def["global_skills"] = args.global_skills
    if getattr(args, "global_commands", None):
        tool_def["global_commands"] = args.global_commands
    if getattr(args, "global_agents", None):
        tool_def["global_agents"] = args.global_agents
    if args.aliases:
        tool_def["aliases"] = args.aliases

    # Validate at least one artifact path provided
    if not any(k in tool_def for k in ("skills", "commands", "agents")):
        print(
            "Error: At least one of --skills, --commands, or --agents is required.",
            file=sys.stderr,
        )
        return 1

    vault_identifier = getattr(args, "vault", None)

    if vault_identifier:
        # Store in vault's vault.yaml
        vault_path = get_vault_by_name_or_path(vault_identifier)
        if vault_path is None:
            print(f"Error: Vault not found: {vault_identifier}", file=sys.stderr)
            return 1

        meta = load_vault_metadata(vault_path)
        if tool_name in meta.get("tools", {}):
            print(f"Error: Tool '{tool_name}' already exists in vault.", file=sys.stderr)
            return 1

        if "tools" not in meta or meta["tools"] is None:
            meta["tools"] = {}
        meta["tools"][tool_name] = tool_def
        save_vault_metadata(vault_path, meta)
        print(f"Added tool '{tool_name}' to vault.")
    else:
        # Store in global config
        global_tools = load_global_tools()
        if tool_name in global_tools:
            print(f"Error: Tool '{tool_name}' already exists in global config.", file=sys.stderr)
            return 1

        global_tools[tool_name] = tool_def
        save_global_tools(global_tools)
        print(f"Added tool '{tool_name}' to global config.")

    return 0


def handle_tool_rm(args: argparse.Namespace) -> int:
    """Handle the tool rm command."""
    tool_name = args.name
    vault_identifier = getattr(args, "vault", None)

    if vault_identifier:
        # Remove from vault's vault.yaml
        vault_path = get_vault_by_name_or_path(vault_identifier)
        if vault_path is None:
            print(f"Error: Vault not found: {vault_identifier}", file=sys.stderr)
            return 1

        meta = load_vault_metadata(vault_path)
        vault_tools = meta.get("tools", {})
        if tool_name not in vault_tools:
            print(f"Error: Tool '{tool_name}' not found in vault.", file=sys.stderr)
            return 1

        del vault_tools[tool_name]
        meta["tools"] = vault_tools
        save_vault_metadata(vault_path, meta)
        print(f"Removed tool '{tool_name}' from vault.")
    else:
        # Remove from global config
        global_tools = load_global_tools()
        if tool_name not in global_tools:
            # Check if it's a built-in only
            if tool_name in BUILTIN_TOOLS:
                print(
                    f"Error: Cannot remove built-in tool '{tool_name}'. "
                    f"Built-in tool definitions cannot be removed.",
                    file=sys.stderr,
                )
            else:
                print(f"Error: Tool '{tool_name}' not found in global config.", file=sys.stderr)
            return 1

        del global_tools[tool_name]
        save_global_tools(global_tools)
        print(f"Removed tool '{tool_name}' from global config.")

    return 0


def handle_tool_info(args: argparse.Namespace) -> int:
    """Handle the tool info command."""
    tool_name = getattr(args, "name", None)
    vault_flag = getattr(args, "vault", None)
    global_filter = getattr(args, "global_filter", False)

    global_tools = load_global_tools()
    default_vault_tools, default_vault_name = load_active_vault_tools()
    default_vault_path = get_default_vault()
    all_vault_data = load_all_vault_tools()
    cwd_tools = load_cwd_vault_tools()

    # Resolve vault filter
    filter_vault_path: str | None = None
    filter_vault_name: str | None = None
    if vault_flag is True:
        # --vault with no value → default vault
        if default_vault_path is None:
            print("Error: No default vault configured.", file=sys.stderr)
            return 1
        filter_vault_path = default_vault_path
        filter_vault_name = default_vault_name
    elif vault_flag is not None:
        # --vault=X → specific vault
        resolved_path = get_vault_by_name_or_path(vault_flag)
        if resolved_path is None:
            print(f"Error: Vault not found: {vault_flag}", file=sys.stderr)
            return 1
        filter_vault_path = resolved_path
        meta = load_vault_metadata(resolved_path)
        filter_vault_name = meta.get("name")

    if tool_name is None:
        return _tool_info_catalog(
            global_tools=global_tools,
            all_vault_data=all_vault_data,
            cwd_tools=cwd_tools,
            default_vault_path=default_vault_path,
            global_filter=global_filter,
            filter_vault_path=filter_vault_path,
            filter_vault_name=filter_vault_name,
        )
    else:
        return _tool_info_detail(
            tool_name=tool_name,
            global_tools=global_tools,
            default_vault_tools=default_vault_tools,
            default_vault_name=default_vault_name,
            default_vault_path=default_vault_path,
            all_vault_data=all_vault_data,
            cwd_tools=cwd_tools,
            global_filter=global_filter,
            filter_vault_path=filter_vault_path,
            filter_vault_name=filter_vault_name,
        )


def _tool_info_catalog(
    global_tools: dict[str, dict],
    all_vault_data: list[tuple[str | None, str, dict[str, dict]]],
    cwd_tools: dict[str, dict],
    default_vault_path: str | None,
    global_filter: bool,
    filter_vault_path: str | None,
    filter_vault_name: str | None,
) -> int:
    """Display the catalog view: all tools grouped by source."""
    found_any = False

    # BUILT-IN section
    if not global_filter and filter_vault_path is None:
        print("BUILT-IN")
        for name in sorted(BUILTIN_TOOLS):
            aliases = BUILTIN_TOOLS[name].get("aliases", [])
            alias_str = f" (aliases: {', '.join(aliases)})" if aliases else ""
            print(f"  {name}{alias_str}")
        found_any = True

    # GLOBAL CONFIG section
    if not filter_vault_path or global_filter:
        if global_tools:
            if found_any:
                print()
            print("GLOBAL CONFIG")
            for name in sorted(global_tools):
                aliases = global_tools[name].get("aliases", [])
                alias_str = f" (aliases: {', '.join(aliases)})" if aliases else ""
                print(f"  {name}{alias_str}")
            found_any = True
        elif global_filter:
            print("GLOBAL CONFIG")
            print("  (no tools defined)")
            found_any = True

    if global_filter:
        return 0

    # Per-vault sections
    if filter_vault_path is not None:
        # Filter to a specific vault
        for vault_name, vault_path, tools in all_vault_data:
            if vault_path == filter_vault_path:
                if found_any:
                    print()
                default_marker = " (default)" if vault_path == default_vault_path else ""
                label = vault_name or vault_path
                print(f"VAULT: {label}{default_marker}")
                if tools:
                    for name in sorted(tools):
                        aliases = tools[name].get("aliases", [])
                        alias_str = f" (aliases: {', '.join(aliases)})" if aliases else ""
                        print(f"  {name}{alias_str}")
                else:
                    print("  (no tools defined)")
                found_any = True
                break
        else:
            if found_any:
                print()
            label = filter_vault_name or filter_vault_path
            print(f"VAULT: {label}")
            print("  (no tools defined)")
            found_any = True
    else:
        # Show all vaults
        for vault_name, vault_path, tools in all_vault_data:
            if not tools:
                continue
            if found_any:
                print()
            default_marker = " (default)" if vault_path == default_vault_path else ""
            label = vault_name or vault_path
            print(f"VAULT: {label}{default_marker}")
            for name in sorted(tools):
                aliases = tools[name].get("aliases", [])
                alias_str = f" (aliases: {', '.join(aliases)})" if aliases else ""
                print(f"  {name}{alias_str}")
            found_any = True

    # CURRENT DIRECTORY section
    if cwd_tools and filter_vault_path is None:
        if found_any:
            print()
        print("CURRENT DIRECTORY (./vault.yaml)")
        for name in sorted(cwd_tools):
            aliases = cwd_tools[name].get("aliases", [])
            alias_str = f" (aliases: {', '.join(aliases)})" if aliases else ""
            print(f"  {name}{alias_str}")

    return 0


def _format_tool_definition(tool_def: dict) -> None:
    """Print the artifact support details for a tool definition."""
    aliases = tool_def.get("aliases", [])
    if aliases:
        print(f"    Aliases: {', '.join(aliases)}")
    for art_type in ("skills", "commands", "agents"):
        if art_type in tool_def:
            repo_path = tool_def[art_type]
            global_key = f"global_{art_type}"
            global_path = tool_def.get(global_key, "")
            print(f"    {art_type}: {repo_path}")
            if global_path:
                print(f"      global: {global_path}")


def _tool_info_detail(
    tool_name: str,
    global_tools: dict[str, dict],
    default_vault_tools: dict[str, dict],
    default_vault_name: str | None,
    default_vault_path: str | None,
    all_vault_data: list[tuple[str | None, str, dict[str, dict]]],
    cwd_tools: dict[str, dict],
    global_filter: bool,
    filter_vault_path: str | None,
    filter_vault_name: str | None,
) -> int:
    """Display detail view for a single tool across all tiers."""
    # Resolve alias first
    resolved_name = resolve_tool_name(tool_name, extra_tools=global_tools, vault_tools=default_vault_tools)

    # Determine which definition is active via three-tier resolution
    active_source: str | None = None
    if default_vault_tools and resolved_name in default_vault_tools:
        active_source = "vault"
    elif global_tools and resolved_name in global_tools:
        active_source = "global"
    elif resolved_name in BUILTIN_TOOLS:
        active_source = "builtin"

    found_any = False

    # BUILT-IN
    if not global_filter and filter_vault_path is None:
        if resolved_name in BUILTIN_TOOLS:
            marker = "ACTIVE" if active_source == "builtin" else "(overridden)"
            symbol = "\u2713" if active_source == "builtin" else "\u25CB"
            print(f"  {symbol} BUILT-IN {marker}")
            _format_tool_definition(BUILTIN_TOOLS[resolved_name])
            found_any = True

    # GLOBAL CONFIG
    if filter_vault_path is None or global_filter:
        if resolved_name in global_tools:
            marker = "ACTIVE" if active_source == "global" else "(overridden)"
            symbol = "\u2713" if active_source == "global" else "\u25CB"
            if found_any:
                print()
            print(f"  {symbol} GLOBAL CONFIG {marker}")
            _format_tool_definition(global_tools[resolved_name])
            found_any = True

    if global_filter:
        if not found_any:
            print(f"No definition for '{resolved_name}' in global config.")
        return 0 if found_any else 1

    # Per-vault definitions
    if filter_vault_path is not None:
        for vault_name, vault_path, tools in all_vault_data:
            if vault_path == filter_vault_path and resolved_name in tools:
                is_default = vault_path == default_vault_path
                if is_default:
                    marker = "ACTIVE" if active_source == "vault" else "(overridden)"
                    symbol = "\u2713" if active_source == "vault" else "\u25CB"
                else:
                    marker = "(not active)"
                    symbol = "\u25CB"
                if found_any:
                    print()
                label = vault_name or vault_path
                default_tag = " (default)" if is_default else ""
                print(f"  {symbol} VAULT: {label}{default_tag} {marker}")
                _format_tool_definition(tools[resolved_name])
                found_any = True
                break
    else:
        for vault_name, vault_path, tools in all_vault_data:
            if resolved_name in tools:
                is_default = vault_path == default_vault_path
                if is_default:
                    marker = "ACTIVE" if active_source == "vault" else "(overridden)"
                    symbol = "\u2713" if active_source == "vault" else "\u25CB"
                else:
                    marker = "(not active)"
                    symbol = "\u25CB"
                if found_any:
                    print()
                label = vault_name or vault_path
                default_tag = " (default)" if is_default else ""
                print(f"  {symbol} VAULT: {label}{default_tag} {marker}")
                _format_tool_definition(tools[resolved_name])
                found_any = True

    # CWD
    if filter_vault_path is None and not global_filter:
        if resolved_name in cwd_tools:
            if found_any:
                print()
            print(f"  \u25CB CURRENT DIRECTORY (./vault.yaml) (not active)")
            _format_tool_definition(cwd_tools[resolved_name])
            found_any = True

    if not found_any:
        print(f"Error: Unknown tool: {resolved_name}", file=sys.stderr)
        return 1

    return 0


def parse_selection(selection: str, max_val: int) -> list[int]:
    """Parse a user selection string into a list of 0-based indices."""
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
    """Handle the spelunk command."""
    target = Path(args.target).resolve()

    if not target.exists() or not target.is_dir():
        print(f"Error: Target directory does not exist: {args.target}", file=sys.stderr)
        return 1

    artifacts = discover_artifacts(target)

    if not artifacts:
        print(f"No artifacts found in {args.target}")
        return 0

    import_cache = load_import_cache(target)

    rows = []
    for art in artifacts:
        name_col = art["name"]

        if art["name"] in import_cache:
            vault_names = ", ".join(import_cache[art["name"]])
            name_col += f" (imported: {vault_names})"

        description = extract_description(art)
        tool_label = art["tool"]
        rows.append((name_col, art["type"], tool_label, description))

    headers = ("NAME", "TYPE", "TOOL", "DESCRIPTION")
    widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(val))

    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    for row in rows:
        print(fmt.format(*row))

    return 0


def handle_store(args: argparse.Namespace) -> int:
    """Handle the store command."""
    target = Path(args.target_dir).resolve()

    if not target.exists() or not target.is_dir():
        print(f"Error: Target directory does not exist: {args.target_dir}", file=sys.stderr)
        return 1

    vault_identifier = getattr(args, "vault", None)
    if vault_identifier:
        vault_path_str = get_vault_by_name_or_path(vault_identifier)
        if vault_path_str is None:
            print(f"Error: Vault not in catalog: {vault_identifier}", file=sys.stderr)
            return 1
    else:
        vault_path_str = get_default_vault()
        if vault_path_str is None:
            print("Error: No default vault set. Use 'art vault add' or 'art vault init' to set up a vault.", file=sys.stderr)
            return 1

    vault_path = Path(vault_path_str)

    vault_info = list_vaults()
    vault_display_name = vault_info["vault_names"].get(vault_path_str, vault_path.name)

    artifacts = discover_artifacts(target)

    if not artifacts:
        print(f"No artifacts found in {args.target_dir}")
        return 0

    print(f"Discovered artifacts in {target}:")
    for i, art in enumerate(artifacts, 1):
        rel_path = art["path"].relative_to(target)
        print(f"  {i}. {art['name']} ({art['type']}) - {rel_path}")

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


def handle_edit(args: argparse.Namespace) -> int:
    """Handle the edit command."""
    import subprocess

    from .utils import get_editor

    artifact_type = args.artifact_type
    artifact_name = args.artifact_name
    vault = getattr(args, "vault", None)
    here = getattr(args, "here", False)
    tools_str = getattr(args, "tools", None)

    tools_list = None
    if tools_str:
        tools_list = [t.strip() for t in tools_str.split(",")]

    resolution = resolve_edit_target(
        artifact_type=artifact_type,
        artifact_name=artifact_name,
        vault=vault,
        here=here,
        tools=tools_list,
    )

    if not resolution["success"]:
        print(f"Error: {resolution['error']}", file=sys.stderr)
        return 1

    editor = get_editor()
    if editor is None:
        print(
            "Error: No editor found. Set $EDITOR or install nano, neovim, vim, or vi.",
            file=sys.stderr,
        )
        return 1

    result = subprocess.run([editor, str(resolution["path"])])
    return result.returncode


def handle_create_artifact(args: argparse.Namespace, artifact_type: str) -> int:
    """Handle create skill/command/agent commands."""
    if artifact_type == "skill":
        artifact_name = args.skill_name
        display_name = getattr(args, "display_name", None) or artifact_name
    elif artifact_type == "command":
        artifact_name = args.command_name
        display_name = artifact_name
    else:
        artifact_name = args.agent_name
        display_name = artifact_name

    description = getattr(args, "description", None)
    content = getattr(args, "content", None)
    field_flags = getattr(args, "field", []) or []
    here = getattr(args, "here", False)
    vault = getattr(args, "vault", None)
    tools_str = getattr(args, "tools", None)

    if description is None:
        print(
            f"Error: --description / -d is required.\n"
            f'Usage: art create {artifact_type} <name> -d "description" [-c content] [-D key=value ...]',
            file=sys.stderr,
        )
        return 1

    extra_fields = {}
    for field_str in field_flags:
        if "=" not in field_str:
            print(f"Error: Invalid field format '{field_str}'. Use key=value.", file=sys.stderr)
            return 1
        key, value = field_str.split("=", 1)
        extra_fields[key] = value

    if here:
        tools_list = None
        if tools_str:
            tools_list = [t.strip() for t in tools_str.split(",")]

        resolution = resolve_project_target(artifact_name, artifact_type=artifact_type, tools=tools_list)
        if not resolution["success"]:
            print(f"Error: {resolution['error']}", file=sys.stderr)
            return 1

        targets = resolution["paths"]
    else:
        resolution = resolve_vault_target(artifact_name, artifact_type=artifact_type, vault=vault)
        if not resolution["success"]:
            print(f"Error: {resolution['error']}", file=sys.stderr)
            return 1

        targets = [resolution["path"]]

    for target_path in targets:
        result = create_artifact(
            artifact_type=artifact_type,
            name=display_name,
            description=description,
            content=content,
            extra_fields=extra_fields if extra_fields else None,
            target_path=target_path,
        )
        if not result["success"]:
            print(f"Error: {result['error']}", file=sys.stderr)
            return 1
        print(f"Created {artifact_type}: {result['path']}")

    return 0


def handle_create_skill(args: argparse.Namespace) -> int:
    """Handle the create skill command."""
    return handle_create_artifact(args, "skill")


def main() -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "import":
        return handle_import(args)

    if args.command == "vault":
        if args.vault_command is None:
            parser.parse_args(["vault", "--help"])
            return 0

        if args.vault_command == "add":
            return handle_vault_add(args)
        if args.vault_command == "init":
            return handle_vault_init(args)
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
            parser.parse_args(["tool", "--help"])
            return 0

        if args.tool_command == "select":
            return handle_tool_select(args)
        if args.tool_command == "list":
            return handle_tool_list(args)
        if args.tool_command == "add":
            return handle_tool_add(args)
        if args.tool_command == "rm":
            return handle_tool_rm(args)
        if args.tool_command == "info":
            return handle_tool_info(args)

    if args.command == "spelunk":
        return handle_spelunk(args)

    if args.command == "store":
        return handle_store(args)

    if args.command == "edit":
        return handle_edit(args)

    if args.command == "create":
        if args.create_command is None:
            parser.parse_args(["create", "--help"])
            return 0

        if args.create_command == "skill":
            return handle_create_skill(args)
        if args.create_command == "command":
            return handle_create_artifact(args, "command")
        if args.create_command == "agent":
            return handle_create_artifact(args, "agent")

    return 0


if __name__ == "__main__":
    sys.exit(main())
