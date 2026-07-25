'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Menu, X, ChevronDown, LogIn } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { BrandLogo } from '@/components/brand-logo'
import { FasoStripe } from '@/components/faso-stripe'

const navLinks = [
  { label: 'Accueil', href: '/' },
  { label: 'Événements', href: '/evenements' },
  { label: 'Support', href: '/support' },
  { label: 'Contact', href: '/contact' },
]

const legalLinks = [
  { label: 'Politique de confidentialité', href: '/legal/confidentialite' },
  { label: "Conditions générales d'utilisation", href: '/legal/cgu' },
  { label: "Politique de l'organisateur", href: '/legal/organisateur' },
  { label: 'Politique du public', href: '/legal/public' },
]

export function SiteNav() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [legalOpen, setLegalOpen] = useState(false)

  return (
    <header className="sticky top-0 z-50 w-full">
      <FasoStripe />
      <div className="border-b border-border bg-background/90 backdrop-blur">
        <nav className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 md:px-6">
          <Link href="/" aria-label="BBDA Events, accueil">
            <BrandLogo />
          </Link>

          {/* Desktop links */}
          <div className="hidden items-center gap-1 lg:flex">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="rounded-md px-3 py-2 text-sm font-medium text-foreground/80 transition-colors hover:bg-secondary hover:text-foreground"
              >
                {link.label}
              </Link>
            ))}

            {/* Legal dropdown */}
            <div
              className="relative"
              onMouseEnter={() => setLegalOpen(true)}
              onMouseLeave={() => setLegalOpen(false)}
            >
              <button
                className="flex items-center gap-1 rounded-md px-3 py-2 text-sm font-medium text-foreground/80 transition-colors hover:bg-secondary hover:text-foreground"
                aria-expanded={legalOpen}
              >
                Légal
                <ChevronDown className="size-4" />
              </button>
              {legalOpen && (
                <div className="absolute right-0 top-full w-64 rounded-lg border border-border bg-popover p-1.5 shadow-lg">
                  {legalLinks.map((link) => (
                    <Link
                      key={link.href}
                      href={link.href}
                      className="block rounded-md px-3 py-2 text-sm text-popover-foreground transition-colors hover:bg-secondary"
                    >
                      {link.label}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="hidden items-center gap-2 lg:flex">
            <Button asChild variant="ghost" size="sm">
              <Link href="/connexion">
                <LogIn className="size-4" />
                Se connecter
              </Link>
            </Button>
            <Button asChild size="sm">
              <Link href="/inscription">Déclarer un événement</Link>
            </Button>
          </div>

          {/* Mobile toggle */}
          <button
            className="inline-flex items-center justify-center rounded-md p-2 text-foreground lg:hidden"
            onClick={() => setMobileOpen((o) => !o)}
            aria-label={mobileOpen ? 'Fermer le menu' : 'Ouvrir le menu'}
            aria-expanded={mobileOpen}
          >
            {mobileOpen ? <X className="size-6" /> : <Menu className="size-6" />}
          </button>
        </nav>

        {/* Mobile panel */}
        {mobileOpen && (
          <div className="border-t border-border bg-background lg:hidden">
            <div className="mx-auto max-w-6xl space-y-1 px-4 py-4">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className="block rounded-md px-3 py-2.5 text-base font-medium text-foreground/90 hover:bg-secondary"
                >
                  {link.label}
                </Link>
              ))}
              <p className="px-3 pt-3 pb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Légal
              </p>
              {legalLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className="block rounded-md px-3 py-2 text-sm text-foreground/80 hover:bg-secondary"
                >
                  {link.label}
                </Link>
              ))}
              <div className="flex flex-col gap-2 pt-4">
                <Button asChild variant="outline">
                  <Link href="/connexion" onClick={() => setMobileOpen(false)}>
                    Se connecter
                  </Link>
                </Button>
                <Button asChild>
                  <Link href="/inscription" onClick={() => setMobileOpen(false)}>
                    Déclarer un événement
                  </Link>
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </header>
  )
}
