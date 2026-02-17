## ADDED Requirements

### Requirement: Windows symlink privilege detection
On Windows, the system MUST detect when symlink creation fails due to insufficient privileges.

#### Scenario: Symlink succeeds
- **WHEN** `Path.symlink_to()` succeeds on Windows
- **THEN** the artifact MUST be linked as a symlink (same behavior as Linux/macOS)
- **AND** the `.art-cache/imported` entry MUST use `:linked`

#### Scenario: Symlink fails with OSError
- **WHEN** `Path.symlink_to()` raises `OSError` on Windows
- **THEN** the system MUST prompt the user to approve falling back to hard links

### Requirement: Hard link fallback on Windows
When symlinks fail on Windows, the system MUST offer hard links as an alternative.

#### Scenario: User approves hard link fallback
- **WHEN** the user approves the hard link fallback prompt
- **THEN** `os.link()` MUST be used to create hard links for all files in the current operation
- **AND** the `.art-cache/imported` entry MUST use `:win_hardlinked`

#### Scenario: User declines hard link fallback
- **WHEN** the user declines the hard link fallback prompt
- **THEN** the import MUST fall back to copying (non-linked import)
- **AND** a message MUST suggest enabling Developer Mode for symlink support

#### Scenario: Hard link same-volume requirement
- **WHEN** hard link creation is attempted and source and destination are on different volumes
- **THEN** an error MUST be displayed explaining that hard links require both paths on the same volume
- **AND** the error MUST suggest enabling Developer Mode: "Settings → System → For Developers → Developer Mode → On"
- **AND** the error MUST suggest importing without `--link` as an alternative

### Requirement: Windows fallback applies to all link operations
The Windows hard link fallback MUST apply to all operations that create links.

#### Scenario: Import with --link on Windows
- **WHEN** `art proj import --link` is run on Windows and symlinks fail
- **THEN** the hard link fallback prompt MUST be shown

#### Scenario: Link command on Windows
- **WHEN** `art proj link helping-hand` is run on Windows and symlinks fail
- **THEN** the hard link fallback prompt MUST be shown

#### Scenario: Config import with --link on Windows
- **WHEN** `art conf import --link` is run on Windows and symlinks fail
- **THEN** the hard link fallback prompt MUST be shown

#### Scenario: Config link command on Windows
- **WHEN** `art conf link helping-hand` is run on Windows and symlinks fail
- **THEN** the hard link fallback prompt MUST be shown

### Requirement: Non-Windows platforms unaffected
The Windows fallback logic MUST NOT affect Linux or macOS behavior.

#### Scenario: Linux symlink behavior
- **WHEN** a link operation is performed on Linux
- **THEN** `Path.symlink_to()` MUST be used directly without fallback logic

#### Scenario: macOS symlink behavior
- **WHEN** a link operation is performed on macOS
- **THEN** `Path.symlink_to()` MUST be used directly without fallback logic
