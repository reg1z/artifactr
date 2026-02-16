### Requirement: Spelunk alias
The `spelunk` command SHALL accept `sp` as an alias.

#### Scenario: Using sp alias
- **WHEN** user runs `art sp`
- **THEN** the command SHALL behave identically to `art spelunk`

### Requirement: Store alias
The `store` command SHALL accept `st` as an alias.

#### Scenario: Using st alias
- **WHEN** user runs `art st ./my-dir`
- **THEN** the command SHALL behave identically to `art store ./my-dir`

### Requirement: Create alias
The `create` command SHALL accept `cr` as an alias.

#### Scenario: Using cr alias
- **WHEN** user runs `art cr skill my-skill -d "desc"`
- **THEN** the command SHALL behave identically to `art create skill my-skill -d "desc"`

### Requirement: Edit alias
The `edit` command SHALL accept `ed` as an alias. This applies to both the top-level `art edit` command and the `art config edit` subcommand.

#### Scenario: Using ed alias at top level
- **WHEN** user runs `art ed skill my-skill`
- **THEN** the command SHALL behave identically to `art edit skill my-skill`

#### Scenario: Using ed alias under config
- **WHEN** user runs `art config ed`
- **THEN** the command SHALL behave identically to `art config edit`

#### Scenario: Using ed alias with config aliases
- **WHEN** user runs `art conf ed` or `art c ed`
- **THEN** the command SHALL behave identically to `art config edit`

### Requirement: Edit subcommand type aliases
The `edit` command's artifact type positional argument SHALL accept single-letter aliases: `s` for `skill`, `c` for `command`, `a` for `agent`.

#### Scenario: Edit skill with short alias
- **WHEN** user runs `art edit s my-skill`
- **THEN** the command SHALL behave identically to `art edit skill my-skill`

#### Scenario: Edit command with short alias
- **WHEN** user runs `art edit c my-command`
- **THEN** the command SHALL behave identically to `art edit command my-command`

#### Scenario: Edit agent with short alias
- **WHEN** user runs `art edit a my-agent`
- **THEN** the command SHALL behave identically to `art edit agent my-agent`

### Requirement: Alias dispatch in main
The `main()` dispatch logic SHALL recognize all new aliases when routing to handler functions.

#### Scenario: Dispatch recognizes sp
- **WHEN** argparse resolves `sp` to the spelunk command
- **THEN** `main()` SHALL route to `handle_spelunk()`

#### Scenario: Dispatch recognizes st
- **WHEN** argparse resolves `st` to the store command
- **THEN** `main()` SHALL route to `handle_store()`

#### Scenario: Dispatch recognizes cr
- **WHEN** argparse resolves `cr` to the create command
- **THEN** `main()` SHALL route to `handle_create_skill()` or `handle_create_artifact()` as appropriate

#### Scenario: Dispatch recognizes ed
- **WHEN** argparse resolves `ed` to the edit command
- **THEN** `main()` SHALL route to `handle_edit()`
