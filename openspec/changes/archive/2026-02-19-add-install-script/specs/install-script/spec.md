## ADDED Requirements

### Requirement: Python 3.10+ detection
The installer SHALL check that `python3` is available and reports `sys.version_info >= (3, 10)` before attempting any install action. If the check fails, the script MUST print a human-readable error explaining the requirement and provide the URL `https://www.python.org/downloads/` as a reference, then exit with a non-zero code.

#### Scenario: Python 3.10+ present
- **WHEN** `python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"` exits 0
- **THEN** the installer proceeds to the install/upgrade/uninstall flow

#### Scenario: Python not found
- **WHEN** `python3` is not in PATH
- **THEN** the installer prints "python3 not found. Install Python 3.10+ from https://www.python.org/downloads/" and exits non-zero

#### Scenario: Python found but too old
- **WHEN** `python3` is present but `sys.version_info < (3, 10)`
- **THEN** the installer prints the detected version, states "Python 3.10+ required", and exits non-zero

---

### Requirement: Windows detection and graceful bail
The installer SHALL detect when it is running on Windows (via `uname` returning a MINGW/CYGWIN/MSYS prefix or absence of `uname`) and exit with a message directing the user to a forthcoming `install.ps1` script.

#### Scenario: Running on Windows via Git Bash or similar
- **WHEN** `uname -s` returns a string starting with `MINGW`, `CYGWIN`, or `MSYS`
- **THEN** the installer prints "Windows detected. A PowerShell installer (install.ps1) is planned. See the README for manual install instructions." and exits non-zero

---

### Requirement: Tiered install strategy (pipx preferred, venv fallback)
When `art` is not already installed, the installer SHALL attempt installation via `pipx` if it is available, and fall back to a managed Python venv otherwise.

#### Scenario: pipx is available
- **WHEN** `command -v pipx` succeeds
- **THEN** the installer runs `pipx install artifactr` and records `method=pipx` in the state file

#### Scenario: pipx is not available, Python 3.10+ is present
- **WHEN** `command -v pipx` fails and Python 3.10+ is confirmed
- **THEN** the installer creates `$DATA_DIR/.venv` via `python3 -m venv`, installs `artifactr` with `.venv/bin/pip install artifactr`, creates `~/.local/bin/` if absent, symlinks `~/.local/bin/art` → `$DATA_DIR/.venv/bin/art`, and records `method=venv` in the state file

---

### Requirement: Platform-appropriate data directory
The installer SHALL resolve `DATA_DIR` based on the host operating system before any install action.

#### Scenario: Linux host
- **WHEN** `uname -s` returns `Linux`
- **THEN** `DATA_DIR` is set to `$HOME/.local/share/artifactr`

#### Scenario: macOS host
- **WHEN** `uname -s` returns `Darwin`
- **THEN** `DATA_DIR` is set to `$HOME/Library/Application Support/artifactr`

---

### Requirement: PATH check and rc file update (venv installs only)
After a venv install, the installer SHALL check whether `~/.local/bin` is present in `$PATH`. If absent, it MUST show the user which rc file will be modified and the exact line that will be appended, prompt for confirmation (unless `--yes` is set), and append `export PATH="$HOME/.local/bin:$PATH"` to that rc file. If `~/.local/bin` is already on `$PATH`, this step is silently skipped.

#### Scenario: ~/.local/bin not in PATH, user confirms
- **WHEN** `~/.local/bin` is not in `$PATH` and the user answers yes to the prompt
- **THEN** `export PATH="$HOME/.local/bin:$PATH"` is appended to the detected rc file, and the rc file path is recorded in the state file as `rc_file=<path>`

#### Scenario: ~/.local/bin not in PATH, --yes flag set
- **WHEN** `~/.local/bin` is not in `$PATH` and `--yes` was passed
- **THEN** the line is appended without prompting, and the rc file path is recorded

#### Scenario: ~/.local/bin already in PATH
- **WHEN** `~/.local/bin` is already present in `$PATH`
- **THEN** the rc file is not modified and no prompt is shown

#### Scenario: PATH export already in rc file
- **WHEN** the rc file already contains a line referencing `/.local/bin`
- **THEN** the export line is not appended again (idempotent)

#### Scenario: pipx install (PATH not managed by installer)
- **WHEN** installation method is `pipx`
- **THEN** the installer does NOT attempt PATH modification (pipx handles this itself)

---

