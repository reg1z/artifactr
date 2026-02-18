## ADDED Requirements

### Requirement: make_help() helper function
A `make_help()` function MUST exist in `cli.py` that returns a dict of kwargs suitable for unpacking into `add_parser()`. It MUST accept the following parameters: `summary: str`, `aliases: list[str] | None = None`, `workflows: str | None = None`, `see_also: list[tuple[str, str]] | None = None`, `notes: str | None = None`.

#### Scenario: Returns required keys
- **WHEN** `make_help(summary="Does a thing.")` is called
- **THEN** the returned dict MUST contain keys `description`, `epilog`, and `formatter_class`

#### Scenario: formatter_class is RawDescriptionHelpFormatter
- **WHEN** `make_help(summary="Does a thing.")` is called
- **THEN** `formatter_class` MUST be `argparse.RawDescriptionHelpFormatter`

#### Scenario: Summary appears in description
- **WHEN** `make_help(summary="Does a thing.")` is called
- **THEN** `description` MUST begin with "Does a thing."

#### Scenario: Aliases appear in description when provided
- **WHEN** `make_help(summary="Does a thing.", aliases=["x", "y"])` is called
- **THEN** `description` MUST contain "Aliases: x, y"

#### Scenario: No Aliases line when aliases is None
- **WHEN** `make_help(summary="Does a thing.", aliases=None)` is called
- **THEN** `description` MUST NOT contain the word "Aliases"

#### Scenario: Workflows section appears in epilog when provided
- **WHEN** `make_help(summary="Does a thing.", workflows="art proj import → art proj link")` is called
- **THEN** `epilog` MUST contain "Workflows:" and "art proj import → art proj link"

#### Scenario: See Also section appears in epilog when provided
- **WHEN** `make_help(summary="Does a thing.", see_also=[("art vault init", "Initialize a new vault")])` is called
- **THEN** `epilog` MUST contain "See Also:" and "art vault init"

#### Scenario: Notes section appears in epilog when provided
- **WHEN** `make_help(summary="Does a thing.", notes="Targets the default vault.")` is called
- **THEN** `epilog` MUST contain "Notes:" and "Targets the default vault."

#### Scenario: Epilog is None when all optional sections are absent
- **WHEN** `make_help(summary="Does a thing.")` is called with no optional kwargs
- **THEN** `epilog` MUST be `None`

#### Scenario: Epilog sections are separated by blank lines
- **WHEN** `make_help()` is called with both `workflows` and `notes` provided
- **THEN** `epilog` MUST contain a blank line between the Workflows and Notes sections

### Requirement: ArtArgumentParser class
An `ArtArgumentParser` class MUST exist in `cli.py` that subclasses `argparse.ArgumentParser`. It MUST accept a `show_help_on_error: bool = False` keyword argument and store it as an instance attribute.

#### Scenario: Class is instantiable
- **WHEN** `ArtArgumentParser()` is called with no arguments
- **THEN** it MUST behave identically to `argparse.ArgumentParser()` with no arguments

#### Scenario: show_help_on_error defaults to False
- **WHEN** `ArtArgumentParser()` is instantiated without specifying `show_help_on_error`
- **THEN** `parser.show_help_on_error` MUST be `False`

#### Scenario: show_help_on_error can be set to True
- **WHEN** `ArtArgumentParser(show_help_on_error=True)` is instantiated
- **THEN** `parser.show_help_on_error` MUST be `True`

### Requirement: ArtArgumentParser error behavior with show_help_on_error=False
When `show_help_on_error` is `False`, `error()` MUST behave identically to `argparse.ArgumentParser.error()`.

#### Scenario: Error exits with code 2
- **WHEN** an `ArtArgumentParser(show_help_on_error=False)` parser encounters a required missing argument
- **THEN** the process MUST exit with code 2

#### Scenario: No help text printed to stderr when False
- **WHEN** an `ArtArgumentParser(show_help_on_error=False)` parser raises an error
- **THEN** the parser's full help text MUST NOT be printed to stderr

### Requirement: ArtArgumentParser error behavior with show_help_on_error=True
When `show_help_on_error` is `True`, `error()` MUST print the full help text to stderr before the standard argparse error line.

#### Scenario: Help text printed to stderr before error
- **WHEN** an `ArtArgumentParser(show_help_on_error=True)` parser encounters a required missing argument
- **THEN** the full help text MUST be written to stderr, followed by the error message

#### Scenario: Still exits with code 2
- **WHEN** an `ArtArgumentParser(show_help_on_error=True)` parser raises an error
- **THEN** the process MUST still exit with code 2

### Requirement: ArtArgumentParser used for all parsers
`create_parser()` MUST use `ArtArgumentParser` for the root parser, and MUST pass `parser_class=ArtArgumentParser` to all `add_subparsers()` calls so that all subparsers are instances of `ArtArgumentParser`.

#### Scenario: Root parser is ArtArgumentParser
- **WHEN** `create_parser()` is called
- **THEN** the returned object MUST be an instance of `ArtArgumentParser`

#### Scenario: Subparsers are ArtArgumentParser
- **WHEN** any subparser is created via `add_parser()` within `create_parser()`
- **THEN** that subparser MUST be an instance of `ArtArgumentParser`
