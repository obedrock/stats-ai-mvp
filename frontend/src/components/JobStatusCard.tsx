import { useState, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";
import { cn } from "@/lib/utils";

interface JobStatusResponse {
  id: string;
  status: string;
  stage: string;
  sub_status?: string;
  result_stdout?: string;
  result_stderr?: string;
  error_message?: string;
}

const STAGES = [
  { key: "queued", label: "Job queued" },
  { key: "fetching_data", label: "Fetching data" },
  { key: "running_r", label: "Running analysis" },
  { key: "generating_interpretation", label: "Generating interpretation" },
] as const;

type StageKey = (typeof STAGES)[number]["key"];

function getStageIndex(stage: string): number {
  return STAGES.findIndex((s) => s.key === stage);
}

interface JobStatusCardProps {
  jobId: string;
  onComplete?: () => void;
  onCancel?: () => void;
}

export function JobStatusCard({ jobId, onComplete, onCancel }: JobStatusCardProps) {
  const queryClient = useQueryClient();
  const [elapsed, setElapsed] = useState(0);
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);
  const cancelDismissRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const startTimeRef = useRef(Date.now());

  // Elapsed timer
  useEffect(() => {
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTimeRef.current) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const { data: jobStatus } = useQuery<JobStatusResponse>({
    queryKey: ["job", jobId],
    queryFn: () => apiFetch<JobStatusResponse>(`/jobs/${jobId}`),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (!status || ["success", "error", "cancelled"].includes(status)) return false;
      return 2000;
    },
    enabled: !!jobId,
  });

  // Notify completion
  useEffect(() => {
    if (jobStatus?.status === "success" && onComplete) {
      onComplete();
    }
  }, [jobStatus?.status, onComplete]);

  const cancelMutation = useMutation({
    mutationFn: () => apiFetch<{ status: string }>(`/jobs/${jobId}/cancel`, { method: "POST" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["job", jobId] });
      if (onCancel) onCancel();
    },
  });

  function handleCancelClick() {
    setShowCancelConfirm(true);
    if (cancelDismissRef.current) clearTimeout(cancelDismissRef.current);
    cancelDismissRef.current = setTimeout(() => {
      setShowCancelConfirm(false);
    }, 10000);
  }

  function handleKeepRunning() {
    if (cancelDismissRef.current) clearTimeout(cancelDismissRef.current);
    setShowCancelConfirm(false);
  }

  function handleConfirmCancel() {
    if (cancelDismissRef.current) clearTimeout(cancelDismissRef.current);
    setShowCancelConfirm(false);
    cancelMutation.mutate();
  }

  const currentStageIndex = getStageIndex(jobStatus?.stage ?? "queued");
  const isError = jobStatus?.status === "error";
  const isComplete = jobStatus?.status === "success";
  const isCancelled = jobStatus?.status === "cancelled";
  const isTerminal = isError || isComplete || isCancelled;

  return (
    <Card
      className={cn(
        "bg-slate-800 border-slate-700",
        isError && "border-red-500"
      )}
    >
      <CardContent className="pt-6 space-y-6">
        {/* Step progress row */}
        <div className="flex items-start gap-0">
          {STAGES.map((stage, index) => {
            const isDone = currentStageIndex > index;
            const isCurrent = currentStageIndex === index && !isTerminal;
            const isPending = currentStageIndex < index || (isTerminal && !isDone);

            return (
              <div key={stage.key} className="flex-1 flex flex-col items-center gap-2">
                <div className="flex items-center w-full">
                  {/* Leading connector */}
                  {index > 0 && (
                    <div
                      className={cn(
                        "flex-1 h-0.5",
                        isDone || isCurrent ? "bg-indigo-500" : "bg-slate-700"
                      )}
                    />
                  )}

                  {/* Dot */}
                  <div
                    className={cn(
                      "w-3 h-3 rounded-full shrink-0",
                      isDone && "bg-indigo-500",
                      isCurrent && "bg-indigo-500 animate-pulse",
                      isPending && !isDone && !isCurrent && "bg-slate-600"
                    )}
                  />

                  {/* Trailing connector */}
                  {index < STAGES.length - 1 && (
                    <div
                      className={cn(
                        "flex-1 h-0.5",
                        isDone ? "bg-indigo-500" : "bg-slate-700"
                      )}
                    />
                  )}
                </div>

                {/* Step label */}
                <span
                  className={cn(
                    "text-[12px] text-center leading-tight px-1",
                    isCurrent && "text-slate-100",
                    isDone && "text-slate-100",
                    isPending && !isDone && !isCurrent && "text-slate-400"
                  )}
                >
                  {stage.label}
                </span>
              </div>
            );
          })}
        </div>

        {/* Sub-status line during fetching_data stage */}
        {jobStatus?.stage === "fetching_data" && jobStatus.sub_status && (
          <span className="text-[12px] text-slate-400">{jobStatus.sub_status}</span>
        )}

        {/* Elapsed time */}
        <div className="text-xs text-slate-400">
          Elapsed: {elapsed}s
        </div>

        {/* Terminal states */}
        {isComplete && (
          <div className="text-sm text-slate-100">Done</div>
        )}

        {isCancelled && (
          <div className="text-sm text-slate-400">Job cancelled.</div>
        )}

        {isError && (
          <div className="space-y-2">
            <p className="text-sm text-red-400">
              {jobStatus?.error_message ?? "Something went wrong. Please try again in a moment."}
            </p>
            <button
              onClick={onCancel}
              className="text-xs text-indigo-400 hover:text-indigo-300 underline"
            >
              Try again
            </button>
          </div>
        )}

        {/* Cancel area (only shown when not terminal) */}
        {!isTerminal && (
          <div className="flex justify-end">
            {showCancelConfirm ? (
              <div className="flex flex-col items-end gap-2">
                <p className="text-xs text-slate-300">
                  Are you sure? This will stop the running analysis.
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleKeepRunning}
                    className="text-slate-400 hover:text-slate-100"
                  >
                    Keep running
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={handleConfirmCancel}
                    disabled={cancelMutation.isPending}
                  >
                    Yes, cancel
                  </Button>
                </div>
              </div>
            ) : (
              <Button
                variant="destructive"
                size="sm"
                onClick={handleCancelClick}
              >
                Cancel Job
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Re-export stage keys for type safety
export type { StageKey };
