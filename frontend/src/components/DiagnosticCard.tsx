import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

type Verdict = "PASS" | "WARN" | "FAIL";

interface DiagnosticCardProps {
  name: string;
  statistic: number;
  pValue: number | null;
  verdict: Verdict;
}

const badgeClasses: Record<Verdict, string> = {
  PASS: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  WARN: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  FAIL: "bg-red-500/20 text-red-400 border-red-500/30",
};

export function DiagnosticCard({
  name,
  statistic,
  pValue,
  verdict,
}: DiagnosticCardProps) {
  return (
    <Card className="bg-slate-800 border-slate-700 flex-1 min-w-[140px]">
      <CardContent className="pt-4 pb-4 px-4 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">{name}</span>
          <Badge className={badgeClasses[verdict]}>{verdict}</Badge>
        </div>
        <p className="text-sm font-medium text-foreground">
          {statistic != null ? statistic.toFixed(4) : "N/A"}
        </p>
        <p className="text-xs text-muted-foreground">
          p = {pValue != null ? pValue.toFixed(4) : "---"}
        </p>
      </CardContent>
    </Card>
  );
}
