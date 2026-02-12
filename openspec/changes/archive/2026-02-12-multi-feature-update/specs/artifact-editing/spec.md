## ADDED Requirements

### Requirement: Edit command
The `art edit <artifact-type> <artifact-name>` command MUST open the artifact's main markdown file in the user's terminal editor.

#### Scenario: Edit skill in vault
- **WHEN** `art edit skill my-skill` is run
- **THEN** the editor MUST open `<default-vault>/skills/my-skill/SKILL.md`

#### Scenario: Edit agent in vault
- **WHEN** `art edit agent my-agent` is run
- **THEN** the editor MUST open `<default-vault>/agents/my-agent.md`

#### Scenario: Edit command in vault
- **WHEN** `art edit command my-cmd` is run
- **THEN** the editor MUST open `<default-vault>/commands/my-cmd.md`

#### Scenario: Explicit vault
- **WHEN** `--vault=<name-or-path>` is provided
- **THEN** the artifact MUST be resolved in that vault instead of the default

#### Scenario: Artifact not found in vault
- **WHEN** the specified artifact does not exist in the target vault
- **THEN** an error MUST be printed to stderr and the command MUST exit with code 1

#### Scenario: No default vault
- **WHEN** no vault is specified and no default vault is set
- **THEN** an error MUST be printed suggesting `art vault add` or `art vault init`

### Requirement: Project-local editing
When `--here` / `-H` is provided, the artifact MUST be resolved in the current project's tool config directory.

#### Scenario: Here mode with default tool
- **WHEN** `art edit skill my-skill --here` is run and the default tool is `claude-code`
- **THEN** the editor MUST open `.claude/skills/my-skill/SKILL.md` relative to the current directory

#### Scenario: Here mode with explicit tool
- **WHEN** `art edit skill my-skill --here --tools=opencode` is run
- **THEN** the editor MUST open `.opencode/skills/my-skill/SKILL.md`

#### Scenario: Here mode artifact not found
- **WHEN** `--here` is used and the artifact does not exist in the project
- **THEN** an error MUST be printed to stderr and the command MUST exit with code 1

### Requirement: Editor resolution
The editor MUST be resolved through a defined fallback chain.

#### Scenario: VISUAL environment variable
- **WHEN** `$VISUAL` is set
- **THEN** its value MUST be used as the editor

#### Scenario: EDITOR environment variable
- **WHEN** `$VISUAL` is not set and `$EDITOR` is set
- **THEN** `$EDITOR` MUST be used as the editor

#### Scenario: Fallback chain
- **WHEN** neither `$VISUAL` nor `$EDITOR` is set
- **THEN** the system MUST search for executables in order: `nano`, `vim`, `vi`, using the first one found

#### Scenario: No editor available
- **WHEN** no editor can be found through any of the above methods
- **THEN** an error MUST be printed: a message indicating no editor was found and suggesting the user set `$EDITOR`

### Requirement: Editor invocation
The editor MUST be launched as a subprocess with the artifact file path as argument.

#### Scenario: Subprocess execution
- **WHEN** the editor is invoked
- **THEN** it MUST run via `subprocess.run([editor, file_path])` and the CLI MUST return the editor's exit code

#### Scenario: Valid artifact types
- **WHEN** `art edit` is run
- **THEN** the `artifact-type` argument MUST accept only `skill`, `agent`, or `command`
