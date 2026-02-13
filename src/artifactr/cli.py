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
from .importer import (
    copy_with_prompt,
    import_artifacts,
    import_artifacts_global,
    remove_from_global_import_cache,
    remove_from_import_cache,
)
from .scanner import (
    discover_artifacts,
    discover_global_artifacts,
    discover_vault_artifacts,
    extract_description,
    is_vault,
    load_import_cache,
)
from .tools import (
    BUILTIN_TOOLS,
    get_aliases_for_tool,
    get_supported_tools,
    get_tool,
    get_tool_config_dirs,
    get_tool_global_dirs,
    get_tool_source,
    resolve_tool_name,
)


def add_type_filter_args(parser: argparse.ArgumentParser, allow_names: bool = True) -> None:
    """Add type filter flags (-S/--skills, -C/--commands, -A/--agents) to a parser.

    Args:
        parser: The argparse parser or subparser to add flags to.
        allow_names: If True, flags accept optional comma-separated names (nargs='?').
                     If False, flags are boolean-only (store_true).
    """
    if allow_names:
        parser.add_argument(
            "-S", "--skills", nargs="?", const=True, default=None,
            help="Filter to skills (optionally specify comma-separated names)",
        )
        parser.add_argument(
            "-C", "--commands", nargs="?", const=True, default=None,
            help="Filter to commands (optionally specify comma-separated names)",
        )
        parser.add_argument(
            "-A", "--agents", nargs="?", const=True, default=None,
            help="Filter to agents (optionally specify comma-separated names)",
        )
    else:
        parser.add_argument(
            "-S", "--skills", action="store_true",
            help="Filter to skills",
        )
        parser.add_argument(
            "-C", "--commands", action="store_true",
            help="Filter to commands",
        )
        parser.add_argument(
            "-A", "--agents", action="store_true",
            help="Filter to agents",
        )


