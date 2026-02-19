param(
    [switch]$Yes,
    [switch]$Uninstall
)
$ErrorActionPreference = 'Stop'

# ── Globals ────────────────────────────────────────────────────────────────────
$DataDir       = "$env:LOCALAPPDATA\artifactr"
$InstallMethod = ""

# ── Helpers ────────────────────────────────────────────────────────────────────
function Confirm-Action {
    param([string]$Message)
    if ($Yes) {
        Write-Host "$Message [y/N] y (auto)"
        return $true
    }
    $response = Read-Host "$Message [y/N]"
    return ($response -eq 'y' -or $response -eq 'Y')
}

function Read-StateFile {
    $stateFile = "$DataDir\.install-info"
    if (-not (Test-Path $stateFile)) { return }
    foreach ($line in (Get-Content $stateFile)) {
        if ($line -match '^method=(.+)$') {
            $script:InstallMethod = $Matches[1]
        }
    }
}

function Write-StateFile {
    New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
    "method=$script:InstallMethod" | Set-Content "$DataDir\.install-info" -Encoding UTF8
}

# ── Python detection ───────────────────────────────────────────────────────────
function Find-Python {
    $candidates = @(
        @{ cmd = 'py';      args = @('-3') },
        @{ cmd = 'python3'; args = @()     },
        @{ cmd = 'python';  args = @()     }
    )
    foreach ($c in $candidates) {
        if (-not (Get-Command $c.cmd -ErrorAction SilentlyContinue)) { continue }
        try {
            & $c.cmd @($c.args) -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>$null
            if ($LASTEXITCODE -eq 0) {
                return $c
            }
        }
        catch {}
    }
    Write-Host "Python 3.10+ is required but was not found."
    Write-Host "Install Python 3.10+ from https://www.python.org/downloads/"
    exit 1
}

# ── Uninstall flow ─────────────────────────────────────────────────────────────
if ($Uninstall) {

    # 6.1 Detect if installed
    $artFound    = Get-Command art -ErrorAction SilentlyContinue
    $stateExists = Test-Path "$DataDir\.install-info"
    if (-not $artFound -and -not $stateExists) {
        Write-Host "artifactr does not appear to be installed."
        exit 0
    }

    Read-StateFile

    # 6.2 Print uninstall summary and confirm
    Write-Host ""
    Write-Host "Uninstall artifactr"
    Write-Host "  Method:         $(if ($InstallMethod) { $InstallMethod } else { 'unknown' })"
    Write-Host "  Data directory: $DataDir"
    Write-Host ""
    if (-not (Confirm-Action "Proceed with uninstall?")) {
        Write-Host "Uninstall cancelled."
        exit 0
    }

    # 6.3 pipx uninstall
    if ($InstallMethod -eq 'pipx') {
        pipx uninstall artifactr
        if (Test-Path $DataDir) {
            Remove-Item $DataDir -Recurse -Force
        }
    }
    # 6.4 venv uninstall
    elseif ($InstallMethod -eq 'venv') {
        if (Test-Path $DataDir) {
            Remove-Item $DataDir -Recurse -Force
        }
        # 6.5 Remove $DataDir\bin from User PATH
        $binDir      = "$DataDir\bin"
        $currentPath = [Environment]::GetEnvironmentVariable('PATH', 'User')
        $parts       = $currentPath -split ';' | Where-Object { $_ -ne '' -and $_ -ne $binDir }
        [Environment]::SetEnvironmentVariable('PATH', ($parts -join ';'), 'User')
    }
    else {
        Write-Host "Unknown install method in state file. Attempting cleanup..."
        if (Test-Path $DataDir) {
            Remove-Item $DataDir -Recurse -Force
        }
        $binDir      = "$DataDir\bin"
        $currentPath = [Environment]::GetEnvironmentVariable('PATH', 'User')
        $parts       = $currentPath -split ';' | Where-Object { $_ -ne '' -and $_ -ne $binDir }
        [Environment]::SetEnvironmentVariable('PATH', ($parts -join ';'), 'User')
    }

    Write-Host ""
    Write-Host "artifactr uninstalled successfully."
    exit 0
}

# ── Find Python (not needed for uninstall) ────────────────────────────────────
$Py = Find-Python

