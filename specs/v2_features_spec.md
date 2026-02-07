---
plan: plans/v2_features_plan.md
---

# Artifactr v2 Features Specification

## Overview

This is an addendum to [the main Artifactr spec](specs/artifactr_spec.md). It covers five new features:

1. `art vault list --all` flag for displaying full vault hierarchy
2. `art import --artifacts` flag for selective artifact importing
3. `.art-cache/imported` tracking file for recording all imports
4. `art spelunk` command for discovering artifacts in a target directory
5. `art store` command for storing discovered artifacts into a vault

## New Terminology

| Term | Definition |
|------|------------|
| **Tool Config Directory** | The hidden folder in a project where a tool stores its config (e.g., `.claude/` for claude-code, `.opencode/` for opencode) |
| **Art Cache** | A `.art-cache/` folder created in target directories to track imported artifacts |
| **Imported File** | The `.art-cache/imported` file that records which artifacts have been imported, along with their vault and tool context |

---

## Requirements

### 1. `art vault list --all` / `-a` Flag

Adds a new flag to the existing `art vault list` command that displays the full vault hierarchy.

#### 1.1. Flag Definition

1.1.1. The `art vault list` command MUST accept `-a` and `--all` flags.

1.1.2. When neither flag is provided, the existing behavior MUST remain unchanged (shows vault paths with default marker).

#### 1.2. Hierarchy Display

1.2.1. When `--all` is provided, the output MUST show a tree-style, indented hierarchy. Since vaults store artifacts in a tool-agnostic structure, the hierarchy has two levels below the vault:
- **Level 1**: Vault name (or path if unnamed)
- **Level 2**: Artifact type headings (e.g., `skills/`, `agents/`, `commands/`) — only if that type has artifacts
- **Level 3**: Individual artifact names within each type

1.2.2. Artifacts MUST be grouped by artifact type (skills, agents, commands). The type label (e.g., `skills/`) acts as a sub-heading only if that type has artifacts.

1.2.3. Artifact names MUST use the filesystem name:
- For **skills** (directories): use the directory name, displayed with a trailing `/` to indicate it's a folder
- For **agents** and **commands** (files): use the filename (e.g., `my-agent.md`)

1.2.4. If an artifact is a folder (e.g., a skill directory), its internal contents MUST NOT be shown — only the folder name itself.

1.2.5. The default vault MUST still be marked with a `*` prefix and `(default)` label, consistent with the existing list output.

#### 1.3. Example Output

```
Registered vaults:
  * favorites (/home/user/vault1) (default)
      skills/
        helping-hand/
        code-review/
      agents/
        reviewer.md

    /home/user/vault2
      commands/
        deploy.md
```

#### 1.4. Edge Cases

1.4.1. If a vault directory no longer exists on disk, the command MUST still list it in the hierarchy but print a warning: `(path not found)` next to the vault name.

1.4.2. If a vault has no artifact directories (no `skills/`, `agents/`, or `commands/` folders), it MUST still appear in the list with no children.

---

### 2. `art import --artifacts` Flag

Adds a new flag to `art import` that allows importing individual artifacts by name instead of importing everything from a vault.

#### 2.1. Flag Definition

2.1.1. The `art import` command MUST accept an `--artifacts` flag.

2.1.2. The flag value MUST be a comma-separated list of artifact names. Example:
```
art import ~/repos/my-project --artifacts=helping-hand,utility-tool,code-review
```

2.1.3. Whitespace around commas in the list MUST be trimmed.

#### 2.2. Artifact Name Resolution

2.2.1. Each name in the list MUST be resolved by searching the vault for matching artifacts across all artifact types (skills, agents, commands).

2.2.2. If an artifact name is **unique** across all types, it MUST be imported without further qualification.

2.2.3. If an artifact name exists in **multiple** artifact types (e.g., both `skills/write-thing/` and `commands/write-thing.md`), the user MUST specify which one using a type prefix:
```
art import ~/repos/my-project --artifacts=skills/write-thing,commands/write-that
```

2.2.4. If a duplicate name is detected and the user has **not** specified a type prefix, the program MUST:
1. Notify the user that the artifact name is ambiguous
2. List the available options with their type prefixes
3. Prompt the user to select exactly **one** option

Example prompt:
```
Ambiguous artifact name: "write-thing"
Found in multiple types:
  1. skills/write-thing
  2. commands/write-thing
Select one [1-2]:
```

2.2.5. If an artifact name (with or without prefix) is not found in the vault, the program MUST print an error for that artifact and continue processing the remaining artifacts.

#### 2.3. Interaction with Existing Flags

2.3.1. `--artifacts` MUST work with `--vault` to specify which vault to search for the named artifacts.

