---
phase: 03-core-analysis-engine
plan: 02
subsystem: api
tags: [claude, anthropic, tool-use, ols, r-code-gen, interpretation]

requires:
  - phase: 02-data-pipeline
    provides: series_mapper.py get_client() singleton pattern (Anthropic SDK tool_use)

provides:
  - "Stage 1 Claude service: generate_ols_slots(prompt, column_names) -> {dep_var, indep_vars, transformations}"
  - "Stage 1 renderer: render_ols_script(dep_var, indep_vars, transformations, data_path) -> R script string"
  - "Stage 2 Claude service: interpret_ols_results(prompt, r_result) -> {interpretation, follow_up_suggestions}"
  - "Stage 2 error service: explain_r_error(prompt, r_stderr) -> {error_explanation, suggested_prompt}"
  - "OLS R template: backend/app/templates/ols_template.R with all diagnostic tests and plotly chart output"

affects: [03-03-celery-task, 03-04-api-endpoint, 03-05-results-display]

tech-stack:
  added: []
  patterns:
    - "Shared Anthropic client singleton via get_client() import from series_mapper — no duplicate client instances"
    - "tool_choice={type: tool, name: ...} forced tool call for guaranteed structured output on all Claude calls"
    - "temperature=0 for Stage 1 (deterministic code gen), temperature=0.3 for Stage 2 (natural language)"
    - "OLS template slot filling: {{DATA_PATH}}, {{DEP_VAR}}, {{INDEP_VARS}}, {{TRANSFORMATIONS}}"

key-files:
  created:
    - backend/app/services/r_code_gen.py
    - backend/app/services/r_interpreter.py
    - backend/app/templates/ols_template.R
    - backend/tests/test_code_gen.py
    - backend/tests/test_interpretation.py
  modified: []

key-decisions:
  - "Stage 1 temperature=0 for deterministic OLS slot extraction (column names must match exactly)"
  - "Stage 2 temperature=0.3 for natural language variation in interpretation text"
  - "render_ols_script uses pathlib.Path(__file__).parent.parent/templates/ols_template.R for portability"
  - "ols_template.R includes full diagnostics: Breusch-Pagan, Durbin-Watson, Shapiro-Wilk (with n<3 guard), VIF; and two plotly charts (coefficient plot, residual plot) using dark theme colors matching UI"

patterns-established:
  - "Claude Stage 1: forced tool_use with available column names in system prompt prevents column hallucination"
  - "Claude Stage 2 diagnostics-aware: system prompt includes specific threshold rules (BP p<0.05, DW <1.5/>2.5, VIF>10, SW p<0.05) so follow-up suggestions are context-aware"
  - "Both service modules are pure functions with no side effects — callable from Celery workers without coupling"

requirements-completed: [ANAL-01, RSLT-01, RSLT-05, RSLT-06]

duration: 15min
completed: 2026-03-24
---

# Phase 03 Plan 02: Claude AI Services (Stage 1 + Stage 2) Summary

**Two Claude tool_use service modules: Stage 1 extracts OLS slots from prompts given column names; Stage 2 interprets R results with diagnostics-aware follow-up suggestions or translates R errors into plain-English fixes.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-03-24T14:53:00Z
- **Completed:** 2026-03-24T15:08:29Z
- **Tasks:** 2 of 2
- **Files modified:** 5

## Accomplishments

- Created `r_code_gen.py` with `generate_ols_slots()` (Stage 1, forced tool_use, temperature=0) and `render_ols_script()` (fills 4 template slots)
- Created `r_interpreter.py` with `interpret_ols_results()` (Stage 2, tool_use, diagnostics-aware system prompt) and `explain_r_error()` (R stderr → plain-English explanation + suggested fix prompt)
- Created `ols_template.R` with full OLS pipeline: data load, transformations slot, `lm()`, BP/DW/SW/VIF diagnostics with edge-case guards, coefficient + residual plotly charts in dark theme, JSON output

## Task Commits

1. **Task 1: Stage 1 Claude service — OLS slot generation and R script rendering** - `71c3f3d` (feat)
2. **Task 2: Stage 2 Claude service — interpretation and error explanation** - `b1cc95f` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `backend/app/services/r_code_gen.py` - Stage 1: generate_ols_slots() + render_ols_script() + CODE_GEN_TOOL schema
- `backend/app/services/r_interpreter.py` - Stage 2: interpret_ols_results() + explain_r_error() + INTERPRET_TOOL + ERROR_INTERPRET_TOOL schemas
- `backend/app/templates/ols_template.R` - R OLS script template with 4 slot placeholders, full diagnostics, plotly charts
- `backend/tests/test_code_gen.py` - 7 tests: slot extraction, tool_use verification, template rendering, error path
- `backend/tests/test_interpretation.py` - 9 tests: interpretation, follow-up suggestions, error explanation, tool_use verification

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all functions are fully implemented with real Claude tool_use calls. The `ols_template.R` template requires R packages (lmtest, sandwich, car, ggplot2, plotly, jsonlite) installed in the Docker container; this is handled by Plan 03's Docker image.

## Self-Check: PASSED

- `backend/app/services/r_code_gen.py` — exists
- `backend/app/services/r_interpreter.py` — exists
- `backend/app/templates/ols_template.R` — exists
- `backend/tests/test_code_gen.py` — 7 tests, all pass
- `backend/tests/test_interpretation.py` — 9 tests, all pass
- Commit `71c3f3d` — Task 1
- Commit `b1cc95f` — Task 2
