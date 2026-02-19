## Context

artifactr currently has no guided install path — users must know to reach for `pipx` or `pip` themselves. The installer is a standalone bash script (no Python bootstrap) that handles everything: environment detection, Python version gating, venv/pipx setup, PATH wiring, upgrade, and uninstall. It is fully external to the Python package; no changes to `src/artifactr/`.

Target platforms: Linux, macOS. Windows deferred (documented in README as future `install.ps1`).

## Goals / Non-Goals

**Goals:**
- Single curl command installs `art` globally with no prior knowledge of Python tooling
- Tiered install: pipx if present, managed venv if not
- Idempotent upgrade path; friendly "already up to date" if no upgrade available
- Clean uninstall via `--uninstall` flag on the same script
- `-y/--yes` for non-interactive use
- State file so uninstall knows how it was installed and which rc file was touched

**Non-Goals:**
- Installing Python itself (check and fail gracefully with instructions if absent)
- Windows `install.ps1` (acknowledged future work)
- Integration with any artifactr Python code (pure shell script)
- Package manager detection beyond `pipx` and `pip`/venv

## Decisions

### 1. Pure bash, no Python bootstrap phase
The script invokes `python3` only for `venv` creation and `pip install`. All control flow is POSIX-compatible bash. This keeps the script auditable and avoids a chicken-and-egg dependency problem.

*Alternatives considered*: A Python installer script (would require Python already callable — same constraint, but less familiar to users reading a shell script).

### 2. Tiered install strategy: pipx → venv
```
pipx available?
  yes → pipx install artifactr      (pipx manages venv + PATH automatically)
  no  → python3 -m venv $DATA_DIR/.venv
        .venv/bin/pip install artifactr
        mkdir -p ~/.local/bin
        ln -sf $DATA_DIR/.venv/bin/art ~/.local/bin/art
```
pipx is preferred because it handles isolation and PATH natively. The venv path is the self-contained fallback for users who haven't installed pipx.

### 3. Platform-specific data directory
```
Linux:  ~/.local/share/artifactr/   (XDG_DATA_HOME convention)
macOS:  ~/Library/Application Support/artifactr/
```
Aligns with where artifactr's own `get_config_dir()` places config on macOS. The venv lives under `$DATA_DIR/.venv/` and the state file at `$DATA_DIR/.install-info`.

*Note*: macOS path contains a space — every reference to `$DATA_DIR` MUST be double-quoted in the script.

### 4. Python version check via sys.version_info
```bash
python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
```
Avoids parsing the `python3 --version` string, which varies across distributions (pre-release suffixes, local build tags). Exit code carries the verdict cleanly.

### 5. State file: flat key=value text
`$DATA_DIR/.install-info` format:
```
method=pipx
rc_file=/home/user/.zshrc
```
Written at install time. Read back at upgrade/uninstall time using POSIX `while IFS='=' read -r key value`. No external tools required. `rc_file` is empty/absent if the user declined PATH modification or if PATH was already set.

For pipx installs, `$DATA_DIR` is created explicitly to hold the state file (pipx manages its own venv elsewhere).

### 6. Upgrade detection
Capture `pip install --upgrade` or `pipx upgrade` output. If the output contains "already satisfied" (pip) or "already installed" (pipx), print a friendly "artifactr is already up to date" rather than surfacing raw tool output. Otherwise, confirm the new version installed.

### 7. Uninstall via --uninstall flag (same script)
Single script URL; uninstall is `curl ... | bash -s -- --uninstall`. Reads state file to decide between `pipx uninstall artifactr` and `rm -rf "$DATA_DIR" && rm -f ~/.local/bin/art`. If `rc_file` was recorded, shows the PATH line and prompts to remove it (or removes it with `--yes`).

### 8. Confirmation model
Every action that modifies the system (install, PATH change, uninstall) is shown to the user with a prompt before execution. `--yes/-y` auto-answers yes to all prompts. This makes non-interactive usage (CI, dotfiles scripts) straightforward without sacrificing transparency for interactive users.

## Risks / Trade-offs

- **Pre-existing manual install (no state file)** → If `art` is found in PATH but no state file exists, the script cannot know how it was installed. Mitigation: detect this case, print a warning, and offer the user guidance to uninstall manually.
- **macOS spaces in path** → `~/Library/Application Support/` must be consistently quoted. Mitigation: assign to a variable immediately and double-quote every use.
- **rc file heuristic** → Shell detection uses `$SHELL` env var; users with non-standard configs may have their PATH added to the wrong file. Mitigation: always show the user what rc file was chosen and what line was added before writing; they can adjust manually.
- **pipx upgrade "already installed" text** → Output text may change across pipx versions. Mitigation: match loosely (`grep -q "already installed"`) and fall back gracefully to showing raw output if match fails.
- **PATH export idempotency** → If the user runs the installer twice, we may add the PATH export twice. Mitigation: before writing, grep the rc file for `/.local/bin` and skip if already present.

## Open Questions

- None — scope is fully defined by the exploration session.
