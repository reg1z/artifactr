## ADDED Requirements

### Requirement: Config edit command
`art config edit` MUST open the global artifactr configuration file in the user's preferred editor.

#### Scenario: Open config in editor
- **WHEN** `art config edit` is run
- **THEN** the global config file at `<config_dir>/config.yaml` MUST be opened in the user's preferred editor using the same resolution as `art edit` (`$VISUAL` → `$EDITOR` → nano/nvim/vim/vi → notepad.exe on Windows)

#### Scenario: No editor found
- **WHEN** `art config edit` is run and no editor can be resolved
- **THEN** an error MUST be displayed indicating no editor was found and suggesting the user set `$EDITOR`

#### Scenario: Config file does not exist
- **WHEN** `art config edit` is run and the config file does not yet exist
- **THEN** the editor MUST still be opened with the path (allowing the user to create it), and the config directory MUST be created if it does not exist

#### Scenario: Using config alias
- **WHEN** `art conf edit` is run
- **THEN** it MUST behave identically to `art config edit`
