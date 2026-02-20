## Requirements

### Requirement: art create supports slash-prefix type/name syntax
The `art create` command MUST accept `type/name` as an alternative to the two-positional `type name` form, consistent with the slash syntax already supported by `art edit`, `art cat`, `art inspect`, `art export`, and `art ls`.

#### Scenario: Slash syntax for skill
- **WHEN** `art create skill/my-skill -d "description"` is run
- **THEN** it MUST behave identically to `art create skill my-skill -d "description"`

#### Scenario: Slash syntax for command
- **WHEN** `art create command/my-command -d "description"` is run
- **THEN** it MUST behave identically to `art create command my-command -d "description"`

#### Scenario: Slash syntax for agent
- **WHEN** `art create agent/my-agent -d "description"` is run
- **THEN** it MUST behave identically to `art create agent my-agent -d "description"`

#### Scenario: Slash syntax with type aliases
- **WHEN** `art create sk/my-skill -d "description"` is run (using a type alias)
- **THEN** it MUST behave identically to `art create skill my-skill -d "description"`

#### Scenario: Two-positional form still accepted
- **WHEN** `art create skill my-skill -d "description"` is run (existing syntax)
- **THEN** it MUST continue to work without any behavior change

#### Scenario: Invalid slash syntax — unknown type
- **WHEN** `art create foo/my-artifact -d "description"` is run with an unrecognized type prefix
- **THEN** argparse MUST error with its standard "unrecognized subcommand" message

#### Scenario: Slash syntax with all flags
- **WHEN** `art create sk/my-skill -d "desc" -V my-vault -D custom=value` is run
- **THEN** all flags MUST be passed through correctly as if the two-positional form were used

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
