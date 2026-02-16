## MODIFIED Requirements

### Requirement: Categorized command groups in epilog
The `art` parser epilog MUST display commands grouped into categories. Command aliases SHALL be shown in parentheses next to the command name.

#### Scenario: Vault Operations category
- **WHEN** `art --help` is run
- **THEN** the epilog MUST contain a "Vault Operations:" section listing `ls`, `rm`, `store (st)`, `edit (ed)`, and `create (cr)` with brief descriptions

#### Scenario: Namespaces category
- **WHEN** `art --help` is run
- **THEN** the epilog MUST contain a "Namespaces:" section listing `vault`, `tool`, `project`, and `config` with their aliases shown in parentheses and brief descriptions

#### Scenario: Discovery category
- **WHEN** `art --help` is run
- **THEN** the epilog MUST contain a "Discovery:" section listing `spelunk (sp)` with a brief description

#### Scenario: Config namespace description
- **WHEN** `art --help` is run
- **THEN** the `config` entry in the Namespaces section SHALL indicate it covers both tool-specific global configs and artifactr's own configuration

## ADDED Requirements

### Requirement: Top-level command description paragraphs
Each top-level command and namespace SHALL have a `description=` parameter that provides a brief, friendly explanation shown in its own `-h` output.

#### Scenario: art vault -h
- **WHEN** user runs `art vault -h`
- **THEN** a description paragraph SHALL appear explaining vault management

#### Scenario: art tool -h
- **WHEN** user runs `art tool -h`
- **THEN** a description paragraph SHALL appear explaining tool management

#### Scenario: art project -h
- **WHEN** user runs `art project -h`
- **THEN** a description paragraph SHALL appear explaining project-side operations

#### Scenario: art config -h
- **WHEN** user runs `art config -h`
- **THEN** a description paragraph SHALL appear explaining tool-specific global config management and that `edit` opens artifactr's own config

#### Scenario: art ls -h
- **WHEN** user runs `art ls -h`
- **THEN** a description paragraph SHALL appear explaining vault artifact listing

#### Scenario: art rm -h
- **WHEN** user runs `art rm -h`
- **THEN** a description paragraph SHALL appear explaining vault artifact removal

#### Scenario: art store -h
- **WHEN** user runs `art store -h`
- **THEN** a description paragraph SHALL appear explaining artifact storage from directories into vaults

#### Scenario: art edit -h
- **WHEN** user runs `art edit -h`
- **THEN** a description paragraph SHALL appear explaining artifact editing

#### Scenario: art create -h
- **WHEN** user runs `art create -h`
- **THEN** a description paragraph SHALL appear explaining artifact creation

#### Scenario: art spelunk -h
- **WHEN** user runs `art spelunk -h`
- **THEN** a description paragraph SHALL appear explaining artifact discovery

### Requirement: Config edit help clarification
The `art config edit` help text SHALL make it clear that this command opens artifactr's own global YAML configuration file, not any tool-specific config.

#### Scenario: Config edit help text
- **WHEN** user runs `art config edit -h`
- **THEN** the help text SHALL explicitly mention "artifactr's global config" or equivalent, distinguishing it from tool configs

### Requirement: Config import help clarification
The `art config import` help text SHALL make it clear that this command imports artifacts into the external tool-specific global config directories (e.g., `~/.claude/commands/`), not into artifactr's own configuration.

#### Scenario: Config import help text
- **WHEN** user runs `art config import -h`
- **THEN** the help text SHALL explicitly state that artifacts are imported into tool-specific global config directories
