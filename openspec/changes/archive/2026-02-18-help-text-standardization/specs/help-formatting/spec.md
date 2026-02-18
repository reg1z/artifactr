## ADDED Requirements

### Requirement: Aliases section in per-command help
Every command that has leaf-level argparse aliases MUST display those aliases in its own `--help` output. The aliases MUST appear in the `description` block, on a line beginning with "Aliases:". Aliases are leaf-level only (the immediate aliases of that parser); parent namespace aliases are not repeated.

#### Scenario: Leaf alias shown in help
- **WHEN** `art vault ls --help` is run
- **THEN** the output MUST contain "Aliases: list"

#### Scenario: Multiple leaf aliases shown
- **WHEN** `art create skill --help` is run
- **THEN** the output MUST contain "Aliases: s, sk"

#### Scenario: No Aliases line when command has no aliases
- **WHEN** `art vault add --help` is run
- **THEN** the output MUST NOT contain a line starting with "Aliases:"

#### Scenario: Namespace alias shown in namespace help
- **WHEN** `art vault --help` is run
- **THEN** the output MUST contain "Aliases: v"

#### Scenario: Project namespace aliases shown
- **WHEN** `art project --help` is run
- **THEN** the output MUST contain "Aliases: proj, p"

### Requirement: Workflows section in relevant command help
Commands with natural sequential relationships to other commands SHOULD include a Workflows section in their `--help` epilog. The section header MUST be "Workflows:" and content MUST use "→" (U+2192) as the step separator.

#### Scenario: Workflows section format
- **WHEN** `art project import --help` is run
- **THEN** the epilog MUST contain "Workflows:" followed by a line containing "→"

#### Scenario: Workflows section absent when not applicable
- **WHEN** `art vault name --help` is run
- **THEN** the epilog MUST NOT contain "Workflows:"

### Requirement: See Also section in relevant command help
Commands with laterally related counterparts (similar purpose or complementary scope) MAY include a See Also section in their `--help` epilog. The section header MUST be "See Also:".

#### Scenario: See Also section format
- **WHEN** a command help includes a See Also section
- **THEN** the epilog MUST contain "See Also:" followed by indented command references with brief descriptions

### Requirement: Notes section in relevant command help
Commands with non-obvious behavior, caveats, or important defaults MAY include a Notes section in their `--help` epilog. The section header MUST be "Notes:". Notes MUST be 1–2 sentences.

#### Scenario: Notes section format
- **WHEN** a command help includes a Notes section
- **THEN** the epilog MUST contain "Notes:" followed by indented text

#### Scenario: Notes absent when nothing substantive to say
- **WHEN** `art vault select --help` is run
- **THEN** the output SHOULD NOT contain a Notes section (nothing non-obvious to document)

### Requirement: All leaf parsers have description paragraphs
Every leaf command's own `--help` output MUST include a description paragraph (populated via `make_help(summary=...)`). No leaf parser may have an empty or absent `description=`.

#### Scenario: vault add has description
- **WHEN** `art vault add --help` is run
- **THEN** a description paragraph MUST appear below the usage line

#### Scenario: vault init has description
- **WHEN** `art vault init --help` is run
- **THEN** a description paragraph MUST appear below the usage line

#### Scenario: vault select has description
- **WHEN** `art vault select --help` is run
- **THEN** a description paragraph MUST appear below the usage line

#### Scenario: vault rm has description
- **WHEN** `art vault rm --help` is run
- **THEN** a description paragraph MUST appear below the usage line

#### Scenario: vault name has description
- **WHEN** `art vault name --help` is run
- **THEN** a description paragraph MUST appear below the usage line

#### Scenario: tool add has description
- **WHEN** `art tool add --help` is run
- **THEN** a description paragraph MUST appear below the usage line

#### Scenario: tool info has description
- **WHEN** `art tool info --help` is run
- **THEN** a description paragraph MUST appear below the usage line

#### Scenario: tool rm has description
- **WHEN** `art tool rm --help` is run
- **THEN** a description paragraph MUST appear below the usage line

#### Scenario: tool select has description
- **WHEN** `art tool select --help` is run
- **THEN** a description paragraph MUST appear below the usage line

### Requirement: Alphabetical subcommand ordering within namespaces
Subcommands MUST be registered in alphabetical order within each namespace. The order of `add_parser()` calls determines display order in `--help` output.

#### Scenario: vault subcommands alphabetical
- **WHEN** `art vault --help` is run
- **THEN** subcommands MUST appear in the order: add, init, ls, name, rm, select

#### Scenario: tool subcommands alphabetical
- **WHEN** `art tool --help` is run
- **THEN** subcommands MUST appear in the order: add, info, ls, rm, select

#### Scenario: project subcommands alphabetical
- **WHEN** `art project --help` is run
- **THEN** subcommands MUST appear in the order: import, link, ls, rm, unlink, wipe

#### Scenario: config subcommands alphabetical
- **WHEN** `art config --help` is run
- **THEN** subcommands MUST appear in the order: edit, import, link, ls, rm, unlink, wipe

#### Scenario: create subcommands alphabetical
- **WHEN** `art create --help` is run
- **THEN** subcommands MUST appear in the order: agent, command, skill

### Requirement: show_help_on_error enabled on specific parsers
The following parsers MUST have `show_help_on_error=True`: namespace parsers (`vault`, `project`, `tool`, `config`, `create`) and leaf parsers (`edit`, `rm`, `vault add`, `vault init`, `vault rm`, `vault name`, `vault select`, `create skill`, `create command`, `create agent`).

#### Scenario: art edit no-args shows help then error
- **WHEN** `art edit` is run with no arguments
- **THEN** the full help text MUST be printed to stderr, followed by the argparse error

#### Scenario: art rm no-args shows help then error
- **WHEN** `art rm` is run with no arguments
- **THEN** the full help text MUST be printed to stderr, followed by the argparse error

#### Scenario: art vault add no-args shows help then error
- **WHEN** `art vault add` is run with no arguments
- **THEN** the full help text MUST be printed to stderr, followed by the argparse error

#### Scenario: art vault init no-args shows help then error
- **WHEN** `art vault init` is run with no arguments
- **THEN** the full help text MUST be printed to stderr, followed by the argparse error

#### Scenario: art create skill no-args shows help then error
- **WHEN** `art create skill` is run with no arguments
- **THEN** the full help text MUST be printed to stderr, followed by the argparse error

#### Scenario: Commands with show_help_on_error=False still show bare error
- **WHEN** `art vault ls --bad-flag` is run
- **THEN** only the standard argparse error line MUST appear (no full help dump)
