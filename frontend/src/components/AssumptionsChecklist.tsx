import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import type { AssumptionItem } from "@/types/data";

interface AssumptionsChecklistProps {
  items: AssumptionItem[];
  onToggle: (key: string) => void;
  onConfirm: () => void;
}

export function AssumptionsChecklist({
  items,
  onToggle,
  onConfirm,
}: AssumptionsChecklistProps) {
  const anyChecked = items.some((item) => item.confirmed ?? item.recommended);

  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm font-medium text-foreground">
        Review assumptions before fetching data
      </p>

      <div className="flex flex-col gap-2">
        {items.map((item) => {
          const checked = item.confirmed ?? item.recommended;
          return (
            <label
              key={item.key}
              className="flex items-center gap-3 min-h-[40px] cursor-pointer group"
            >
              <Checkbox
                checked={checked}
                onCheckedChange={() => onToggle(item.key)}
                className="shrink-0"
              />
              <span className="text-sm text-foreground group-hover:text-foreground/90 transition-colors">
                {item.label}
              </span>
            </label>
          );
        })}
      </div>

      <div className="flex justify-end pt-2">
        <Button
          onClick={onConfirm}
          disabled={!anyChecked}
          className="bg-accent text-accent-foreground hover:bg-accent/90 min-h-[44px] px-5 disabled:opacity-50"
        >
          Confirm and Fetch Data
        </Button>
      </div>
    </div>
  );
}
