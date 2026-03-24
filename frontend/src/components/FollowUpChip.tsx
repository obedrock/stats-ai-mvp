import { Button } from "@/components/ui/button";
import type { FollowUpSuggestion } from "@/types/analysis";

interface FollowUpChipProps {
  suggestion: FollowUpSuggestion;
  onSelect: (promptText: string) => void;
}

export function FollowUpChip({ suggestion, onSelect }: FollowUpChipProps) {
  return (
    <Button
      variant="outline"
      onClick={() => onSelect(suggestion.prompt_text)}
      className="rounded-full px-4 py-2 h-auto text-left border-border hover:border-indigo-500 hover:text-foreground transition-colors"
    >
      <span className="text-sm">
        <span className="font-semibold">{suggestion.title}</span>
        <span className="text-muted-foreground"> — {suggestion.explanation}</span>
      </span>
    </Button>
  );
}
