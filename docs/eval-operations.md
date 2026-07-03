# Eval Operations — onboarding a client (operator runbook)

How to take a new evaluation client (e.g. X-ray classification review) from raw data to
radiologist-reviewed results. **A new client onboards via config, not code.**

---

## 0. One-time schema migration

Before the first client, apply `supabase_schema.sql` in the Supabase SQL editor. Slice #2
adds two things the pipeline now depends on:

- `project_submissions.eval_config` (jsonb) — the per-project labeling schema.
- `project_clinicians` (table) — which clinicians are assigned to which project.

The isolation gate test (`tests/test_isolation.py`) will refuse to pass until these exist.

---

## 1. Create the project + its eval_config

Each project carries an `eval_config` describing what the reviewer sees and answers. The
labeling UI is **generated from this schema** (`build_label_config`), so a new client or a
new question set is a config change, never a code change.

```jsonc
{
  "title": "Chest X-ray classification review",
  "schema": {
    "classes": ["Normal", "Pneumonia", "TB", "Effusion"],   // the client's label set
    "multi_label": false,
    "fields": {
      "verdict":       { "type": "single", "options": ["Correct", "Incorrect", "Partially correct"], "required": true },
      "correct_label": { "type": "from_classes", "visible_when": "verdict!=Correct" },
      "critical_miss": { "type": "structured", "visible_when": "verdict!=Correct" },
      "radiologist_confidence": { "type": "scale", "min": 1, "max": 5 },
      "cannot_assess": { "type": "flag", "label": "Cannot assess" },
      "rationale":     { "type": "text" }
    }
  }
}
```

Field types: `single`, `from_classes`, `structured`, `scale`, `flag`, `text`. An invalid
config fails loudly (HTTP 422 on sync) rather than producing a broken labeling UI.

Set it on the row: `project_submissions.eval_config = <the json above>`. If a project has
no `eval_config`, sync falls back to the built-in task-type config (existing projects keep
working).

---

## 2. Ingest the client's images

```bash
python scripts/ingest_xray.py \
  --company "Abhishek Radiology" \
  --email   client@acme.com \
  --images  ./their_xrays \
  --predictions preds.csv \
  --ttl-days 7
```

`preds.csv` has a header `filename,prediction`. Images upload to a **private** bucket under
a per-client prefix (derived from `--email`) with de-identified (hashed) keys, and are
served to Label Studio via time-limited signed URLs.

> **Do not ingest real client X-rays until the isolation gate is green** (see §5). Demo /
> public PNGs only until then.

---

## 3. Assign clinicians (required — creating the project does not grant access)

Since Slice #2, **project creation alone grants nobody access.** A clinician sees and labels
a project only if they are assigned to it in `project_clinicians`. The operator (admin key)
sees everything.

```sql
insert into project_clinicians (project_id, clinician_id)
values ('<project-uuid>', '<clinician-uuid>');
```

Get clinician IDs from the `clinicians` table (create them via `POST /admin/clinicians`).
An unassigned work code gets `403` from every work endpoint.

---

## 4. Send to Label Studio, then pull results

- **Send:** `/admin` → select the project → *Send to Label Studio* (`POST /ls/sync`). Creates
  the LS project from the generated config and pushes pending items as tasks.
- **Pull:** `POST /ls/pull` (or the LS webhook) writes annotations back to `project_items`.
- The client downloads reviewed results from their portal.

---

## 5. Isolation gate (must be green before real client data)

```bash
PYTHONPATH=. python3 tests/test_isolation.py
```

- **Gate A (storage):** a client cannot read another client's object — private-bucket
  objects are not world-readable; only the owner's signed URL serves them.
- **Gate B (scoping):** a work code cannot reach an unassigned project by passing its id
  (`403`), and an assigned clinician can.

Both must pass. If either is hard to make pass, stop — do not weaken the test.

---

## Isolation notes & known limits

- **Signed-URL TTL:** default **7 days** (`storage.DEFAULT_SIGNED_URL_TTL`, override with
  `--ttl-days`). URLs **do not auto-refresh** — if a radiologist stays on a case past the
  TTL the image link expires; re-run *Send to Label Studio* to regenerate fresh URLs.
- **De-identification scope:** covers **object keys / filenames only** (hashed). It does
  **not** strip DICOM headers or burned-in pixel PHI — out of scope until we add DICOM
  ingest. Only send data that is already free of burned-in identifiers.
- **RLS (future hardening):** isolation is currently enforced at the **application layer**
  (`_labeler_can_access`) plus a **private storage bucket** with signed URLs — not full
  Postgres row-level security. Per-tenant DB RLS is planned hardening, not yet in place.
- **Audit failures are silent by design (future hardening):** audit writes are best-effort
  so a hiccup never blocks a labeling save (see `app/services/audit.py`). When the audit
  trail becomes a client deliverable, add monitoring/alerting on the logged audit-write
  failures so a silent audit outage surfaces before a client notices a gap.
