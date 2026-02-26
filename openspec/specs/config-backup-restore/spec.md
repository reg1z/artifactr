## Requirements

### Requirement: Backup archive format
A backup archive MUST be a valid zip file containing: a `manifest.yaml` at the root listing all included vaults; a `config_snapshot.yaml` at the root with configuration settings; and one directory per vault named after the vault's name, containing its `vault.yaml`, `skills/`, `commands/`, and `agents/` subdirectories.

#### Scenario: Archive is a valid zip
- **WHEN** a backup is created
- **THEN** the output file MUST be openable as a standard zip archive

#### Scenario: manifest.yaml present and valid
- **WHEN** the backup zip is opened
- **THEN** a `manifest.yaml` MUST be present at the root with `format_version`, `created_at`, and a `vaults` list (each entry having `name` and `dir` keys)

#### Scenario: config_snapshot.yaml present and valid
- **WHEN** the backup zip is opened
- **THEN** a `config_snapshot.yaml` MUST be present containing `format_version`, `created_at`, `default_vault_name`, `default_tool`, `nav_mode`, and `tools`

#### Scenario: Vault dirs use vault names not paths
- **WHEN** vault directories are listed inside the backup zip
- **THEN** they MUST be named using the vault's registered name, not its absolute filesystem path

### Requirement: `art config backup` command
The CLI MUST register a `backup` subcommand under the `config` namespace. Running it MUST produce a zip archive containing all registered vaults' contents and a config snapshot.

#### Scenario: Default output filename
- **WHEN** `art config backup` is run without an output argument
- **THEN** the archive MUST be written to `artifactr-backup-YYYYMMDD.zip` in the current working directory, where YYYYMMDD is the current date

#### Scenario: Custom output path
- **WHEN** `art config backup my-backup.zip` is run
- **THEN** the archive MUST be written to `my-backup.zip`

#### Scenario: Errors if output already exists
- **WHEN** `art config backup` is run and the output file already exists
- **THEN** the command MUST exit with an error without modifying the existing file

#### Scenario: All vaults included
- **WHEN** `art config backup` is run with multiple vaults registered
- **THEN** every registered vault's contents MUST appear in the archive

#### Scenario: Config snapshot includes default_vault_name
- **WHEN** a default vault is set and `art config backup` is run
- **THEN** `config_snapshot.yaml` MUST include `default_vault_name` equal to that vault's registered name (not its absolute path)

#### Scenario: Config snapshot when no default vault
- **WHEN** no default vault is set and `art config backup` is run
- **THEN** `config_snapshot.yaml` MUST include `default_vault_name: null`

#### Scenario: No registered vaults
- **WHEN** `art config backup` is run with no vaults registered
- **THEN** the command MUST produce an archive with only `manifest.yaml` and `config_snapshot.yaml` and exit successfully

### Requirement: `art config restore` command
The CLI MUST register a `restore` subcommand under the `config` namespace. Running it MUST extract vault contents from the archive, register all extracted vaults, and apply stored configuration settings.

#### Scenario: Requires archive argument
- **WHEN** `art config restore` is run without a positional argument
- **THEN** the command MUST exit with an error indicating a backup archive is required

#### Scenario: Errors on invalid archive
- **WHEN** `art config restore` is given a path that does not exist or is not a valid zip
- **THEN** the command MUST exit with an error

#### Scenario: Errors on missing manifest
- **WHEN** the archive does not contain `manifest.yaml`
- **THEN** the command MUST exit with an error

### Requirement: Restore vault extraction location
All vaults from a backup archive MUST be extracted to `~/.config/artifactr/vaults/<vault-name>/`. Absolute paths from the original machine MUST NOT be restored.

#### Scenario: Vaults extracted to config vaults dir
- **WHEN** `art config restore backup.zip` is run
- **THEN** each vault MUST be extracted to `~/.config/artifactr/vaults/<vault-name>/`

#### Scenario: Extracted vaults registered
- **WHEN** vaults are extracted
- **THEN** each vault MUST be registered in `config.yaml` with its original name and the new extracted path

### Requirement: Restore name conflict resolution
When a vault name from the archive conflicts with an already-registered vault name, the restore operation MUST assign a non-conflicting name by appending `-1`, `-2`, etc. until unique.

#### Scenario: Name conflict causes rename
- **WHEN** a vault named `personal` is already registered and the backup contains a vault also named `personal`
- **THEN** the restored vault MUST be registered as `personal-1` (or the next available suffix)

#### Scenario: No conflict — original name used
- **WHEN** a vault name from the backup does not conflict with any existing registration
- **THEN** the vault MUST be registered using its original name

#### Scenario: Rename reported to user
- **WHEN** a name conflict rename occurs
- **THEN** the output MUST inform the user of the original name and the assigned name

### Requirement: Restore applies config settings
After extracting vaults, `art config restore` MUST apply `default_tool`, `nav_mode`, and `tools` from `config_snapshot.yaml` to the global config.

#### Scenario: default_tool restored
- **WHEN** `config_snapshot.yaml` contains `default_tool: claude-code`
- **THEN** after restore, the configured default tool MUST be `claude-code`

#### Scenario: nav_mode restored
- **WHEN** `config_snapshot.yaml` contains a non-null `nav_mode`
- **THEN** after restore, `nav_mode` in config MUST match the snapshot value

#### Scenario: Custom tools restored
- **WHEN** `config_snapshot.yaml` contains a non-empty `tools` dict
- **THEN** after restore, the `tools` dict in config MUST match the snapshot

### Requirement: Restore sets default vault
After extraction, `art config restore` MUST set `default_vault` to the extracted path of the vault whose name matches `default_vault_name` from `config_snapshot.yaml`.

#### Scenario: Default vault set after restore
- **WHEN** `config_snapshot.yaml` has `default_vault_name: personal` and the `personal` vault is successfully extracted
- **THEN** the restored `default_vault` MUST point to the newly extracted vault's path

#### Scenario: Default vault set after rename
- **WHEN** the vault named in `default_vault_name` was renamed due to a conflict (e.g., to `personal-1`)
- **THEN** `default_vault` MUST point to the renamed vault's path

#### Scenario: Missing default vault name warns
- **WHEN** `default_vault_name` in the snapshot does not match any vault in the archive
- **THEN** the command MUST emit a warning and leave `default_vault` unchanged
