import * as React from "react";
import { Loader2 } from "lucide-react";
import type { UploadResult } from "@/types/data";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
const ACCEPTED_EXTENSIONS = [".csv", ".xlsx", ".xls", ".json"];
const ACCEPTED_MIME = [
  "text/csv",
  "application/vnd.ms-excel",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "application/json",
  "text/plain",
];

interface UploadDropzoneProps {
  onUpload: (result: UploadResult) => void;
}

function isAcceptedFile(file: File): boolean {
  const name = file.name.toLowerCase();
  return ACCEPTED_EXTENSIONS.some((ext) => name.endsWith(ext));
}

export function UploadDropzone({ onUpload }: UploadDropzoneProps) {
  const [isDragOver, setIsDragOver] = React.useState(false);
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [shake, setShake] = React.useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  const errorTimerRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  // Clean up timer on unmount
  React.useEffect(() => {
    return () => {
      if (errorTimerRef.current) clearTimeout(errorTimerRef.current);
    };
  }, []);

  function showError(msg: string) {
    setError(msg);
    setShake(true);
    if (errorTimerRef.current) clearTimeout(errorTimerRef.current);
    // Remove shake class after animation
    setTimeout(() => setShake(false), 500);
    // Clear error text after 4 seconds
    errorTimerRef.current = setTimeout(() => setError(null), 4000);
  }

  async function handleFile(file: File) {
    if (!isAcceptedFile(file)) {
      showError(
        "Could not read this file. Make sure it is a valid CSV, Excel, or JSON file."
      );
      return;
    }

    setError(null);
    setIsLoading(false);

    // Show spinner if parse takes >500ms
    const loadingTimer = setTimeout(() => setIsLoading(true), 500);

    try {
      const token = localStorage.getItem("token");
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${API_BASE}/data/upload`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });

      clearTimeout(loadingTimer);
      setIsLoading(false);

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        showError(
          (body as { detail?: string }).detail ||
            "Could not read this file. Make sure it is a valid CSV, Excel, or JSON file."
        );
        return;
      }

      const result: UploadResult = await res.json();
      onUpload(result);
    } catch {
      clearTimeout(loadingTimer);
      setIsLoading(false);
      showError(
        "Could not read this file. Make sure it is a valid CSV, Excel, or JSON file."
      );
    }
  }

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }

  function handleDragEnter(e: React.DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }

  function handleDragLeave(e: React.DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    // Only leave if exiting the zone entirely
    if (e.currentTarget.contains(e.relatedTarget as Node)) return;
    setIsDragOver(false);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) void handleFile(file);
  }

  function handleClick() {
    fileInputRef.current?.click();
  }

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) void handleFile(file);
    // Reset so the same file can be re-selected
    e.target.value = "";
  }

  return (
    <div className="flex flex-col gap-2">
      <div
        role="button"
        tabIndex={0}
        onClick={handleClick}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") handleClick();
        }}
        onDragOver={handleDragOver}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative flex min-h-[120px] cursor-pointer items-center justify-center rounded-lg border-2 border-dashed transition-colors ${
          shake ? "animate-shake" : ""
        }`}
        style={
          isDragOver
            ? { borderColor: "#6366f1", backgroundColor: "#1e3a5f" }
            : { borderColor: "#334155", backgroundColor: "#1e293b" }
        }
        aria-label="Upload file"
      >
        {isLoading ? (
          <Loader2 className="size-5 animate-spin text-muted-foreground" />
        ) : (
          <p className="select-none text-sm text-muted-foreground text-center px-4">
            {isDragOver
              ? "Drop to upload"
              : "Drop CSV, Excel, or JSON here — or click to browse"}
          </p>
        )}
      </div>
      {error && (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      )}
      <input
        ref={fileInputRef}
        type="file"
        accept={ACCEPTED_EXTENSIONS.join(",")}
        className="hidden"
        onChange={handleInputChange}
      />
    </div>
  );
}
