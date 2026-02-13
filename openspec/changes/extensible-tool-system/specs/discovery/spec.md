## MODIFIED Requirements

### Requirement: Artifact probing logic
A shared probing mechanism MUST discover artifacts within a target directory by searching tool config directories.

#### Scenario: Config directory search
- **WHEN** a target directory is probed
- **THEN** directories corresponding to all known tools' repo-local artifact paths MUST be searched (derived from tool definitions, not hardcoded)

#### Scenario: Partial tool probing
- **WHEN** probing for a tool that only supports skills
- **THEN** only the tool's skills path MUST be searched; commands and agents paths MUST be skipped

#### Scenario: Custom tool probing
- **WHEN** a custom tool is defined with `skills: .my-tool/skills`
- **THEN** `.my-tool/skills/` MUST be included in the probe search paths

#### Scenario: Skill detection
- **WHEN** searching a tool's skills path
- **THEN** any subdirectory containing a `SKILL.md` file (case-sensitive) is detected as a skill artifact

#### Scenario: Agent detection
- **WHEN** searching a tool's agents path
- **THEN** any `.md` file directly within is detected as an agent artifact

#### Scenario: Command detection
- **WHEN** searching a tool's commands path
- **THEN** any `.md` file directly within is detected as a command artifact