# ── Upgrade flow ───────────────────────────────────────────────────────────────
if (Get-Command art -ErrorAction SilentlyContinue) {

    # 5.2 Read state file; warn if unmanaged install
    Read-StateFile
    if (-not $InstallMethod) {
        Write-Host "Warning: artifactr is installed but was not managed by this script."
        Write-Host "Please uninstall it manually before re-running this installer."
        exit 1
    }

    Write-Host ""
    Write-Host "Upgrading artifactr (method: $InstallMethod)..."

    # 5.3 pipx upgrade
    if ($InstallMethod -eq 'pipx') {
        $output = pipx upgrade artifactr 2>&1 | Out-String
        if ($output -match 'already installed') {
            Write-Host "artifactr is already up to date."
        }
        else {
            Write-Host $output.Trim()
            Write-Host "artifactr upgraded successfully."
        }
    }
    # 5.4 venv upgrade
    elseif ($InstallMethod -eq 'venv') {
        $output = & "$DataDir\.venv\Scripts\pip.exe" install --upgrade artifactr 2>&1 | Out-String
        if ($output -match 'already satisfied') {
            Write-Host "artifactr is already up to date."
        }
        else {
            Write-Host $output.Trim()
            Write-Host "artifactr upgraded successfully."
        }
    }

    exit 0
}

# ── Fresh install ──────────────────────────────────────────────────────────────

# 4.1 Detect install method
if (Get-Command pipx -ErrorAction SilentlyContinue) {
    $InstallMethod = 'pipx'
}
else {
    $InstallMethod = 'venv'
}

# 4.6 Print install summary
Write-Host ""
Write-Host "Install artifactr"
Write-Host "  Method: $InstallMethod"
if ($InstallMethod -eq 'venv') {
    Write-Host "  Venv location: $DataDir\.venv"
    Write-Host "  Shim:          $DataDir\bin\art.cmd"
}
Write-Host ""
if (-not (Confirm-Action "Proceed with installation?")) {
    Write-Host "Installation cancelled."
    exit 0
}

# 4.2 pipx fresh install
if ($InstallMethod -eq 'pipx') {
    pipx install artifactr
    Write-StateFile
}
# 4.3 venv fresh install
elseif ($InstallMethod -eq 'venv') {
    New-Item -ItemType Directory -Force -Path $DataDir | Out-Null

    # Create venv
    & $Py.cmd @($Py.args) -m venv "$DataDir\.venv"

    # Install artifactr into venv
    & "$DataDir\.venv\Scripts\pip.exe" install artifactr

    # 4.4 Create art.cmd shim
    New-Item -ItemType Directory -Force -Path "$DataDir\bin" | Out-Null
    '@"%~dp0..\.venv\Scripts\art.exe" %*' | Set-Content "$DataDir\bin\art.cmd" -Encoding ASCII

    Write-StateFile

    # 4.5 Add $DataDir\bin to User PATH if absent
    $binDir      = "$DataDir\bin"
    $currentPath = [Environment]::GetEnvironmentVariable('PATH', 'User')
    $parts       = $currentPath -split ';' | Where-Object { $_ -ne '' }
    if ($parts -notcontains $binDir) {
        try {
            $newPath = ($parts + $binDir) -join ';'
            [Environment]::SetEnvironmentVariable('PATH', $newPath, 'User')
            Write-Host "Added '$binDir' to User PATH."
        }
        catch {
            Write-Host "Warning: Could not update User PATH automatically."
            Write-Host "Please add '$binDir' to your PATH manually."
        }
    }
}

# Print success
Write-Host ""
$version = 'unknown'
try {
    if ($InstallMethod -eq 'venv') {
        $pipShow     = & "$DataDir\.venv\Scripts\pip.exe" show artifactr 2>$null
        $versionLine = $pipShow | Where-Object { $_ -match '^Version:' }
        if ($versionLine) { $version = ($versionLine -split '\s+')[1] }
    }
    else {
        $pipxOut = pipx list --short 2>$null
        $artLine = $pipxOut | Where-Object { $_ -match '^artifactr\s' }
        if ($artLine) { $version = ($artLine -split '\s+')[1] }
    }
}
catch {}
Write-Host "artifactr $version installed successfully."
if ($InstallMethod -eq 'venv') {
    Write-Host "Open a new shell for PATH changes to take effect."
}
