## 1. Fix artifact counting in import_artifacts (local import)

- [x] 1.1 Fix full-import path: change `artifact_count += result["copied"]` to `artifact_count += 1 if result["copied"] > 0` (line ~397)
- [x] 1.2 Fix selective-import path: change `imported[tool_name][artifact_type] += result["copied"]` to `+= 1 if result["copied"] > 0` (line ~370-371)

## 2. Fix artifact counting in import_artifacts_global (global import)

- [x] 2.1 Fix full-import path: change `artifact_count += result["copied"]` to `artifact_count += 1 if result["copied"] > 0` (line ~630)
- [x] 2.2 Fix selective-import path: change `imported[tool_name][artifact_type] += result["copied"]` to `+= 1 if result["copied"] > 0` (line ~600-601)
