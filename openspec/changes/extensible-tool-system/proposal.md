## Why

The tool system is hardcoded — adding a new AI coding agent requires writing a Python adapter class and modifying the registry. Users cannot add support for their own tools, and every tool implicitly supports all artifact types (skills, commands, agents) even when it doesn't. OpenAI Codex, for example, only supports skills — there's no way to express that today. An extensible, config-driven tool system lets users add tools themselves, supports partial artifact coverage, and makes built-in tools just data rather than code.

## What Changes

- **Replace per-tool Python adapter classes with a unified `GenericToolAdapter`** that reads tool definitions from config. `ClaudeCodeAdapter` and `OpenCodeAdapter` are removed. **BREAKING** for any code importing these classes directly.
- **Introduce per-artifact-type path configuration** — each tool defines separate repo-local and global paths for skills, commands, and agents independently. Omitted keys mean the tool doesn't support that artifact type.
- **Add tool definition sources with precedence**: built-in defaults (Python dict) < user global config (`~/.config/artifactr/config.yaml`) < vault config (`<vault>/vault.yaml`). Higher precedence overrides lower.
- **Add `vault.yaml` metadata file** to vaults — stores vault name and vault-scoped tool definitions. Backwards-compatible (optional file).
- **Ship OpenAI Codex as a built-in default** (skills-only: `.agents/skills` repo-local, `$HOME/.agents/skills` global).
- **New CLI commands**: `art tool add`, `art tool rm`, `art tool show` for managing custom tool definitions.
- **Enhance `art tool list`** to display artifact support matrix, source, and aliases per tool.

## Capabilities

### New Capabilities
- `custom-tools`: User-defined tool registration via `art tool add` with per-artifact-type path configuration, stored in global config or vault metadata. Includes `art tool rm` and `art tool show`.
- `vault-metadata`: Introduction of `vault.yaml` at vault root for portable vault name and vault-scoped tool definitions.
- `partial-artifact-support`: Tools can support a subset of artifact types. Omitted path keys signal unsupported types. Import, create, spelunk, and store operations respect this.

### Modified Capabilities
- `tool-aliases`: Aliases now come from tool definition config (both built-in and user-defined) rather than a separate hardcoded dict.
- `cli`: New subcommands under `art tool` (`add`, `rm`, `show`). Enhanced output for `art tool list`.
- `importing`: Must check tool's supported artifact types before importing; skip unsupported types.
- `discovery`: When discovering/storing for a specific tool, only scan supported artifact types.
- `creation`: Warn or error when creating an artifact type the selected tool doesn't support.

## Impact

- **Code**: `tools/base.py` (new `GenericToolAdapter`, remove `ToolAdapter` ABC or repurpose), `tools/__init__.py` (config-driven registry replacing hardcoded), `tools/claude_code.py` and `tools/opencode.py` (removed), `cli.py` (new subcommands, enhanced list), `importer.py` (partial support checks), `scanner.py` (partial support checks), `creator.py` (validation), `config.py` (load/save tool definitions + vault.yaml).
- **Config**: New `tools:` section in `config.yaml`. New `vault.yaml` file format.
- **Dependencies**: No new dependencies (PyYAML already used for config).
- **Backwards compatibility**: Existing vaults without `vault.yaml` continue working. Existing `config.yaml` without `tools:` section works (built-in defaults apply). Tool alias behavior preserved.
