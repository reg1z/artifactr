## Why

The `art` CLI's `--help` output is inconsistent: some commands have rich description paragraphs, others have none; aliases are undocumented in a command's own help screen; no-args behavior varies unpredictably between silently showing help and throwing a bare argparse error; and subcommand ordering differs across namespaces. This creates a fragmented experience that's hard to navigate and harder to maintain as the CLI grows.

## What Changes

- **New `make_help()` helper**: A function that produces standardized `description=`, `epilog=`, and `formatter_class=` kwargs for every `add_parser()` call, enforcing a consistent format by construction.
- **New `ArtArgumentParser` class**: Subclass of `argparse.ArgumentParser` with a `show_help_on_error: bool = False` flag. When `True`, the `error()` method prints full help to stderr before the error message. Replaces bare `argparse.ArgumentParser` as the parser class everywhere.
- **Standardized help sections**: Every command's `--help` gains a structured format with: Summary (1–2 sentences), Aliases (leaf-level, optional), Workflows (optional), See Also (optional), Notes (optional).
- **Alphabetical subcommand ordering**: All `add_parser()` registrations reordered alphabetically within each namespace (`vault`, `tool`, `project`, `config`, `create`).
- **`show_help_on_error=True`** on specific commands: namespace parsers (`vault`, `project`, `tool`, `config`, `create`) and leaf commands where required args aren't self-evident (`edit`, `rm`, `vault add`, `vault init`, `vault rm`, `vault name`, `vault select`, `create skill`, `create command`, `create agent`).
- **AGENTS.md documentation**: New alias maintenance rule and `## Help Text Format` section documenting `make_help()` conventions.

## Capabilities

### New Capabilities

- `help-text-standard`: The `make_help()` helper function and `ArtArgumentParser` class — the infrastructure that makes standardized, consistent help output possible across all commands.

### Modified Capabilities

- `help-formatting`: New requirements for Aliases, Workflows, See Also, and Notes sections in per-command help output; no-args behavior via `ArtArgumentParser`; alphabetical subcommand ordering.

## Impact

- `src/artifactr/cli.py`: Primary file. New `ArtArgumentParser` class, new `make_help()` function, all `add_parser()` calls updated with `**make_help(...)` and reordered alphabetically. `add_subparsers()` calls updated to pass `parser_class=ArtArgumentParser`. Namespace no-args handling simplified (replace `parse_args(["x", "--help"])` pattern with `show_help_on_error` on the parser).
- `AGENTS.md`: Two additions — alias maintenance rule under Conventions, new Help Text Format section.
- No changes to business logic modules, tests for behavior, or external dependencies.
