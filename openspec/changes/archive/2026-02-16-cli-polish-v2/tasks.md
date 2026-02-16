## 1. Command Aliases

- [x] 1.1 Add `aliases=["sp"]` to spelunk parser in `create_parser()`
- [x] 1.2 Add `aliases=["st"]` to store parser in `create_parser()`
- [x] 1.3 Add `aliases=["cr"]` to create parser in `create_parser()`
- [x] 1.4 Add `aliases=["ed"]` to top-level edit parser in `create_parser()`
- [x] 1.5 Add `aliases=["ed"]` to config edit subparser in `create_parser()`
- [x] 1.6 Expand edit `artifact_type` choices to include `"s"`, `"c"`, `"a"` and add normalization logic in `handle_edit()` to map short forms to full names
- [x] 1.7 Update `main()` dispatch to recognize `"sp"`, `"st"`, `"cr"`, `"ed"` aliases in the command routing conditionals

## 2. Store Force Flag

- [x] 2.1 Add `-f`/`--force` argument to the store parser in `create_parser()`
- [x] 2.2 Update `handle_store()` to pass `force=True` to `copy_with_prompt()` when `--force` is set

## 3. Orphaned Import Detection

- [x] 3.1 Add a helper function `check_import_health(artifact_name, artifact_type, vault_name, config)` that returns `None`, `"source missing"`, or `"vault not found"`
- [x] 3.2 Update the spelunk display loop in `handle_spelunk()` to call the helper and append the status to the `(imported: ...)` indicator

## 4. KeyboardInterrupt Handling

- [x] 4.1 Wrap the `main()` call in `__main__.py` with `try/except KeyboardInterrupt` that prints a newline and exits with code 130

## 5. Help Text

- [x] 5.1 Update the `art --help` epilog to show new aliases: `store (st)`, `edit (ed)`, `create (cr)`, `spelunk (sp)`
- [x] 5.2 Update the `config` entry in the epilog Namespaces section to mention tool-specific global configs and artifactr's own configuration
- [x] 5.3 Add `description=` to vault parser with brief explanation of vault management
- [x] 5.4 Add `description=` to tool parser with brief explanation of tool management
- [x] 5.5 Add `description=` to project parser (update existing description to be more descriptive)
- [x] 5.6 Add `description=` to config parser with explanation covering tool-specific global configs and artifactr's own config
- [x] 5.7 Add `description=` to ls parser with brief explanation
- [x] 5.8 Add `description=` to rm parser with brief explanation
- [x] 5.9 Add `description=` to store parser with brief explanation
- [x] 5.10 Add `description=` to edit parser with brief explanation
- [x] 5.11 Add `description=` to create parser with brief explanation
- [x] 5.12 Add `description=` to spelunk parser with brief explanation
- [x] 5.13 Update `config edit` subparser help text to clarify it opens artifactr's own global YAML config
- [x] 5.14 Update `config import` subparser help text to clarify it imports into tool-specific global config directories

## 6. Tests

- [x] 6.1 Add tests for all new command aliases (sp, st, cr, ed, edit s/c/a)
- [x] 6.2 Add test for `art store --force` passing force=True to copy_with_prompt
- [x] 6.3 Add tests for orphaned import detection (source missing, vault not found, healthy)
- [x] 6.4 Add test for KeyboardInterrupt producing clean exit with code 130
