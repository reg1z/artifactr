## Why

artifactr has no automated installer for Windows. The existing `install.sh` detects Windows and exits with a "planned" message, leaving Windows users to manually `pip install artifactr` without guidance on PATH, isolated environments, or uninstall. A native PowerShell installer closes this gap and brings Windows to parity with the Linux/macOS experience.

## What Changes

- Add `install.ps1` — a standalone PowerShell installer that mirrors `install.sh` behavior using Windows idioms
- Update README under "Extended Usage" to document the Windows one-liner, direct invocation with flags, and uninstall command

## Capabilities

### New Capabilities

- `install-script-windows`: PowerShell installer for Windows covering Python detection, tiered install (pipx preferred, managed venv fallback), User PATH management via registry, upgrade, uninstall, state file, and confirmation model

### Modified Capabilities

- `install-script`: Update the Windows detection note — `install.sh` currently says "planned"; update to say `install.ps1` is available with a reference

## Impact

- New file: `install.ps1` at repo root (fully external to `src/artifactr/`)
- Modified file: `README.md` (under "Extended Usage" heading only)
- Modified file: `openspec/specs/install-script/spec.md` (Windows detection scenario updated)
- No changes to Python package, `src/artifactr/`, or existing tests
