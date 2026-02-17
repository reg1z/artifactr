## Purpose

Import cache v2 format extends the cache file to support vault path tracking and link state suffixes for artifact entries.

## Requirements

### Requirement: Vault paths section in import cache
The `.art-cache/imported` file MUST support a `[vault_paths]` section that maps vault labels to filesystem paths.

#### Scenario: Vault path recorded on import
- **WHEN** an artifact is imported from a vault
- **THEN** the vault's label and filesystem path MUST be recorded in the `[vault_paths]` section

#### Scenario: Vault path format
- **WHEN** a vault path entry is written
- **THEN** it MUST use the format `<vault_label>=<filesystem_path>`

#### Scenario: Vault path lookup
- **WHEN** the `link` command needs to create a symlink to a vault
- **THEN** it MUST resolve the vault path from the `[vault_paths]` section using the vault label from the imported entry

#### Scenario: Duplicate vault labels
- **WHEN** multiple imports use the same vault label
- **THEN** the vault path MUST be updated to the latest path (last write wins)

### Requirement: Link state suffix in import cache
Each entry in the `[imported]` section MUST have a suffix indicating its link state.

#### Scenario: Linked artifact suffix
- **WHEN** an artifact is imported with `--link` or converted via `link` command
- **THEN** its entry MUST end with `:linked`

#### Scenario: Copied artifact suffix
- **WHEN** an artifact is imported without `--link` or converted via `unlink` command
- **THEN** its entry MUST end with `:copied`

#### Scenario: Windows hard-linked artifact suffix
- **WHEN** an artifact is linked via the Windows hard link fallback
- **THEN** its entry MUST end with `:win_hardlinked`

#### Scenario: Link state update on toggle
- **WHEN** `art proj link` or `art proj unlink` changes an artifact's state
- **THEN** the suffix in `.art-cache/imported` MUST be updated to reflect the new state

### Requirement: Backward compatibility with legacy format
The cache parser MUST handle files written in the pre-v2 format.

#### Scenario: Entry without suffix
- **WHEN** a cache entry has no `:` suffix (e.g., `favorites.claude-code.helping-hand`)
- **THEN** it MUST be treated as `:copied`

#### Scenario: File without section headers
- **WHEN** a cache file has no `[vault_paths]` or `[imported]` headers
- **THEN** all lines MUST be treated as `[imported]` entries

#### Scenario: Mixed format
- **WHEN** a cache file contains both legacy entries (no suffix) and v2 entries (with suffix)
- **THEN** both MUST be parsed correctly

### Requirement: Global import cache v2 format
The global cache at `~/.config/artifactr/.art-cache-global/imported` MUST use the same v2 format.

#### Scenario: Global cache vault paths
- **WHEN** a global import is performed
- **THEN** the vault path MUST be recorded in the `[vault_paths]` section of the global cache

#### Scenario: Global cache link state
- **WHEN** a global artifact is linked or unlinked
- **THEN** the suffix in the global cache MUST be updated
