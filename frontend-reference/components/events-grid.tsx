'use client'

import { useState } from 'react'
import Image from 'next/image'
import { Calendar, MapPin, Ticket, Search } from 'lucide-react'
import { events, eventTypes, typeColors } from '@/lib/events'

export function EventsGrid() {
  const [active, setActive] = useState<string>('Tous')
  const [query, setQuery] = useState('')

  const filtered = events.filter((ev) => {
    const matchType = active === 'Tous' || ev.type === active
    const matchQuery =
      query.trim() === '' ||
      ev.title.toLowerCase().includes(query.toLowerCase()) ||
      ev.artist.toLowerCase().includes(query.toLowerCase()) ||
      ev.city.toLowerCase().includes(query.toLowerCase())
    return matchType && matchQuery
  })

  return (
    <div>
      {/* Controls */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap gap-2">
          {eventTypes.map((type) => (
            <button
              key={type}
              onClick={() => setActive(type)}
              className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                active === type
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-secondary text-secondary-foreground hover:bg-secondary/70'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
        <div className="relative w-full lg:w-72">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Rechercher un événement…"
            className="w-full rounded-md border border-input bg-card py-2.5 pl-9 pr-3 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground/70 focus:border-primary focus:ring-2 focus:ring-primary/20"
          />
        </div>
      </div>

      {/* Grid */}
      {filtered.length === 0 ? (
        <p className="mt-12 text-center text-muted-foreground">
          Aucun événement ne correspond à votre recherche.
        </p>
      ) : (
        <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((ev) => (
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
                  <p className="flex items-center gap-2">
                    <Ticket className="size-4 text-primary" />
                    {ev.price}
                  </p>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  )
}
