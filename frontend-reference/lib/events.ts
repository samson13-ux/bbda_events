export type EventItem = {
  image: string
  type: 'Concert' | 'Festival' | 'Gala' | 'Spectacle' | 'Exposition'
  title: string
  artist: string
  date: string
  city: string
  price: string
}

export const eventTypes = [
  'Tous',
  'Concert',
  'Festival',
  'Gala',
  'Spectacle',
  'Exposition',
] as const

export const typeColors: Record<string, string> = {
  Concert: 'bg-destructive/10 text-destructive',
  Festival: 'bg-primary/10 text-primary',
  Gala: 'bg-accent/25 text-accent-foreground',
  Spectacle: 'bg-primary/10 text-primary',
  Exposition: 'bg-destructive/10 text-destructive',
}

export const events: EventItem[] = [
  {
    image: '/images/event-concert.png',
    type: 'Concert',
    title: 'Nuit des Étoiles Musicales',
    artist: 'Floby & invités',
    date: '15 mars 2026',
    city: 'Ouagadougou',
    price: '5 000 FCFA',
  },
  {
    image: '/images/event-festival.png',
    type: 'Festival',
    title: 'Festival des Masques et des Arts',
    artist: 'Troupes traditionnelles',
    date: '22 février 2026',
    city: 'Bobo-Dioulasso',
    price: '3 000 FCFA',
  },
  {
    image: '/images/event-gala.png',
    type: 'Gala',
    title: 'Gala de la Culture Burkinabè',
    artist: 'Amity Meria',
    date: '5 avril 2026',
    city: 'Koudougou',
    price: '10 000 FCFA',
  },
  {
    image: '/images/event-spectacle.png',
    type: 'Spectacle',
    title: 'Théâtre : Les Voix du Faso',
    artist: 'Compagnie Marbayassa',
    date: '18 avril 2026',
    city: 'Ouagadougou',
    price: '2 000 FCFA',
  },
  {
    image: '/images/event-exposition.png',
    type: 'Exposition',
    title: 'Regards Contemporains',
    artist: 'Collectif SIAO',
    date: '2 mai 2026',
    city: 'Ouagadougou',
    price: 'Entrée libre',
  },
  {
    image: '/images/event-concert.png',
    type: 'Concert',
    title: 'Live Acoustique du Faso',
    artist: 'Kandy Guira',
    date: '24 mai 2026',
    city: 'Bobo-Dioulasso',
    price: '4 000 FCFA',
  },
]
