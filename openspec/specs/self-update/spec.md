## Purpose

Defines the behavior of `art update` (alias: `art upgrade`) — the in-tool command for upgrading artifactr to the latest version published on PyPI. The command detects the active install method, checks for available updates, confirms with the user, executes the upgrade, and verifies the result. It replaces the need to remember and re-run the original one-liner install command.

---

## Requirements

### Requirement: Platform data directory resolution
`get_data_dir()` in `utils.py` SHALL return the platform-appropriate directory where the install state file and managed venv are stored.

#### Scenario: Linux host
- **WHEN** `platform.system()` returns `"Linux"`
- **THEN** `get_data_dir()` returns `~/.local/share/artifactr/`

#### Scenario: macOS host
- **WHEN** `platform.system()` returns `"Darwin"`
- **THEN** `get_data_dir()` returns `~/Library/Application Support/artifactr/`

#### Scenario: Windows host
- **WHEN** `platform.system()` returns `"Windows"`
- **THEN** `get_data_dir()` returns `%APPDATA%/artifactr/` (falling back to `~/AppData/Roaming/artifactr/` if `APPDATA` is unset)

---

### Requirement: Editable install detection and refusal
The command SHALL detect editable (development) installs and refuse to upgrade, directing the user to manage the install manually.

#### Scenario: Editable install detected via PEP 610 metadata
- **WHEN** `importlib.metadata.distribution("artifactr")` contains a `direct_url.json` with `dir_info.editable == true`
- **THEN** the command prints a message indicating a dev install was detected and that the user should manage upgrades manually (e.g., via `git pull` or `pip install -e .`), then exits with code 1

---

### Requirement: Install method detection via sys.executable
The command SHALL determine the active install method by inspecting `sys.executable` before any other action.

#### Scenario: pipx-managed install
- **WHEN** `"pipx/venvs/artifactr"` is a substring of `str(Path(sys.executable))`
- **THEN** install method is resolved as `pipx`

#### Scenario: Script-managed venv install
- **WHEN** `Path(sys.executable)` is relative to `get_data_dir() / ".venv"`
- **THEN** install method is resolved as `venv`

#### Scenario: Unknown install (system pip, manual venv elsewhere)
- **WHEN** neither the pipx nor venv conditions match, and the install is not editable
- **THEN** install method is resolved as `unknown`, the command prints a warning that the install method could not be confirmed, and proceeds to attempt the upgrade via `sys.executable -m pip`

---

### Requirement: PyPI version check before upgrade
The command SHALL query the PyPI JSON API for the latest published version of `artifactr` before running any upgrade and SHALL report the available version to the user.

#### Scenario: Latest version available and newer than installed
- **WHEN** PyPI returns a version string newer than the currently installed version
- **THEN** the command prints the current and available versions (e.g., `artifactr 0.3.1 → 0.3.2 available`) before prompting

#### Scenario: Already on the latest version
- **WHEN** PyPI returns a version string equal to the currently installed version
- **THEN** the command prints "artifactr X.Y.Z is already up to date." and exits with code 0 without running any upgrade command

#### Scenario: PyPI query fails (network error, timeout, HTTP error)
- **WHEN** the HTTP request to `https://pypi.org/pypi/artifactr/json` fails for any reason (timeout ≤ 5 s, DNS error, non-200 response)
- **THEN** the command prints a warning explaining the failure and exits with code 1 without attempting an upgrade

---

### Requirement: Upgrade confirmation prompt
The command SHALL prompt the user for confirmation before running the upgrade, unless `--yes` / `-y` is set.

#### Scenario: User confirms upgrade
- **WHEN** a newer version is available and the user answers `y` or `Y` at the prompt
- **THEN** the upgrade proceeds

#### Scenario: User declines upgrade
- **WHEN** a newer version is available and the user answers anything other than `y` or `Y`
- **THEN** the command prints "Upgrade cancelled." and exits with code 0

#### Scenario: --yes flag suppresses prompt
- **WHEN** `--yes` or `-y` is passed and a newer version is available
- **THEN** the upgrade proceeds without prompting

---

### Requirement: Upgrade execution
The command SHALL run the appropriate upgrade command based on the detected install method.

#### Scenario: pipx upgrade
- **WHEN** install method is `pipx`
- **THEN** the command runs `pipx upgrade --pip-args=--no-cache-dir artifactr`

#### Scenario: venv or unknown upgrade
- **WHEN** install method is `venv` or `unknown`
- **THEN** the command runs `sys.executable -m pip install --upgrade --no-cache-dir artifactr`

---

### Requirement: Post-upgrade version verification
After running the upgrade command, the command SHALL verify the newly installed version by querying `pip show artifactr` and SHALL report the result.

#### Scenario: Upgrade succeeded and version matches expected
- **WHEN** `pip show artifactr` reports the version string that PyPI indicated as latest
- **THEN** the command prints "artifactr upgraded to X.Y.Z." and exits with code 0

#### Scenario: Upgrade subprocess failed (non-zero exit)
- **WHEN** the upgrade subprocess exits with a non-zero code
- **THEN** the command prints the subprocess output and exits with code 1

---

### Requirement: PATH repair for venv installs on Linux and macOS
After a successful upgrade, if the install method is `venv` or `unknown`, the command SHALL check whether `~/.local/bin` is present in `$PATH` and offer to repair it if absent.

#### Scenario: ~/.local/bin already in PATH
- **WHEN** `~/.local/bin` is present in `os.environ["PATH"]`
- **THEN** the PATH check is silently skipped

#### Scenario: PATH export already in rc file
- **WHEN** `~/.local/bin` is not in `$PATH` but the rc file already contains a line referencing `/.local/bin`
- **THEN** the PATH check is silently skipped (idempotent)

#### Scenario: ~/.local/bin missing from PATH, user confirms repair
- **WHEN** `~/.local/bin` is not in `$PATH`, the rc file does not contain the export line, and the user answers `y` or `Y`
- **THEN** `export PATH="$HOME/.local/bin:$PATH"` is appended to the detected shell rc file

#### Scenario: ~/.local/bin missing from PATH, --yes flag set
- **WHEN** `~/.local/bin` is not in `$PATH`, the rc file does not contain the export line, and `--yes` was passed
- **THEN** `export PATH="$HOME/.local/bin:$PATH"` is appended without prompting

#### Scenario: Windows host
- **WHEN** `platform.system()` returns `"Windows"`
- **THEN** PATH repair is skipped entirely

#### Scenario: pipx install
- **WHEN** install method is `pipx`
- **THEN** PATH repair is skipped entirely (pipx manages its own PATH)

---

### Requirement: --check flag (dry-run version check)
The command SHALL support a `--check` flag that queries PyPI and reports the available version without running any upgrade.

#### Scenario: Update available, --check passed
- **WHEN** `--check` is passed and a newer version is available
- **THEN** the command prints the current and available versions and exits with code 0, without prompting or upgrading

#### Scenario: Already up to date, --check passed
- **WHEN** `--check` is passed and the installed version equals the latest on PyPI
- **THEN** the command prints "artifactr X.Y.Z is already up to date." and exits with code 0

---

### Requirement: Command registration and aliases
The command SHALL be registered in the CLI as `update` with alias `upgrade`.

#### Scenario: art update invocation
- **WHEN** the user runs `art update`
- **THEN** the update handler is invoked

#### Scenario: art upgrade invocation
- **WHEN** the user runs `art upgrade`
- **THEN** the update handler is invoked (alias)
