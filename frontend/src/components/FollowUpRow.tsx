import type { FollowUpSuggestion } from "@/types/analysis";
import { FollowUpChip } from "./FollowUpChip";

interface FollowUpRowProps {
  suggestions: FollowUpSuggestion[];
  onSelect: (promptText: string) => void;
}

export function FollowUpRow({ suggestions, onSelect }: FollowUpRowProps) {
  if (suggestions.length === 0) return null;
  return (
    <section id="follow-up">
      <h2 className="text-base font-semibold text-foreground mb-3">
        Suggested next steps
      </h2>
      <div className="flex flex-wrap gap-2">
        {suggestions.map((s) => (
          <FollowUpChip key={s.title} suggestion={s} onSelect={onSelect} />
        ))}
      </div>
    </section>
  );
}
