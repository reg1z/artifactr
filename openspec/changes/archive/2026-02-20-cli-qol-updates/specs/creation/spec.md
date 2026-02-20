## ADDED Requirements

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
