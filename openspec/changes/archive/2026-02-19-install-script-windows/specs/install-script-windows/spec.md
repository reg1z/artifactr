## Purpose

Defines the behavior of the `install.ps1` PowerShell installer script for artifactr on Windows. The script handles Python detection, environment detection, tiered installation (pipx preferred, managed venv fallback), User PATH management via registry, upgrade, and uninstall. It is fully external to the Python package — no changes to `src/artifactr/`.

---

## Requirements

### Requirement: Python 3.10+ detection
The installer SHALL probe for a Python executable in order: `py -3`, then `python3`, then `python`. For each candidate found, it MUST verify `sys.version_info >= (3, 10)`. The first candidate that passes the version check SHALL be used for all subsequent Python operations. If no candidate passes, the script MUST print a human-readable error explaining the requirement, provide the URL `https://www.python.org/downloads/`, and exit with a non-zero code.

#### Scenario: py launcher present and Python 3.10+
- **WHEN** `py -3` is available and reports `sys.version_info >= (3, 10)`
- **THEN** `py -3` is selected as the Python executable and the installer proceeds

#### Scenario: py launcher absent, python3 present and 3.10+
- **WHEN** `py -3` is not found but `python3` is available and passes the version check
- **THEN** `python3` is selected as the Python executable and the installer proceeds

#### Scenario: py and python3 absent, python present and 3.10+
- **WHEN** neither `py -3` nor `python3` are found but `python` is available and passes the version check
- **THEN** `python` is selected as the Python executable and the installer proceeds

#### Scenario: Python candidate found but too old
- **WHEN** a candidate executable is present but `sys.version_info < (3, 10)`
- **THEN** that candidate is skipped and the next candidate is tried

#### Scenario: No Python 3.10+ candidate found
- **WHEN** none of `py -3`, `python3`, or `python` pass the version check
- **THEN** the installer prints the detected situation, states "Python 3.10+ required", provides `https://www.python.org/downloads/`, and exits non-zero

---

### Requirement: Data directory
The installer SHALL use `$env:LOCALAPPDATA\artifactr` as the data directory for venv, state file, and bin shim storage.

#### Scenario: LOCALAPPDATA is set
- **WHEN** `$env:LOCALAPPDATA` is defined (standard on all modern Windows)
- **THEN** `$DataDir` resolves to `$env:LOCALAPPDATA\artifactr` (e.g., `C:\Users\username\AppData\Local\artifactr`)

---

### Requirement: Tiered install strategy (pipx preferred, venv fallback)
When `art` is not already installed, the installer SHALL attempt installation via `pipx` if it is available, and fall back to a managed Python venv otherwise.

#### Scenario: pipx is available
- **WHEN** `Get-Command pipx -ErrorAction SilentlyContinue` succeeds
- **THEN** the installer runs `pipx install artifactr` and records `method=pipx` in the state file

#### Scenario: pipx is not available, Python 3.10+ is present
- **WHEN** `pipx` is not found and a Python 3.10+ candidate was identified
- **THEN** the installer creates `$DataDir\.venv` via `<python> -m venv`, installs artifactr with `$DataDir\.venv\Scripts\pip.exe install artifactr`, creates the `$DataDir\bin` directory, writes the `art.cmd` shim, adds `$DataDir\bin` to User PATH, and records `method=venv` in the state file

---

### Requirement: venv bin shim
For venv installs, the installer SHALL create a `$DataDir\bin\art.cmd` wrapper that delegates to the venv's `art.exe`.

#### Scenario: art.cmd is created
- **WHEN** venv install completes
- **THEN** `$DataDir\bin\art.cmd` exists and contains `@"%~dp0\..\venv\Scripts\art.exe" %*`

---

### Requirement: User PATH management (venv installs only)
After a venv install, the installer SHALL add `$DataDir\bin` to the User PATH in the Windows registry. If `$DataDir\bin` is already present in User PATH, this step SHALL be silently skipped. pipx installs MUST NOT trigger PATH modification (pipx manages its own PATH via `ensurepath`).

#### Scenario: $DataDir\bin not in User PATH
- **WHEN** `$DataDir\bin` is not present in the User PATH registry value
- **THEN** the installer appends `$DataDir\bin` to User PATH using `[Environment]::SetEnvironmentVariable("PATH", ..., "User")`

#### Scenario: $DataDir\bin already in User PATH
- **WHEN** `$DataDir\bin` is already present in User PATH
- **THEN** the installer skips PATH modification silently

#### Scenario: pipx install
- **WHEN** installation method is `pipx`
- **THEN** the installer does NOT modify User PATH

---

