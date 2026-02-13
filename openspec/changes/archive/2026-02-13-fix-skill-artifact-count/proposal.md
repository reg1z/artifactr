## Why

`art import` reports inflated artifact counts for skills. A skill directory containing 3 files is counted as 3 artifacts instead of 1. This makes the import summary misleading — users see `skills: 3` when they imported a single skill.

## What Changes

- Fix artifact counting in `import_artifacts` and `import_artifacts_global` so that each top-level item (file or directory) in a vault's artifact type directory counts as exactly 1 artifact, regardless of how many files it contains internally.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `importing`: The import result counts must reflect the number of logical artifacts imported, not the number of files copied. A skill directory is one artifact.

## Impact

- `src/artifactr/importer.py`: 4 locations where `artifact_count += result["copied"]` or equivalent needs to become a conditional `+= 1`
- Both `import_artifacts` (local) and `import_artifacts_global` (global) are affected, in both their full-import and selective-import code paths
