## Context

Skills are the only directory-based artifact type. Commands and agents are single `.md` files, but a skill lives at `<vault>/skills/<name>/` with `SKILL.md` as its primary file and arbitrarily nested supporting files (e.g. `references/`, `templates/`). The current `art edit skill <name>` opens only `SKILL.md` via `subprocess.run([editor, path])` — the rest of the directory is invisible to the tooling.

The `handle_edit` function currently requires `artifact_type` as a mandatory positional argument. Multiple commands already use the `type/name` prefix syntax (e.g. `art rm`, `art copy`) with a consistent set of type aliases (`s`, `sk`, `c`, `cmd`, `a`, `agt`).

## Goals / Non-Goals

**Goals:**
- Interactive file picker for directory-based artifacts (skills) during `art edit`
- Sub-path targeting: `art edit my-skill/refs/hooks.md`, `art cat my-skill/refs/hooks.md`
- Optional type prefix on `art edit`; type auto-detected from artifact name when omitted
- `art ls <artifact-name>` to list files within a directory-based artifact
- `art cat` to print the primary file content of any artifact
- `art inspect` to display structured frontmatter + file tree
- `art export` to package a single artifact as a portable `.zip`
- `art store ./artifact.zip` auto-detecting zip input (single artifact or vault bundle)

**Non-Goals:**
- Recursive or nested interactive picker (single-level file tree is sufficient)
- `art edit` launching an editor on the skill *directory* (incompatible with terminal editors)
- Vault-level operations (handled by `art vault export/import`)
- Metadata manifest in exported zips
- Windows symlink-specific handling (covered by existing `windows-link-fallback` spec)

## Decisions

### Decision: Interactive picker is terminal readline, not a TUI library

**Options considered:**
- A: Use a TUI library (e.g. `curses`, `prompt_toolkit`) for arrow-key navigation
- B: Numbered menu using stdlib `input()` with plain terminal output

**Choice: B** — `prompt_toolkit` and `curses` add complexity and platform risk. A numbered menu using `input()` works identically on all platforms, in all terminal emulators, and over SSH. The picker renders the file tree with indices and action keys, then reads a single line of input. This is consistent with how other interactive `art` commands (e.g. `art store` selection) work.

### Decision: Sub-path uses slash-delimited positional, not a `--file` flag

`art edit my-skill/references/hooks.md` vs `art edit my-skill --file references/hooks.md`.

**Choice: slash-delimited positional** — Consistent with the existing `type/name` prefix convention used across `art rm`, `art cp`, `art nav`. The parser distinguishes type-prefix tokens (known aliases: `s`, `sk`, `c`, `cmd`, `a`, `agt`, `ag`) from artifact names, then treats remaining segments as the sub-path. This means `type/name/sub/path` is unambiguous.

### Decision: `art edit` type argument becomes optional, retaining backward compatibility

The current parser defines `artifact_type` and `artifact_name` as two separate positionals. The new form collapses them into a single positional (`artifact`) that accepts the full `[type/]name[/sub/path]` specifier, with backward compatibility for the old two-positional form.

**Migration**: The argparse parser accepts either one positional (new unified form) or two positionals (old `type name` form) by inspecting whether the first argument is a known type alias. This avoids a breaking change.

### Decision: Picker auto-opens only when skill has files beyond `SKILL.md`

If a skill contains only `SKILL.md`, `art edit my-skill` opens `SKILL.md` directly (no picker). If the skill has additional files, the picker opens. `-i`/`--interactive` forces the picker regardless. `-m`/`--main` always skips the picker and opens `SKILL.md` directly.

**Rationale**: Prevents friction for the common case of simple skills while surfacing the picker when it provides navigation value.

### Decision: `art export` produces a zip with the artifact directory at the root

For skills:
```
my-skill.zip
  └── my-skill/
        SKILL.md
        references/
          hooks.md
```
For commands/agents (file-based), the `.md` file is placed inside a single-directory wrapper with the artifact name:
```
my-command.zip
  └── my-command/
        my-command.md
```
This makes the format consistent (always a named directory at root), compatible with Claude.ai's skill zip upload format, and importable via `art store ./my-skill.zip`.

### Decision: `art store` zip detection via file extension + content inspection

When `art store ./something.zip` is run:
1. Detect `.zip` extension → unzip to `tempfile.mkdtemp()`
2. Inspect root entries:
   - Single directory containing `SKILL.md` → single skill, auto-store without selection modal
   - Single directory containing a `.md` file matching directory name → single command/agent, auto-store
   - Multiple root directories OR root contains `skills/`/`commands/`/`agents/` → vault bundle → show selection modal
3. Clean up temp dir after store completes

`tempfile.mkdtemp()` resolves to the platform-appropriate temp directory (`/tmp` on Linux, `$TMPDIR` on macOS, `%TEMP%` on Windows) with no extra handling needed.

### Decision: No manifest in exported artifact zips

Vault exports (`art vault export`) use `manifest.yaml` to register multiple vaults. Single-artifact exports carry no manifest — the zip structure itself is the contract. This keeps the format minimal and compatible with third-party tools (e.g. Claude.ai zip upload).

## Risks / Trade-offs

- **Picker input() blocks on non-interactive stdin** → If `art edit` is called in a script or piped, the picker would block. Mitigation: detect `sys.stdin.isatty()` before showing picker; if not a TTY, fall back to opening the primary file directly (same as single-file behavior).
- **Sub-path parsing ambiguity if artifact names contain slashes** → Artifact names cannot contain path separators by convention (filesystem constraint). Not a practical risk.
- **`art store` zip detection heuristic can misclassify edge cases** → A vault zip that happens to contain only one artifact would be treated as a single-artifact zip. Acceptable trade-off; user can always use `art vault import` for vault zips explicitly.
- **Backward compatibility for `art edit skill my-skill` (two positionals)** → The two-positional old form must still work. The parser needs to distinguish "is the first arg a type alias?" to route correctly.

## Open Questions

- None — all decisions resolved during exploration.
