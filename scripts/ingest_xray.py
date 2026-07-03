"""
Ingest a folder of X-ray images + their model predictions into a Senebiclabs project,
ready to send to Label Studio for radiologist review.

Usage:
  python scripts/ingest_xray.py --company "Abhishek Radiology" --email client@acme.com \
      --images ./xrays --predictions preds.csv [--ttl-days 7]

Manifest (CSV, header required). Default columns are `filename,prediction`:
  filename,prediction
  img001.png,Pneumonia

For a client whose columns differ, pass --mapping mapping.json (Slice #4 declared mapping):
  {"format": "csv", "image_column": "image", "prediction_column": "model_label",
   "extra_columns": ["study_id"]}
A malformed manifest fails loudly before anything uploads.

Isolation (Slice #2): images go to a PRIVATE bucket under a per-client prefix, with
de-identified (hashed) keys, and are served to Label Studio via time-limited signed URLs.
De-id covers keys/filenames only — NOT DICOM headers or burned-in pixel PHI (out of scope
until DICOM). Signed URLs do not auto-refresh; if a review window outlives the TTL, re-run
`/admin` → Send to Label Studio to regenerate them.

Do NOT ingest real client X-rays until the isolation gate tests pass. Demo/public PNGs only.
"""
import argparse
import json
import os

from app.services import ingest, storage
from app.services.supabase_client import get_client


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--company", required=True, help="customer name, e.g. 'Abhishek Radiology'")
    ap.add_argument("--email", required=True, help="client identifier (drives the per-client storage prefix)")
    ap.add_argument("--images", required=True, help="folder containing the image files")
    ap.add_argument("--predictions", required=True, help="manifest CSV (default columns: filename,prediction)")
    ap.add_argument("--mapping", help="optional JSON file: declared column mapping for a client's format")
    ap.add_argument("--ttl-days", type=int, default=7, help="signed-URL lifetime (default 7 days)")
    args = ap.parse_args()

    db = get_client()
    if db is None:
        raise SystemExit("Supabase not configured (check .env).")

    # Declared mapping: default (filename/prediction) unless the client's format differs.
    mapping = ingest.DEFAULT_MAPPING
    if args.mapping:
        with open(args.mapping, encoding="utf-8") as f:
            mapping = json.load(f)
    try:
        manifest = ingest.load_manifest(args.predictions, mapping)   # loud on bad input
    except ValueError as exc:
        raise SystemExit(f"MANIFEST ERROR: {exc}")

    client_id = storage.client_id_for(args.email)
    ttl = args.ttl_days * 24 * 3600
    storage.ensure_bucket(db)

    sub = db.table("project_submissions").insert({
        "company": args.company, "email": args.email,
        "task_type": "xray_classification", "status": "new",
    }).execute()
    pid = sub.data[0]["id"]
    print("project id:", pid, "| client prefix:", client_id)

    rows, missing = [], []
    for i, r in enumerate(manifest):
        path = os.path.join(args.images, r["image"])
        if not os.path.exists(path):
            missing.append(r["image"])
            continue
        key = storage.upload_image(client_id, path, db)          # private, de-identified key
        url = storage.signed_url(key, ttl, db)                    # time-limited access
        content = {"image": url, "prediction": r["prediction"], **r["extra"]}
        rows.append({"project_id": pid, "idx": i, "content": content})
        print(f"  [{i + 1}/{len(manifest)}] uploaded (de-identified)")

    if rows:
        db.table("project_items").insert(rows).execute()
    print(f"\ncreated {len(rows)} tasks in project {pid}")
    if missing:
        raise SystemExit(f"ERROR: {len(missing)} images in the manifest were not found: {missing[:5]}")
    print("Next: assign a radiologist (project_clinicians), then /admin -> 'xray_classification' -> Send to Label Studio.")


if __name__ == "__main__":
    main()
