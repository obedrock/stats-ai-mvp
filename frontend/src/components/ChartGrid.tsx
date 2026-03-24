import { lazy, Suspense } from "react";
import type { ChartData } from "@/types/analysis";

// Lazy-load plotly to avoid CJS/ESM interop issues in production builds.
// react-plotly.js's default entry wires factory + plotly together internally.
const Plot = lazy(() =>
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  import("react-plotly.js").then((mod) => ({ default: (mod as any).default || mod }))
);

interface ChartGridProps {
  charts: ChartData[];
}

export function ChartGrid({ charts }: ChartGridProps) {
  return (
    <section id="charts">
      <h2 className="text-base font-semibold text-foreground mb-3">Charts</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {charts.map((chart) => (
          <div
            key={chart.name}
            className="bg-slate-800 border border-slate-700 rounded-lg p-4"
            aria-label={`Chart: ${chart.name.replace(/_/g, " ")}`}
          >
            <Suspense
              fallback={
                <div className="flex items-center justify-center h-[360px] text-sm text-muted-foreground">
                  Loading chart...
                </div>
              }
            >
              <Plot
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                data={chart.data as any[]}
                layout={{
                  ...(chart.layout as Record<string, unknown>),
                  paper_bgcolor: "transparent",
                  plot_bgcolor: "transparent",
                  font: { color: "#f1f5f9" },
                  xaxis: {
                    ...((chart.layout?.xaxis as Record<string, unknown>) ?? {}),
                    gridcolor: "#334155",
                  },
                  yaxis: {
                    ...((chart.layout?.yaxis as Record<string, unknown>) ?? {}),
                    gridcolor: "#334155",
                  },
                  margin: { l: 50, r: 20, t: 40, b: 40 },
                }}
                useResizeHandler={true}
                style={{ width: "100%", height: "360px" }}
                config={{ responsive: true, displayModeBar: false }}
              />
            </Suspense>
          </div>
        ))}
      </div>
    </section>
  );
}
