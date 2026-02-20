## Context

Six small UX gaps were identified across `art spelunk`, `art create`, `art nav` shell wrapper, the top-level parser, and help text. All changes are additive or alter defaults — no public APIs or data formats change. The codebase has no network connections or external services to coordinate with, so rollout and rollback are both trivial (revert a version bump, restore a string).

## Goals / Non-Goals

**Goals:**
- `art spelunk` defaults to CWD when no target is given, with `-g`/`--global` as the deliberate opt-in for global config
- `art create type/name` is accepted as an alternative to `art create type name`
- `art nav --help` displays properly formatted help text in shell environments
- Top-level `art -V` prints the version
- Main help epilog uses "Artifact Operations" instead of "Vault Operations"
- Version advances to 0.3.2

**Non-Goals:**
- Changing any other command defaults
- Modifying behavior when an explicit target is provided to `art spelunk`
- Adding slash syntax to any command other than `art create` (all others already support it)

## Decisions

### D1: Spelunk CWD default — change the `if` condition in `handle_spelunk`

**Decision**: Replace `if target_str is None or global_spelunk:` with `if global_spelunk:` and default `target` to `Path.cwd()` when no target is given.

**Rationale**: CWD is the obvious expected default for a "discover what's here" command. The `-g`/`--global` flag already exists; we just need to make it the explicit path rather than the implicit one. No new argument parsing is needed.

**Ripple effects**:
- `original_target` must be `Path.cwd()` (not `None`) when no target is given, so the LOCATION column produces relative paths instead of falling back to absolute paths.
- The import-cache loading condition (`if target_str and not global_spelunk:`) must also fire for the CWD default (i.e., when `target_str is None` but `global_spelunk is False`).
- `_compute_spelunk_location`'s `original_target is None` branch was only ever hit in the global case; it should be simplified to `if global_spelunk:` now.

### D2: `art create` slash syntax — argv pre-processing in `_main()`

**Decision**: Pre-process `sys.argv[1:]` in `_main()` before calling `parser.parse_args(argv)`, expanding `["create", "skill/my-skill", ...]` to `["create", "skill", "my-skill", ...]`.

**Why not handle it at the dispatch level?** With argparse subparsers, the slash-notation string is treated as the subcommand name. If `"skill/my-skill"` doesn't match any registered subparser, argparse raises an error before we ever reach the `if args.command in ("create", "cr"):` block. We must intercept before `parse_args`.

**Why not a separate top-level `art create skill/name` parser?** That would require duplicating all the subparser argument definitions (description, field flags, vault flags, etc.) for a second entry point, adding maintenance burden.

**Implementation**: In `_main()`, before `parser.parse_args(argv)`:
```
if len(argv) >= 2 and argv[0] in ("create", "cr") and "/" in argv[1]:
    type_part, _, name_part = argv[1].partition("/")
    if type_part in _TYPE_ALIASES and name_part:
        argv = [argv[0], type_part, name_part] + argv[2:]
```
This is non-destructive: if the slash form is invalid (unknown type, empty name), argv is left unchanged and the normal subparser error fires.

### D3: Shell wrapper `--help` fix — detect help flags before the nav intercept

**Decision**: In all four shell snippets, add a loop before the `--print` path that detects `--help` or `-h` among the nav args and short-circuits to `command art "$@"`.

**Why not check the exit code of the `--print` invocation?** `argparse --help` exits with code 0, so the wrapper cannot distinguish a successful path print from a help invocation by exit code alone.

**Why not strip `--print` when `--help` is present?** Routing to `command art "$@"` is simpler and handles any future help-triggering flags (e.g., if a `--man` flag were added).

### D4: `-V` for `--version` — top-level parser only

**Decision**: Add `"-V"` to the `--version` argument at the top-level parser in `create_parser()`.

**No conflict**: Subcommand parsers use `-V` for `--vault`, but those are separate argument parsers with independent namespaces.

### D5: "Artifact Operations" rename — single string change

**Decision**: Change `"Vault Operations:\n"` to `"Artifact Operations:\n"` in the top-level parser's epilog. No spec-level behavior changes.

## Risks / Trade-offs

- **Spelunk test breakage**: Any test that calls `art spelunk` with no target and expects global-config results will fail. These tests must be updated to use `art spelunk -g` or to mock/set CWD. Low risk — easy to identify and fix.
- **Shell snippet upgrade gap**: Users with already-installed shell snippets will not get the `--help` fix until they re-run `art shell setup`. This is acceptable — no behavior regression for existing users, just a missing improvement.
- **argv mutation in `_main()`**: Pre-processing `sys.argv` via a local `argv` variable is clean. We pass `argv` to `parse_args(argv)` instead of the no-argument form. This requires changing `_main()` to work with a local list rather than relying on `parse_args()` reading `sys.argv[1:]` implicitly — a minor refactor with no functional impact.

## Open Questions

None — all decisions are clear from the exploration session.
