## ADDED Requirements

### Requirement: Type filter argument helper
A shared helper function `add_type_filter_args(parser, allow_names=True)` MUST add type filter flags to any argparse subparser.

#### Scenario: Adding type filter flags with names allowed
- **WHEN** `add_type_filter_args(parser, allow_names=True)` is called
- **THEN** the parser MUST accept `-S`/`--skills`, `-C`/`--commands`, and `-A`/`--agents` flags, each with `nargs='?'`, `const=True`, `default=None`

#### Scenario: Adding type filter flags without names
- **WHEN** `add_type_filter_args(parser, allow_names=False)` is called
- **THEN** the parser MUST accept `-S`/`--skills`, `-C`/`--commands`, and `-A`/`--agents` flags, each with `action="store_true"`

### Requirement: Type filter resolution helper
A shared helper function `resolve_type_filters(args)` MUST interpret parsed type filter arguments into a structured result.

#### Scenario: No type filters specified
- **WHEN** none of `-S`, `-C`, `-A` are provided
- **THEN** `resolve_type_filters(args)` MUST return `None`, indicating all types are included

#### Scenario: Boolean type filter (flag without value)
- **WHEN** `-S` is provided without a value
- **THEN** the result MUST include `{"skills": True}`, indicating all skills are included

#### Scenario: Named type filter (flag with comma-separated value)
- **WHEN** `-S foo,bar` is provided
- **THEN** the result MUST include `{"skills": ["foo", "bar"]}`, indicating only the named skills are included

#### Scenario: Multiple type filters combined
- **WHEN** `-S -C` are both provided
- **THEN** the result MUST include both `"skills"` and `"commands"` keys, and `"agents"` MUST be excluded

#### Scenario: store_true type filter
- **WHEN** `-S` is provided on a parser configured with `allow_names=False`
- **THEN** the result MUST include `{"skills": True}` and exclude types whose flags were not set

### Requirement: Type filter respects tool support
Commands using type filters MUST skip artifact types that the active tool does not support, even when the corresponding type flag is set.

#### Scenario: Type flag for unsupported type
- **WHEN** `-A` (agents) is specified and the active tool does not support agents
- **THEN** agents MUST be silently skipped; no error MUST be raised
