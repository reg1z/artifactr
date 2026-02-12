## MODIFIED Requirements

### Requirement: Dependencies
Artifactr MUST only require Python 3.

#### Scenario: Standard library usage
- **WHEN** Artifactr is built
- **THEN** it MUST use these standard library modules:
  - `argparse` for CLI parsing
  - `pathlib` for cross-platform path handling
  - `shutil` for file operations
  - `os` and `platform` for system detection

#### Scenario: External dependencies
- **WHEN** YAML parsing is needed
- **THEN** the `PyYAML` library MUST be used

#### Scenario: TUI dependency
- **WHEN** the interactive TUI mode is used
- **THEN** the `textual` library (>=0.50) MUST be available as a project dependency
