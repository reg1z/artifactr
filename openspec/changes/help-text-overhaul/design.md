## Context

The `art` CLI uses Python's `argparse` which auto-generates help text from subparser registrations. The default output lists all subcommands flat under "positional arguments" with no grouping. We need categorized output while keeping all subparsers functionally intact for routing and individual `--help`.

## Goals / Non-Goals

**Goals:**
- Categorized, scannable `art --help` output with grouped commands
- Clean usage line: `art [-h] [--version] <command> [<args>]`
- Concise documentation of default-targeting behavior
- Every subcommand has an informative `help=` description

**Non-Goals:**
- Customizing help output for individual subcommands (e.g., `art vault --help`)
- Adding a documentation spec for README.md formatting (separate effort)
- Changing any command behavior

## Decisions

### Custom formatter via subclass
**Decision**: Create `ArtHelpFormatter(argparse.RawDescriptionHelpFormatter)` that overrides `_format_action` (to suppress auto-generated subparser listing) and `_format_usage` (for a clean usage line). The categorized command list lives in the parser's `epilog` string.

**Alternatives considered**:
- **Pure epilog with SUPPRESS**: Setting `help=argparse.SUPPRESS` on each subparser. Rejected because argparse still shows the positional arguments group header and `==SUPPRESS==` can leak in edge cases. Also, SUPPRESS could interfere with argparse-manpage or similar tooling that reads `help=` values.
- **Fully custom `format_help()`**: Complete override. Rejected as over-engineered — we only need to suppress two things (subparser list and usage line).

**Rationale**: The custom formatter approach gives full visual control over the top-level help while leaving all subparser `help=` strings intact. Tools that introspect the parser tree (like argparse-manpage) read `help=` directly, not the formatted output, so they remain compatible.

### Epilog-based command categories
**Decision**: Define the categorized command list as a multi-line string in the `epilog` parameter. Categories:
- **Vault Operations**: `ls`, `rm`, `store`, `edit`, `create`
- **Namespaces**: `vault`, `tool`, `project`, `config` (with aliases shown)
- **Discovery**: `spelunk`

**Rationale**: `RawDescriptionHelpFormatter` preserves whitespace in the epilog, allowing hand-formatted columns. The epilog only changes when commands are added/removed (infrequent).

### Default-targeting note in description
**Decision**: Add a one-liner below the main description: "Commands target the active vault/tool by default (see: art vault select, art tool select)."

**Rationale**: Keeps it visible without repeating on every subcommand. The project-targeting note goes in `art project --help` since it's namespace-specific.

## Risks / Trade-offs

- **[Private API usage: `_format_action`, `_format_usage`]** → These are stable internal methods in `argparse` that haven't changed across Python 3.x versions. The risk of breakage is low, and the fallback is a slightly uglier help output (not a crash).
- **[Manual epilog maintenance]** → Adding a new top-level command requires updating the epilog string. Acceptable given the low frequency of new commands.
