import type { Metadata } from 'next'
import EvalNav from '../components/EvalNav'
import FooterSection from '../components/sections/FooterSection'

export const metadata: Metadata = {
  title: 'Medical AI evaluation',
  description:
    "Licensed clinicians annotate and evaluate medical AI. You get a defensible breakdown of where your model is right, where it fails, and what it critically missed — across radiology, pathology, clinical text, medical LLMs, and more.",
  alternates: { canonical: '/evaluate' },
  openGraph: {
    title: 'Prove your medical AI works · Senebiclabs',
    description: 'Licensed clinicians annotate and evaluate medical AI, across every modality. A performance breakdown, not just labels.',
    url: 'https://senebiclabs.com/evaluate',
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

// ── One spacing scale — reused everywhere, no one-off values ──
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
          <span className="iso-label" style={eyebrow(36)}>Medical AI annotation &amp; evaluation</span>
          <h1 style={{ ...T_DISPLAY, maxWidth: 940, margin: '0 auto' }}>
            Prove your medical AI <em style={em}>works</em>.
          </h1>
          <p style={{ ...T_SUB, fontSize: 'clamp(18px, 1.9vw, 22px)', maxWidth: 660, margin: '36px auto 0' }}>
            Licensed clinicians review your model&rsquo;s real outputs and show you where it&rsquo;s
            right, where it fails, and what it critically missed.
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
            Most medical AI ships on <em style={em}>trust</em>. A validation set that looks nothing
            like the clinic will not survive a hospital, a regulator, or an investor asking how you
            know it is right.
          </p>
        </div>
      </section>

      {/* ── WHAT YOU GET ───────────────────────────────────────────────── */}
      <section id="what-you-get" style={{ ...SECTION, scrollMarginTop: 90 }}>
        <div className="wrap">
          <Head tag="What you get" title={<>Expert validation, <em style={em}>not labels</em>.</>}
                sub="A licensed clinician reviews every output and tells you three things." />

          <div className="blocks-3col" style={{ marginTop: GAP_GRID }}>
            {[
              { n: '01', t: 'Was it right?', d: 'Every output confirmed or rejected against a clinician’s read.' },
              { n: '02', t: 'The correct answer', d: 'Where the model is wrong, the clinician’s correct read — not just a flag.' },
              { n: '03', t: 'What it critically missed', d: 'The dangerous cases: findings a clinician catches and the model did not.' },
            ].map((c, i) => (
              <div key={c.n} style={{ ...CELL, marginLeft: i % 3 === 0 ? 0 : -1 }}>
                <Cell tag={c.n} title={c.t} body={c.d} />
              </div>
            ))}
          </div>

          {/* Deliverable — full-width panel, flush under the grid */}
          <div style={{ ...CELL, marginTop: -1, padding: 'clamp(56px, 6vw, 80px) clamp(30px, 3vw, 40px)', textAlign: 'center' }}>
            <span className="iso-label" style={eyebrow(GAP_HEAD)}>The deliverable</span>
            <h3 style={{ ...T_H2, fontSize: 'clamp(26px, 3vw, 40px)', margin: '0 auto', maxWidth: 640 }}>A report you can defend.</h3>
            <p style={{ ...T_SUB, margin: '28px auto 0', maxWidth: 700 }}>
              Accuracy, precision and recall per finding, a confusion matrix, and every failure
              named — measured on the reviewed sample.
            </p>
          </div>
        </div>
      </section>

      {/* ── MODALITIES (peer list) ─────────────────────────────────────── */}
      <section id="modalities" style={{ ...SECTION, scrollMarginTop: 90 }}>
        <div className="wrap">
          <Head tag="What we evaluate" title={<>Across every medical <em style={em}>modality</em>.</>}
                sub="Wherever your model touches medicine, a licensed specialist can evaluate it." />

          <div className="blocks-3col" style={{ marginTop: GAP_GRID }}>
            {[
              { t: 'Clinical text', d: 'Notes, extraction, and coding.' },
              { t: 'Radiology', d: 'X-ray, CT, and MRI review.' },
              { t: 'Pathology', d: 'Whole-slide and histology.' },
              { t: 'Medical LLMs', d: 'Output evaluation and RLHF.' },
              { t: 'Genomics & omics', d: 'Genomic and multi-omic annotation.' },
              { t: 'De-identification & PHI', d: 'Redaction and PHI review.' },
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
          <Head tag="About" title={<>How the review <em style={em}>works</em>.</>}
                sub="Licensed clinicians conduct structured, case-by-case review — built so the result holds up." />

          <div className="cards-2col" style={{ marginTop: GAP_GRID, gap: 1, background: 'var(--hairline)', borderRadius: 0 }}>
            <div style={{ background: 'var(--navy)', padding: PAD_CELL, display: 'flex', flexDirection: 'column' }}>
              <Cell tag="Who reviews"
                    title="Licensed clinicians, case by case"
                    body="Every case is reviewed by a licensed clinician as a structured expert assessment, one case at a time. Not crowd labelers, and not a model grading a model." />
            </div>
            <div style={{ background: 'var(--navy)', padding: PAD_CELL, display: 'flex', flexDirection: 'column' }}>
              <Cell tag="Why it holds up"
                    title="Defensible by construction"
                    body="Each case gets a structured, multi-dimension assessment. Data is de-identified and isolated per client, and every review is recorded — who reviewed what, and when." />
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
              { n: 'Step 01', t: 'Send your outputs', d: 'A sample of your data and your model’s predictions.' },
              { n: 'Step 02', t: 'Clinicians review', d: 'Licensed specialists assess each case, de-identified and isolated.' },
              { n: 'Step 03', t: 'You get the report', d: 'A performance breakdown you can act on and show.' },
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
            Prove your medical AI <em style={em}>works</em>.
          </h2>
          <p style={{ ...T_SUB, maxWidth: 560, margin: '28px auto 0' }}>
            Book a demo — see where your model is right, where it fails, and what it missed.
          </p>
          <div style={{ marginTop: 52, display: 'flex', justifyContent: 'center' }}>
            <Cta center />
          </div>
        </div>
      </section>

      <FooterSection />
    </>
  )
}
