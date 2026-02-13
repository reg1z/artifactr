## REMOVED Requirements

### Requirement: Import command
**Reason**: The top-level `art import` command is removed. Project-side import is now `art proj import` (see `project-commands` spec). Global config import is now `art conf import` (see `config-commands` spec).
**Migration**: Use `art proj import [target]` for project imports, `art conf import` for global config imports.
