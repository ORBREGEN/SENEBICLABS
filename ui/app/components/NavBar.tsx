'use client'

import { useState } from 'react'
import Logo from './Logo'

type Page = 'home' | 'patients' | 'about' | 'analyse' | 'experts' | 'contribute'

const LINKS: { label: string; href: string; page: Page }[] = [
  { label: 'Patients',    href: '/patients',   page: 'patients'   },
  { label: 'Specialists', href: '/experts',    page: 'experts'    },
  { label: 'Contribute',  href: '/contribute', page: 'contribute' },
  { label: 'About',       href: '/about',      page: 'about'      },
]

export default function NavBar({ active, onLight }: { active?: Page; onLight?: boolean }) {
  const [open, setOpen] = useState(false)

  return (
    <nav className={`top scrolled${open ? ' nav-open' : ''}${onLight ? ' nav-on-light' : ''}`}>
      <div className="wrap row">

        <a className="brand" href="/" onClick={() => setOpen(false)}>
          <span className="mark"><Logo size={20} /></span>
          Senebiclabs
        </a>

        {/* Desktop links */}
        <div className="nav-links">
          {LINKS.map(l => (
            <a key={l.page} href={l.href} style={active === l.page ? { color: 'var(--ink)' } : {}}>
              {l.label}
            </a>
          ))}
        </div>

        {/* Right side: CTA on desktop, hamburger on mobile */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, gridColumn: 3 }}>
          <a href="/experts" className="nav-join-cta nav-cta-desktop">Join as specialist →</a>
          <button
            className="nav-hamburger"
            onClick={() => setOpen(o => !o)}
            aria-label={open ? 'Close menu' : 'Open menu'}
          >
            {open ? (
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path d="M2 2l14 14M16 2L2 16" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path d="M2 4h14M2 9h14M2 14h14" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
              </svg>
            )}
          </button>
        </div>

      </div>

      {/* Mobile menu */}
      {open && (
        <div className="nav-mobile-menu">
          {LINKS.map(l => (
            <a
              key={l.page}
              href={l.href}
              className={active === l.page ? 'nav-mobile-active' : ''}
              onClick={() => setOpen(false)}
            >
              {l.label}
            </a>
          ))}
          <a href="/experts" className="nav-join-cta" onClick={() => setOpen(false)}>
            Join as specialist →
          </a>
        </div>
      )}
    </nav>
  )
}
