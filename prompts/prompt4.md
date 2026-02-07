spec name: v3_features_spec.md
plan name: v3_features_plan.md
- `art import` Add support for importing artifacts into a tool's user-wide global config directories
	- Uses a new flags: `--global` or `-g`
		- using this flag means that no target directory needs to be specified (this argument can be left empty). Instead it will target the default user-specific config dirs for each tool.
	- claude-code (reference https://code.claude.com/docs/en/settings)
		- skills → ~/.claude/skills
		- agents → ~/.claude/agents
		- commands → ~/.claude/commands
	- opencode
		- skills → ~/.config/opencode/skills
		- agents → ~/.config/opencode/agents
		- commands → ~/.config/opencode/commands
- `art import` add the `--force` / `-f` flags
	- Running the command with the force flag will import the specified artifacts overwriting any pre-existing artifacts of the same name in the target directories. The user confirmation for each file will be skipped.
