import * as React from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

interface AssumptionsBannerProps {
  assumptions: string[];
}

export function AssumptionsBanner({ assumptions }: AssumptionsBannerProps) {
  const [open, setOpen] = React.useState(false);

  if (assumptions.length === 0) return null;

  return (
    <div
      className="border-b border-border"
      style={{ backgroundColor: "#1e293b" }}
    >
      <Collapsible open={open} onOpenChange={setOpen}>
        <CollapsibleTrigger className="flex w-full items-center gap-1.5 px-4 py-2 text-[12px] text-muted-foreground hover:text-foreground transition-colors">
          {open ? (
            <ChevronDown className="size-3.5 shrink-0" />
          ) : (
            <ChevronRight className="size-3.5 shrink-0" />
          )}
          <span>Assumptions applied — click to review</span>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <ul className="px-4 pb-3 space-y-1">
            {assumptions.map((assumption, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-sm text-foreground"
              >
                <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-muted-foreground" />
                <span>{assumption}</span>
              </li>
            ))}
          </ul>
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
}
