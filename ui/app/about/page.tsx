import type { Metadata } from 'next'
import EvalNav from '../components/EvalNav'
import EvalFooter from '../components/EvalFooter'

export const metadata: Metadata = {
  title: 'About · Senebiclabs',
  description:
    'Senebiclabs is the data infrastructure under medical AI. Licensed clinicians label, evaluate, and create the data medical models are trained, aligned, and tested on — traceable to a name, isolated per client.',
  alternates: { canonical: '/about' },
  openGraph: {
    title: 'About · Senebiclabs',
    description: 'The clinician layer underneath medical AI: who we are and why we build it.',
    url: 'https://senebiclabs.com/about',
  },
}

// Same design language as the homepage: Geist for headings, DM Sans to read,
// Geist Mono for labels. Stark monochrome, centered throughout.
const SANS = "'Geist', system-ui, -apple-system, sans-serif"
const READ = "'DM Sans', system-ui, sans-serif"

const T_DISPLAY: React.CSSProperties = { fontFamily: SANS, fontWeight: 600, fontSize: 'clamp(40px, 6.4vw, 88px)', letterSpacing: '-0.04em', lineHeight: 1.0 }
const T_H2: React.CSSProperties = { fontFamily: SANS, fontWeight: 600, fontSize: 'clamp(28px, 3.8vw, 48px)', letterSpacing: '-0.03em', lineHeight: 1.08 }
const T_H3: React.CSSProperties = { fontFamily: SANS, fontWeight: 600, fontSize: 'clamp(19px, 1.7vw, 22px)', letterSpacing: '-0.02em', lineHeight: 1.28 }
const T_LEAD: React.CSSProperties = { fontFamily: READ, fontWeight: 400, fontSize: 'clamp(17px, 1.6vw, 20px)', lineHeight: 1.7, color: 'rgba(255,255,255,0.74)' }
const T_BODY: React.CSSProperties = { fontFamily: READ, fontWeight: 400, fontSize: 15.5, lineHeight: 1.7, color: 'rgba(255,255,255,0.62)' }

const PAD_SECTION = 'clamp(80px, 11vw, 140px) 0'
const GAP_GRID = 'clamp(48px, 6vw, 72px)'
const PAD_CELL = 'clamp(38px, 4vw, 52px) clamp(28px, 3vw, 38px)'
const WIDE: React.CSSProperties = { maxWidth: 1440, margin: '0 auto', padding: '0 clamp(24px, 4vw, 60px)' }
const SECTION: React.CSSProperties = { padding: PAD_SECTION, borderTop: '1px solid var(--hairline)' }
const HEAD: React.CSSProperties = { textAlign: 'center', maxWidth: 820, margin: '0 auto' }
const CELL: React.CSSProperties = { border: '1px solid var(--hairline)', background: 'var(--navy)', padding: PAD_CELL, display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }

function Head({ tag, title, sub }: { tag: string; title: string; sub?: string }) {
  return (
    <div style={HEAD}>
      <span className="iso-label" style={{ display: 'inline-block', marginBottom: 24 }}>{tag}</span>
      <h2 style={{ ...T_H2, margin: 0, textWrap: 'balance' }}>{title}</h2>
      {sub && <p style={{ ...T_LEAD, margin: '24px auto 0', maxWidth: 660 }}>{sub}</p>}
    </div>
  )
}

function Prose({ children }: { children: React.ReactNode }) {
  return <div style={{ maxWidth: 720, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 22 }}>{children}</div>
}

