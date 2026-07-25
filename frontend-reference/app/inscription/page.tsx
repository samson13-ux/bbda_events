import Image from 'next/image'
import { Check } from 'lucide-react'
import { SiteNav } from '@/components/site-nav'
import { SiteFooter } from '@/components/site-footer'
import { RegisterForm } from '@/components/register-form'

const benefits = [
  'Déclarez vos événements en ligne, sans déplacement',
  'Suivez vos dossiers et téléchargez vos quittances',
  'Promouvez vos événements sur la page publique',
]

export default function InscriptionPage() {
  return (
    <>
      <SiteNav />
      <main className="bg-secondary/30">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 py-12 md:px-6 lg:grid-cols-[1fr_1.1fr] lg:py-16">
          {/* Left promo panel */}
          <div className="hidden flex-col lg:flex">
            <div className="relative flex-1 overflow-hidden rounded-2xl border border-border">
              <Image
                src="/images/event-festival.png"
                alt="Festival culturel burkinabè avec danseurs en tenues traditionnelles"
                fill
                className="object-cover"
                sizes="50vw"
              />
              <div className="absolute inset-0 bg-primary/70" />
              <div className="absolute inset-0 flex flex-col justify-end p-8 text-primary-foreground">
                <h2 className="text-balance font-serif text-3xl font-bold">
                  Rejoignez la communauté des organisateurs culturels
                </h2>
                <ul className="mt-6 space-y-3">
                  {benefits.map((b) => (
                    <li key={b} className="flex items-start gap-2.5 text-sm">
                      <span className="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full bg-primary-foreground/20">
                        <Check className="size-3.5" />
                      </span>
                      {b}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* Form */}
          <div>
            <div className="mb-6">
              <h1 className="font-serif text-3xl font-bold tracking-tight text-foreground md:text-4xl">
                Créer un compte organisateur
              </h1>
              <p className="mt-2 text-muted-foreground">
                Renseignez vos informations pour commencer à déclarer vos événements
                culturels auprès du BBDA.
              </p>
            </div>
            <RegisterForm />
          </div>
        </div>
      </main>
      <SiteFooter />
    </>
  )
}
