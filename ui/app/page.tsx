import type { Metadata } from 'next'
import EvalNav from './components/EvalNav'
import EvalFooter from './components/EvalFooter'

export const metadata: Metadata = {
  title: 'Data infrastructure for medical AI',
  description:
    "Senebiclabs is the data layer for medical AI. Licensed clinicians label, evaluate, and create the data that trains and validates your models, across radiology, pathology, clinical text, and medical LLMs.",
  alternates: { canonical: '/' },
  openGraph: {
    title: 'The data layer for medical AI · Senebiclabs',
    description: 'Licensed clinicians label, evaluate, and create clinician-grade data for medical AI, with quality you can defend.',
    url: 'https://senebiclabs.com',
  },
}

// ── One type scale (6 sizes), 3 weights: 100 headings · 300 body · 600 accent ──
const DISPLAY = '"SF Pro Display", -apple-system, BlinkMacSystemFont, system-ui, sans-serif'
const BODY = '"DM Sans", system-ui, sans-serif'
const T_DISPLAY: React.CSSProperties = { fontFamily: DISPLAY, fontWeight: 100, fontSize: 'clamp(44px, 6.6vw, 88px)', letterSpacing: '0.03em', lineHeight: 1.04 }
const T_H2: React.CSSProperties = { fontFamily: DISPLAY, fontWeight: 100, fontSize: 'clamp(32px, 4vw, 52px)', letterSpacing: '0.02em', lineHeight: 1.14 }
const T_H3: React.CSSProperties = { fontFamily: DISPLAY, fontWeight: 100, fontSize: 'clamp(21px, 1.9vw, 24px)', letterSpacing: '0.02em', lineHeight: 1.3 }
const T_SUB: React.CSSProperties = { fontFamily: BODY, fontWeight: 300, fontSize: 'clamp(17px, 1.6vw, 20px)', lineHeight: 1.7, color: 'rgba(255,255,255,0.86)' }
const T_BODY: React.CSSProperties = { fontFamily: BODY, fontWeight: 300, fontSize: 16, lineHeight: 1.72, color: 'rgba(255,255,255,0.7)' }
const em: React.CSSProperties = { fontWeight: 600, fontStyle: 'normal' }

// ── One spacing scale, reused everywhere, no one-off values ──
const PAD_SECTION = 'clamp(104px, 13vw, 168px) 0'
const GAP_GRID = 'clamp(64px, 7vw, 88px)'          // section header → grid
const PAD_CELL = 'clamp(40px, 4.4vw, 52px) clamp(30px, 3vw, 40px)'
const GAP_HEAD = 28                                 // eyebrow → title → sub rhythm

const SECTION: React.CSSProperties = { padding: PAD_SECTION, borderTop: '1px solid var(--hairline)' }
const HEAD: React.CSSProperties = { textAlign: 'center', maxWidth: 780, margin: '0 auto' }
const CELL: React.CSSProperties = { border: '1px solid var(--hairline)', background: 'var(--navy)', padding: PAD_CELL, display: 'flex', flexDirection: 'column' }
const eyebrow = (mb: number): React.CSSProperties => ({ display: 'inline-block', marginBottom: mb })

function Head({ tag, title, sub }: { tag: string; title: React.ReactNode; sub: string }) {
  return (
    <div style={HEAD}>
      <span className="iso-label" style={eyebrow(GAP_HEAD)}>{tag}</span>
      <h2 style={{ ...T_H2, margin: 0 }}>{title}</h2>
      <p style={{ ...T_SUB, maxWidth: 620, margin: `${GAP_HEAD}px auto 0` }}>{sub}</p>
    </div>
  )
}

function Cell({ tag, title, body }: { tag?: string; title: string; body: string; }) {
  return (
    <>
      {tag && <span className="iso-label" style={{ marginBottom: 28 }}>{tag}</span>}
      <h3 style={{ ...T_H3, margin: '0 0 12px' }}>{title}</h3>
      <p style={T_BODY}>{body}</p>
    </>
  )
}

function Cta({ center = false }: { center?: boolean }) {
  return (
    <div style={{ display: 'flex', gap: 28, alignItems: 'center', flexWrap: 'wrap', justifyContent: center ? 'center' : 'flex-start' }}>
      <a href="/submit" className="nav-join-cta">Book a demo →</a>
      <a href="mailto:senebiclabs@gmail.com" className="iso-cta iso-cta--muted" style={{ textTransform: 'none', fontSize: 13, letterSpacing: '0.03em' }}>
        or just email us →
      </a>
    </div>
  )
}

