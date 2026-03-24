---
phase: "02-data-pipeline"
plan: "05"
subsystem: "backend/data-pipeline"
tags: ["file-upload", "frequency-resolution", "data-pipeline", "cleaning", "pandas"]
dependency_graph:
  requires: ["02-01", "02-03"]
  provides: ["file_parser.parse_uploaded_file", "frequency_resolver.detect_frequencies", "frequency_resolver.check_frequency_conflict", "frequency_resolver.apply_resolution", "data_pipeline.clean_and_merge"]
  affects: ["backend/app/services/", "backend/tests/"]
tech_stack:
  added: ["pandas==3.0.1", "openpyxl>=3.1.0", "fredapi==0.5.2", "yfinance==1.2.0", "anthropic>=0.86.0"]
  patterns: ["TDD RED/GREEN", "pandas CoW explicit .copy()", "IQR outlier detection with Z-score fallback", "ffill/interpolate/drop missing value strategy"]
key_files:
  created:
    - backend/app/services/file_parser.py
    - backend/app/services/frequency_resolver.py
    - backend/app/services/data_pipeline.py
    - backend/app/schemas/data.py
    - backend/tests/test_file_parser.py
    - backend/tests/test_frequency_resolver.py
    - backend/tests/test_data_pipeline.py
    - backend/tests/fixtures/sample.csv
    - backend/tests/fixtures/malformed.csv
    - backend/tests/fixtures/sample.json
    - backend/tests/fixtures/sample.xlsx
  modified:
    - backend/pyproject.toml
decisions:
  - "Z-score fallback added to outlier detection when IQR=0 — handles constant-value baselines with extreme outliers that standard IQR cannot detect"
  - "infer_datetime_format removed from pd.to_datetime call — deprecated in pandas 3.x; inference happens automatically"
  - "select_dtypes uses include=['object','string'] instead of include='object' — avoids pandas 4.x deprecation warning about string dtype inclusion"
metrics:
  duration_seconds: 401
  completed_date: "2026-03-23"
  tasks_completed: 2
  files_created: 11
  files_modified: 1
---

# Phase 02 Plan 05: Data Pipeline Services Summary

**One-liner:** File parsing (CSV/Excel/JSON with auto-fix), frequency mismatch detection and resampling, and full data cleaning pipeline (timezone/missing/outlier/merge) using pandas 3.0 CoW patterns.

## What Was Built

### Task 1: file_parser.py and frequency_resolver.py

**`backend/app/services/file_parser.py`** — `parse_uploaded_file(content, filename) -> dict`

- Detects format by extension: `.csv` -> `pd.read_csv`, `.xlsx`/`.xls` -> `pd.read_excel(engine="openpyxl")`, `.json` -> `pd.read_json`
- Auto-fix step 1: drops fully empty rows, records count in changes
- Auto-fix step 2: coerces object columns to numeric where >80% of values convert (sentinel values like "N/A", "---" become NaN)
- Auto-fix step 3: coerces remaining object columns to datetime where >80% convert
- Column type detection: "numeric", "date", "text" (>10 unique), "category" (<=10 unique)
- Auto-assigns `role="date_index"` when exactly one date column exists
- Returns: preview (first 10 rows), columns (info list), changes (auto-fix report), total_rows, dataframe

**`backend/app/services/frequency_resolver.py`** — 3 functions:

- `detect_frequencies(dataframes)`: uses `pd.infer_freq` per series, returns "irregular" for non-DatetimeIndex
- `check_frequency_conflict(dataframes)`: ranks frequencies by granularity, selects lowest-frequency series as target, recommends mean aggregation
- `apply_resolution(df, target_freq, method)`: supports mean/last/sum (resample+agg) and ffill (asfreq+ffill); explicit `.copy()` per pandas 3.0 CoW

### Task 2: data_pipeline.py

**`backend/app/services/data_pipeline.py`** — `clean_and_merge(dataframes, metadata, mode) -> dict`

Six-step pipeline:

1. **Timezone normalization**: `tz_localize("UTC")` for naive, `tz_convert("UTC")` for tz-aware non-UTC
2. **Missing value handling**: ffill if <5% missing, linear interpolate if 5-20%, drop rows if >20%
3. **Unit normalization**: documents unit hints from metadata (billions, percentage, index) in assumptions
4. **Outlier detection**: 3-IQR bounds; Z-score fallback when IQR=0; flags but never removes
5. **Merge**: `pd.concat(axis=1, join="inner")` on DatetimeIndex
6. **Preview**: first 50 rows as records, column stats (min/max/mean/missing_count), total_rows

Returns: merged_df, preview_rows, column_stats, assumptions (all transformations), total_rows, outlier_flags

## Test Results

16 tests pass across 3 test files:

- `test_file_parser.py`: 5 tests (CSV/Excel/JSON type detection, malformed CSV auto-fix, unsupported extension error)
- `test_frequency_resolver.py`: 6 tests (daily vs quarterly conflict, no-conflict same-freq, mean aggregation, ffill upsampling, unknown method error)
- `test_data_pipeline.py`: 5 tests (missing value handling, timezone alignment, unit normalization, outlier detection, quick mode assumptions)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `infer_datetime_format` removed from pd.to_datetime call**
- **Found during:** Task 1 GREEN phase
- **Issue:** `pd.to_datetime(..., infer_datetime_format=True)` raises `TypeError` in pandas 3.x — the parameter was deprecated and removed
- **Fix:** Removed the argument; datetime inference is automatic in pandas 3.x
- **Files modified:** `backend/app/services/file_parser.py`
- **Commit:** ac33544

**2. [Rule 2 - Missing critical functionality] Z-score fallback for outlier detection when IQR=0**
- **Found during:** Task 2 GREEN phase (test_outlier_detection failed)
- **Issue:** When baseline values are constant (e.g., 49 values at 100.0), IQR=0, and the original code silently skipped detection — missing the extreme outlier at 10000.0
- **Fix:** Added Z-score (|z| > 3) as fallback when IQR=0 with nonzero std
- **Files modified:** `backend/app/services/data_pipeline.py`
- **Commit:** 6a0b9da

**3. [Rule 2 - Missing critical functionality] `select_dtypes` updated for pandas 4.x compatibility**
- **Found during:** Task 1 GREEN phase
- **Issue:** `select_dtypes(include="object")` raises `Pandas4Warning` about string dtype being silently included; will break in a future pandas version
- **Fix:** Changed to `include=["object", "string"]` to be explicit
- **Files modified:** `backend/app/services/file_parser.py`
- **Commit:** ac33544

## Commits

| Hash | Type | Description |
|------|------|-------------|
| 74202e6 | test | TDD RED: failing tests for file_parser and frequency_resolver |
| ac33544 | feat | GREEN: file_parser and frequency_resolver implementation |
| 53e6bae | test | TDD RED: failing tests for data_pipeline orchestrator |
| 6a0b9da | feat | GREEN: data_pipeline clean_and_merge orchestrator |

## Known Stubs

None — all functions are fully implemented and wired with real data transformations.

## Self-Check: PASSED
