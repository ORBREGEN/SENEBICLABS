import Logo from './Logo'

// Conversion nav for the /evaluate sell page. Brand-consistent with the site nav
// (same .top pill, hairline, fonts, monochrome) but stripped for selling: one exit
// home via the logo, two in-page anchors to the proof, one persistent CTA. No site
// directory links (they are exits away from converting), no hamburger.
export default function EvalNav() {
  return (
    <nav className="top scrolled">
      <div className="wrap row">

        {/* The one clean exit: logo -> home */}
        <a className="brand" href="/">
          <span className="mark"><Logo size={20} /></span>
          Senebiclabs
        </a>

        {/* In-page anchors to the proof (desktop only; .nav-links hides under 768px).
            All four are on-page section jumps — About is this service's #about, not the
            main-site company About. No directory links, no dropdowns. */}
        <div className="nav-links">
          <a href="#what-you-get">What you get</a>
          <a href="#modalities">Modalities</a>
          <a href="#about">About</a>
          <a href="#why-us">Why us</a>
        </div>

        {/* Persistent CTA — always visible, including mobile */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, gridColumn: 3 }}>
          <a href="https://calendly.com/senebiclabs/30min" target="_blank" rel="noopener noreferrer" className="nav-join-cta">Book a demo →</a>
        </div>

      </div>
    </nav>
  )
}
