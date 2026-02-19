## Context

`install.sh` provides a polished install experience for Linux and macOS but exits immediately on Windows with a "planned" message. Windows users must manually `pip install artifactr` with no guidance on isolated environments, PATH setup, or uninstall. `install.ps1` is a standalone PowerShell script at the repo root that mirrors `install.sh`'s structure and guarantees using idiomatic Windows tooling.

The script is fully external to `src/artifactr/` — no Python package changes required.

## Goals / Non-Goals

**Goals:**
- Mirror every functional flow of `install.sh`: fresh install, upgrade, uninstall, confirmation model, state file
- pipx preferred, managed venv fallback with proper PATH wiring
- No admin rights required (User scope throughout)
- One-liner that works regardless of the user's execution policy setting

**Non-Goals:**
- WSL (Windows Subsystem for Linux) — users in WSL should use `install.sh`
- Scoop / Chocolatey / winget package manager integration
- Machine-scope (admin) installs
- Signing the script (out of scope for now)

## Decisions

### D1: Python detection order — `py -3` → `python3` → `python`

**Decision**: Try each in order; version-check every candidate found.

**Rationale**: `py` (the Python Launcher) is the canonical Windows Python entry point installed alongside the official python.org MSI. `python3` rarely resolves natively on Windows but is worth trying for environments where it does (e.g., some conda setups). `python` is the fallback but may resolve to Python 2, the Windows Store stub, or nothing — the version check catches bad matches. The first candidate that passes 3.10+ wins.

**Alternative considered**: Require `py` only. Rejected because it excludes environments that have Python 3 on PATH as `python` without the launcher (e.g., conda, custom installs).

---

### D2: venv fallback PATH strategy — dedicated bin dir + `.cmd` shim

**Decision**: For venv installs, create `$DataDir\bin\art.cmd` and add `$DataDir\bin` to User PATH.

**Rationale**: Mirrors the pipx pattern — pipx exposes shims at `%USERPROFILE%\.local\bin`, a dedicated directory cleanly separated from the venv internals. Adding `.venv\Scripts` directly to PATH (the simpler approach) would expose pip, python, activate, and other venv internals alongside `art`, polluting the user's PATH. A dedicated bin dir with a single `.cmd` wrapper is clean, easy to uninstall (one PATH entry to remove), and consistent with the unix symlink-to-`~/.local/bin` approach.

`art.cmd` content:
```bat
@"%~dp0\..\venv\Scripts\art.exe" %*
```

**Alternative considered**: Add `$DataDir\.venv\Scripts` directly to PATH. Rejected for PATH pollution reasons above.

---

### D3: One-liner invocation — `powershell -ExecutionPolicy ByPass -c "irm ... | iex"`

**Decision**: Document the one-liner with `-ExecutionPolicy ByPass` wrapper.

**Rationale**: `irm | iex` executes content from memory, which bypasses execution policy by default. However, wrapping with `-ExecutionPolicy ByPass` is the industry standard (uv, rustup, etc.) and makes the one-liner bulletproof on machines with `Restricted` or `AllSigned` policy without requiring users to change their system settings. Parameters (`-Yes`, `-Uninstall`) are not needed in the one-liner — users who need them can download and invoke directly.

---

### D4: PATH management via registry (User scope)

**Decision**: Use `[Environment]::SetEnvironmentVariable("PATH", ..., "User")` to add/remove the bin dir.

**Rationale**: Windows has no shell rc file equivalent. Modifying User PATH in the registry is the correct, permanent, non-admin way to make a directory available in new shells. The state file stores `method=` only (no `rc_file` key needed — there is no rc file on Windows). On uninstall, the script reads the current User PATH, filters out `$DataDir\bin`, and writes back.

---

### D5: State file — same `key=value` format as `install.sh`

**Decision**: `$DataDir\.install-info` with identical `key=value` format. Only `method=pipx` or `method=venv`; no `rc_file` key.

**Rationale**: Keeps state file format consistent and human-readable. Simplifies any future cross-platform tooling that might read state files.

## Risks / Trade-offs

**PATH registry edit may fail in locked-down environments** → Mitigation: wrap with `try/catch` and print a clear error telling the user to manually add `$DataDir\bin` to their PATH.

**`python` command on Windows may resolve to the Microsoft Store stub** → Mitigation: the version check (`sys.version_info >= (3, 10)`) will fail on the Store stub since running it prompts to install and exits non-zero; the script moves on to the next candidate.

**pipx not in PATH after pipx installs itself** → Mitigation: note in success message that a new shell may be needed if pipx was just installed. Not an install.ps1 problem per se — same caveat exists on unix.

**`irm` may be blocked by corporate proxies** → Mitigation: document direct download + invocation as an alternative in README.