def resolve_type_filters(args: argparse.Namespace) -> dict[str, Any] | None:
    """Interpret parsed type filter arguments into a structured result.

    Returns:
        None if no filters are specified (all types included).
        Dict mapping type names to True (all of type) or list of names.
    """
    result: dict[str, Any] = {}

    for type_name in ("skills", "commands", "agents"):
        val = getattr(args, type_name, None)
        if val is True:
            result[type_name] = True
        elif val is not None and val is not False and isinstance(val, str):
            result[type_name] = [n.strip() for n in val.split(",")]

    return result if result else None


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

    # list command (vault-side)
    list_parser = subparsers.add_parser(
        "list", help="List artifacts in a vault"
    )
    list_parser.add_argument(
        "--vault", help="Vault to list from (default: default vault)"
    )
    add_type_filter_args(list_parser)

    # rm command (vault-side)
    rm_parser = subparsers.add_parser(
        "rm", help="Remove artifacts from a vault"
    )
    rm_parser.add_argument(
        "names", nargs="+", help="Artifact names to remove (supports type/name prefix)"
    )
    rm_parser.add_argument(
        "--vault", help="Vault to remove from (default: default vault)"
    )
    rm_parser.add_argument(
        "-f", "--force", action="store_true",
        help="Skip confirmation prompt",
    )

    # spelunk command
    spelunk_parser = subparsers.add_parser(
        "spelunk", help="Discover artifacts in a directory, vault, or global config"
    )
    spelunk_parser.add_argument("target", nargs="?", default=None, help="Path to directory to probe")
    spelunk_parser.add_argument(
        "-g", "--global", action="store_true", dest="global_spelunk",
        help="Explicitly scan global config directories",
    )
    spelunk_parser.add_argument(
        "--tools", help="Comma-separated list of tools to filter to",
    )
    add_type_filter_args(spelunk_parser)

    # project namespace (art project / art proj)
    project_parser = subparsers.add_parser(
        "project", aliases=["proj"], help="Project-side artifact operations"
    )
    proj_subparsers = project_parser.add_subparsers(dest="proj_command")

    # proj import
    proj_import = proj_subparsers.add_parser(
        "import", help="Import artifacts from vault into a project"
    )
    proj_import.add_argument(
        "target", nargs="?", default=None, help="Path to target git repository (default: cwd)"
    )
    proj_import.add_argument(
        "--vault", help="Vault to import from (default: default vault)"
    )
    proj_import.add_argument(
        "--tools", help="Comma-separated list of tools to import",
    )
    proj_import.add_argument(
        "--artifacts", help="Comma-separated list of artifact names to import",
    )
    proj_import.add_argument(
        "-l", "--link", action="store_true",
        help="Symlink vault contents instead of copying",
    )
    proj_import.add_argument(
        "-f", "--force", action="store_true",
        help="Overwrite existing files without prompting",
    )
    proj_import.add_argument(
        "--no-exclude", action="store_true",
        help="Don't add artifact paths to .git/info/exclude (.art-cache still excluded)",
    )
    add_type_filter_args(proj_import)

    # proj rm
    proj_rm = proj_subparsers.add_parser(
        "rm", help="Remove imported artifacts from a project"
    )
    proj_rm.add_argument("names", nargs="+", help="Artifact names to remove")
    proj_rm.add_argument(
        "--target", default=None, help="Project path (default: cwd)",
    )
    proj_rm.add_argument(
        "--tools", help="Comma-separated tool filter",
    )
    proj_rm.add_argument(
        "-f", "--force", action="store_true",
        help="Skip confirmation prompt",
    )
    add_type_filter_args(proj_rm, allow_names=False)

    # proj wipe
    proj_wipe = proj_subparsers.add_parser(
        "wipe", help="Clear all imported artifacts from a project"
    )
    proj_wipe.add_argument(
        "--target", default=None, help="Project path (default: cwd)",
    )
    proj_wipe.add_argument(
        "--tools", help="Comma-separated tool filter",
    )
    proj_wipe.add_argument(
        "-f", "--force", action="store_true",
        help="Skip confirmation prompt",
    )
    add_type_filter_args(proj_wipe)

    # proj list
    proj_list = proj_subparsers.add_parser(
        "list", help="Show imported artifacts in a project"
    )
    proj_list.add_argument(
        "--target", default=None, help="Project path (default: cwd)",
    )
    proj_list.add_argument(
        "--tools", help="Comma-separated tool filter",
    )
    add_type_filter_args(proj_list)

    # config namespace (art config / art conf)
    config_parser = subparsers.add_parser(
        "config", aliases=["conf"], help="Global config artifact operations"
    )
    conf_subparsers = config_parser.add_subparsers(dest="conf_command")

    # conf import
    conf_import = conf_subparsers.add_parser(
        "import", help="Import artifacts into global config directories"
    )
    conf_import.add_argument(
        "--vault", help="Vault to import from (default: default vault)"
    )
    conf_import.add_argument(
        "--tools", help="Comma-separated list of tools to import",
    )
    conf_import.add_argument(
        "--artifacts", help="Comma-separated list of artifact names to import",
    )
    conf_import.add_argument(
        "-l", "--link", action="store_true",
        help="Symlink vault contents instead of copying",
    )
    conf_import.add_argument(
        "-f", "--force", action="store_true",
        help="Overwrite existing files without prompting",
    )
    add_type_filter_args(conf_import)

    # conf rm
    conf_rm = conf_subparsers.add_parser(
        "rm", help="Remove globally imported artifacts"
    )
    conf_rm.add_argument("names", nargs="+", help="Artifact names to remove")
    conf_rm.add_argument(
        "--tools", help="Comma-separated tool filter",
    )
    conf_rm.add_argument(
        "-f", "--force", action="store_true",
        help="Skip confirmation prompt",
    )
    add_type_filter_args(conf_rm, allow_names=False)

    # conf wipe
    conf_wipe = conf_subparsers.add_parser(
        "wipe", help="Clear all globally imported artifacts"
    )
    conf_wipe.add_argument(
        "--tools", help="Comma-separated tool filter",
    )
    conf_wipe.add_argument(
        "-f", "--force", action="store_true",
        help="Skip confirmation prompt",
    )
    add_type_filter_args(conf_wipe)

    # conf list
    conf_list = conf_subparsers.add_parser(
        "list", help="Show globally imported artifacts"
    )
    conf_list.add_argument(
        "--tools", help="Comma-separated tool filter",
    )
    add_type_filter_args(conf_list)

    # store command
    store_parser = subparsers.add_parser(
        "store", help="Store artifacts from a directory into a vault"
    )
    store_parser.add_argument("target_dir", help="Path to directory containing artifacts")
    store_parser.add_argument(
        "--vault", help="Vault to store into (default: default vault)"
    )
    add_type_filter_args(store_parser)

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


