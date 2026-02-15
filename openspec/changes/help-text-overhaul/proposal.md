## Why

The current `art --help` output dumps all subcommands in a flat, uncategorized list. Users can't quickly distinguish namespace commands (vault, tool, project, config) from direct vault operations (ls, rm, store, edit, create) or discovery (spelunk). The base description is outdated, and implicit behavior like default vault/tool targeting isn't documented in help text.

## What Changes

- **Custom help formatter**: Replace the default argparse help output for the base `art` command with a categorized layout using a custom formatter class and hand-crafted epilog.
- **Categorized command groups**: Group commands into "Vault Operations", "Namespaces", and "Discovery" sections in the epilog.
- **Updated base description**: Change from "Manage AI project artifacts across repositories" to "Manage AI artifacts across multiple configurations, tools, & repositories."
- **Default-targeting documentation**: Add concise notes in help text explaining that commands default to the active vault/tool, and that `art project` commands target the current directory unless `--target` is specified.
- **Subcommand descriptions**: Ensure every command and subcommand has an informative `help=` string.

## Capabilities

### New Capabilities
- `help-formatting`: Specification for how `art --help` output is structured, including the custom formatter class, categorized command groups, and documentation conventions.

### Modified Capabilities
_(None — this change is purely about presentation, not about changing command behavior or requirements.)_

## Impact

- `src/artifactr/cli.py`: New `CustomHelpFormatter` class, updated parser description, added epilog string, updated `help=` strings on all subparsers.
- No behavioral changes to any commands.
- No dependency changes.
