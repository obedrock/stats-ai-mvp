// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-expect-error -- react-plotly.js has no bundled type declarations; Plotly types from chartData are unknown[]
import createPlotlyComponent from "react-plotly.js/factory";
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-expect-error -- plotly.js-dist-min has no bundled type declarations
import Plotly from "plotly.js-dist-min";
import type { ChartData } from "@/types/analysis";

// eslint-disable-next-line @typescript-eslint/no-unsafe-call
const Plot = createPlotlyComponent(Plotly) as React.ComponentType<{
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: any[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  layout: Record<string, any>;
  useResizeHandler?: boolean;
  style?: React.CSSProperties;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  config?: Record<string, any>;
}>;

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
            <Plot
              data={chart.data as unknown[]}
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
          </div>
        ))}
      </div>
    </section>
  );
}
