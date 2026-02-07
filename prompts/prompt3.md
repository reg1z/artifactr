# Artifactr new changes
- new flags for `art vault list`
	- `-a` / `--all` → this will list the full vault hierarchy: individual vaults at the top level, then individual tools, and the artifacts within. If an artifact is itself a folder (e.g. in the case of a skill), the contents of the artifact folder will not be shown. The filename/directory name of the tool folders and artifacts will be used in this display.
- new flag for `art import`
	- `--artifacts` → should now be able to import individual artifacts with this flag. one should be able to specify multiple artifacts with a comma separated list as well. e.g. `art import ~/repos/my-project --artifacts=helping-hand,utility-tool,code-review
	- This should work fine for unique names, however, if there are artifacts of different types that have the same name, the user should be able to specify which one to use with a prefix like this: `art import ~/repos/my-project --artifacts=skills/write-thing,commands/write-that`
		- If a duplicate is detected and a user has not specified a prefix, the program should notify the user and prompt them for the specific skill they'd like to import
	- The flag should play well with existing flags (`--vault`, `--tools`, `--link`)
- `art import` update:
	- creates / updates a folder within the target directory called `.art-cache`. This folder is also added to the `.git/info/exclude` file along with all other imported artifacts. The `.art-cache` folder is for keeping track of project-specific imports. Within this folder will be the `imported` file. Each line in this file will represent an individual artifact that has been imported into the target directory – each artifact will have the vault name it was imported from AND the tool it was imported for as a prefix. When a skill is imported into more than 1 tool, duplicate lines should be made that correspond to each tool used. See the example below for the proper format.

example `.art-cache/imported`:
```
favs.claude-code.helping-hand
vault1.claude-code.utility-tool
vault1.opencode.utility-tool
```

- new commands
	- `art spelunk <target>` → this will probe the target directory (most likely a git repo, but no need to check for this) for artifacts and list any individual artifacts that it finds. This command will only probe the directories of tools that artifactr supports (currently claude-code and opencode, and so it will only search within the .claude and .opencode folders currently).
		- Each row of output should contain the following (in this order):
			- The artifact name
			- The type of artifact that was discovered (i.e. skill, command, etc.)
			- The full filepath of the artifact
			- This command will check the names of discovered skills against previous imports listed in the `.art-cache/imported` file. If matches are found, the output should make it clear that a discovered artifact is likely a previous import from another vault.
			- If the main artifact file (e.g. `skill-name/SKILL.md)`) contains yaml frontmatter with a non-empty "description" property, then list that description after the name of the artifact.
	- `art store <target_dir>` → For use in tandem with `art spelunk`. This command can be used to store individual artifacts discovered in a target dir. For the operation to succeed, the artifacts being stored MUST be within the default configuration folder of a supported tool (currently .claude and .opencode), otherwise it will fail.
