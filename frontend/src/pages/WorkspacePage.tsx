import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import { JobStatusCard } from "@/components/JobStatusCard";
import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";

interface JobCreateResponse {
  id: string;
  status: string;
}

export default function WorkspacePage() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleTestJob() {
    setSubmitting(true);
    try {
      const job = await apiFetch<JobCreateResponse>("/jobs/", {
        method: "POST",
        body: JSON.stringify({ r_script: "cat('hello from R')" }),
      });
      setJobId(job.id);
    } catch {
      // ignore errors in smoke test button
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AppShell>
      <div className="flex flex-col items-center justify-center h-full gap-8">
        {jobId ? (
          <div className="w-full max-w-2xl">
            <JobStatusCard
              jobId={jobId}
              onComplete={() => setJobId(null)}
              onCancel={() => setJobId(null)}
            />
          </div>
        ) : (
          <>
            <div className="text-center space-y-3">
              <h1 className="text-xl font-semibold text-slate-100">
                Ready when you are
              </h1>
              <p className="text-sm text-slate-400 max-w-md">
                Describe what you want to analyse and Stats-AI will fetch the data, run the stats, and explain the results.
              </p>
            </div>

            {import.meta.env.DEV && (
              <Button
                onClick={handleTestJob}
                disabled={submitting}
                variant="outline"
                className="border-slate-600 text-slate-300 hover:bg-slate-800"
              >
                {submitting ? "Submitting…" : "Test Job (dev only)"}
              </Button>
            )}
          </>
        )}
      </div>
    </AppShell>
  );
}
