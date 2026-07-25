import { Users, Ticket, LayoutDashboard, Check } from 'lucide-react'

const solutions = [
  {
    icon: Ticket,
    title: 'Pour les organisateurs',
    points: [
      'Déclaration en ligne simplifiée',
      'Suivi des dossiers en temps réel',
      'Quittance numérique téléchargeable',
      'Promotion de votre événement',
    ],
  },
  {
    icon: Users,
    title: 'Pour le public',
    points: [
      'Découverte des événements culturels',
      'Recherche par ville et par type',
      'Affiches, dates et lieux détaillés',
      'Agenda culturel burkinabè',
    ],
  },
  {
    icon: LayoutDashboard,
    title: 'Pour le BBDA',
    points: [
      'Gestion centralisée des déclarations',
      'Suivi des redevances et arriérés',
      'Tableau de bord statistiques',
      'Modération des événements publics',
    ],
  },
]

export function Solutions() {
  return (
    <section className="bg-secondary/40 py-16 md:py-20">
      <div className="mx-auto max-w-6xl px-4 md:px-6">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-balance font-serif text-3xl font-bold tracking-tight text-foreground md:text-4xl">
            Une solution pour chaque acteur
          </h2>
          <p className="mt-4 text-pretty leading-relaxed text-muted-foreground">
            De l&apos;organisateur au grand public, en passant par les agents du BBDA.
          </p>
        </div>

        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {solutions.map((s) => (
            <div key={s.title} className="rounded-2xl border border-border bg-card p-6">
              <div className="flex size-12 items-center justify-center rounded-xl bg-accent/20 text-accent-foreground">
                <s.icon className="size-6" />
              </div>
              <h3 className="mt-5 text-lg font-semibold text-foreground">{s.title}</h3>
              <ul className="mt-4 space-y-2.5">
                {s.points.map((p) => (
                  <li key={p} className="flex items-start gap-2 text-sm text-muted-foreground">
                    <Check className="mt-0.5 size-4 shrink-0 text-primary" />
                    {p}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
