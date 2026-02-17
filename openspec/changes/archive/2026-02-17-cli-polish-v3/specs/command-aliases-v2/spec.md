## ADDED Requirements

### Requirement: Extended artifact type aliases for edit
The `art edit` command's artifact type argument MUST accept additional aliases beyond the existing single-letter shortcuts.

#### Scenario: Edit command with cmd alias
- **WHEN** `art edit cmd my-command` is run
- **THEN** the command MUST behave identically to `art edit command my-command`

#### Scenario: Edit command with com alias
- **WHEN** `art edit com my-command` is run
- **THEN** the command MUST behave identically to `art edit command my-command`

#### Scenario: Edit skill with sk alias
- **WHEN** `art edit sk my-skill` is run
- **THEN** the command MUST behave identically to `art edit skill my-skill`

#### Scenario: Edit agent with agt alias
- **WHEN** `art edit agt my-agent` is run
- **THEN** the command MUST behave identically to `art edit agent my-agent`

#### Scenario: Edit agent with ag alias
- **WHEN** `art edit ag my-agent` is run
- **THEN** the command MUST behave identically to `art edit agent my-agent`

### Requirement: Extended artifact type aliases for create
The `art create` command's subcommand names MUST accept additional aliases beyond the existing single-letter shortcuts.

#### Scenario: Create command with cmd alias
- **WHEN** `art create cmd my-command -d "desc"` is run
- **THEN** the command MUST behave identically to `art create command my-command -d "desc"`

#### Scenario: Create command with com alias
- **WHEN** `art create com my-command -d "desc"` is run
- **THEN** the command MUST behave identically to `art create command my-command -d "desc"`

#### Scenario: Create skill with sk alias
- **WHEN** `art create sk my-skill -d "desc"` is run
- **THEN** the command MUST behave identically to `art create skill my-skill -d "desc"`

#### Scenario: Create agent with agt alias
- **WHEN** `art create agt my-agent -d "desc"` is run
- **THEN** the command MUST behave identically to `art create agent my-agent -d "desc"`

#### Scenario: Create agent with ag alias
- **WHEN** `art create ag my-agent -d "desc"` is run
- **THEN** the command MUST behave identically to `art create agent my-agent -d "desc"`
