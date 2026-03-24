import * as React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import type { FrequencyConflict, ResolutionChoice } from "@/types/data";

type ResolutionMethod = ResolutionChoice["method"];

interface RadioOption {
  value: ResolutionMethod;
  label: string;
}

const RADIO_OPTIONS: RadioOption[] = [
  { value: "mean", label: "Aggregate to lower frequency (mean)" },
  { value: "last", label: "Aggregate to lower frequency (last)" },
  { value: "sum", label: "Aggregate to lower frequency (sum)" },
  { value: "ffill", label: "Interpolate to higher frequency (forward-fill)" },
  { value: "abort", label: "Abort analysis" },
];

interface FrequencyMismatchDialogProps {
  conflict: FrequencyConflict;
  onConfirm: (choice: ResolutionChoice) => void;
  onCancel: () => void;
}

export function FrequencyMismatchDialog({
  conflict,
  onConfirm,
  onCancel,
}: FrequencyMismatchDialogProps) {
  const [selectedMethod, setSelectedMethod] = React.useState<ResolutionMethod>(
    () => {
      const rec = conflict.recommended_method as ResolutionMethod;
      const valid = RADIO_OPTIONS.some((o) => o.value === rec);
      return valid ? rec : "mean";
    }
  );

  function handleConfirm() {
    onConfirm({
      method: selectedMethod,
      target_frequency: conflict.target_frequency,
    });
  }

  // Build body text from series_frequencies
  const bodyText = conflict.series_frequencies
    .map(
      (sf) =>
        `${sf.series_id}: ${sf.row_count.toLocaleString()} ${sf.frequency} rows`
    )
    .join(" · ");

  return (
    <Dialog
      open={true}
      // Prevent closing when open state changes from outside clicks or escape
      onOpenChange={(open, details) => {
        if (!open && details) {
          // Block outside press and escape key dismissal
          details.preventUnmountOnClose?.();
        }
      }}
      // @ts-expect-error — base-ui prop not in shadcn wrapper types
      disablePointerDismissal={true}
    >
      <DialogContent
        showCloseButton={false}
        className="sm:max-w-lg bg-card border-border"
        // Block outside click interaction
        onInteractOutside={(e: Event) => e.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle className="text-[20px] font-semibold text-foreground">
            Data frequencies do not match
          </DialogTitle>
        </DialogHeader>

        <div className="flex flex-col gap-4 py-1">
          {/* Body description */}
          <p className="text-sm text-foreground">
            {bodyText} — choose how to align them before proceeding.
          </p>

          {/* Recommendation card */}
          <div
            className="rounded-lg border p-3"
            style={{ borderColor: "#6366f1", backgroundColor: "#1e3a5f" }}
          >
            <p className="text-sm text-foreground">
              <span className="font-medium text-accent">Recommended:</span>{" "}
              {conflict.recommendation}
            </p>
          </div>

          {/* Options */}
          <RadioGroup
            value={selectedMethod}
            onValueChange={(v) => setSelectedMethod(v as ResolutionMethod)}
            className="gap-3"
          >
            {RADIO_OPTIONS.map((option) => (
              <div
                key={option.value}
                className="flex items-center gap-3 min-h-[40px]"
              >
                <RadioGroupItem
                  value={option.value}
                  id={`freq-option-${option.value}`}
                />
                <Label
                  htmlFor={`freq-option-${option.value}`}
                  className="text-sm text-foreground cursor-pointer"
                >
                  {option.label}
                </Label>
              </div>
            ))}
          </RadioGroup>
        </div>

        <DialogFooter>
          <Button
            variant="ghost"
            onClick={onCancel}
            className="text-muted-foreground"
          >
            Cancel analysis
          </Button>
          <Button
            onClick={handleConfirm}
            className="bg-accent text-accent-foreground hover:bg-accent/90 min-h-[44px]"
          >
            Confirm
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
