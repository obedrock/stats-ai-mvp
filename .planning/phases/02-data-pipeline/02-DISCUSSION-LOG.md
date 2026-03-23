# Phase 2: Data Pipeline - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-23
**Phase:** 02-data-pipeline
**Areas discussed:** Prompt parsing & source detection, Frequency mismatch UX, User upload & parsing flow, Data preview & assumptions display

---

## Prompt Parsing & Source Detection

### Ambiguity Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-pick best match | Claude picks most common FRED series, shows what it chose — user can override | ✓ |
| Show candidates first | Present 2-3 candidate series with descriptions, let user pick before fetching | |
| Strict match only | Only proceed if confident — ask user to clarify if ambiguous | |

**User's choice:** Auto-pick best match
**Notes:** None

### FRED Validation Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Validate every ID | Hit FRED /series endpoint for every series ID before fetching | |
| Validate + suggest corrections | Validate, and if invalid, search FRED for similar series names and suggest alternatives | ✓ |
| Trust Claude, validate on failure | Skip pre-validation, only check if fetch fails | |

**User's choice:** Validate + suggest corrections
**Notes:** Addresses STATE.md hallucination concern with active correction

### Data Source Override

| Option | Description | Selected |
|--------|-------------|----------|
| Show source chips, editable | Detected sources as editable chips — click to change source or series ID | ✓ |
| Source dropdown per variable | Full dropdown per variable for FRED, Yahoo, or upload | |
| No override in MVP | Auto-detect only, rephrase prompt if wrong | |

**User's choice:** Show source chips, editable
**Notes:** None

### Multi-Source Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Fetch all in parallel | Detect each variable's source independently, fetch all in parallel, merge after | ✓ |
| Sequential with confirmation | Show detected sources, fetch one at a time with user confirmation | |
| Warn before mixed fetch | Brief notice about multiple sources, then proceed automatically | |

**User's choice:** Fetch all in parallel
**Notes:** Frequency mismatch dialog handles alignment post-fetch

---

## Frequency Mismatch UX

### Resolution Options

| Option | Description | Selected |
|--------|-------------|----------|
| 3 options with recommendation | Aggregate, interpolate, or align — Claude recommends best for analysis type | |
| 2 simple options | Aggregate to lower or interpolate to higher frequency | |
| Auto-resolve with explanation | System picks best method, explains reasoning — user confirms or overrides | ✓ |

**User's choice:** Auto-resolve with explanation
**Notes:** Combined with always-blocking dialog — reduces cognitive load while maintaining transparency

### Dialog Timing

| Option | Description | Selected |
|--------|-------------|----------|
| After fetch, before analysis | Fetch all data first, detect mismatches, show dialog with actual data context | ✓ |
| Before fetch | Detect likely mismatch from metadata, ask before fetching | |
| Inline in data preview | Show mismatch as part of data preview step | |

**User's choice:** After fetch, before analysis
**Notes:** None

### Blocking Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Always block | User MUST choose before proceeding — matches PROJECT.md principle | ✓ |
| Block with timeout default | Block 30s, then proceed with recommended method | |
| Non-blocking notification | Show auto-chosen method, let user undo after | |

**User's choice:** Always block
**Notes:** Aligns with success criterion #3 and core principle

---

## User Upload & Parsing Flow

### Upload Entry Point

| Option | Description | Selected |
|--------|-------------|----------|
| Upload button + drag-drop | Dedicated drag-and-drop area alongside prompt input | ✓ |
| Prompt-triggered upload | Type "use my data" in prompt, system responds with upload dialog | |
| Sidebar data manager | Separate "My Data" section in sidebar | |

**User's choice:** Upload button + drag-drop
**Notes:** None

### Column Mapping Confirmation

| Option | Description | Selected |
|--------|-------------|----------|
| Table preview with editable types | First 5-10 rows, column headers with type/role dropdowns | ✓ |
| Summary card | Compact summary with edit buttons per column | |
| Accept/reject only | Show schema, accept or upload different file | |

**User's choice:** Table preview with editable types
**Notes:** None

### Error Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Inline error with guidance | Specific error with suggestion | |
| Reject and explain | Reject file with explanation | |
| Auto-fix with report | Auto-handle issues, show report of changes | ✓ |

**User's choice:** Auto-fix with report
**Notes:** Don't reject outright — fix and show what changed

---

## Data Preview & Assumptions Display

### Data Preview Presentation

| Option | Description | Selected |
|--------|-------------|----------|
| Expandable panel below prompt | Expandable section with scrollable table, column stats, "Run Analysis" button | ✓ |
| Full-page data view | Separate page with full table and distributions | |
| Modal overlay | Pop-up modal with data table and quick stats | |

**User's choice:** Expandable panel below prompt
**Notes:** None

### Quick Mode Assumptions

| Option | Description | Selected |
|--------|-------------|----------|
| Assumptions banner in results | Collapsible banner at top of results listing assumptions | ✓ |
| Brief pre-run summary | One-line summary with "Proceed" button before running | |
| Inline annotations | Weave assumptions into plain-English interpretation | |

**User's choice:** Assumptions banner in results
**Notes:** None

### Detailed Mode Approval

| Option | Description | Selected |
|--------|-------------|----------|
| Checklist with defaults | Each assumption as togglable checklist item with defaults pre-selected | ✓ |
| Step-by-step wizard | Walk through each variable one at a time | |
| Free-text override | Show defaults, user types corrections | |

**User's choice:** Checklist with defaults
**Notes:** None

### Mode Switching

| Option | Description | Selected |
|--------|-------------|----------|
| Toggle in prompt area | Quick/Detailed toggle near prompt input, persists via preference | ✓ |
| Per-analysis choice | System asks each time before execution | |
| Settings only | Set once in user settings | |

**User's choice:** Toggle in prompt area
**Notes:** Quick is the default

---

## Claude's Discretion

- Specific FRED series ID mapping logic and fallback strategies
- Aggregation methods in frequency mismatch dialog
- Column type auto-detection algorithm for uploads
- Data preview table styling and column stats
- Cache TTL values and eviction strategy
- Redis cache key format

## Deferred Ideas

None — discussion stayed within phase scope
