'use client'
import { useState } from 'react'
import NavBar from '../components/NavBar'
import EvalFooter from '../components/EvalFooter'
import Toast from '../components/ui/Toast'

const TASK_TYPES = [
  'Medical Image Annotation and Curation',
  'Clinical Text Labeling and Extraction',
  'Data Generation and RLHF for Medical LLMs',
  'Model Test and Evaluation for Healthcare AI',
  'Genomics and Omics Annotation',
  'De-identification and PHI Redaction',
  'Expert Clinical Review and Second Opinion',
  'Other',
]

const POINTS = [
  {
    heading: 'We review and scope',
    body: 'We come back within one business day with a short call to scope a small pilot, before you commit to anything larger.',
  },
  {
    heading: 'Specialists do the work',
    body: 'Credentialed medical specialists label your data on our platform, with gold-standard checks and agreement built into every task.',
  },
  {
    heading: 'You get data you can trust',
    body: 'We deliver labeled data with quality metrics attached, ready to train or evaluate your models.',
  },
]

type Form = {
  name: string; email: string; company: string; description: string
  task_type: string[]; sample_link: string
}

const check = (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden style={{ flexShrink: 0, marginTop: 2 }}>
    <circle cx="8" cy="8" r="7.25" stroke="var(--teal)" strokeWidth="1.1" />
    <polyline points="5 8.2 7.2 10.4 11 6" stroke="var(--teal)" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
)

export default function SubmitPage() {
  const [form, setForm] = useState<Form>({
    name: '', email: '', company: '', description: '',
    task_type: [], sample_link: '',
  })
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)
  const [error, setError] = useState('')

  const set = (k: 'name' | 'email' | 'company' | 'description' | 'sample_link') =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      setForm({ ...form, [k]: e.target.value })

  const toggle = (v: string) =>
    setForm(f => ({ ...f, task_type: f.task_type.includes(v) ? f.task_type.filter(x => x !== v) : [...f.task_type, v] }))

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (loading) return
    setLoading(true)
    setError('')
    try {
      const res = await fetch('/api/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...form,
          task_type: form.task_type.join(', '),
        }),
      })
      const data = await res.json()
      if (!data.ok) throw new Error(data.message ?? '')
      setDone(true)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <div className="submit-light">
      <NavBar minimal onLight />

      <section className="submit-section">
        <div className="wrap">
          <div className="submit-split">

            {/* Left — copy */}
            <div className="submit-copy">
              <span className="micro" style={{ display: 'block', color: 'var(--ink)', marginBottom: 28 }}>For companies</span>
              <h1 style={{
                fontFamily: 'Geist, sans-serif',
                fontWeight: 300,
                fontSize: 'clamp(38px, 4.6vw, 60px)',
                lineHeight: 1.06,
                letterSpacing: '0.01em',
                textWrap: 'balance',
                marginBottom: 24,
              }}>
                Let&rsquo;s build your dataset.
              </h1>
              <p style={{ fontSize: 18, color: 'var(--ink)', lineHeight: 1.75, maxWidth: 480, marginBottom: 44 }}>
                Tell us what you need annotated. We match it to credentialed medical
                specialists, run it through quality control, and deliver labeled data
                ready for your models. Every project starts with a small pilot.
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 26, maxWidth: 460 }}>
                {POINTS.map(p => (
                  <div key={p.heading} style={{ display: 'flex', gap: 14 }}>
                    {check}
                    <div>
                      <h3 style={{ fontSize: 16, fontWeight: 500, letterSpacing: '-0.01em', marginBottom: 5 }}>{p.heading}</h3>
                      <p style={{ fontSize: 14.5, lineHeight: 1.65, color: 'var(--slate)' }}>{p.body}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right — form */}
            <div className="submit-form-col">
              <span className="micro" style={{ display: 'block', color: 'var(--slate)', marginBottom: 18 }}>Project details</span>

              {done ? (
                <div className="sf-success">
                  <svg className="sf-success-icon" width="22" height="22" viewBox="0 0 20 20" fill="none">
                    <circle cx="10" cy="10" r="9" stroke="currentColor" strokeWidth="1.3" />
                    <polyline points="6 10.5 9 13.5 14 7" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  <div>
                    <h4>Project received.</h4>
                    <p>Thanks, {form.name.split(' ')[0] || 'there'}. We will be in touch within one business day to scope your pilot. Watch your inbox for a confirmation.</p>
                  </div>
                </div>
              ) : (
                <form onSubmit={submit} className="sf-form">
                  <div className="sf-row">
                    <div className="sf-field">
                      <label className="sf-label" htmlFor="name">Your name *</label>
                      <input id="name" className="sf-input" value={form.name} onChange={set('name')} required disabled={loading} autoComplete="name" />
                    </div>
                    <div className="sf-field">
                      <label className="sf-label" htmlFor="email">Work email *</label>
                      <input id="email" className="sf-input" type="email" value={form.email} onChange={set('email')} required disabled={loading} autoComplete="email" />
                    </div>
                  </div>

                  <div className="sf-field">
                    <label className="sf-label" htmlFor="company">Company *</label>
                    <input id="company" className="sf-input" value={form.company} onChange={set('company')} required disabled={loading} autoComplete="organization" />
                  </div>

                  <div className="sf-field">
                    <label className="sf-label">What can we help with? <span className="opt">Select all that apply</span></label>
                    <div className="sf-checks">
                      {TASK_TYPES.map(o => (
                        <label key={o} className="sf-check">
                          <input type="checkbox" checked={form.task_type.includes(o)} onChange={() => toggle(o)} disabled={loading} />
                          <span>{o}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  <div className="sf-field">
                    <label className="sf-label" htmlFor="description">Describe your project in detail *</label>
                    <p className="sf-help">Include the type of data, roughly how many items, your timeline, and any budget. The more detail, the faster we can scope it.</p>
                    <textarea id="description" className="sf-textarea" value={form.description} onChange={set('description')} required disabled={loading} rows={6} />
                  </div>

                  <div className="sf-field">
                    <label className="sf-label" htmlFor="sample_link">Sample data or guidelines <span className="opt">Optional</span></label>
                    <input id="sample_link" className="sf-input" value={form.sample_link} onChange={set('sample_link')} disabled={loading} />
                  </div>

                  <button className="sf-submit" type="submit" disabled={loading}>
                    {loading ? 'Submitting…' : 'Submit project'}
                  </button>
                  <p className="sf-note">We reply within one business day. Your details stay private.</p>
                </form>
              )}

              {error && <Toast message={error} onDismiss={() => setError('')} />}
            </div>

          </div>
        </div>
      </section>

      <EvalFooter />
      </div>
    </>
  )
}
