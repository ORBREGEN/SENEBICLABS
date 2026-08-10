import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'API · Senebiclabs',
  description: 'Senebiclabs API: push items, poll status and results, and receive a webhook when a clinician-reviewed batch is delivered.',
  robots: { index: false },
}

const MONO = 'ui-monospace, "SF Mono", Menlo, Consolas, monospace'
const BASE = 'https://senebiclabs-api-777437555578.us-central1.run.app/api/v1/project'

const wrap: React.CSSProperties = { maxWidth: 820, margin: '0 auto', padding: 'clamp(40px, 8vw, 96px) 22px 120px' }
const eyebrow: React.CSSProperties = { fontFamily: MONO, fontSize: 11, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--slate)' }
const h2: React.CSSProperties = { fontSize: 'clamp(22px, 3vw, 28px)', fontWeight: 600, letterSpacing: '-0.01em', margin: '0 0 14px' }
const h3: React.CSSProperties = { fontSize: 16, fontWeight: 600, margin: '0 0 6px' }
const p: React.CSSProperties = { fontSize: 15, lineHeight: 1.7, color: 'rgba(255,255,255,0.72)', margin: '0 0 14px', maxWidth: '68ch' }
const section: React.CSSProperties = { marginTop: 'clamp(44px, 6vw, 72px)', paddingTop: 'clamp(36px, 5vw, 56px)', borderTop: '1px solid var(--hairline)' }
const inlineCode: React.CSSProperties = { fontFamily: MONO, fontSize: '0.86em', background: 'rgba(255,255,255,0.06)', border: '1px solid var(--hairline)', borderRadius: 5, padding: '1px 6px', color: '#e2e8f0' }

function Code({ children }: { children: string }) {
  return (
    <pre style={{ background: '#0d1117', border: '1px solid var(--hairline)', borderRadius: 10, padding: '16px 18px', overflowX: 'auto', margin: '0 0 18px' }}>
      <code style={{ fontFamily: MONO, fontSize: 12.5, lineHeight: 1.7, color: '#e2e8f0', whiteSpace: 'pre' }}>{children}</code>
    </pre>
  )
}

