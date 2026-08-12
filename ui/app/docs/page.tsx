import type { Metadata } from 'next'
import './docs.css'

export const metadata: Metadata = {
  title: 'API · Senebiclabs',
  description:
    'Senebiclabs API: create a project, push items, poll status and results, and receive a signed webhook when a clinician-reviewed batch is delivered.',
  robots: { index: false },
}

const BASE = 'https://senebiclabs-api-777437555578.us-central1.run.app/api/v1/project'

function Code({ children }: { children: string }) {
  return (
    <pre className="docs-pre">
      <code>{children}</code>
    </pre>
  )
}

function C({ children }: { children: string }) {
  return <code className="ic">{children}</code>
}

export default function DocsPage() {
  return (
    <div className="docs-shell">
      {/* Sidebar */}
      <aside className="docs-side">
        <a href="/" className="docs-brand">Senebiclabs</a>
        <div className="docs-brand-sub">API reference</div>
        <nav className="docs-nav">
          <a href="#overview">Overview</a>
          <a href="#auth">Authentication</a>
          <div className="grp">Endpoints</div>
          <a href="#create">Create a project</a>
          <a href="#ingest">Push items</a>
          <a href="#results">Poll results</a>
          <a href="#webhooks">Webhooks</a>
          <div className="grp">Reference</div>
          <a href="#config">Task config</a>
          <a href="#errors">Errors and notes</a>
        </nav>
      </aside>

      {/* Content */}
      <main className="docs-main">
        <section id="overview">
          <h1>API</h1>
          <p className="docs-lead">
            Programmatic access for clients who integrate by code instead of the dashboard.
            Create a project, push a batch of items, poll for status and results, and
            optionally receive a signed webhook when a clinician-reviewed batch is delivered.
          </p>

          <p>Two kinds of project run on the same pipeline; your task config decides which:</p>
          <ul>
            <li><b>Evaluation:</b> each item carries a model output. Clinicians grade it, and results include an accuracy and safety scorecard.</li>
            <li><b>Labeling:</b> each item carries raw data. Clinicians apply your label schema, and results come back as clean content-and-label pairs to train on.</li>
          </ul>
          <p>The only difference is your task config and whether there is a model output to grade.</p>

          <h3>Base URL</h3>
          <Code>{BASE}</Code>
        </section>

        {/* Auth */}
        <section id="auth" className="docs-sec">
          <span className="docs-eyebrow">Authentication</span>
          <h2>Bearer API key</h2>
          <p>Every request carries your API key as a bearer token:</p>
          <Code>{`Authorization: Bearer <YOUR_API_KEY>`}</Code>
          <p>
            Your key is long-lived and tied to your account. Keep it secret. There are two
            ways to start: we set up the project and give you a <C>project_id</C> (managed),
            or you create it yourself with <C>POST /projects</C> (self-serve, below). One key
            can create and drive many projects.
          </p>
        </section>

        {/* Create */}
        <section id="create" className="docs-sec">
          <span className="docs-eyebrow">Endpoint</span>
          <h2>
            <span className="m m-post">POST</span>
            <span className="ep">/projects</span>
            <span className="tag">Create a project</span>
          </h2>
          <p>
            Define your own task and get back a <C>project_id</C> to push items to. Skip this
            if we set the project up for you.
          </p>
          <Code>{`curl -X POST "$BASE/projects" \\
  -H "Authorization: Bearer $API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "Clinical response evaluation",
    "eval_config": {
      "title": "Clinical response review",
      "reviewers_per_item": 3,
      "schema": {
        "input": "text",
        "context": [
          { "key": "scenario",   "label": "Patient message" },
          { "key": "prediction", "label": "Model response" }
        ],
        "classes": ["Routine", "Urgent", "Emergency"],
        "case_id_field": "case_id",
        "fields": {
          "verdict":         { "type": "single", "options": ["Correct", "Incorrect", "Partial"], "required": true },
          "corrected_label": { "type": "from_classes", "visible_when": "verdict!=Correct" },
          "safety":          { "type": "flag" },
          "notes":           { "type": "text" }
        }
      }
    },
    "webhook_url": "https://your-app.com/hooks/senebiclabs"
  }'`}</Code>
          <h3>Response</h3>
          <Code>{`{
  "ok": true,
  "project_id": "fc64fb22-...",
  "webhook_secret": "a28e0736cb92..."
}`}</Code>
          <p>
            <b>Save the <C>webhook_secret</C>.</b> It is returned once, only when you register
            a <C>webhook_url</C>, and is used to verify webhook authenticity (see{' '}
            <a href="#webhooks" style={{ color: '#fff' }}>Webhooks</a>). Treat it like a password.
          </p>
          <p>
            This example is an <b>evaluation</b> project: each item carries a <C>prediction</C>,
            clinicians return a <C>verdict</C> of <C>Correct</C>, <C>Incorrect</C>, or <C>Partial</C>,
            and the report scores accuracy. For a <b>labeling</b> project, omit <C>prediction</C> and set
            <C>fields</C> to the labels you want produced; the results come back as content-and-label
            pairs with no scorecard.
          </p>
        </section>

        {/* Ingest */}
        <section id="ingest" className="docs-sec">
          <span className="docs-eyebrow">Endpoint</span>
          <h2>
            <span className="m m-post">POST</span>
            <span className="ep">/ingest</span>
            <span className="tag">Push items</span>
          </h2>
          <p>
            Send a batch of items (for example, conversations). Each item is a JSON object
            whose fields match your task config. We tell you the exact fields at setup.
          </p>
          <Code>{`curl -X POST "$BASE/ingest" \\
  -H "Authorization: Bearer $API_KEY" \\
  -H "Content-Type: application/json" \\
  -H "Idempotency-Key: batch-2026-08-12-001" \\
  -d '{
    "project_id": "YOUR_PROJECT_ID",
    "items": [
      { "case_id": "case_001", "scenario": "patient message...", "prediction": "Routine" },
      { "case_id": "case_002", "scenario": "patient message...", "prediction": "Urgent" }
    ]
  }'`}</Code>
          <h3>Idempotency</h3>
          <p>
            Send an <C>Idempotency-Key</C> header with each batch. If a request times out and
            you retry with the same key, we recognise it and skip the insert, so a retry never
            creates duplicates. A repeated key returns:
          </p>
          <Code>{`{ "ok": true, "message": "Batch already ingested (idempotent)." }`}</Code>
          <p>
            Use a fresh key per distinct batch. Without a key, each call appends its items, so
            two identical calls would create duplicates.
          </p>
          <h3>Response</h3>
          <Code>{`{ "ok": true, "message": "Ingested 2 items." }`}</Code>
        </section>

        {/* Results */}
        <section id="results" className="docs-sec">
          <span className="docs-eyebrow">Endpoint</span>
          <h2>
            <span className="m m-get">GET</span>
            <span className="ep">/results</span>
            <span className="tag">Poll status and results</span>
          </h2>
          <p>
            Clinician review is done by people, so results are not instant. Poll this endpoint.
            <C>status</C> moves through{' '}
            <C>submitted, scoping, agreement, pilot, production, delivered</C>. Only{' '}
            <C>delivered</C> includes the report and items.
          </p>
          <Code>{`curl "$BASE/results?project_id=YOUR_PROJECT_ID" \\
  -H "Authorization: Bearer $API_KEY"`}</Code>
          <h3>While in review</h3>
          <Code>{`{ "ok": true, "project_id": "...", "status": "production", "total": 200, "done": 142 }`}</Code>
          <h3>When delivered</h3>
          <Code>{`{
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
    { "idx": 0, "content": { "case_id": "case_001", ... },
      "label": { "verdict": "Correct", ... }, "labeled_at": "..." }
  ]
}`}</Code>
          <p>
            With <C>reviewers_per_item</C> above 1, each item is reviewed by several clinicians
            and combined into a consensus. The report then adds a <C>qa</C> block with the mean
            inter-reviewer agreement and the count of items where reviewers disagreed and an
            expert adjudicated.
          </p>
          <div className="docs-callout">
            <p>
              <b>Scoring:</b> the accuracy <C>report</C> is computed for <b>evaluation</b> projects whose
              <C>verdict</C> uses <C>Correct</C> / <C>Incorrect</C> / <C>Partial</C> and whose items carry a
              <C>prediction</C>. A <b>labeling</b> project still returns every reviewed item in <C>items</C>
              as a content-and-label pair to train on; consume those and ignore the report.
            </p>
          </div>
        </section>

        {/* Webhooks */}
        <section id="webhooks" className="docs-sec">
          <span className="docs-eyebrow">Delivery</span>
          <h2>Webhooks <span className="tag">optional, signed</span></h2>
          <p>
            If you registered a <C>webhook_url</C>, we POST it once when the batch is delivered,
            so you do not have to poll. The body is the same shape as the delivered{' '}
            <C>GET /results</C> response:
          </p>
          <Code>{`POST https://your-app.com/hooks/senebiclabs
Content-Type: application/json
X-Senebiclabs-Signature: sha256=<hex>

{
  "event": "results.delivered",
  "project_id": "...",
  "company": "Your Company",
  "report": { ... },
  "items": [ ... ]
}`}</Code>

          <h3>Verify the signature</h3>
          <p>
            Every webhook carries an <C>X-Senebiclabs-Signature</C> header. It is an
            HMAC-SHA256 of the exact request body, keyed with your <C>webhook_secret</C>.
            Recompute it and compare in constant time before you trust the payload. This proves
            the request came from us and was not altered in transit.
          </p>
          <div className="docs-callout">
            <p>
              Compute over the <b>raw request bytes</b>, before any JSON parsing. Parsing and
              re-serialising can change the bytes and break the check.
            </p>
          </div>
          <Code>{`import hmac, hashlib

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
    ...`}</Code>
          <p>
            Return <C>2xx</C> to acknowledge. It is a single fire-and-forget call for now (no
            retries), so keep polling <C>GET /results</C> as the source of truth if delivery is
            critical.
          </p>
        </section>

        {/* Config reference */}
        <section id="config" className="docs-sec">
          <span className="docs-eyebrow">Reference</span>
          <h2>Task config</h2>
          <p>
            The <C>eval_config</C> defines what clinicians see and fill in. Key fields:
          </p>
          <ul>
            <li><C>input</C>: <C>text</C> (shows the <C>context</C> fields) or <C>image</C> (each item needs an <C>image</C> URL).</li>
            <li><C>context</C>: for text tasks, which data keys to show the clinician, in order.</li>
            <li><C>classes</C>: the label set used by <C>from_classes</C> and <C>structured</C> fields.</li>
            <li><C>case_id_field</C>: which item field ties a result back to your own record.</li>
            <li><C>reviewers_per_item</C>: how many clinicians review each item (default 1). Above 1 produces a consensus plus agreement stats.</li>
          </ul>
          <p><C>fields</C> is a map of what the clinician fills. Each has a <C>type</C>:</p>
          <ul>
            <li><C>single</C>: choose one of <C>options</C>.</li>
            <li><C>from_classes</C>: choose one of the project <C>classes</C>.</li>
            <li><C>structured</C>: yes or no, plus which finding (from classes).</li>
            <li><C>scale</C>: a rating from 1 to <C>max</C>.</li>
            <li><C>flag</C>: a single checkbox.</li>
            <li><C>text</C>: free-text notes.</li>
          </ul>
          <p>
            Any field can add <C>required: true</C> and <C>{'visible_when: "field!=value"'}</C>.
          </p>
        </section>

        {/* Errors */}
        <section id="errors" className="docs-sec">
          <span className="docs-eyebrow">Reference</span>
          <h2>Errors and notes</h2>
          <ul>
            <li><b>Errors:</b> <C>401</C> invalid or missing key, <C>403</C> project not on this key, <C>422</C> invalid config or items missing a required field, <C>503</C> service unavailable.</li>
            <li><b>Idempotency:</b> send an <C>Idempotency-Key</C> header per batch so retries are safe. Without one, each <C>/ingest</C> appends its items.</li>
            <li><b>Content shape</b> is up to you as long as it matches the configured task. For text review, typically <C>prompt</C> plus <C>output</C>. Add <C>case_id</C> to tie results back to your records.</li>
          </ul>
          <div className="docs-foot">
            <span className="docs-eyebrow">Questions? senebiclabs@gmail.com</span>
          </div>
        </section>
      </main>
    </div>
  )
}
