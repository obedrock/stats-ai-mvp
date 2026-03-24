import * as React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import type { AnalysisError } from "@/types/analysis";

interface ErrorResultCardProps {
  error: AnalysisError;
  onRetry: (suggestedPrompt: string) => void;
}

export function ErrorResultCard({ error, onRetry }: ErrorResultCardProps) {
  const [showRaw, setShowRaw] = React.useState(false);

  return (
    <Card className="bg-slate-800 border-red-500">
      <CardContent className="pt-6 space-y-4">
        <h2 className="text-base font-semibold text-red-400">
          Analysis could not complete
        </h2>
        <p className="text-sm text-foreground">{error.error_explanation}</p>

        <Collapsible open={showRaw} onOpenChange={setShowRaw}>
          <CollapsibleTrigger className="text-xs text-muted-foreground hover:text-foreground transition-colors">
            {showRaw ? "Hide R output" : "Show R output"}
          </CollapsibleTrigger>
          <CollapsibleContent>
            <pre className="mt-2 bg-[#0f0f1a] rounded-lg p-3 overflow-x-auto">
              <code className="text-xs font-mono text-red-300">
                {error.r_stderr}
              </code>
            </pre>
          </CollapsibleContent>
        </Collapsible>

        <Button
          onClick={() => onRetry(error.suggested_prompt)}
          className="w-full sm:w-auto bg-accent text-accent-foreground hover:bg-accent/90"
        >
          Try a modified prompt
        </Button>
      </CardContent>
    </Card>
  );
}
