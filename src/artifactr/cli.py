"""CLI interface for Artifactr.

This module provides the command-line interface using argparse.
Program logic is decoupled from CLI invocations to allow for future GUI development.
"""

import argparse
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .catalog import (
    add_vaults,
    copy_vault,
    create_vault_directory,
    export_vaults,
    get_default_tool,
    get_default_vault,
    get_vault_by_name_or_path,
    get_vault_hierarchy,
    import_vaults_from_zip,
    init_vault,
    list_tools_info,
    list_vaults,
    name_vault,
    remove_vaults,
    resolve_vaults_for_export,
    select_default,
    select_default_tool,
)
from .config import (
    get_nav_mode,
    load_active_vault_tools,
    load_all_vault_tools,
    load_cwd_vault_tools,
    load_global_tools,
    load_vault_metadata,
    save_global_tools,
    save_vault_metadata,
)
from .creator import create_artifact, create_skill, find_artifact_in_vault, resolve_edit_target, resolve_project_target, resolve_vault_target
from .importer import (
    copy_with_prompt,
    import_artifacts,
    import_artifacts_global,
    remove_from_global_import_cache,
    remove_from_import_cache,
)
from .scanner import (
    discover_artifacts,
    discover_artifacts_by_structure,
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


# Reserved type tokens for `art nav` target resolution
# These take precedence over vault names when used as a bare nav target
_NAV_TYPE_ALIASES: dict[str, str] = {
    "skills": "skills",
    "s": "skills",
    "sk": "skills",
    "commands": "commands",
    "c": "commands",
    "cmd": "commands",
    "com": "commands",
    "agents": "agents",
    "a": "agents",
    "agt": "agents",
}


# Type aliases for [type/]name[/sub/path] specifier parsing (shared across edit, ls, cat, inspect, export)
_TYPE_ALIASES: dict[str, str] = {
    "skill": "skill", "s": "skill", "sk": "skill",
    "command": "command", "c": "command", "cmd": "command", "com": "command",
    "agent": "agent", "a": "agent", "agt": "agent", "ag": "agent",
}


def _parse_artifact_specifier(specifier: str) -> tuple[str | None, str, str | None]:
    """Parse a [type/]name[/sub/path] specifier.

    Returns:
        (artifact_type, name, subpath) where artifact_type and subpath may be None.
    """
    parts = specifier.split("/")
    if parts[0] in _TYPE_ALIASES:
        artifact_type: str | None = _TYPE_ALIASES[parts[0]]
        name = parts[1] if len(parts) > 1 else ""
        subpath = "/".join(parts[2:]) if len(parts) > 2 else None
    else:
        artifact_type = None
        name = parts[0]
        subpath = "/".join(parts[1:]) if len(parts) > 1 else None
    return artifact_type, name, subpath or None


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


def check_import_health(
    artifact_name: str,
    artifact_type: str,
    vault_name: str,
) -> str | None:
    """Check whether an imported artifact's source still exists.

    Returns:
        None if source exists, "source missing" if artifact gone from vault,
        "vault not found" if vault itself is missing.
    """
    vault_path_str = get_vault_by_name_or_path(vault_name)
    if vault_path_str is None:
        return "vault not found"

    vault_path = Path(vault_path_str)
    if not vault_path.is_dir():
        return "vault not found"

    type_to_plural = {"skill": "skills", "command": "commands", "agent": "agents"}
    type_plural = type_to_plural.get(artifact_type, artifact_type + "s")

    if artifact_type == "skill":
        source = vault_path / type_plural / artifact_name / "SKILL.md"
    else:
        source = vault_path / type_plural / f"{artifact_name}.md"

    if not source.exists():
        return "source missing"

    return None


class ArtHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Custom formatter that suppresses the auto-generated subparser list and provides a clean usage line."""

    def _format_action(self, action: argparse.Action) -> str:
        if isinstance(action, argparse._SubParsersAction):
            return ""
        return super()._format_action(action)

    def _format_usage(self, usage: str | None, actions: Any, groups: Any, prefix: str | None) -> str:
        if prefix == "":
            # Called by argparse to compute subparser prog — use default behavior
            return super()._format_usage(usage, actions, groups, prefix)
        return "usage: art [-h] [--version] <command> [<args>]\n\n"


class ArtArgumentParser(argparse.ArgumentParser):
    """ArgumentParser subclass with optional show-help-on-error behavior."""

    def __init__(self, *args: Any, show_help_on_error: bool = False, **kwargs: Any) -> None:
        self.show_help_on_error = show_help_on_error
        super().__init__(*args, **kwargs)

    def error(self, message: str) -> None:
        if self.show_help_on_error:
            self.print_help(sys.stderr)
        super().error(message)


def make_help(
    summary: str,
    aliases: list[str] | None = None,
    workflows: str | None = None,
    see_also: list[tuple[str, str]] | None = None,
    notes: str | None = None,
) -> dict:
    """Build standardized help kwargs for add_parser() calls.

    Returns a dict with description, epilog, and formatter_class keys suitable
    for unpacking with ** into add_parser().
    """
    description = summary
    if aliases:
        description += f"\n\nAliases: {', '.join(aliases)}"

    epilog_sections = []
    if workflows:
        epilog_sections.append(f"Workflows:\n  {workflows}")
    if see_also:
        lines = ["See Also:"]
        for cmd, desc in see_also:
            lines.append(f"  {cmd}  {desc}")
        epilog_sections.append("\n".join(lines))
    if notes:
        epilog_sections.append(f"Notes:\n  {notes}")

    epilog = "\n\n".join(epilog_sections) if epilog_sections else None

    return {
        "description": description,
        "epilog": epilog,
        "formatter_class": argparse.RawDescriptionHelpFormatter,
    }


def create_parser() -> ArtArgumentParser:
    """Create and configure the argument parser with all subcommands."""
    parser = ArtArgumentParser(
        prog="art",
        description=(
            "Manage AI artifacts across multiple configurations, tools, & repositories.\n"
            "Commands target the active vault/tool by default (see: art vault select, art tool select)."
        ),
        epilog=(
            "Vault Operations:\n"
            "  ls              List artifacts in a vault (or files within an artifact)\n"
            "  rm              Remove artifacts from a vault\n"
            "  copy     (cp)   Copy artifacts within or across vaults\n"
            "  store    (st)   Store artifacts from a directory or zip into a vault\n"
            "  edit     (ed)   Edit an artifact in your editor\n"
            "  cat             Print artifact primary file content to stdout\n"
            "  inspect         Display artifact frontmatter and file tree\n"
            "  export          Export an artifact as a zip archive\n"
            "  create   (cr)   Create new artifacts (skill, command, agent)\n"
            "\n"
            "Namespaces:\n"
            "  vault    (v)    Manage vaults (add, init, rm, name, select, ls, copy, export, import)\n"
            "  tool     (t)    Manage tools (select, ls, add, rm, info)\n"
            "  project  (p)    Project-side artifact operations (import, rm, wipe, ls, link, unlink)\n"
            "  config   (c)    Tool-specific global configs & artifactr settings (import, rm, wipe, ls, link, unlink, edit)\n"
            "  shell           Shell integration utilities (setup)\n"
            "\n"
            "Navigation:\n"
            "  nav             Navigate to a vault or artifact-type directory\n"
            "\n"
            "Discovery:\n"
            "  spelunk  (sp)   Discover artifacts in a directory, vault, or global config\n"
        ),
        formatter_class=ArtHelpFormatter,
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands", parser_class=ArtArgumentParser)

    # vault command with subcommands
    vault_parser = subparsers.add_parser(
        "vault", aliases=["v"], help="Manage vaults",
        show_help_on_error=True,
        **make_help(
            summary="Manage artifact vaults — named directories organizing your AI artifacts.",
            aliases=["v"],
        ),
    )
    vault_subparsers = vault_parser.add_subparsers(dest="vault_command", parser_class=ArtArgumentParser)

    # vault add (alphabetical: 1st)
    vault_add = vault_subparsers.add_parser(
        "add", help="Add vaults to catalog",
        show_help_on_error=True,
        **make_help(
            summary="Add an existing vault directory to the catalog.",
            notes="Paths must already exist on disk.",
        ),
    )
    vault_add.add_argument("paths", nargs="+", help="Vault paths to add")
    vault_add.add_argument(
        "--name", help="Name for the vault (only when adding a single vault)"
    )
    vault_add.add_argument(
        "--set-default", action="store_true",
        help="Set the added vault as the default",
    )

    # vault init (alphabetical: 2nd)
    vault_init = vault_subparsers.add_parser(
        "init", aliases=["create", "cr"], help="Initialize a new vault directory",
        show_help_on_error=True,
        **make_help(
            summary="Create and register a new vault directory.",
            aliases=["create", "cr"],
            notes="Creates the directory if it does not exist.",
        ),
    )
    vault_init.add_argument("target_dir", help="Path to the vault directory")
    vault_init.add_argument(
        "--name", help="Name for the vault",
    )
    vault_init.add_argument(
        "--set-default", action="store_true",
        help="Set the initialized vault as the default",
    )
    vault_init.add_argument(
        "-y", "--yes", action="store_true",
        help="Auto-confirm directory creation without prompting",
    )

    # vault ls (alphabetical: 3rd)
    vault_list = vault_subparsers.add_parser(
        "ls", aliases=["list"], help="List all vaults",
        **make_help(
            summary="List all vaults in the catalog.",
            aliases=["list"],
        ),
    )
    vault_list.add_argument(
        "-a", "--all", action="store_true", dest="show_all",
        help="Show full vault hierarchy with artifacts",
    )

    # vault name (alphabetical: 4th)
    vault_name = vault_subparsers.add_parser(
        "name", help="Set or change a vault's name",
        show_help_on_error=True,
        **make_help(summary="Set or change a vault's display name."),
    )
    vault_name.add_argument("vault", help="Vault name or path to rename")
    vault_name.add_argument("name", help="New name for the vault")

    # vault rm (alphabetical: 5th)
    vault_rm = vault_subparsers.add_parser(
        "rm", help="Remove vaults from catalog",
        show_help_on_error=True,
        **make_help(summary="Remove a vault from the catalog."),
    )
    vault_rm.add_argument("paths", nargs="+", help="Vault paths to remove")

    # vault select (alphabetical: 6th)
    vault_select = vault_subparsers.add_parser(
        "select", help="Set default vault",
        show_help_on_error=True,
        **make_help(summary="Set the default vault."),
    )
    vault_select.add_argument("path", help="Vault name or path to set as default")

    # vault copy (alphabetical: after select)
    vault_copy_parser = vault_subparsers.add_parser(
        "copy", aliases=["cp"], help="Copy a vault to a new location",
        show_help_on_error=True,
        **make_help(
            summary=(
                "Duplicate a vault to a new path and auto-register the copy in the catalog. "
                "Source can be a registered vault name or a filesystem path. "
                "If dest contains no path separator it is treated as a new vault name "
                "and placed under the configured vaults directory."
            ),
            aliases=["cp"],
            workflows="art vault copy <source> <dest> → art vault ls",
            see_also=[
                ("art vault export", "Pack one or more vaults into a portable .zip archive"),
                ("art copy", "Copy individual artifacts within or across vaults"),
            ],
            notes=(
                "Default scope: skills/, commands/, agents/, vault.yaml only. "
                "Use --all to include additional files (always excludes .git/)."
            ),
        ),
    )
    vault_copy_parser.add_argument(
        "source",
        help="Source vault name or path",
    )
    vault_copy_parser.add_argument(
        "dest",
        help=(
            "Destination path or bare name. "
            "No path separator → placed at <config_dir>/vaults/<name>/. "
            "Path with separators → used verbatim."
        ),
    )
    vault_copy_parser.add_argument(
        "-a", "--all", action="store_true", dest="copy_all",
        help="Copy all vault contents except .git/ (default: artifact dirs + vault.yaml only)",
    )

    # vault export
    vault_export_parser = vault_subparsers.add_parser(
        "export", help="Export vaults to a zip archive",
        show_help_on_error=True,
        **make_help(
            summary=(
                "Export one or more registered vaults to a self-contained .zip archive. "
                "The archive contains per-vault artifact directories, vault.yaml files, "
                "and a manifest.yaml at the root for use with 'art vault import'."
            ),
            workflows="art vault export <vaults> bundle.zip → art vault import bundle.zip",
            see_also=[
                ("art vault import", "Extract and register vaults from a .zip archive"),
                ("art vault copy", "Duplicate a vault locally without archiving"),
            ],
            notes=(
                "Vaults spec: comma-separated names (vault-1,vault-2), glob pattern ('claude-*'), or --all. "
                "Quote glob patterns to prevent shell expansion."
            ),
        ),
    )
    vault_export_parser.add_argument(
        "vaults_spec", nargs="?", default=None,
        help="Comma-separated vault names or glob pattern (e.g. 'claude-*'); omit when using --all",
    )
    vault_export_parser.add_argument(
        "output",
        help="Output .zip file path (must not already exist)",
    )
    vault_export_parser.add_argument(
        "-a", "--all", action="store_true", dest="export_all",
        help="Export all registered vaults",
    )

    # vault import
    vault_import_parser = vault_subparsers.add_parser(
        "import", help="Import vaults from a zip archive",
        show_help_on_error=True,
        **make_help(
            summary=(
                "Extract vaults from a .zip archive created by 'art vault export' and register them. "
                "Reads manifest.yaml from the archive to determine vault names and directory layout. "
                "Each vault is extracted as a direct subdirectory of the destination."
            ),
            workflows="art vault export bundle.zip → art vault import bundle.zip",
            see_also=[
                ("art vault export", "Create a portable .zip archive of one or more vaults"),
                ("art vault ls", "Confirm newly imported vaults are registered"),
            ],
            notes=(
                "Default destination: <config_dir>/vaults/. "
                "Confirmation is required unless -y/--yes is passed. "
                "Vaults that would create name or path conflicts are skipped with an error; others still import."
            ),
        ),
    )
    vault_import_parser.add_argument(
        "archive",
        help="Path to the .zip archive produced by 'art vault export'",
    )
    vault_import_parser.add_argument(
        "dest", nargs="?", default=None,
        help="Destination directory for extracted vaults (default: <config_dir>/vaults/)",
    )
    vault_import_parser.add_argument(
        "-y", "--yes", action="store_true",
        help="Skip confirmation prompt and extract immediately",
    )

    # tool command with subcommands
    tool_parser = subparsers.add_parser(
        "tool", aliases=["t"], help="Manage tools",
        show_help_on_error=True,
        **make_help(
            summary="Manage AI tool definitions and their artifact directory mappings.",
            aliases=["t"],
        ),
    )
    tool_subparsers = tool_parser.add_subparsers(dest="tool_command", parser_class=ArtArgumentParser)

    # tool add (alphabetical: 1st)
    tool_add = tool_subparsers.add_parser(
        "add", help="Add a custom tool definition",
        **make_help(summary="Register a custom tool definition in the catalog."),
    )
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
    tool_add.add_argument(
        "-V", "--vault", action="append", default=None, dest="vaults",
        help="Store in vault's metadata — comma-separated or repeatable",
    )
    tool_add.add_argument(
        "-g", "--global", action="store_true", dest="global_config",
        help="Explicitly store in global config (default behavior)",
    )

    # tool info (alphabetical: 2nd)
    tool_info = tool_subparsers.add_parser(
        "info", help="Show tool information and catalog",
        **make_help(summary="Display tool configuration and catalog details."),
    )
    tool_info.add_argument("name", nargs="?", help="Tool identifier to display (omit for catalog view)")
    tool_info.add_argument(
        "-V", "--vault", action="append", default=None, dest="vaults",
        help="Filter to vault tools — comma-separated or repeatable",
    )
    tool_info.add_argument(
        "-a", "--all", action="store_true", dest="show_all",
        help="Show all tool definitions from all sources",
    )
    tool_info.add_argument(
        "-g", "--global", action="store_true", dest="global_filter",
        help="Filter to global config tools only",
    )

    # tool ls (alphabetical: 3rd)
    tool_list = tool_subparsers.add_parser(
        "ls", aliases=["list"], help="List supported tools",
        **make_help(
            summary="List all registered tools across sources.",
            aliases=["list"],
        ),
    )
    tool_list.add_argument(
        "-V", "--vault", action="append", default=None, dest="vaults",
        help="Use tools from this vault — comma-separated or repeatable",
    )
    tool_list.add_argument(
        "-a", "--all", action="store_true", dest="show_all",
        help="List tools from all catalog vaults and global config",
    )

    # tool rm (alphabetical: 4th)
    tool_rm = tool_subparsers.add_parser(
        "rm", help="Remove a custom tool definition",
        **make_help(summary="Remove a custom tool definition from the catalog."),
    )
    tool_rm.add_argument("name", help="Tool identifier to remove")
    tool_rm.add_argument("-V", "--vault", help="Remove from vault's metadata instead of global config")
    tool_rm.add_argument(
        "-g", "--global", action="store_true", dest="global_config",
        help="Explicitly remove from global config (default behavior)",
    )

    # tool select (alphabetical: 5th)
    tool_select = tool_subparsers.add_parser(
        "select", help="Set default tool",
        **make_help(summary="Set the default tool."),
    )
    tool_select.add_argument("name", help="Tool name")

    # ls command (vault-side)
    list_parser = subparsers.add_parser(
        "ls", aliases=["list"], help="List artifacts in a vault",
        **make_help(
            summary=(
                "List artifacts stored in a vault. "
                "Optionally supply an artifact name (or [type/]name) to list files within that artifact."
            ),
            aliases=["list"],
        ),
    )
    list_parser.add_argument(
        "artifact_name", nargs="?", default=None,
        help="Optional artifact name ([type/]name) to list files within a directory-based artifact",
    )
    list_parser.add_argument(
        "-V", "--vault", action="append", default=None, dest="vaults",
        help="Vault to list from — comma-separated or repeatable (default: default vault)",
    )
    add_type_filter_args(list_parser)

    # rm command (vault-side)
    rm_parser = subparsers.add_parser(
        "rm", help="Remove artifacts from a vault",
        show_help_on_error=True,
        **make_help(summary="Remove artifacts from a vault by name."),
    )
    rm_parser.add_argument(
        "names", nargs="+", help="Artifact names to remove (supports type/name prefix)"
    )
    rm_parser.add_argument(
        "-V", "--vault", help="Vault to remove from (default: default vault)"
    )
    rm_parser.add_argument(
        "-f", "--force", action="store_true",
        help="Skip confirmation prompt",
    )

    # spelunk command
    spelunk_parser = subparsers.add_parser(
        "spelunk", aliases=["sp"], help="Discover artifacts in a directory, vault, or global config",
        **make_help(
            summary="Discover artifacts in a directory, vault, or global config.",
            aliases=["sp"],
        ),
    )
    spelunk_parser.add_argument("target", nargs="?", default=None, help="Path to directory to probe")
    spelunk_parser.add_argument(
        "-g", "--global", action="store_true", dest="global_spelunk",
        help="Explicitly scan global config directories",
    )
    spelunk_parser.add_argument(
        "--tools", help="Comma-separated list of tools to filter to",
    )
    spelunk_parser.add_argument(
        "-d", "--depth", type=int, default=2,
        help="Max directory depth for artifact scanning (default: 2)",
    )
    spelunk_parser.add_argument(
        "--format", choices=["human", "json", "yaml", "md", "markdown"], default="human",
        help="Output format (default: human)",
    )
    spelunk_parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Include DESCRIPTION column in human-format output",
    )
    add_type_filter_args(spelunk_parser)

    # nav command
    nav_parser = subparsers.add_parser(
        "nav", help="Navigate to a vault or artifact-type directory",
        **make_help(
            summary=(
                "Navigate to a vault or artifact-type directory. "
                "Target can be a type alias (skills, s, sk, commands, c, cmd, agents, a, agt), "
                "a registered vault name, or a vault/type path. "
                "Omit target to navigate to the default vault root."
            ),
            workflows="art shell setup → art nav [target]",
            see_also=[
                ("art shell setup", "Install shell wrapper for seamless cd behavior"),
                ("art vault ls", "List registered vaults and their paths"),
            ],
            notes=(
                "Set a default mode with nav_mode in config.yaml (wrapper|spawn|window|print). "
                "Flags --print, --spawn, -w override the config for a single invocation."
            ),
        ),
    )
    nav_parser.add_argument(
        "target", nargs="?", default=None,
        help=(
            "Type alias (skills/s/sk, commands/c/cmd/com, agents/a/agt), "
            "vault name, or vault/type path (default: default vault root)"
        ),
    )
    nav_parser.add_argument(
        "--print", action="store_true", dest="nav_print",
        help="Print resolved path to stdout — consumed by the shell wrapper function installed by 'art shell setup'",
    )
    nav_parser.add_argument(
        "-s", "--spawn", action="store_true",
        help="Launch an interactive subshell with its cwd set to the resolved path",
    )
    nav_parser.add_argument(
        "-w", "--window", action="store_true",
        help="Open a new terminal window at the resolved path (best-effort; uses $TERMINAL then platform fallbacks)",
    )

    # shell namespace
    shell_parser = subparsers.add_parser(
        "shell", help="Shell integration utilities",
        show_help_on_error=True,
        **make_help(
            summary="Shell integration utilities for Artifactr.",
            see_also=[("art nav", "Navigate to vault/type directories using the installed wrapper")],
        ),
    )
    shell_subparsers = shell_parser.add_subparsers(dest="shell_command", parser_class=ArtArgumentParser)

    shell_setup = shell_subparsers.add_parser(
        "setup", help="Install shell wrapper function into rc file",
        **make_help(
            summary=(
                "Detect your shell and append the art() wrapper function to its rc file. "
                "The wrapper intercepts 'art nav' invocations and evaluates the result as a cd command, "
                "enabling seamless directory navigation from your shell."
            ),
            workflows="art shell setup → source <rcfile> → art nav [target]",
            see_also=[("art nav", "Use the wrapper after setup to navigate vaults")],
            notes=(
                "Supports bash, zsh, sh, fish, and PowerShell. "
                "Fish writes a standalone ~/.config/fish/functions/art.fish instead of appending to config.fish."
            ),
        ),
    )
    shell_setup.add_argument(
        "-y", "--yes", action="store_true",
        help="Skip all confirmation and preview prompts — write snippet immediately",
    )

    # project namespace (art project / art proj)
    project_parser = subparsers.add_parser(
        "project", aliases=["proj", "p"], help="Project-side artifact operations",
        show_help_on_error=True,
        **make_help(
            summary="Manage artifacts within a project (import, list, remove, link).",
            aliases=["proj", "p"],
        ),
    )
    proj_subparsers = project_parser.add_subparsers(dest="proj_command", parser_class=ArtArgumentParser)

    # proj import (alphabetical: 1st)
    proj_import = proj_subparsers.add_parser(
        "import", help="Import artifacts from vault into a project",
        **make_help(
            summary="Copy or symlink vault artifacts into a project directory.",
            workflows="art proj import → art proj link → art proj unlink",
            see_also=[("art config import", "Same operation targeting global tool config dirs")],
        ),
    )
    proj_import.add_argument(
        "target", nargs="?", default=None, help="Path to target git repository (default: cwd)"
    )
    proj_import.add_argument(
        "-V", "--vault", action="append", default=None, dest="vaults",
        help="Vault to import from — comma-separated or repeatable (default: default vault)",
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
    proj_import.add_argument(
        "-y", "--yes", action="store_true",
        help="Auto-confirm prompts (e.g., non-git target)",
    )
    add_type_filter_args(proj_import)

    # proj link (alphabetical: 2nd)
    proj_link = proj_subparsers.add_parser(
        "link", aliases=["ln"], help="Link imported artifacts to vault sources (symlink)",
        **make_help(
            summary="Convert imported copies to symlinks pointing at vault sources.",
            aliases=["ln"],
            workflows="art proj import → art proj link → art proj unlink",
            see_also=[("art proj unlink", "Replace symlinks with copies")],
        ),
    )
    proj_link.add_argument("names", nargs="*", help="Artifact names or glob patterns")
    proj_link.add_argument(
        "-a", "--all", action="store_true", dest="link_all",
        help="Link all imported artifacts",
    )
    proj_link.add_argument(
        "-f", "--force", action="store_true",
        help="Auto-backup and link without prompting on diff",
    )
    proj_link.add_argument(
        "-V", "--vault", action="append", default=None, dest="vaults",
        help="Scope to vault(s) — comma-separated or repeatable (default: default vault)",
    )
    proj_link.add_argument(
        "--target", default=None, help="Project path (default: cwd)",
    )
    add_type_filter_args(proj_link, allow_names=False)

    # proj ls (alphabetical: 3rd)
    proj_list = proj_subparsers.add_parser(
        "ls", aliases=["list"], help="Show imported artifacts in a project",
        **make_help(
            summary="List artifacts imported into this project.",
            aliases=["list"],
        ),
    )
    proj_list.add_argument(
        "--target", default=None, help="Project path (default: cwd)",
    )
    proj_list.add_argument(
        "--tools", help="Comma-separated tool filter",
    )
    proj_list.add_argument(
        "-V", "--vault", action="append", default=None, dest="vaults",
        help="Filter by vault — comma-separated or repeatable",
    )
    add_type_filter_args(proj_list)

    # proj rm (alphabetical: 4th)
    proj_rm = proj_subparsers.add_parser(
        "rm", help="Remove imported artifacts from a project",
        **make_help(summary="Remove specific imported artifacts from a project."),
    )
    proj_rm.add_argument("names", nargs="+", help="Artifact names to remove")
    proj_rm.add_argument(
        "--target", default=None, help="Project path (default: cwd)",
    )
    proj_rm.add_argument(
        "--tools", help="Comma-separated tool filter",
    )
    proj_rm.add_argument(
        "-V", "--vault", action="append", default=None, dest="vaults",
        help="Filter by vault — comma-separated or repeatable",
    )
    proj_rm.add_argument(
        "-f", "--force", action="store_true",
        help="Skip confirmation prompt",
    )
    add_type_filter_args(proj_rm, allow_names=False)

    # proj unlink (alphabetical: 5th)
    proj_unlink = proj_subparsers.add_parser(
        "unlink", aliases=["uln"], help="Unlink artifacts (replace symlinks with copies)",
        **make_help(
            summary="Replace symlinks with standalone copies.",
            aliases=["uln"],
            see_also=[("art proj link", "Convert copies to symlinks")],
        ),
    )
    proj_unlink.add_argument("names", nargs="*", help="Artifact names or glob patterns")
    proj_unlink.add_argument(
        "-a", "--all", action="store_true", dest="unlink_all",
        help="Unlink all imported artifacts",
    )
    proj_unlink.add_argument(
        "-V", "--vault", action="append", default=None, dest="vaults",
        help="Scope to vault(s) — comma-separated or repeatable (default: default vault)",
    )
    proj_unlink.add_argument(
        "--target", default=None, help="Project path (default: cwd)",
    )
    add_type_filter_args(proj_unlink, allow_names=False)

    # proj wipe (alphabetical: 6th)
    proj_wipe = proj_subparsers.add_parser(
        "wipe", help="Clear all imported artifacts from a project",
        **make_help(
            summary="Remove all imported artifacts and clear the import cache.",
            notes="Removes all imported artifacts and clears the import cache.",
        ),
    )
    proj_wipe.add_argument(
        "--target", default=None, help="Project path (default: cwd)",
    )
    proj_wipe.add_argument(
        "--tools", help="Comma-separated tool filter",
    )
    proj_wipe.add_argument(
        "-V", "--vault", action="append", default=None, dest="vaults",
        help="Filter by vault — comma-separated or repeatable",
    )
    proj_wipe.add_argument(
        "-f", "--force", action="store_true",
        help="Skip confirmation prompt",
    )
    add_type_filter_args(proj_wipe)

    # config namespace (art config / art conf)
    config_parser = subparsers.add_parser(
        "config", aliases=["conf", "c"],
        help="Tool-specific global configs & artifactr settings",
        show_help_on_error=True,
        **make_help(
            summary="Manage tool-specific global configs and artifactr settings.",
            aliases=["conf", "c"],
        ),
    )
    conf_subparsers = config_parser.add_subparsers(dest="conf_command", parser_class=ArtArgumentParser)

    # conf edit (alphabetical: 1st)
    conf_subparsers.add_parser(
        "edit", aliases=["ed"], help="Open artifactr's global YAML config in editor",
        **make_help(
            summary="Open artifactr's global YAML configuration in your editor.",
            aliases=["ed"],
            see_also=[("art tool add", "Add a custom tool to the config")],
        ),
    )

    # conf import (alphabetical: 2nd)
    conf_import = conf_subparsers.add_parser(
        "import", help="Import artifacts into tool-specific global config directories (e.g., ~/.claude/commands/)",
        **make_help(
            summary="Copy or symlink vault artifacts into global tool config directories.",
            see_also=[("art proj import", "Same operation targeting a project directory")],
        ),
    )
    conf_import.add_argument(
        "-V", "--vault", action="append", default=None, dest="vaults",
        help="Vault to import from — comma-separated or repeatable (default: default vault)",
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

    # conf link (alphabetical: 3rd)
    conf_link = conf_subparsers.add_parser(
        "link", aliases=["ln"], help="Link globally imported artifacts to vault sources (symlink)",
        **make_help(
            summary="Convert globally imported copies to symlinks.",
            aliases=["ln"],
        ),
    )
    conf_link.add_argument("names", nargs="*", help="Artifact names or glob patterns")
    conf_link.add_argument(
        "-a", "--all", action="store_true", dest="link_all",
        help="Link all globally imported artifacts",
    )
    conf_link.add_argument(
        "-f", "--force", action="store_true",
        help="Auto-backup and link without prompting on diff",
    )
    conf_link.add_argument(
        "-V", "--vault", action="append", default=None, dest="vaults",
        help="Scope to vault(s) — comma-separated or repeatable (default: default vault)",
    )
    add_type_filter_args(conf_link, allow_names=False)

    # conf ls (alphabetical: 4th)
    conf_list = conf_subparsers.add_parser(
        "ls", aliases=["list"], help="Show globally imported artifacts",
        **make_help(
            summary="List artifacts imported into global tool config directories.",
            aliases=["list"],
        ),
    )
    conf_list.add_argument(
        "--tools", help="Comma-separated tool filter",
    )
    conf_list.add_argument(
        "-V", "--vault", action="append", default=None, dest="vaults",
        help="Filter by vault — comma-separated or repeatable",
    )
    add_type_filter_args(conf_list)

    # conf rm (alphabetical: 5th)
    conf_rm = conf_subparsers.add_parser(
        "rm", help="Remove globally imported artifacts",
        **make_help(summary="Remove specific globally imported artifacts."),
    )
    conf_rm.add_argument("names", nargs="+", help="Artifact names to remove")
    conf_rm.add_argument(
        "--tools", help="Comma-separated tool filter",
    )
    conf_rm.add_argument(
        "-V", "--vault", action="append", default=None, dest="vaults",
        help="Filter by vault — comma-separated or repeatable",
    )
    conf_rm.add_argument(
        "-f", "--force", action="store_true",
        help="Skip confirmation prompt",
    )
    add_type_filter_args(conf_rm, allow_names=False)

    # conf unlink (alphabetical: 6th)
    conf_unlink = conf_subparsers.add_parser(
        "unlink", aliases=["uln"], help="Unlink globally imported artifacts (replace symlinks with copies)",
        **make_help(
            summary="Replace global symlinks with standalone copies.",
            aliases=["uln"],
        ),
    )
    conf_unlink.add_argument("names", nargs="*", help="Artifact names or glob patterns")
    conf_unlink.add_argument(
        "-a", "--all", action="store_true", dest="unlink_all",
        help="Unlink all globally imported artifacts",
    )
    conf_unlink.add_argument(
        "-V", "--vault", action="append", default=None, dest="vaults",
        help="Scope to vault(s) — comma-separated or repeatable (default: default vault)",
    )
    add_type_filter_args(conf_unlink, allow_names=False)

    # conf wipe (alphabetical: 7th)
    conf_wipe = conf_subparsers.add_parser(
        "wipe", help="Clear all globally imported artifacts",
        **make_help(summary="Remove all globally imported artifacts and clear the global cache."),
    )
    conf_wipe.add_argument(
        "--tools", help="Comma-separated tool filter",
    )
    conf_wipe.add_argument(
        "-V", "--vault", action="append", default=None, dest="vaults",
        help="Filter by vault — comma-separated or repeatable",
    )
    conf_wipe.add_argument(
        "-f", "--force", action="store_true",
        help="Skip confirmation prompt",
    )
    add_type_filter_args(conf_wipe)

    # copy command (art copy / art cp)
    copy_parser = subparsers.add_parser(
        "copy", aliases=["cp"], help="Copy artifacts within or across vaults",
        show_help_on_error=True,
        **make_help(
            summary=(
                "Copy one or more artifacts within or across vaults using cp-style positional syntax. "
                "Source format: [vault/][type/]name-or-glob. "
                "Glob wildcards (* ? [...]) expand to all matching artifacts. "
                "Frontmatter 'name:' fields are searched as a fallback when no filename match is found."
            ),
            aliases=["cp"],
            see_also=[
                ("art vault copy", "Duplicate an entire vault to a new location"),
                ("art ls", "List artifacts available in a vault"),
                ("art store", "Capture project artifacts into a vault"),
            ],
            notes=(
                "Destination: trailing slash or a registered vault name = copy into that vault. "
                "No trailing slash and unregistered name = rename/duplicate within the source vault. "
                "Type prefixes: s/sk/skills, c/cmd/com/commands, a/agt/agents."
            ),
        ),
    )
    copy_parser.add_argument(
        "source",
        help=(
            "Source artifact specifier: [vault/][type/]name-or-glob. "
            "Examples: my-skill, skills/my-skill, vault-1/my-skill, vault-1/skills/my-skill, skills/*"
        ),
    )
    copy_parser.add_argument(
        "dest",
        help=(
            "Destination: 'vault-name/' or 'vault-name' (container) copies into the vault; "
            "'vault/new-name' copies to a named vault with a new name; "
            "bare 'new-name' duplicates within the source vault."
        ),
    )

    # store command
    store_parser = subparsers.add_parser(
        "store", aliases=["st"], help="Store artifacts from a directory into a vault",
        **make_help(
            summary="Discover and store artifacts from a directory into a vault.",
            aliases=["st"],
        ),
    )
    store_parser.add_argument("target_dir", nargs="?", default=None, help="Path to directory containing artifacts")
    store_parser.add_argument(
        "-V", "--vault", action="append", default=None, dest="vaults",
        help="Vault to store into — comma-separated or repeatable (default: default vault)",
    )
    store_parser.add_argument(
        "-g", "--global", action="store_true", dest="global_store",
        help="Store from global tool config directories",
    )
    store_parser.add_argument(
        "--tools", help="Comma-separated list of tools to filter",
    )
    store_parser.add_argument(
        "-f", "--force", action="store_true",
        help="Overwrite existing artifacts in the vault without prompting",
    )
    add_type_filter_args(store_parser)

    # edit command
    edit_parser = subparsers.add_parser(
        "edit", aliases=["ed"], help="Edit an artifact in your editor",
        show_help_on_error=True,
        **make_help(
            summary=(
                "Open an artifact's file in your editor. "
                "Accepts [type/]name[/sub/path] or the legacy two-positional form (type name). "
                "Type is auto-detected when omitted."
            ),
            aliases=["ed"],
            notes=(
                "Use -i to force the file picker for skills; -m to always open SKILL.md directly; "
                "-n <path> to create a new file within the skill."
            ),
        ),
    )
    edit_parser.add_argument(
        "artifact", nargs="+",
        help="Artifact specifier: [type/]name[/sub/path], or legacy: type name",
    )
    edit_parser.add_argument(
        "-V", "--vault", help="Target vault (name or path)",
    )
    edit_parser.add_argument(
        "-H", "--here", action="store_true",
        help="Edit in current project instead of vault",
    )
    edit_parser.add_argument(
        "--tools",
        help="Comma-separated tool list (used with --here)",
    )
    edit_parser.add_argument(
        "-i", "--interactive", action="store_true",
        help="Force interactive file picker for directory-based artifacts (skills)",
    )
    edit_parser.add_argument(
        "-m", "--main", action="store_true",
        help="Open the primary file (SKILL.md) directly, bypassing the file picker",
    )
    edit_parser.add_argument(
        "-n", "--new-file", dest="new_file", metavar="PATH",
        help="Create a new file at relative PATH within the skill directory and open it",
    )

    # cat command
    cat_parser = subparsers.add_parser(
        "cat", help="Print artifact primary file content to stdout",
        **make_help(
            summary=(
                "Print the raw content of an artifact's primary file to stdout. "
                "Accepts [type/]name[/sub/path] specifier; sub-path supported for skills."
            ),
        ),
    )
    cat_parser.add_argument(
        "artifact", help="Artifact specifier: [type/]name[/sub/path]",
    )
    cat_parser.add_argument(
        "-V", "--vault", help="Target vault (name or path)",
    )
    cat_parser.add_argument(
        "-H", "--here", action="store_true",
        help="Resolve artifact from current project instead of vault",
    )
    cat_parser.add_argument(
        "--tools", help="Comma-separated tool list (used with --here)",
    )

    # inspect command
    inspect_parser = subparsers.add_parser(
        "inspect", help="Display artifact frontmatter and file tree",
        **make_help(
            summary=(
                "Display structured frontmatter metadata and (for skills) the file tree "
                "of all files within the artifact directory."
            ),
        ),
    )
    inspect_parser.add_argument(
        "artifact", help="Artifact specifier: [type/]name",
    )
    inspect_parser.add_argument(
        "-V", "--vault", help="Target vault (name or path)",
    )
    inspect_parser.add_argument(
        "-H", "--here", action="store_true",
        help="Resolve artifact from current project instead of vault",
    )
    inspect_parser.add_argument(
        "--tools", help="Comma-separated tool list (used with --here)",
    )

    # export command
    export_parser = subparsers.add_parser(
        "export", help="Export an artifact as a zip archive",
        **make_help(
            summary=(
                "Package a single artifact as a portable .zip archive. "
                "Skill directories are zipped with their full structure; "
                "commands/agents are wrapped in a named directory."
            ),
        ),
    )
    export_parser.add_argument(
        "artifact", help="Artifact specifier: [type/]name",
    )
    export_parser.add_argument(
        "-V", "--vault", help="Target vault (name or path)",
    )
    export_parser.add_argument(
        "-o", "--output", metavar="PATH",
        help="Output zip file path (default: <cwd>/<artifact-name>.zip)",
    )

    # create command with subcommands
    create_parser = subparsers.add_parser(
        "create", aliases=["cr"], help="Create new artifacts",
        show_help_on_error=True,
        **make_help(
            summary="Create new skills, commands, or agents from the command line.",
            aliases=["cr"],
        ),
    )
    create_subparsers = create_parser.add_subparsers(dest="create_command", parser_class=ArtArgumentParser)

    # create agent (alphabetical: 1st)
    create_agent_parser = create_subparsers.add_parser(
        "agent", aliases=["a", "agt", "ag"], help="Create a new agent",
        show_help_on_error=True,
        **make_help(
            summary="Create a new agent artifact.",
            aliases=["a", "agt", "ag"],
        ),
    )
    create_agent_parser.add_argument(
        "agent_name", help="Agent identifier"
    )
    create_agent_parser.add_argument(
        "-n", "--name", dest="display_name",
        help="Override the frontmatter display name",
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
        "-V", "--vault", action="append", default=None, dest="vaults",
        help="Target vault — comma-separated or repeatable (name or path)",
    )
    create_agent_parser.add_argument(
        "--tools",
        help="Comma-separated tool list (used with --here)",
    )

    # create command (alphabetical: 2nd)
    create_command_parser = create_subparsers.add_parser(
        "command", aliases=["c", "cmd", "com"], help="Create a new command",
        show_help_on_error=True,
        **make_help(
            summary="Create a new command artifact.",
            aliases=["c", "cmd", "com"],
        ),
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
        "-V", "--vault", action="append", default=None, dest="vaults",
        help="Target vault — comma-separated or repeatable (name or path)",
    )
    create_command_parser.add_argument(
        "--tools",
        help="Comma-separated tool list (used with --here)",
    )

    # create skill (alphabetical: 3rd)
    create_skill_parser = create_subparsers.add_parser(
        "skill", aliases=["s", "sk"], help="Create a new skill",
        show_help_on_error=True,
        **make_help(
            summary="Create a new skill artifact.",
            aliases=["s", "sk"],
        ),
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
        "-V", "--vault", action="append", default=None, dest="vaults",
        help="Target vault — comma-separated or repeatable (name or path)",
    )
    create_skill_parser.add_argument(
        "--tools",
        help="Comma-separated tool list (used with --here)",
    )

    return parser


def _load_vault_tools_for_import(args: argparse.Namespace, vault_path_str: str | None = None) -> tuple[dict, dict]:
    """Load global and vault tools for import operations.

    Args:
        args: Parsed arguments (checks for .vaults or .vault).
        vault_path_str: If provided, use this vault path directly.
    """
    from .tools import reload_registry

    global_tools = load_global_tools()
    vault_tools: dict[str, dict] = {}

    if vault_path_str:
        meta = load_vault_metadata(vault_path_str)
        vault_tools = meta.get("tools", {})
    else:
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


def _list_skill_files(skill_dir: Path) -> list[Path]:
    """List all files in a skill directory, SKILL.md first, then rest alphabetically."""
    main_file = skill_dir / "SKILL.md"
    all_files: list[Path] = []
    if main_file.exists():
        all_files.append(main_file)
    for p in sorted(skill_dir.rglob("*")):
        if p.is_file() and p != main_file:
            all_files.append(p)
    return all_files


def _print_skill_file_listing(skill_dir: Path) -> None:
    """Print all files in a skill directory, SKILL.md first with (main) label."""
    files = _list_skill_files(skill_dir)
    for f in files:
        rel = f.relative_to(skill_dir)
        if f.name == "SKILL.md" and f.parent == skill_dir:
            print(f"  {rel}  (main)")
        else:
            print(f"  {rel}")


def handle_list(args: argparse.Namespace) -> int:
    """Handle the art list command (vault-side listing)."""
    artifact_name_arg = getattr(args, "artifact_name", None)

    # If an artifact name is given, list files within that artifact
    if artifact_name_arg is not None:
        artifact_type, artifact_name, _subpath = _parse_artifact_specifier(artifact_name_arg)

        # Resolve vault
        vault_identifier = None
        raw_vaults = getattr(args, "vaults", None)
        if raw_vaults:
            for v in raw_vaults:
                for part in v.split(","):
                    part = part.strip()
                    if part:
                        vault_identifier = part
                        break
                if vault_identifier:
                    break

        if vault_identifier:
            vault_path_str = get_vault_by_name_or_path(vault_identifier)
            if vault_path_str is None:
                print(f"Error: Vault not found: {vault_identifier}", file=sys.stderr)
                return 1
        else:
            vault_path_str = get_default_vault()
            if vault_path_str is None:
                print("Error: No default vault set. Use 'art vault add' or 'art vault init' to set up a vault.", file=sys.stderr)
                return 1

        matches = find_artifact_in_vault(artifact_name, vault_path_str, artifact_type)
        if not matches:
            print(f"Error: Artifact '{artifact_name}' not found in vault.", file=sys.stderr)
            return 1

        match = matches[0]
        if match["type"] != "skill":
            print(
                f"Error: '{artifact_name}' is a file-based artifact ({match['type']}) and does not support file listing.",
                file=sys.stderr,
            )
            return 1

        skill_dir = match["dir"]
        _print_skill_file_listing(skill_dir)
        return 0

    has_vault_flag = getattr(args, "vaults", None) is not None
    vault_paths = _resolve_vault_paths(args)
    if not vault_paths:
        if has_vault_flag:
            # User specified -V but none resolved
            print("No artifacts found in vault.")
            return 0
        vault_path_str = get_default_vault()
        if vault_path_str is None:
            print("Error: No default vault set. Use 'art vault add' or 'art vault init' to set up a vault.", file=sys.stderr)
            return 1
        vault_paths = [Path(vault_path_str)]

    multi_vault = len(vault_paths) > 1
    type_filters = resolve_type_filters(args)

    all_rows: list[tuple] = []
    vault_info = list_vaults()
    for vault_path in vault_paths:
        artifacts = discover_vault_artifacts(vault_path)
        if type_filters:
            artifacts = _apply_type_filters(artifacts, type_filters)

        vault_label = vault_info["vault_names"].get(str(vault_path), vault_path.name)
        for art in artifacts:
            description = extract_description(art)
            if multi_vault:
                all_rows.append((art["name"], art["type"], description, vault_label))
            else:
                all_rows.append((art["name"], art["type"], description))

    if not all_rows:
        print("No artifacts found in vault.")
        return 0

    if multi_vault:
        headers = ("NAME", "TYPE", "DESCRIPTION", "VAULT")
    else:
        headers = ("NAME", "TYPE", "DESCRIPTION")

    widths = [len(h) for h in headers]
    for row in all_rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(val))

    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    for row in all_rows:
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
    from .utils import is_git_repo

    target = args.target or str(Path.cwd())
    force = getattr(args, "force", False)
    no_exclude = getattr(args, "no_exclude", False)
    yes = getattr(args, "yes", False)

    target_path = Path(target).resolve()
    if target_path.exists() and not is_git_repo(target_path):
        if not yes:
            try:
                response = input("Target is not a git repository. Continue without git integration? [Y/n]: ")
                if response.lower() in ("n", "no"):
                    print("Aborted.")
                    return 0
            except EOFError:
                print("Aborted.")
                return 0

    vault_paths = _resolve_vault_paths(args)
    if not vault_paths:
        # Fall back to default vault behavior (let import_artifacts handle it)
        vault_paths_strs: list[str | None] = [None]
    else:
        vault_paths_strs = [str(vp) for vp in vault_paths]

    tools_list: list[str]
    if args.tools:
        tools_list = [t.strip() for t in args.tools.split(",")]
    else:
        tools_list = [get_default_tool()]

    artifacts_list = None
    if getattr(args, "artifacts", None):
        artifacts_list = [a.strip() for a in args.artifacts.split(",")]

    type_filters = resolve_type_filters(args)
    link = getattr(args, "link", False)

    any_failure = False
    for vault_str in vault_paths_strs:
        _load_vault_tools_for_import(args, vault_path_str=vault_str)
        try:
            result = import_artifacts(
                target=target,
                vault=vault_str,
                tools=tools_list,
                link=link,
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
            any_failure = True
            continue

        print_import_summary(result, link=link)

    return 1 if any_failure else 0


def handle_proj_rm(args: argparse.Namespace) -> int:
    """Handle the proj rm command."""
    target_path = Path(args.target).resolve() if getattr(args, "target", None) else Path.cwd().resolve()
    force = getattr(args, "force", False)

    tools_filter = None
    if getattr(args, "tools", None):
        tools_filter = [t.strip() for t in args.tools.split(",")]

    type_filters = resolve_type_filters(args)
    vault_labels = _resolve_vault_labels_for_filter(args)

    # Load cache to find artifact locations
    cache = _load_cache_entries(target_path)
    if vault_labels:
        cache = [e for e in cache if e["vault"] in vault_labels]
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
    vault_labels = _resolve_vault_labels_for_filter(args)

    cache = _load_cache_entries(target_path)
    if vault_labels:
        cache = [e for e in cache if e["vault"] in vault_labels]
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
    vault_labels = _resolve_vault_labels_for_filter(args)

    cache = _load_cache_entries(target_path)
    if not cache:
        print("No imported artifacts found.")
        return 0

    rows = []
    for entry in cache:
        if tools_filter and entry["tool"] not in tools_filter:
            continue
        if type_filters and entry["type_plural"] not in type_filters:
            continue
        if vault_labels and entry["vault"] not in vault_labels:
            continue
        arrow = ""
        link_state = entry.get("link_state", "")
        if link_state == "linked":
            arrow = " \u2192"
        elif link_state in ("hardlinked", "win_hardlinked"):
            arrow = " \u21d2"
        state_col = link_state if link_state else "copied"
        rows.append((entry["name"] + arrow, entry["type"], entry["tool"], entry["vault"], state_col))

    if not rows:
        print("No matching imported artifacts found.")
        return 0

    headers = ("NAME", "TYPE", "TOOL", "VAULT", "STATE")
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

    vault_paths = _resolve_vault_paths(args)
    if not vault_paths:
        vault_paths_strs: list[str | None] = [None]
    else:
        vault_paths_strs = [str(vp) for vp in vault_paths]

    tools_list: list[str]
    if args.tools:
        tools_list = [t.strip() for t in args.tools.split(",")]
    else:
        tools_list = [get_default_tool()]

    artifacts_list = None
    if getattr(args, "artifacts", None):
        artifacts_list = [a.strip() for a in args.artifacts.split(",")]

    type_filters = resolve_type_filters(args)
    link = getattr(args, "link", False)

    any_failure = False
    for vault_str in vault_paths_strs:
        _load_vault_tools_for_import(args, vault_path_str=vault_str)
        try:
            result = import_artifacts_global(
                vault=vault_str,
                tools=tools_list,
                link=link,
                artifacts=artifacts_list,
                force=getattr(args, "force", False),
                type_filters=type_filters,
            )
        finally:
            reload_registry()

        if not result["success"]:
            for error in result["errors"]:
                print(error, file=sys.stderr)
            any_failure = True
            continue

        print_import_summary(result, link=link)

    return 1 if any_failure else 0


def handle_conf_rm(args: argparse.Namespace) -> int:
    """Handle the conf rm command."""
    force = getattr(args, "force", False)

    tools_filter = None
    if getattr(args, "tools", None):
        tools_filter = [t.strip() for t in args.tools.split(",")]

    type_filters = resolve_type_filters(args)
    vault_labels = _resolve_vault_labels_for_filter(args)

    cache = _load_global_cache_entries()
    if vault_labels:
        cache = [e for e in cache if e["vault"] in vault_labels]
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
    vault_labels = _resolve_vault_labels_for_filter(args)

    cache = _load_global_cache_entries()
    if vault_labels:
        cache = [e for e in cache if e["vault"] in vault_labels]
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


def handle_config_edit(args: argparse.Namespace) -> int:
    """Handle the config edit command."""
    import subprocess

    from .utils import get_config_dir, get_editor

    editor = get_editor()
    if editor is None:
        print(
            "Error: No editor found. Set $EDITOR or install nano, neovim, vim, or vi.",
            file=sys.stderr,
        )
        return 1

    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.yaml"

    result = subprocess.run([editor, str(config_path)])
    return result.returncode


def handle_conf_list(args: argparse.Namespace) -> int:
    """Handle the conf list command."""
    tools_filter = None
    if getattr(args, "tools", None):
        tools_filter = [t.strip() for t in args.tools.split(",")]

    type_filters = resolve_type_filters(args)
    vault_labels = _resolve_vault_labels_for_filter(args)

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
        if vault_labels and entry["vault"] not in vault_labels:
            continue
        arrow = ""
        link_state = entry.get("link_state", "")
        if link_state == "linked":
            arrow = " \u2192"
        elif link_state in ("hardlinked", "win_hardlinked"):
            arrow = " \u21d2"
        state_col = link_state if link_state else "copied"
        rows.append((entry["name"] + arrow, entry["type"], entry["tool"], entry["vault"], state_col))

    if not rows:
        print("No matching imported artifacts found.")
        return 0

    headers = ("NAME", "TYPE", "TOOL", "VAULT", "STATE")
    widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(val))

    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    for row in rows:
        print(fmt.format(*row))

    return 0


def _resolve_vault_paths(args: argparse.Namespace) -> list[Path]:
    """Resolve vault paths from repeatable/comma-separated `-V` flags.

    Returns:
        List of resolved vault Paths.
    """
    raw_vaults = getattr(args, "vaults", None)
    if raw_vaults:
        paths = []
        for v in raw_vaults:
            for part in v.split(","):
                part = part.strip()
                if part:
                    resolved = get_vault_by_name_or_path(part)
                    if resolved:
                        paths.append(Path(resolved))
                    else:
                        print(f"Warning: Vault not found: {part}", file=sys.stderr)
        return paths

    # Default: use the default vault
    default_vault = get_default_vault()
    if default_vault:
        return [Path(default_vault)]

    return []


def _resolve_vault_labels_for_filter(args: argparse.Namespace) -> list[str] | None:
    """Resolve vault labels from -V flags for cache entry filtering.

    Returns:
        List of vault labels to filter by, or None if no filter specified.
    """
    raw_vaults = getattr(args, "vaults", None)
    if not raw_vaults:
        return None

    labels = []
    for v in raw_vaults:
        for part in v.split(","):
            part = part.strip()
            if part:
                resolved_path = get_vault_by_name_or_path(part)
                if resolved_path:
                    info = list_vaults()
                    vault_name = info["vault_names"].get(resolved_path)
                    labels.append(vault_name if vault_name else Path(resolved_path).name)
                else:
                    labels.append(part)
    return labels if labels else None


def _resolve_vault_scope(args: argparse.Namespace) -> list[str]:
    """Resolve vault labels to scope link/unlink operations to.

    If --vault/-V is provided, uses those vaults (supports comma-separated and repeatable).
    Otherwise, falls back to the default vault label.

    Returns:
        List of vault labels (names or directory basenames) to scope to.
    """
    raw_vaults = getattr(args, "vaults", None)
    if raw_vaults:
        # Flatten comma-separated values from repeatable --vault flags
        labels = []
        for v in raw_vaults:
            for part in v.split(","):
                part = part.strip()
                if part:
                    # Resolve name-or-path to the vault label used in cache
                    resolved_path = get_vault_by_name_or_path(part)
                    if resolved_path:
                        # Look up the display name for this vault
                        info = list_vaults()
                        vault_name = info["vault_names"].get(resolved_path)
                        labels.append(vault_name if vault_name else Path(resolved_path).name)
                    else:
                        # Use as-is (might be a label already)
                        labels.append(part)
        return labels

    # Default: use the default vault
    default_vault = get_default_vault()
    if default_vault:
        info = list_vaults()
        vault_name = info["vault_names"].get(default_vault)
        return [vault_name if vault_name else Path(default_vault).name]

    return []


def handle_proj_link(args: argparse.Namespace) -> int:
    """Handle the proj link command."""
    from .importer import link_artifacts

    target_path = Path(args.target).resolve() if getattr(args, "target", None) else Path.cwd().resolve()
    names = args.names if args.names else []
    all_flag = getattr(args, "link_all", False)
    force = getattr(args, "force", False)
    type_filters = resolve_type_filters(args)

    vault_labels = _resolve_vault_scope(args)
    if not vault_labels:
        print("Error: No default vault set. Use --vault/-V to specify a vault.", file=sys.stderr)
        return 1

    if not names and not all_flag:
        print("Error: Specify artifact names or use --all/-a to link all artifacts.", file=sys.stderr)
        return 1

    result = link_artifacts(target_path, names, all_flag, force, vault_labels, type_filters)

    for error in result["errors"]:
        print(f"Error: {error}", file=sys.stderr)

    summary_parts = []
    if result["linked"]:
        summary_parts.append(f"{result['linked']} linked")
    if result["skipped"]:
        summary_parts.append(f"{result['skipped']} skipped")
    if result["backed_up"]:
        summary_parts.append(f"{result['backed_up']} backed up")
    if summary_parts:
        print(f"\n{', '.join(summary_parts)}.")

    return 1 if result["errors"] and not result["linked"] else 0


def handle_proj_unlink(args: argparse.Namespace) -> int:
    """Handle the proj unlink command."""
    from .importer import unlink_artifacts

    target_path = Path(args.target).resolve() if getattr(args, "target", None) else Path.cwd().resolve()
    names = args.names if args.names else []
    all_flag = getattr(args, "unlink_all", False)
    type_filters = resolve_type_filters(args)

    vault_labels = _resolve_vault_scope(args)
    if not vault_labels:
        print("Error: No default vault set. Use --vault/-V to specify a vault.", file=sys.stderr)
        return 1

    if not names and not all_flag:
        print("Error: Specify artifact names or use --all/-a to unlink all artifacts.", file=sys.stderr)
        return 1

    result = unlink_artifacts(target_path, names, all_flag, vault_labels, type_filters)

    for error in result["errors"]:
        print(f"Error: {error}", file=sys.stderr)

    summary_parts = []
    if result["unlinked"]:
        summary_parts.append(f"{result['unlinked']} unlinked")
    if result["skipped"]:
        summary_parts.append(f"{result['skipped']} skipped")
    if summary_parts:
        print(f"\n{', '.join(summary_parts)}.")

    return 1 if result["errors"] and not result["unlinked"] else 0


def handle_conf_link(args: argparse.Namespace) -> int:
    """Handle the conf link command."""
    from .importer import link_artifacts_global

    names = args.names if args.names else []
    all_flag = getattr(args, "link_all", False)
    force = getattr(args, "force", False)
    type_filters = resolve_type_filters(args)

    vault_labels = _resolve_vault_scope(args)
    if not vault_labels:
        print("Error: No default vault set. Use --vault/-V to specify a vault.", file=sys.stderr)
        return 1

    if not names and not all_flag:
        print("Error: Specify artifact names or use --all/-a to link all artifacts.", file=sys.stderr)
        return 1

    result = link_artifacts_global(names, all_flag, force, vault_labels, type_filters)

    for error in result["errors"]:
        print(f"Error: {error}", file=sys.stderr)

    summary_parts = []
    if result["linked"]:
        summary_parts.append(f"{result['linked']} linked")
    if result["skipped"]:
        summary_parts.append(f"{result['skipped']} skipped")
    if result["backed_up"]:
        summary_parts.append(f"{result['backed_up']} backed up")
    if summary_parts:
        print(f"\n{', '.join(summary_parts)}.")

    return 1 if result["errors"] and not result["linked"] else 0


def handle_conf_unlink(args: argparse.Namespace) -> int:
    """Handle the conf unlink command."""
    from .importer import unlink_artifacts_global

    names = args.names if args.names else []
    all_flag = getattr(args, "unlink_all", False)
    type_filters = resolve_type_filters(args)

    vault_labels = _resolve_vault_scope(args)
    if not vault_labels:
        print("Error: No default vault set. Use --vault/-V to specify a vault.", file=sys.stderr)
        return 1

    if not names and not all_flag:
        print("Error: Specify artifact names or use --all/-a to unlink all artifacts.", file=sys.stderr)
        return 1

    result = unlink_artifacts_global(names, all_flag, vault_labels, type_filters)

    for error in result["errors"]:
        print(f"Error: {error}", file=sys.stderr)

    summary_parts = []
    if result["unlinked"]:
        summary_parts.append(f"{result['unlinked']} unlinked")
    if result["skipped"]:
        summary_parts.append(f"{result['skipped']} skipped")
    if summary_parts:
        print(f"\n{', '.join(summary_parts)}.")

    return 1 if result["errors"] and not result["unlinked"] else 0


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

    current_section = "imported"  # Default for legacy files

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue

        # Handle section headers
        if line == "[vault_paths]":
            current_section = "vault_paths"
            continue
        if line == "[imported]":
            current_section = "imported"
            continue
        if current_section == "vault_paths":
            continue

        # Preserve :suffix as link_state instead of stripping
        entry = line
        link_state = ""
        if ":" in entry:
            entry, link_state = entry.rsplit(":", 1)

        parts = entry.split(".")
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
            "link_state": link_state,
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

    current_section = "imported"  # Default for legacy files

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue

        # Handle section headers
        if line == "[vault_paths]":
            current_section = "vault_paths"
            continue
        if line == "[imported]":
            current_section = "imported"
            continue
        if current_section == "vault_paths":
            continue

        # Preserve :suffix as link_state instead of stripping
        entry = line
        link_state = ""
        if ":" in entry:
            entry, link_state = entry.rsplit(":", 1)

        parts = entry.split(".")
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
            "link_state": link_state,
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


def print_import_summary(result: dict[str, Any], link: bool = False) -> None:
    """Print a summary of the import operation."""
    imported = result["imported"]
    skipped = result["skipped"]
    link_label = " (linked)" if link else " (copied)" if link is not None else ""

    total_imported = 0
    for tool_name, counts in imported.items():
        tool_total = sum(counts.values())
        if tool_total > 0:
            print(f"\n{tool_name}:")
            for artifact_type, count in counts.items():
                if count > 0:
                    print(f"  {artifact_type}: {count}{link_label}")
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

    if name and name in _NAV_TYPE_ALIASES:
        print(
            f"Warning: '{name}' is a reserved type token. "
            f"'art nav {name}' will navigate to the artifact type directory, not this vault.",
            file=sys.stderr,
        )

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
    yes = getattr(args, "yes", False)

    if name and name in _NAV_TYPE_ALIASES:
        print(
            f"Warning: '{name}' is a reserved type token. "
            f"'art nav {name}' will navigate to the artifact type directory, not this vault.",
            file=sys.stderr,
        )

    result = init_vault(args.target_dir, name=name)

    if result.get("dir_missing"):
        target_path = result["target_path"]
        if not yes:
            try:
                response = input(f"Directory does not exist: {target_path}\nCreate it? [Y/n]: ")
                if response.lower() in ("n", "no"):
                    print("Aborted.")
                    return 0
            except EOFError:
                print("Aborted.")
                return 0
        result = create_vault_directory(args.target_dir, name=name)

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


def handle_vault_copy(args: argparse.Namespace) -> int:
    """Handle the vault copy command."""
    copy_all = getattr(args, "copy_all", False)
    result = copy_vault(args.source, args.dest, copy_all=copy_all)
    if result["success"]:
        print(f"Copied vault to: {result['dest_path']} (name: {result['name']})")
        return 0
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 1


def handle_vault_export(args: argparse.Namespace) -> int:
    """Handle the vault export command."""
    export_all = getattr(args, "export_all", False)
    vaults_spec = getattr(args, "vaults_spec", None)
    output = args.output

    sel = resolve_vaults_for_export(vaults_spec, export_all)
    if not sel["success"]:
        print(f"Error: {sel['error']}", file=sys.stderr)
        return 1

    result = export_vaults(sel["vault_paths"], sel["vault_names"], output)
    if result["success"]:
        print(f"Exported {len(sel['vault_paths'])} vault(s) to: {result['output']}")
        return 0
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 1


def handle_vault_import(args: argparse.Namespace) -> int:
    """Handle the vault import command."""
    from .config import get_config_dir as _get_config_dir

    archive = args.archive
    dest = getattr(args, "dest", None)
    yes = getattr(args, "yes", False)

    # Determine destination for display
    if dest is None:
        dest_display = str(_get_config_dir() / "vaults")
    else:
        dest_display = str(Path(dest).expanduser().resolve())

    # Preview and confirm
    if not yes:
        print(f"Archive: {archive}")
        print(f"Destination: {dest_display}")
        try:
            confirm = input("Proceed with extraction? [y/N]: ")
        except EOFError:
            confirm = "n"
        if confirm.strip().lower() not in ("y", "yes"):
            print("Aborted.")
            return 0

    result = import_vaults_from_zip(archive, dest)
    if result["error"]:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 1

    for extracted in result["extracted"]:
        print(f"Imported vault '{extracted['name']}' → {extracted['path']}")

    for err in result["errors"]:
        print(f"Warning: {err}", file=sys.stderr)

    if not result["extracted"]:
        print("No vaults were imported.")
        return 1 if result["errors"] else 0

    return 0


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
    show_all = getattr(args, "show_all", False)
    vault_paths = _resolve_vault_paths(args)

    if show_all and vault_paths and getattr(args, "vaults", None):
        print("Error: --all and -V are mutually exclusive.", file=sys.stderr)
        return 1

    global_tools = load_global_tools()

    if show_all:
        # List tools from all catalog vaults + global config
        all_vault_data = load_all_vault_tools()
        # Aggregate all vault tools
        combined_vault_tools: dict[str, dict] = {}
        for _vname, _vpath, vtools in all_vault_data:
            combined_vault_tools.update(vtools)
        vault_tools = combined_vault_tools
        vault_name = None
    elif vault_paths and getattr(args, "vaults", None):
        # Multi-vault: aggregate tools from specified vaults
        combined_vault_tools = {}
        for vp in vault_paths:
            meta = load_vault_metadata(str(vp))
            vt = meta.get("tools", {})
            combined_vault_tools.update(vt)
        vault_tools = combined_vault_tools
        vault_name = None
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
        tool_def["aliases"] = [a.strip() for raw in args.aliases for a in raw.split(",")]

    # Validate at least one artifact path provided
    if not any(k in tool_def for k in ("skills", "commands", "agents")):
        print(
            "Error: At least one of --skills, --commands, or --agents is required.",
            file=sys.stderr,
        )
        return 1

    has_vault_flag = getattr(args, "vaults", None) is not None
    vault_paths = _resolve_vault_paths(args) if has_vault_flag else []

    if vault_paths:
        # Store in vault(s)' vault.yaml
        for vault_path in vault_paths:
            vault_path_str = str(vault_path)
            meta = load_vault_metadata(vault_path_str)
            if tool_name in meta.get("tools", {}):
                print(f"Error: Tool '{tool_name}' already exists in vault '{vault_path.name}'.", file=sys.stderr)
                return 1

            if "tools" not in meta or meta["tools"] is None:
                meta["tools"] = {}
            meta["tools"][tool_name] = tool_def
            save_vault_metadata(vault_path_str, meta)
            print(f"Added tool '{tool_name}' to vault '{vault_path.name}'.")
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
    global_filter = getattr(args, "global_filter", False)
    show_all = getattr(args, "show_all", False)

    vault_paths = _resolve_vault_paths(args)
    has_vault_flag = getattr(args, "vaults", None) is not None

    if show_all and has_vault_flag:
        print("Error: --all and -V are mutually exclusive.", file=sys.stderr)
        return 1

    global_tools = load_global_tools()
    default_vault_tools, default_vault_name = load_active_vault_tools()
    default_vault_path = get_default_vault()
    all_vault_data = load_all_vault_tools()
    cwd_tools = load_cwd_vault_tools()

    # Resolve vault filter
    filter_vault_paths: list[str] = []
    if show_all:
        # --all: show everything, no filtering
        pass
    elif has_vault_flag:
        filter_vault_paths = [str(vp) for vp in vault_paths]

    # For backward compat with _tool_info_catalog/_tool_info_detail, use single filter_vault_path
    # when only one vault is specified; for multiple, we iterate
    filter_vault_path: str | None = None
    filter_vault_name: str | None = None
    if len(filter_vault_paths) == 1:
        filter_vault_path = filter_vault_paths[0]
        meta = load_vault_metadata(filter_vault_path)
        filter_vault_name = meta.get("name")
    elif len(filter_vault_paths) > 1:
        # For multi-vault filter, show each vault's tools
        for fvp in filter_vault_paths:
            meta = load_vault_metadata(fvp)
            fvn = meta.get("name")
            if tool_name is None:
                _tool_info_catalog(
                    global_tools=global_tools,
                    all_vault_data=all_vault_data,
                    cwd_tools=cwd_tools,
                    default_vault_path=default_vault_path,
                    global_filter=False,
                    filter_vault_path=fvp,
                    filter_vault_name=fvn,
                )
            else:
                _tool_info_detail(
                    tool_name=tool_name,
                    global_tools=global_tools,
                    default_vault_tools=default_vault_tools,
                    default_vault_name=default_vault_name,
                    default_vault_path=default_vault_path,
                    all_vault_data=all_vault_data,
                    cwd_tools=cwd_tools,
                    global_filter=False,
                    filter_vault_path=fvp,
                    filter_vault_name=fvn,
                )
        return 0

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


def _resolve_copy_type(prefix: str) -> str | None:
    """Resolve a type prefix to its canonical subdirectory name."""
    type_map = {
        "skill": "skills", "skills": "skills", "s": "skills", "sk": "skills",
        "command": "commands", "commands": "commands", "c": "commands", "cmd": "commands", "com": "commands",
        "agent": "agents", "agents": "agents", "a": "agents", "agt": "agents", "ag": "agents",
    }
    return type_map.get(prefix)


def _resolve_copy_source(source_spec: str) -> dict[str, Any]:
    """Parse and resolve a copy source specifier.

    Source format: [vault/][type/]name-or-glob

    Returns dict with:
        - vault_path: str resolved vault path
        - type_subdir: str | None (e.g. 'skills')
        - name_pattern: str (name or glob pattern)
        - error: str | None
    """
    parts = source_spec.split("/")

    vault_path: str | None = None
    type_subdir: str | None = None
    name_pattern: str

    if len(parts) == 1:
        # bare name — use default vault
        name_pattern = parts[0]
        vault_path = get_default_vault()
        if vault_path is None:
            return {"vault_path": None, "type_subdir": None, "name_pattern": name_pattern,
                    "error": "No default vault set."}
    elif len(parts) == 2:
        first, second = parts
        resolved_type = _resolve_copy_type(first)
        if resolved_type is not None:
            type_subdir = resolved_type
            name_pattern = second
            vault_path = get_default_vault()
            if vault_path is None:
                return {"vault_path": None, "type_subdir": type_subdir, "name_pattern": name_pattern,
                        "error": "No default vault set."}
        else:
            resolved = get_vault_by_name_or_path(first)
            if resolved is not None:
                vault_path = resolved
                name_pattern = second
            else:
                name_pattern = source_spec
                vault_path = get_default_vault()
                if vault_path is None:
                    return {"vault_path": None, "type_subdir": None, "name_pattern": name_pattern,
                            "error": "No default vault set."}
    elif len(parts) == 3:
        vault_spec, type_spec, name_pattern = parts
        resolved = get_vault_by_name_or_path(vault_spec)
        if resolved is None:
            return {"vault_path": None, "type_subdir": None, "name_pattern": name_pattern,
                    "error": f"Vault not found: {vault_spec}"}
        vault_path = resolved
        resolved_type = _resolve_copy_type(type_spec)
        if resolved_type is None:
            return {"vault_path": vault_path, "type_subdir": None, "name_pattern": name_pattern,
                    "error": f"Unknown type alias: {type_spec}"}
        type_subdir = resolved_type
    else:
        return {"vault_path": None, "type_subdir": None, "name_pattern": "/".join(parts),
                "error": f"Cannot parse source specifier: {source_spec}"}

    return {"vault_path": vault_path, "type_subdir": type_subdir, "name_pattern": name_pattern, "error": None}


def _resolve_copy_dest(dest_spec: str, source_vault_path: str) -> dict[str, Any]:
    """Parse copy destination specifier.

    Returns dict with:
        - vault_path: str | None (if container destination)
        - new_name: str | None (if rename destination)
        - is_container: bool
        - error: str | None
    """
    # Trailing slash → container
    if dest_spec.endswith("/"):
        vault_name = dest_spec.rstrip("/")
        resolved = get_vault_by_name_or_path(vault_name)
        if resolved is None:
            return {"vault_path": None, "new_name": None, "is_container": True, "error": f"Vault not found: {vault_name}"}
        return {"vault_path": resolved, "new_name": None, "is_container": True, "error": None}

    # Check if it's vault/name format
    if "/" in dest_spec:
        parts = dest_spec.split("/", 1)
        vault_spec, new_name = parts
        resolved = get_vault_by_name_or_path(vault_spec)
        if resolved is not None:
            return {"vault_path": resolved, "new_name": new_name, "is_container": False, "error": None}

    # Check if it's a registered vault name (no trailing slash)
    resolved = get_vault_by_name_or_path(dest_spec)
    if resolved is not None:
        return {"vault_path": resolved, "new_name": None, "is_container": True, "error": None}

    # Treat as new artifact name (within source vault)
    return {"vault_path": source_vault_path, "new_name": dest_spec, "is_container": False, "error": None}


def _find_artifacts_in_vault(
    vault_path: str,
    type_subdir: str | None,
    name_pattern: str,
) -> list[dict[str, Any]]:
    """Find artifacts in a vault matching type and name/glob pattern.

    Returns list of dicts with 'type_subdir', 'name', 'path' (Path object).
    """
    import fnmatch as _fnmatch
    from .creator import _find_by_frontmatter_name as _fm_find, _parse_frontmatter_name as _fm_parse

    vault_dir = Path(vault_path)
    is_glob = any(c in name_pattern for c in ("*", "?", "["))

    search_types = [type_subdir] if type_subdir else ["skills", "commands", "agents"]
    results: list[dict[str, Any]] = []

    for tdir in search_types:
        type_path = vault_dir / tdir
        if not type_path.is_dir():
            continue

        if tdir == "skills":
            candidates = [
                {"name": item.name, "path": item}
                for item in sorted(type_path.iterdir()) if item.is_dir()
            ]
        else:
            candidates = [
                {"name": item.stem, "path": item}
                for item in sorted(type_path.iterdir()) if item.is_file() and item.suffix == ".md"
            ]

        if is_glob:
            for cand in candidates:
                # Match by filesystem name
                if _fnmatch.fnmatch(cand["name"], name_pattern):
                    results.append({"type_subdir": tdir, "name": cand["name"], "path": cand["path"]})
                    continue
                # Match by frontmatter name
                if tdir == "skills":
                    fm_file = cand["path"] / "SKILL.md"
                    if fm_file.is_file():
                        fm_name = _fm_parse(fm_file)
                        if fm_name and _fnmatch.fnmatch(fm_name, name_pattern):
                            results.append({"type_subdir": tdir, "name": cand["name"], "path": cand["path"]})
                else:
                    fm_name = _fm_parse(cand["path"])
                    if fm_name and _fnmatch.fnmatch(fm_name, name_pattern):
                        results.append({"type_subdir": tdir, "name": cand["name"], "path": cand["path"]})
        else:
            # Exact match by name
            for cand in candidates:
                if cand["name"] == name_pattern:
                    results.append({"type_subdir": tdir, "name": cand["name"], "path": cand["path"]})
                    break

    return results


def _copy_artifact_to_vault(
    artifact: dict[str, Any],
    dest_vault_path: str,
    new_name: str | None,
) -> dict[str, Any]:
    """Copy a single artifact to a destination vault (or new name in same vault).

    Args:
        artifact: Dict with 'type_subdir', 'name', 'path'.
        dest_vault_path: Absolute path string for the destination vault.
        new_name: If set, rename the artifact; otherwise keep original name.

    Returns:
        Result dict with 'success', 'dest', 'error'.
    """
    dest_vault = Path(dest_vault_path)
    tdir = artifact["type_subdir"]
    src_path: Path = artifact["path"]
    target_name = new_name if new_name else artifact["name"]

    dest_type_dir = dest_vault / tdir
    dest_type_dir.mkdir(parents=True, exist_ok=True)

    if tdir == "skills":
        dest = dest_type_dir / target_name
    else:
        dest = dest_type_dir / f"{target_name}.md"

    if dest.exists():
        return {"success": False, "dest": str(dest), "error": f"Destination already exists: {dest}"}

    if src_path.is_dir():
        shutil.copytree(src_path, dest)
    else:
        shutil.copy2(src_path, dest)

    return {"success": True, "dest": str(dest), "error": None}


def handle_copy(args: argparse.Namespace) -> int:
    """Handle the copy command."""
    source_spec = args.source
    dest_spec = args.dest

    # Parse source
    src = _resolve_copy_source(source_spec)
    if src["error"]:
        print(f"Error: {src['error']}", file=sys.stderr)
        return 1

    # Find matching artifacts
    artifacts = _find_artifacts_in_vault(src["vault_path"], src["type_subdir"], src["name_pattern"])

    is_glob = any(c in src["name_pattern"] for c in ("*", "?", "["))

    if not artifacts and not is_glob:
        # Try frontmatter name fallback for non-glob
        from .creator import _find_by_frontmatter_name as _fm_find
        vault_path = src["vault_path"]
        type_subdir = src["type_subdir"]
        subdir_to_type = {"skills": "skill", "commands": "command", "agents": "agent"}

        for tdir in ([type_subdir] if type_subdir else ["skills", "commands", "agents"]):
            art_type = subdir_to_type.get(tdir, tdir.rstrip("s"))
            fm_path = _fm_find(art_type, src["name_pattern"], Path(vault_path))
            if fm_path is not None:
                if art_type == "skill":
                    art_path = fm_path.parent
                else:
                    art_path = fm_path
                artifacts.append({
                    "type_subdir": tdir,
                    "name": art_path.name if art_type == "skill" else art_path.stem,
                    "path": art_path,
                })
                break

    if not artifacts:
        print(f"Error: No artifact found matching '{source_spec}'.", file=sys.stderr)
        return 1

    # Check multi-type name conflict for bare name (no type prefix)
    if not is_glob and not src["type_subdir"] and len(artifacts) > 1:
        types_found = [a["type_subdir"] for a in artifacts]
        hints = ", ".join(f"{t}/{src['name_pattern']}" for t in types_found)
        print(f"Error: '{src['name_pattern']}' matches multiple types: {types_found}. Use a type prefix: {hints}", file=sys.stderr)
        return 1

    # Parse destination
    dst = _resolve_copy_dest(dest_spec, src["vault_path"])
    if dst["error"]:
        print(f"Error: {dst['error']}", file=sys.stderr)
        return 1

    # Multi-artifact requires container destination
    if len(artifacts) > 1 and not dst["is_container"]:
        print("Error: Multi-artifact sources require a container destination (trailing slash or registered vault name).", file=sys.stderr)
        return 1

    dest_vault_path = dst["vault_path"]

    errors = []
    for artifact in artifacts:
        new_name = dst["new_name"] if not dst["is_container"] else None
        result = _copy_artifact_to_vault(artifact, dest_vault_path, new_name)
        if result["success"]:
            print(f"Copied: {artifact['name']} → {result['dest']}")
        else:
            errors.append(result["error"])
            print(f"Error: {result['error']}", file=sys.stderr)

    return 1 if errors else 0


def handle_nav(args: argparse.Namespace) -> int:
    """Handle the nav command."""
    import subprocess as _subprocess
    from .config import get_nav_mode as _get_nav_mode

    target_arg = getattr(args, "target", None)
    nav_print = getattr(args, "nav_print", False)
    spawn = getattr(args, "spawn", False)
    window = getattr(args, "window", False)

    # Resolve target path
    default_vault = get_default_vault()
    if default_vault is None:
        print("Error: No default vault set. Use 'art vault add' or 'art vault init'.", file=sys.stderr)
        return 1

    vault_path: Path | None = None

    if target_arg is None:
        # Default: vault root
        vault_path = Path(default_vault)
    elif target_arg in _NAV_TYPE_ALIASES:
        # Type alias → type subdir of default vault
        type_subdir = _NAV_TYPE_ALIASES[target_arg]
        vault_path = Path(default_vault) / type_subdir
    elif "/" in target_arg:
        # vault/type format
        parts = target_arg.split("/", 1)
        vault_name, type_part = parts[0], parts[1]
        resolved_vault = get_vault_by_name_or_path(vault_name)
        if resolved_vault is None:
            print(f"Error: Unknown vault: {vault_name}", file=sys.stderr)
            return 1
        if type_part in _NAV_TYPE_ALIASES:
            type_subdir = _NAV_TYPE_ALIASES[type_part]
            vault_path = Path(resolved_vault) / type_subdir
        else:
            print(f"Error: Unknown type alias '{type_part}'. Valid: skills, commands, agents (and short forms).", file=sys.stderr)
            return 1
    else:
        # Try as vault name
        resolved_vault = get_vault_by_name_or_path(target_arg)
        if resolved_vault is not None:
            vault_path = Path(resolved_vault)
        else:
            print(f"Error: '{target_arg}' is not a recognized type alias or registered vault name.", file=sys.stderr)
            return 1

    if vault_path is None or not vault_path.is_dir():
        print(f"Error: Target directory does not exist: {vault_path}", file=sys.stderr)
        return 1

    # Determine mode (flag > config > error)
    if nav_print:
        mode = "print"
    elif spawn:
        mode = "spawn"
    elif window:
        mode = "window"
    else:
        mode = _get_nav_mode()
        if mode is None:
            print(
                "Error: No navigation mode configured.\n"
                "Options:\n"
                "  --print   Print the path (for use in shell wrapper — run 'art shell setup')\n"
                "  --spawn   Open a subshell at the target directory\n"
                "  --window  Open a new terminal window at the target directory\n"
                "Set a default in config.yaml with: nav_mode: wrapper|spawn|window|print",
                file=sys.stderr,
            )
            return 1
        if mode == "wrapper":
            mode = "print"

    resolved_path = str(vault_path.resolve())

    if mode == "print":
        print(resolved_path)
        return 0
    elif mode == "spawn":
        shell = os.environ.get("SHELL", "sh") if sys.platform != "win32" else "powershell.exe"
        _subprocess.run([shell], cwd=resolved_path)
        return 0
    elif mode == "window":
        terminal = os.environ.get("TERMINAL")
        if terminal:
            try:
                _subprocess.Popen([terminal, "--working-directory", resolved_path])
                return 0
            except (FileNotFoundError, OSError):
                pass

        if sys.platform == "darwin":
            try:
                _subprocess.Popen(["open", "-a", "Terminal", resolved_path])
                return 0
            except (FileNotFoundError, OSError):
                pass
        elif sys.platform == "win32":
            for term in ("wt", "cmd.exe"):
                try:
                    _subprocess.Popen([term, "/d", resolved_path])
                    return 0
                except (FileNotFoundError, OSError):
                    continue
        else:
            import shutil as _shutil
            for term in ("xterm", "gnome-terminal", "konsole", "alacritty", "kitty"):
                if _shutil.which(term):
                    try:
                        _subprocess.Popen([term, "--working-directory", resolved_path])
                        return 0
                    except (FileNotFoundError, OSError):
                        continue

        print("Error: No terminal emulator found. Set $TERMINAL or use --spawn instead.", file=sys.stderr)
        return 1

    return 0


def handle_shell_setup(args: argparse.Namespace) -> int:
    """Handle the shell setup command."""
    from .utils import detect_shell as _detect_shell
    from .utils import get_shell_rc_file as _get_shell_rc_file
    from .utils import get_shell_wrapper_snippet as _get_shell_wrapper_snippet

    yes = getattr(args, "yes", False)
    shell = _detect_shell()
    rc_file = _get_shell_rc_file(shell)
    snippet = _get_shell_wrapper_snippet(shell)

    if rc_file is None:
        print(f"Error: Unsupported shell: {shell}. Cannot determine rc file.", file=sys.stderr)
        return 1

    is_fish = shell == "fish"

    print(f"Detected shell: {shell}")
    print(f"Target file: {rc_file}")

    if not yes:
        try:
            preview = input("Preview snippet before applying? [y/N]: ")
        except EOFError:
            preview = "n"
        if preview.strip().lower() in ("y", "yes"):
            print("\n" + snippet)

        try:
            confirm = input(f"\nAppend snippet to {rc_file}? [y/N]: ")
        except EOFError:
            confirm = "n"
        if confirm.strip().lower() not in ("y", "yes"):
            print("Aborted.")
            return 0

    # Write snippet
    rc_file.parent.mkdir(parents=True, exist_ok=True)

    if is_fish:
        if rc_file.exists() and not yes:
            try:
                overwrite = input(f"{rc_file} already exists. Overwrite? [y/N]: ")
            except EOFError:
                overwrite = "n"
            if overwrite.strip().lower() not in ("y", "yes"):
                print("Aborted.")
                return 0
        rc_file.write_text(snippet, encoding="utf-8")
        print(f"\nWrote snippet to {rc_file}")
    else:
        with open(rc_file, "a", encoding="utf-8") as f:
            f.write("\n" + snippet)
        print(f"\nAppended snippet to {rc_file}")

    if is_fish:
        print("Fish functions are auto-loaded — no source command needed.")
    else:
        print(f"Run: source {rc_file}")
        print("Or start a new shell session.")

    return 0


def _compute_spelunk_location(artifact_path: Path, original_target: Path | None, global_spelunk: bool) -> str:
    """Compute the display location for a spelunk artifact.

    For global spelunk, returns a home-collapsed absolute path (~/...).
    For directory/vault spelunk, returns path relative to original_target.
    Falls back to absolute path if relative_to() fails (e.g. symlink outside root).
    """
    if global_spelunk or original_target is None:
        home = Path.home()
        try:
            rel = artifact_path.relative_to(home)
            return "~/" + str(rel)
        except ValueError:
            return str(artifact_path)
    else:
        try:
            return str(artifact_path.relative_to(original_target))
        except ValueError:
            return str(artifact_path)


def _format_spelunk_data(artifacts: list[dict]) -> list[dict]:
    """Build a shared data structure for spelunk output formatters."""
    return [
        {
            "name": art["name"],
            "type": art["type"],
            "path": str(art["path"]),
            "source": art.get("tool", "unknown"),
        }
        for art in artifacts
    ]


def _format_spelunk_json(artifacts: list[dict]) -> str:
    """Format spelunk results as JSON."""
    import json
    data = _format_spelunk_data(artifacts)
    return json.dumps(data, indent=2)


def _format_spelunk_yaml(artifacts: list[dict]) -> str:
    """Format spelunk results as YAML."""
    import yaml
    data = _format_spelunk_data(artifacts)
    return yaml.dump(data, default_flow_style=False)


def _format_spelunk_markdown(artifacts: list[dict], original_target: Path | None = None, global_spelunk: bool = False) -> str:
    """Format spelunk results as a markdown table."""
    data = _format_spelunk_data(artifacts)
    lines = ["| Name | Type | Location |", "| --- | --- | --- |"]
    for item, art in zip(data, artifacts):
        location = _compute_spelunk_location(art["path"], original_target, global_spelunk)
        lines.append(f"| {item['name']} | {item['type']} | {location} |")
    return "\n".join(lines)


def handle_spelunk(args: argparse.Namespace) -> int:
    """Handle the spelunk command."""
    target_str = getattr(args, "target", None)
    global_spelunk = getattr(args, "global_spelunk", False)
    tools_filter_str = getattr(args, "tools", None)
    depth = getattr(args, "depth", 2)
    output_format = getattr(args, "format", "human")
    verbose = getattr(args, "verbose", False)

    tools_filter = None
    if tools_filter_str:
        global_tools = load_global_tools()
        vault_tools_dict, _ = load_active_vault_tools()
        tools_filter = [
            resolve_tool_name(t.strip(), extra_tools=global_tools, vault_tools=vault_tools_dict)
            for t in tools_filter_str.split(",")
        ]

    type_filters = resolve_type_filters(args)

    # Track the original target for LOCATION column relativization
    original_target: Path | None = None

    if target_str is None or global_spelunk:
        # Global config spelunk
        if target_str is None and not global_spelunk and output_format == "human":
            print("No target specified — spelunking global config directories.\n")
        artifacts = discover_global_artifacts(tools_filter=tools_filter)
        global_spelunk = True
    else:
        target = Path(target_str).resolve()
        original_target = target
        if not target.exists() or not target.is_dir():
            print(f"Error: Target directory does not exist: {target_str}", file=sys.stderr)
            return 1

        if is_vault(target):
            artifacts = discover_vault_artifacts(target)
        else:
            artifacts = discover_artifacts(target)
            if tools_filter:
                artifacts = [a for a in artifacts if a["tool"] in tools_filter]
            # Layer 3: depth-based structure scanning as fallback
            if not artifacts:
                artifacts = discover_artifacts_by_structure(target, depth=depth)

    if type_filters:
        artifacts = _apply_type_filters(artifacts, type_filters)

    if not artifacts:
        label = target_str or "global config"
        if output_format == "json":
            print("[]")
        elif output_format == "yaml":
            print("[]")
        elif output_format in ("md", "markdown"):
            print(_format_spelunk_markdown([], original_target, global_spelunk))
        else:
            print(f"No artifacts found in {label}")
        return 0

    # Structured output formats
    if output_format == "json":
        print(_format_spelunk_json(artifacts))
        return 0
    elif output_format == "yaml":
        print(_format_spelunk_yaml(artifacts))
        return 0
    elif output_format in ("md", "markdown"):
        print(_format_spelunk_markdown(artifacts, original_target, global_spelunk))
        return 0

    # Human format
    import_cache: dict[str, list[str]] = {}
    if target_str and not global_spelunk:
        import_cache = load_import_cache(original_target or Path(target_str).resolve())

    rows = []
    for art in artifacts:
        name_col = art["name"]

        if art["name"] in import_cache:
            vault_parts = []
            for vname in import_cache[art["name"]]:
                health = check_import_health(art["name"], art["type"], vname)
                if health:
                    vault_parts.append(f"{vname}, {health}")
                else:
                    vault_parts.append(vname)
            name_col += f" (imported: {'; '.join(vault_parts)})"

        location = _compute_spelunk_location(art["path"], original_target, global_spelunk)

        if verbose:
            description = extract_description(art)
            rows.append((name_col, art["type"], location, description))
        else:
            rows.append((name_col, art["type"], location))

    if verbose:
        headers = ("NAME", "TYPE", "LOCATION", "DESCRIPTION")
    else:
        headers = ("NAME", "TYPE", "LOCATION")
    widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(val))

    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    for row in rows:
        print(fmt.format(*row))

    return 0


def _detect_zip_artifact_type(extracted_dir: Path) -> str:
    """Inspect extracted zip directory contents to classify the artifact type.

    Returns one of: "single-skill", "single-file-artifact", "vault-bundle".
    Raises ValueError if no recognizable artifact structure is found.
    """
    root_entries = [e for e in extracted_dir.iterdir() if not e.name.startswith(".")]
    root_dirs = [e for e in root_entries if e.is_dir()]
    root_files = [e for e in root_entries if e.is_file()]

    if not root_entries:
        raise ValueError("Zip archive contains no recognizable artifact structure.")

    # Multiple root directories → vault bundle
    if len(root_dirs) > 1:
        return "vault-bundle"

    # Single root file (not directory) at root → not a recognized structure
    if not root_dirs and root_files:
        raise ValueError("Zip archive contains no recognizable artifact structure.")

    single_dir = root_dirs[0]

    # Check if the single dir itself contains skills/commands/agents → vault bundle
    sub_entries = list(single_dir.iterdir())
    sub_names = {e.name for e in sub_entries if e.is_dir()}
    if sub_names & {"skills", "commands", "agents"}:
        return "vault-bundle"

    # Single directory with SKILL.md → single skill
    if (single_dir / "SKILL.md").is_file():
        return "single-skill"

    # Single directory containing a .md file matching directory name → file-based artifact
    md_files = [f for f in sub_entries if f.is_file() and f.suffix == ".md"]
    if len(md_files) == 1 and md_files[0].stem == single_dir.name:
        return "single-file-artifact"

    raise ValueError("Zip archive contains no recognizable artifact structure.")


def _store_artifacts_to_vault(
    artifacts: list[dict],
    vault_paths: list[Path],
    force: bool,
    source_label: str,
) -> int:
    """Run the interactive artifact selection and copy flow. Returns exit code."""
    if not artifacts:
        print(f"No artifacts found in {source_label}")
        return 0

    print(f"Discovered artifacts in {source_label}:")
    for i, art in enumerate(artifacts, 1):
        print(f"  {i}. {art['name']} ({art['type']}) - {art['path']}")

    try:
        selection = input(f"\nSelect artifacts to store [1-{len(artifacts)}, all]: ")
    except EOFError:
        return 0

    indices = parse_selection(selection, len(artifacts))
    if not indices:
        return 0

    vault_info = list_vaults()
    for vault_path in vault_paths:
        vault_display_name = vault_info["vault_names"].get(str(vault_path), vault_path.name)
        stored_count = 0
        for idx in indices:
            art = artifacts[idx]
            source_path = art["path"]
            dest = vault_path / art["type_plural"] / source_path.name

            if source_path.is_symlink():
                try:
                    resolved = source_path.resolve()
                    if str(resolved).startswith(str(vault_path.resolve())):
                        print(f"Skipping '{art['name']}': already linked to this vault")
                        continue
                except OSError:
                    pass

            result = copy_with_prompt(source_path, dest, force=force)
            if result["copied"] > 0:
                print(f"Stored: {art['name']} ({art['type']}) -> {dest}")
                stored_count += 1

        print(f"\n{stored_count} artifact(s) stored to vault: {vault_display_name}")

    return 0


def handle_store(args: argparse.Namespace) -> int:
    """Handle the store command."""
    import tempfile
    import zipfile

    global_store = getattr(args, "global_store", False)
    target_dir = getattr(args, "target_dir", None)
    tools_str = getattr(args, "tools", None)

    if global_store and target_dir:
        print("Error: Cannot use both --global and a target directory.", file=sys.stderr)
        return 1
    if not global_store and not target_dir:
        print("Error: Either a target directory or --global is required.", file=sys.stderr)
        return 1

    # Zip input: error if combined with --global
    if target_dir and target_dir.endswith(".zip"):
        if global_store:
            print("Error: A zip file target cannot be used with --global.", file=sys.stderr)
            return 1

        zip_path = Path(target_dir).resolve()
        if not zip_path.exists():
            print(f"Error: Zip file does not exist: {target_dir}", file=sys.stderr)
            return 1
        if not zipfile.is_zipfile(zip_path):
            print(f"Error: File is not a valid zip archive: {target_dir}", file=sys.stderr)
            return 1

        vault_paths = _resolve_vault_paths(args)
        if not vault_paths:
            vault_path_str = get_default_vault()
            if vault_path_str is None:
                print("Error: No default vault set. Use 'art vault add' or 'art vault init' to set up a vault.", file=sys.stderr)
                return 1
            vault_paths = [Path(vault_path_str)]

        force = getattr(args, "force", False)
        tmp_dir = Path(tempfile.mkdtemp())
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(tmp_dir)

            try:
                zip_type = _detect_zip_artifact_type(tmp_dir)
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                return 1

            if zip_type in ("single-skill", "single-file-artifact"):
                # The zip has a flat structure: <artifact-name>/ at root.
                # Build source path and dest directly from the single root directory.
                root_dirs = [e for e in tmp_dir.iterdir() if e.is_dir()]
                if not root_dirs:
                    print("Error: No recognizable artifacts found in zip.", file=sys.stderr)
                    return 1
                single_dir = root_dirs[0]
                if zip_type == "single-skill":
                    source_path = single_dir  # the skill directory
                    type_plural = "skills"
                    artifact_name = single_dir.name
                else:
                    # single-file-artifact: find the .md file in the single dir
                    md_files = [f for f in single_dir.iterdir() if f.is_file() and f.suffix == ".md"]
                    if not md_files:
                        print("Error: No .md file found in zip artifact directory.", file=sys.stderr)
                        return 1
                    source_path = md_files[0]
                    artifact_name = source_path.stem
                    type_plural = "commands"  # default; could be agent but indistinguishable without frontmatter

                vault_info = list_vaults()
                for vault_path in vault_paths:
                    vault_display_name = vault_info["vault_names"].get(str(vault_path), vault_path.name)
                    dest = vault_path / type_plural / source_path.name
                    result = copy_with_prompt(source_path, dest, force=force)
                    stored_count = 1 if result["copied"] > 0 else 0
                    if stored_count:
                        print(f"Stored: {artifact_name} -> {dest}")
                    print(f"\n{stored_count} artifact(s) stored to vault: {vault_display_name}")
                return 0
            else:
                # vault-bundle: show selection modal
                artifacts = discover_artifacts_by_structure(tmp_dir)
                type_filters = resolve_type_filters(args)
                if type_filters:
                    artifacts = _apply_type_filters(artifacts, type_filters)
                return _store_artifacts_to_vault(artifacts, vault_paths, force, str(zip_path))
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    vault_paths = _resolve_vault_paths(args)
    if not vault_paths:
        vault_path_str = get_default_vault()
        if vault_path_str is None:
            print("Error: No default vault set. Use 'art vault add' or 'art vault init' to set up a vault.", file=sys.stderr)
            return 1
        vault_paths = [Path(vault_path_str)]

    if global_store:
        tools_filter = None
        if tools_str:
            tools_filter = [resolve_tool_name(t.strip()) for t in tools_str.split(",")]
        artifacts = discover_global_artifacts(tools_filter=tools_filter)
    else:
        target = Path(target_dir).resolve()

        if not target.exists() or not target.is_dir():
            print(f"Error: Target directory does not exist: {target_dir}", file=sys.stderr)
            return 1

        if tools_str:
            tools_filter = [resolve_tool_name(t.strip()) for t in tools_str.split(",")]
            artifacts = discover_artifacts(target)
            artifacts = [a for a in artifacts if a["tool"] in tools_filter]
        else:
            artifacts = discover_artifacts(target)

    type_filters = resolve_type_filters(args)
    if type_filters:
        artifacts = _apply_type_filters(artifacts, type_filters)

    source_label = "global config" if global_store else target_dir
    force = getattr(args, "force", False)
    return _store_artifacts_to_vault(artifacts, vault_paths, force, source_label)


def _show_skill_picker(skill_dir: Path) -> Path | None:
    """Display interactive file picker for a skill directory.

    Returns the selected file path, or None if the user quits.
    Handles new-file, import-file, and delete actions inline.
    """
    import subprocess
    from .utils import get_editor

    while True:
        files = _list_skill_files(skill_dir)
        print(f"\nSkill: {skill_dir.name}")
        for i, f in enumerate(files, 1):
            rel = f.relative_to(skill_dir)
            label = " (main)" if f.name == "SKILL.md" and f.parent == skill_dir else ""
            print(f"  {i}. {rel}{label}")
        print("\n  [n] New file  [i] Import file  [d] Delete file  [q] Quit")

        try:
            raw = input("\nSelect file or action [Enter = open SKILL.md]: ").strip()
        except EOFError:
            return None

        if raw == "" or raw == "q":
            if raw == "":
                return skill_dir / "SKILL.md"
            return None

        if raw == "n":
            try:
                rel_path = input("New file path (relative): ").strip()
            except EOFError:
                continue
            if not rel_path:
                print("Error: Path cannot be empty.")
                continue
            new_file = skill_dir / rel_path
            if new_file.exists():
                print(f"Error: File already exists: {rel_path}")
                continue
            new_file.parent.mkdir(parents=True, exist_ok=True)
            new_file.touch()
            return new_file

        if raw == "i":
            try:
                src_raw = input("Source file path: ").strip()
            except EOFError:
                continue
            src = Path(src_raw).expanduser()
            if not src.exists():
                print(f"Error: Source file not found: {src_raw}")
                continue
            try:
                dest_raw = input(f"Destination path within skill [default: {src.name}]: ").strip()
            except EOFError:
                continue
            dest_rel = dest_raw if dest_raw else src.name
            dest = skill_dir / dest_rel
            if dest.exists():
                try:
                    confirm = input(f"File already exists at {dest_rel}. Overwrite? [y/N]: ").strip().lower()
                except EOFError:
                    continue
                if confirm not in ("y", "yes"):
                    print("Aborted.")
                    continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            return dest

        if raw == "d":
            del_files = _list_skill_files(skill_dir)
            for i, f in enumerate(del_files, 1):
                rel = f.relative_to(skill_dir)
                print(f"  {i}. {rel}")
            try:
                sel_raw = input("Select file to delete [number]: ").strip()
            except EOFError:
                continue
            try:
                sel_idx = int(sel_raw) - 1
            except ValueError:
                print("Invalid selection.")
                continue
            if sel_idx < 0 or sel_idx >= len(del_files):
                print("Invalid selection.")
                continue
            to_delete = del_files[sel_idx]
            if to_delete.name == "SKILL.md" and to_delete.parent == skill_dir:
                print("Error: Cannot delete the primary file (SKILL.md).")
                continue
            rel_del = to_delete.relative_to(skill_dir)
            try:
                confirm = input(f"Delete {rel_del}? [y/N]: ").strip().lower()
            except EOFError:
                continue
            if confirm not in ("y", "yes"):
                print("Aborted.")
                continue
            to_delete.unlink()
            # Remove empty parent dirs (except skill root)
            parent = to_delete.parent
            while parent != skill_dir:
                if not any(parent.iterdir()):
                    parent.rmdir()
                    parent = parent.parent
                else:
                    break
            print(f"Deleted: {rel_del}")
            continue

        # Numeric selection
        try:
            idx = int(raw) - 1
        except ValueError:
            print(f"Invalid input: {raw!r}. Enter a file number, or n/i/d/q.")
            continue
        if idx < 0 or idx >= len(files):
            print(f"Invalid selection: must be 1–{len(files)}.")
            continue
        return files[idx]


def _resolve_edit_artifact(
    specifier_parts: list[str],
    vault: str | None,
    here: bool,
    tools_list: list[str] | None,
) -> tuple[str | None, str | None, str | None, str | None]:
    """Parse specifier parts → (artifact_type, artifact_name, subpath, error).

    Handles both old two-positional form and new unified specifier.
    Returns (artifact_type, artifact_name, subpath, error_message).
    """
    if len(specifier_parts) == 2 and specifier_parts[0] in _TYPE_ALIASES:
        # Old two-positional form: art edit skill my-skill
        artifact_type = _TYPE_ALIASES[specifier_parts[0]]
        artifact_name = specifier_parts[1]
        subpath = None
    elif len(specifier_parts) == 1:
        # New unified form: art edit [type/]name[/sub/path]
        artifact_type, artifact_name, subpath = _parse_artifact_specifier(specifier_parts[0])
    elif len(specifier_parts) == 2 and specifier_parts[0] not in _TYPE_ALIASES:
        # Two args but first is not a type → error
        return None, None, None, (
            f"Invalid artifact specifier: {' '.join(specifier_parts)!r}. "
            "Use: art edit [type/]name or art edit <type> <name>"
        )
    else:
        return None, None, None, (
            f"Too many positional arguments. Use: art edit [type/]name or art edit <type> <name>"
        )

    return artifact_type, artifact_name, subpath, None


def handle_edit(args: argparse.Namespace) -> int:
    """Handle the edit command."""
    import subprocess

    from .utils import get_editor

    vault = getattr(args, "vault", None)
    here = getattr(args, "here", False)
    tools_str = getattr(args, "tools", None)
    force_interactive = getattr(args, "interactive", False)
    force_main = getattr(args, "main", False)
    new_file_path = getattr(args, "new_file", None)

    tools_list = None
    if tools_str:
        tools_list = [t.strip() for t in tools_str.split(",")]

    specifier_parts: list[str] = args.artifact
    artifact_type, artifact_name, subpath, parse_error = _resolve_edit_artifact(
        specifier_parts, vault, here, tools_list
    )
    if parse_error:
        print(f"Error: {parse_error}", file=sys.stderr)
        return 1

    # Auto-detect artifact type if not specified
    if artifact_type is None:
        if here:
            # For --here mode, auto-detect using project dirs
            from .utils import get_editor as _ge  # noqa: F401 (just ensure import)
            # Fall back to resolve_edit_target with each type
            resolution = None
            found_types: list[str] = []
            for atype in ("skill", "command", "agent"):
                r = resolve_edit_target(atype, artifact_name, vault=None, here=True, tools=tools_list)
                if r["success"]:
                    found_types.append(atype)
            if len(found_types) == 0:
                print(f"Error: Artifact '{artifact_name}' not found in project", file=sys.stderr)
                return 1
            if len(found_types) > 1:
                print(
                    f"Error: Ambiguous artifact name '{artifact_name}': found as {', '.join(found_types)}. "
                    f"Use a type prefix (e.g. skill/{artifact_name}).",
                    file=sys.stderr,
                )
                return 1
            artifact_type = found_types[0]
        else:
            vault_path_str = get_vault_by_name_or_path(vault) if vault else get_default_vault()
            if vault_path_str is None:
                print("Error: No default vault set. Use 'art vault add' or 'art vault init' to set up a vault.", file=sys.stderr)
                return 1
            matches = find_artifact_in_vault(artifact_name, vault_path_str)
            if len(matches) == 0:
                print(f"Error: Artifact '{artifact_name}' not found in vault", file=sys.stderr)
                return 1
            if len(matches) > 1:
                types_found = [m["type"] for m in matches]
                print(
                    f"Error: Ambiguous artifact name '{artifact_name}': found as {', '.join(types_found)}. "
                    f"Use a type prefix (e.g. skill/{artifact_name}).",
                    file=sys.stderr,
                )
                return 1
            # Use the match path directly — avoids a second vault-lookup
            match = matches[0]
            artifact_type = match["type"]
            resolved_path = match["path"]
            # Jump directly to editor logic, bypassing the resolve_edit_target call below
            editor = get_editor()
            if editor is None:
                print(
                    "Error: No editor found. Set $EDITOR or install nano, neovim, vim, or vi.",
                    file=sys.stderr,
                )
                return 1
            is_skill = artifact_type == "skill"
            # (new_file / subpath handled below after the resolve block)
            if new_file_path is not None:
                if not is_skill:
                    print(f"Error: --new-file is not supported for file-based artifact types ({artifact_type}).", file=sys.stderr)
                    return 1
                skill_dir = resolved_path.parent
                new_full = skill_dir / new_file_path
                if new_full.exists():
                    print(f"Error: File already exists: {new_file_path}", file=sys.stderr)
                    return 1
                new_full.parent.mkdir(parents=True, exist_ok=True)
                new_full.touch()
                return subprocess.run([editor, str(new_full)]).returncode
            if subpath is not None:
                if not is_skill:
                    print(f"Error: Sub-paths are not supported for file-based artifact types ({artifact_type}).", file=sys.stderr)
                    return 1
                skill_dir = resolved_path.parent
                sub_full = skill_dir / subpath
                if not sub_full.exists():
                    print(f"Error: File not found in skill: {subpath}", file=sys.stderr)
                    return 1
                return subprocess.run([editor, str(sub_full)]).returncode
            if is_skill:
                skill_dir = resolved_path.parent
                if force_main or not sys.stdin.isatty():
                    return subprocess.run([editor, str(resolved_path)]).returncode
                skill_files = _list_skill_files(skill_dir)
                if force_interactive or len(skill_files) > 1:
                    chosen = _show_skill_picker(skill_dir)
                    if chosen is None:
                        return 0
                    return subprocess.run([editor, str(chosen)]).returncode
            return subprocess.run([editor, str(resolved_path)]).returncode

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

    resolved_path: Path = resolution["path"]

    editor = get_editor()
    if editor is None:
        print(
            "Error: No editor found. Set $EDITOR or install nano, neovim, vim, or vi.",
            file=sys.stderr,
        )
        return 1

    # For skills (directory-based), resolved_path is SKILL.md; parent is the skill dir
    is_skill = artifact_type == "skill"

    # Handle --new-file flag
    if new_file_path is not None:
        if not is_skill:
            print(
                f"Error: --new-file is not supported for file-based artifact types ({artifact_type}).",
                file=sys.stderr,
            )
            return 1
        skill_dir = resolved_path.parent
        new_full = skill_dir / new_file_path
        if new_full.exists():
            print(f"Error: File already exists: {new_file_path}", file=sys.stderr)
            return 1
        new_full.parent.mkdir(parents=True, exist_ok=True)
        new_full.touch()
        result = subprocess.run([editor, str(new_full)])
        return result.returncode

    # Handle sub-path
    if subpath is not None:
        if not is_skill:
            print(
                f"Error: Sub-paths are not supported for file-based artifact types ({artifact_type}).",
                file=sys.stderr,
            )
            return 1
        skill_dir = resolved_path.parent
        sub_full = skill_dir / subpath
        if not sub_full.exists():
            print(f"Error: File not found in skill: {subpath}", file=sys.stderr)
            return 1
        result = subprocess.run([editor, str(sub_full)])
        return result.returncode

    # Skills: interactive picker logic
    if is_skill:
        skill_dir = resolved_path.parent
        # -m: always open SKILL.md directly
        if force_main:
            result = subprocess.run([editor, str(resolved_path)])
            return result.returncode
        # Non-TTY: skip picker
        if not sys.stdin.isatty():
            result = subprocess.run([editor, str(resolved_path)])
            return result.returncode
        # -i: always show picker; otherwise only if skill has files beyond SKILL.md
        skill_files = _list_skill_files(skill_dir)
        has_extra_files = len(skill_files) > 1
        if force_interactive or has_extra_files:
            chosen = _show_skill_picker(skill_dir)
            if chosen is None:
                return 0
            result = subprocess.run([editor, str(chosen)])
            return result.returncode

    result = subprocess.run([editor, str(resolved_path)])
    return result.returncode


def _resolve_artifact_for_read(
    specifier: str,
    vault: str | None,
    here: bool,
    tools_str: str | None,
) -> tuple[dict | None, str | None, str | None]:
    """Resolve an artifact for read-only commands (cat, inspect, export).

    Returns (resolution_dict, artifact_type, subpath) or (None, None, error_msg) on failure.
    resolution_dict keys: success, path (the primary file).
    """
    tools_list = [t.strip() for t in tools_str.split(",")] if tools_str else None
    artifact_type, artifact_name, subpath = _parse_artifact_specifier(specifier)

    if artifact_type is None:
        # Auto-detect
        if here:
            found_types: list[str] = []
            for atype in ("skill", "command", "agent"):
                r = resolve_edit_target(atype, artifact_name, vault=None, here=True, tools=tools_list)
                if r["success"]:
                    found_types.append(atype)
            if not found_types:
                return None, None, f"Artifact '{artifact_name}' not found in project"
            if len(found_types) > 1:
                return None, None, (
                    f"Ambiguous artifact name '{artifact_name}': found as {', '.join(found_types)}. "
                    f"Use a type prefix (e.g. skill/{artifact_name})."
                )
            artifact_type = found_types[0]
        else:
            vault_path_str = get_vault_by_name_or_path(vault) if vault else get_default_vault()
            if vault_path_str is None:
                return None, None, "No default vault set. Use 'art vault add' or 'art vault init' to set up a vault."
            matches = find_artifact_in_vault(artifact_name, vault_path_str)
            if not matches:
                return None, None, f"Artifact '{artifact_name}' not found in vault"
            if len(matches) > 1:
                types_found = [m["type"] for m in matches]
                return None, None, (
                    f"Ambiguous artifact name '{artifact_name}': found as {', '.join(types_found)}. "
                    f"Use a type prefix (e.g. skill/{artifact_name})."
                )
            # Use the match path directly — avoids a second vault-lookup in resolve_edit_target
            match = matches[0]
            return {"success": True, "path": match["path"]}, match["type"], subpath

    resolution = resolve_edit_target(
        artifact_type=artifact_type,
        artifact_name=artifact_name,
        vault=vault,
        here=here,
        tools=tools_list,
    )
    if not resolution["success"]:
        return None, None, resolution["error"]

    return resolution, artifact_type, subpath


def handle_cat(args: argparse.Namespace) -> int:
    """Handle the cat command — print artifact primary file content to stdout."""
    vault = getattr(args, "vault", None)
    here = getattr(args, "here", False)
    tools_str = getattr(args, "tools", None)

    resolution, artifact_type, subpath = _resolve_artifact_for_read(
        args.artifact, vault, here, tools_str
    )
    if resolution is None:
        print(f"Error: {artifact_type}", file=sys.stderr)  # artifact_type holds error msg here
        return 1

    resolved_path: Path = resolution["path"]
    is_skill = artifact_type == "skill"

    if subpath is not None:
        if not is_skill:
            print(
                f"Error: Sub-paths are not supported for file-based artifact types ({artifact_type}).",
                file=sys.stderr,
            )
            return 1
        skill_dir = resolved_path.parent
        sub_full = skill_dir / subpath
        if not sub_full.exists():
            print(f"Error: File not found in skill: {subpath}", file=sys.stderr)
            return 1
        print(sub_full.read_text(encoding="utf-8"), end="")
        return 0

    print(resolved_path.read_text(encoding="utf-8"), end="")
    return 0


def _parse_frontmatter(file_path: Path) -> dict:
    """Parse YAML frontmatter from a file. Returns empty dict if none found."""
    import yaml as _yaml

    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError:
        return {}

    if not text.startswith("---"):
        return {}

    lines = text.splitlines()
    end_idx = None
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        return {}

    fm_text = "\n".join(lines[1:end_idx])
    try:
        data = _yaml.safe_load(fm_text)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def handle_inspect(args: argparse.Namespace) -> int:
    """Handle the inspect command — display frontmatter and file tree."""
    vault = getattr(args, "vault", None)
    here = getattr(args, "here", False)
    tools_str = getattr(args, "tools", None)

    resolution, artifact_type, _subpath = _resolve_artifact_for_read(
        args.artifact, vault, here, tools_str
    )
    if resolution is None:
        print(f"Error: {artifact_type}", file=sys.stderr)
        return 1

    resolved_path: Path = resolution["path"]
    is_skill = artifact_type == "skill"

    # Parse frontmatter
    fm = _parse_frontmatter(resolved_path)
    print("Frontmatter:")
    if fm:
        for key, value in fm.items():
            if isinstance(value, (list, dict)):
                import yaml as _yaml
                rendered = _yaml.dump(value, default_flow_style=False).rstrip("\n")
                print(f"  {key}:")
                for line in rendered.splitlines():
                    print(f"    {line}")
            else:
                print(f"  {key}: {value}")
    else:
        print("  (no frontmatter found)")

    # File tree for directory-based artifacts
    if is_skill:
        skill_dir = resolved_path.parent
        print("\nFiles:")
        _print_skill_file_listing(skill_dir)

    return 0


def handle_export(args: argparse.Namespace) -> int:
    """Handle the export command — package artifact as a zip archive."""
    import zipfile

    vault = getattr(args, "vault", None)
    output_path_str = getattr(args, "output", None)

    resolution, artifact_type, _subpath = _resolve_artifact_for_read(
        args.artifact, vault, False, None
    )
    if resolution is None:
        print(f"Error: {artifact_type}", file=sys.stderr)
        return 1

    resolved_path: Path = resolution["path"]
    is_skill = artifact_type == "skill"

    # Determine artifact filesystem name (folder or file stem)
    if is_skill:
        artifact_dir = resolved_path.parent
        artifact_fs_name = artifact_dir.name
    else:
        artifact_fs_name = resolved_path.stem

    # Determine output zip path
    if output_path_str:
        zip_path = Path(output_path_str).expanduser().resolve()
    else:
        zip_path = Path.cwd() / f"{artifact_fs_name}.zip"

    if zip_path.exists():
        print(f"Error: Output path already exists: {zip_path}", file=sys.stderr)
        return 1

    if not zip_path.parent.exists():
        print(f"Error: Output directory does not exist: {zip_path.parent}", file=sys.stderr)
        return 1

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        if is_skill:
            for f in artifact_dir.rglob("*"):
                if f.is_file():
                    arcname = f"{artifact_fs_name}/{f.relative_to(artifact_dir)}"
                    zf.write(f, arcname)
        else:
            arcname = f"{artifact_fs_name}/{artifact_fs_name}.md"
            zf.write(resolved_path, arcname)

    print(f"Exported: {artifact_fs_name} -> {zip_path}")
    return 0


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
        display_name = getattr(args, "display_name", None)

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
        vault_paths = _resolve_vault_paths(args)
        if not vault_paths:
            resolution = resolve_vault_target(artifact_name, artifact_type=artifact_type, vault=None)
            if not resolution["success"]:
                print(f"Error: {resolution['error']}", file=sys.stderr)
                return 1
            targets = [resolution["path"]]
        else:
            targets = []
            for vp in vault_paths:
                resolution = resolve_vault_target(artifact_name, artifact_type=artifact_type, vault=str(vp))
                if not resolution["success"]:
                    print(f"Error: {resolution['error']}", file=sys.stderr)
                    return 1
                targets.append(resolution["path"])

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
    try:
        return _main()
    except KeyboardInterrupt:
        print()
        return 130


def _main() -> int:
    """Internal main dispatch."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    if args.command in ("ls", "list"):
        return handle_list(args)

    if args.command == "rm":
        return handle_rm(args)

    if args.command in ("project", "proj", "p"):
        proj_cmd = getattr(args, "proj_command", None)
        if proj_cmd is None:
            parser.parse_args([args.command, "--help"])
            return 0
        if proj_cmd == "import":
            return handle_proj_import(args)
        if proj_cmd == "rm":
            return handle_proj_rm(args)
        if proj_cmd == "wipe":
            return handle_proj_wipe(args)
        if proj_cmd in ("ls", "list"):
            return handle_proj_list(args)
        if proj_cmd in ("link", "ln"):
            return handle_proj_link(args)
        if proj_cmd in ("unlink", "uln"):
            return handle_proj_unlink(args)

    if args.command in ("config", "conf", "c"):
        conf_cmd = getattr(args, "conf_command", None)
        if conf_cmd is None:
            parser.parse_args([args.command, "--help"])
            return 0
        if conf_cmd == "import":
            return handle_conf_import(args)
        if conf_cmd == "rm":
            return handle_conf_rm(args)
        if conf_cmd == "wipe":
            return handle_conf_wipe(args)
        if conf_cmd in ("ls", "list"):
            return handle_conf_list(args)
        if conf_cmd in ("edit", "ed"):
            return handle_config_edit(args)
        if conf_cmd in ("link", "ln"):
            return handle_conf_link(args)
        if conf_cmd in ("unlink", "uln"):
            return handle_conf_unlink(args)

    if args.command in ("vault", "v"):
        if args.vault_command is None:
            parser.parse_args([args.command, "--help"])
            return 0

        if args.vault_command == "add":
            return handle_vault_add(args)
        if args.vault_command in ("init", "create", "cr"):
            return handle_vault_init(args)
        if args.vault_command == "rm":
            return handle_vault_rm(args)
        if args.vault_command == "name":
            return handle_vault_name(args)
        if args.vault_command == "select":
            return handle_vault_select(args)
        if args.vault_command in ("ls", "list"):
            return handle_vault_list(args)
        if args.vault_command in ("copy", "cp"):
            return handle_vault_copy(args)
        if args.vault_command == "export":
            return handle_vault_export(args)
        if args.vault_command == "import":
            return handle_vault_import(args)

    if args.command in ("copy", "cp"):
        return handle_copy(args)

    if args.command in ("tool", "t"):
        if args.tool_command is None:
            parser.parse_args([args.command, "--help"])
            return 0

        if args.tool_command == "select":
            return handle_tool_select(args)
        if args.tool_command in ("ls", "list"):
            return handle_tool_list(args)
        if args.tool_command == "add":
            return handle_tool_add(args)
        if args.tool_command == "rm":
            return handle_tool_rm(args)
        if args.tool_command == "info":
            return handle_tool_info(args)

    if args.command == "nav":
        return handle_nav(args)

    if args.command == "shell":
        shell_cmd = getattr(args, "shell_command", None)
        if shell_cmd is None:
            parser.parse_args(["shell", "--help"])
            return 0
        if shell_cmd == "setup":
            return handle_shell_setup(args)

    if args.command in ("spelunk", "sp"):
        return handle_spelunk(args)

    if args.command in ("store", "st"):
        return handle_store(args)

    if args.command in ("edit", "ed"):
        return handle_edit(args)

    if args.command == "cat":
        return handle_cat(args)

    if args.command == "inspect":
        return handle_inspect(args)

    if args.command == "export":
        return handle_export(args)

    if args.command in ("create", "cr"):
        if args.create_command is None:
            parser.parse_args([args.command, "--help"])
            return 0

        if args.create_command in ("skill", "s", "sk"):
            return handle_create_skill(args)
        if args.create_command in ("command", "c", "cmd", "com"):
            return handle_create_artifact(args, "command")
        if args.create_command in ("agent", "a", "agt", "ag"):
            return handle_create_artifact(args, "agent")

    return 0


if __name__ == "__main__":
    sys.exit(main())
