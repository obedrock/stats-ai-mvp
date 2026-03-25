import { lazy, Suspense, Component, type ComponentProps, type ReactNode } from "react";
import type { ChartData } from "@/types/analysis";

// Lazy-load plotly to avoid CJS/ESM interop issues in production builds
const PlotLazy = lazy(() => import("react-plotly.js"));

type PlotProps = ComponentProps<typeof PlotLazy>;

// Error boundary to prevent plotly crashes from blanking the whole page
class ChartErrorBoundary extends Component<
  { children: ReactNode; name: string },
  { error: string | null }
> {
  state = { error: null as string | null };

  static getDerivedStateFromError(err: Error) {
    return { error: err.message };
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex items-center justify-center h-[360px] text-sm text-muted-foreground">
          Chart failed to render: {this.state.error}
        </div>
      );
    }
    return this.props.children;
  }
}

function PlotChart(props: PlotProps) {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center h-[360px] text-sm text-muted-foreground">
          Loading chart...
        </div>
      }
    >
      <PlotLazy {...props} />
    </Suspense>
  );
}

interface ChartGridProps {
  charts: ChartData[];
}

export function ChartGrid({ charts }: ChartGridProps) {
  if (!charts || charts.length === 0) return null;

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
            <ChartErrorBoundary name={chart.name}>
              <PlotChart
                data={chart.data as Record<string, unknown>[]}
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
            </ChartErrorBoundary>
          </div>
        ))}
      </div>
    </section>
  );
}
