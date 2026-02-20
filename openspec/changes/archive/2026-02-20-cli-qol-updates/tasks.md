## 1. Version Bump

- [x] 1.1 Update `__version__` in `src/artifactr/__init__.py` from `0.3.1` to `0.3.2`
- [x] 1.2 Update `version` in `pyproject.toml` from `0.3.1` to `0.3.2`

## 2. Top-Level Parser Changes

- [x] 2.1 Add `-V` as a short alias for `--version` in the top-level parser (`create_parser()`, line ~302)
- [x] 2.2 Rename `"Vault Operations:\n"` to `"Artifact Operations:\n"` in the top-level parser epilog (`create_parser()`, line ~276)

## 3. art spelunk CWD Default

- [x] 3.1 In `handle_spelunk()`, replace `if target_str is None or global_spelunk:` with `if global_spelunk:`
- [x] 3.2 In the `else` branch, default `target` to `Path.cwd()` when `target_str is None`
- [x] 3.3 Ensure `original_target` is set to `Path.cwd()` (not left `None`) when no target is given
- [x] 3.4 Update the import-cache loading condition: fire when `not global_spelunk` (regardless of whether `target_str` is None)
- [x] 3.5 In `_compute_spelunk_location()`, simplify `if global_spelunk or original_target is None:` to `if global_spelunk:`
- [x] 3.6 Remove the `"No target specified — spelunking global config directories.\n"` print statement

## 4. art create Slash Syntax

- [x] 4.1 In `_main()`, change `args = parser.parse_args()` to use a local `argv = sys.argv[1:]` variable passed to `parse_args(argv)`
- [x] 4.2 Before calling `parse_args(argv)`, add argv pre-processing: if `argv[0] in ("create", "cr")` and `"/" in argv[1]`, split `argv[1]` on `/` and, if the type part is in `_TYPE_ALIASES` and the name part is non-empty, replace `argv[1]` with `[type_part, name_part]`

## 5. art nav Shell Wrapper --help Fix

- [x] 5.1 In `get_shell_wrapper_snippet()` for the **bash/sh/dash** variant: add a loop over `"${@:2}"` that checks for `--help` or `-h` and routes to `command art "$@"; return $?`
- [x] 5.2 Apply the same help-flag loop to the **zsh** variant
- [x] 5.3 Apply equivalent help-flag detection to the **fish** variant (using `for _arg in $argv[2..]`)
- [x] 5.4 Apply equivalent help-flag detection to the **PowerShell** variant (iterating `$args[1..($args.Length-1)]`)

## 6. Tests

- [x] 6.1 Update any existing spelunk tests that expect global-config results when no target is given — change them to use `-g`/`--global` or mock CWD
- [x] 6.2 Add tests for `art spelunk` (no args) targeting CWD
- [x] 6.3 Add tests for `art create skill/name`, `art create cmd/name`, `art create agt/name` slash syntax
- [x] 6.4 Add test for `art -V` printing the version string
