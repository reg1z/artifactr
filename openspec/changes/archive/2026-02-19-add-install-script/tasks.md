## 1. Script Skeleton and Argument Parsing

- [x] 1.1 Create `install.sh` at repo root with shebang (`#!/usr/bin/env bash`) and `set -euo pipefail`
- [x] 1.2 Implement argument parsing loop: `--yes`/`-y` sets `AUTO_YES=1`; `--uninstall` sets `UNINSTALL=1`; unknown flags print usage and exit non-zero
- [x] 1.3 Implement `confirm()` helper: prints message + `[y/N]`, auto-answers yes when `AUTO_YES=1`, returns 0 for yes and 1 for no

## 2. Platform and Environment Detection

- [x] 2.1 Detect OS via `uname -s`; set `DATA_DIR` to `$HOME/.local/share/artifactr` (Linux) or `$HOME/Library/Application Support/artifactr` (macOS)
- [x] 2.2 Detect Windows (`MINGW*`, `CYGWIN*`, `MSYS*`) and exit with message directing user to future `install.ps1`
- [x] 2.3 Detect shell rc file from `$SHELL` basename (bash → `~/.bashrc`, zsh → `~/.zshrc`, fish → `~/.config/fish/config.fish`, sh/dash → `~/.profile`); fall back to `~/.profile` if unknown

## 3. Python Version Check

- [x] 3.1 Check `command -v python3`; exit with "python3 not found" message and python.org URL if absent
- [x] 3.2 Run `python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"`; if non-zero, detect and print the actual version, state "Python 3.10+ required", and exit non-zero

## 4. State File Helpers

- [x] 4.1 Implement `read_state_file()`: uses `while IFS='=' read -r key value` to populate `INSTALL_METHOD` and `RC_FILE` variables from `$DATA_DIR/.install-info`; no-ops silently if file absent
- [x] 4.2 Implement `write_state_file()`: uses `printf` to write `method` and (optionally) `rc_file` keys to `$DATA_DIR/.install-info`; creates `$DATA_DIR` first with `mkdir -p`

## 5. Install Flow

- [x] 5.1 Detect existing install: check `command -v art`; if found, branch to upgrade flow (Section 6); if not found, proceed with fresh install
- [x] 5.2 Show install summary (what will be installed, where, which method) and call `confirm()`; exit cleanly if declined
- [x] 5.3 Implement pipx install path: run `pipx install artifactr`, write state file with `method=pipx`
- [x] 5.4 Implement venv install path: `mkdir -p "$DATA_DIR"`, `python3 -m venv "$DATA_DIR/.venv"`, `"$DATA_DIR/.venv/bin/pip" install artifactr`, `mkdir -p ~/.local/bin`, `ln -sf "$DATA_DIR/.venv/bin/art" ~/.local/bin/art`; write state file with `method=venv`
- [x] 5.5 Implement PATH check (venv installs only): check if `~/.local/bin` is in `$PATH`; if absent, check rc file for existing `/.local/bin` reference (idempotency guard); if not already there, show rc file path + line to be added, call `confirm()`, append `export PATH="$HOME/.local/bin:$PATH"` to rc file; update state file with `rc_file=<path>`
- [x] 5.6 Print success message with installed version and reminder to `source <rc_file>` if PATH was modified

## 6. Upgrade Flow

- [x] 6.1 Call `read_state_file()`; if `$DATA_DIR/.install-info` is absent but `art` was found in PATH, print unmanaged-install warning and exit non-zero
- [x] 6.2 Implement pipx upgrade: capture output of `pipx upgrade artifactr`; grep for "already installed" → print "artifactr is already up to date." and exit 0; otherwise print version confirmation
- [x] 6.3 Implement venv upgrade: capture output of `"$DATA_DIR/.venv/bin/pip" install --upgrade artifactr`; grep for "already satisfied" → print "artifactr is already up to date." and exit 0; otherwise print version confirmation

## 7. Uninstall Flow

- [x] 7.1 Detect if installed: check `command -v art` OR existence of `$DATA_DIR/.install-info`; if neither, print "artifactr does not appear to be installed." and exit 0
- [x] 7.2 Show uninstall summary and call `confirm()`; exit cleanly if declined
- [x] 7.3 Implement pipx uninstall: run `pipx uninstall artifactr`; remove `$DATA_DIR` (state file dir only)
- [x] 7.4 Implement venv uninstall: `rm -rf "$DATA_DIR"` and `rm -f ~/.local/bin/art`
- [x] 7.5 If `RC_FILE` is set in state, show the PATH export line and call `confirm()` to remove it; use a portable `grep -v` + temp file swap to delete the line from the rc file
- [x] 7.6 Print "artifactr uninstalled successfully."

## 8. README Update

- [x] 8.1 Add an "Installation" subsection under the "Extended Usage" heading documenting the curl one-liner, the `--yes` flag variant, and the uninstall one-liner
- [x] 8.2 Add a note that Windows support (`install.ps1`) is planned; direct Windows users to `pip install artifactr` in the meantime
