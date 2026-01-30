Please implement
- Rather than having the program import artifacts into ALL supported tool directories by default, have the user select a specific tool. It should be like selecting a default vault, but with the user's desired tool. Make the program default opencode. This is ran with `art tool select <tool>`
- Add the `--link` / `-l` flag to the art import command. This flag will symlink vault contents rather than copying them into the target repo.
