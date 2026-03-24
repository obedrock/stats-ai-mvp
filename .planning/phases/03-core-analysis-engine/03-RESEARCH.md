# Phase 3: Core Analysis Engine - Research

**Researched:** 2026-03-24
**Domain:** R execution pipeline, Claude two-stage API, OLS diagnostic tests, Plotly JSON roundtrip, React results rendering
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Results Page Layout**
- D-01: Scrollable sections — all results visible in a single scrollable view with anchored section headers. Order: interpretation at top, then coefficient table, diagnostics, charts, R code, follow-up suggestions.
- D-02: Diagnostic tests displayed as summary cards — each diagnostic as a compact card with test name, statistic value, p-value, and a pass/warn/fail badge (green/yellow/red). Cards in a row for quick visual scan.
- D-03: Plotly charts displayed side-by-side in a 2-column grid (coefficient plot + residual plot). Falls back to stacked on narrow screens.
- D-04: R code section collapsed by default behind a "View R Code" expander with a copy-to-clipboard button visible even when collapsed.

**R Code Generation**
- D-05: Single JSON to stdout — R script outputs one JSON object containing all sections: coefficients, diagnostics, plotly_charts, model_summary. Python parses stdout as JSON. Single contract between R and Python.
- D-06: Data handoff via CSV temp file — Python writes the merged DataFrame to a CSV in the temp directory. R reads it with read.csv(). Docker mounts the tmpdir as read-only. Simple and debuggable.
- D-07: Template with Claude filling slots — a base OLS template with standard diagnostics and Plotly output is pre-written. Claude fills in: dependent var, independent vars, transformations, column mappings. Ensures diagnostics and output format are always correct.
- D-08: Interpretation appears all at once — wait for Claude's full Stage 2 interpretation, then render the complete results page. No streaming infrastructure needed.

**Error Feedback**
- D-09: Inline error card replacing results — when R fails, the results area shows an error card with plain-English explanation, suggested fix, and a collapsible section with raw R error for power users.
- D-10: Claude translates R errors — send R stderr + original prompt context to Claude. Claude returns a plain-English explanation and a suggested modified prompt.
- D-11: "Try a modified prompt" button pre-fills the prompt input with Claude's suggested fix.

**Follow-up Suggestions**
- D-12: Clickable suggestion chips below results — 2-3 chips at the bottom of the results page.
- D-13: Suggestions are context-aware — Claude references specific diagnostic results when suggesting follow-ups.
- D-14: Clicking a follow-up chip pre-fills the prompt input and scrolls up. Does NOT auto-submit.

### Claude's Discretion
- R template structure and specific R code patterns for diagnostics
- System prompt wording for Stage 1 (code generation) and Stage 2 (interpretation)
- Diagnostic test pass/warn/fail thresholds (standard statistical conventions)
- Plotly chart styling and color scheme (consistent with dark theme)
- Coefficient table column formatting (decimal places, significance stars)
- How the existing `run_r_analysis` Celery task is extended vs refactored for the new data handoff and JSON output pattern

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ANAL-01 | User can run OLS regression via natural language prompt | R template pattern with Claude slot-filling (D-07); clean_and_merge output → CSV handoff (D-06) |
| ANAL-05 | System automatically runs diagnostic tests: Breusch-Pagan | `lmtest::bptest()` in R sandbox; already installed in stats-ai-r-sandbox image |
| ANAL-06 | System automatically runs diagnostic tests: Durbin-Watson | `lmtest::dwtest()` in R sandbox; already installed |
| ANAL-07 | System automatically runs diagnostic tests: VIF | `car::vif()` in R sandbox; already installed |
| ANAL-08 | System automatically runs diagnostic tests: Shapiro-Wilk | `stats::shapiro.test()` — base R, no extra package required |
| ANAL-10 | User can run standalone hypothesis tests: t-tests, F-tests, chi-square, ANOVA | Base R stats functions; Phase 3 OLS template lays the pattern for later expansion |
| RSLT-01 | System displays plain-English interpretation via Claude API | Stage 2 Claude call (interpretation system prompt); uses existing anthropic SDK pattern from series_mapper.py |
| RSLT-02 | System displays coefficient tables with SEs, p-values, CIs | R outputs from `summary(model)` and `confint(model)` captured in JSON stdout |
| RSLT-03 | System generates interactive Plotly charts | `ggplot2` + `plotly::ggplotly()` → `plotly::plotly_json()` in R; `react-plotly.js` on frontend |
| RSLT-04 | User can view and copy the generated R code | R code stored on Job model and displayed via RCodeBlock component (collapsed by default) |
| RSLT-05 | System translates R errors into actionable plain-English feedback | Stage 2 error path: R stderr + prompt → Claude error explanation → ErrorResultCard |
| RSLT-06 | After analysis, Claude suggests related follow-up tests | Stage 2 response includes follow_up_suggestions array; rendered as FollowUpChip components |

</phase_requirements>

---

## Summary

Phase 3 builds the complete OLS analysis execution loop on top of the Phase 1+2 foundation. The core challenge is threefold: (1) generating correct R code via Claude that always produces the expected JSON stdout contract, (2) wiring the Phase 2 data pipeline output (merged DataFrame) into the R execution sandbox via CSV temp file, and (3) rendering the structured results across six frontend sections defined by the UI-SPEC.

The existing codebase provides all the infrastructure needed: `run_r_analysis` Celery task with Docker subprocess, the R sandbox image with all required packages (lmtest, sandwich, car, ggplot2, plotly, jsonlite), the `series_mapper.py` Claude API pattern for tool-use calls, and the `JobStatusCard` component with `running_r` and `generating_interpretation` stages already wired. Phase 3 extends these, it does not replace them.