def _load_vault_tools_for_import(args: argparse.Namespace) -> tuple[dict, dict]:
    """Load global and vault tools for import operations."""
    from .tools import reload_registry

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

    reload_registry(global_tools=global_tools, vault_tools=vault_tools)
    return global_tools, vault_tools


def handle_list(args: argparse.Namespace) -> int:
    """Handle the art list command (vault-side listing)."""
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
    artifacts = discover_vault_artifacts(vault_path)

    type_filters = resolve_type_filters(args)
    if type_filters:
        artifacts = _apply_type_filters(artifacts, type_filters)

    if not artifacts:
        print("No artifacts found in vault.")
        return 0

    rows = []
    for art in artifacts:
        description = extract_description(art)
        rows.append((art["name"], art["type"], description))

    headers = ("NAME", "TYPE", "DESCRIPTION")
    widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(val))

    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    for row in rows:
        print(fmt.format(*row))

    return 0


def handle_rm(args: argparse.Namespace) -> int:
    """Handle the art rm command (vault-side removal)."""
    from .importer import resolve_artifact_names

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
    force = getattr(args, "force", False)

    resolved = resolve_artifact_names(vault_path, args.names)
    if not resolved:
        print("No matching artifacts found.", file=sys.stderr)
        return 1

    if not force:
        print("The following artifacts will be removed:")
        for art in resolved:
            print(f"  {art['type']}/{art['name']}")
        try:
            response = input("Continue? [y/N]: ")
            if response.lower() not in ("y", "yes"):
                print("Aborted.")
                return 0
        except EOFError:
            print("Aborted.")
            return 0

    import shutil
    removed = 0
    for art in resolved:
        source = art["source"]
        if source.is_dir():
            shutil.rmtree(source)
        elif source.is_file():
            source.unlink()
        print(f"Removed: {art['type']}/{art['name']}")
        removed += 1

    print(f"\n{removed} artifact(s) removed.")
    return 0


def handle_proj_import(args: argparse.Namespace) -> int:
    """Handle the proj import command."""
    from .tools import reload_registry

    target = args.target or str(Path.cwd())
    force = getattr(args, "force", False)
    no_exclude = getattr(args, "no_exclude", False)

    _load_vault_tools_for_import(args)

    tools_list: list[str]
    if args.tools:
        tools_list = [t.strip() for t in args.tools.split(",")]
    else:
        tools_list = [get_default_tool()]

    artifacts_list = None
    if getattr(args, "artifacts", None):
        artifacts_list = [a.strip() for a in args.artifacts.split(",")]

    type_filters = resolve_type_filters(args)

    try:
        result = import_artifacts(
            target=target,
            vault=getattr(args, "vault", None),
            tools=tools_list,
            link=getattr(args, "link", False),
            artifacts=artifacts_list,
            force=force,
            no_exclude=no_exclude,
            type_filters=type_filters,
        )
    finally:
        reload_registry()

    if not result["success"]:
        for error in result["errors"]:
            print(error, file=sys.stderr)
        return 1

    print_import_summary(result)
    return 0


def handle_proj_rm(args: argparse.Namespace) -> int:
    """Handle the proj rm command."""
    target_path = Path(args.target).resolve() if getattr(args, "target", None) else Path.cwd().resolve()
    force = getattr(args, "force", False)

    tools_filter = None
    if getattr(args, "tools", None):
        tools_filter = [t.strip() for t in args.tools.split(",")]

    type_filters = resolve_type_filters(args)

    # Load cache to find artifact locations
    cache = _load_cache_entries(target_path)
    if not cache:
        print("No imported artifacts found.", file=sys.stderr)
        return 1

    # Find artifacts matching the given names
    global_tools = load_global_tools()
    vault_tools_dict, _ = load_active_vault_tools()
    tool_config_dirs = get_tool_config_dirs(global_tools=global_tools, vault_tools=vault_tools_dict)

    to_remove: list[dict] = []
    for name in args.names:
        found = _find_project_artifacts(target_path, name, tool_config_dirs, cache, tools_filter, type_filters)
        to_remove.extend(found)

    if not to_remove:
        print("No matching artifacts found.", file=sys.stderr)
        return 1

    if not force:
        print("The following artifacts will be removed:")
        for art in to_remove:
            print(f"  {art['name']} ({art['type']}) - {art['path']}")
        try:
            response = input("Continue? [y/N]: ")
            if response.lower() not in ("y", "yes"):
                print("Aborted.")
                return 0
        except EOFError:
            print("Aborted.")
            return 0

    import shutil
    removed_names = []
    for art in to_remove:
        path = art["path"]
        if path.is_dir():
            shutil.rmtree(path)
        elif path.is_file():
            path.unlink()
        removed_names.append(art["name"])
        print(f"Removed: {art['name']} ({art['type']})")

    if removed_names:
        remove_from_import_cache(target_path, removed_names)

    print(f"\n{len(removed_names)} artifact(s) removed.")
    return 0


