## 1. New spec

- [x] 1.1 Create `openspec/specs/install-script-windows/spec.md` from change delta

## 2. install.ps1 — script skeleton

- [x] 2.1 Create `install.ps1` at repo root with `param([switch]$Yes, [switch]$Uninstall)` and `$ErrorActionPreference = 'Stop'`
- [x] 2.2 Set `$DataDir = "$env:LOCALAPPDATA\artifactr"` and declare all global variables
- [x] 2.3 Implement `Confirm-Action` helper (prints message + `[y/N]`, respects `$Yes`, uses `Read-Host`)
- [x] 2.4 Implement `Read-StateFile` helper (parses `key=value` from `$DataDir\.install-info`)
- [x] 2.5 Implement `Write-StateFile` helper (writes `method=` to `$DataDir\.install-info`)

## 3. install.ps1 — Python detection

- [x] 3.1 Implement `Find-Python` function: probe `py -3` → `python3` → `python` in order
- [x] 3.2 For each candidate, run `& $candidate -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"` to version-check
- [x] 3.3 Return the first passing candidate; if none pass, print error with download URL and exit non-zero

## 4. install.ps1 — install flows

- [x] 4.1 Implement pipx detection (`Get-Command pipx -ErrorAction SilentlyContinue`) and set `$InstallMethod`
- [x] 4.2 Implement pipx fresh install: `pipx install artifactr` + `Write-StateFile`
- [x] 4.3 Implement venv fresh install: `<python> -m venv $DataDir\.venv` + pip install artifactr
- [x] 4.4 Implement `art.cmd` shim creation at `$DataDir\bin\art.cmd` with `@"%~dp0\..\venv\Scripts\art.exe" %*`
- [x] 4.5 Implement User PATH addition: read registry, append `$DataDir\bin` if absent, write back via `[Environment]::SetEnvironmentVariable`
- [x] 4.6 Print install summary (method, venv location if applicable) before prompting

## 5. install.ps1 — upgrade flow

- [x] 5.1 Detect existing install via `Get-Command art -ErrorAction SilentlyContinue`
- [x] 5.2 Read state file; print warning and exit if no state file found (unmanaged install)
- [x] 5.3 Implement pipx upgrade: `pipx upgrade artifactr`; detect "already installed" output
- [x] 5.4 Implement venv upgrade: `& "$DataDir\.venv\Scripts\pip.exe" install --upgrade artifactr`; detect "already satisfied" output

## 6. install.ps1 — uninstall flow

- [x] 6.1 Detect if installed (`Get-Command art` or `$DataDir\.install-info` exists); exit cleanly if neither found
- [x] 6.2 Print uninstall summary (method, data directory) and confirm
- [x] 6.3 Implement pipx uninstall: `pipx uninstall artifactr` + `Remove-Item $DataDir -Recurse`
- [x] 6.4 Implement venv uninstall: `Remove-Item $DataDir -Recurse` (removes `.venv`, `bin`, state file)
- [x] 6.5 Remove `$DataDir\bin` from User PATH on uninstall if present (read → filter → write)

## 7. install.sh update

- [x] 7.1 Update Windows detection message in `install.sh` from "A PowerShell installer (install.ps1) is planned." to "Use install.ps1 instead."
- [x] 7.2 Update `openspec/specs/install-script/spec.md` Windows detection scenario to match

## 8. README update

- [x] 8.1 Add Windows one-liner under "Extended Usage": `powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/reg1z/artifactr/main/install.ps1 | iex"`
- [x] 8.2 Document direct invocation with `-Yes` and `-Uninstall` for users who download the script