The two highest-risk items are: (a) Claude reliably filling the R template slots with correct column names that match the CSV headers produced by `clean_and_merge()`, and (b) the Plotly JSON roundtrip from R's `plotly_json()` rendering correctly via `react-plotly.js` with the dark theme layout overrides. Both are solvable with defensive patterns documented below.

**Primary recommendation:** Build around a pre-written R template with narrowly scoped Claude slot-filling (column names, variable roles, transformations only). Never let Claude write free-form R code for Phase 3 — the template guarantees diagnostics run and JSON output is always correctly structured.

---

## Standard Stack

### Core (all already in project — no new installs)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| anthropic (Python SDK) | 0.86.0 | Claude API calls (Stage 1 + Stage 2) | Already used in series_mapper.py; same pattern extended for code gen and interpretation |
| celery[redis] | 5.6.2 | Async R execution task queue | Already wiring run_r_analysis; extend with CSV mount and JSON parsing |
| R: lmtest | 0.9-40+ | bptest(), dwtest() | Installed in stats-ai-r-sandbox image |
| R: sandwich | 3.x | HC3 robust standard errors | Installed in stats-ai-r-sandbox image |
| R: car | 3.x | vif() for multicollinearity | Installed in stats-ai-r-sandbox image |
| R: stats (base) | built-in | shapiro.test(), lm(), confint() | Always available in R; no install |
| R: ggplot2 | 3.5.x | Chart generation | Installed in stats-ai-r-sandbox image |
| R: plotly (R) | 4.10.x | ggplotly() → plotly_json() | Installed in stats-ai-r-sandbox image |
| R: jsonlite | 1.8.x | toJSON() for stdout contract | Installed in stats-ai-r-sandbox image |
| react-plotly.js | 2.6.x | Render Plotly JSON from R | In project stack; not yet installed in frontend |
| plotly.js-dist | 2.x | Peer dep for react-plotly.js | Required alongside react-plotly.js |

### New Frontend Install Required

```bash
cd frontend && npm install react-plotly.js plotly.js-dist-min
# Use plotly.js-dist-min for smaller bundle (~3MB vs ~7MB full)
# react-plotly.js 2.6.x accepts either dist variant
```

**Note:** `@types/react-plotly.js` is bundled with `react-plotly.js` starting 2.6.x — no separate `@types` install needed.

### New Backend Install Required

```bash
# No new Python packages needed for Phase 3
# All required packages already in requirements.txt / uv.lock
```

---

## Architecture Patterns

### The Two-Stage Claude Call Pattern (Phase 3 Extension)

Phase 3 extends the established Claude API pattern from `series_mapper.py`:

**Stage 1 — Code Generation (temperature=0, tool_use)**
- Input: original user prompt + column names from merged DataFrame + data schema
- Output: tool_use response with slot values (dep_var, indep_vars, transformations)
- Pattern: same tool_use approach as `detect_data_sources` in series_mapper.py
- Claude fills slots, NOT writes free-form code

**Stage 2 — Interpretation + Suggestions (temperature=0.3, standard message)**
- Input: R JSON output + original prompt + diagnostic results
- Output: structured JSON with interpretation text, follow_up_suggestions array
- On R error path: input is R stderr + prompt; output is error_explanation + suggested_prompt

### R Output JSON Contract (D-05)

The R template MUST produce exactly this structure to stdout. Python parses it with `json.loads(stdout)`:

```json
{
  "coefficients": [
    {
      "variable": "GDP",
      "estimate": 0.423,
      "std_error": 0.089,
      "t_stat": 4.75,
      "p_value": 0.0001,
      "ci_lower": 0.248,
      "ci_upper": 0.598
    }
  ],
  "model_summary": {
    "r_squared": 0.734,
    "adj_r_squared": 0.721,
    "f_statistic": 55.3,
    "f_p_value": 0.000001,
    "n_obs": 96,
    "degrees_of_freedom": 3
  },
  "diagnostics": {
    "breusch_pagan": {"statistic": 2.31, "p_value": 0.128, "df": 2},
    "durbin_watson": {"statistic": 1.87, "p_value": null},
    "vif": {"GDP": 1.23, "INFLATION": 1.45},
    "shapiro_wilk": {"statistic": 0.984, "p_value": 0.312}
  },
  "plotly_charts": [
    {"name": "coefficient_plot", "json": "...plotly JSON string..."},
    {"name": "residual_plot", "json": "...plotly JSON string..."}
  ]
}
```

**Key detail:** `plotly_json()` in R returns a character string of JSON. Each chart JSON is stored as a string inside the outer JSON object, then parsed by the Python layer before storing.

### R Template Structure (D-07)

The pre-written template skeleton. Claude fills ONLY the marked slots:

