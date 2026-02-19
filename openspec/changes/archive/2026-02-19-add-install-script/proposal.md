## Why

Installing artifactr currently requires users to know and invoke `pipx` or `pip` manually — no one-shot path exists for someone discovering the tool for the first time. A `curl | bash` installer (with a companion uninstall flag) gives users a reliable, guided entry point that handles environment setup, PATH configuration, and upgrades without requiring prior knowledge of Python tooling.

## What Changes

- New `install.sh` bash script (Linux + macOS) hosted at the repo root
- Script detects Python 3.10+, falls back gracefully with actionable instructions if absent
- Tiered install strategy: use `pipx` if available, otherwise create a managed venv at a platform-appropriate data directory and symlink `art` into `~/.local/bin/`
- PATH check — detects if `~/.local/bin` is on `$PATH` and offers to append the export to the user's shell rc file
- Upgrade path — if `art` is already installed, upgrades rather than reinstalls; reports "already up to date" cleanly if no upgrade is available
- Uninstall path — `--uninstall` flag removes the venv (or invokes `pipx uninstall`), the `~/.local/bin/art` symlink, and offers to remove the PATH export from the rc file
- `-y` / `--yes` flag skips all confirmation prompts for non-interactive / scripted use
- Windows is explicitly out of scope for this change; a `install.ps1` PowerShell equivalent is left as a documented future addition
- README updated under the "Extended Usage" heading to document the one-liner and uninstall command

## Capabilities

### New Capabilities

- `install-script`: A self-contained bash installer script that handles dependency checking, environment setup, PATH configuration, upgrade, and uninstall for artifactr on Linux and macOS

### Modified Capabilities

<!-- No existing spec-level behavior changes -->

## Impact

- New file: `install.sh` at repo root
- `README.md`: additions under the "Extended Usage" heading only
- No changes to `src/artifactr/` — installer is pure shell, fully external to the Python package
- No new Python dependencies
- Hosted via GitHub raw URL: `https://raw.githubusercontent.com/reg1z/artifactr/main/install.sh`
