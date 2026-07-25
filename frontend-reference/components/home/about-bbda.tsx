import Link from 'next/link'
import Image from 'next/image'
import { ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'

export function AboutBbda() {
  return (
    <section className="bg-background py-16 md:py-20">
      <div className="mx-auto grid max-w-6xl items-center gap-10 px-4 md:px-6 lg:grid-cols-2">
        <div className="relative aspect-[4/3] overflow-hidden rounded-2xl border border-border shadow-lg">
          <Image
            src="/images/event-spectacle.png"
            alt="Spectacle culturel sur scène au Burkina Faso"
            fill
            className="object-cover"
            sizes="(max-width: 1024px) 100vw, 50vw"
          />
        </div>
        <div>
          <h2 className="text-balance font-serif text-3xl font-bold tracking-tight text-foreground md:text-4xl">
            Le Bureau Burkinabè du Droit d&apos;Auteur
          </h2>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            Le BBDA est l&apos;institution publique chargée de la protection et de la
            gestion collective des droits d&apos;auteur et des droits voisins au
            Burkina Faso. Il perçoit les redevances auprès des organisateurs
            d&apos;événements culturels occasionnels et assure la promotion de la
            culture burkinabè.
          </p>
          <p className="mt-4 leading-relaxed text-muted-foreground">
            BBDA Events prolonge cette mission en offrant un service numérique
            moderne, transparent et accessible à tous les créateurs.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Button asChild variant="outline">
              <Link href="/legal/organisateur">
                En savoir plus
                <ArrowRight className="size-4" />
              </Link>
            </Button>
          </div>
        </div>
      </div>

      {/* Final CTA */}
      <div className="mx-auto mt-16 max-w-6xl px-4 md:px-6">
        <div className="rounded-3xl bg-primary px-6 py-12 text-center text-primary-foreground md:py-16">
          <h2 className="text-balance font-serif text-3xl font-bold md:text-4xl">
            Prêt à déclarer votre événement ?
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-pretty leading-relaxed text-primary-foreground/85">
            Créez votre compte organisateur et lancez votre déclaration en quelques minutes.
          </p>
          <Button
            asChild
            size="lg"
            variant="secondary"
            className="mt-7"
          >
            <Link href="/inscription">
              Créer mon compte organisateur
              <ArrowRight className="size-4" />
            </Link>
          </Button>
        </div>
      </div>
    </section>
  )
}
