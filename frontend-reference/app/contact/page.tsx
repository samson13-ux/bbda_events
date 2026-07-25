import { MapPin, Phone, Mail, Clock } from 'lucide-react'
import { SiteNav } from '@/components/site-nav'
import { SiteFooter } from '@/components/site-footer'
import { PageHeader } from '@/components/page-header'
import { ContactForm } from '@/components/contact-form'

export const metadata = {
  title: 'Contact — BBDA Events',
  description: 'Contactez le Bureau Burkinabè du Droit d’Auteur (BBDA).',
}

const infos = [
  {
    icon: MapPin,
    label: 'Adresse',
    value: 'Avenue Bassawarga, 01 BP 3926, Ouagadougou 01, Burkina Faso',
  },
  { icon: Phone, label: 'Téléphone', value: '+226 25 30 00 00' },
  { icon: Mail, label: 'Email', value: 'contact@bbda.bf' },
  { icon: Clock, label: 'Horaires', value: 'Lun. – Ven. : 7h30 – 16h00' },
]

export default function ContactPage() {
  return (
    <>
      <SiteNav />
      <main>
        <PageHeader
          eyebrow="Nous contacter"
          title="Entrons en contact"
          description="Une question sur vos déclarations ou vos droits d'auteur ? Notre équipe est à votre écoute."
        />

        <section className="bg-background py-12 md:py-16">
          <div className="mx-auto grid max-w-6xl gap-10 px-4 md:px-6 lg:grid-cols-[1fr_1.4fr]">
            {/* Info panel */}
            <div>
              <h2 className="font-serif text-2xl font-bold text-foreground">Coordonnées</h2>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                Rendez-nous visite ou joignez-nous par téléphone et par email.
              </p>
              <ul className="mt-6 space-y-5">
                {infos.map((info) => (
                  <li key={info.label} className="flex items-start gap-3">
                    <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                      <info.icon className="size-5" />
                    </span>
                    <div>
                      <p className="text-sm font-medium text-foreground">{info.label}</p>
                      <p className="text-sm text-muted-foreground">{info.value}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>

            {/* Form */}
            <div>
              <ContactForm />
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  )
}
