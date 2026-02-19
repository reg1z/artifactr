## ADDED Requirements

### Requirement: art vault export produces a zip archive
The `art vault export` command MUST export one or more vaults to a single `.zip` archive containing artifact directories and a `manifest.yaml`.

#### Scenario: Single vault export
- **WHEN** `art vault export my-vault /path/to/bundle.zip` is run
- **THEN** a `.zip` archive MUST be created at `/path/to/bundle.zip`
- **AND** the archive MUST contain the vault's `skills/`, `commands/`, `agents/` directories and `vault.yaml` under a directory named after the vault
- **AND** a `manifest.yaml` MUST be included at the archive root

#### Scenario: Multiple vaults via comma-separated list
- **WHEN** `art vault export vault-1,vault-2 /path/to/bundle.zip` is run
- **THEN** both vaults MUST be included in the archive as separate top-level directories
- **AND** a single `manifest.yaml` at the archive root MUST list both vaults

#### Scenario: Glob pattern vault selection
- **WHEN** `art vault export "claude-*" /path/to/bundle.zip` is run (quoted to prevent shell expansion)
- **THEN** all registered vaults whose name matches the glob pattern MUST be included in the archive

#### Scenario: --all flag exports all registered vaults
- **WHEN** `art vault export --all /path/to/bundle.zip` is run (alias: `-a`)
- **THEN** ALL registered vaults MUST be included in the archive

#### Scenario: No vault specified — error
- **WHEN** `art vault export /path/to/bundle.zip` is run with no vault name, glob, or `--all`
- **THEN** an error MUST be printed to stderr and the command MUST exit with code 1

#### Scenario: Output path exists — error
- **WHEN** the specified output `.zip` path already exists
- **THEN** an error MUST be printed to stderr and the command MUST exit with code 1 without writing

### Requirement: art vault export archive structure
The zip archive produced by `art vault export` MUST follow a defined internal structure.

#### Scenario: Per-vault directory naming
- **WHEN** a vault is exported
- **THEN** its contents MUST be placed under a directory named after the vault's registered name (or directory basename if unnamed)

#### Scenario: manifest.yaml format
- **WHEN** the archive is created
- **THEN** a `manifest.yaml` MUST be included at the archive root with the following structure:
  ```yaml
  vaults:
    - name: <vault-name>
      dir: <directory-name-in-archive>
  ```
- **AND** one entry per exported vault MUST be present

#### Scenario: Only artifact contents included
- **WHEN** a vault is exported
- **THEN** ONLY `skills/`, `commands/`, `agents/`, and `vault.yaml` MUST be included from each vault
- **AND** other files in the vault root (`.git/`, additional user files, etc.) MUST be excluded

### Requirement: art vault import extracts and registers vaults
The `art vault import` command MUST extract vaults from a `.zip` archive and register them.

#### Scenario: Default destination — fallback location with confirmation
- **WHEN** `art vault import bundle.zip` is run with no destination argument
- **THEN** the command MUST print the fallback destination (`<config_dir>/vaults/`) and list which vaults will be extracted there
- **AND** the user MUST be asked to confirm before extraction proceeds

#### Scenario: --yes skips confirmation
- **WHEN** `art vault import bundle.zip --yes` is run (alias: `-y`)
- **THEN** all confirmation prompts MUST be skipped and extraction MUST proceed immediately
- **AND** the destination and extracted vault locations MUST still be printed to stdout

#### Scenario: Explicit destination overrides fallback
- **WHEN** `art vault import bundle.zip /path/to/dest/` is run with a destination argument
- **THEN** vaults MUST be extracted into `/path/to/dest/<vault-dir>/` (flat layout)
- **AND** the confirmation prompt MUST still be shown (suppressible with `-y`)

#### Scenario: Flat layout extraction
- **WHEN** vaults are extracted
- **THEN** each vault MUST be placed as a direct subdirectory of the destination: `<dest>/<vault-dir>/`
- **AND** the internal archive directory structure (one dir per vault) MUST be preserved as-is

#### Scenario: Auto-registration from manifest
- **WHEN** extraction completes
- **THEN** each vault listed in `manifest.yaml` MUST be registered in `config.yaml` using the vault name from the manifest
- **AND** registration MUST use the extracted path as the vault path

#### Scenario: Vault name or path conflict on import — error
- **WHEN** a vault name or path from the manifest already exists in `config.yaml`
- **THEN** an error MUST be printed for that vault and it MUST NOT be re-registered
- **AND** other non-conflicting vaults in the archive MUST still be registered

#### Scenario: Invalid or non-zip input — error
- **WHEN** the input file is not a valid `.zip` archive or does not contain a `manifest.yaml`
- **THEN** an error MUST be printed to stderr and the command MUST exit with code 1
