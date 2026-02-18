## 1. Infrastructure: ArtArgumentParser and make_help()

- [x] 1.1 Add `ArtArgumentParser` class to `cli.py`: subclasses `argparse.ArgumentParser`, accepts `show_help_on_error: bool = False`, overrides `error()` to print full help to stderr before calling `super().error()` when flag is `True`
- [x] 1.2 Add `make_help()` function to `cli.py`: accepts `summary`, `aliases`, `workflows`, `see_also`, `notes`; returns dict with `description`, `epilog`, and `formatter_class=argparse.RawDescriptionHelpFormatter`
- [x] 1.3 Update `create_parser()` root parser to use `ArtArgumentParser` instead of `argparse.ArgumentParser`
- [x] 1.4 Update all `add_subparsers()` calls to pass `parser_class=ArtArgumentParser`

## 2. Namespace Parsers: show_help_on_error + make_help()

- [x] 2.1 Update `vault` parser: set `show_help_on_error=True`, add `**make_help(summary=..., aliases=["v"])`
- [x] 2.2 Update `project` parser: set `show_help_on_error=True`, add `**make_help(summary=..., aliases=["proj", "p"])`
- [x] 2.3 Update `tool` parser: set `show_help_on_error=True`, add `**make_help(summary=..., aliases=["t"])`
- [x] 2.4 Update `config` parser: set `show_help_on_error=True`, add `**make_help(summary=..., aliases=["conf", "c"])`
- [x] 2.5 Update `create` parser: set `show_help_on_error=True`, add `**make_help(summary=..., aliases=["cr"])`
- [x] 2.6 Remove the `parser.parse_args(["namespace", "--help"])` fallback calls from `_main()` dispatch (now redundant — keep the `if cmd is None: parser.print_help(); return 0` pattern as-is)

## 3. Vault Subcommands: Alphabetical Order + make_help()

- [x] 3.1 Reorder vault subcommands alphabetically: `add`, `init`, `ls`, `name`, `rm`, `select`
- [x] 3.2 `vault add`: set `show_help_on_error=True`, add `**make_help(summary=..., notes="Paths must already exist on disk.")`
- [x] 3.3 `vault init`: set `show_help_on_error=True`, add `**make_help(summary=..., aliases=["create", "cr"], notes="Creates the directory if it does not exist.")`
- [x] 3.4 `vault ls`: add `**make_help(summary=..., aliases=["list"])`
- [x] 3.5 `vault name`: set `show_help_on_error=True`, add `**make_help(summary=...)`
- [x] 3.6 `vault rm`: set `show_help_on_error=True`, add `**make_help(summary=...)`
- [x] 3.7 `vault select`: set `show_help_on_error=True`, add `**make_help(summary=...)`

## 4. Tool Subcommands: Alphabetical Order + make_help()

- [x] 4.1 Reorder tool subcommands alphabetically: `add`, `info`, `ls`, `rm`, `select`
- [x] 4.2 `tool add`: add `**make_help(summary=...)`
- [x] 4.3 `tool info`: add `**make_help(summary=...)`
- [x] 4.4 `tool ls`: add `**make_help(summary=..., aliases=["list"])`
- [x] 4.5 `tool rm`: add `**make_help(summary=...)`
- [x] 4.6 `tool select`: add `**make_help(summary=...)`

## 5. Project Subcommands: Alphabetical Order + make_help()

- [x] 5.1 Reorder project subcommands alphabetically: `import`, `link`, `ls`, `rm`, `unlink`, `wipe`
- [x] 5.2 `project import`: add `**make_help(summary=..., workflows="art proj import → art proj link → art proj unlink", see_also=[("art config import", "Same operation targeting global tool config dirs")])`
- [x] 5.3 `project link`: add `**make_help(summary=..., aliases=["ln"], workflows="art proj import → art proj link → art proj unlink", see_also=[("art proj unlink", "Replace symlinks with copies")])`
- [x] 5.4 `project ls`: add `**make_help(summary=..., aliases=["list"])`
- [x] 5.5 `project rm`: add `**make_help(summary=...)`
- [x] 5.6 `project unlink`: add `**make_help(summary=..., aliases=["uln"], see_also=[("art proj link", "Convert copies to symlinks")])`
- [x] 5.7 `project wipe`: add `**make_help(summary=..., notes="Removes all imported artifacts and clears the import cache.")`

## 6. Config Subcommands: Alphabetical Order + make_help()

- [x] 6.1 Reorder config subcommands alphabetically: `edit`, `import`, `link`, `ls`, `rm`, `unlink`, `wipe`
- [x] 6.2 `config edit`: add `**make_help(summary=..., aliases=["ed"], see_also=[("art tool add", "Add a custom tool to the config")])`
- [x] 6.3 `config import`: add `**make_help(summary=..., see_also=[("art proj import", "Same operation targeting a project directory")])`
- [x] 6.4 `config link`: add `**make_help(summary=..., aliases=["ln"])`
- [x] 6.5 `config ls`: add `**make_help(summary=..., aliases=["list"])`
- [x] 6.6 `config rm`: add `**make_help(summary=...)`
- [x] 6.7 `config unlink`: add `**make_help(summary=..., aliases=["uln"])`
- [x] 6.8 `config wipe`: add `**make_help(summary=...)`

## 7. Create Subcommands: Alphabetical Order + make_help()

- [x] 7.1 Reorder create subcommands alphabetically: `agent`, `command`, `skill`
- [x] 7.2 `create agent`: set `show_help_on_error=True`, add `**make_help(summary=..., aliases=["a", "agt", "ag"])`
- [x] 7.3 `create command`: set `show_help_on_error=True`, add `**make_help(summary=..., aliases=["c", "cmd", "com"])`
- [x] 7.4 `create skill`: set `show_help_on_error=True`, add `**make_help(summary=..., aliases=["s", "sk"])`

## 8. Top-Level Leaf Commands: make_help()

- [x] 8.1 `ls` (top-level): add `**make_help(summary=..., aliases=["list"])`
- [x] 8.2 `rm` (top-level): set `show_help_on_error=True`, add `**make_help(summary=...)`
- [x] 8.3 `spelunk`: add `**make_help(summary=..., aliases=["sp"])`
- [x] 8.4 `store`: add `**make_help(summary=..., aliases=["st"])`
- [x] 8.5 `edit`: set `show_help_on_error=True`, add `**make_help(summary=..., aliases=["ed"])`

## 9. AGENTS.md Updates

- [x] 9.1 Add alias maintenance rule under Conventions: "When adding, changing, or removing command aliases, both the argparse `aliases=` and the `make_help(aliases=...)` call must be updated. The `--help` output is the user-facing source of truth for discoverability."
- [x] 9.2 Add `## Help Text Format` section documenting `make_help()` parameters: which are required/optional, their intent, and the rendered section names (Summary, Aliases, Workflows, See Also, Notes)

## 10. Tests

- [x] 10.1 Test `make_help()`: verify `description`, `epilog`, and `formatter_class` keys; verify alias line present/absent; verify each optional epilog section appears/absent correctly
- [x] 10.2 Test `ArtArgumentParser`: verify `show_help_on_error=False` default; verify error exits with code 2; verify `show_help_on_error=True` prints help to stderr before error
- [x] 10.3 Verify existing tests still pass; update any assertions on subcommand ordering that break due to alphabetical reorder
- [x] 10.4 Smoke-test rendered output: run `art <cmd> --help` for each modified command and verify Aliases/Workflows/See Also/Notes sections appear as expected