```r
# Auto-generated by Stats-AI — do not edit manually
# Slots filled by Claude: dep_var, indep_vars, data_path, transformations

library(lmtest)
library(sandwich)
library(car)
library(ggplot2)
library(plotly)
library(jsonlite)

# ── Data loading ──────────────────────────────────────────────────────────────
df <- read.csv("{{DATA_PATH}}", stringsAsFactors = FALSE)
df$date <- as.Date(df$date)

# ── Transformations (Claude fills this block) ─────────────────────────────────
{{TRANSFORMATIONS}}

# ── Model ─────────────────────────────────────────────────────────────────────
formula_str <- "{{DEP_VAR}} ~ {{INDEP_VARS}}"
model <- lm(as.formula(formula_str), data = df)
coef_summary <- summary(model)$coefficients
ci <- confint(model)

# ── Diagnostics ───────────────────────────────────────────────────────────────
bp_test    <- bptest(model)
dw_test    <- dwtest(model)
vif_vals   <- tryCatch(vif(model), error = function(e) NULL)
sw_test    <- shapiro.test(residuals(model))

# ── Coefficient plot ──────────────────────────────────────────────────────────
coef_df <- data.frame(
  variable = rownames(ci)[-1],
  estimate = coef(model)[-1],
  ci_lower = ci[-1, 1],
  ci_upper = ci[-1, 2]
)
p_coef <- ggplot(coef_df, aes(x = variable, y = estimate)) +
  geom_point(color = "#6366f1") +
  geom_errorbar(aes(ymin = ci_lower, ymax = ci_upper), width = 0.2, color = "#6366f1") +
  geom_hline(yintercept = 0, linetype = "dashed", color = "#94a3b8") +
  coord_flip() +
  theme_minimal() +
  theme(
    panel.background = element_rect(fill = "transparent", color = NA),
    plot.background  = element_rect(fill = "transparent", color = NA),
    panel.grid.major = element_line(color = "#334155"),
    text             = element_text(color = "#f1f5f9")
  ) +
  labs(title = "Coefficient Estimates", x = NULL, y = "Estimate")

# ── Residual plot ─────────────────────────────────────────────────────────────
resid_df <- data.frame(fitted = fitted(model), residuals = residuals(model))
p_resid <- ggplot(resid_df, aes(x = fitted, y = residuals)) +
  geom_point(alpha = 0.6, color = "#6366f1") +
  geom_hline(yintercept = 0, linetype = "dashed", color = "#94a3b8") +
  theme_minimal() +
  theme(
    panel.background = element_rect(fill = "transparent", color = NA),
    plot.background  = element_rect(fill = "transparent", color = NA),
    panel.grid.major = element_line(color = "#334155"),
    text             = element_text(color = "#f1f5f9")
  ) +
  labs(title = "Residuals vs Fitted", x = "Fitted Values", y = "Residuals")

# ── Assemble output ───────────────────────────────────────────────────────────
coef_rows <- lapply(rownames(coef_summary), function(nm) {
  list(
    variable  = nm,
    estimate  = round(coef_summary[nm, "Estimate"], 6),
    std_error = round(coef_summary[nm, "Std. Error"], 6),
    t_stat    = round(coef_summary[nm, "t value"], 4),
    p_value   = round(coef_summary[nm, "Pr(>|t|)"], 6),
    ci_lower  = round(ci[nm, 1], 6),
    ci_upper  = round(ci[nm, 2], 6)
  )
})

vif_out <- if (!is.null(vif_vals)) as.list(round(vif_vals, 4)) else list()

output <- list(
  coefficients = coef_rows,
  model_summary = list(
    r_squared          = round(summary(model)$r.squared, 6),
    adj_r_squared      = round(summary(model)$adj.r.squared, 6),
    f_statistic        = round(summary(model)$fstatistic[1], 4),
    f_p_value          = round(pf(summary(model)$fstatistic[1],
                                  summary(model)$fstatistic[2],
                                  summary(model)$fstatistic[3],
                                  lower.tail = FALSE), 6),
    n_obs              = nrow(df),
    degrees_of_freedom = model$df.residual
  ),
  diagnostics = list(
    breusch_pagan = list(
      statistic = round(bp_test$statistic[[1]], 4),
      p_value   = round(bp_test$p.value[[1]], 6),
      df        = as.integer(bp_test$parameter[[1]])
    ),
    durbin_watson = list(
      statistic = round(dw_test$statistic[[1]], 4),
      p_value   = round(dw_test$p.value[[1]], 6)
    ),
    vif = vif_out,
    shapiro_wilk = list(
      statistic = round(sw_test$statistic[[1]], 4),
      p_value   = round(sw_test$p.value[[1]], 6)
    )
  ),
  plotly_charts = list(
    list(name = "coefficient_plot", json = plotly_json(ggplotly(p_coef), pretty = FALSE)),
    list(name = "residual_plot",    json = plotly_json(ggplotly(p_resid), pretty = FALSE))
  )
)

cat(toJSON(output, auto_unbox = TRUE))
```

### CSV Handoff Pattern (D-06)

Python writes CSV before invoking Docker. Docker mounts the tmpdir with the CSV as read-only alongside the R script:

```python
# In the extended run_r_analysis task
with tempfile.TemporaryDirectory() as tmpdir:
    # Write data CSV
    csv_path = os.path.join(tmpdir, "data.csv")
    df.to_csv(csv_path, index=True, index_label="date")

    # Write R script (with DATA_PATH filled)
    script_path = os.path.join(tmpdir, "analysis.R")
    r_script = template.replace("{{DATA_PATH}}", "/data/data.csv")
    with open(script_path, "w") as f:
        f.write(r_script)

    _current_proc = subprocess.Popen([
        "docker", "run", "--rm",
        "--network", "none",
        "--memory", "512m",
        "--cpus", "1.0",
        "--read-only",
        "--tmpfs", "/tmp:size=64m",
        "--user", "1000",
        "-v", f"{script_path}:/analysis.R:ro",
        "-v", f"{csv_path}:/data/data.csv:ro",   # ← NEW: mount CSV
        "stats-ai-r-sandbox", "Rscript", "/analysis.R",
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
```

**Important:** The `/data/` directory does not exist in the R sandbox image. Docker creates it when mounting a volume to a non-existent path — this works correctly. Alternatively, mount the entire tmpdir as `/data`. The single-file mount per file is cleaner and more restrictive.

### Stage 1 Tool Use Schema

Claude fills exactly these slots — nothing more:

```python
CODE_GEN_TOOL = {
    "name": "generate_ols_slots",
    "description": "Extract OLS model specification from a natural language prompt given known column names.",
    "input_schema": {
        "type": "object",
        "properties": {
            "dep_var": {
                "type": "string",
                "description": "Column name of the dependent variable from the provided column list."
            },
            "indep_vars": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Column names of independent variables from the provided column list."
            },
            "transformations": {
                "type": "string",
                "description": "R code block for any transformations (log, lag, pct_change). Empty string if none."
            }
        },
        "required": ["dep_var", "indep_vars", "transformations"]
    }
}
```

