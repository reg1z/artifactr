## Context

`install.sh` handles upgrades via `pip install --upgrade`, but its "already up to date" detection greps for `"already satisfied"` — which matches dependency lines even when artifactr itself was upgraded, producing false "already up to date" messages. Beyond that, users have no in-tool path for updating: they must remember the original one-liner install command.

The new `art update` command (alias: `upgrade`) lives entirely in the Python package. It detects the install method, checks PyPI for the latest version, confirms with the user, runs the appropriate upgrade command, and verifies the result.

## Goals / Non-Goals

**Goals:**
- `art update` works for all install methods (script-managed pipx, script-managed venv, manual venv, system pip)
- Accurate "up to date" detection using version comparison, not output parsing
- PyPI check before running the upgrade (show available version first)
- PATH repair for venv installs where `~/.local/bin` is missing from `$PATH`
- Graceful refusal for editable (dev) installs
- All stdlib — no new dependencies

**Non-Goals:**
- Fixing `install.sh` directly (out of scope for this change)
- Updating Windows `install.ps1` upgrade behavior
- Handling `pipx` PATH injection (pipx manages its own PATH)
- Rollback on failed upgrade

## Decisions

### D1: New `updater.py` module

`cli.py` is already ~3270 lines. All update logic (install detection, PyPI query, version comparison, upgrade execution, PATH repair) lives in `src/artifactr/updater.py`. `cli.py` gets only `handle_update()` and the parser registration.

_Alternative_: inline everything in `cli.py` — rejected, too much growth in an already large file.

### D2: Install method detection via `sys.executable` path

Detection order:

1. **Editable install** — check `importlib.metadata` for `direct_url.json` with `"editable": true`. If found, refuse with a helpful message.
2. **pipx** — `"pipx/venvs/artifactr"` is a substring of `str(Path(sys.executable))`. Works on Linux and macOS regardless of whether the state file exists.
3. **Managed venv** — `Path(sys.executable).is_relative_to(get_data_dir() / ".venv")`. Covers the script-installed venv.
4. **Unknown** — anything else (system pip, manual venv elsewhere). Still attempt upgrade via `sys.executable -m pip install --upgrade --no-cache-dir artifactr`, but warn the user that the install method could not be confirmed.

State file (`.install-info`) is read only as a fallback when `sys.executable` detection is ambiguous, and for retrieving the `rc_file` path for PATH repair.

_Alternative_: state file only — rejected because it doesn't work for manual installs.

### D3: PyPI JSON API for version check

`https://pypi.org/pypi/artifactr/json` → `info.version`. Uses `urllib.request.urlopen` (stdlib). Timeout of 5 seconds. On any error (network unavailable, timeout, HTTP error), the command prints a warning and aborts rather than blindly upgrading.

_Alternative_: `pip index versions artifactr` subprocess — rejected, adds subprocess overhead and the output format is not stable across pip versions.

### D4: Use `sys.executable -m pip` for venv and unknown upgrades

`subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "--no-cache-dir", "artifactr"])` always targets the correct environment regardless of which pip binary is on PATH.

For pipx: `subprocess.run(["pipx", "upgrade", "--pip-args=--no-cache-dir", "artifactr"])`.

### D5: Version verification via `pip show` after upgrade

`importlib.metadata.version()` returns the version cached at process startup — it won't reflect a just-completed upgrade. After running the upgrade subprocess, verification uses `subprocess.run([sys.executable, "-m", "pip", "show", "artifactr"])` and parses the `Version:` line to confirm the new version.

### D6: PATH repair scope

PATH repair is offered only for venv installs (managed or unknown) on Linux and macOS. It checks:
1. Is `~/.local/bin` in `os.environ["PATH"]`?
2. If not, is the export line already in the rc file?
3. If not, offer to append `export PATH="$HOME/.local/bin:$PATH"` to the rc file.

The rc file path is read from the state file (`rc_file=` key) when available; otherwise detected fresh via `detect_shell()` → `get_shell_rc_file()` from `utils.py`.

Windows has no `~/.local/bin` concept — PATH repair is skipped entirely on Windows.

### D7: `get_data_dir()` in `utils.py`

Mirrors `get_config_dir()` but diverges on Linux:

| Platform | Data dir |
|---|---|
| Linux | `~/.local/share/artifactr/` |
| macOS | `~/Library/Application Support/artifactr/` |
| Windows | `%APPDATA%/artifactr/` |

On macOS and Windows, `get_data_dir()` returns the same path as `get_config_dir()`, preserving backward compatibility with the existing `.install-info` location.

## Risks / Trade-offs

- **PyPI unavailable** → command exits with a clear error rather than a silent no-op. The user can still run `install.sh` manually.
- **Version metadata stale in-process** → mitigated by using `pip show` post-upgrade rather than `importlib.metadata`.
- **Editable install detection fails** → `direct_url.json` is standard PEP 610 metadata; present in all modern pip installs. Older pip (<21.3) may not write it — in that case the command falls through to "unknown" and attempts upgrade anyway (harmless for non-editable installs, but dev users could accidentally upgrade themselves from PyPI). Acceptable risk given `pip 21.3` is from 2021.
- **pipx path varies across installs** → checking for `"pipx/venvs/artifactr"` as a substring is broad enough to catch `~/.local/share/pipx/`, `~/.local/pipx/`, and `/opt/pipx/` layouts.

## Open Questions

_(none — all decisions made in exploration)_
