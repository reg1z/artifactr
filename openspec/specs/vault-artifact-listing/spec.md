## ADDED Requirements

### Requirement: List vault contents
`art ls` MUST display artifacts in a vault, with multi-vault support.

#### Scenario: List single vault (default)
- **WHEN** `art ls` is run without `-V`
- **THEN** artifacts from the default vault MUST be listed with columns NAME, TYPE, TOOL

#### Scenario: List single vault by name
- **WHEN** `art ls -V favorites` is run
- **THEN** artifacts from `favorites` MUST be listed with columns NAME, TYPE, TOOL

#### Scenario: List multiple vaults
- **WHEN** `art ls -V vault1,vault2` is run
- **THEN** artifacts from both vaults MUST be listed with columns NAME, TYPE, TOOL, VAULT

#### Scenario: Vault column added for multi-vault
- **WHEN** multiple vaults are specified via `-V`
- **THEN** a VAULT column MUST be added to the output indicating which vault each artifact belongs to

#### Scenario: Vault column absent for single vault
- **WHEN** a single vault is listed (default or single `-V`)
- **THEN** the VAULT column MUST NOT be shown

#### Scenario: Multi-vault with type filter
- **WHEN** `art ls -V vault1,vault2 -S` is run
- **THEN** only skills from both vaults MUST be listed

#### Scenario: List with skills filter
- **WHEN** `art list -S` is run
- **THEN** only skill artifacts MUST be shown

#### Scenario: List with commands filter
- **WHEN** `art list -C` is run
- **THEN** only command artifacts MUST be shown

#### Scenario: List with agents filter
- **WHEN** `art list -A` is run
- **THEN** only agent artifacts MUST be shown

#### Scenario: List with named filter
- **WHEN** `art list -S foo,bar` is run
- **THEN** only skills named `foo` and `bar` MUST be shown

#### Scenario: List with multiple type filters
- **WHEN** `art list -S -C` is run
- **THEN** skills and commands MUST be shown; agents MUST be excluded

#### Scenario: Empty vault
- **WHEN** `art list` is run and the vault contains no artifacts
- **THEN** a message MUST indicate the vault is empty

#### Scenario: No default vault
- **WHEN** `art list` is run and no default vault is configured
- **THEN** an error MUST be displayed instructing the user to set up a vault

### Requirement: Vault artifact list description extraction
Each listed artifact MUST display its description from YAML frontmatter, truncated to 50 characters if necessary.

#### Scenario: Skill description
- **WHEN** a skill's `SKILL.md` has a `description` field in its YAML frontmatter
- **THEN** that description MUST be displayed (truncated with `...` if over 50 chars)

#### Scenario: Missing description
- **WHEN** an artifact has no `description` in its frontmatter
- **THEN** `-` MUST be displayed as the description

### Requirement: art ls accepts an artifact name to list files within a directory-based artifact
`art ls` MUST accept an optional positional artifact-name argument. When provided, it MUST list the files within that artifact's directory rather than listing vault artifacts.

#### Scenario: List files within a skill
- **WHEN** `art ls my-skill` is run and `my-skill` is a skill in the default vault
- **THEN** all files within the skill's directory MUST be listed
- **AND** `SKILL.md` MUST be listed first and labeled as `(main)`
- **AND** files in subdirectories MUST be shown with their relative path

#### Scenario: List files with type prefix
- **WHEN** `art ls skill/my-skill` or `art ls sk/my-skill` is run
- **THEN** files within the named skill MUST be listed

#### Scenario: List files with explicit vault
- **WHEN** `art ls my-skill -V work` is run
- **THEN** files within `my-skill` in the `work` vault MUST be listed

#### Scenario: File-based artifact errors
- **WHEN** `art ls my-command` is run and `my-command` is a command (file-based)
- **THEN** an error MUST be printed to stderr stating that `my-command` is a file-based artifact and does not support file listing
- **AND** the command MUST exit with code 1

#### Scenario: Artifact name not found
- **WHEN** `art ls nonexistent` is run and no artifact by that name is found in the default vault
- **THEN** an error MUST be printed to stderr and the command MUST exit with code 1

#### Scenario: Skill with only SKILL.md
- **WHEN** `art ls my-skill` is run and the skill contains only `SKILL.md`
- **THEN** only `SKILL.md` MUST be listed (labeled as `(main)`)

#### Scenario: No artifact name — existing behavior preserved
- **WHEN** `art ls` is run with no positional argument
- **THEN** the existing vault artifact listing behavior MUST apply (list all artifacts in the default vault)
