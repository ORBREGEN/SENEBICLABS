# Eval Operations — onboarding a client (operator runbook)

How to take a new evaluation client (e.g. X-ray classification review) from first contact to
delivered, radiologist-reviewed results. **A new client onboards via config, not code.**

---

## The full lifecycle at a glance

The whole path, customer bookends included. The customer touches only steps 1 and 9;
everything between is operator-driven. **Steps 2–5 are deliberately manual for now** — do
them by hand for the first client before automating anything.

| # | Who | What happens | Where |
|---|-----|--------------|-------|
| 1 | **Customer** | Lands on `/evaluate`, submits a project | `POST /project/submit` → `project_submissions` (stage `submitted`) |
| 2 | Operator | Scope the deal, advance the stage, set the project's `eval_config` (label set + fields + conditionals) | `POST /project/admin/advance`, set `eval_config` |
| 3 | Operator | Ingest the client's images: private per-client storage, de-identified keys, signed URLs | `scripts/ingest_xray.py` → `project_items` |
| 4 | Operator | Create reviewers and **assign** them to the project | `POST /project/admin/clinicians` + `project_clinicians` |
| 5 | Operator | Generate the LS config and push tasks | `POST /ls/sync` → Label Studio |
| 6 | Reviewers | Annotate (X-ray: in Label Studio; other types: in-app `/work/*` queue) | LS UI / `/work/next` + `/work/label` |
| 7 | Operator | Pull annotations back; structured fields collapse; every write is audited | `POST /ls/pull` (or `/ls/webhook`) → `project_items.label` + `audit_events` |
| 8 | Operator | QA: progress, export, and the audit trail (who labeled/reviewed, when) | `/project/admin/progress`, `/admin/export`, `/admin/audit/{id}` |
| 9 | **Customer** | Once stage is `delivered`, sign in and download results | `/portal/request` → `/portal/projects` → `GET /project/portal/results` |

**One-line pipeline:**

```
/evaluate -> /submit -> project_submissions
   -> (operator: eval_config; ingest_xray.py -> private storage -> project_items)
   -> (operator: clinicians + project_clinicians assignment)
   -> /ls/sync -> Label Studio  <- reviewers annotate
   -> /ls/pull (+ collapse structured) -> project_items.label + audit_events
   -> operator QA via /admin/audit, /admin/export
   -> stage=delivered -> /portal/results -> customer downloads
```

Isolation and audit guarantees hold only against the **deployed** instance running this
code. Before ingesting any real client data: **deploy, then re-run the isolation gate tests
against the deployed instance**, not just locally (config can drift between environments).

---

## 0. One-time schema migration

Before the first client, apply `supabase_schema.sql` in the Supabase SQL editor. The
pipeline depends on three additions:

- `project_submissions.eval_config` (jsonb) — the per-project labeling schema.
- `project_clinicians` (table) — which clinicians are assigned to which project.
- `audit_events` (table) — the append-only audit trail.

The gate tests (`tests/test_isolation.py`, `tests/test_audit.py`) refuse to pass until these exist.

---

## 1. Customer submits the project

The customer lands on `/evaluate` and submits via `/submit` → `POST /project/submit`, which
creates a `project_submissions` row at stage `submitted` and emails a notification. This is
the only self-serve step; you drive everything from here.

---

## 2. Create the project + its eval_config

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

## 3. Ingest the client's images

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

## 4. Assign clinicians (required — creating the project does not grant access)

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

## 5. Send to Label Studio, reviewers annotate, then pull results

- **Send:** `/admin` → select the project → *Send to Label Studio* (`POST /ls/sync`). Creates
  the LS project from the generated config and pushes pending items as tasks.
- **Annotate:** reviewers label in Label Studio (X-ray) or the in-app `/work/*` queue (other
  task types). The brief + LS link come from `GET /project/work/brief`.
- **Pull:** `POST /ls/pull` (or the LS webhook) writes annotations back to `project_items`;
  structured fields (e.g. `critical_miss`) collapse into one object, and every write records
  an `audit_events` row (actor, source, value snapshot).

---

## 6. QA and deliver (step 9 is the customer's)

- **QA (operator):** review `/project/admin/progress`, the raw `/project/admin/export`, and
  the full audit trail at `GET /project/admin/audit/{project_id}` — who labeled/reviewed each
  item, with what value, through which channel, and when. Corrections re-run `/work/label`
  (the operator can label anything) and land as `review` events; nothing is overwritten silently.
- **Deliver:** advance the project to stage `delivered` (`POST /project/admin/advance`). The
  customer then requests a magic link (`/portal/request`), signs in (`/portal/projects`), and
  downloads via `GET /project/portal/results` — which enforces email ownership AND
  `stage == delivered` before returning any labels.

---

## 7. Isolation gate (must be green before real client data)

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
