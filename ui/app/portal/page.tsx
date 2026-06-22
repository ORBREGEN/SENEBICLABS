'use client'
import { useEffect, useState, useCallback } from 'react'
import NavBar from '../components/NavBar'
import FooterSection from '../components/sections/FooterSection'
import Toast from '../components/ui/Toast'
import { parseDataset, type ParsedDataset } from '../lib/dataset'

const dropzone: React.CSSProperties = {
  display: 'block', border: '1px dashed var(--hairline-strong)', borderRadius: 12,
  padding: '26px 20px', textAlign: 'center', cursor: 'pointer',
}

const STAGES = [
  { key: 'submitted',  label: 'Submitted',     desc: 'We have your project and are reviewing it.' },
  { key: 'scoping',    label: 'Scoping call',  desc: 'We align on your data, accuracy target, and timeline.' },
  { key: 'agreement',  label: 'Agreement',     desc: 'NDA and work agreement signed.' },
  { key: 'pilot',      label: 'Pilot sample',  desc: 'Specialists label a small batch for your review.' },
  { key: 'production', label: 'Production',    desc: 'The full batch is labeled, with quality control on every task.' },
  { key: 'delivered',  label: 'Delivered',     desc: 'Your labeled data is handed back, ready for your models.' },
]

type Project = {
  id: string
  company: string | null
  description: string | null
  task_type: string | null
  stage: string
  stage_note: string | null
  created_at: string | null
  total: number
  done: number
}

const CheckMark = (
  <svg width="11" height="9" viewBox="0 0 11 9" fill="none" aria-hidden>
    <polyline points="1 5 4 8 10 1" stroke="var(--navy)" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
)

function DataUpload({ project, token, onUploaded }: { project: Project; token: string; onUploaded: () => void }) {
  const [parsed, setParsed] = useState<(ParsedDataset & { filename: string }) | null>(null)
  const [err, setErr] = useState('')
  const [uploading, setUploading] = useState(false)
  const [msg, setMsg] = useState('')

  const onFile = async (file: File) => {
    setErr(''); setMsg('')
    try {
      const text = await file.text()
      const { items, columns } = parseDataset(file.name, text)
      if (!items.length) throw new Error('No rows found in that file.')
      setParsed({ items, columns, filename: file.name })
    } catch (e: unknown) {
      setParsed(null)
      setErr(e instanceof Error ? e.message : 'Could not read that file.')
    }
  }

  const upload = async () => {
    if (!parsed) return
    setUploading(true); setErr('')
    try {
      const res = await fetch('/api/portal/items', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, project_id: project.id, items: parsed.items }),
      })
      const data = await res.json()
      if (!data.ok) throw new Error(data.message ?? 'Upload failed.')
      setMsg(data.message)
      setParsed(null)
      onUploaded()
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Upload failed.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div style={{ marginTop: 28 }}>
      <span className="micro" style={{ display: 'block', marginBottom: 10 }}>Your data</span>
      {project.total > 0 ? (
        <p style={{ fontSize: 15, color: 'var(--ink)', marginBottom: 14 }}>
          <strong>{project.total.toLocaleString()} tasks</strong> uploaded · {project.done.toLocaleString()} labeled
        </p>
      ) : (
        <p style={{ fontSize: 14.5, color: 'var(--ink)', lineHeight: 1.6, marginBottom: 14 }}>
          No data uploaded yet. Upload your dataset and each row becomes one labeling task.
        </p>
      )}

      {!parsed ? (
        <label style={dropzone}
          onDragOver={e => e.preventDefault()}
          onDrop={e => { e.preventDefault(); const f = e.dataTransfer.files?.[0]; if (f) onFile(f) }}
        >
          <input type="file" accept=".csv,.json,text/csv,application/json" style={{ display: 'none' }}
            onChange={e => { const f = e.target.files?.[0]; if (f) onFile(f); e.target.value = '' }} />
          <span style={{ color: 'var(--ink)', fontWeight: 500, fontSize: 15 }}>Drop a CSV or JSON file</span>
          <span style={{ display: 'block', marginTop: 6, fontSize: 13, color: 'var(--slate)' }}>or click to browse · each row becomes one task</span>
        </label>
      ) : (
        <div style={{ border: '1px solid var(--hairline-strong)', borderRadius: 12, padding: 18 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 12, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 15, fontWeight: 600 }}>{parsed.filename}</span>
            <span className="micro">{parsed.items.length.toLocaleString()} rows</span>
          </div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 12 }}>
            {parsed.columns.map(c => (
              <span key={c} className="micro" style={{ border: '1px solid var(--hairline-strong)', borderRadius: 999, padding: '4px 10px' }}>{c}</span>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 14, marginTop: 16, alignItems: 'center', flexWrap: 'wrap' }}>
            <button className="sf-submit" onClick={upload} disabled={uploading} style={{ padding: '11px 20px', fontSize: 14 }}>
              {uploading ? 'Uploading…' : `Upload ${parsed.items.length.toLocaleString()} tasks`}
            </button>
            <button onClick={() => setParsed(null)} className="micro" style={{ background: 'none', border: 'none', cursor: 'pointer' }}>Choose another file</button>
          </div>
        </div>
      )}
      {err && <p style={{ color: '#dc2626', fontSize: 13, marginTop: 10 }}>{err}</p>}
      {msg && <p className="micro" style={{ marginTop: 12 }}>{msg}</p>}
    </div>
  )
}

