## 1. Utils — Data Directory

- [x] 1.1 Add `get_data_dir()` to `src/artifactr/utils.py` — returns `~/.local/share/artifactr/` on Linux, `~/Library/Application Support/artifactr/` on macOS, `%APPDATA%/artifactr/` on Windows (mirrors `get_config_dir()` but diverges on Linux)

## 2. Core Updater Module

- [x] 2.1 Create `src/artifactr/updater.py` with `detect_install_method()` — inspects `sys.executable` for editable flag (PEP 610 `direct_url.json`), pipx path substring, managed venv path, and falls back to `"unknown"`
- [x] 2.2 Add `get_current_version()` to `updater.py` — uses `importlib.metadata.version("artifactr")`
- [x] 2.3 Add `get_latest_pypi_version()` to `updater.py` — queries `https://pypi.org/pypi/artifactr/json` via `urllib.request`, 5-second timeout, raises on any error
- [x] 2.4 Add `run_upgrade()` to `updater.py` — dispatches to `pipx upgrade` or `sys.executable -m pip install --upgrade --no-cache-dir artifactr` based on install method; returns subprocess result
- [x] 2.5 Add `get_installed_version_from_pip()` to `updater.py` — runs `sys.executable -m pip show artifactr` and parses the `Version:` line for post-upgrade verification
- [x] 2.6 Add `check_and_repair_path()` to `updater.py` — checks `~/.local/bin` in `$PATH`, reads rc file path from state file or detects via `detect_shell()`/`get_shell_rc_file()`, offers to append the export line; skips on Windows and for pipx installs

## 3. CLI Integration

- [x] 3.1 Add `handle_update(args)` to `src/artifactr/cli.py` — orchestrates the full flow: detect method → check editable → get current version → query PyPI → compare → confirm (unless `--yes`) → upgrade → verify → PATH repair
- [x] 3.2 Register `update` parser in `cli.py` `_main()` with alias `upgrade`, flags `--yes`/`-y` and `--check`, using `make_help()`

## 4. Tests

- [x] 4.1 Write tests for `get_data_dir()` covering Linux, macOS, and Windows platform cases
- [x] 4.2 Write tests for `detect_install_method()` covering editable, pipx, managed venv, and unknown cases (mock `sys.executable` and `importlib.metadata`)
- [x] 4.3 Write tests for `get_latest_pypi_version()` covering success, HTTP error, and timeout cases (mock `urllib.request.urlopen`)
- [x] 4.4 Write tests for `handle_update` CLI integration: already up to date, upgrade available + confirm, upgrade available + decline, `--check` flag, editable install refusal
