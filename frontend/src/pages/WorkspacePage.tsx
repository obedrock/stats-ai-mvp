import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/AppShell";
import { JobStatusCard } from "@/components/JobStatusCard";
import { PromptInput } from "@/components/PromptInput";
import { SourceChip } from "@/components/SourceChip";
import { UploadDropzone } from "@/components/UploadDropzone";
import { ColumnMappingTable } from "@/components/ColumnMappingTable";
import { FrequencyMismatchDialog } from "@/components/FrequencyMismatchDialog";
import { QuickDetailedToggle } from "@/components/QuickDetailedToggle";
import { DataPreviewPanel } from "@/components/DataPreviewPanel";
import { AssumptionsBanner } from "@/components/AssumptionsBanner";
import { AssumptionsChecklist } from "@/components/AssumptionsChecklist";
import { apiFetch } from "@/lib/api";
import { useAnalysisStore } from "@/store/analysis";
import type {
  PromptParseResponse,
  UploadResult,
  FrequencyConflict,
  DataPreview,
  ResolutionChoice,
  AssumptionItem,
  ParsedSource,
} from "@/types/data";
import type { ColumnMapping } from "@/components/ColumnMappingTable";

// Shape returned by /data/fetch and /data/resolve-frequency
interface JobCreatedResponse {
  id: string;
  status: string;
}

// Shape returned by /data/preview/{job_id}
// Can be FrequencyConflict, DataPreview, or a status object
interface PreviewStatusResponse {
  status?: string;
  stage?: string;
  sub_status?: string;
  // FrequencyConflict fields
  has_conflict?: boolean;
  series_frequencies?: FrequencyConflict["series_frequencies"];
  recommendation?: string;
  recommended_method?: string;
  target_frequency?: string;
  // DataPreview fields
  rows?: DataPreview["rows"];
  total_rows?: number;
  columns?: DataPreview["columns"];
  assumptions?: string[];
  cache_keys?: string[];
}