System prompt must include the column names as context: `"Available columns: date, {col1}, {col2}, ..."`

### Stage 2 System Prompt Pattern

Stage 2 receives the JSON output from R and produces interpretation + follow-up suggestions. Return as structured JSON via tool_use:

```python
INTERPRET_TOOL = {
    "name": "interpret_ols_results",
    "input_schema": {
        "type": "object",
        "properties": {
            "interpretation": {
                "type": "string",
                "description": "2-4 paragraph plain-English interpretation of the OLS results."
            },
            "follow_up_suggestions": {
                "type": "array",
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "explanation": {"type": "string"},
                        "prompt_text": {"type": "string"}
                    },
                    "required": ["title", "explanation", "prompt_text"]
                }
            }
        },
        "required": ["interpretation", "follow_up_suggestions"]
    }
}
```

Stage 2 system prompt MUST include: the R JSON results, the original user prompt, and a brief on the diagnostic thresholds so suggestions are context-aware (D-13).

### Error Stage 2 Pattern

When R returns non-zero exit code, use a separate system prompt:

```python
ERROR_INTERPRET_TOOL = {
    "name": "explain_r_error",
    "input_schema": {
        "type": "object",
        "properties": {
            "error_explanation": {"type": "string"},
            "suggested_prompt": {"type": "string"}
        },
        "required": ["error_explanation", "suggested_prompt"]
    }
}
```

Input: R stderr text + original user prompt. Output stored on job and passed to frontend for ErrorResultCard rendering.

### Pipelined Celery Task Architecture

Phase 3 needs two execution paths, both as Celery tasks:

**Path A — Full pipeline (normal flow):**
`fetch_data` task → `run_ols_analysis` task (new in Phase 3)

The `run_ols_analysis` task:
1. Receives `job_id`, `prompt`, `cache_keys` (from fetch_data result stored on Job)
2. Reconstructs DataFrame from Redis cache keys
3. Calls Stage 1 Claude (slot filling) via `run_in_executor` (sync SDK call)
4. Writes CSV to tmpdir, fills R template
5. `self.update_state(stage="running_r")`
6. Runs Docker subprocess (existing pattern from `run_r_analysis`)
7. On R success: Parses JSON stdout, calls Stage 2 Claude for interpretation
8. `self.update_state(stage="generating_interpretation")`
9. Stores full result on Job model; updates job.status = "success"
10. On R error: Calls Stage 2 error interpretation path; stores on Job

**Alternatively** (simpler for Phase 3): Extend `run_r_analysis` task to accept the DataFrame and do all 10 steps in a single task. The CONTEXT.md leaves this to Claude's discretion (D-44). The single-task approach is recommended — it avoids Celery chain complexity and the Phase 3 flow is linear.

### Job Model Extension (new columns needed)

Phase 3 needs to store structured analysis results. New columns for the `jobs` table:

```python
# New columns to add via Alembic manual migration
r_result_json: Mapped[str] = mapped_column(Text, nullable=True)     # Parsed R JSON output
interpretation: Mapped[str] = mapped_column(Text, nullable=True)     # Claude Stage 2 text
follow_up_suggestions: Mapped[str] = mapped_column(Text, nullable=True)  # JSON array
error_explanation: Mapped[str] = mapped_column(Text, nullable=True)  # Claude error text
suggested_prompt: Mapped[str] = mapped_column(Text, nullable=True)   # Claude suggested fix
```

All stored as Text (JSON-serialized) — consistent with Phase 1+2 precedent (no JSONB to preserve SQLite test compat).

### Analysis Router (New)

New router: `backend/app/routers/analysis.py` with prefix `/analysis`:

```
POST /analysis/run       — Accept job_id (from preview_ready stage) + prompt; start run_ols_analysis task
GET  /analysis/{job_id}  — Poll for analysis status; return full results when complete
```

The frontend "Run Analysis" button triggers `POST /analysis/run`. The frontend then polls `GET /analysis/{job_id}` at 2s intervals until `status == "success"` or `"error"`.

**Note:** The existing `/jobs/{job_id}` polling in JobStatusCard polls the jobs router for stage updates. The analysis router can reuse the same job record — the polling endpoints differ only in what they return (stage vs full results).

### Zustand Store Extension

```typescript
// New states to add to pipelineStage union type
type PipelineStage =
  | "idle" | "parsing" | "confirming_sources" | "fetching"
  | "frequency_conflict" | "confirming_assumptions" | "preview_ready"
  | "running_analysis"    // ← new: analysis job submitted, polling
  | "analysis_complete"   // ← new: results ready, show ResultsSection
  | "analysis_error";     // ← new: R failed, show ErrorResultCard

// New state fields
analysisJobId: string | null;          // separate from data pipeline jobId
analysisResult: AnalysisResult | null; // parsed result from GET /analysis/{id}
analysisError: AnalysisError | null;   // error explanation + suggested prompt
```

The WorkspacePage conditional rendering adds three new branches for these stages.

### react-plotly.js Integration Pattern

```typescript
// Source: react-plotly.js docs / CLAUDE.md project stack
import Plot from "react-plotly.js";

// R's plotly_json() output is a JSON string.
// Python parses it and returns data + layout as separate objects.
// Frontend receives: { data: PlotData[], layout: Partial<Layout> }

function PlotlyChart({ chartJson }: { chartJson: { data: unknown; layout: unknown } }) {
  return (
    <Plot
      data={chartJson.data as Plotly.Data[]}
      layout={{
        ...(chartJson.layout as Partial<Plotly.Layout>),
        // Dark theme overrides (D-03 / UI-SPEC)
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { color: "#f1f5f9" },
        gridcolor: "#334155",
      }}
      useResizeHandler={true}
      style={{ width: "100%", height: "360px" }}
      config={{ responsive: true, displayModeBar: false }}
    />
  );
}
```

