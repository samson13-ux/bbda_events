import Image from 'next/image'
import { Check } from 'lucide-react'
import { SiteNav } from '@/components/site-nav'
import { SiteFooter } from '@/components/site-footer'
import { LoginForm } from '@/components/login-form'

export const metadata = {
  title: 'Connexion — BBDA Events',
  description: 'Connectez-vous à votre espace organisateur BBDA Events.',
}

const benefits = [
  'Accédez à vos déclarations en cours',
  'Téléchargez vos quittances et attestations',
  'Gérez la promotion de vos événements',
]

export default function ConnexionPage() {
  return (
    <>
      <SiteNav />
      <main className="bg-secondary/30">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 py-12 md:px-6 lg:grid-cols-[1.1fr_1fr] lg:py-16">
          {/* Promo panel */}
          <div className="hidden flex-col lg:flex">
            <div className="relative flex-1 overflow-hidden rounded-2xl border border-border">
              <Image
                src="/images/event-gala.png"
                alt="Gala culturel burkinabè en soirée"
                fill
                className="object-cover"
                sizes="50vw"
              />
              <div className="absolute inset-0 bg-primary/70" />
              <div className="absolute inset-0 flex flex-col justify-end p-8 text-primary-foreground">
                <h2 className="text-balance font-serif text-3xl font-bold">
                  Bon retour parmi nous
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
          <div className="flex flex-col justify-center">
            <div className="mb-6">
              <h1 className="font-serif text-3xl font-bold tracking-tight text-foreground md:text-4xl">
                Connexion
              </h1>
              <p className="mt-2 text-muted-foreground">
                Accédez à votre espace organisateur pour gérer vos événements.
              </p>
            </div>
            <LoginForm />
          </div>
        </div>
      </main>
      <SiteFooter />
    </>
  )
}
