import NavBar from '../components/NavBar'
import EvalFooter from '../components/EvalFooter'

const DISPLAY = '"SF Pro Display", -apple-system, BlinkMacSystemFont, system-ui, sans-serif'
const BODY = '"DM Sans", system-ui, sans-serif'

/* ---------- Hero (centered) ---------- */
function Hero() {
  return (
    <section style={{ padding: 'clamp(150px, 18vw, 230px) 0 clamp(72px, 10vw, 120px)' }}>
      <div className="wrap" style={{ textAlign: 'center' }}>
        <span className="iso-label" style={{ display: 'inline-block', marginBottom: 30 }}>
          Clinician-grade evaluation for medical AI
        </span>
        <h1 style={{
          fontFamily: DISPLAY, fontWeight: 100, fontSize: 'clamp(40px, 6vw, 82px)',
          letterSpacing: '0.04em', lineHeight: 1.05, margin: '0 auto 34px', maxWidth: 900,
        }}>
          Know exactly where your medical AI is unsafe.
        </h1>
        <p style={{
          fontFamily: BODY, fontWeight: 200, fontSize: 'clamp(18px, 1.9vw, 23px)', color: 'var(--ink)',
          lineHeight: 1.7, maxWidth: 680, margin: '0 auto 48px',
        }}>
          Senebiclabs puts licensed clinicians on your model&rsquo;s outputs. They score every one
          for accuracy and safety, and flag what is dangerous before your patients see it.
        </p>
        <div style={{ display: 'flex', gap: 32, alignItems: 'center', justifyContent: 'center', flexWrap: 'wrap' }}>
          <a href="/submit" className="iso-cta">Start a pilot →</a>
          <a href="#how" className="iso-cta iso-cta--muted">How it works →</a>
        </div>
      </div>
    </section>
  )
}

/* ---------- Problem (editorial statement) ---------- */
function Problem() {
  return (
    <section style={{ padding: 'clamp(72px, 10vw, 140px) 0', borderTop: '1px solid var(--hairline)' }}>
      <div className="wrap">
        <span className="iso-label" style={{ display: 'block', marginBottom: 44 }}>The problem</span>
        <p style={{
          fontFamily: DISPLAY, fontWeight: 100, fontSize: 'clamp(26px, 3.4vw, 46px)',
          letterSpacing: '0.03em', lineHeight: 1.2, color: 'var(--ink)', maxWidth: 940, margin: 0,
        }}>
          Medical AI ships to patients faster than anyone can check it. A confident, wrong answer is
          not a bug. It is a risk to a life. Internal review does not scale, and engineers cannot
          catch what a clinician would.
        </p>
      </div>
    </section>
  )
}

/* ---------- How it works (bordered cells) ---------- */
const STEPS = [
  { n: '01', t: 'Send your outputs', d: 'A sample of prompts and responses, as CSV or JSONL. No integration, no setup.' },
  { n: '02', t: 'Clinicians evaluate', d: 'Licensed clinicians score every output for accuracy and safety, flag the unsafe ones, and write the reasoning.' },
  { n: '03', t: 'You get a verdict', d: 'Scored data, a ranked list of failures, and the rationale. Ready for your evaluations, RLHF, or guardrails.' },
]

function HowItWorks() {
  return (
    <section id="how" style={{ padding: 'clamp(64px, 9vw, 110px) 0', borderTop: '1px solid var(--hairline)' }}>
      <div className="wrap">
        <span className="iso-label" style={{ display: 'block', marginBottom: 44 }}>How it works</span>
        <div className="blocks-3col">
          {STEPS.map((s, i) => (
            <div key={s.n} style={{
              border: '1px solid var(--hairline)', marginLeft: i > 0 ? -1 : 0,
              padding: 'clamp(28px, 4vw, 48px) clamp(22px, 3vw, 40px) clamp(32px, 4.5vw, 52px)',
              display: 'flex', flexDirection: 'column', minHeight: 300,
            }}>
              <div className="iso-label" style={{ marginBottom: 32 }}>{s.n}</div>
              <h3 style={{ fontFamily: DISPLAY, fontWeight: 100, fontSize: 'clamp(20px, 2vw, 26px)', letterSpacing: '0.02em', lineHeight: 1.3, marginBottom: 16 }}>{s.t}</h3>
              <p style={{ fontFamily: BODY, fontWeight: 300, fontSize: 15.5, color: 'var(--ink)', lineHeight: 1.7, marginTop: 'auto' }}>{s.d}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ---------- Trust (bordered cells) ---------- */
const PILLARS = [
  { t: 'Licensed clinicians', d: 'Every output is reviewed by credentialed, practicing clinicians. Not crowd workers, not a model grading a model.' },
  { t: 'Auditable rationale', d: 'Each label carries the clinician&rsquo;s written reasoning, so every score is defensible and traceable.' },
  { t: 'Consensus quality', d: 'Critical items are double-reviewed and reconciled, so you get reliability you can measure, not one opinion.' },
]

function Why() {
  return (
    <section style={{ padding: 'clamp(64px, 9vw, 110px) 0', borderTop: '1px solid var(--hairline)' }}>
      <div className="wrap">
        <span className="iso-label" style={{ display: 'block', marginBottom: 44 }}>Why it is trustworthy</span>
        <div className="blocks-3col">
          {PILLARS.map((p, i) => (
            <div key={p.t} style={{
              border: '1px solid var(--hairline)', marginLeft: i > 0 ? -1 : 0,
              padding: 'clamp(28px, 4vw, 48px) clamp(22px, 3vw, 40px) clamp(32px, 4.5vw, 52px)',
              display: 'flex', flexDirection: 'column', minHeight: 260,
            }}>
              <h3 style={{ fontFamily: DISPLAY, fontWeight: 100, fontSize: 'clamp(20px, 2vw, 26px)', letterSpacing: '0.02em', lineHeight: 1.3, marginBottom: 18 }}>{p.t}</h3>
              <p style={{ fontFamily: BODY, fontWeight: 300, fontSize: 15.5, color: 'var(--ink)', lineHeight: 1.7, marginTop: 'auto' }}
                 dangerouslySetInnerHTML={{ __html: p.d }} />
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ---------- CTA (centered) ---------- */
function CTA() {
  return (
    <section style={{ padding: 'clamp(96px, 13vw, 170px) 0', borderTop: '1px solid var(--hairline)' }}>
      <div className="wrap" style={{ textAlign: 'center' }}>
        <h2 style={{ fontFamily: DISPLAY, fontWeight: 100, fontSize: 'clamp(32px, 4.5vw, 60px)', letterSpacing: '0.03em', lineHeight: 1.1, margin: '0 auto 30px', maxWidth: 760 }}>
          See what we would find in your model.
        </h2>
        <p style={{ fontFamily: BODY, fontWeight: 300, fontSize: 'clamp(18px, 1.8vw, 22px)', color: 'var(--ink)', lineHeight: 1.7, maxWidth: 600, margin: '0 auto 48px' }}>
          Send us 100 of your model&rsquo;s outputs. We will show you exactly where it is unsafe, in a week.
        </p>
        <a href="/submit" className="iso-cta">Start a pilot →</a>
      </div>
    </section>
  )
}

export default function EvaluatePage() {
  return (
    <>
      <NavBar minimal />
      <Hero />
      <Problem />
      <HowItWorks />
      <Why />
      <CTA />
      <EvalFooter />
    </>
  )
}
