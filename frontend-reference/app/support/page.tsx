import Link from 'next/link'
import { BookOpen, LifeBuoy, MessageCircle, Phone } from 'lucide-react'
import { SiteNav } from '@/components/site-nav'
import { SiteFooter } from '@/components/site-footer'
import { PageHeader } from '@/components/page-header'
import { FaqAccordion } from '@/components/faq-accordion'

export const metadata = {
  title: 'Support — BBDA Events',
  description: "Centre d'aide et foire aux questions de la plateforme BBDA Events.",
}

const channels = [
  {
    icon: BookOpen,
    title: 'Guides pratiques',
    text: 'Tutoriels pas à pas pour déclarer et promouvoir vos événements.',
  },
  {
    icon: Phone,
    title: 'Assistance téléphonique',
    text: 'Du lundi au vendredi, de 7h30 à 16h00 : +226 25 30 00 00.',
  },
  {
    icon: MessageCircle,
    title: 'Nous écrire',
    text: 'Une question précise ? Contactez notre équipe support.',
  },
]

export default function SupportPage() {
  return (
    <>
      <SiteNav />
      <main>
        <PageHeader
          eyebrow="Centre d'aide"
          title="Comment pouvons-nous vous aider ?"
          description="Trouvez des réponses à vos questions sur la déclaration et la promotion de vos événements culturels."
        />

        <section className="bg-background py-12 md:py-16">
          <div className="mx-auto max-w-6xl px-4 md:px-6">
            <div className="grid gap-6 md:grid-cols-3">
              {channels.map((c) => (
                <div key={c.title} className="rounded-2xl border border-border bg-card p-6">
                  <div className="flex size-11 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <c.icon className="size-5" />
                  </div>
                  <h3 className="mt-4 font-serif text-lg font-bold text-foreground">{c.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{c.text}</p>
                </div>
              ))}
            </div>

            <div className="mt-14">
              <div className="mb-6 flex items-center gap-2">
                <LifeBuoy className="size-5 text-primary" />
                <h2 className="font-serif text-2xl font-bold text-foreground">
                  Foire aux questions
                </h2>
              </div>
              <FaqAccordion />
            </div>

            <div className="mt-12 rounded-2xl bg-secondary/50 p-8 text-center">
              <h2 className="font-serif text-xl font-bold text-foreground">
                Vous ne trouvez pas votre réponse ?
              </h2>
              <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-muted-foreground">
                Notre équipe est disponible pour vous accompagner dans vos démarches.
              </p>
              <Link
                href="/contact"
                className="mt-5 inline-flex items-center justify-center rounded-md bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90"
              >
                Contacter le support
              </Link>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  )
}
