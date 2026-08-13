import type { Metadata } from 'next'
import EvalNav from './components/EvalNav'
import EvalFooter from './components/EvalFooter'

export const metadata: Metadata = {
  title: 'Clinician-grade data for medical AI · Senebiclabs',
  description:
    'Senebiclabs is the data layer for medical AI. Licensed clinicians label, evaluate, and create the data medical models are trained, aligned, and tested on, delivered by API, isolated per client, and traceable to a name.',
  alternates: { canonical: '/' },
  openGraph: {
    title: 'Clinician-grade data for medical AI · Senebiclabs',
    description: 'Licensed clinicians label, evaluate, and create the data medical models are trained, aligned, and tested on.',
    url: 'https://senebiclabs.com',
  },
}

// Type: Geist (brand) for headings, DM Sans for reading, Geist Mono for labels.
// Confident weights, tight tracking. No hairline display faces, no centered slop.
const SANS = "'Geist', system-ui, -apple-system, sans-serif"
const READ = "'DM Sans', system-ui, sans-serif"

const T_DISPLAY: React.CSSProperties = { fontFamily: SANS, fontWeight: 600, fontSize: 'clamp(40px, 5.8vw, 78px)', letterSpacing: '-0.035em', lineHeight: 1.0 }
const T_H2: React.CSSProperties = { fontFamily: SANS, fontWeight: 600, fontSize: 'clamp(28px, 3.6vw, 46px)', letterSpacing: '-0.03em', lineHeight: 1.08 }
const T_H3: React.CSSProperties = { fontFamily: SANS, fontWeight: 600, fontSize: 'clamp(19px, 1.7vw, 22px)', letterSpacing: '-0.02em', lineHeight: 1.28 }
const T_LEAD: React.CSSProperties = { fontFamily: READ, fontWeight: 400, fontSize: 'clamp(17px, 1.6vw, 20px)', lineHeight: 1.6, color: 'rgba(255,255,255,0.74)' }
const T_BODY: React.CSSProperties = { fontFamily: READ, fontWeight: 400, fontSize: 15.5, lineHeight: 1.66, color: 'rgba(255,255,255,0.62)' }

const WRAP_TIGHT = 760
const PAD_SECTION = 'clamp(88px, 11vw, 140px) 0'
const GAP_GRID = 'clamp(48px, 6vw, 72px)'
const PAD_CELL = 'clamp(34px, 3.6vw, 46px) clamp(28px, 2.8vw, 38px)'

const SECTION: React.CSSProperties = { padding: PAD_SECTION, borderTop: '1px solid var(--hairline)' }
const CELL: React.CSSProperties = { border: '1px solid var(--hairline)', background: 'var(--navy)', padding: PAD_CELL, display: 'flex', flexDirection: 'column' }

function Head({ tag, title, sub }: { tag: string; title: string; sub?: string }) {
  return (
    <div style={{ maxWidth: WRAP_TIGHT }}>
      <span className="iso-label" style={{ display: 'inline-block', marginBottom: 22 }}>{tag}</span>
      <h2 style={{ ...T_H2, margin: 0, textWrap: 'balance' }}>{title}</h2>
      {sub && <p style={{ ...T_LEAD, margin: '22px 0 0', maxWidth: 620 }}>{sub}</p>}
    </div>
  )
}

function Cell({ tag, title, body }: { tag?: string; title: string; body: string }) {
  return (
    <>
      {tag && <span className="iso-label" style={{ marginBottom: 26 }}>{tag}</span>}
      <h3 style={{ ...T_H3, margin: '0 0 10px' }}>{title}</h3>
      <p style={{ ...T_BODY, margin: 0 }}>{body}</p>
    </>
  )
}

function Ctas() {
  return (
    <div style={{ display: 'flex', gap: 18, alignItems: 'center', flexWrap: 'wrap' }}>
      <a href="/submit" className="nav-join-cta">Book a demo →</a>
      <a href="/docs" className="iso-cta" style={{ fontSize: 12 }}>Read the docs →</a>
    </div>
  )
}