**Important:** `plotly_json()` in R returns a single JSON string that contains `data` and `layout` as top-level keys. Python must `json.loads()` this string before sending to frontend. The frontend receives two separate JSON objects (data array + layout object), NOT the raw string.

### Recommended Project Structure

```
backend/app/
├── routers/
│   └── analysis.py          ← new: POST /analysis/run, GET /analysis/{id}
├── schemas/
│   └── analysis.py          ← new: AnalysisResult, AnalysisError Pydantic schemas
├── services/
│   └── r_code_gen.py        ← new: Stage 1 Claude call + template rendering
│   └── r_interpreter.py     ← new: Stage 2 Claude call (interpret + error)
├── tasks/
│   └── analysis.py          ← extend: add CSV mount, JSON parsing, Stage 1+2 logic
│   └── data_pipeline.py     ← no change
├── templates/
│   └── ols_template.R       ← new: pre-written R template with {{SLOTS}}

frontend/src/
├── components/
│   ├── InterpretationSection.tsx   ← new
│   ├── CoefficientTable.tsx        ← new
│   ├── DiagnosticsRow.tsx          ← new (contains DiagnosticCard)
│   ├── DiagnosticCard.tsx          ← new
│   ├── ChartGrid.tsx               ← new
│   ├── RCodeBlock.tsx              ← new
│   ├── ErrorResultCard.tsx         ← new
│   ├── FollowUpChip.tsx            ← new
│   └── FollowUpRow.tsx             ← new
├── pages/
│   └── WorkspacePage.tsx           ← extend: add running_analysis, analysis_complete, analysis_error branches
├── store/
│   └── analysis.ts                 ← extend: new stage values + analysisResult/analysisError fields
├── types/
│   └── analysis.ts                 ← new: AnalysisResult, DiagnosticResult, CoefficientRow types
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Heteroskedasticity-consistent SEs | Custom SE calculation | `sandwich::vcovHC(model, type="HC3")` | Sandwich estimator handles multiple HC types; HC3 is the econometric standard for small samples |
| OLS diagnostic testing | Custom stat tests | `lmtest::bptest()`, `lmtest::dwtest()`, `car::vif()`, `stats::shapiro.test()` | These are tested implementations; BP test in particular requires correct chi-sq df handling |
| Interactive chart rendering | SVG/Canvas chart from coefficients | `react-plotly.js` consuming R's `plotly_json()` | Avoids re-implementing hover, zoom, axis formatting; R already produces correct chart structure |
| Plotly chart theming for dark mode | Custom CSS overrides | `paper_bgcolor`, `plot_bgcolor`, `font.color` layout overrides | Plotly layout system handles dark mode cleanly; CSS targeting Plotly internals is fragile |
| JSON serialization from R | Custom print statements | `jsonlite::toJSON(output, auto_unbox = TRUE)` | `auto_unbox=TRUE` is critical — without it, single-element arrays stay as `[value]` instead of `value`, breaking Python parsing |
| Copy to clipboard | Custom clipboard logic | `navigator.clipboard.writeText()` with `useState` for icon swap | Browser API is sufficient; no library needed |
| Significance stars | Manual threshold checks | Inline utility `p < 0.001 → "***"` etc. in coefficient table | One-liner; not worth a library |

**Key insight:** The R ecosystem has production-grade implementations for every econometric diagnostic test. Any custom Python re-implementation would be less accurate and harder to maintain than the R equivalents.

---

## Common Pitfalls

### Pitfall 1: jsonlite auto_unbox and single-predictor VIF

**What goes wrong:** When a model has only one independent variable, `car::vif()` returns a named scalar (not a named vector). `jsonlite::toJSON()` without `auto_unbox=TRUE` wraps scalars in arrays. Python JSON parsing then receives `{"GDP": [1.0]}` instead of `{"GDP": 1.0}`.

**Why it happens:** R's type system treats single-value vectors differently. `toJSON(auto_unbox=TRUE)` unwraps them; without it, everything is an array.

**How to avoid:** Always use `toJSON(output, auto_unbox=TRUE)` in the R template. Additionally, VIF is undefined for single-predictor models — wrap `vif()` in `tryCatch` and return `null`/empty list when only one predictor exists.

**Warning signs:** Python `json.loads()` produces lists where floats are expected; CI table renders `[0.234]` instead of `0.234`.

### Pitfall 2: Column name mismatch between CSV and R template

**What goes wrong:** `clean_and_merge()` renames columns to the `series_id` (e.g., `GDPC1`, `DFF`). Claude Stage 1 fills `dep_var="GDPC1"` but the CSV header might be `GDPC1` or `gdpc1` depending on pandas `.to_csv()` behavior. The `lm()` call silently fails with "object not found" if names don't match exactly.

**Why it happens:** Pandas column names are case-sensitive and preserved as-is from the DataFrame. Claude sees column names in the prompt context but might infer different casing.

**How to avoid:** Explicitly pass the exact column names from the DataFrame to the Stage 1 system prompt: `f"Available columns (exact case): {', '.join(df.columns.tolist())}"`. The R template should not lowercase or rename columns.

**Warning signs:** R stderr contains "object 'X' not found" or `lm()` formula error.

### Pitfall 3: Durbin-Watson p-value availability

**What goes wrong:** `lmtest::dwtest()` computes the DW statistic but the p-value can be `NA` for small samples or certain model structures. Python JSON parsing fails or frontend shows `null` p-value without explanation.

**Why it happens:** DW p-values require interpolation from tables; for very small samples (n < 15) or certain patterns, lmtest returns `NA`.

**How to avoid:** In the R template, use `tryCatch` around DW p-value extraction. If `is.na(dw_p)`, set to `null` in JSON output. Frontend DiagnosticCard must handle `null` p-value gracefully (show "—" instead of a number).

**Warning signs:** JSON parsing error on `null` values; NaN appearing in the DW diagnostic card.

### Pitfall 4: Plotly JSON too large for stdout buffer

**What goes wrong:** Two `ggplotly()` charts with many data points can produce 100–500KB of JSON. Subprocess stdout buffer fills up, causing the process to hang until `communicate()` drains it. The 60s timeout expires.

**Why it happens:** `subprocess.Popen` with `stdout=subprocess.PIPE` has a default OS buffer (typically 64KB on Linux). If R writes more than the buffer before Python reads it, R blocks waiting for the buffer to drain.

**How to avoid:** The existing code correctly uses `_current_proc.communicate(timeout=60)` which drains stdout/stderr in one call. This is safe. Additionally, use `plotly::style(p, showlegend=FALSE)` and `ggplotly(p, tooltip=c("x","y"))` to reduce chart data payload.

**Warning signs:** R subprocess hangs at exactly 60 seconds; DW test completes but JSON output is truncated.

### Pitfall 5: Shapiro-Wilk sample size limit

**What goes wrong:** `shapiro.test()` in base R fails with an error if `n > 5000` or `n < 3`. For large merged datasets (possible with daily Yahoo Finance data), this throws an R error and terminates the script.

**Why it happens:** The Shapiro-Wilk test is computationally limited to the 3–5000 sample range.

**How to avoid:** Wrap `shapiro.test()` in the R template: if `nrow(df) > 5000`, apply to a random sample of 5000 rows. If `nrow(df) < 3`, skip with a `null` result. Document the sampling in the JSON output.

**Warning signs:** R script exits with "sample size must be between 3 and 5000"; the R sandbox returns a non-zero exit code even when the regression itself is correct.

### Pitfall 6: Frontend polling transitions and result hydration

**What goes wrong:** The frontend polls `/analysis/{job_id}` and receives the full result object when complete. If the result object is large (multiple charts with embedded Plotly JSON), the first successful poll response is large. TanStack Query caches it, but the WorkspacePage transition from `running_analysis` to `analysis_complete` must happen atomically — partial renders show unstyled JSON blobs.

**Why it happens:** Zustand state updates are synchronous but React re-renders are batched. If `setPipelineStage("analysis_complete")` and `setAnalysisResult(data)` are called separately, a flash of empty state can occur.

**How to avoid:** Call `setPipelineStage` and `setAnalysisResult` in a single `set()` call in the Zustand store action. Parse and validate the result before transitioning stages.

---

## Code Examples

### Stage 1 Claude Call (slot filling)

```python
# Source: extends series_mapper.py pattern
import asyncio
import anthropic
import os

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

