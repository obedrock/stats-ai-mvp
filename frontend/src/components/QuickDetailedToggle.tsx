import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAnalysisStore } from "@/store/analysis";
import type { AnalysisMode } from "@/types/data";

export function QuickDetailedToggle() {
  const mode = useAnalysisStore((s) => s.mode);
  const setMode = useAnalysisStore((s) => s.setMode);

  return (
    <Tabs
      value={mode}
      onValueChange={(v) => setMode(v as AnalysisMode)}
      className="w-fit"
    >
      <TabsList className="h-7 p-0.5">
        <TabsTrigger
          value="quick"
          className="px-3 text-xs data-active:bg-accent data-active:text-accent-foreground"
        >
          Quick
        </TabsTrigger>
        <TabsTrigger
          value="detailed"
          className="px-3 text-xs data-active:bg-accent data-active:text-accent-foreground"
        >
          Detailed
        </TabsTrigger>
      </TabsList>
    </Tabs>
  );
}
