## ADDED Requirements

### Requirement: Artifact-shaped directory detection
The depth scanning system MUST identify directories that contain artifact-shaped content by looking for well-known directory names (`skills/`, `agents/`, `commands/`).

#### Scenario: Skills directory detected
- **WHEN** a directory named `skills` is found within the scan depth
- **THEN** its subdirectories MUST be checked for `SKILL.md` files to identify skill artifacts

#### Scenario: Commands directory detected
- **WHEN** a directory named `commands` is found within the scan depth
- **THEN** its `.md` files MUST be identified as command artifacts

#### Scenario: Agents directory detected
- **WHEN** a directory named `agents` is found within the scan depth
- **THEN** its `.md` files MUST be identified as agent artifacts

#### Scenario: Nested artifact directories
- **WHEN** multiple `skills/` directories exist at different depths within the scan range
- **THEN** all of them MUST be discovered and their artifacts included in results

#### Scenario: Source attribution for depth-scanned artifacts
- **WHEN** artifacts are found via depth scanning (not vault or tool-config discovery)
- **THEN** the source MUST be attributed as `"directory"` with the parent path of the artifact directory
