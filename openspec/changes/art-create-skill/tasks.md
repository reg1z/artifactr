## 1. Dependencies and Project Setup

- [ ] 1.1 Add `textual>=0.50` to `pyproject.toml` dependencies
- [ ] 1.2 Create empty module files: `src/artifactr/creator.py`, `src/artifactr/tui.py`, `src/artifactr/known_fields.py`

## 2. Known Fields Registry

- [ ] 2.1 Implement `known_fields.py` with dataclass/dict entries for Claude Code fields: `argument-hint`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `model`, `context`, `agent` — each with name, description, field_type, supported_by, default, and options where applicable

## 3. Creator Business Logic

- [ ] 3.1 Implement `create_skill()` in `creator.py` — accepts name, description, content, extra fields dict, target path; generates YAML frontmatter and writes `<target>/skills/<name>/SKILL.md`
- [ ] 3.2 Implement vault target resolution — resolve vault path from `--vault` flag or default vault, error if not found
- [ ] 3.3 Implement project-local target resolution — resolve tool config directories via tool adapters when `--here` is used, supporting `--tools` for multi-tool output
- [ ] 3.4 Implement overwrite protection — check if skill directory already exists, error with message if so

## 4. CLI Integration

- [ ] 4.1 Add `create` subcommand to argparse in `cli.py` with `skill` sub-subcommand and all flags: positional `name`, `-n/--name`, `-d/--description`, `-c/--content`, `-D/--field` (append), `-H/--here`, `--vault`, `--tools`
- [ ] 4.2 Implement `handle_create_skill()` in `cli.py` — mode detection (content flags → non-interactive, otherwise → TUI), vault/project resolution, delegation to creator or TUI
- [ ] 4.3 Wire `handle_create_skill()` into the `main()` dispatch

## 5. Textual TUI

- [ ] 5.1 Implement base TUI app in `tui.py` with Textual `App` — form layout with Name input (pre-populated), Description input, Content textarea, Cancel/Create buttons
- [ ] 5.2 Implement "Add Field" button and modal picker — custom field name input at top, known fields list below with descriptions and tool compatibility info
- [ ] 5.3 Implement known field rendering — add appropriate widgets when a known field is selected (text input, checkbox/switch for booleans, select dropdown for enums like `context`)
- [ ] 5.4 Implement tooltips for known fields — tooltip icon next to each known field on the form showing description and "Supported by: <tools>" info
- [ ] 5.5 Implement field removal — remove affordance next to added fields, returns field to available list in picker
- [ ] 5.6 Implement form validation — require description before enabling Create button
- [ ] 5.7 Wire TUI output to `create_skill()` — on Create, collect all form values and call creator business logic

## 6. Testing

- [ ] 6.1 Add tests for `creator.py` — skill scaffolding, vault targeting, project-local targeting, overwrite protection
- [ ] 6.2 Add tests for CLI argument parsing — all flags, mode detection, error cases
- [ ] 6.3 Add tests for `known_fields.py` — registry structure validation, required fields present
