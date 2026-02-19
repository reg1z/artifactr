## MODIFIED Requirements

### Requirement: Windows detection and graceful bail
The installer SHALL detect when it is running on Windows (via `uname` returning a MINGW/CYGWIN/MSYS prefix or absence of `uname`) and exit with a message directing the user to `install.ps1`.

#### Scenario: Running on Windows via Git Bash or similar
- **WHEN** `uname -s` returns a string starting with `MINGW`, `CYGWIN`, or `MSYS`
- **THEN** the installer prints "Windows detected. Use install.ps1 instead. See the README for instructions." and exits non-zero