2.3.2. `--artifacts` MUST work with `--tools` to control which tool destinations receive the imported artifacts.

2.3.3. `--artifacts` MUST work with `--link` / `-l` to create symlinks instead of copies for the selected artifacts.

2.3.4. When `--artifacts` is provided, ONLY the specified artifacts are imported — the full vault contents are NOT imported.

---

### 3. `.art-cache/imported` Tracking File

Introduces a cache directory in target projects to track which artifacts have been imported.

#### 3.1. Cache Directory Structure

3.1.1. When artifacts are imported (via `art import`, with or without `--artifacts`), a `.art-cache/` directory MUST be created in the target directory if it doesn't already exist.

3.1.2. Inside `.art-cache/`, a file named `imported` MUST be created or updated.

3.1.3. The `.art-cache/` directory MUST be added to `.git/info/exclude` along with all other imported artifacts.

#### 3.2. Imported File Format

3.2.1. Each line in `.art-cache/imported` represents a single imported artifact.

3.2.2. Each line MUST use dot-separated notation with three parts:
```
<vault-name-or-basename>.<tool-name>.<artifact-name>
```

- **vault-name-or-basename**: The vault's assigned name if it has one; otherwise, the basename of the vault directory path
- **tool-name**: The tool the artifact was imported for (e.g., `claude-code`, `opencode`)
- **artifact-name**: The filesystem name of the artifact (directory name for skills, filename without extension for agents/commands)

3.2.3. When a single artifact is imported into multiple tools, a **separate line** MUST be written for each tool. Example:
```
favs.claude-code.helping-hand
favs.opencode.helping-hand
```

3.2.4. Duplicate lines MUST NOT be written. Before appending, the program MUST check if the exact line already exists.

#### 3.3. Example `.art-cache/imported`

```
favs.claude-code.helping-hand
vault1.claude-code.utility-tool
vault1.opencode.utility-tool
```

This shows:
- `helping-hand` was imported from the vault named `favs` for `claude-code`
- `utility-tool` was imported from `vault1` for both `claude-code` and `opencode`

---

### 4. `art spelunk <target>` Command

A new command that probes a target directory for existing artifacts and reports what it finds.

#### 4.1. Command Definition

4.1.1. The command MUST accept a single positional argument: `target`, the path to the directory to probe.

4.1.2. The target does NOT need to be a git repository. It can be any directory.

#### 4.2. Probing Logic

4.2.1. The command MUST only search within directories that correspond to supported tools' config directories. Currently, this means:
- `.claude/` (for claude-code)
- `.opencode/` (for opencode)

4.2.2. Within each tool config directory, the command MUST search the standard artifact type subdirectories: `skills/`, `agents/`, `commands/`.

4.2.3. Artifact detection rules:
- **Skills**: Any subdirectory within `skills/` that contains a `SKILL.md` file (case-sensitive)
- **Agents**: Any `.md` file directly within `agents/`
- **Commands**: Any `.md` file directly within `commands/`

#### 4.3. Output Format

4.3.1. The output MUST be a table with aligned columns. The columns, in order, are:

| Column | Description |
|--------|-------------|
| **NAME** | The artifact name. For skills, the directory name. For agents/commands, the filename without extension. |
| **TYPE** | The artifact type: `skill`, `agent`, or `command` (singular form) |
| **TOOL** | The tool the artifact was found under, derived from the config directory name (e.g., `claude` for `.claude/`, `opencode` for `.opencode/`) |
| **DESCRIPTION** | If the main artifact file contains YAML frontmatter with a non-empty `description` property, show it. Otherwise, show `-` |

4.3.2. A header row MUST be printed above the table data.

4.3.3. Column widths MUST be dynamically sized to fit the longest value in each column, with at least 2 spaces of padding between columns.

#### 4.4. Import Detection

4.4.1. After discovering artifacts, the command MUST check the target directory for an `.art-cache/imported` file.

4.4.2. For each discovered artifact, the command MUST compare its name against the artifact names listed in `.art-cache/imported`.

4.4.3. If a match is found, the output MUST append a marker to the artifact's name indicating it is a previous import. The marker format is: `(imported: <vault-name>)` where `<vault-name>` is taken from the matching line in the imported file.

Example output row:
```
helping-hand (imported: favs)    skill    claude    A helpful assistant
```

4.4.4. If a discovered artifact matches multiple import entries (e.g., imported from different vaults), all vault names MUST be listed: `(imported: favs, vault2)`.

#### 4.5. Frontmatter Parsing

4.5.1. To extract the `description` property, the command MUST read the main artifact file:
- For skills: `<skill-dir>/SKILL.md`
- For agents: the agent `.md` file itself
- For commands: the command `.md` file itself

