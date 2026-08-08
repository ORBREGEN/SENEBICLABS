// Self-contained footer for the eval-business funnel — no links to the science side.
const DISPLAY = '"SF Pro Display", -apple-system, BlinkMacSystemFont, system-ui, sans-serif'
const BODY = '"DM Sans", system-ui, sans-serif'

export default function EvalFooter() {
  return (
    <footer style={{ borderTop: '1px solid var(--hairline)', padding: 'clamp(48px, 7vw, 84px) 0' }}>
      <div className="wrap" style={{ textAlign: 'center' }}>
        <div style={{ fontFamily: DISPLAY, fontWeight: 300, fontSize: 19, letterSpacing: '0.04em', marginBottom: 14 }}>
          Senebiclabs
        </div>
        <p style={{ fontFamily: BODY, fontWeight: 300, fontSize: 14, color: 'var(--slate)', lineHeight: 1.6, maxWidth: 460, margin: '0 auto 24px' }}>
          The clinician-grade data layer for medical AI — labeling, evaluation, and RLHF.
        </p>
        <a href="/submit" className="iso-cta">Book a demo →</a>
        <div style={{ display: 'flex', gap: 24, justifyContent: 'center', flexWrap: 'wrap', marginTop: 36 }}>
          <a href="/evaluate/privacy" className="iso-cta iso-cta--muted">Privacy</a>
          <a href="/evaluate/terms" className="iso-cta iso-cta--muted">Terms</a>
          <a href="mailto:senebiclabs@gmail.com" className="iso-cta iso-cta--muted">Contact</a>
        </div>
        <p style={{ fontFamily: 'Geist Mono, monospace', fontSize: 11, letterSpacing: '0.1em', color: 'var(--slate)', marginTop: 24 }}>
          © 2026 Senebiclabs
        </p>
      </div>
    </footer>
  )
}