def handle_proj_wipe(args: argparse.Namespace) -> int:
    """Handle the proj wipe command."""
    target_path = Path(args.target).resolve() if getattr(args, "target", None) else Path.cwd().resolve()
    force = getattr(args, "force", False)

    tools_filter = None
    if getattr(args, "tools", None):
        tools_filter = [t.strip() for t in args.tools.split(",")]

    type_filters = resolve_type_filters(args)

    cache = _load_cache_entries(target_path)
    if not cache:
        print("No imported artifacts found.")
        return 0

    global_tools = load_global_tools()
    vault_tools_dict, _ = load_active_vault_tools()
    tool_config_dirs = get_tool_config_dirs(global_tools=global_tools, vault_tools=vault_tools_dict)

    to_remove = _find_all_project_artifacts(target_path, tool_config_dirs, cache, tools_filter, type_filters)

    if not to_remove:
        print("No matching artifacts found.")
        return 0

    if not force:
        print("The following artifacts will be removed:")
        for art in to_remove:
            print(f"  {art['name']} ({art['type']}) - {art['path']}")
        try:
            response = input("Continue? [y/N]: ")
            if response.lower() not in ("y", "yes"):
                print("Aborted.")
                return 0
        except EOFError:
            print("Aborted.")
            return 0

    import shutil
    removed_names = []
    for art in to_remove:
        path = art["path"]
        if path.is_dir():
            shutil.rmtree(path)
        elif path.is_file():
            path.unlink()
        removed_names.append(art["name"])
        print(f"Removed: {art['name']} ({art['type']})")

    if removed_names:
        remove_from_import_cache(target_path, removed_names)

    print(f"\n{len(removed_names)} artifact(s) removed.")
    return 0


def handle_proj_list(args: argparse.Namespace) -> int:
    """Handle the proj list command."""
    target_path = Path(args.target).resolve() if getattr(args, "target", None) else Path.cwd().resolve()

    tools_filter = None
    if getattr(args, "tools", None):
        tools_filter = [t.strip() for t in args.tools.split(",")]

    type_filters = resolve_type_filters(args)

    cache = _load_cache_entries(target_path)
    if not cache:
        print("No imported artifacts found.")
        return 0

    rows = []
    for entry in cache:
        # Apply tool filter
        if tools_filter and entry["tool"] not in tools_filter:
            continue
        # Apply type filter
        if type_filters and entry["type_plural"] not in type_filters:
            continue
        rows.append((entry["name"], entry["type"], entry["tool"], entry["vault"]))

    if not rows:
        print("No matching imported artifacts found.")
        return 0

    headers = ("NAME", "TYPE", "TOOL", "VAULT")
    widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(val))

    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    for row in rows:
        print(fmt.format(*row))

    return 0


def handle_conf_import(args: argparse.Namespace) -> int:
    """Handle the conf import command."""
    from .tools import reload_registry

    _load_vault_tools_for_import(args)

    tools_list: list[str]
    if args.tools:
        tools_list = [t.strip() for t in args.tools.split(",")]
    else:
        tools_list = [get_default_tool()]

    artifacts_list = None
    if getattr(args, "artifacts", None):
        artifacts_list = [a.strip() for a in args.artifacts.split(",")]

    type_filters = resolve_type_filters(args)

    try:
        result = import_artifacts_global(
            vault=getattr(args, "vault", None),
            tools=tools_list,
            link=getattr(args, "link", False),
            artifacts=artifacts_list,
            force=getattr(args, "force", False),
            type_filters=type_filters,
        )
    finally:
        reload_registry()

    if not result["success"]:
        for error in result["errors"]:
            print(error, file=sys.stderr)
        return 1

    print_import_summary(result)
    return 0


