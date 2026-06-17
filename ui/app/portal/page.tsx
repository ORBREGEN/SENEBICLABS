'use client'
import { useEffect, useState } from 'react'
import NavBar from '../components/NavBar'
import FooterSection from '../components/sections/FooterSection'
import Toast from '../components/ui/Toast'

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
}

const CheckMark = (
  <svg width="11" height="9" viewBox="0 0 11 9" fill="none" aria-hidden>
    <polyline points="1 5 4 8 10 1" stroke="var(--navy)" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
)

function Tracker({ project }: { project: Project }) {
  const current = Math.max(0, STAGES.findIndex(s => s.key === project.stage))
  return (
    <div className="pt-project">
      <h2 className="pt-company">{project.company || 'Your project'}</h2>
      {project.task_type && <p className="pt-services">{project.task_type}</p>}

      <div className="pt-status">
        <span className="micro" style={{ display: 'block', marginBottom: 8 }}>Current status</span>
        <div className="pt-status-stage">{STAGES[current].label}</div>
        <p className="pt-status-desc">{project.stage_note || STAGES[current].desc}</p>
      </div>

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

  useEffect(() => {
    const t = new URLSearchParams(window.location.search).get('token')
    setToken(t)
    setChecked(true)
    if (t) {
      setLoading(true)
      fetch(`/api/portal/projects?token=${encodeURIComponent(t)}`)
        .then(r => r.json())
        .then(data => {
          if (!data.ok) throw new Error(data.message ?? 'This link is no longer valid.')
          setProjects(data.projects ?? [])
        })
        .catch(err => setFetchError(err instanceof Error ? err.message : 'Could not load your project.'))
        .finally(() => setLoading(false))
    }
  }, [])

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
                {projects!.map(p => <Tracker key={p.id} project={p} />)}
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
