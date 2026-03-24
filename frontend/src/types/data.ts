// Types mirroring backend/app/schemas/data.py

export interface ParsedSource {
  source: "FRED" | "YAHOO";
  series_id: string;
  display_name: string;
  rationale: string;
  valid: boolean | null;
  suggestions: Array<{ id: string; name: string }>;
}

export interface PromptParseResponse {
  sources: ParsedSource[];
  date_range: { start: string; end: string } | null;
}

export interface SourceOverride {
  index: number;
  series_id: string;
  source: "FRED" | "YAHOO";
}

export interface FrequencyInfo {
  series_id: string;
  frequency: string;
  row_count: number;
}

export interface FrequencyConflict {
  has_conflict: boolean;
  series_frequencies: FrequencyInfo[];
  recommendation: string;
  recommended_method: string;
  target_frequency: string;
}

export interface ResolutionChoice {
  method: "mean" | "last" | "sum" | "ffill" | "abort";
  target_frequency: string;
}

export interface ColumnStat {
  name: string;
  dtype: string;
  min: number | null;
  max: number | null;
  mean: number | null;
  missing_count: number;
}

export interface DataPreview {
  rows: Record<string, unknown>[];
  total_rows: number;
  columns: ColumnStat[];
  assumptions: string[];
  cache_keys: string[];
}

export interface ColumnInfo {
  name: string;
  detected_type: "numeric" | "date" | "text" | "category";
  role: "dependent" | "independent" | "date_index" | "ignore" | null;
}

export interface UploadResult {
  preview: Record<string, unknown>[];
  columns: ColumnInfo[];
  changes: string[];
  total_rows: number;
}

export interface AssumptionItem {
  key: string;
  label: string;
  recommended: boolean;
  confirmed: boolean | null;
}

export type AnalysisMode = "quick" | "detailed";