def generate_ols_slots(prompt: str, column_names: list[str]) -> dict:
    """Call Claude Stage 1 to extract OLS model specification."""
    columns_str = ", ".join(column_names)
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=512,
        temperature=0,
        system=(
            f"You are an econometrician configuring an OLS regression. "
            f"Available columns (exact case, from cleaned data): {columns_str}. "
            f"Identify the dependent variable, independent variables, and any required "
            f"transformations (log, lag, percent change). Only use column names from the list above."
        ),
        tools=[CODE_GEN_TOOL],
        tool_choice={"type": "tool", "name": "generate_ols_slots"},
        messages=[{"role": "user", "content": prompt}],
    )
    tool_use = next(b for b in response.content if b.type == "tool_use")
    return tool_use.input
```

### Stage 2 Claude Interpretation Call

```python
def interpret_ols_results(prompt: str, r_result: dict) -> dict:
    """Call Claude Stage 2 to interpret OLS results and suggest follow-ups."""
    import json
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        temperature=0.3,
        system=(
            "You are a statistical analyst explaining OLS regression results to an economist. "
            "Be precise, reference specific coefficient values and p-values. "
            "For follow-up suggestions, reference diagnostic failures directly: "
            "if Breusch-Pagan p < 0.05 suggest robust SEs; "
            "if Durbin-Watson < 1.5 suggest lag terms; "
            "if VIF > 10 suggest removing correlated predictors; "
            "if Shapiro-Wilk p < 0.05 suggest log transformation."
        ),
        tools=[INTERPRET_TOOL],
        tool_choice={"type": "tool", "name": "interpret_ols_results"},
        messages=[{
            "role": "user",
            "content": (
                f"Original request: {prompt}\n\n"
                f"Results:\n{json.dumps(r_result, indent=2)}"
            )
        }],
    )
    tool_use = next(b for b in response.content if b.type == "tool_use")
    return tool_use.input
```

### Plotly JSON Parsing in Python

```python
import json

def parse_plotly_charts(plotly_charts_raw: list[dict]) -> list[dict]:
    """Parse embedded plotly JSON strings from R output.

    R's plotly_json() returns a JSON string. toJSON() wraps it as a string
    inside the outer JSON. We must json.loads() each chart's json field.
    """
    parsed = []
    for chart in plotly_charts_raw:
        chart_data = json.loads(chart["json"])  # Parse the inner JSON string
        parsed.append({
            "name": chart["name"],
            "data": chart_data.get("data", []),
            "layout": chart_data.get("layout", {}),
        })
    return parsed
```

### DiagnosticCard Badge Logic

```typescript
// Source: UI-SPEC thresholds (D-02 / 03-UI-SPEC.md)
type BadgeVariant = "pass" | "warn" | "fail";

function getDiagnosticBadge(
  testName: "breusch_pagan" | "durbin_watson" | "vif" | "shapiro_wilk",
  result: DiagnosticResult
): BadgeVariant {
  switch (testName) {
    case "breusch_pagan":
    case "shapiro_wilk":
      if (result.p_value === null) return "warn";
      if (result.p_value > 0.05) return "pass";
      if (result.p_value >= 0.01) return "warn";
      return "fail";
    case "durbin_watson":
      const dw = result.statistic;
      if (dw >= 1.5 && dw <= 2.5) return "pass";
      if (dw >= 1.0 && dw <= 3.0) return "warn";
      return "fail";
    case "vif":
      // VIF is per-variable; return worst case
      const maxVif = Math.max(...Object.values(result.per_variable ?? {}));
      if (maxVif < 5) return "pass";
      if (maxVif <= 10) return "warn";
      return "fail";
  }
}

