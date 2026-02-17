## Requirements

### Requirement: Create artifact in vault
`art create <type> <name>` MUST support multi-vault `-V` to create the artifact in multiple vaults.

#### Scenario: Create in single vault
- **WHEN** `art create skill foo -V favorites` is run
- **THEN** the skill MUST be created in `favorites` vault only

#### Scenario: Create in multiple vaults
- **WHEN** `art create skill foo -V vault1,vault2` is run
- **THEN** the skill MUST be created in both `vault1` and `vault2` vaults

#### Scenario: Create without vault flag
- **WHEN** `art create skill foo` is run without `-V`
- **THEN** the skill MUST be created in the default vault (existing behavior)

#### Scenario: Create with --here flag
- **WHEN** `art create skill foo --here` is run with `-V vault1,vault2`
- **THEN** `-V` MUST be ignored since `--here` creates locally (existing behavior)

### Requirement: Agent display name override
The `art create agent` command MUST support `--name`/`-n` to set the YAML frontmatter `name` field independently of the agent's filename.

#### Scenario: Agent with display name
- **WHEN** `art create agent my-helper -d "desc" --name "Helper Bot"` is run
- **THEN** the agent file MUST be created as `my-helper.md` with `name: Helper Bot` in its YAML frontmatter

#### Scenario: Agent without display name
- **WHEN** `art create agent my-helper -d "desc"` is run without `--name`
- **THEN** the agent file MUST be created as `my-helper.md` without a `name` field in frontmatter (existing behavior)

#### Scenario: Display name in vault
- **WHEN** `art create agent my-helper --name "Helper Bot" --vault favorites` is run
- **THEN** the agent MUST be created at `<favorites-vault>/agents/my-helper.md` with `name: Helper Bot` in frontmatter

#### Scenario: Display name with --here
- **WHEN** `art create agent my-helper --name "Helper Bot" --here` is run
- **THEN** the agent MUST be created in the project's tool config directory with `name: Helper Bot` in frontmatter
