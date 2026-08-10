# Senebiclabs API

Programmatic access for clients who integrate by code instead of the dashboard.
Push items to a project, poll for status and results, and optionally receive a
webhook when a batch is reviewed and delivered.

**Base URL**

```
https://senebiclabs-api-777437555578.us-central1.run.app/api/v1/project
```

**Auth** — every request carries your API key as a bearer token:

```
Authorization: Bearer <YOUR_API_KEY>
```

Your API key and `project_id` are issued by Senebiclabs (one project per engagement).
The key is long-lived; keep it secret.

---

## 1. Push items — `POST /ingest`

Send a batch of items (e.g. conversations) to your project. Each item is a JSON
object; its fields are whatever your task config expects.

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

- `items` — array of objects. Fields must match the project's task config
  (we tell you the exact fields when we set up the project).
- `webhook_url` — optional. If set, we POST the results here when the batch is
  delivered (see §3). Registering it once is enough; you can omit it afterward.

Response:

```json
{ "ok": true, "message": "Ingested 2 items." }
```

---

## 2. Poll status + results — `GET /results`

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
      "label": { "verdict": "Correct", ... }, "labeled_at": "..." }
  ]
}
```

Poll every few minutes; a batch typically delivers within the agreed turnaround.

---

## 3. Webhook (optional) — we call you

If you registered a `webhook_url`, we `POST` it once when the batch is delivered,
so you do not have to poll:

```json
{
  "event": "results.delivered",
  "project_id": "...",
  "company": "Your Company",
  "report": { ... },
  "items": [ ... ]
}
```

Return `2xx` to acknowledge. It is a single fire-and-forget call for now (no
retries), so keep polling as the source of truth if delivery is critical.

---

## Notes

- **Errors**: `401` invalid/missing key · `403` project not on this key ·
  `422` items missing a field the task needs · `503` service unavailable.
- **Idempotency**: each `/ingest` call appends items; sending the same batch twice
  creates duplicates. De-duplicate on your side or send each batch once.
- **Content shape** is up to you as long as it matches the configured task
  (for text review, typically `prompt` + `output`; add `case_id` to tie results
  back to your own records).
