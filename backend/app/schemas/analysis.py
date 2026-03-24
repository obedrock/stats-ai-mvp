from pydantic import BaseModel, ConfigDict


class AnalysisRunRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    job_id: str          # UUID of the preview_ready job
    prompt: str          # Original user prompt text


class CoefficientRow(BaseModel):
    variable: str
    estimate: float
    std_error: float
    t_stat: float
    p_value: float
    ci_lower: float
    ci_upper: float


class ModelSummary(BaseModel):
    r_squared: float
    adj_r_squared: float
    f_statistic: float
    f_p_value: float
    n_obs: int
    degrees_of_freedom: int


class DiagnosticResult(BaseModel):
    statistic: float
    p_value: float | None = None   # DW p-value can be null
    df: int | None = None          # Only BP has df


class DiagnosticsBundle(BaseModel):
    breusch_pagan: DiagnosticResult
    durbin_watson: DiagnosticResult
    vif: dict[str, float]          # variable_name -> VIF value; empty dict if single predictor
    shapiro_wilk: DiagnosticResult


class ChartData(BaseModel):
    name: str              # "coefficient_plot" or "residual_plot"
    data: list[dict]       # Plotly data array (parsed from R plotly_json)
    layout: dict           # Plotly layout object (parsed from R plotly_json)


class FollowUpSuggestion(BaseModel):
    title: str
    explanation: str
    prompt_text: str


class AnalysisResultResponse(BaseModel):
    """Full successful analysis result returned to frontend."""
    model_config = ConfigDict(from_attributes=True)
    job_id: str
    status: str                              # "success"
    coefficients: list[CoefficientRow]
    model_summary: ModelSummary
    diagnostics: DiagnosticsBundle
    charts: list[ChartData]
    r_code: str                               # The generated R script
    interpretation: str                       # Claude Stage 2 plain-English text
    follow_up_suggestions: list[FollowUpSuggestion]


class AnalysisErrorResponse(BaseModel):
    """Error result when R fails."""
    model_config = ConfigDict(from_attributes=True)
    job_id: str
    status: str                              # "error"
    error_explanation: str                   # Claude plain-English error explanation
    suggested_prompt: str                    # Claude's suggested fix
    r_stderr: str                            # Raw R error output
    r_code: str                              # The R script that failed
