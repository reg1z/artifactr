## Purpose

Defines how link state (linked/copied/hardlinked) is displayed in import summaries and list outputs.

## Requirements

### Requirement: Import summary shows link state
`print_import_summary()` MUST indicate the link mode when artifacts are imported with `--link`.

#### Scenario: Import with link mode
- **WHEN** artifacts are imported with `--link`
- **THEN** each non-zero artifact type line MUST display `(linked)` suffix, e.g., `skills: 3 (linked)`

#### Scenario: Import without link mode
- **WHEN** artifacts are imported without `--link`
- **THEN** each non-zero artifact type line MUST display `(copied)` suffix, e.g., `skills: 3 (copied)`

#### Scenario: Total line includes link state
- **WHEN** the import summary total is printed
- **THEN** it MUST include the link state, e.g., `Total: 5 artifact(s) imported (linked)`

### Requirement: List output shows link state column
`art proj ls` and `art conf ls` MUST display a STATE column showing the link state of each artifact.

#### Scenario: Linked artifact display
- **WHEN** a listed artifact has `:linked` state in the cache
- **THEN** the NAME column MUST show a `→` arrow indicator and the STATE column MUST show `linked`

#### Scenario: Copied artifact display
- **WHEN** a listed artifact has `:copied` state or no suffix in the cache
- **THEN** the NAME column MUST have no arrow indicator and the STATE column MUST show `copied`

#### Scenario: Hardlinked artifact display
- **WHEN** a listed artifact has `:win_hardlinked` state in the cache
- **THEN** the NAME column MUST show a `⇒` arrow indicator and the STATE column MUST show `hardlinked`

#### Scenario: Column headers
- **WHEN** `art proj ls` or `art conf ls` output is displayed
- **THEN** the columns MUST be NAME, TYPE, TOOL, VAULT, STATE

### Requirement: Cache parser preserves link state
`_load_cache_entries()` and `_load_global_cache_entries()` MUST return link state in each entry.

#### Scenario: Entry with linked suffix
- **WHEN** a cache entry has `:linked` suffix
- **THEN** the parsed entry MUST include `link_state: "linked"`

#### Scenario: Entry with copied suffix
- **WHEN** a cache entry has `:copied` suffix
- **THEN** the parsed entry MUST include `link_state: "copied"`

#### Scenario: Entry with win_hardlinked suffix
- **WHEN** a cache entry has `:win_hardlinked` suffix
- **THEN** the parsed entry MUST include `link_state: "win_hardlinked"`

#### Scenario: Legacy entry without suffix
- **WHEN** a cache entry has no `:` suffix
- **THEN** the parsed entry MUST include `link_state: "copied"` (default)
