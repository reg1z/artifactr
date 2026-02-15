## 1. Custom help formatter

- [x] 1.1 Create `ArtHelpFormatter` class in `cli.py` subclassing `argparse.RawDescriptionHelpFormatter`, overriding `_format_action` to suppress subparser actions and `_format_usage` for a custom usage line
- [x] 1.2 Set the `art` parser to use `ArtHelpFormatter` as its `formatter_class`

## 2. Description and epilog

- [x] 2.1 Update the parser `description` to "Manage AI artifacts across multiple configurations, tools, & repositories." with a default-targeting note
- [x] 2.2 Write the categorized epilog string with Vault Operations, Namespaces, and Discovery sections
- [x] 2.3 Update `pyproject.toml` description to match the new base description

## 3. Subcommand help strings

- [x] 3.1 Audit all `add_parser()` calls and ensure every one has a descriptive `help=` string
- [x] 3.2 Update `art project` parser description to note current-directory default targeting

## 4. Verification

- [x] 4.1 Run `art --help` and verify output matches the categorized layout with no argparse auto-generated subparser list
- [x] 4.2 Run `art <subcommand> --help` for each subcommand and verify individual help still works correctly
