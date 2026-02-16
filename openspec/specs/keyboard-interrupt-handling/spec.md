### Requirement: Global KeyboardInterrupt handling
The program entry point SHALL catch `KeyboardInterrupt` and exit cleanly with exit code 130.

#### Scenario: Ctrl-C during any operation
- **WHEN** the user presses Ctrl-C at any point during program execution
- **THEN** the program SHALL print a newline and exit with code 130
- **AND** no traceback SHALL be displayed

#### Scenario: Exit code convention
- **WHEN** the program exits due to KeyboardInterrupt
- **THEN** the exit code SHALL be 130 (Unix convention: 128 + SIGINT signal 2)