def handle_conf_rm(args: argparse.Namespace) -> int:
    """Handle the conf rm command."""
    force = getattr(args, "force", False)

    tools_filter = None
    if getattr(args, "tools", None):
        tools_filter = [t.strip() for t in args.tools.split(",")]

    type_filters = resolve_type_filters(args)

    cache = _load_global_cache_entries()
    if not cache:
        print("No globally imported artifacts found.", file=sys.stderr)
        return 1

    global_tools = load_global_tools()
    vault_tools_dict, _ = load_active_vault_tools()
    tool_global_dirs = get_tool_global_dirs(global_tools=global_tools, vault_tools=vault_tools_dict)

    to_remove: list[dict] = []
    for name in args.names:
        found = _find_global_artifacts(name, tool_global_dirs, cache, tools_filter, type_filters)
        to_remove.extend(found)

    if not to_remove:
        print("No matching artifacts found.", file=sys.stderr)
        return 1

    if not force:
        print("The following artifacts will be removed:")
        for art in to_remove:
            print(f"  {art['name']} ({art['type']}) - {art['path']}")
        try:
            response = input("Continue? [y/N]: ")
            if response.lower() not in ("y", "yes"):
                print("Aborted.")
                return 0
        except EOFError:
            print("Aborted.")
            return 0

    import shutil
    removed_names = []
    for art in to_remove:
        path = art["path"]
        if path.is_dir():
            shutil.rmtree(path)
        elif path.is_file():
            path.unlink()
        removed_names.append(art["name"])
        print(f"Removed: {art['name']} ({art['type']})")

    if removed_names:
        remove_from_global_import_cache(removed_names)

    print(f"\n{len(removed_names)} artifact(s) removed.")
    return 0


def handle_conf_wipe(args: argparse.Namespace) -> int:
    """Handle the conf wipe command."""
    force = getattr(args, "force", False)

    tools_filter = None
    if getattr(args, "tools", None):
        tools_filter = [t.strip() for t in args.tools.split(",")]

    type_filters = resolve_type_filters(args)

    cache = _load_global_cache_entries()
    if not cache:
        print("No globally imported artifacts found.")
        return 0

    global_tools = load_global_tools()
    vault_tools_dict, _ = load_active_vault_tools()
    tool_global_dirs = get_tool_global_dirs(global_tools=global_tools, vault_tools=vault_tools_dict)

    to_remove = _find_all_global_artifacts(tool_global_dirs, cache, tools_filter, type_filters)

    if not to_remove:
        print("No matching artifacts found.")
        return 0

    if not force:
        print("The following artifacts will be removed:")
        for art in to_remove:
            print(f"  {art['name']} ({art['type']}) - {art['path']}")
        try:
            response = input("Continue? [y/N]: ")
            if response.lower() not in ("y", "yes"):
                print("Aborted.")
                return 0
        except EOFError:
            print("Aborted.")
            return 0

    import shutil
    removed_names = []
    for art in to_remove:
        path = art["path"]
        if path.is_dir():
            shutil.rmtree(path)
        elif path.is_file():
            path.unlink()
        removed_names.append(art["name"])
        print(f"Removed: {art['name']} ({art['type']})")

    if removed_names:
        remove_from_global_import_cache(removed_names)

    print(f"\n{len(removed_names)} artifact(s) removed.")
    return 0


def handle_conf_list(args: argparse.Namespace) -> int:
    """Handle the conf list command."""
    tools_filter = None
    if getattr(args, "tools", None):
        tools_filter = [t.strip() for t in args.tools.split(",")]

    type_filters = resolve_type_filters(args)

    cache = _load_global_cache_entries()
    if not cache:
        print("No globally imported artifacts found.")
        return 0

    rows = []
    for entry in cache:
        if tools_filter and entry["tool"] not in tools_filter:
            continue
        if type_filters and entry["type_plural"] not in type_filters:
            continue
        rows.append((entry["name"], entry["type"], entry["tool"], entry["vault"]))

    if not rows:
        print("No matching imported artifacts found.")
        return 0

    headers = ("NAME", "TYPE", "TOOL", "VAULT")
    widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(val))

    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    for row in rows:
        print(fmt.format(*row))

    return 0


def _apply_type_filters(artifacts: list[dict], type_filters: dict[str, Any]) -> list[dict]:
    """Filter a list of artifacts based on type filters."""
    result = []
    for art in artifacts:
        type_plural = art["type_plural"]
        if type_plural not in type_filters:
            continue
        filter_val = type_filters[type_plural]
        if filter_val is True:
            result.append(art)
        elif isinstance(filter_val, list):
            if art["name"] in filter_val:
                result.append(art)
    return result