export default function DocsPage() {
  return (
    <main style={wrap}>
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
        <a href="/" style={{ fontSize: 18, fontWeight: 640, letterSpacing: '-0.01em', color: 'var(--ink)', textDecoration: 'none' }}>Senebiclabs</a>
        <span style={eyebrow}>API reference</span>
      </div>

      <h1 style={{ fontSize: 'clamp(30px, 5vw, 44px)', fontWeight: 620, letterSpacing: '-0.02em', margin: '36px 0 16px' }}>API</h1>
      <p style={{ ...p, fontSize: 17 }}>
        Programmatic access for clients who integrate by code instead of the dashboard.
        Push items to a project, poll for status and results, and optionally receive a
        webhook when a clinician-reviewed batch is delivered.
      </p>

      <div style={{ marginTop: 28 }}>
        <span style={eyebrow}>Base URL</span>
        <Code>{BASE}</Code>
        <span style={eyebrow}>Auth</span>
        <p style={{ ...p, margin: '10px 0 8px' }}>Every request carries your API key as a bearer token:</p>
        <Code>{`Authorization: Bearer <YOUR_API_KEY>`}</Code>
        <p style={p}>
          Your API key is long-lived and tied to your account. Keep it secret. There are
          two ways to start: we set up the project and give you a <code style={inlineCode}>project_id</code>
          {' '}(managed), or you create it yourself with <code style={inlineCode}>POST /projects</code> (self-serve, below).
        </p>
      </div>

      {/* Create project */}
      <section style={section}>
        <span style={eyebrow}>1</span>
        <h2 style={h2}>Create a project <span style={{ ...eyebrow, textTransform: 'none', letterSpacing: 0, color: 'var(--slate)', fontSize: 14 }}>(self-serve)</span> <code style={{ ...inlineCode, fontSize: '0.7em' }}>POST /projects</code></h2>
        <p style={p}>
          Define your own task and get back a <code style={inlineCode}>project_id</code> to push items to.
          Skip this if we set the project up for you.
        </p>
        <Code>{`curl -X POST "$BASE/projects" \\
  -H "Authorization: Bearer $API_KEY" \\
  -H "Content-Type: application/json" \\
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
  }'`}</Code>
        <p style={p}>Returns <code style={inlineCode}>{`{ "ok": true, "project_id": "..." }`}</code>. Then push items to it (below).</p>
        <h3 style={h3}>Config reference</h3>
        <p style={p}>
          <code style={inlineCode}>input</code>: <code style={inlineCode}>&quot;text&quot;</code> (shows the <code style={inlineCode}>context</code> fields) or
          {' '}<code style={inlineCode}>&quot;image&quot;</code> (each item needs an <code style={inlineCode}>image</code> URL).
          {' '}<code style={inlineCode}>fields</code> is a map of what the clinician fills; each has a <code style={inlineCode}>type</code>:
        </p>
        <ul style={{ ...p, paddingLeft: 20 }}>
          <li><code style={inlineCode}>single</code> — choose one of <code style={inlineCode}>options</code></li>
          <li><code style={inlineCode}>from_classes</code> — choose one of the project <code style={inlineCode}>classes</code></li>
          <li><code style={inlineCode}>structured</code> — yes/no plus which finding (from classes)</li>
          <li><code style={inlineCode}>scale</code> — a 1..<code style={inlineCode}>max</code> rating</li>
          <li><code style={inlineCode}>flag</code> — a single checkbox</li>
          <li><code style={inlineCode}>text</code> — free-text notes</li>
        </ul>
        <p style={p}>
          <code style={inlineCode}>required: true</code> and <code style={inlineCode}>visible_when: &quot;field!=value&quot;</code> are optional on any field.
        </p>
      </section>

      {/* Ingest */}
      <section style={section}>
        <span style={eyebrow}>2</span>
        <h2 style={h2}>Push items <code style={{ ...inlineCode, fontSize: '0.7em' }}>POST /ingest</code></h2>
        <p style={p}>
          Send a batch of items (for example, conversations). Each item is a JSON object whose
          fields match your project&rsquo;s task config (we tell you the exact fields at setup).
        </p>
        <Code>{`curl -X POST "$BASE/ingest" \\
  -H "Authorization: Bearer $API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "project_id": "YOUR_PROJECT_ID",
    "items": [
      { "case_id": "conv_001", "prompt": "user message...", "output": "bot reply..." },
      { "case_id": "conv_002", "prompt": "user message...", "output": "bot reply..." }
    ],
    "webhook_url": "https://your-app.com/hooks/senebiclabs"
  }'`}</Code>
        <p style={p}>
          <code style={inlineCode}>webhook_url</code> is optional. If set, we POST the results
          there when the batch is delivered (see section 3). Registering it once is enough.
        </p>
        <h3 style={h3}>Response</h3>
        <Code>{`{ "ok": true, "message": "Ingested 2 items." }`}</Code>
      </section>

      {/* Results */}
      <section style={section}>
        <span style={eyebrow}>3</span>
        <h2 style={h2}>Poll status and results <code style={{ ...inlineCode, fontSize: '0.7em' }}>GET /results</code></h2>
        <p style={p}>
          Clinician review is done by people, so results are not instant. Poll this endpoint.
          <code style={inlineCode}>status</code> moves through
          {' '}<code style={inlineCode}>submitted &rarr; scoping &rarr; agreement &rarr; pilot &rarr; production &rarr; delivered</code>.
          Only <code style={inlineCode}>delivered</code> includes the report and items.
        </p>
        <Code>{`curl "$BASE/results?project_id=YOUR_PROJECT_ID" \\
  -H "Authorization: Bearer $API_KEY"`}</Code>
        <h3 style={h3}>While in review</h3>
        <Code>{`{ "ok": true, "project_id": "...", "status": "production", "total": 200, "done": 142 }`}</Code>
        <h3 style={h3}>When delivered</h3>
        <Code>{`{
  "ok": true,
  "project_id": "...",
  "status": "delivered",
  "total": 200,
  "done": 200,
  "report": {
    "accuracy": { "value": 0.8, "correct": 160, "assessable": 200 },
    "critical_misses": [ ... ],
    "per_class": { ... }
  },
  "items": [
    { "idx": 0, "content": { "case_id": "conv_001", ... },
      "label": { "verdict": "Correct", ... }, "labeled_at": "..." }
  ]
}`}</Code>
      </section>

      {/* Webhook */}
      <section style={section}>
        <span style={eyebrow}>4</span>
        <h2 style={h2}>Webhook <span style={{ ...eyebrow, textTransform: 'none', letterSpacing: 0, color: 'var(--slate)', fontSize: 14 }}>(optional)</span></h2>
        <p style={p}>
          If you registered a <code style={inlineCode}>webhook_url</code>, we POST it once when the
          batch is delivered, so you do not have to poll:
        </p>
        <Code>{`{
  "event": "results.delivered",
  "project_id": "...",
  "company": "Your Company",
  "report": { ... },
  "items": [ ... ]
}`}</Code>
        <p style={p}>
          Return <code style={inlineCode}>2xx</code> to acknowledge. It is a single fire-and-forget
          call for now (no retries), so keep polling as the source of truth if delivery is critical.
        </p>
      </section>

      {/* Errors */}
      <section style={section}>
        <span style={eyebrow}>Notes</span>
        <ul style={{ ...p, paddingLeft: 20 }}>
          <li style={{ marginBottom: 8 }}><b style={{ color: 'var(--ink)' }}>Errors:</b> <code style={inlineCode}>401</code> invalid or missing key, <code style={inlineCode}>403</code> project not on this key, <code style={inlineCode}>422</code> items missing a field the task needs, <code style={inlineCode}>503</code> service unavailable.</li>
          <li style={{ marginBottom: 8 }}><b style={{ color: 'var(--ink)' }}>Idempotency:</b> each <code style={inlineCode}>/ingest</code> appends items. Sending the same batch twice creates duplicates, so send each batch once.</li>
          <li><b style={{ color: 'var(--ink)' }}>Content shape</b> is up to you as long as it matches the configured task. For text review, typically <code style={inlineCode}>prompt</code> + <code style={inlineCode}>output</code>. Add <code style={inlineCode}>case_id</code> to tie results back to your own records.</li>
        </ul>
      </section>

      <p style={{ ...eyebrow, marginTop: 64 }}>Questions? senebiclabs@gmail.com</p>
    </main>
  )
}
