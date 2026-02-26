# ROADMAP.md
Keeping track of potential features.

Stuff under "Planned" will definitely be shipped.

## Planned

### Documentation
- Add better documentation apart from the README.

### artifactr skills
- Importable skill files that ship with the tool that provide coding agents with context of how and where to create skills/artifacts with `artifactr` in mind.

### Backups
- Backup format for:
  - Vault Catalog
  - Program configuration

### Output Formats
- Add json/yaml/markdown output formats to more commands than just `art spelunk`.

---

## Exploring

### Vault → Tool Pairing
- Ability to explicitly "pair" a vault with an intended agentic tool.
- Defined in `vault.yaml` with any applicable custom tool definitions.
- Would communicate the intention of a vault.
- Would pair well with vault-specific tool definitions.
- Key Questions
	- Would this pairing override the selected default tool when using a certain vault?
	    - Potentially, this setting would override any default tool during multi-vault operations, unless a specific tool is defined with `--tools`

### Artifact Types

#### Other Potential Built-in Artifact Types
- Scripts
  - Would these be import-able into skills?
- Hooks (event handlers)
- AGENTS.md
  - This doesn't seem terribly useful, as AGENTS.md is usually project-specific.
  - Is Vault -> Project pairing a good idea?

#### Custom Artifact Types
Not all agentic tools support the same artifact types. And there are frequently new formats and standards popping up.

- Ability to configure custom artifact types.
- Key Questions
	- Defined globally, (`~/.config/artifactr/`), vault-scoped (`vault.yaml`), or have options for both?
	- Should we be able to tie artifacts to specific tools?
		- Presumably this is part of the intention behind **Vault → Tool Pairing**, so such a feature might be redundant.
	- The addition of more artifact types might bloat the columnar output of `art tool list`.

#### Converting an artifact between types

### OpenCode-specific
- Option to add corresponding minimal command(s) for imported skills

### Recursive AGENTS.md linking
- Automate symbolic linking of AGENTS.md throughout an entire project for coding agent tools that do not support it.
- Running this command would recurse through folders in a project, detecting any AGENTS.md that it finds, creating a symlink with a user-provided filename.
  - ❓Does this risk the possibility that an agent will read the same content twice? That would double up on context for a single file. Maybe it should just be an empty file that says "Follow AGENTS.md at this same folder level."


---

## Someday Perhaps

### `spelunk` expanded enumeration
- Add more sophisticated enumeration of artifacts. Detect all sorts of files associated with LLM dev-tool usage
  - AGENTS.md, certain json files, ..., etc.
- Ability to `spelunk` remote repositories?
  - Goes against design philosophy

### Artifact Security Scanning


### Marketplace /  Plugin Parsing
- A way to parse plugin / skill marketplace structures for artifacts
	- e.g.
		- claude marketplace format (https://code.claude.com/docs/en/plugin-marketplaces).
		- plugin format https://code.claude.com/docs/en/plugins
- Key Questions
	- What other formats are worth parsing?
	- Should a user be able define their own personal list of marketplace URLs/locations to facilitate browsing/search?
		- Given all the open source skill/artifact sharing going on, there is potential here, ***but it goes against the no-network design.***
		- This COULD just be a static list…
	- Package manager format for artifact management?

### TUI
- A TUI frontend.
- Still usable through an `ssh` connection
- Likely implemented with textual (if at all)

### Full-fledged version control of artifacts
- Could facilitate rolling back / testing particular versions of artifacts
- Key Questions
  - Would this be useful at all when most ppl would probably just use a git repo anyway?