def _load_cache_entries(target: Path) -> list[dict]:
    """Load import cache entries as structured dicts, enriched with type info."""
    cache_file = target / ".art-cache" / "imported"
    if not cache_file.is_file():
        return []

    entries = []
    try:
        content = cache_file.read_text(encoding="utf-8")
    except OSError:
        return []

    # Build a lookup to determine artifact types from filesystem
    global_tools = load_global_tools()
    vault_tools_dict, _ = load_active_vault_tools()
    tool_config_dirs = get_tool_config_dirs(global_tools=global_tools, vault_tools=vault_tools_dict)

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(".")
        if len(parts) < 3:
            continue
        vault_name = parts[0]
        tool_name = parts[1]
        artifact_name = parts[-1]

        # Determine type by probing filesystem
        art_type, art_type_plural = _resolve_artifact_type(
            target, artifact_name, tool_name, tool_config_dirs
        )

        entries.append({
            "name": artifact_name,
            "tool": tool_name,
            "vault": vault_name,
            "type": art_type,
            "type_plural": art_type_plural,
            "raw": line,
        })

    return entries


def _load_global_cache_entries() -> list[dict]:
    """Load global import cache entries as structured dicts, enriched with type info."""
    cache_file = Path.home() / ".config" / "artifactr" / ".art-cache-global" / "imported"
    if not cache_file.is_file():
        return []

    entries = []
    try:
        content = cache_file.read_text(encoding="utf-8")
    except OSError:
        return []

    global_tools = load_global_tools()
    vault_tools_dict, _ = load_active_vault_tools()
    tool_global_dirs = get_tool_global_dirs(global_tools=global_tools, vault_tools=vault_tools_dict)

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(".")
        if len(parts) < 3:
            continue
        vault_name = parts[0]
        tool_name = parts[1]
        artifact_name = parts[-1]

        art_type, art_type_plural = _resolve_global_artifact_type(
            artifact_name, tool_name, tool_global_dirs
        )

        entries.append({
            "name": artifact_name,
            "tool": tool_name,
            "vault": vault_name,
            "type": art_type,
            "type_plural": art_type_plural,
            "raw": line,
        })

    return entries


def _resolve_artifact_type(
    target: Path,
    name: str,
    tool_name: str,
    tool_config_dirs: dict[str, dict[str, str]],
) -> tuple[str, str]:
    """Resolve the type of an artifact by probing the filesystem."""
    if tool_name in tool_config_dirs:
        type_paths = tool_config_dirs[tool_name]
        for artifact_type, repo_path in type_paths.items():
            base = target / repo_path
            if artifact_type == "skills":
                if (base / name).is_dir() and (base / name / "SKILL.md").is_file():
                    return ("skill", "skills")
            elif artifact_type == "commands":
                if (base / f"{name}.md").is_file():
                    return ("command", "commands")
            elif artifact_type == "agents":
                if (base / f"{name}.md").is_file():
                    return ("agent", "agents")
    return ("unknown", "unknown")


def _resolve_global_artifact_type(
    name: str,
    tool_name: str,
    tool_global_dirs: dict[str, dict[str, str]],
) -> tuple[str, str]:
    """Resolve the type of a globally imported artifact by probing the filesystem."""
    if tool_name in tool_global_dirs:
        type_paths = tool_global_dirs[tool_name]
        for artifact_type, global_path in type_paths.items():
            base = Path(global_path)
            if artifact_type == "skills":
                if (base / name).is_dir() and (base / name / "SKILL.md").is_file():
                    return ("skill", "skills")
            elif artifact_type == "commands":
                if (base / f"{name}.md").is_file():
                    return ("command", "commands")
            elif artifact_type == "agents":
                if (base / f"{name}.md").is_file():
                    return ("agent", "agents")
    return ("unknown", "unknown")


