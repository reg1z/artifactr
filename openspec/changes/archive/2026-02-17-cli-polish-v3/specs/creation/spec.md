## ADDED Requirements

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
