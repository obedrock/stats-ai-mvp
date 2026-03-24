"""
File upload parsing service.

Parses CSV, Excel (.xlsx), and JSON files uploaded by users.
Auto-detects column types and applies auto-fix transformations with a change report.

DATA-12: User can upload CSV, Excel (.xlsx), and JSON files.
DATA-13: Auto-detect column types and date formats from uploaded files.
DATA-10 (partial): D-10 — malformed files are auto-fixed with a report.
"""

import io

import pandas as pd


def parse_uploaded_file(content: bytes, filename: str) -> dict:
    """Parse an uploaded file and return preview, column info, and auto-fix report.

    Args:
        content: Raw file bytes.
        filename: Original filename (used to detect format via extension).

    Returns:
        dict with keys:
          - preview: list[dict] — first 10 rows as records
          - columns: list[dict] — column info (name, detected_type, role)
          - changes: list[str] — auto-fix descriptions
          - total_rows: int — row count after cleaning
          - dataframe: pd.DataFrame — cleaned DataFrame (not serialized, internal use)

    Raises:
        ValueError: If the file extension is not supported.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "csv":
        df = pd.read_csv(io.BytesIO(content))
    elif ext in ("xlsx", "xls"):
        df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
    elif ext == "json":
        df = pd.read_json(io.BytesIO(content))
    else:
        raise ValueError(
            f"Unsupported file type: .{ext}. Accepted formats: CSV, Excel (.xlsx), JSON"
        )

    changes: list[str] = []

    # Auto-fix step 1: drop fully empty rows
    original_len = len(df)
    df = df.dropna(how="all").copy()
    dropped = original_len - len(df)
    if dropped > 0:
        changes.append(f"{dropped} fully empty row(s) dropped")

    # Auto-fix step 2: coerce object columns to numeric where >80% convert successfully
    for col in df.select_dtypes(include=["object", "string"]).columns:
        coerced = pd.to_numeric(df[col], errors="coerce")
        non_null = df[col].notna().sum()
        if non_null == 0:
            continue
        converted = coerced.notna().sum()
        # Also count NaN-coerced values (sentinel strings like "N/A", "---")
        # that were previously non-null object values
        sentinel_count = int(non_null - converted)
        if non_null > 0 and converted / non_null >= 0.8:
            df[col] = coerced.copy()
            if sentinel_count > 0:
                changes.append(
                    f"Column '{col}': {sentinel_count} non-numeric value(s) coerced to NaN"
                )

    # Auto-fix step 3: coerce remaining object columns to datetime where >80% convert
    for col in df.select_dtypes(include=["object", "string"]).columns:
        coerced = pd.to_datetime(df[col], errors="coerce")
        non_null = df[col].notna().sum()
        if non_null == 0:
            continue
        converted = coerced.notna().sum()
        if converted / non_null >= 0.8:
            df[col] = coerced.copy()
            changes.append(f"Column '{col}': coerced to datetime")

    # Column detection: build type list
    columns: list[dict] = []
    date_columns: list[str] = []

    for col in df.columns:
        dtype = df[col].dtype
        n_unique = df[col].nunique()

        if pd.api.types.is_datetime64_any_dtype(dtype):
            detected_type = "date"
            date_columns.append(col)
        elif pd.api.types.is_numeric_dtype(dtype):
            detected_type = "numeric"
        elif n_unique <= 10:
            detected_type = "category"
        else:
            detected_type = "text"

        columns.append({"name": col, "detected_type": detected_type, "role": None})

    # Auto-assign date_index role if exactly one date column
    if len(date_columns) == 1:
        for col_info in columns:
            if col_info["name"] == date_columns[0]:
                col_info["role"] = "date_index"

    return {
        "preview": df.head(10).to_dict(orient="records"),
        "columns": columns,
        "changes": changes,
        "total_rows": len(df),
        "dataframe": df,
    }