### Requirement: Install state file
The installer SHALL write a plain `key=value` state file at `$DATA_DIR/.install-info` immediately after a successful install. The file MUST contain at minimum a `method` key (`pipx` or `venv`). If the rc file was modified, a `rc_file` key MUST also be written with the absolute path to that file.

#### Scenario: venv install with PATH modification
- **WHEN** install method is venv and rc file was updated
- **THEN** `.install-info` contains both `method=venv` and `rc_file=/absolute/path`

#### Scenario: pipx install
- **WHEN** install method is pipx
- **THEN** `.install-info` contains `method=pipx` (and no `rc_file` key, or empty)

---

### Requirement: Upgrade existing install
When `art` is already installed (detected via `command -v art`) and the `--uninstall` flag is NOT set, the installer SHALL upgrade the existing installation rather than reinstalling from scratch.

#### Scenario: Upgrade via pipx
- **WHEN** state file records `method=pipx`
- **THEN** the installer runs `pipx upgrade artifactr`

#### Scenario: Upgrade via venv
- **WHEN** state file records `method=venv`
- **THEN** the installer runs `$DATA_DIR/.venv/bin/pip install --upgrade artifactr`

#### Scenario: Already on latest version
- **WHEN** the upgrade command output indicates no upgrade was performed (pip: "already satisfied"; pipx: "already installed")
- **THEN** the installer prints "artifactr is already up to date." and exits 0

#### Scenario: art found but no state file
- **WHEN** `command -v art` succeeds but no `.install-info` file exists at `$DATA_DIR`
- **THEN** the installer prints a warning that the existing install was not managed by this script and exits non-zero with guidance to uninstall manually before re-running

---

### Requirement: Uninstall via --uninstall flag
The installer SHALL support a `--uninstall` flag. When passed, it reads the state file and removes the installation, then optionally removes the PATH export from the rc file.

#### Scenario: Uninstall pipx install
- **WHEN** `--uninstall` is passed and state file records `method=pipx`
- **THEN** the installer runs `pipx uninstall artifactr` and removes `$DATA_DIR` (state file only; pipx manages its own venv)

#### Scenario: Uninstall venv install
- **WHEN** `--uninstall` is passed and state file records `method=venv`
- **THEN** the installer removes `$DATA_DIR` (including `.venv`) and `~/.local/bin/art`

#### Scenario: Remove PATH export on uninstall
- **WHEN** `--uninstall` is passed and state file records a `rc_file`
- **THEN** the installer shows the PATH export line and prompts the user to remove it (or removes it automatically with `--yes`), then removes the line from the rc file

#### Scenario: Uninstall when not installed
- **WHEN** `--uninstall` is passed but neither `command -v art` succeeds nor `$DATA_DIR/.install-info` exists
- **THEN** the installer prints "artifactr does not appear to be installed." and exits 0

---

### Requirement: Confirmation model
Every action that modifies the system (installing, adding to PATH, uninstalling, modifying rc file) SHALL be preceded by a human-readable description of what will happen, followed by a `[y/N]` prompt. If the user answers anything other than `y` or `Y`, the action MUST be skipped. The `--yes` / `-y` flag MUST suppress all prompts and proceed as if the user answered yes to everything.

#### Scenario: Interactive install, user confirms
- **WHEN** `--yes` is not set and the user types `y` at the install prompt
- **THEN** installation proceeds

#### Scenario: Interactive install, user declines
- **WHEN** `--yes` is not set and the user types `n` (or presses Enter) at the install prompt
- **THEN** the installer exits without making changes

#### Scenario: Non-interactive with --yes
- **WHEN** `--yes` is set
- **THEN** all prompts are skipped and all actions proceed automatically

---

### Requirement: README documentation
The README SHALL be updated under the "Extended Usage" heading to document the one-liner install command, the `--yes` flag usage, and the uninstall command. No content above the "Extended Usage" heading SHALL be changed.

#### Scenario: Install command documented
- **WHEN** a user reads the README under "Extended Usage"
- **THEN** they can find `curl -fsSL https://raw.githubusercontent.com/reg1z/artifactr/main/install.sh | bash` as the install command

#### Scenario: Uninstall command documented
- **WHEN** a user reads the README under "Extended Usage"
- **THEN** they can find the uninstall one-liner with `bash -s -- --uninstall`

#### Scenario: Windows note documented
- **WHEN** a user reads the README under "Extended Usage"
- **THEN** they can find a note that Windows support (`install.ps1`) is planned and to use `pip install artifactr` in the meantime
