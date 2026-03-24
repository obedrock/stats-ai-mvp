import * as React from "react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Copy, Check } from "lucide-react";

interface RCodeBlockProps {
  code: string;
}

export function RCodeBlock({ code }: RCodeBlockProps) {
  const [open, setOpen] = React.useState(false);
  const [copied, setCopied] = React.useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <section id="r-code">
      <Collapsible open={open} onOpenChange={setOpen}>
        <div className="flex items-center gap-2">
          <CollapsibleTrigger className="text-base font-semibold text-foreground hover:text-accent transition-colors">
            {open ? "Hide R Code" : "View R Code"}
          </CollapsibleTrigger>
          <button
            onClick={handleCopy}
            className="text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Copy R code to clipboard"
          >
            {copied ? (
              <Check className="size-4" />
            ) : (
              <Copy className="size-4" />
            )}
          </button>
          {copied && (
            <span className="text-xs text-muted-foreground" aria-live="polite">
              Copied!
            </span>
          )}
        </div>
        <CollapsibleContent>
          <pre className="mt-3 bg-[#0f0f1a] rounded-lg p-4 overflow-x-auto">
            <code className="text-xs font-mono text-slate-300 leading-relaxed">
              {code}
            </code>
          </pre>
        </CollapsibleContent>
      </Collapsible>
    </section>
  );
}
