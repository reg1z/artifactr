## Context

`copy_with_prompt` returns `{"copied": N, "skipped": M}` where N is the number of **files** copied. When importing a skill directory containing multiple files, N equals the file count, not 1. The import logic uses this file count as the artifact count, inflating the reported number.

Four code paths are affected — the full-import and selective-import paths in both `import_artifacts` (local) and `import_artifacts_global` (global).

## Goals / Non-Goals

**Goals:**
- Each top-level vault item (skill directory, agent file, command file) counts as exactly 1 artifact in import results
- Fix all four affected code paths consistently

**Non-Goals:**
- Changing `copy_with_prompt` return values (file-level counts are still useful for its contract)
- Changing the import cache tracking (already tracks by artifact name, not file count)
- Adding tests (out of scope for this change)

## Decisions

**Decision: Increment artifact count conditionally at the call site**

At each of the 4 locations where `artifact_count` (or equivalent) is accumulated, change from adding `result["copied"]` to adding `1` when `result["copied"] > 0`.

Alternative considered: Modifying `copy_with_prompt` to return a separate "logical item" count. Rejected because the function's contract is about files, and callers may want file-level granularity. The fix belongs at the import-level counting logic, not the copy utility.

## Risks / Trade-offs

- [Minimal risk] The change is mechanical — 4 nearly identical edits. No behavioral change beyond the count reporting.
