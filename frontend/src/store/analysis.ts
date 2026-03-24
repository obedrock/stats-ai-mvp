import { create } from "zustand";
import { persist } from "zustand/middleware";
import type {
  ParsedSource,
  FrequencyConflict,
  ResolutionChoice,
  DataPreview,
  UploadResult,
  AssumptionItem,
  AnalysisMode,
} from "@/types/data";

interface AnalysisState {
  // Prompt
  prompt: string;
  setPrompt: (p: string) => void;

  // Sources (from Claude parsing)
  sources: ParsedSource[];
  setSources: (s: ParsedSource[]) => void;
  updateSource: (index: number, update: Partial<ParsedSource>) => void;
  removeSource: (index: number) => void;

  // Mode (persisted to localStorage)
  mode: AnalysisMode;
  setMode: (m: AnalysisMode) => void;

  // Frequency conflict
  frequencyConflict: FrequencyConflict | null;
  setFrequencyConflict: (fc: FrequencyConflict | null) => void;
  resolution: ResolutionChoice | null;
  setResolution: (r: ResolutionChoice | null) => void;

  // Data preview
  preview: DataPreview | null;
  setPreview: (p: DataPreview | null) => void;

  // Upload
  uploadResult: UploadResult | null;
  setUploadResult: (u: UploadResult | null) => void;

  // Assumptions
  assumptions: AssumptionItem[];
  setAssumptions: (a: AssumptionItem[]) => void;
  toggleAssumption: (key: string) => void;

  // Job tracking
  jobId: string | null;
  setJobId: (id: string | null) => void;

  // Pipeline stage for UI
  pipelineStage: "idle" | "parsing" | "confirming_sources" | "fetching" | "frequency_conflict" | "confirming_assumptions" | "preview_ready";
  setPipelineStage: (s: AnalysisState["pipelineStage"]) => void;

  // Reset
  reset: () => void;
}

const initialState = {
  prompt: "",
  sources: [] as ParsedSource[],
  frequencyConflict: null as FrequencyConflict | null,
  resolution: null as ResolutionChoice | null,
  preview: null as DataPreview | null,
  uploadResult: null as UploadResult | null,
  assumptions: [] as AssumptionItem[],
  jobId: null as string | null,
  pipelineStage: "idle" as const,
};

export const useAnalysisStore = create<AnalysisState>()(
  persist(
    (set) => ({
      ...initialState,
      mode: "quick",

      setPrompt: (prompt) => set({ prompt }),
      setSources: (sources) => set({ sources }),
      updateSource: (index, update) =>
        set((state) => ({
          sources: state.sources.map((s, i) =>
            i === index ? { ...s, ...update } : s
          ),
        })),
      removeSource: (index) =>
        set((state) => ({
          sources: state.sources.filter((_, i) => i !== index),
        })),
      setMode: (mode) => set({ mode }),
      setFrequencyConflict: (frequencyConflict) => set({ frequencyConflict }),
      setResolution: (resolution) => set({ resolution }),
      setPreview: (preview) => set({ preview }),
      setUploadResult: (uploadResult) => set({ uploadResult }),
      setAssumptions: (assumptions) => set({ assumptions }),
      toggleAssumption: (key) =>
        set((state) => ({
          assumptions: state.assumptions.map((a) =>
            a.key === key ? { ...a, confirmed: !(a.confirmed ?? a.recommended) } : a
          ),
        })),
      setJobId: (jobId) => set({ jobId }),
      setPipelineStage: (pipelineStage) => set({ pipelineStage }),
      reset: () => set(initialState),
    }),
    {
      name: "stats-ai:analysis-mode",
      partialize: (state) => ({ mode: state.mode }),
    }
  )
);