export default function HomePage() {
  return (
    <>
      <EvalNav />

      {/* HERO — left aligned, confident  */}
      <section style={{ padding: 'clamp(140px, 17vw, 200px) 0 clamp(56px, 8vw, 96px)' }}>
        <div className="wrap">
          <span className="iso-label" style={{ display: 'inline-block', marginBottom: 30 }}>Data infrastructure for medical AI</span>
          <h1 style={{ ...T_DISPLAY, maxWidth: 940, margin: 0, textWrap: 'balance' }}>
            Clinician-grade data for medical AI.
          </h1>
          <p style={{ ...T_LEAD, fontSize: 'clamp(18px, 1.8vw, 22px)', maxWidth: 640, margin: '30px 0 0' }}>
            Licensed clinicians label, evaluate, and create the data medical models are
            trained, aligned, and tested on. Delivered by API, isolated per client, and
            traceable to a name.
          </p>
          <div style={{ marginTop: 44 }}>
            <Ctas />
          </div>
        </div>
      </section>

      {/* TRUST BAR — factual capabilities, not metrics  */}
      <section style={{ borderTop: '1px solid var(--hairline)', borderBottom: '1px solid var(--hairline)' }}>
        <div className="wrap" style={{ display: 'flex', flexWrap: 'wrap', gap: '14px 28px', padding: '22px 48px' }}>
          {['Licensed clinicians', 'De-identified', 'Isolated per client', 'Consensus reviewed', 'API-native', 'Fully audited'].map((t, i) => (
            <span key={t} className="iso-label" style={{ fontSize: 12, letterSpacing: '0.1em', color: i === 0 ? 'var(--ink)' : 'var(--slate)' }}>{t}</span>
          ))}
        </div>
      </section>

      {/* PROBLEM  */}
      <section style={SECTION}>
        <div className="wrap">
          <span className="iso-label" style={{ display: 'inline-block', marginBottom: 22 }}>The problem</span>
          <p style={{ ...T_H2, fontSize: 'clamp(24px, 3vw, 38px)', maxWidth: 900, margin: 0, textWrap: 'balance' }}>
            Medical AI is only as good as its data. Crowd labels and a model grading itself
            do not hold up to a hospital, a regulator, or an investor asking how you know it
            is right.
          </p>
        </div>
      </section>

      {/* WHAT WE DO  */}
      <section id="what-you-get" style={{ ...SECTION, scrollMarginTop: 90 }}>
        <div className="wrap">
          <Head tag="What we do" title="Label. Evaluate. Create."
                sub="The data work behind a medical model, at every stage of its life, done by licensed clinicians." />
          <div className="blocks-3col" style={{ marginTop: GAP_GRID }}>
            {[
              { n: '01', t: 'Label', d: 'Turn raw medical data into ground truth: imaging labels, clinical extraction, classification, and de-identification.' },
              { n: '02', t: 'Evaluate', d: 'Grade model outputs against a clinician read. Every critical miss surfaced, in an accuracy and safety report you can defend.' },
              { n: '03', t: 'Create', d: 'Clinician-written gold answers and preference data to fine-tune and align on, the scarce data teams cannot crowdsource.' },
            ].map((c, i) => (
              <div key={c.n} style={{ ...CELL, marginLeft: i % 3 === 0 ? 0 : -1 }}>
                <Cell tag={c.n} title={c.t} body={c.d} />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* HOW IT WORKS — the real pipeline, API-first  */}
      <section id="how" style={{ ...SECTION, scrollMarginTop: 90 }}>
        <div className="wrap">
          <Head tag="How it works" title="Built API-first."
                sub="Send data, licensed clinicians review it, you get it back. One pipeline, an API around it." />
          <div className="blocks-3col" style={{ marginTop: GAP_GRID }}>
            {[
              { n: 'Step 01', t: 'Send your data', d: 'Push items through the API or the dashboard. Raw data to label, or your model outputs to grade.' },
              { n: 'Step 02', t: 'Clinicians review', d: 'Licensed specialists work each case, with several reviewers per item combined into a consensus.' },
              { n: 'Step 03', t: 'Get it back', d: 'Labeled datasets or scored reports, delivered by API and signed webhook, keyed to your own case IDs.' },
            ].map((s, i) => (
              <div key={s.n} style={{ ...CELL, marginLeft: i % 3 === 0 ? 0 : -1 }}>
                <Cell tag={s.n} title={s.t} body={s.d} />
              </div>
            ))}
          </div>
          <p style={{ ...T_BODY, marginTop: 26 }}>
            <a href="/docs" className="iso-cta" style={{ fontSize: 12 }}>Read the API reference →</a>
          </p>
        </div>
      </section>

      {/* RIGOR / WHY US  */}
      <section id="why-us" style={{ ...SECTION, scrollMarginTop: 90 }}>
        <div className="wrap">
          <Head tag="Why us" title="Defensible by construction."
                sub="How medical data is handled separates a result you can stand behind from a liability." />
          <div className="cards-2col" style={{ marginTop: GAP_GRID, gap: 1, background: 'var(--hairline)' }}>
            {[
              { k: 'Credible', t: 'Licensed clinicians', d: 'Medical specialists review your data, one case at a time. Not a crowd, and not a model grading a model.' },
              { k: 'Rigorous', t: 'Consensus quality control', d: 'Several clinicians review each item, combined with inter-reviewer agreement so you can see where they concur.' },
              { k: 'Private', t: 'Isolated per client', d: 'Your data is de-identified before review and walled off from every other client.' },
              { k: 'Defensible', t: 'Fully audited', d: 'Every review is recorded: who did it, what they decided, and when.' },
            ].map((p) => (
              <div key={p.t} style={{ background: 'var(--navy)', padding: PAD_CELL, display: 'flex', flexDirection: 'column' }}>
                <Cell tag={p.k} title={p.t} body={p.d} />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* MODALITIES  */}
      <section id="modalities" style={{ ...SECTION, scrollMarginTop: 90 }}>
        <div className="wrap">
          <Head tag="What we cover" title="Across every medical modality."
                sub="Wherever a model touches medicine, a licensed specialist can label and evaluate it." />
          <div className="blocks-3col" style={{ marginTop: GAP_GRID }}>
            {[
              { t: 'Clinical text', d: 'Extraction, coding, and summaries.' },
              { t: 'Radiology', d: 'X-ray, CT, and MRI.' },
              { t: 'Pathology', d: 'Whole-slide and histology.' },
              { t: 'Medical LLMs', d: 'Evaluation, safety, and preference data.' },
              { t: 'Genomics and omics', d: 'Variant and multi-omic data.' },
              { t: 'De-identification', d: 'PHI detection and redaction.' },
            ].map((m, i) => (
              <div key={m.t} style={{ ...CELL, marginLeft: i % 3 === 0 ? 0 : -1, marginTop: i >= 3 ? -1 : 0 }}>
                <Cell title={m.t} body={m.d} />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CLOSE  */}
      <section style={SECTION}>
        <div className="wrap">
          <h2 style={{ ...T_H2, maxWidth: 720, margin: 0, textWrap: 'balance' }}>
            Build medical AI on data you can defend.
          </h2>
          <p style={{ ...T_LEAD, maxWidth: 560, margin: '22px 0 0' }}>
            Start with a slice, see the value, then scale. Book a demo, or read the docs and
            start from code.
          </p>
          <div style={{ marginTop: 40 }}>
            <Ctas />
          </div>
        </div>
      </section>

      <EvalFooter />
    </>
  )
}
