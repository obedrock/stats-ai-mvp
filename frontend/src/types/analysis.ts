// TODO: Replace unknown[] and Record<string, unknown> with Plotly.Data[] and
// Partial<Plotly.Layout> once react-plotly.js and @types/plotly.js are installed in Plan 04.

export interface CoefficientRow {
  variable: string;
  estimate: number;
  std_error: number;
  t_stat: number;
  p_value: number;
  ci_lower: number;
  ci_upper: number;
}

export interface ModelSummary {
  r_squared: number;
  adj_r_squared: number;
  f_statistic: number;
  f_p_value: number;
  n_obs: number;
  degrees_of_freedom: number;
}

export interface DiagnosticResult {
  statistic: number;
  p_value: number | null;
  df?: number | null;
}

export interface DiagnosticsBundle {
  breusch_pagan: DiagnosticResult;
  durbin_watson: DiagnosticResult;
  vif: Record<string, number>;
  shapiro_wilk: DiagnosticResult;
}

export interface ChartData {
  name: string;
  data: unknown[];
  layout: Record<string, unknown>;
}

export interface FollowUpSuggestion {
  title: string;
  explanation: string;
  prompt_text: string;
}

export interface AnalysisResult {
  job_id: string;
  status: "success";
  coefficients: CoefficientRow[];
  model_summary: ModelSummary;
  diagnostics: DiagnosticsBundle;
  charts: ChartData[];
  r_code: string;
  interpretation: string;
  follow_up_suggestions: FollowUpSuggestion[];
}

export interface AnalysisError {
  job_id: string;
  status: "error";
  error_explanation: string;
  suggested_prompt: string;
  r_stderr: string;
  r_code: string;
}

export type AnalysisResponse = AnalysisResult | AnalysisError;