const BADGE_CLASSES: Record<BadgeVariant, string> = {
  pass: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  warn: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  fail: "bg-red-500/20 text-red-400 border-red-500/30",
};
```

### Alembic Manual Migration Pattern (consistent with Phase 1+2)

```python
# backend/alembic/versions/c6f3b1d8e2a4_add_analysis_result_columns_to_jobs.py
def upgrade() -> None:
    op.add_column("jobs", sa.Column("r_result_json", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("interpretation", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("follow_up_suggestions", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("error_explanation", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("suggested_prompt", sa.Text(), nullable=True))

def downgrade() -> None:
    for col in ["r_result_json", "interpretation", "follow_up_suggestions",
                "error_explanation", "suggested_prompt"]:
        op.drop_column("jobs", col)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| R plotly via PNG export | plotly_json() roundtrip to react-plotly.js | 2020+ | Interactive charts vs static images |
| rpy2 for R integration | subprocess with Docker isolation | Project decision | Safer: R crash cannot kill Python process |
| Streaming R output parsing | Single JSON stdout contract | D-05 decision | Simpler parsing; no partial-result complexity |
| Free-form R code generation | Template + Claude slot-filling | D-07 decision | Guarantees diagnostic tests always run |
| sandwich vcovHC(type="HC1") | HC3 as default | ~2015 (MacKinnon-White) | HC3 is less biased in small samples |

**Deprecated/outdated:**
- `lm.robust()` from estimatr: Acceptable alternative but not in R sandbox image; use `sandwich` + `coeftest` instead
- R's `plot(model)` for diagnostics: Produces static graphics device output, not Plotly-compatible; use ggplot2 + ggplotly instead

---

## Open Questions

1. **DataFrame reconstruction from Redis cache keys**
   - What we know: `fetch_data` task returns `cache_keys` list; `data_pipeline.py` stores DataFrames as `df.to_json()` in Redis
   - What's unclear: Does the `run_ols_analysis` task need to reconstruct the merged DataFrame from individual series cache keys and re-run `clean_and_merge()`? Or should the merged DataFrame itself be cached?
   - Recommendation: Cache the merged DataFrame output of `clean_and_merge()` separately with a key like `merged:{job_id}` (TTL 1h) so Phase 3 can retrieve it without re-merging. If not cached, reconstruct from individual series keys and re-merge — this is safe but adds ~1s latency.

2. **ANAL-10: Standalone hypothesis tests in Phase 3 scope**
   - What we know: ANAL-10 is in the Phase 3 requirement list per REQUIREMENTS.md and CONTEXT.md
   - What's unclear: The phase description focuses on OLS; ANAL-10 (t-tests, F-tests, chi-square, ANOVA) might just mean the F-test from the OLS summary is sufficient for Phase 3 scope
   - Recommendation: For Phase 3, satisfy ANAL-10 by including the model F-test in the OLS results (already in `model_summary.f_statistic`). Standalone test endpoints are a Phase 4+ extension. The planner should confirm this interpretation.

3. **Analysis job endpoint design: new router vs extend existing jobs router**
   - What we know: Existing `/jobs` router handles generic job submission and status polling; D context says Phase 3 wires `handleRunAnalysis` in WorkspacePage
   - What's unclear: Whether `POST /analysis/run` should be a new router or a new endpoint in the existing jobs router
   - Recommendation: New router `/analysis` — keeps separation of concerns clean and avoids adding Phase 3 analysis concerns to the already-complete Phase 1 jobs router.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Docker | R sandbox execution | Unknown (not installed on dev) | — | Authoring only — Docker required on deployment server |
| stats-ai-r-sandbox image | R execution | Unknown (requires Docker) | r-base:4.4.2 | Build on deploy server |
| react-plotly.js | Frontend chart rendering | Not yet installed | 2.6.x | — (required) |
| plotly.js-dist-min | Peer dep for react-plotly.js | Not yet installed | 2.x | — (required) |
| anthropic Python SDK | Stage 1 + Stage 2 Claude calls | Installed | 0.86.0 | — |
| jsonlite (R) | JSON stdout from R | Installed in image | 1.8.x | — |

**Missing dependencies with no fallback:**
- `react-plotly.js` + `plotly.js-dist-min` — must be installed in frontend before chart components can be built

**Note on Docker:** Per STATE.md, Docker Desktop is not installed on the dev machine. All Docker-dependent tests (test_r_sandbox.py) require the deploy server. Development of R template and Claude services can proceed on the dev machine without Docker; integration testing requires the deploy environment.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.x + pytest-asyncio |
| Config file | `backend/pytest.ini` (existing) |
| Quick run command | `cd backend && uv run pytest tests/test_analysis_service.py -x` |
| Full suite command | `cd backend && uv run pytest tests/ -x` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ANAL-01 | OLS runs and returns coefficient table | unit | `pytest tests/test_analysis_service.py::test_ols_returns_coefficients -x` | Wave 0 |
| ANAL-05 | Breusch-Pagan test runs and parses | unit | `pytest tests/test_r_template.py::test_bp_test_in_output -x` | Wave 0 |
| ANAL-06 | Durbin-Watson test runs and parses | unit | `pytest tests/test_r_template.py::test_dw_test_in_output -x` | Wave 0 |
| ANAL-07 | VIF test runs and parses | unit | `pytest tests/test_r_template.py::test_vif_in_output -x` | Wave 0 |
| ANAL-08 | Shapiro-Wilk test runs and parses | unit | `pytest tests/test_r_template.py::test_sw_test_in_output -x` | Wave 0 |
| ANAL-10 | F-test statistic in model_summary | unit | `pytest tests/test_analysis_service.py::test_f_statistic_present -x` | Wave 0 |
| RSLT-01 | Interpretation non-empty string | unit (mock Claude) | `pytest tests/test_r_interpreter.py::test_interpretation_returned -x` | Wave 0 |
| RSLT-02 | Coefficient table has SEs, p-values, CIs | unit | `pytest tests/test_analysis_service.py::test_coefficient_fields -x` | Wave 0 |
| RSLT-03 | Plotly charts array non-empty, data parseable | unit | `pytest tests/test_analysis_service.py::test_plotly_charts_parseable -x` | Wave 0 |
| RSLT-04 | R code stored on job | integration | `pytest tests/test_analysis_router.py::test_r_code_on_job -x` | Wave 0 |
| RSLT-05 | R error returns error_explanation | unit (mock R fail) | `pytest tests/test_r_interpreter.py::test_error_explanation_returned -x` | Wave 0 |
| RSLT-06 | Follow-up suggestions array length 2-3 | unit (mock Claude) | `pytest tests/test_r_interpreter.py::test_follow_up_suggestions -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `cd backend && uv run pytest tests/test_analysis_service.py -x`
- **Per wave merge:** `cd backend && uv run pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

All test files for Phase 3 are new:

- [ ] `backend/tests/test_analysis_service.py` — covers ANAL-01, ANAL-10, RSLT-02, RSLT-03, RSLT-04
- [ ] `backend/tests/test_r_template.py` — covers ANAL-05, ANAL-06, ANAL-07, ANAL-08 (requires Docker on CI)
- [ ] `backend/tests/test_r_interpreter.py` — covers RSLT-01, RSLT-05, RSLT-06 (mock Claude responses)
- [ ] `backend/tests/test_analysis_router.py` — covers RSLT-04 integration path

**Note on R template tests:** `test_r_template.py` tests require the Docker sandbox to be running. They should be marked `@pytest.mark.docker` and excluded from the quick run command. The CI/CD pipeline on the deploy server runs them in full suite mode.

---

## Project Constraints (from CLAUDE.md)

These directives from CLAUDE.md are BINDING on planning and implementation:

| Constraint | Value |
|------------|-------|
| R execution method | subprocess with Docker — NEVER rpy2, NEVER shell=True |
| R sandbox image | `stats-ai-r-sandbox` (r-base:4.4.2 + lmtest, sandwich, car, ggplot2, plotly, jsonlite) |
| Claude model | `claude-sonnet-4-5` (established in series_mapper.py) |
| Python version | 3.12 via uv |
| Package manager | uv — use `uv pip install`, `uv run` |
| Async pattern | `run_in_executor` for sync blocking calls (Claude SDK) inside async FastAPI |
| ORM | SQLAlchemy 2.0 async with `create_async_engine` |
| DB column type | Text (not JSONB) for JSON blobs — preserves SQLite test compat |
| Alembic migrations | Manual (not autogenerate) — PostgreSQL unavailable locally |
| Frontend test runner | vitest |
| Python linting | Ruff |
| Temperature for code gen | 0 (deterministic) |
| Temperature for interpretation | Not specified — use 0.3 (low, consistent results) |
| Frontend state | Zustand 5.x; only mode persisted to localStorage |
| API polling | TanStack Query v5 at 2s intervals; use `useEffect` on query data (not `onSuccess`) |
| Chart rendering | react-plotly.js 2.6.x consuming R plotly_json() output |
| Dark theme | slate-950 background, indigo-500 accent |

---

## Sources

### Primary (HIGH confidence)
- Codebase: `backend/app/tasks/analysis.py` — existing Docker subprocess pattern for R execution
- Codebase: `backend/app/services/series_mapper.py` — existing tool_use pattern for Claude API; reuse directly
- Codebase: `backend/app/models/job.py` — existing Job model; Text columns for JSON storage confirmed
- Codebase: `r-sandbox/Dockerfile` — confirmed all required R packages installed: lmtest, sandwich, car, ggplot2, plotly, jsonlite
- Codebase: `frontend/src/components/JobStatusCard.tsx` — confirmed `running_r` and `generating_interpretation` stages already present
- Codebase: `frontend/src/store/analysis.ts` — existing pipelineStage state machine; extension pattern clear
- Codebase: `.planning/phases/03-core-analysis-engine/03-UI-SPEC.md` — component inventory, layout contract, interaction contract, color tokens
- `.planning/STATE.md` — established decisions: Text columns for SQLite compat, manual Alembic migrations, run_in_executor for sync calls, TanStack Query v5 useEffect pattern
- `CLAUDE.md` — stack versions, R package list, execution patterns, compatibility matrix

### Secondary (MEDIUM confidence)
- CLAUDE.md sources section: plotly R roundtrip pattern at https://plotly-r.com/overview.html — pattern is standard but integration details verified against template code
- jsonlite auto_unbox behavior — verified against standard R documentation; behavior is stable across jsonlite versions

### Tertiary (LOW confidence)
- Subprocess stdout buffer size (64KB typical on Linux) — general knowledge; specific behavior depends on Docker bridge network configuration. Mitigated by using `communicate()` which drains buffer.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages pre-installed in R sandbox image, verified from Dockerfile
- Architecture: HIGH — builds directly on confirmed existing patterns from Phase 1+2 code
- R template: HIGH — patterns from standard R documentation; jsonlite/plotly behavior well-documented
- Pitfalls: MEDIUM-HIGH — items 1-3 are well-known R/jsonlite issues; items 4-6 require validation in integration testing
- Frontend: HIGH — UI-SPEC provides precise component and interaction specifications

**Research date:** 2026-03-24
**Valid until:** 2026-04-24 (30 days; stable ecosystem — lmtest, sandwich, plotly are slow-moving)