export default function AboutPage() {
  return (
    <>
      <EvalNav />

      {/* HERO / MISSION  */}
      <section style={{ padding: 'clamp(112px, 13vw, 168px) 0 clamp(56px, 7vw, 88px)' }}>
        <div style={{ ...WIDE, textAlign: 'center' }}>
          <span className="iso-label" style={{ display: 'inline-block', marginBottom: 30 }}>About Senebiclabs</span>
          <h1 style={{ ...T_DISPLAY, maxWidth: 1120, margin: '0 auto', textWrap: 'balance' }}>
            The data layer medical AI can be trusted on.
          </h1>
          <p style={{ ...T_LEAD, fontSize: 'clamp(18px, 1.9vw, 23px)', maxWidth: 800, margin: '34px auto 0' }}>
            Senebiclabs is the data infrastructure under medical AI. We put licensed clinicians
            between raw medicine and the models built on it — so the data a model learns from,
            aligns to, and is judged against was made by people qualified to judge it.
          </p>
        </div>
      </section>

      {/* WHY WE EXIST  */}
      <section style={SECTION}>
        <div style={WIDE}>
          <Head tag="Why we exist" title="Medical AI is only as good as its data." />
          <div style={{ marginTop: GAP_GRID }}>
            <Prose>
              <p style={{ ...T_LEAD, textAlign: 'center' }}>
                Every medical model is a mirror of the data behind it. Yet most of that data is
                labeled by crowds with no clinical training, or graded by another model with no
                accountability.
              </p>
              <p style={{ ...T_BODY, fontSize: 17, textAlign: 'center' }}>
                That holds up in a demo. It does not hold up in front of a hospital&rsquo;s safety
                board, a regulator asking how you know the model is right, or an investor asking who
                signed off. The distance between &ldquo;it works on our benchmark&rdquo; and &ldquo;a
                clinician will stake their name on it&rdquo; is where medical AI stalls. We exist to
                close it.
              </p>
            </Prose>
          </div>
        </div>
      </section>

      {/* THESIS  */}
      <section style={SECTION}>
        <div style={WIDE}>
          <Head
            tag="What we believe"
            title="Clinical data deserves clinical judgment."
            sub="Not a crowd. Not a model grading a model. Licensed clinicians — the people a hospital would trust to make the call — reviewing your data one case at a time, and putting a name to the judgment."
          />
        </div>
      </section>

      {/* WHAT WE DO  */}
      <section style={SECTION}>
        <div style={WIDE}>
          <Head tag="What we do" title="Evaluate. Label. Create."
                sub="The data work behind a medical model, at every stage of its life — done by licensed clinicians." />
          <div className="blocks-3col" style={{ marginTop: GAP_GRID }}>
            {[
              { n: '01', t: 'Evaluate', d: "Grade a model's outputs against a clinician read. Every critical miss surfaced, in a report you can put in front of a regulator." },
              { n: '02', t: 'Label', d: 'Turn raw medical data into ground truth — imaging labels, clinical extraction, classification — reviewed case by case.' },
              { n: '03', t: 'Create', d: 'Clinician-written gold answers, preferences, and benchmarks to fine-tune, align, and stress-test on.' },
            ].map((c, i) => (
              <div key={c.n} style={{ ...CELL, marginLeft: i % 3 === 0 ? 0 : -1 }}>
                <span className="iso-label" style={{ marginBottom: 24 }}>{c.n}</span>
                <h3 style={{ ...T_H3, margin: '0 0 10px' }}>{c.t}</h3>
                <p style={{ ...T_BODY, margin: 0, maxWidth: 340 }}>{c.d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PRINCIPLES  */}
      <section style={SECTION}>
        <div style={WIDE}>
          <Head tag="The standard" title="What we refuse to compromise on." />
          <div className="blocks-3col" style={{ marginTop: GAP_GRID }}>
            {[
              { n: 'I', t: 'Clinical judgment, not crowds', d: 'Every case is reviewed by a licensed clinician. Where the stakes call for it, several — combined into a consensus, with their agreement shown, so you see exactly where they concur.' },
              { n: 'II', t: 'Traceable to a name', d: 'Every review is recorded: who decided, what they decided, and when. A result you can defend to a safety board is one you can trace to the person who made it.' },
              { n: 'III', t: 'Model surfaces, clinician judges', d: 'The pipeline presents the data; the clinician makes the call. We are strict about that line — it is what makes the output accountable, not automated guesswork.' },
              { n: 'IV', t: 'Your data, walled off', d: 'De-identified before review and isolated from every other client. Confidentiality is enforced by the system, not just promised in a contract.' },
              { n: 'V', t: 'Honest about the numbers', d: 'We report the support behind each figure, the reviewer agreement, and the cases we could not assess — never a single flattering number. If a result is thin, we say so.' },
              { n: 'VI', t: 'Earn the next layer', d: 'We lead with the judgment only clinicians can give and expand from there. We do not ship a capability we cannot yet stand behind.' },
            ].map((c, i) => (
              <div key={c.n} style={{ ...CELL, marginLeft: i % 3 === 0 ? 0 : -1, marginTop: i >= 3 ? -1 : 0 }}>
                <span className="iso-label" style={{ marginBottom: 20, opacity: 0.6 }}>{c.n}</span>
                <h3 style={{ ...T_H3, margin: '0 0 12px' }}>{c.t}</h3>
                <p style={{ ...T_BODY, margin: 0, maxWidth: 340 }}>{c.d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ORIGIN  */}
      <section style={SECTION}>
        <div style={WIDE}>
          <Head tag="Where this came from" title="A gap nobody was closing." />
          <div style={{ marginTop: GAP_GRID }}>
            <Prose>
              <p style={{ ...T_LEAD, textAlign: 'center' }}>
                Senebiclabs began from a simple observation: the models being built to read scans,
                answer patients, and guide care were being trained and tested on data no clinician
                had ever checked.
              </p>
              <p style={{ ...T_BODY, fontSize: 17, textAlign: 'center' }}>
                The tools to move fast already existed. The layer that made the output trustworthy
                did not. So we set out to build it — clinical judgment made systematic: credentialed
                specialists, consensus review, de-identification, and a full audit trail, wrapped in
                an API so a team can send data and get back something they can defend.
              </p>
            </Prose>
          </div>
        </div>
      </section>

      {/* VISION  */}
      <section style={SECTION}>
        <div style={WIDE}>
          <Head
            tag="Where we're going"
            title="The data infrastructure for medical AI."
            sub="We start with the expert layer — the judgment only credentialed clinicians can give. From there, the whole data stack a medical model needs, across every modality: imaging, pathology, clinical text, genomics, medical LLMs. One trusted layer between medicine and the models built on it."
          />
        </div>
      </section>

      {/* CLOSE  */}
      <section style={SECTION}>
        <div style={{ ...WIDE, textAlign: 'center' }}>
          <h2 style={{ ...T_H2, maxWidth: 760, margin: '0 auto', textWrap: 'balance' }}>
            Build medical AI on data you can defend.
          </h2>
          <p style={{ ...T_LEAD, maxWidth: 560, margin: '24px auto 0' }}>
            Start with a slice, see the value, then scale. Book a demo, or read the docs and start
            from code.
          </p>
          <div style={{ display: 'flex', gap: 18, alignItems: 'center', flexWrap: 'wrap', justifyContent: 'center', marginTop: 44 }}>
            <a href="/submit" className="nav-join-cta">Book a demo →</a>
            <a href="/docs" className="iso-cta" style={{ fontSize: 12 }}>Read the docs →</a>
          </div>
        </div>
      </section>

      <EvalFooter />
    </>
  )
}
