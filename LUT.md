# Artifactr Lookup Table

| Spec | Code | Purpose |
| ---- | ---- | ------- |
| specs/artifactr_spec.md §1 | src/artifactr/utils.py | Cross-platform config directory paths (Linux/macOS/Windows) |
| specs/artifactr_spec.md §2 | src/artifactr/config.py | Configuration storage (load/save config.yaml) |
| specs/artifactr_spec.md §3 | src/artifactr/tools/base.py | Vault structure and artifact types (skills/agents/commands) |
| specs/artifactr_spec.md §4 | src/artifactr/tools/ | Tool adapter pattern (base class + implementations) |
| specs/artifactr_spec.md §5.2 | src/artifactr/tools/claude_code.py | Claude Code import destinations (.claude/) |
| specs/artifactr_spec.md §5.3 | src/artifactr/tools/opencode.py | OpenCode import destinations (.opencode/) |
| specs/artifactr_spec.md §6 | src/artifactr/cli.py | CLI interface using argparse |
| specs/artifactr_spec.md §7.1 | src/artifactr/importer.py | `art import` command logic |
| specs/artifactr_spec.md §7.2-7.5 | src/artifactr/catalog.py | Vault management (add/rm/select/list) |
| specs/artifactr_spec.md §7.1.8 | src/artifactr/importer.py:18-52 | Git exclude file management |
