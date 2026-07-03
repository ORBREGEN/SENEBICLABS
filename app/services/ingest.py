"""
Declared-mapping ingest scaffolding (Slice #4 — the client-independent half).

A client sends a tabular manifest (CSV today) whose columns use THEIR names. Instead of
hardcoding 'filename'/'prediction', the operator declares a column mapping and this module
turns the manifest into normalized items. Bad input fails loudly (ValueError) BEFORE any
image is uploaded, so a malformed manifest never becomes half a project.

The client-specific part — their exact column names and class list — is a mapping dict
filled in at onboarding, no code change. Only the generic machinery + validation live here.

Mapping shape:
    {
      "format": "csv",              # only 'csv' supported today; declared so unknowns fail loud
      "image_column": "filename",   # required: column holding the image filename
      "prediction_column": "pred",  # optional: column holding the model prediction
      "extra_columns": ["study_id"] # optional: extra columns to carry into the item content
    }
"""
import csv
import os

SUPPORTED_FORMATS = {"csv"}

# Sensible default so the existing X-ray pilot keeps working with no mapping supplied.
DEFAULT_MAPPING = {"format": "csv", "image_column": "filename", "prediction_column": "prediction"}


def parse_mapping(mapping: dict) -> dict:
    """Validate and normalize a declared mapping. Raises ValueError on anything unusable."""
    if not isinstance(mapping, dict):
        raise ValueError("mapping must be an object")
    fmt = (mapping.get("format") or "csv").lower()
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"unsupported manifest format {fmt!r}; supported: {sorted(SUPPORTED_FORMATS)}")
    image_col = mapping.get("image_column")
    if not image_col or not isinstance(image_col, str):
        raise ValueError("mapping.image_column is required (which column holds the image filename)")
    pred_col = mapping.get("prediction_column")
    if pred_col is not None and not isinstance(pred_col, str):
        raise ValueError("mapping.prediction_column must be a column name (string) or omitted")
    extra = mapping.get("extra_columns") or []
    if not isinstance(extra, list) or any(not isinstance(c, str) for c in extra):
        raise ValueError("mapping.extra_columns must be a list of column names")
    return {"format": fmt, "image_column": image_col, "prediction_column": pred_col, "extra_columns": list(extra)}


def load_manifest(path: str, mapping: dict) -> list[dict]:
    """Read the manifest and return normalized rows: {image, prediction, extra:{...}}.

    Fails loudly (ValueError) on unknown format, a missing declared column, an empty
    manifest, or a row with a blank image cell — before anything is uploaded.
    """
    m = parse_mapping(mapping)
    if not os.path.exists(path):
        raise ValueError(f"manifest not found: {path}")

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        declared = [m["image_column"]]
        if m["prediction_column"]:
            declared.append(m["prediction_column"])
        declared += m["extra_columns"]
        missing = [c for c in declared if c not in headers]
        if missing:
            raise ValueError(f"manifest is missing declared column(s) {missing}; it has {headers}")

        rows = []
        for i, row in enumerate(reader, start=1):
            image = (row.get(m["image_column"]) or "").strip()
            if not image:
                raise ValueError(f"row {i}: blank value in image column {m['image_column']!r}")
            pred = (row.get(m["prediction_column"]) or "").strip() if m["prediction_column"] else None
            extra = {c: (row.get(c) or "").strip() for c in m["extra_columns"]}
            rows.append({"image": image, "prediction": pred, "extra": extra})

    if not rows:
        raise ValueError("manifest has no data rows")
    return rows
