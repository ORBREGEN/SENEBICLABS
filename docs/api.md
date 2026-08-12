# Senebiclabs API

Programmatic access for clients who integrate by code instead of the dashboard.
Create a project, push items, poll for status and results, and optionally receive a
**signed** webhook when a clinician-reviewed batch is delivered.

> The canonical, always-current version of this reference is the web page at
> **https://senebiclabs.com/docs**. This file mirrors it.

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
      "reviewers_per_item": 5,
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

Returns:

```json
{
  "ok": true,
  "project_id": "fc64fb22-...",
  "webhook_secret": "a28e0736cb92..."
}
```

**Save the `webhook_secret`.** It is returned once, only when you register a
`webhook_url`, and is used to verify webhook authenticity (§4). Treat it like a
password.

### Config reference

- `input` — `"text"` (shows the `context` fields) or `"image"` (each item needs an
  `image` URL).
- `context` — text mode only: which data keys to show the clinician, in order.
- `classes` — the label set used by `from_classes` and `structured` fields.
- `case_id_field` — which item field ties a result back to your own record.
- `reviewers_per_item` — how many clinicians review each item (default `1`). Above 1
  produces a consensus plus inter-reviewer agreement stats in the report.
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
  -H "Idempotency-Key: batch-2026-08-12-001" \
  -d '{
    "project_id": "YOUR_PROJECT_ID",
    "items": [
      { "case_id": "conv_001", "prompt": "user message...", "output": "bot reply..." },
      { "case_id": "conv_002", "prompt": "user message...", "output": "bot reply..." }
    ]
  }'
```

- `items` — array of objects, fields must match the task config.

### Idempotency

Send an `Idempotency-Key` header with each batch. If a request times out and you
retry with the same key, we recognise it and skip the insert, so a retry never
creates duplicates. A repeated key returns:

```json
{ "ok": true, "message": "Batch already ingested (idempotent)." }
```

Use a fresh key per distinct batch. Without a key, each call appends its items, so
two identical calls would create duplicates.

Response on a new batch: `{ "ok": true, "message": "Ingested 2 items." }`

You can also register (or update) the delivery webhook here by passing a
`webhook_url` field in the body — but `POST /projects` is the usual place, and only
that response returns the `webhook_secret`.

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
  "report": {
    "accuracy": { "value": 0.8, "correct": 160, "assessable": 200 },
    "critical_misses": [ ... ],
    "per_class": { ... },
    "qa": { "mean_agreement": 0.86, "reviewers": 5, "disagreements": 12 }
  },
  "items": [
    { "idx": 0, "content": { "case_id": "conv_001", ... },
      "label": { "verdict": "Safe", ... }, "labeled_at": "..." }
  ]
}
```

With `reviewers_per_item` above 1, each item is reviewed by several clinicians and
combined into a consensus. The report then adds a `qa` block with the mean
inter-reviewer agreement and the count of items where reviewers disagreed and an
expert adjudicated.

---

## 4. Webhook (optional, signed) — we call you

If you registered a `webhook_url`, we `POST` it once when the batch is delivered. The
body is the same shape as the delivered `GET /results` response:

```
POST https://your-app.com/hooks/senebiclabs
Content-Type: application/json
X-Senebiclabs-Signature: sha256=<hex>

{
  "event": "results.delivered",
  "project_id": "...",
  "company": "Your Company",
  "report": { ... },
  "items": [ ... ]
}
```

### Verify the signature

Every webhook carries an `X-Senebiclabs-Signature` header: an HMAC-SHA256 of the exact
request body, keyed with your `webhook_secret`. Recompute it over the **raw request
bytes** (before any JSON parsing — re-serialising can change the bytes and break the
check) and compare in constant time before trusting the payload.

```python
import hmac, hashlib

def verify(raw_body: bytes, header: str, secret: str) -> bool:
    expected = "sha256=" + hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header or "")

# FastAPI example
@app.post("/hooks/senebiclabs")
async def hook(request: Request):
    raw = await request.body()
    sig = request.headers.get("X-Senebiclabs-Signature", "")
    if not verify(raw, sig, WEBHOOK_SECRET):
        raise HTTPException(status_code=401)
    payload = json.loads(raw)   # trusted from here
    ...
```

Return `2xx` to acknowledge. Single fire-and-forget call for now (no retries), so keep
polling `GET /results` as the source of truth if delivery is critical.

---

## Notes

- **Errors**: `401` invalid/missing key · `403` project not on this key ·
  `422` invalid config or items missing a required field · `503` service unavailable.
- **Idempotency**: send an `Idempotency-Key` header per batch so retries are safe.
  Without one, each `/ingest` appends its items.
- **Content shape** is up to you as long as it matches the configured task (for text
  review, typically `prompt` + `output`; add `case_id` to tie results to your records).
