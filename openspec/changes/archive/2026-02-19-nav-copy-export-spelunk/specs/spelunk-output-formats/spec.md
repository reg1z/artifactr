## MODIFIED Requirements

### Requirement: Spelunk output formatting layer
A formatting layer MUST exist that serializes spelunk discovery results into the requested output format.

#### Scenario: Human format rendering
- **WHEN** the human format is selected
- **THEN** output MUST be a fixed-width table with columns: NAME, TYPE, LOCATION
- **AND** the TOOL column MUST NOT be present
- **AND** the DESCRIPTION column MUST NOT be present by default

#### Scenario: JSON format rendering
- **WHEN** the json format is selected
- **THEN** output MUST be serialized using `json.dumps` with indentation for readability

#### Scenario: YAML format rendering
- **WHEN** the yaml format is selected
- **THEN** output MUST be serialized using PyYAML's `yaml.dump` with `default_flow_style=False`

#### Scenario: Markdown format rendering
- **WHEN** the md/markdown format is selected
- **THEN** output MUST be a markdown table with columns for Name, Type, and Location

#### Scenario: Empty results
- **WHEN** no artifacts are discovered and structured output is requested
- **THEN** JSON MUST output an empty array `[]`, YAML MUST output an empty list, and markdown MUST output a table header with no rows

## ADDED Requirements

### Requirement: Spelunk LOCATION column
The human-format spelunk output MUST include a LOCATION column showing the artifact's path relative to the original search root.

#### Scenario: Vault spelunk — relative to vault root
- **WHEN** spelunking a vault directory
- **THEN** the LOCATION column MUST show the artifact path relative to the vault root (e.g., `skills/my-skill`)

#### Scenario: Directory spelunk — relative to target
- **WHEN** spelunking a non-vault directory
- **THEN** the LOCATION column MUST show the artifact path relative to the original target directory passed to the command (e.g., `.claude/skills/my-skill`)

#### Scenario: Depth-scan finds vault mid-search — still relative to original root
- **WHEN** depth scanning discovers a vault at some nested level within the target directory
- **THEN** artifacts within that vault MUST have their LOCATION shown relative to the original search root, NOT relative to the discovered vault root

#### Scenario: Global spelunk — home-collapsed paths
- **WHEN** spelunking global config directories
- **THEN** the LOCATION column MUST show paths with the home directory collapsed to `~/` (e.g., `~/.claude/skills/my-skill`)

#### Scenario: Symlink resolves outside search root — fallback to absolute
- **WHEN** an artifact's resolved absolute path cannot be expressed relative to the original search root (e.g., because a symlink targets a path outside the tree)
- **THEN** the LOCATION column MUST show the absolute path rather than raising an error

### Requirement: Spelunk --verbose flag restores DESCRIPTION column
The `art spelunk` command MUST support a `--verbose` / `-v` flag that adds the DESCRIPTION column to human-format output.

#### Scenario: --verbose adds DESCRIPTION column
- **WHEN** `art spelunk [target] --verbose` is run (alias: `-v`)
- **THEN** the human-format output MUST include a DESCRIPTION column after LOCATION
- **AND** the DESCRIPTION MUST be populated from YAML frontmatter or the first non-frontmatter line of the artifact file, consistent with the existing `extract_description` logic

#### Scenario: Default output omits DESCRIPTION
- **WHEN** `art spelunk` is run without `--verbose`
- **THEN** the DESCRIPTION column MUST NOT appear in the output
