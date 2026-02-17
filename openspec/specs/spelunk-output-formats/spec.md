## ADDED Requirements

### Requirement: Spelunk output formatting layer
A formatting layer MUST exist that serializes spelunk discovery results into the requested output format.

#### Scenario: Human format rendering
- **WHEN** the human format is selected
- **THEN** the existing human-readable output MUST be produced (no change to current behavior)

#### Scenario: JSON format rendering
- **WHEN** the json format is selected
- **THEN** output MUST be serialized using `json.dumps` with indentation for readability

#### Scenario: YAML format rendering
- **WHEN** the yaml format is selected
- **THEN** output MUST be serialized using PyYAML's `yaml.dump` with `default_flow_style=False`

#### Scenario: Markdown format rendering
- **WHEN** the md/markdown format is selected
- **THEN** output MUST be a markdown table with columns for Name, Type, Source, and Path

#### Scenario: Empty results
- **WHEN** no artifacts are discovered and structured output is requested
- **THEN** JSON MUST output an empty array `[]`, YAML MUST output an empty list, and markdown MUST output a table header with no rows
