# Phase 3: Core Analysis Engine - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-24
**Phase:** 03-core-analysis-engine
**Areas discussed:** Results page layout, R code generation, Error feedback UX, Follow-up suggestions

---

## Results Page Layout

### Section Organization

| Option | Description | Selected |
|--------|-------------|----------|
| Scrollable sections | All sections visible in single scrollable view with anchored headers. Interpretation at top, then coefficients, diagnostics, charts, R code. | ✓ |
| Tabbed sections | Tabs across top, one section visible at a time. Cleaner but requires clicking between sections. | |
| Hybrid: summary + tabs | Interpretation pinned at top, tabs below for details. | |

**User's choice:** Scrollable sections
**Notes:** Best for the "analysis as narrative" feel.

### Diagnostic Test Presentation

| Option | Description | Selected |
|--------|-------------|----------|
| Summary cards | Each diagnostic as compact card with test name, statistic, p-value, pass/warn/fail badge. | ✓ |
| Table format | All diagnostics in a single table. More traditional academic look. | |
| You decide | Claude picks best format. | |

**User's choice:** Summary cards
**Notes:** None

### R Code Visibility

| Option | Description | Selected |
|--------|-------------|----------|
| Collapsed with copy button | Hidden by default behind expander. Copy button visible even when collapsed. | ✓ |
| Always visible | Always shown in syntax-highlighted code block. | |
| You decide | Claude picks. | |

**User's choice:** Collapsed with copy button
**Notes:** None

### Chart Arrangement

| Option | Description | Selected |
|--------|-------------|----------|
| Side-by-side | 2-column grid, falls back to stacked on narrow screens. | ✓ |
| Stacked vertically | Full-width charts, more scrolling. | |
| You decide | Claude picks. | |

**User's choice:** Side-by-side
**Notes:** None

---

## R Code Generation

### R Output Format

| Option | Description | Selected |
|--------|-------------|----------|
| Single JSON to stdout | R outputs one JSON object with all sections. Python parses stdout. | ✓ |
| Multiple files in tmpdir | R writes separate files. Python reads each. | |
| You decide | Claude picks. | |

**User's choice:** Single JSON to stdout
**Notes:** Simple, single contract.

### Data Handoff

| Option | Description | Selected |
|--------|-------------|----------|
| CSV via temp file | Python writes DataFrame to CSV, Docker mounts as read-only, R reads with read.csv(). | ✓ |
| Inline in R script | Data serialized directly into R script. | |
| You decide | Claude picks. | |

**User's choice:** CSV via temp file
**Notes:** Simple and debuggable.

### Code Generation Approach

| Option | Description | Selected |
|--------|-------------|----------|
| Template with Claude filling slots | Base OLS template pre-written. Claude fills dependent var, independent vars, transformations. | ✓ |
| Full script generation | Claude generates complete R script from scratch each time. | |
| You decide | Claude picks. | |

**User's choice:** Template with Claude filling slots
**Notes:** Ensures diagnostics and output format are always correct.

### Interpretation Delivery

| Option | Description | Selected |
|--------|-------------|----------|
| Appear all at once | Wait for full interpretation, then render complete results page. | ✓ |
| Stream in progressively | Stream tokens while showing tables/charts immediately. | |
| You decide | Claude picks. | |

**User's choice:** Appear all at once
**Notes:** No streaming infrastructure needed.

---

## Error Feedback UX

### Error Presentation

| Option | Description | Selected |
|--------|-------------|----------|
| Inline error card replacing results | Error card with plain-English explanation, suggested fix, collapsible raw error. | ✓ |
| Toast notification + retry | Banner at top, prompt stays active. | |
| You decide | Claude picks. | |

**User's choice:** Inline error card replacing results
**Notes:** None

### Error Translation

| Option | Description | Selected |
|--------|-------------|----------|
| Claude translates | Send R stderr to Claude with prompt context. Claude explains and suggests fix. | ✓ |
| Pattern matching + fallback | Regex for common errors, Claude for unknown. | |
| You decide | Claude picks. | |

**User's choice:** Claude translates
**Notes:** Handles novel errors well.

### Error Retry UX

| Option | Description | Selected |
|--------|-------------|----------|
| Pre-fill prompt with suggestion | Claude's suggested fix pre-fills prompt input. User can edit before submitting. | ✓ |
| Just refocus prompt input | Scroll to prompt, user writes own retry. | |
| You decide | Claude picks. | |

**User's choice:** Pre-fill prompt with suggestion
**Notes:** Low friction retry.

---

## Follow-up Suggestions

### Suggestion Presentation

| Option | Description | Selected |
|--------|-------------|----------|
| Clickable chips below results | 2-3 chips at bottom with title and 1-line explanation. | ✓ |
| Inline in interpretation text | Woven into interpretation paragraph. | |
| Sidebar section | Suggestions in left sidebar. | |

**User's choice:** Clickable chips below results
**Notes:** Feels like a conversation.

### Context Awareness

| Option | Description | Selected |
|--------|-------------|----------|
| Reference diagnostics | Claude tailors suggestions based on specific test results. | ✓ |
| Generic suggestions only | Standard follow-ups without referencing results. | |
| You decide | Claude picks. | |

**User's choice:** Reference diagnostics
**Notes:** Makes the app feel intelligent.

### Click Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Pre-fill for review | Pre-fills prompt, scrolls up. User reviews before submitting. | ✓ |
| Run immediately | Triggers analysis right away. | |
| You decide | Claude picks. | |

**User's choice:** Pre-fill for review
**Notes:** User stays in control.

---

## Claude's Discretion

- R template structure and specific R code patterns
- System prompt wording for code generation and interpretation
- Diagnostic test thresholds
- Plotly chart styling
- Coefficient table formatting
- How run_r_analysis task is extended for new patterns

## Deferred Ideas

None — discussion stayed within phase scope
