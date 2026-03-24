declare module "react-plotly.js" {
  import { Component } from "react";

  interface PlotParams {
    data: Record<string, unknown>[];
    layout?: Record<string, unknown>;
    config?: Record<string, unknown>;
    style?: React.CSSProperties;
    useResizeHandler?: boolean;
    onInitialized?: (figure: { data: unknown[]; layout: unknown }, graphDiv: HTMLElement) => void;
    onUpdate?: (figure: { data: unknown[]; layout: unknown }, graphDiv: HTMLElement) => void;
  }

  export default class Plot extends Component<PlotParams> {}
}
