## ADDED Requirements

### Requirement: Depth-controlled artifact scanning
When spelunking a non-vault, non-tool-config directory, the system MUST perform a depth-controlled recursive scan for artifact-shaped directory structures.

#### Scenario: Default depth scanning
- **WHEN** `art spelunk ./project` is run and `./project` is not a vault and has no tool config directories
- **THEN** the system MUST scan up to depth 2 for directories named `skills/`, `agents/`, or `commands/` containing artifact-shaped content

#### Scenario: Custom depth
- **WHEN** `art spelunk ./project --depth 4` is run
- **THEN** the system MUST scan up to 4 levels deep for artifact-shaped directories

#### Scenario: Depth 0
- **WHEN** `art spelunk ./project --depth 0` is run
- **THEN** only the immediate target directory MUST be scanned (no recursion)

#### Scenario: Skill detection in scanned directories
- **WHEN** a `skills/` directory is found during depth scanning
- **THEN** subdirectories containing `SKILL.md` MUST be detected as skill artifacts

#### Scenario: Command detection in scanned directories
- **WHEN** a `commands/` directory is found during depth scanning
- **THEN** `.md` files directly within MUST be detected as command artifacts

#### Scenario: Agent detection in scanned directories
- **WHEN** an `agents/` directory is found during depth scanning
- **THEN** `.md` files directly within MUST be detected as agent artifacts

#### Scenario: Vault and tool-config take priority
- **WHEN** `art spelunk ./dir` is run and `./dir` contains a `vault.yaml`
- **THEN** vault discovery MUST be used and depth scanning MUST NOT run

### Requirement: Structured output formats
The `art spelunk` command MUST support multiple output formats via `--format`.

#### Scenario: Human output (default)
- **WHEN** `art spelunk` is run without `--format` or with `--format human`
- **THEN** output MUST be in the existing human-readable format

#### Scenario: JSON output
- **WHEN** `art spelunk --format json` is run
- **THEN** output MUST be valid JSON containing artifact data with type, name, path, and source information

#### Scenario: YAML output
- **WHEN** `art spelunk --format yaml` is run
- **THEN** output MUST be valid YAML containing the same data structure as JSON output

#### Scenario: Markdown output
- **WHEN** `art spelunk --format md` is run
- **THEN** output MUST be a markdown-formatted table of artifacts

#### Scenario: Markdown alias
- **WHEN** `art spelunk --format markdown` is run
- **THEN** it MUST behave identically to `--format md`

#### Scenario: Structured output data
- **WHEN** structured output (json, yaml, md) is requested
- **THEN** each artifact entry MUST include at minimum: `name`, `type` (skill/command/agent), `path` (absolute file path), and `source` (vault name, tool name, or "directory")