type ResultItem = { idx: number; content: Record<string, unknown>; label: Record<string, unknown> | null; labeled_at: string | null }

function toCSV(items: ResultItem[]): string {
  if (!items.length) return ''
  const ck = new Set<string>(), lk = new Set<string>()
  for (const it of items) {
    Object.keys(it.content ?? {}).forEach(k => ck.add(k))
    Object.keys(it.label ?? {}).forEach(k => { if (k !== '_result') lk.add(k) })
  }
  const cols = Array.from(ck), labs = Array.from(lk)
  const esc = (v: unknown) => {
    const s = v == null ? '' : typeof v === 'object' ? JSON.stringify(v) : String(v)
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
  }
  const headers = ['idx', ...cols, ...labs.map(k => `label_${k}`), 'labeled_at']
  const lines = [headers.join(',')]
  for (const it of items) {
    lines.push([
      it.idx,
      ...cols.map(k => esc(it.content?.[k])),
      ...labs.map(k => esc(it.label?.[k])),
      esc(it.labeled_at),
    ].join(','))
  }
  return lines.join('\n')
}

function ResultsDownload({ project, token }: { project: Project; token: string }) {
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')

  const download = async (fmt: 'json' | 'csv') => {
    setBusy(true); setErr('')
    try {
      const res = await fetch(`/api/portal/results?token=${encodeURIComponent(token)}&project=${encodeURIComponent(project.id)}`)
      const data = await res.json()
      if (!data.ok) throw new Error(data.message ?? 'Could not download results.')
      const items: ResultItem[] = data.items ?? []
      const base = (project.company || 'results').replace(/\s+/g, '_')
      const blob = fmt === 'json'
        ? new Blob([JSON.stringify(items, null, 2)], { type: 'application/json' })
        : new Blob([toCSV(items)], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = `${base}_results.${fmt}`; a.click()
      URL.revokeObjectURL(url)
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Could not download results.')
    } finally { setBusy(false) }
  }

  const btn: React.CSSProperties = { padding: '11px 18px', borderRadius: 10, fontSize: 14, fontWeight: 600, cursor: 'pointer', border: '1px solid #111', background: '#111', color: '#fff' }
  const ghost: React.CSSProperties = { ...btn, background: '#fff', color: '#111' }

  return (
    <div className="pt-status" style={{ marginTop: 24, border: '1px solid #d9f0e0', background: '#f4fbf6', borderRadius: 14, padding: '18px 20px' }}>
      <span className="micro" style={{ display: 'block', marginBottom: 6, color: '#15803d' }}>Results ready</span>
      <p className="pt-status-desc" style={{ marginBottom: 14 }}>Your annotated dataset is complete. Download it below.</p>
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        <button style={btn} onClick={() => download('json')} disabled={busy}>{busy ? 'Preparing…' : 'Download JSON'}</button>
        <button style={ghost} onClick={() => download('csv')} disabled={busy}>Download CSV</button>
      </div>
      {err && <p style={{ color: '#dc2626', fontSize: 13, marginTop: 10 }}>{err}</p>}
    </div>
  )
}

function Tracker({ project, token, onUploaded }: { project: Project; token: string; onUploaded: () => void }) {
  const current = Math.max(0, STAGES.findIndex(s => s.key === project.stage))
  return (
    <div className="pt-project">
      <h2 className="pt-company">{project.company || 'Your project'}</h2>
      {project.task_type && <p className="pt-services">{project.task_type}</p>}

      <DataUpload project={project} token={token} onUploaded={onUploaded} />

      <div className="pt-status" style={{ marginTop: 28 }}>
        <span className="micro" style={{ display: 'block', marginBottom: 8 }}>Current status</span>
        <div className="pt-status-stage">{STAGES[current].label}</div>
        <p className="pt-status-desc">{project.stage_note || STAGES[current].desc}</p>
      </div>

      {project.stage === 'delivered' && <ResultsDownload project={project} token={token} />}

      {project.description && (
        <div className="pt-brief">
          <span className="micro" style={{ display: 'block', marginBottom: 8 }}>Your brief</span>
          <p className="pt-desc">{project.description}</p>
        </div>
      )}

      <span className="micro" style={{ display: 'block', margin: '28px 0 18px' }}>Progress</span>
      <div className="pt-steps">
        {STAGES.map((s, i) => {
          const state = i < current ? 'done' : i === current ? 'current' : 'upcoming'
          return (
            <div className={`pt-step ${state}`} key={s.key}>
              <div className="pt-rail">
                <span className="pt-dot">{state === 'done' && CheckMark}</span>
                {i < STAGES.length - 1 && <span className="pt-bar" />}
              </div>
              <div className="pt-body">
                <div className="pt-label">{s.label}</div>
                <div className="pt-sub">{s.desc}</div>
                {state === 'current' && project.stage_note && (
                  <div className="pt-note">{project.stage_note}</div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default function PortalPage() {
  const [token, setToken] = useState<string | null>(null)
  const [checked, setChecked] = useState(false)        // finished reading the URL
  const [loading, setLoading] = useState(false)
  const [projects, setProjects] = useState<Project[] | null>(null)
  const [fetchError, setFetchError] = useState('')

  const [email, setEmail] = useState('')
  const [requesting, setRequesting] = useState(false)
  const [requested, setRequested] = useState(false)
  const [reqError, setReqError] = useState('')

  const loadProjects = useCallback((t: string) => {
    setLoading(true)
    fetch(`/api/portal/projects?token=${encodeURIComponent(t)}`)
      .then(r => r.json())
      .then(data => {
        if (!data.ok) throw new Error(data.message ?? 'This link is no longer valid.')
        setProjects(data.projects ?? [])
      })
      .catch(err => setFetchError(err instanceof Error ? err.message : 'Could not load your project.'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    const t = new URLSearchParams(window.location.search).get('token')
    setToken(t)
    setChecked(true)
    if (t) loadProjects(t)
  }, [loadProjects])

  const requestLink = async (e: React.FormEvent) => {
    e.preventDefault()
    if (requesting) return
    setRequesting(true)
    setReqError('')
    try {
      const res = await fetch('/api/portal/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      })
      const data = await res.json()
      if (!data.ok) throw new Error(data.message ?? '')
      setRequested(true)
    } catch (err: unknown) {
      setReqError(err instanceof Error ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setRequesting(false)
    }
  }

  const showProjects = token && projects && projects.length > 0
  const showEmailForm = checked && (!token || !!fetchError)

  return (
    <>
      <div className="submit-light">
        <NavBar onLight />

        <section className="submit-section">
          <div className="wrap" style={{ maxWidth: 760 }}>
            <span className="micro" style={{ display: 'block', color: 'var(--ink)', marginBottom: 28 }}>Customer portal</span>
            <h1 style={{
              fontFamily: 'Geist, sans-serif',
              fontWeight: 300,
              fontSize: 'clamp(38px, 4.6vw, 60px)',
              lineHeight: 1.06,
              letterSpacing: '0.01em',
              marginBottom: 24,
            }}>
              Your project.
            </h1>

            {/* Loading */}
            {token && loading && (
              <p style={{ fontSize: 17, color: 'var(--ink)', lineHeight: 1.7 }}>Loading your project…</p>
            )}

            {/* Projects */}
            {showProjects && (
              <div style={{ marginTop: 44 }}>
                {projects!.map(p => <Tracker key={p.id} project={p} token={token!} onUploaded={() => loadProjects(token!)} />)}
                <p style={{ fontSize: 14.5, color: 'var(--ink)', lineHeight: 1.6, marginTop: 8 }}>
                  Questions about your project? Just reply to any email from us.
                </p>
              </div>
            )}

            {/* Token but no projects */}
            {token && !loading && projects && projects.length === 0 && (
              <p style={{ fontSize: 17, color: 'var(--ink)', lineHeight: 1.7, marginTop: 20 }}>
                We could not find a project tied to this link. If you have submitted one, request a fresh link below.
              </p>
            )}

            {/* Email request form (no token, or expired/invalid token) */}
            {showEmailForm && !showProjects && (
              <div style={{ maxWidth: 460, marginTop: token ? 40 : 8 }}>
                {fetchError && (
                  <p style={{ fontSize: 16, color: 'var(--ink)', lineHeight: 1.7, marginBottom: 28 }}>{fetchError}</p>
                )}
                {!fetchError && (
                  <p style={{ fontSize: 18, color: 'var(--ink)', lineHeight: 1.75, marginBottom: 36 }}>
                    Enter the email you submitted your project with. We will send you a secure sign-in link.
                  </p>
                )}

                {requested ? (
                  <div className="sf-success">
                    <svg className="sf-success-icon" width="22" height="22" viewBox="0 0 20 20" fill="none">
                      <circle cx="10" cy="10" r="9" stroke="currentColor" strokeWidth="1.3" />
                      <polyline points="6 10.5 9 13.5 14 7" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    <div>
                      <h4>Check your inbox.</h4>
                      <p>If that email has a project with us, a sign-in link is on its way. It is valid for 14 days.</p>
                    </div>
                  </div>
                ) : (
                  <form onSubmit={requestLink} className="sf-form">
                    <div className="sf-field">
                      <label className="sf-label" htmlFor="email">Work email</label>
                      <input id="email" className="sf-input" type="email" value={email} onChange={e => setEmail(e.target.value)} required disabled={requesting} autoComplete="email" />
                    </div>
                    <button className="sf-submit" type="submit" disabled={requesting}>
                      {requesting ? 'Sending…' : 'Email me a sign-in link'}
                    </button>
                  </form>
                )}

                {reqError && <Toast message={reqError} onDismiss={() => setReqError('')} />}
              </div>
            )}
          </div>
        </section>

        <FooterSection />
      </div>
    </>
  )
}
