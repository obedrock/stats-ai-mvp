import * as React from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Button } from "@/components/ui/button";
import type { UploadResult, ColumnInfo } from "@/types/data";

// ColumnMapping is a confirmed ColumnInfo (role must be non-null)
export interface ColumnMapping {
  name: string;
  detected_type: ColumnInfo["detected_type"];
  role: NonNullable<ColumnInfo["role"]>;
}

type ColumnRole = NonNullable<ColumnInfo["role"]>;
type ColumnType = ColumnInfo["detected_type"];

const TYPE_OPTIONS: { value: ColumnType; label: string }[] = [
  { value: "numeric", label: "Numeric" },
  { value: "date", label: "Date" },
  { value: "text", label: "Text" },
  { value: "category", label: "Category" },
];

const ROLE_OPTIONS: { value: ColumnRole | ""; label: string }[] = [
  { value: "", label: "— select role —" },
  { value: "dependent", label: "Dependent variable" },
  { value: "independent", label: "Independent variable" },
  { value: "date_index", label: "Date index" },
  { value: "ignore", label: "Ignore" },
];

interface ColumnMappingTableProps {
  result: UploadResult;
  onConfirm: (columns: ColumnMapping[]) => void;
}

export function ColumnMappingTable({ result, onConfirm }: ColumnMappingTableProps) {
  const [localColumns, setLocalColumns] = React.useState<ColumnInfo[]>(
    () => result.columns.map((c) => ({ ...c }))
  );
  const [autoFixOpen, setAutoFixOpen] = React.useState(false);

  // Derive column names that had coercion issues from result.changes
  const coercedColumnNames = React.useMemo(() => {
    const names = new Set<string>();
    for (const change of result.changes) {
      // Heuristic: change messages often mention column names
      for (const col of result.columns) {
        if (change.toLowerCase().includes(col.name.toLowerCase())) {
          names.add(col.name);
        }
      }
    }
    return names;
  }, [result.changes, result.columns]);

  function updateType(index: number, type: ColumnType) {
    setLocalColumns((prev) =>
      prev.map((c, i) => (i === index ? { ...c, detected_type: type } : c))
    );
  }

  function updateRole(index: number, role: ColumnRole | "") {
    setLocalColumns((prev) =>
      prev.map((c, i) =>
        i === index ? { ...c, role: role === "" ? null : role } : c
      )
    );
  }

  const allRolesAssigned = localColumns.every((c) => c.role !== null);

  function handleConfirm() {
    if (!allRolesAssigned) return;
    onConfirm(
      localColumns.map((c) => ({
        name: c.name,
        detected_type: c.detected_type,
        role: c.role as ColumnRole,
      }))
    );
  }

  // Preview rows: first 10
  const previewRows = result.preview.slice(0, 10);

  // Auto-fix report: parse counts from changes
  const rowsDropped = result.changes.filter((c) =>
    c.toLowerCase().includes("row")
  ).length;
  const valuesCoerced = result.changes.filter((c) =>
    c.toLowerCase().includes("coerce") || c.toLowerCase().includes("value")
  ).length;

  return (
    <div className="flex flex-col gap-3">
      {result.changes.length > 0 && (
        <Collapsible open={autoFixOpen} onOpenChange={setAutoFixOpen}>
          <CollapsibleTrigger className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors">
            {autoFixOpen ? (
              <ChevronDown className="size-3.5" />
            ) : (
              <ChevronRight className="size-3.5" />
            )}
            <span>
              {rowsDropped} rows dropped, {valuesCoerced} values coerced —
              click to see details
            </span>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <ul className="mt-2 rounded-lg border border-border bg-card/50 p-3 space-y-1">
              {result.changes.map((change, i) => (
                <li key={i} className="text-xs text-muted-foreground">
                  {change}
                </li>
              ))}
            </ul>
          </CollapsibleContent>
        </Collapsible>
      )}

      <div className="overflow-x-auto rounded-lg border border-border">
        <Table>
          <TableHeader className="bg-muted/50">
            <TableRow>
              {localColumns.map((col, i) => (
                <TableHead key={col.name} className="min-w-[160px] px-3 py-2">
                  <div className="flex flex-col gap-1.5">
                    <div className="flex items-center gap-1.5">
                      {coercedColumnNames.has(col.name) && (
                        <span
                          className="inline-block size-2 rounded-full shrink-0"
                          style={{ backgroundColor: "#f59e0b" }}
                          title="Type coercion applied"
                        />
                      )}
                      <span className="font-semibold text-[14px] text-foreground truncate">
                        {col.name}
                      </span>
                    </div>
                    <select
                      value={col.detected_type}
                      onChange={(e) =>
                        updateType(i, e.target.value as ColumnType)
                      }
                      className="h-6 rounded border border-border bg-background px-1.5 text-xs text-foreground focus:border-accent focus:outline-none"
                    >
                      {TYPE_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                    <select
                      value={col.role ?? ""}
                      onChange={(e) =>
                        updateRole(i, e.target.value as ColumnRole | "")
                      }
                      className="h-6 rounded border border-border bg-background px-1.5 text-xs text-foreground focus:border-accent focus:outline-none"
                    >
                      {ROLE_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {previewRows.map((row, rowIdx) => (
              <TableRow key={rowIdx}>
                {localColumns.map((col) => (
                  <TableCell
                    key={col.name}
                    className="px-3 py-1.5 text-sm text-foreground"
                  >
                    {String(row[col.name] ?? "")}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <p className="text-xs text-muted-foreground">
        Showing {previewRows.length} of {result.total_rows} rows
      </p>

      <div className="flex justify-end">
        <Button
          onClick={handleConfirm}
          disabled={!allRolesAssigned}
          className="min-h-[44px] bg-accent text-accent-foreground hover:bg-accent/90 px-5"
        >
          Confirm Mapping
        </Button>
      </div>
    </div>
  );
}