export default function WorkspacePage() {
  const {
    sources,
    mode,
    frequencyConflict,
    preview,
    uploadResult,
    assumptions,
    jobId,
    pipelineStage,
    setSources,
    updateSource,
    removeSource,
    setFrequencyConflict,
    setResolution,
    setPreview,
    setUploadResult,
    setAssumptions,
    setPipelineStage,
    setJobId,
    reset,
  } = useAnalysisStore();

  const [dateRange, setDateRange] = React.useState<{ start: string; end: string } | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  // Poll /data/preview/{jobId} when we're in "fetching" stage
  const { data: previewPollData } = useQuery<PreviewStatusResponse>({
    queryKey: ["preview", jobId],
    queryFn: () => apiFetch<PreviewStatusResponse>(`/data/preview/${jobId}`),
    enabled: !!jobId && pipelineStage === "fetching",
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return 2000;
      // Stop polling once we get a terminal result
      if (data.has_conflict !== undefined) return false; // FrequencyConflict
      if (data.rows !== undefined) return false;          // DataPreview
      return 2000;
    },
  });

  // Handle preview poll results
  React.useEffect(() => {
    if (!previewPollData || pipelineStage !== "fetching") return;

    // Frequency conflict
    if (previewPollData.has_conflict !== undefined && previewPollData.series_frequencies) {
      setFrequencyConflict({
        has_conflict: previewPollData.has_conflict,
        series_frequencies: previewPollData.series_frequencies,
        recommendation: previewPollData.recommendation ?? "",
        recommended_method: previewPollData.recommended_method ?? "mean",
        target_frequency: previewPollData.target_frequency ?? "",
      });
      setPipelineStage("frequency_conflict");
      return;
    }
    // Data ready
    if (previewPollData.rows !== undefined && previewPollData.columns !== undefined) {
      setPreview({
        rows: previewPollData.rows,
        total_rows: previewPollData.total_rows ?? 0,
        columns: previewPollData.columns,
        assumptions: previewPollData.assumptions ?? [],
        cache_keys: previewPollData.cache_keys ?? [],
      });
      setPipelineStage("preview_ready");
    }
  }, [previewPollData, pipelineStage, setFrequencyConflict, setPreview, setPipelineStage]);

  // ---- Helpers ----

  function buildPrefetchAssumptions(srcs: ParsedSource[]): AssumptionItem[] {
    const items: AssumptionItem[] = [];
    for (const src of srcs) {
      if (src.source === "FRED") {
        items.push({
          key: `log_${src.series_id}`,
          label: `Log-transform ${src.display_name} (${src.series_id})`,
          recommended: true,
          confirmed: null,
        });
        items.push({
          key: `pct_${src.series_id}`,
          label: `Express ${src.display_name} as % change`,
          recommended: false,
          confirmed: null,
        });
      }
      if (src.source === "YAHOO") {
        items.push({
          key: `log_${src.series_id}`,
          label: `Log-transform ${src.display_name} price`,
          recommended: false,
          confirmed: null,
        });
        items.push({
          key: `returns_${src.series_id}`,
          label: `Use returns instead of price levels for ${src.display_name}`,
          recommended: true,
          confirmed: null,
        });
      }
    }
    // Common multi-source assumption
    if (srcs.length > 1) {
      items.push({
        key: "lag_1",
        label: "Include 1-period lag for independent variables",
        recommended: false,
        confirmed: null,
      });
    }
    return items;
  }

  // ---- Handlers ----

  async function handlePromptSubmit(promptText: string) {
    setError(null);
    setPipelineStage("parsing");
    try {
      const response = await apiFetch<PromptParseResponse>("/data/parse-prompt", {
        method: "POST",
        body: JSON.stringify({ prompt: promptText, mode }),
      });
      setSources(response.sources);
      setDateRange(response.date_range);
      setPipelineStage("confirming_sources");
      // Populate pre-fetch assumptions for detailed mode
      if (mode === "detailed") {
        const prefetchAssumptions = buildPrefetchAssumptions(response.sources);
        setAssumptions(prefetchAssumptions);
      }
    } catch (err: unknown) {
      console.error("parse-prompt failed:", err);
      let message = "Could not parse your prompt. Please try again.";
      if (err instanceof TypeError) {
        message = `Cannot reach backend: ${err.message}`;
      } else if (err && typeof err === "object" && "detail" in err) {
        message = String((err as { detail: unknown }).detail);
      } else if (err && typeof err === "object" && "status" in err) {
        message = `Request failed (${(err as { status: number }).status}). Check the console for details.`;
      }
      setError(message);
      setPipelineStage("idle");
    }
  }

  async function handleSourceOverride(index: number, newSeriesId: string) {
    try {
      const source = sources[index];
      const result = await apiFetch<{
        source: "FRED" | "YAHOO";
        series_id: string;
        display_name: string;
        rationale: string;
        valid: boolean;
        suggestions: Array<{ id: string; name: string }>;
      }>("/data/parse-prompt/override", {
        method: "POST",
        body: JSON.stringify({
          index,
          series_id: newSeriesId,
          source: source.source,
        }),
      });
      updateSource(index, result);
    } catch {
      // Ignore override errors — chip stays in error state
    }
  }

  async function handleFetchData() {
    setError(null);
    try {
      const response = await apiFetch<JobCreatedResponse>("/data/fetch", {
        method: "POST",
        body: JSON.stringify({
          sources,
          date_range: dateRange,
          mode,
        }),
      });
      setJobId(response.id);
      setPipelineStage("fetching");
    } catch {
      setError("Could not start data fetch. Please try again.");
    }
  }

  async function handleFrequencyConfirm(choice: ResolutionChoice) {
    setResolution(choice);
    setFrequencyConflict(null);
    if (!jobId) return;
    try {
      const response = await apiFetch<JobCreatedResponse>(
        `/data/resolve-frequency?job_id=${jobId}`,
        {
          method: "POST",
          body: JSON.stringify(choice),
        }
      );
      setJobId(response.id);
      setPipelineStage("fetching");
    } catch {
      setError("Could not submit frequency resolution. Please try again.");
      setPipelineStage("confirming_sources");
    }
  }

  function handleFrequencyCancel() {
    reset();
  }

  function handleUpload(result: UploadResult) {
    setUploadResult(result);
  }

  async function handleConfirmMapping(columns: ColumnMapping[]) {
    try {
      await apiFetch("/data/upload/confirm-mapping", {
        method: "POST",
        body: JSON.stringify({ columns }),
      });
    } catch {
      // Non-blocking; mapping stored client-side for now
    }
    // Keep uploadResult in store; user can proceed to fetch with upload data
  }

  function handleRunAnalysis() {
    // Phase 3 wiring: to be implemented
  }

  function handleAssumptionsConfirm() {
    setPipelineStage("confirming_sources");
  }

  const isParsingOrFetching =
    pipelineStage === "parsing" || pipelineStage === "fetching";

  // ---- Layout ----

  return (
    <AppShell>
      <div className="flex flex-col gap-6 max-w-3xl mx-auto w-full">

        {/* FrequencyMismatchDialog (modal overlay) */}
        {pipelineStage === "frequency_conflict" && frequencyConflict && (
          <FrequencyMismatchDialog
            conflict={frequencyConflict}
            onConfirm={handleFrequencyConfirm}
            onCancel={handleFrequencyCancel}
          />
        )}

        {/* Mode toggle */}
        <div className="flex items-center justify-between">
          <QuickDetailedToggle />
        </div>

        {/* Error message */}
        {error && (
          <p className="text-sm text-destructive" role="alert">
            {error}
          </p>
        )}

        {/* Idle: empty state + prompt */}
        {pipelineStage === "idle" && (
          <div className="flex flex-col gap-8">
            <div className="text-center space-y-3">
              <h1 className="text-xl font-semibold text-slate-100">
                Ready when you are
              </h1>
              <p className="text-sm text-slate-400 max-w-md mx-auto">
                Describe what you want to analyse and Stats-AI will fetch the data, run the stats, and explain the results.
              </p>
            </div>

            <PromptInput
              onSubmit={handlePromptSubmit}
              disabled={false}
            />

            <UploadDropzone onUpload={handleUpload} />

            {uploadResult && (
              <ColumnMappingTable
                result={uploadResult}
                onConfirm={handleConfirmMapping}
              />
            )}
          </div>
        )}

        {/* Parsing stage */}
        {pipelineStage === "parsing" && (
          <div className="flex flex-col gap-6">
            <PromptInput
              onSubmit={handlePromptSubmit}
              disabled={true}
            />
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <div className="size-4 animate-spin rounded-full border-2 border-accent border-t-transparent" />
              <span>Detecting data sources...</span>
            </div>
          </div>
        )}

        {/* Confirming sources stage */}
        {pipelineStage === "confirming_sources" && (
          <div className="flex flex-col gap-6">
            <PromptInput
              onSubmit={handlePromptSubmit}
              disabled={isParsingOrFetching}
            />

            {sources.length > 0 && (
              <div className="flex flex-col gap-3">
                <p className="text-sm text-muted-foreground">Detected sources — review and edit before fetching:</p>
                <div className="flex flex-wrap gap-2">
                  {sources.map((source, index) => (
                    <SourceChip
                      key={`${source.source}-${source.series_id}-${index}`}
                      source={source}
                      index={index}
                      onOverride={handleSourceOverride}
                      onRemove={removeSource}
                    />
                  ))}
                </div>

                {/* Detailed mode: show AssumptionsChecklist before fetch */}
                {mode === "detailed" && assumptions.length > 0 ? (
                  <AssumptionsChecklist
                    items={assumptions}
                    onToggle={useAnalysisStore.getState().toggleAssumption}
                    onConfirm={handleAssumptionsConfirm}
                  />
                ) : (
                  <div className="flex justify-end">
                    <button
                      onClick={handleFetchData}
                      disabled={sources.length === 0}
                      className="inline-flex items-center justify-center rounded-md bg-accent text-accent-foreground hover:bg-accent/90 min-h-[44px] px-5 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Fetch Data
                    </button>
                  </div>
                )}
              </div>
            )}

            {uploadResult && (
              <ColumnMappingTable
                result={uploadResult}
                onConfirm={handleConfirmMapping}
              />
            )}
          </div>
        )}

        {/* Confirming assumptions (detailed mode) */}
        {pipelineStage === "confirming_assumptions" && (
          <div className="flex flex-col gap-6">
            <AssumptionsChecklist
              items={assumptions}
              onToggle={useAnalysisStore.getState().toggleAssumption}
              onConfirm={handleAssumptionsConfirm}
            />
          </div>
        )}

        {/* Fetching stage */}
        {pipelineStage === "fetching" && jobId && (
          <div className="flex flex-col gap-4">
            <JobStatusCard
              jobId={jobId}
              onComplete={() => {
                // Preview polling handles transition to preview_ready
              }}
              onCancel={() => reset()}
            />
          </div>
        )}

        {/* Preview ready stage */}
        {pipelineStage === "preview_ready" && preview && (
          <div className="flex flex-col gap-4">
            {/* Assumptions banner (quick mode) */}
            {mode === "quick" && preview.assumptions.length > 0 && (
              <AssumptionsBanner assumptions={preview.assumptions} />
            )}

            <DataPreviewPanel
              preview={preview}
              onRunAnalysis={handleRunAnalysis}
            />
          </div>
        )}
      </div>
    </AppShell>
  );
}