4.5.2. YAML frontmatter is delimited by `---` on its own line at the start of the file and closed by another `---` on its own line.

4.5.3. If the file does not contain valid YAML frontmatter, or the frontmatter does not have a `description` key, or the `description` value is empty, the description column MUST show `-`.

4.5.4. Descriptions longer than 50 characters MUST be truncated with `...` appended.

#### 4.6. Edge Cases

4.6.1. If the target directory does not exist, the program MUST print an error and exit with code 1.

4.6.2. If no tool config directories are found in the target, the program MUST print: `No artifacts found in <target>`.

4.6.3. If tool config directories exist but contain no artifacts, the program MUST print: `No artifacts found in <target>`.

#### 4.7. Example Output

```
NAME                              TYPE      TOOL      DESCRIPTION
helping-hand (imported: favs)     skill     claude    A helpful assistant
utility-tool                      skill     claude    -
reviewer                          agent     claude    Reviews code changes
deploy                            command   opencode  -
```

---

### 5. `art store <target_dir>` Command

A new command for storing individual artifacts discovered in a target directory into a vault.

#### 5.1. Command Definition

5.1.1. The command MUST accept a single positional argument: `target_dir`, the path to the directory containing artifacts to store.

5.1.2. The command MUST accept an optional `--vault` flag to specify which vault to store into. If not provided, the default vault MUST be used.

#### 5.2. Discovery and Selection

5.2.1. The command MUST discover artifacts using the same probing logic as `art spelunk` (see Section 4.2).

5.2.2. After discovering artifacts, the command MUST present them to the user in a numbered, interactive list and allow the user to select which ones to store.

5.2.3. The selection prompt MUST support:
- Individual numbers: `1`
- Comma-separated numbers: `1,3,5`
- Ranges: `1-3`
- The word `all` to select everything
- Combinations: `1,3-5,7`

Example:
```
Discovered artifacts in /home/user/repo:
  1. helping-hand (skill) - .claude/skills/helping-hand
  2. utility-tool (skill) - .claude/skills/utility-tool
  3. reviewer (agent) - .claude/agents/reviewer.md
  4. deploy (command) - .opencode/commands/deploy.md

Select artifacts to store [1-4, all]:
```

#### 5.3. Validation

5.3.1. For the operation to succeed, each selected artifact MUST be located within a recognized tool config directory (`.claude/` or `.opencode/`). This is inherently satisfied by the discovery logic (Section 4.2), but MUST be validated.

5.3.2. If the target vault does not exist in the catalog, the program MUST print an error and exit with code 1.

5.3.3. If no artifacts are discovered, the program MUST print: `No artifacts found in <target_dir>` and exit with code 0.

#### 5.4. Storage Logic

5.4.1. When storing an artifact, it MUST be copied from the tool config directory to the vault's tool-agnostic structure. Specifically:
- A skill at `<target>/.claude/skills/my-skill/` is stored to `<vault>/skills/my-skill/`
- An agent at `<target>/.claude/agents/my-agent.md` is stored to `<vault>/agents/my-agent.md`
- A command at `<target>/.opencode/commands/deploy.md` is stored to `<vault>/commands/deploy.md`

5.4.2. If an artifact with the same name already exists in the vault, the user MUST be prompted before overwriting (reuse the existing `prompt_overwrite` function).

5.4.3. After storing, the program MUST print a confirmation for each artifact stored.

#### 5.5. Example Usage

```sh
# Store artifacts into default vault
art store ~/repos/my-project

# Store artifacts into a specific vault
art store ~/repos/my-project --vault=favorites
```

#### 5.6. Example Session

```
$ art store ~/repos/my-project
Discovered artifacts in /home/user/repos/my-project:
  1. helping-hand (skill) - .claude/skills/helping-hand
  2. utility-tool (skill) - .claude/skills/utility-tool
  3. reviewer (agent) - .claude/agents/reviewer.md

Select artifacts to store [1-3, all]: 1,3

Stored: helping-hand (skill) -> /home/user/vault/skills/helping-hand
Stored: reviewer (agent) -> /home/user/vault/agents/reviewer.md

2 artifact(s) stored to vault: favorites
```

---

### 6. Error Handling

6.1. All errors MUST be printed to stderr, consistent with existing behavior.

6.2. All new commands MUST exit with code 1 on error and code 0 on success.

6.3. User prompts (overwrite, disambiguation, selection) MUST handle `EOFError` gracefully by defaulting to "no action" (skip/cancel).

---

### 7. Dependencies

7.1. The `yaml` module (PyYAML, already a dependency) MUST be used for parsing YAML frontmatter in `art spelunk`.

7.2. No new external dependencies are required.
