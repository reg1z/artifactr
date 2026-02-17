## ADDED Requirements

### Requirement: Yes flag for auto-confirmation
Commands that display interactive Y/n confirmation prompts MUST accept `--yes`/`-y` to automatically answer "yes" to all such prompts.

#### Scenario: Flag suppresses confirmation
- **WHEN** a command with `--yes` encounters a Y/n confirmation prompt
- **THEN** the prompt MUST be skipped and the "yes" path MUST be taken automatically

#### Scenario: Flag does not affect non-confirmation prompts
- **WHEN** a command with `--yes` encounters a multi-choice or freeform prompt
- **THEN** the prompt MUST still be displayed (the flag only affects Y/n confirmations)

#### Scenario: Short flag
- **WHEN** `-y` is passed to a command that supports `--yes`
- **THEN** it MUST behave identically to `--yes`
