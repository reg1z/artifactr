## Coding Agent Tool Support
- [x] claude-code
- [x] opencode
- [x] Codex (built-in, skills only)
- [x] Custom tool support via `art tool add` (Cursor, Gemini CLI, Amp, Goose, etc.)
- [x] Per-artifact-type path configuration (partial artifact support)
- [x] Three-tier tool resolution: built-in < global config < vault config
- [x] `vault.yaml` for portable vault metadata and vault-scoped tool definitions

## User-friendliness
- [ ] Add the option for a user to disable artifact(s) from being added to `.git/info/exclude`.

New commands
- [ ] New command: Generate an example vault
  - Generates an example vault with some different types of artifacts.
- [ ] New command: For editing a target repo's artifacts. Delete/wipe/etc.

## Feature Update: Adding Vaults
- [ ] New Command: 
  - Adds an entire vault catalog in one command.
  - The default names of vaults should just be the same as their directory name.
- [ ] `art vault add` changes
  - Have this command assign a default name to the vault that matches it's folder name. e.g. `/path/to/my/personal-vault` would be named "personal-vault"
  - When adding a new vault, if a vault already exists with the same name, have the program prompt the user for a different name.
  - Has a `--set-default` flag that sets the initialized vault as the new default
- [ ] `art vault init <vault_name> <target_dir>` Initialize an entirely new vault in a target directory. Requires providing a name for the vault.
  - If a user has no default vault configured, the program will notify users to either use `art vault add` to add a vault into the tool's configuration or to use `art vault init` to initialize a new vault.
  - Has a `--set-default` flag that sets the initialized vault as the new default


## Feature Addition: Artifact Creation
NOTE: Not all coding agents support the same artifact types. It just so happens that claude-code and opencode support similar structures.

- [x] New command: `art create <artifact-type>`
  - [ ] TUI-based artifact creation
    - uses the textual library for the interface https://textual.textualize.io/
  - Support for
    - Initially we only want to support skills.
    - [x] Skills
    - [ ] Commands
    - [ ] Agents

### Artifact Creation: Skills
Documentation referencing tool-specific yaml frontmatter has been included in the repo's references.
- Input fields for yaml frontmatter
  - name (required)
  - description (required)
  - the user can add any arbitrary number of other frontmatter fields they wish. Suggestions exist for frontmatter to use based on the tool they have selected. These suggestions provide tooltips with some small info on the suggested frontmatter field, the tool it's supported in and what it's used for. The reason being that claude-code/opencode/other coding agents automatically detect different fields from one another.
- Input field for the actual skill content.

## Feature Addition: Artifact Editing
- [ ] New command: `art edit <artifact-type> <artifact-name>`
  - Opens the specific artifact's main `<ARTIFACT>.md` (e.g. SKILL.md) in your terminal's/shell's default text editor (nano/vim/nvim, whatever the env var is configured as)

## Feature Addition: Marketplace Integration
- [ ] Add a way to parse plugin / skill marketplaces for artifacts.
  - e.g. in the case of claude marketplaces (https://code.claude.com/docs/en/plugin-marketplaces), it would use `marketplace.json` to find targets.
- [ ] User can define their own personal list of marketplace URLs


