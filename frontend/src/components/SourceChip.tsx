import * as React from "react";
import { Database, TrendingUp, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Input } from "@/components/ui/input";
import type { ParsedSource } from "@/types/data";

interface SourceChipProps {
  source: ParsedSource;
  index: number;
  onOverride: (index: number, newSeriesId: string) => void;
  onRemove: (index: number) => void;
}

export function SourceChip({
  source,
  index,
  onOverride,
  onRemove,
}: SourceChipProps) {
  const [open, setOpen] = React.useState(false);
  const [editValue, setEditValue] = React.useState(source.series_id);
  const [visible, setVisible] = React.useState(false);
  const [removing, setRemoving] = React.useState(false);

  // Fade in on mount
  React.useEffect(() => {
    const t = requestAnimationFrame(() => setVisible(true));
    return () => cancelAnimationFrame(t);
  }, []);

  // Reset edit value when popover opens
  React.useEffect(() => {
    if (open) setEditValue(source.series_id);
  }, [open, source.series_id]);

  const isError = source.valid === false;

  function handleRemove(e: React.MouseEvent) {
    e.stopPropagation();
    setRemoving(true);
    setTimeout(() => onRemove(index), 100);
  }

  function handleConfirm() {
    const trimmed = editValue.trim();
    if (trimmed && trimmed !== source.series_id) {
      onOverride(index, trimmed);
    }
    setOpen(false);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") handleConfirm();
    if (e.key === "Escape") setOpen(false);
  }

  const Icon = source.source === "FRED" ? Database : TrendingUp;

  const chipBorderClass = isError
    ? "border-destructive"
    : open
      ? "border-accent"
      : "border-border";

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger
        render={
          <div
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") setOpen(true);
            }}
            style={{
              opacity: removing ? 0 : visible ? 1 : 0,
              transition: removing
                ? "opacity 100ms ease-out"
                : "opacity 150ms ease-in",
              minHeight: "44px",
            }}
            className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-medium bg-card text-foreground cursor-pointer select-none transition-colors ${chipBorderClass}`}
          />
        }
      >
        <Icon className="size-3.5 shrink-0 text-muted-foreground" />
        <span className="text-muted-foreground text-xs">
          {source.source}:
        </span>
        <span className="font-mono text-xs">{source.series_id}</span>
        {isError && (
          <span className="text-destructive text-xs font-medium">
            Invalid — click to fix
          </span>
        )}
        <button
          type="button"
          onClick={handleRemove}
          className="ml-1 rounded-full p-0.5 text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
          aria-label={`Remove ${source.series_id}`}
        >
          <X className="size-3" />
        </button>
      </PopoverTrigger>

      <PopoverContent className="w-72 p-3 bg-card border-border" side="bottom" align="start">
        <div className="flex flex-col gap-2">
          <p className="text-xs text-muted-foreground font-medium">
            Edit series ID
          </p>
          <Input
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter series ID (e.g. GDPC1)"
            className="h-8 text-sm"
            autoFocus
          />
          {isError && (
            <p className="text-xs text-destructive">
              Series not found — try a different ID or let Stats-AI search FRED
            </p>
          )}
          {source.suggestions.length > 0 && (
            <div className="flex flex-col gap-1">
              <p className="text-xs text-muted-foreground">Did you mean:</p>
              {source.suggestions.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => {
                    onOverride(index, s.id);
                    setOpen(false);
                  }}
                  className="text-left text-xs text-accent hover:underline px-1 py-0.5 rounded hover:bg-accent/10 transition-colors"
                >
                  {s.id} — {s.name}
                </button>
              ))}
            </div>
          )}
          <div className="flex justify-end gap-2 pt-1">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setOpen(false)}
            >
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={handleConfirm}
              className="bg-accent text-accent-foreground hover:bg-accent/90"
              disabled={!editValue.trim()}
            >
              Confirm
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
