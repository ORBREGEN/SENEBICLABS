# Senebiclabs API

Programmatic access for clients who integrate by code instead of the dashboard.
Create a task, push items, poll for status and results, and optionally receive a
webhook when a clinician-reviewed batch is delivered.

**Base URL**

```
https://senebiclabs-api-777437555578.us-central1.run.app/api/v1/project
```

**Auth** — every request carries your API key as a bearer token:

```
Authorization: Bearer <YOUR_API_KEY>
```

Your API key is long-lived and tied to your account. Keep it secret. There are two
ways to start: we set up the project and give you a `project_id` (managed), or you
create it yourself with `POST /projects` (self-serve, §1). One key can create and
drive many projects.

---

## 1. Create a project (self-serve) — `POST /projects`

Define your own task and get back a `project_id` to push items to. Skip this if we
set the project up for you.

```bash
curl -X POST "$BASE/projects" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Heyrafiki safety review",
    "eval_config": {
      "title": "Response safety review",
      "schema": {
        "input": "text",
        "context": [
          { "key": "prompt", "label": "User message" },
          { "key": "output", "label": "Bot reply" }
        ],
        "classes": ["Safe", "Unsafe"],
        "case_id_field": "case_id",
        "fields": {
          "verdict":       { "type": "single", "options": ["Safe", "Unsafe"], "required": true },
          "correct_label": { "type": "from_classes", "visible_when": "verdict!=Safe" },
          "severity":      { "type": "scale", "max": 5 },
          "notes":         { "type": "text" }
        }
      }
    },
    "webhook_url": "https://your-app.com/hooks/senebiclabs"
  }'
```

Returns `{ "ok": true, "project_id": "..." }`.

### Config reference

- `input` — `"text"` (shows the `context` fields) or `"image"` (each item needs an
  `image` URL).
- `context` — text mode only: which data keys to show the clinician, in order.
- `classes` — the label set used by `from_classes` and `structured` fields.
- `case_id_field` — which item field ties a result back to your own record.
- `fields` — a map of what the clinician fills. Each has a `type`:
  - `single` — choose one of `options`
  - `from_classes` — choose one of the project `classes`
  - `structured` — yes/no plus which finding (from classes)
  - `scale` — a 1..`max` rating
  - `flag` — a single checkbox
  - `text` — free-text notes
- Optional on any field: `required: true`, `visible_when: "field!=value"`.

---

## 2. Push items — `POST /ingest`

Send a batch of items (e.g. conversations). Each item is a JSON object whose fields
match your task config.

```bash
curl -X POST "$BASE/ingest" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "YOUR_PROJECT_ID",
    "items": [
      { "case_id": "conv_001", "prompt": "user message...", "output": "bot reply..." },
      { "case_id": "conv_002", "prompt": "user message...", "output": "bot reply..." }
    ],
    "webhook_url": "https://your-app.com/hooks/senebiclabs"
  }'
```

- `items` — array of objects, fields must match the task config.
- `webhook_url` — optional; if set, we POST results here on delivery (§4).

Response: `{ "ok": true, "message": "Ingested 2 items." }`

---

## 3. Poll status + results — `GET /results`

Clinician review is done by people, so results are not instant. Poll this endpoint;
`status` moves through `submitted → scoping → agreement → pilot → production → delivered`.
Only `delivered` includes `report` and `items`.

```bash
curl "$BASE/results?project_id=YOUR_PROJECT_ID" \
  -H "Authorization: Bearer $API_KEY"
```

While in review:

```json
{ "ok": true, "project_id": "...", "status": "production", "total": 200, "done": 142 }
```

When delivered:

```json
{
  "ok": true,
  "project_id": "...",
  "status": "delivered",
  "total": 200,
  "done": 200,
  "report": { "accuracy": { "value": 0.8, "correct": 160, "assessable": 200 },
              "critical_misses": [ ... ], "per_class": { ... } },
  "items": [
    { "idx": 0, "content": { "case_id": "conv_001", ... },
      "label": { "verdict": "Safe", ... }, "labeled_at": "..." }
  ]
}
```

---

## 4. Webhook (optional) — we call you

If you registered a `webhook_url`, we `POST` it once when the batch is delivered:

```json
{
  "event": "results.delivered",
  "project_id": "...",
  "company": "Your Company",
  "report": { ... },
  "items": [ ... ]
}
```

Return `2xx` to acknowledge. Single fire-and-forget call for now (no retries), so
keep polling as the source of truth if delivery is critical.

---

## Notes

- **Errors**: `401` invalid/missing key · `403` project not on this key ·
  `422` invalid config or items missing a required field · `503` service unavailable.
- **Idempotency**: each `/ingest` appends items; sending the same batch twice creates
  duplicates. De-duplicate on your side or send each batch once.
- **Content shape** is up to you as long as it matches the configured task (for text
  review, typically `prompt` + `output`; add `case_id` to tie results to your records).
