import type { DiagnosticsBundle } from "@/types/analysis";
import { DiagnosticCard } from "./DiagnosticCard";

type Verdict = "PASS" | "WARN" | "FAIL";

function bpVerdict(p: number | null): Verdict {
  if (p === null) return "WARN";
  if (p > 0.05) return "PASS";
  if (p >= 0.01) return "WARN";
  return "FAIL";
}

function dwVerdict(stat: number): Verdict {
  if (stat >= 1.5 && stat <= 2.5) return "PASS";
  if ((stat >= 1.0 && stat < 1.5) || (stat > 2.5 && stat <= 3.0)) return "WARN";
  return "FAIL";
}

function vifVerdict(vif: Record<string, number>): Verdict {
  const vals = Object.values(vif);
  if (vals.length === 0) return "PASS";
  const maxVif = Math.max(...vals);
  if (maxVif < 5) return "PASS";
  if (maxVif <= 10) return "WARN";
  return "FAIL";
}

function swVerdict(p: number | null): Verdict {
  if (p === null) return "WARN";
  if (p > 0.05) return "PASS";
  if (p >= 0.01) return "WARN";
  return "FAIL";
}

interface DiagnosticsRowProps {
  diagnostics: DiagnosticsBundle;
}

export function DiagnosticsRow({ diagnostics }: DiagnosticsRowProps) {
  const maxVif =
    Object.values(diagnostics.vif).length > 0
      ? Math.max(...Object.values(diagnostics.vif))
      : 0;

  return (
    <section id="diagnostics">
      <h2 className="text-base font-semibold text-foreground mb-3">
        Diagnostics
      </h2>
      <div className="flex flex-wrap gap-3">
        <DiagnosticCard
          name="Breusch-Pagan"
          statistic={diagnostics.breusch_pagan.statistic}
          pValue={diagnostics.breusch_pagan.p_value}
          verdict={bpVerdict(diagnostics.breusch_pagan.p_value)}
        />
        <DiagnosticCard
          name="Durbin-Watson"
          statistic={diagnostics.durbin_watson.statistic}
          pValue={diagnostics.durbin_watson.p_value}
          verdict={dwVerdict(diagnostics.durbin_watson.statistic)}
        />
        <DiagnosticCard
          name="VIF (max)"
          statistic={maxVif}
          pValue={null}
          verdict={vifVerdict(diagnostics.vif)}
        />
        <DiagnosticCard
          name="Shapiro-Wilk"
          statistic={diagnostics.shapiro_wilk.statistic}
          pValue={diagnostics.shapiro_wilk.p_value}
          verdict={swVerdict(diagnostics.shapiro_wilk.p_value)}
        />
      </div>
    </section>
  );
}
