import * as React from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { useAnalysisStore } from "@/store/analysis";

interface PromptInputProps {
  onSubmit: (prompt: string) => void;
  disabled?: boolean;
}

export function PromptInput({ onSubmit, disabled = false }: PromptInputProps) {
  const prompt = useAnalysisStore((s) => s.prompt);
  const setPrompt = useAnalysisStore((s) => s.setPrompt);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (prompt.trim().length < 5) return;
    onSubmit(prompt.trim());
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    // Cmd/Ctrl+Enter to submit
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      if (prompt.trim().length >= 5 && !disabled) {
        onSubmit(prompt.trim());
      }
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-2 w-full">
      <Textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder="Describe what you want to analyse..."
        className="resize-none min-h-[80px] bg-card border-border text-foreground placeholder:text-muted-foreground focus-visible:border-accent focus-visible:ring-accent/30"
        rows={3}
      />
      <div className="flex justify-end">
        <Button
          type="submit"
          disabled={disabled || prompt.trim().length < 5}
          className="bg-accent text-accent-foreground hover:bg-accent/90 min-h-[44px] px-5"
        >
          Fetch Data
        </Button>
      </div>
    </form>
  );
}
