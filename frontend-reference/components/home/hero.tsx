import Link from 'next/link'
import Image from 'next/image'
import { ArrowRight, Compass } from 'lucide-react'
import { Button } from '@/components/ui/button'

export function Hero() {
  return (
    <section className="relative overflow-hidden bg-background">
      <div className="mx-auto grid max-w-6xl items-center gap-10 px-4 py-16 md:px-6 lg:grid-cols-2 lg:py-24">
        <div>
          <span className="inline-flex items-center gap-2 rounded-full border border-border bg-secondary px-3 py-1 text-xs font-medium text-secondary-foreground">
            <span className="size-1.5 rounded-full bg-primary" />
            Plateforme officielle du BBDA
          </span>
          <h1 className="mt-5 text-balance font-serif text-4xl font-bold leading-tight tracking-tight text-foreground md:text-5xl lg:text-6xl">
            Plateforme de déclaration et de promotion des événements culturels
          </h1>
          <p className="mt-5 text-pretty text-lg font-semibold text-primary">
            Déclarez. Promouvez. Célébrez.
          </p>
          <p className="mt-2 max-w-md text-pretty leading-relaxed text-muted-foreground">
            Le BBDA, une clé pour l&apos;épanouissement des créateurs. Déclarez vos
            manifestations en ligne et donnez de la visibilité à la culture burkinabè.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Button asChild size="lg">
              <Link href="/inscription">
                Déclarer mon événement
                <ArrowRight className="size-4" />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link href="/evenements">
                <Compass className="size-4" />
                Découvrir les événements
              </Link>
            </Button>
          </div>
        </div>

        <div className="relative">
          <div className="relative aspect-[4/3] overflow-hidden rounded-2xl border border-border shadow-xl">
            <Image
              src="/images/hero-concert.png"
              alt="Concert culturel en plein air au Burkina Faso avec une foule enthousiaste"
              fill
              priority
              className="object-cover"
              sizes="(max-width: 1024px) 100vw, 50vw"
            />
          </div>
          <div className="absolute -bottom-5 -left-5 hidden rounded-xl border border-border bg-card p-4 shadow-lg sm:block">
            <p className="font-serif text-2xl font-bold text-primary">+250</p>
            <p className="text-xs text-muted-foreground">événements promus</p>
          </div>
        </div>
      </div>
    </section>
  )
}
