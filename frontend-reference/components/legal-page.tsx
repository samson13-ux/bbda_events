import Link from 'next/link'
import { SiteNav } from '@/components/site-nav'
import { SiteFooter } from '@/components/site-footer'
import { PageHeader } from '@/components/page-header'

const legalLinks = [
  { label: 'Politique de confidentialité', href: '/legal/confidentialite' },
  { label: "Conditions générales d'utilisation", href: '/legal/cgu' },
  { label: "Politique de l'organisateur", href: '/legal/organisateur' },
  { label: 'Politique du public', href: '/legal/public' },
]

export type LegalSection = { heading: string; body: string[] }

export function LegalPage({
  title,
  updated,
  current,
  sections,
}: {
  title: string
  updated: string
  current: string
  sections: LegalSection[]
}) {
  return (
    <>
      <SiteNav />
      <main>
        <PageHeader eyebrow="Informations légales" title={title} description={`Dernière mise à jour : ${updated}`} />

        <section className="bg-background py-12 md:py-16">
          <div className="mx-auto grid max-w-6xl gap-10 px-4 md:px-6 lg:grid-cols-[240px_1fr]">
            {/* Side nav */}
            <aside className="lg:sticky lg:top-24 lg:self-start">
              <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Documents légaux
              </p>
              <nav className="flex flex-col gap-1">
                {legalLinks.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`rounded-md px-3 py-2 text-sm transition-colors ${
                      link.href === current
                        ? 'bg-primary/10 font-medium text-primary'
                        : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
                    }`}
                  >
                    {link.label}
                  </Link>
                ))}
              </nav>
            </aside>

            {/* Content */}
            <article className="max-w-2xl">
              {sections.map((section) => (
                <div key={section.heading} className="mb-8">
                  <h2 className="font-serif text-xl font-bold text-foreground">{section.heading}</h2>
                  {section.body.map((p, i) => (
                    <p key={i} className="mt-3 text-sm leading-relaxed text-muted-foreground">
                      {p}
                    </p>
                  ))}
                </div>
              ))}
            </article>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  )
}
