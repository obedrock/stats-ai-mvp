import { useRef, useEffect } from "react";
import type { ChartData } from "@/types/analysis";

// Render plotly charts using the imperative API (Plotly.newPlot) instead of
// react-plotly.js component. The react-plotly.js component crashes with React 19
// error #306 because it tries to render plotly internal objects as React children.

interface ChartGridProps {
  charts: ChartData[];
}

function PlotDiv({ chart }: { chart: ChartData }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let mounted = true;

    import("plotly.js-dist-min").then((mod) => {
      const Plotly = mod.default || mod;
      if (!mounted || !ref.current) return;

      const darkLayout = {
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
      };

      Plotly.newPlot(ref.current, chart.data as Record<string, unknown>[], darkLayout, {
        responsive: true,
        displayModeBar: false,
      });
    });

    return () => {
      mounted = false;
      if (ref.current) {
        import("plotly.js-dist-min").then((mod) => {
          const Plotly = mod.default || mod;
          if (ref.current) Plotly.purge(ref.current);
        });
      }
    };
  }, [chart]);

  return <div ref={ref} style={{ width: "100%", height: "360px" }} />;
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
            <PlotDiv chart={chart} />
          </div>
        ))}
      </div>
    </section>
  );
}
