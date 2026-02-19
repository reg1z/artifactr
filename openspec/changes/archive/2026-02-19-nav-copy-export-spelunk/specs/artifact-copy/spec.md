## ADDED Requirements

### Requirement: art copy source resolution
The `art copy` command MUST resolve the source artifact(s) from positional arguments using vault-prefix, type-prefix, and name-or-glob syntax.

#### Scenario: Bare name — resolves from default vault
- **WHEN** `art copy my-skill vault-2/` is run with a bare name (no prefixes)
- **THEN** the source MUST be resolved against the selected default vault
- **AND** if exactly one artifact with that name exists across all types, it MUST be used
- **AND** if multiple artifacts of different types share that name, an error MUST be printed requiring a type prefix, and the command MUST exit with code 1

#### Scenario: Type-prefix — disambiguates by type
- **WHEN** a source is provided in `<type>/<name>` format (e.g., `command/explore`, `agt/my-agent`, `s/my-skill`)
- **THEN** only artifacts of the resolved type MUST be searched
- **AND** all type aliases MUST be recognized as valid type prefixes (`skill`, `skills`, `s`, `sk`, `command`, `commands`, `c`, `cmd`, `com`, `agent`, `agents`, `a`, `agt`)

#### Scenario: Vault-prefix — resolves from named vault
- **WHEN** a source is provided in `<vault>/<name>` format (e.g., `vault-1/my-skill`)
- **THEN** the named vault MUST be used as the source vault for resolution
- **AND** if the first path component is both a registered vault name and a type alias, the vault MUST take precedence

#### Scenario: Fully-qualified source
- **WHEN** a source is provided in `<vault>/<type>/<name>` format (e.g., `vault-1/command/explore`)
- **THEN** vault, type, and name MUST all be resolved from the respective components

#### Scenario: Frontmatter name fallback
- **WHEN** no artifact directory or file with the given name exists in the resolved search scope
- **THEN** YAML frontmatter `name:` fields MUST be scanned as a fallback (same resolution rules as `art edit`)
- **AND** if still no match is found, an error MUST be printed to stderr and the command MUST exit with code 1

### Requirement: art copy destination resolution
The `art copy` command MUST resolve the destination from the last positional argument.

#### Scenario: Trailing slash — copy into vault
- **WHEN** the last positional argument ends with `/` (e.g., `vault-2/`)
- **THEN** the argument (minus the trailing slash) MUST be treated as the destination vault name
- **AND** the artifact MUST be copied into the corresponding type subdirectory of that vault (preserving artifact type)

#### Scenario: No trailing slash and last arg is a registered vault name
- **WHEN** the last positional argument has no trailing slash but matches a registered vault name
- **THEN** it MUST be treated as a destination vault (equivalent to `<vault>/` with trailing slash)

#### Scenario: No trailing slash and last arg is not a registered vault name
- **WHEN** the last positional argument has no trailing slash and does not match a registered vault name
- **THEN** it MUST be treated as the new artifact name (duplicate/rename within the source vault)

#### Scenario: Vault/name destination — cross-vault with explicit name
- **WHEN** the destination is in `<vault>/<name>` format without trailing slash
- **THEN** the artifact MUST be copied to the named vault with the specified name

### Requirement: art copy same-vault duplicate
The `art copy` command MUST support duplicating an artifact within the same vault.

#### Scenario: Same-vault rename/duplicate
- **WHEN** `art copy my-skill my-skill-v2` is run and `my-skill-v2` is not a registered vault name
- **THEN** `my-skill` MUST be copied to a new artifact named `my-skill-v2` in the same vault
- **AND** the new artifact MUST be placed in the same type subdirectory as the source

### Requirement: art copy type coercion
When copying across vaults, the artifact type MUST travel with the artifact.

#### Scenario: Skill copied to another vault lands in skills/
- **WHEN** `art copy my-skill vault-2/` is run and `my-skill` is a skill
- **THEN** the copy MUST be placed in `vault-2/skills/my-skill/`

#### Scenario: Command copied to another vault lands in commands/
- **WHEN** `art copy my-cmd vault-2/` is run and `my-cmd` is a command
- **THEN** the copy MUST be placed in `vault-2/commands/my-cmd.md`

### Requirement: art copy glob pattern matching
The `art copy` command MUST support glob patterns in source names.

#### Scenario: Wildcard copies all artifacts
- **WHEN** `art copy * vault-2/` is run
- **THEN** all artifacts in the selected default vault MUST be copied to `vault-2`

#### Scenario: Type-scoped wildcard
- **WHEN** `art copy skills/* vault-2/` is run
- **THEN** only skill artifacts from the default vault MUST be copied to `vault-2/skills/`

#### Scenario: Pattern glob
- **WHEN** `art copy agents/*-runner vault-6/` is run
- **THEN** only agent artifacts whose name or frontmatter `name:` field matches `*-runner` MUST be copied

#### Scenario: Wildcard to non-container destination is an error
- **WHEN** a glob source resolves to multiple artifacts and the destination has no trailing slash and is not a registered vault name
- **THEN** an error MUST be printed explaining that multi-artifact sources require a container destination, and the command MUST exit with code 1

### Requirement: art copy aliases
The `art copy` command MUST be accessible via the alias `art cp`.

#### Scenario: art cp is equivalent to art copy
- **WHEN** `art cp` is run with any valid arguments
- **THEN** behavior MUST be identical to `art copy` with the same arguments