export default function EvaluatePage() {
  return (
    <>
      <EvalNav />

      {/* ── HERO ───────────────────────────────────────────────────────── */}
      <section style={{ padding: 'clamp(164px, 20vw, 240px) 0 clamp(96px, 12vw, 136px)' }}>
        <div className="wrap" style={{ textAlign: 'center' }}>
          <span className="iso-label" style={eyebrow(36)}>Data infrastructure for medical AI</span>
          <h1 style={{ ...T_DISPLAY, maxWidth: 940, margin: '0 auto' }}>
            Clinician-grade data for <em style={em}>medical AI</em>.
          </h1>
          <p style={{ ...T_SUB, fontSize: 'clamp(18px, 1.9vw, 22px)', maxWidth: 700, margin: '36px auto 0' }}>
            Licensed clinicians label, evaluate, and create the data that trains and
            validates your models. The layer between raw medicine and a model you can trust.
          </p>
          <div style={{ marginTop: 52, display: 'flex', justifyContent: 'center' }}>
            <Cta center />
          </div>
        </div>
      </section>

      {/* ── THE PROBLEM ────────────────────────────────────────────────── */}
      <section style={SECTION}>
        <div className="wrap" style={{ textAlign: 'center' }}>
          <span className="iso-label" style={eyebrow(GAP_HEAD)}>The problem</span>
          <p style={{ ...T_H2, maxWidth: 900, margin: '0 auto' }}>
            Medical AI is only as good as its <em style={em}>data</em>. Crowd labels and a model
            grading itself will not survive a hospital, a regulator, or an investor asking how you
            know it is right.
          </p>
        </div>
      </section>

      {/* ── WHAT YOU GET ───────────────────────────────────────────────── */}
      <section id="what-you-get" style={{ ...SECTION, scrollMarginTop: 90 }}>
        <div className="wrap">
          <Head tag="What we do" title={<>Label. Evaluate. <em style={em}>Create</em>.</>}
                sub="The three kinds of data work medical AI runs on, all done by licensed clinicians." />

          <div className="blocks-3col" style={{ marginTop: GAP_GRID }}>
            {[
              { n: '01', t: 'Label', d: 'Turn raw medical data into ground truth: imaging labels, clinical extraction, classification, and de-identification.' },
              { n: '02', t: 'Evaluate', d: 'Grade your model’s outputs against a clinician’s read, with every critical miss surfaced, in a report you can defend.' },
              { n: '03', t: 'Create', d: 'Clinician-written gold answers and demonstrations to fine-tune and align on.' },
            ].map((c, i) => (
              <div key={c.n} style={{ ...CELL, marginLeft: i % 3 === 0 ? 0 : -1 }}>
                <Cell tag={c.n} title={c.t} body={c.d} />
              </div>
            ))}
          </div>

          {/* Deliverable, full-width panel, flush under the grid */}
          <div style={{ ...CELL, marginTop: -1, padding: 'clamp(56px, 6vw, 80px) clamp(30px, 3vw, 40px)', textAlign: 'center' }}>
            <span className="iso-label" style={eyebrow(GAP_HEAD)}>The deliverable</span>
            <h3 style={{ ...T_H2, fontSize: 'clamp(26px, 3vw, 40px)', margin: '0 auto', maxWidth: 640 }}>Data you can defend.</h3>
            <p style={{ ...T_SUB, margin: '28px auto 0', maxWidth: 700 }}>
              Labeled datasets, scored reports, or gold examples, every item traceable to a
              licensed clinician and keyed to your own case IDs.
            </p>
          </div>
        </div>
      </section>

      {/* ── MODALITIES (peer list) ─────────────────────────────────────── */}
      <section id="modalities" style={{ ...SECTION, scrollMarginTop: 90 }}>
        <div className="wrap">
          <Head tag="What we cover" title={<>Across every medical <em style={em}>modality</em>.</>}
                sub="Wherever your model touches medicine, a licensed specialist can label and evaluate it." />

          <div className="blocks-3col" style={{ marginTop: GAP_GRID }}>
            {[
              { t: 'Clinical text', d: 'Extraction, coding, and summaries.' },
              { t: 'Radiology', d: 'X-ray, CT, and MRI.' },
              { t: 'Pathology', d: 'Whole-slide and histology.' },
              { t: 'Medical LLMs', d: 'Evaluation, safety, and RLHF.' },
              { t: 'Genomics & omics', d: 'Variant and multi-omic data.' },
              { t: 'De-identification', d: 'PHI detection and redaction.' },
            ].map((m, i) => (
              <div key={m.t} style={{ ...CELL, marginLeft: i % 3 === 0 ? 0 : -1, marginTop: i >= 3 ? -1 : 0 }}>
                <Cell title={m.t} body={m.d} />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── ABOUT (this service only) ──────────────────────────────────── */}
      <section id="about" style={{ ...SECTION, scrollMarginTop: 90 }}>
        <div className="wrap">
          <Head tag="About" title={<>How the work <em style={em}>holds up</em>.</>}
                sub="Licensed clinicians do structured, case-by-case work, built so the result holds up." />

          <div className="cards-2col" style={{ marginTop: GAP_GRID, gap: 1, background: 'var(--hairline)', borderRadius: 0 }}>
            <div style={{ background: 'var(--navy)', padding: PAD_CELL, display: 'flex', flexDirection: 'column' }}>
              <Cell tag="Who does it"
                    title="Licensed clinicians, case by case"
                    body="Every case is handled by a licensed clinician as a structured expert task, one at a time. Not crowd labelers, and not a model grading a model." />
            </div>
            <div style={{ background: 'var(--navy)', padding: PAD_CELL, display: 'flex', flexDirection: 'column' }}>
              <Cell tag="Why it holds up"
                    title="Defensible by construction"
                    body="Each case gets a structured, multi-dimension assessment. Data is de-identified and isolated per client, and every task is recorded: who did what, and when." />
            </div>
          </div>
        </div>
      </section>

      {/* ── WHY US (even 2×2) ──────────────────────────────────────────── */}
      <section id="why-us" style={{ ...SECTION, scrollMarginTop: 90 }}>
        <div className="wrap">
          <Head tag="Why us" title={<>Compliance-grade by <em style={em}>default</em>.</>}
                sub="How the data is handled separates a defensible result from a liability. Built for medical data, not crowdsourced." />

          <div className="cards-2col" style={{ marginTop: GAP_GRID, gap: 1, background: 'var(--hairline)', borderRadius: 0 }}>
            {[
              { k: 'Credible', t: 'Licensed clinicians', d: 'Medical specialists review your data, not a crowd.' },
              { k: 'Safe', t: 'De-identified', d: 'Identifiers stripped before anyone sees a case.' },
              { k: 'Private', t: 'Isolated per client', d: 'Your data walled off from every other client’s.' },
              { k: 'Defensible', t: 'Fully audited', d: 'Every review logged: who, what, and when.' },
            ].map((p) => (
              <div key={p.t} style={{ background: 'var(--navy)', padding: PAD_CELL, display: 'flex', flexDirection: 'column' }}>
                <Cell tag={p.k} title={p.t} body={p.d} />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ───────────────────────────────────────────────── */}
      <section style={SECTION}>
        <div className="wrap">
          <Head tag="How it works" title={<>Prove it on a <em style={em}>slice</em> first.</>}
                sub="Start small. See the value before you commit to volume." />

          <div className="blocks-3col" style={{ marginTop: GAP_GRID }}>
            {[
              { n: 'Step 01', t: 'Send your data', d: 'Raw data to label, or your model’s outputs to evaluate.' },
              { n: 'Step 02', t: 'Clinicians work', d: 'Licensed specialists label, evaluate, or write, de-identified and isolated.' },
              { n: 'Step 03', t: 'You get it back', d: 'Labeled data, a scored report, or gold examples, keyed to your IDs.' },
            ].map((s, i) => (
              <div key={s.n} style={{ ...CELL, marginLeft: i % 3 === 0 ? 0 : -1 }}>
                <Cell tag={s.n} title={s.t} body={s.d} />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CLOSE ──────────────────────────────────────────────────────── */}
      <section style={SECTION}>
        <div className="wrap" style={{ textAlign: 'center' }}>
          <h2 style={{ ...T_H2, maxWidth: 720, margin: '0 auto' }}>
            Build medical AI on data you can <em style={em}>defend</em>.
          </h2>
          <p style={{ ...T_SUB, maxWidth: 560, margin: '28px auto 0' }}>
            Book a demo to see how clinician-grade data changes what your model can prove.
          </p>
          <div style={{ marginTop: 52, display: 'flex', justifyContent: 'center' }}>
            <Cta center />
          </div>
        </div>
      </section>

      <EvalFooter />
    </>
  )
}
