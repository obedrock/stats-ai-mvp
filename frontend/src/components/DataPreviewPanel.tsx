import * as React from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import type { DataPreview } from "@/types/data";

interface DataPreviewPanelProps {
  preview: DataPreview;
  onRunAnalysis: () => void;
}

function SkeletonRow({ columns }: { columns: number }) {
  return (
    <TableRow>
      {Array.from({ length: columns }).map((_, i) => (
        <TableCell key={i} className="px-3 py-2">
          <div className="h-4 w-full animate-pulse rounded bg-slate-800" />
        </TableCell>
      ))}
    </TableRow>
  );
}

export function DataPreviewPanel({ preview, onRunAnalysis }: DataPreviewPanelProps) {
  const [open, setOpen] = React.useState(false);

  const columnNames = preview.columns.map((c) => c.name);
  const previewRows = preview.rows.slice(0, 50);

  function formatStat(value: number | null): string {
    if (value === null) return "—";
    return Number.isInteger(value) ? String(value) : value.toFixed(4);
  }

  return (
    <Card className="bg-card border-border">
      <CardContent className="px-4 py-3">
        <Collapsible open={open} onOpenChange={setOpen}>
          <CollapsibleTrigger className="flex w-full items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors py-1">
            {open ? (
              <ChevronDown className="size-3.5 shrink-0" />
            ) : (
              <ChevronRight className="size-3.5 shrink-0" />
            )}
            <span>
              {open
                ? "Hide data preview"
                : `Show data preview (${preview.total_rows} rows)`}
            </span>
          </CollapsibleTrigger>

          <CollapsibleContent>
            <div className="mt-3 flex flex-col gap-3">
              {/* Scrollable table */}
              <div
                className="overflow-y-auto rounded-lg border border-border"
                style={{ maxHeight: "320px" }}
              >
                <Table>
                  <TableHeader>
                    <TableRow className="border-b border-border">
                      {columnNames.map((name) => (
                        <TableHead
                          key={name}
                          className="bg-muted px-3 py-2 text-[12px] font-normal text-foreground whitespace-nowrap"
                          style={{ backgroundColor: "#1e293b" }}
                        >
                          {name}
                        </TableHead>
                      ))}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {previewRows.length > 0
                      ? previewRows.map((row, rowIdx) => (
                          <TableRow key={rowIdx} className="border-b border-border/50">
                            {columnNames.map((name) => (
                              <TableCell
                                key={name}
                                className="px-3 py-1.5 text-sm text-foreground whitespace-nowrap"
                              >
                                {String(row[name] ?? "")}
                              </TableCell>
                            ))}
                          </TableRow>
                        ))
                      : Array.from({ length: 5 }).map((_, i) => (
                          <SkeletonRow key={i} columns={columnNames.length || 3} />
                        ))}
                  </TableBody>
                </Table>
              </div>

              {/* Stats bar */}
              <div className="overflow-x-auto">
                <div className="flex gap-6 text-[12px] text-muted-foreground whitespace-nowrap py-1">
                  {preview.columns.map((col) => (
                    <span key={col.name}>
                      <span className="font-medium text-foreground">{col.name}</span>
                      {" "}
                      <span>
                        min {formatStat(col.min)}
                        {" · "}
                        max {formatStat(col.max)}
                        {" · "}
                        mean {formatStat(col.mean)}
                        {" · "}
                        missing {col.missing_count}
                      </span>
                    </span>
                  ))}
                </div>
              </div>

              {/* Run Analysis button */}
              <div className="flex justify-end pt-1">
                <Button
                  onClick={onRunAnalysis}
                  className="bg-accent text-accent-foreground hover:bg-accent/90 min-h-[44px] px-5"
                >
                  Run Analysis
                </Button>
              </div>
            </div>
          </CollapsibleContent>
        </Collapsible>
      </CardContent>
    </Card>
  );
}
