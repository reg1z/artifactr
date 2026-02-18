# Tool Support
- [x] Built-ins for popular tools
  - [x] claude-code
  - [x] opencode
  - [x] Codex (skills only)
- [x] Custom tool support via `art tool add` (Cursor, Gemini CLI, Amp, Goose, etc.)
- [x] Per-artifact-type path configuration (partial artifact support)
- [x] Three-tier tool resolution: built-in < global config < vault config
- [x] `vault.yaml` for portable vault metadata and vault-scoped tool definitions

# Vault Management

## User-friendliness
- [x] Add the option for a user to disable artifact(s) from being added to `.git/info/exclude` (`--no-exclude` on `proj import`).
- [x] When adding a new vault, if a vault already exists with the same name, have the program prompt the user for a different name.

## Catalog Management
- [ ] Catalog Management
  - [ ] Support for exporting any number of vaults to a directory (as a folder/zip archive/etc)
  - [ ] Import an entire **catalog** (of potentially many vaults) with 1 command

## Vault-Tool Pairs
- [ ] Vault-Tool pairs.
  - Ability to explicitly "pair" a vault with an intended agentic tool.
  - Defined in `vault.yaml` with any applicable custom tool definitions.
- Key Questions
  - Would this pairing override the selected default tool when using a certain vault?
    - Potentially, this setting could override any default tool during multi-vault operations, unless a specific tool is defined with `--tools`

# Artifact Management
Not all agentic tools support the same artifact types

CRUD Support for:
- [x] Skills
- [x] Commands
- [x] Agents
- [ ] Custom Artifact Types

## Artifact Creation
- [x] `art create <artifact-type>` command


## Artifact Editing
- [x] `art edit <artifact-type> <artifact-name>`
  - Opens the specific artifact's main `<ARTIFACT>.md` (e.g. SKILL.md) in your terminal/shell default text editor (nano/vim/nvim, whatever the env var is configured as)

## Custom Artifact types
- [ ] Ability to configure custom artifact types.
 - [ ] Can be defined globally (`~/.config/artifactr/`) or vault-scoped (`vault.yaml`).
- Key Questions
  - Should these be tied to individual tools?
    - The addition of additional artifact types might bloat the columnar output of `art tool list`.

## User-defined Artifact "Marketplaces" Integration
- [ ] A way to parse plugin / skill marketplace structures for artifacts.
  - e.g. claude marketplace format (https://code.claude.com/docs/en/plugin-marketplaces).
- Key Questions
  - Should ANY network connectivity be added to the tool at all?
  - Should a user be able define their own personal list of marketplace URLs to facilitate browsing?
  - Package manager format for artifact management?



# TUI
- [ ] Eventual TUI frontend. Likely implemented with textual (if at all).
