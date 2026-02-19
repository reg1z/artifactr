## ADDED Requirements

### Requirement: art nav target resolution
The `art nav` command MUST resolve a navigation target path from its positional argument.

#### Scenario: No argument — defaults to vault root
- **WHEN** `art nav` is run with no positional argument
- **THEN** the target path MUST be the root directory of the selected default vault

#### Scenario: Type alias argument — navigates to type subdir
- **WHEN** `art nav` is run with a positional argument that is a recognized type alias (`skills`, `s`, `sk`, `commands`, `c`, `cmd`, `com`, `agents`, `a`, `agt`)
- **THEN** the target path MUST be the corresponding subdirectory (`skills/`, `commands/`, or `agents/`) within the selected default vault

#### Scenario: Vault name argument — navigates to vault root
- **WHEN** `art nav` is run with a positional argument that is a registered vault name and is not a recognized type alias
- **THEN** the target path MUST be the root directory of that vault

#### Scenario: vault/type path argument — navigates to type subdir of named vault
- **WHEN** `art nav` is run with a positional argument in `<vault>/<type>` format (e.g., `vault-3/skills`, `vault-3/s`)
- **THEN** the target path MUST be the resolved type subdirectory within the named vault

#### Scenario: Unknown argument — error
- **WHEN** `art nav` is run with a positional argument that is neither a recognized type alias nor a registered vault name nor a valid vault/type path
- **THEN** an error MUST be printed to stderr and the command MUST exit with code 1

#### Scenario: Target directory does not exist
- **WHEN** the resolved target path does not exist as a directory
- **THEN** an error MUST be printed to stderr and the command MUST exit with code 1

### Requirement: art nav output modes
The `art nav` command MUST support multiple navigation output modes controlled by flags and the `nav_mode` config field.

#### Scenario: --print flag outputs path to stdout
- **WHEN** `art nav [target] --print` is run
- **THEN** the resolved path MUST be printed to stdout with no trailing newline beyond the path itself, and the command MUST exit with code 0
- **AND** this flag is the mechanism used by the shell wrapper function

#### Scenario: --spawn flag opens subshell in current terminal
- **WHEN** `art nav [target] --spawn` is run (alias: `-s`)
- **THEN** a new interactive shell MUST be launched as a subprocess with its working directory set to the resolved target path
- **AND** the shell used MUST be the value of `$SHELL` on Unix, `powershell.exe` on Windows if `$SHELL` is unset

#### Scenario: --window flag opens new terminal window
- **WHEN** `art nav [target] --window` is run (alias: `-w`)
- **THEN** a best-effort attempt MUST be made to open a new terminal window at the resolved target path
- **AND** the terminal emulator MUST be resolved in this order: `$TERMINAL` env var, then a platform-specific fallback list (Linux: xterm, gnome-terminal, konsole, alacritty, kitty; macOS: Terminal.app via `open -a Terminal`; Windows: `wt`, then `cmd.exe`)
- **AND** if no terminal emulator can be found, an error MUST be printed to stderr and the command MUST exit with code 1

#### Scenario: nav_mode config field — wrapper mode
- **WHEN** `nav_mode: wrapper` is set in `config.yaml` and `art nav` is run without mode flags
- **THEN** the command MUST behave as if `--print` was passed (outputs the path for shell function consumption)

#### Scenario: nav_mode config field — spawn mode
- **WHEN** `nav_mode: spawn` is set in `config.yaml` and `art nav` is run without mode flags
- **THEN** the command MUST behave as if `--spawn` was passed

#### Scenario: nav_mode config field — window mode
- **WHEN** `nav_mode: window` is set in `config.yaml` and `art nav` is run without mode flags
- **THEN** the command MUST behave as if `--window` was passed

#### Scenario: nav_mode config field — print mode
- **WHEN** `nav_mode: print` is set in `config.yaml` and `art nav` is run without mode flags
- **THEN** the resolved path MUST be printed to stdout

#### Scenario: Flag overrides nav_mode config
- **WHEN** `nav_mode` is set in `config.yaml` and a mode flag (`--spawn`, `-w`) is also passed
- **THEN** the flag MUST take precedence over the configured mode

#### Scenario: No mode configured — error with instructions
- **WHEN** `art nav` is run with no mode flag and no `nav_mode` in `config.yaml`
- **THEN** an informative error MUST be printed to stderr explaining the three available modes and how to configure one, and the command MUST exit with code 1

### Requirement: art nav vault name collision warning
The `art vault add` and `art vault init` commands MUST warn when a vault name conflicts with a reserved `art nav` type token.

#### Scenario: Vault named with a reserved type token
- **WHEN** `art vault add` or `art vault init` is run with `--name <name>` where `<name>` is a recognized type alias (`skills`, `s`, `sk`, `commands`, `c`, `cmd`, `com`, `agents`, `a`, `agt`)
- **THEN** a warning MUST be printed explaining that `art nav <name>` will resolve to the artifact type, not this vault
- **AND** the vault MUST still be created (the warning does not block the operation)

### Requirement: art shell setup installs shell wrapper
The `art shell setup` command MUST install the `art` shell wrapper function into the user's shell configuration.

#### Scenario: Detect shell and target rc file
- **WHEN** `art shell setup` is run
- **THEN** the running shell MUST be detected from `$SHELL` (Unix) or `$PSVersionTable` presence (PowerShell on Windows)
- **AND** the appropriate rc file MUST be identified: `~/.bashrc` (bash), `~/.zshrc` (zsh), `~/.profile` (sh), `~/.config/fish/functions/art.fish` (fish), `$PROFILE` (PowerShell)

#### Scenario: Snippet preview prompt
- **WHEN** `art shell setup` is run without `-y`/`--yes`
- **THEN** the user MUST be asked if they would like to preview the snippet before it is applied
- **AND** if the user selects yes, the full snippet MUST be printed to stdout
- **THEN** the user MUST be asked to confirm before the snippet is written

#### Scenario: Auto-approve with --yes
- **WHEN** `art shell setup --yes` is run (alias: `-y`)
- **THEN** all confirmation prompts MUST be skipped and the snippet MUST be written directly
- **AND** the target file and a summary of what was written MUST be printed to stdout

#### Scenario: Snippet appended, not overwritten
- **WHEN** the snippet is applied
- **THEN** it MUST be appended to the existing rc file content, not overwrite it
- **AND** a comment line identifying it as Artifactr shell integration MUST precede the function definition

#### Scenario: Post-install instruction
- **WHEN** the snippet is successfully written
- **THEN** the command MUST print a message instructing the user to `source` the rc file or start a new shell

#### Scenario: Fish shell — separate function file
- **WHEN** the detected shell is fish
- **THEN** the wrapper function MUST be written to `~/.config/fish/functions/art.fish` as a standalone file (not appended to `config.fish`)
- **AND** if `~/.config/fish/functions/art.fish` already exists, the user MUST be warned and asked to confirm overwrite
