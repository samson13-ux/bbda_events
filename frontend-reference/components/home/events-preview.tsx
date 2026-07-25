import Link from 'next/link'
import Image from 'next/image'
import { Calendar, MapPin, ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'

const events = [
  {
    image: '/images/event-concert.png',
    type: 'Concert',
    title: 'Nuit des Étoiles Musicales',
    artist: 'Floby & invités',
    date: '15 mars 2026',
    city: 'Ouagadougou',
  },
  {
    image: '/images/event-festival.png',
    type: 'Festival',
    title: 'Festival des Masques et des Arts',
    artist: 'Troupes traditionnelles',
    date: '22 février 2026',
    city: 'Bobo-Dioulasso',
  },
  {
    image: '/images/event-gala.png',
    type: 'Gala',
    title: 'Gala de la Culture Burkinabè',
    artist: 'Amity Meria',
    date: '5 avril 2026',
    city: 'Koudougou',
  },
]

const typeColors: Record<string, string> = {
  Concert: 'bg-destructive/10 text-destructive',
  Festival: 'bg-primary/10 text-primary',
  Gala: 'bg-accent/25 text-accent-foreground',
}

export function EventsPreview() {
  return (
    <section className="bg-background py-16 md:py-20">
      <div className="mx-auto max-w-6xl px-4 md:px-6">
        <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <h2 className="text-balance font-serif text-3xl font-bold tracking-tight text-foreground md:text-4xl">
              Événements à venir
            </h2>
            <p className="mt-3 max-w-md text-pretty leading-relaxed text-muted-foreground">
              Découvrez une sélection d&apos;événements culturels déclarés et promus
              sur la plateforme.
            </p>
          </div>
          <Button asChild variant="outline">
            <Link href="/evenements">
              Tous les événements
              <ArrowRight className="size-4" />
            </Link>
          </Button>
        </div>

        <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {events.map((ev) => (
            <article
              key={ev.title}
              className="group overflow-hidden rounded-2xl border border-border bg-card transition-shadow hover:shadow-lg"
            >
              <div className="relative aspect-[16/10] overflow-hidden">
                <Image
                  src={ev.image || '/placeholder.svg'}
                  alt={`Affiche de ${ev.title}`}
                  fill
                  className="object-cover transition-transform duration-300 group-hover:scale-105"
                  sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
                />
                <span
                  className={`absolute left-3 top-3 rounded-full px-2.5 py-1 text-xs font-semibold ${typeColors[ev.type]}`}
                >
                  {ev.type}
                </span>
              </div>
              <div className="p-5">
                <h3 className="font-serif text-lg font-bold text-foreground">{ev.title}</h3>
                <p className="mt-1 text-sm text-primary">{ev.artist}</p>
                <div className="mt-4 space-y-1.5 text-sm text-muted-foreground">
                  <p className="flex items-center gap-2">
                    <Calendar className="size-4 text-primary" />
                    {ev.date}
                  </p>
                  <p className="flex items-center gap-2">
                    <MapPin className="size-4 text-primary" />
                    {ev.city}
                  </p>
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}
