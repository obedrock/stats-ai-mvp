import * as React from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { CoefficientRow, ModelSummary } from "@/types/analysis";

interface CoefficientTableProps {
  coefficients: CoefficientRow[];
  modelSummary: ModelSummary;
}

function sigStars(p: number): string {
  if (p < 0.001) return "***";
  if (p < 0.01) return "**";
  if (p < 0.05) return "*";
  return "";
}

export function CoefficientTable({
  coefficients,
  modelSummary,
}: CoefficientTableProps) {
  const [sortByP, setSortByP] = React.useState(false);
  const sorted = sortByP
    ? [...coefficients].sort((a, b) => a.p_value - b.p_value)
    : coefficients;

  return (
    <section id="coefficients">
      <div className="border border-slate-700 rounded-lg overflow-hidden">
        <div className="flex items-center justify-between px-4 pt-6 pb-3">
          <h2 className="text-base font-semibold text-foreground">
            Coefficients
          </h2>
          <button
            onClick={() => setSortByP(!sortByP)}
            className="text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            {sortByP ? "Original order" : "Sort by p-value"}
          </button>
        </div>
        <Table>
          <TableHeader>
            <TableRow className="border-slate-700">
              <TableHead className="text-xs text-muted-foreground">
                Variable
              </TableHead>
              <TableHead className="text-xs text-muted-foreground text-right">
                Coef
              </TableHead>
              <TableHead className="text-xs text-muted-foreground text-right">
                Std Err
              </TableHead>
              <TableHead className="text-xs text-muted-foreground text-right">
                t-stat
              </TableHead>
              <TableHead className="text-xs text-muted-foreground text-right">
                p-value
              </TableHead>
              <TableHead className="text-xs text-muted-foreground text-right">
                95% CI
              </TableHead>
              <TableHead className="text-xs text-muted-foreground text-right">
                Sig
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sorted.map((row) => (
              <TableRow key={row.variable} className="border-slate-700">
                <TableCell className="text-sm font-medium py-2">
                  {row.variable}
                </TableCell>
                <TableCell className="text-sm text-right py-2">
                  {row.estimate.toFixed(4)}
                </TableCell>
                <TableCell className="text-sm text-right py-2">
                  {row.std_error.toFixed(4)}
                </TableCell>
                <TableCell className="text-sm text-right py-2">
                  {row.t_stat.toFixed(3)}
                </TableCell>
                <TableCell className="text-sm text-right py-2">
                  {row.p_value.toFixed(4)}
                </TableCell>
                <TableCell className="text-sm text-right py-2">
                  [{row.ci_lower.toFixed(3)}, {row.ci_upper.toFixed(3)}]
                </TableCell>
                <TableCell className="text-sm text-right py-2 font-mono">
                  {sigStars(row.p_value)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {/* Model summary footer */}
        <div className="px-4 py-3 border-t border-slate-700 flex flex-wrap gap-4 text-xs text-muted-foreground">
          <span>R² = {modelSummary.r_squared.toFixed(4)}</span>
          <span>Adj R² = {modelSummary.adj_r_squared.toFixed(4)}</span>
          <span>
            F = {modelSummary.f_statistic.toFixed(2)} (p ={" "}
            {modelSummary.f_p_value.toFixed(4)})
          </span>
          <span>N = {modelSummary.n_obs}</span>
          <span>df = {modelSummary.degrees_of_freedom}</span>
        </div>
      </div>
    </section>
  );
}