def _find_project_artifacts(
    target: Path,
    name: str,
    tool_config_dirs: dict[str, dict[str, str]],
    cache: list[dict],
    tools_filter: list[str] | None,
    type_filters: dict[str, Any] | None,
) -> list[dict]:
    """Find project artifacts matching a name across tool config dirs."""
    # Check if name has a type prefix
    type_prefix = None
    search_name = name
    if "/" in name:
        type_prefix, search_name = name.split("/", 1)

    matches = []
    for tool_name, type_paths in tool_config_dirs.items():
        if tools_filter and tool_name not in tools_filter:
            continue

        for artifact_type, repo_path in type_paths.items():
            if type_prefix and artifact_type != type_prefix:
                continue
            if type_filters and artifact_type not in type_filters:
                continue

            base = target / repo_path
            if artifact_type == "skills":
                candidate = base / search_name
                if candidate.is_dir() and (candidate / "SKILL.md").is_file():
                    matches.append({
                        "name": search_name,
                        "type": "skill",
                        "type_plural": "skills",
                        "path": candidate,
                        "tool": tool_name,
                    })
            else:
                candidate = base / f"{search_name}.md"
                if candidate.is_file():
                    singular = "command" if artifact_type == "commands" else "agent"
                    matches.append({
                        "name": search_name,
                        "type": singular,
                        "type_plural": artifact_type,
                        "path": candidate,
                        "tool": tool_name,
                    })

    if len(matches) > 1 and type_prefix is None and type_filters is None:
        # Ambiguous — prompt user
        print(f'Ambiguous artifact name: "{name}"')
        print("Found in multiple locations:")
        for i, m in enumerate(matches, 1):
            print(f"  {i}. {m['type_plural']}/{m['name']} ({m['tool']})")
        try:
            choice = input(f"Select one [1-{len(matches)}]: ")
            idx = int(choice) - 1
            if 0 <= idx < len(matches):
                return [matches[idx]]
        except (EOFError, ValueError):
            pass
        return []

    return matches


def _find_all_project_artifacts(
    target: Path,
    tool_config_dirs: dict[str, dict[str, str]],
    cache: list[dict],
    tools_filter: list[str] | None,
    type_filters: dict[str, Any] | None,
) -> list[dict]:
    """Find all project artifacts that match filters, based on cache."""
    seen = set()
    results = []

    for entry in cache:
        if tools_filter and entry["tool"] not in tools_filter:
            continue

        name = entry["name"]
        tool_name = entry["tool"]

        if tool_name not in tool_config_dirs:
            continue

        type_paths = tool_config_dirs[tool_name]
        for artifact_type, repo_path in type_paths.items():
            if type_filters and artifact_type not in type_filters:
                continue

            base = target / repo_path
            if artifact_type == "skills":
                candidate = base / name
                if candidate.is_dir() and (candidate / "SKILL.md").is_file():
                    key = str(candidate)
                    if key not in seen:
                        seen.add(key)
                        results.append({
                            "name": name,
                            "type": "skill",
                            "type_plural": "skills",
                            "path": candidate,
                            "tool": tool_name,
                        })
            else:
                candidate = base / f"{name}.md"
                if candidate.is_file():
                    key = str(candidate)
                    if key not in seen:
                        seen.add(key)
                        singular = "command" if artifact_type == "commands" else "agent"
                        results.append({
                            "name": name,
                            "type": singular,
                            "type_plural": artifact_type,
                            "path": candidate,
                            "tool": tool_name,
                        })

    return results


def _find_global_artifacts(
    name: str,
    tool_global_dirs: dict[str, dict[str, str]],
    cache: list[dict],
    tools_filter: list[str] | None,
    type_filters: dict[str, Any] | None,
) -> list[dict]:
    """Find globally imported artifacts matching a name."""
    type_prefix = None
    search_name = name
    if "/" in name:
        type_prefix, search_name = name.split("/", 1)

    matches = []
    for tool_name, type_paths in tool_global_dirs.items():
        if tools_filter and tool_name not in tools_filter:
            continue

        for artifact_type, global_path in type_paths.items():
            if type_prefix and artifact_type != type_prefix:
                continue
            if type_filters and artifact_type not in type_filters:
                continue

            base = Path(global_path)
            if artifact_type == "skills":
                candidate = base / search_name
                if candidate.is_dir() and (candidate / "SKILL.md").is_file():
                    matches.append({
                        "name": search_name,
                        "type": "skill",
                        "type_plural": "skills",
                        "path": candidate,
                        "tool": tool_name,
                    })
            else:
                candidate = base / f"{search_name}.md"
                if candidate.is_file():
                    singular = "command" if artifact_type == "commands" else "agent"
                    matches.append({
                        "name": search_name,
                        "type": singular,
                        "type_plural": artifact_type,
                        "path": candidate,
                        "tool": tool_name,
                    })

    return matches