### Requirement: Install state file
The installer SHALL write a plain `key=value` state file at `$DataDir\.install-info` immediately after a successful install. The file MUST contain a `method` key with value `pipx` or `venv`. No `rc_file` key is written (Windows PATH is managed via registry, not a shell rc file).

#### Scenario: pipx install state file
- **WHEN** install method is pipx
- **THEN** `.install-info` contains `method=pipx`

#### Scenario: venv install state file
- **WHEN** install method is venv
- **THEN** `.install-info` contains `method=venv`

---

### Requirement: Upgrade existing install
When `art` is already installed (detected via `Get-Command art -ErrorAction SilentlyContinue`) and `-Uninstall` is NOT set, the installer SHALL upgrade the existing installation.

#### Scenario: Upgrade via pipx
- **WHEN** state file records `method=pipx`
- **THEN** the installer runs `pipx upgrade artifactr`

#### Scenario: Upgrade via venv
- **WHEN** state file records `method=venv`
- **THEN** the installer runs `& "$DataDir\.venv\Scripts\pip.exe" install --upgrade artifactr`

#### Scenario: Already on latest version
- **WHEN** the upgrade command output indicates no upgrade was performed (pip: "already satisfied"; pipx: "already installed")
- **THEN** the installer prints "artifactr is already up to date." and exits 0

#### Scenario: art found but no state file
- **WHEN** `Get-Command art` succeeds but no `.install-info` file exists at `$DataDir`
- **THEN** the installer prints a warning that the existing install was not managed by this script and exits non-zero with guidance to uninstall manually before re-running

---

### Requirement: Uninstall via -Uninstall flag
The installer SHALL support an `-Uninstall` switch. When passed, it reads the state file and removes the installation, then removes `$DataDir\bin` from User PATH if it is present.

#### Scenario: Uninstall pipx install
- **WHEN** `-Uninstall` is passed and state file records `method=pipx`
- **THEN** the installer runs `pipx uninstall artifactr` and removes `$DataDir`

#### Scenario: Uninstall venv install
- **WHEN** `-Uninstall` is passed and state file records `method=venv`
- **THEN** the installer removes `$DataDir` (including `.venv` and `bin`) and removes `$DataDir\bin` from User PATH

#### Scenario: Remove $DataDir\bin from User PATH on uninstall
- **WHEN** `-Uninstall` is passed and `$DataDir\bin` is present in User PATH
- **THEN** the installer reads the current User PATH, filters out the `$DataDir\bin` entry, and writes the result back via `[Environment]::SetEnvironmentVariable("PATH", ..., "User")`

#### Scenario: Uninstall when not installed
- **WHEN** `-Uninstall` is passed but neither `Get-Command art` succeeds nor `$DataDir\.install-info` exists
- **THEN** the installer prints "artifactr does not appear to be installed." and exits 0

---

### Requirement: Confirmation model
Every action that modifies the system (installing, adding to PATH, uninstalling) SHALL be preceded by a human-readable description of what will happen, followed by a `[y/N]` prompt via `Read-Host`. If the user answers anything other than `y` or `Y`, the action MUST be skipped. The `-Yes` switch MUST suppress all prompts and proceed as if the user answered yes to everything.

#### Scenario: Interactive install, user confirms
- **WHEN** `-Yes` is not set and the user types `y` at the install prompt
- **THEN** installation proceeds

#### Scenario: Interactive install, user declines
- **WHEN** `-Yes` is not set and the user types anything other than `y`/`Y` at the install prompt
- **THEN** the installer exits without making changes

#### Scenario: Non-interactive with -Yes
- **WHEN** `-Yes` is set
- **THEN** all prompts are skipped and all actions proceed automatically

---

### Requirement: No admin rights required
All installer operations SHALL use User scope. No UAC elevation, no machine-scope registry writes, no writes to system directories.

#### Scenario: All paths are user-writable
- **WHEN** the installer runs as a standard (non-elevated) user
- **THEN** all operations succeed: `$env:LOCALAPPDATA\artifactr` is created, User PATH is modified, pipx venvs are created in user directories

---

### Requirement: README documentation
The README SHALL be updated under the "Extended Usage" heading to document the Windows one-liner, direct invocation with `-Yes` / `-Uninstall`, and the PowerShell execution policy wrapper. No content above the "Extended Usage" heading SHALL be changed.

#### Scenario: Windows install command documented
- **WHEN** a user reads the README under "Extended Usage"
- **THEN** they can find `powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/reg1z/artifactr/main/install.ps1 | iex"` as the Windows install command

#### Scenario: Windows uninstall documented
- **WHEN** a user reads the README under "Extended Usage"
- **THEN** they can find instructions for downloading and running `.\install.ps1 -Uninstall`
