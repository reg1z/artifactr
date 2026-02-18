## Context

`cli.py` is the sole file containing all parser construction. It currently uses a mix of bare `argparse.ArgumentParser` (root), bare `argparse.ArgumentParser` subparsers (all sub-parsers), and a custom `ArtHelpFormatter` applied only to the root parser. Some leaf commands have `description=` strings, others have none. Aliases are visible in parent listings but never in a command's own help output. No-args behavior on leaf commands with required positionals produces a bare argparse error with no contextual help.

The `ArtHelpFormatter` already overrides `_format_action` (to suppress the auto-generated subparser list) and `_format_usage` (for the custom root usage line). It extends `RawDescriptionHelpFormatter`, which preserves whitespace in `description=` and `epilog=` — a critical property for structured multi-section output.

## Goals / Non-Goals

**Goals:**
- Provide a `make_help()` function that produces consistent `description=`, `epilog=`, and `formatter_class=` kwargs for any `add_parser()` call.
- Introduce `ArtArgumentParser` so that specific parsers can print full help before an argparse error, with per-parser opt-in via `show_help_on_error`.
- Standardize the rendered sections: Summary, Aliases, Workflows, See Also, Notes.
- Reorder all subcommands alphabetically within each namespace.
- Document the conventions in AGENTS.md.

**Non-Goals:**
- Changes to any handler logic or business modules.
- Adding an `--examples` flag (roadmap item).
- Changing the root parser's custom epilog (categorized command groups) — that format is already established and tested.
- Rewriting tests; existing tests should still pass. New tests cover `make_help()` output and `ArtArgumentParser.error()` behavior.

## Decisions

### `make_help()` returns a dict of kwargs, not a string

**Decision**: `make_help()` returns `{"description": ..., "epilog": ..., "formatter_class": ...}` to be unpacked with `**` at the `add_parser()` call site.

**Rationale**: A string-only helper can only populate `description=`. The format requires `epilog=` for optional sections (Workflows, See Also, Notes) and `formatter_class=` to ensure `RawDescriptionHelpFormatter` is applied to every subparser (currently only the root has it). Returning a dict makes `make_help()` the single configuration source for help rendering, and the call site is readable: `**make_help(summary="...", aliases=[...])`.

**Alternative considered**: Separate helpers for description and epilog. Rejected — two call sites per parser doubles the surface area for drift and makes it easy to forget one.

### `ArtArgumentParser` with `show_help_on_error: bool = False`

**Decision**: Subclass `argparse.ArgumentParser`; override `error()` to conditionally call `self.print_help(sys.stderr)` before `super().error(message)`. Default the flag to `False`; opt in per-parser.

**Rationale**: Defaulting to `False` forces deliberate per-command decisions about whether showing the full help on an error is actually helpful (e.g., a 30-line `project import` help dump on a typo may obscure the error). The flag is trivially toggled. Calling `super().error()` preserves argparse's error formatting and exit code (`2`).

**Alternative considered**: Always show help on error (no flag). Rejected — for commands with long option lists, this buries the error message and adds noise for experienced users who mistype a flag.

**Alternative considered**: Detect "missing required" errors by message string. Rejected — brittle; argparse message strings are not part of any public API.

### `formatter_class` baked into `make_help()`

**Decision**: `make_help()` always includes `"formatter_class": argparse.RawDescriptionHelpFormatter` in its return dict.

**Rationale**: Without `RawDescriptionHelpFormatter`, argparse word-wraps `description=` and `epilog=` freely, breaking the intentional layout of multi-section epilog text. Baking it into `make_help()` means it's never accidentally omitted. `ArtHelpFormatter` (root-only) extends `RawDescriptionHelpFormatter`, so the root retains all its custom behavior; subparsers use `RawDescriptionHelpFormatter` directly since they don't need the subcommand-suppression override.

### Alphabetical ordering is enforced at call site, not runtime

**Decision**: Reorder `add_parser()` calls in source. Do not sort at runtime.

**Rationale**: argparse preserves insertion order in help output. Sorting at source is explicit, reviewable in diffs, and requires no runtime logic. Alphabetical is unambiguous — no judgment calls needed per namespace.

### Namespace no-args handling via `show_help_on_error` replaces `parse_args(["x", "--help"])` hack

**Decision**: Remove the `parser.parse_args(["namespace", "--help"])` calls in `_main()` dispatch. Instead, set `show_help_on_error=True` on namespace parsers. When a namespace is invoked with no subcommand, argparse will not raise an error (subcommands aren't strictly required by argparse for namespace parsers) — so the existing `if args.vault_command is None: parser.print_help(); return 0` pattern is kept as-is, which already works correctly.

**Clarification**: `show_help_on_error=True` on namespace parsers handles the case where *argparse itself* raises an error (e.g., unrecognized argument). The no-subcommand case is already handled explicitly in `_main()` and doesn't need to change.

## Risks / Trade-offs

- **Large diff, low logic risk**: This change touches nearly every `add_parser()` call in a ~3,270-line file. The risk is mechanical (missing a call, wrong alias, off-by-one in epilog spacing) rather than behavioral. Careful review of rendered output with `art <cmd> --help` after implementation is essential.
- **`RawDescriptionHelpFormatter` requires manual line management**: Descriptions and epilog text must handle their own wrapping (≤80 chars recommended). Long summaries need manual newlines. [Risk] → Keep summary strings short; `make_help()` can enforce a lint-style check or just rely on author discipline.
- **Alphabetical reordering changes test assertions**: Any tests that assert on the order of subcommands listed in help output will need updating. [Risk] → Search for such assertions before and after implementation.

## Open Questions

- *(Resolved)* Workflow vs. Workflows: **Workflows** (plural).
- *(Resolved)* `show_help_on_error` default: **False**.
- *(Deferred)* Specific `see_also` content per command: fill in obvious pairs now (link/unlink, proj import/config import), leave rest as `None` for future PRs.
- *(Deferred)* `--examples` flag: roadmap item, not in scope.
