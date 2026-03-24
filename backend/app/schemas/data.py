from typing import Optional

from pydantic import BaseModel, Field


# --- Prompt Parsing ---

class PromptSubmit(BaseModel):
    """User submits a natural language analysis prompt."""
    prompt: str = Field(..., min_length=5, max_length=2000)
    mode: str = Field(default="quick", pattern="^(quick|detailed)$")


class ParsedSource(BaseModel):
    """A data source detected from the user's prompt by Claude."""
    source: str = Field(..., pattern="^(FRED|YAHOO)$")
    series_id: str
    display_name: str
    rationale: str
    valid: Optional[bool] = None  # None = not yet validated
    suggestions: list[dict] = Field(default_factory=list)  # [{id, name}] if invalid


class PromptParseResponse(BaseModel):
    """Response from the prompt parsing endpoint."""
    sources: list[ParsedSource]
    date_range: Optional[dict] = None  # {start: str, end: str}


class SourceOverride(BaseModel):
    """User overrides a detected source's series ID."""
    index: int  # Which source in the array to override
    series_id: str
    source: str = Field(..., pattern="^(FRED|YAHOO)$")  # Source type for validation routing


# --- Frequency Resolution ---

class FrequencyInfo(BaseModel):
    """Frequency metadata for a single series."""
    series_id: str
    frequency: str  # "D" (daily), "QS" (quarterly), "MS" (monthly), "irregular"
    row_count: int


class FrequencyConflict(BaseModel):
    """Returned when fetched series have different frequencies."""
    has_conflict: bool
    series_frequencies: list[FrequencyInfo]
    recommendation: str  # e.g., "Aggregate AAPL to quarterly via mean"
    recommended_method: str  # "mean", "last", "sum", "ffill"
    target_frequency: str  # Target freq code: "QS", "MS", "D"


class ResolutionChoice(BaseModel):
    """User's chosen resolution for frequency mismatch."""
    method: str = Field(..., pattern="^(mean|last|sum|ffill|abort)$")
    target_frequency: str


# --- Data Preview ---

class ColumnStat(BaseModel):
    """Per-column statistics for data preview."""
    name: str
    dtype: str
    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    missing_count: int = 0


class DataPreview(BaseModel):
    """Preview of cleaned/merged dataset."""
    rows: list[dict]  # First 50 rows as records
    total_rows: int
    columns: list[ColumnStat]
    assumptions: list[str]  # List of assumption strings
    cache_keys: list[str]  # Redis keys used for this data


# --- File Upload ---

class ColumnInfo(BaseModel):
    """Auto-detected column info from uploaded file."""
    name: str
    detected_type: str  # "numeric", "date", "text", "category"
    role: Optional[str] = None  # "dependent", "independent", "date_index", "ignore"


class ColumnMapping(BaseModel):
    """User-confirmed column mapping override."""
    name: str
    type: str = Field(..., pattern="^(numeric|date|text|category)$")
    role: str = Field(..., pattern="^(dependent|independent|date_index|ignore)$")


class UploadResult(BaseModel):
    """Result from file upload parsing."""
    preview: list[dict]  # First 10 rows as records
    columns: list[ColumnInfo]
    changes: list[str]  # Auto-fix report strings
    total_rows: int


class ConfirmMapping(BaseModel):
    """User confirms column mappings for uploaded file."""
    columns: list[ColumnMapping]


# --- Assumptions ---

class AssumptionItem(BaseModel):
    """A single assumption in detailed mode."""
    key: str  # e.g., "log_transform_gdp"
    label: str  # e.g., "Log-transform GDP"
    recommended: bool  # Pre-selected default
    confirmed: Optional[bool] = None  # User's choice (detailed mode)


class AssumptionsConfirm(BaseModel):
    """User confirms assumptions in detailed mode."""
    items: list[AssumptionItem]


# --- Fetch Job ---

class FetchRequest(BaseModel):
    """Request to start data fetching after source confirmation."""
    job_id: str
    sources: list[ParsedSource]
    date_range: dict  # {start: str, end: str}
    mode: str = Field(default="quick", pattern="^(quick|detailed)$")
    resolution: Optional[ResolutionChoice] = None  # If frequency conflict was resolved
    assumptions: Optional[list[AssumptionItem]] = None  # If detailed mode confirmed