def _find_all_global_artifacts(
    tool_global_dirs: dict[str, dict[str, str]],
    cache: list[dict],
    tools_filter: list[str] | None,
    type_filters: dict[str, Any] | None,
) -> list[dict]:
    """Find all globally imported artifacts that match filters."""
    seen = set()
    results = []

    for entry in cache:
        if tools_filter and entry["tool"] not in tools_filter:
            continue

        name = entry["name"]
        tool_name = entry["tool"]

        if tool_name not in tool_global_dirs:
            continue

        type_paths = tool_global_dirs[tool_name]
        for artifact_type, global_path in type_paths.items():
            if type_filters and artifact_type not in type_filters:
                continue

            base = Path(global_path)
            if artifact_type == "skills":
                candidate = base / name
                if candidate.is_dir() and (candidate / "SKILL.md").is_file():
                    key = str(candidate)
                    if key not in seen:
                        seen.add(key)
                        results.append({
                            "name": name,
                            "type": "skill",
                            "type_plural": "skills",
                            "path": candidate,
                            "tool": tool_name,
                        })
            else:
                candidate = base / f"{name}.md"
                if candidate.is_file():
                    key = str(candidate)
                    if key not in seen:
                        seen.add(key)
                        singular = "command" if artifact_type == "commands" else "agent"
                        results.append({
                            "name": name,
                            "type": singular,
                            "type_plural": artifact_type,
                            "path": candidate,
                            "tool": tool_name,
                        })

    return results


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
    target_str = getattr(args, "target", None)
    global_spelunk = getattr(args, "global_spelunk", False)
    tools_filter_str = getattr(args, "tools", None)

    tools_filter = None
    if tools_filter_str:
        global_tools = load_global_tools()
        vault_tools_dict, _ = load_active_vault_tools()
        tools_filter = [
            resolve_tool_name(t.strip(), extra_tools=global_tools, vault_tools=vault_tools_dict)
            for t in tools_filter_str.split(",")
        ]

    type_filters = resolve_type_filters(args)

    if target_str is None or global_spelunk:
        # Global config spelunk
        if target_str is None and not global_spelunk:
            print("No target specified — spelunking global config directories.\n")
        artifacts = discover_global_artifacts(tools_filter=tools_filter)
    else:
        target = Path(target_str).resolve()
        if not target.exists() or not target.is_dir():
            print(f"Error: Target directory does not exist: {target_str}", file=sys.stderr)
            return 1

        if is_vault(target):
            artifacts = discover_vault_artifacts(target)
            if tools_filter:
                # Tool filter doesn't apply to vault direct scan but we still accept it
                pass
        else:
            artifacts = discover_artifacts(target)
            if tools_filter:
                artifacts = [a for a in artifacts if a["tool"] in tools_filter]

    if type_filters:
        artifacts = _apply_type_filters(artifacts, type_filters)

    if not artifacts:
        label = target_str or "global config"
        print(f"No artifacts found in {label}")
        return 0

    import_cache: dict[str, list[str]] = {}
    if target_str and not global_spelunk:
        target = Path(target_str).resolve()
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

    type_filters = resolve_type_filters(args)
    if type_filters:
        artifacts = _apply_type_filters(artifacts, type_filters)

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

    if args.command == "list":
        return handle_list(args)

    if args.command == "rm":
        return handle_rm(args)

    if args.command in ("project", "proj"):
        proj_cmd = getattr(args, "proj_command", None)
        if proj_cmd is None:
            parser.parse_args(["project", "--help"])
            return 0
        if proj_cmd == "import":
            return handle_proj_import(args)
        if proj_cmd == "rm":
            return handle_proj_rm(args)
        if proj_cmd == "wipe":
            return handle_proj_wipe(args)
        if proj_cmd == "list":
            return handle_proj_list(args)

    if args.command in ("config", "conf"):
        conf_cmd = getattr(args, "conf_command", None)
        if conf_cmd is None:
            parser.parse_args(["config", "--help"])
            return 0
        if conf_cmd == "import":
            return handle_conf_import(args)
        if conf_cmd == "rm":
            return handle_conf_rm(args)
        if conf_cmd == "wipe":
            return handle_conf_wipe(args)
        if conf_cmd == "list":
            return handle_conf_list(args)

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
