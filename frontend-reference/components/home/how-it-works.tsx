import { FileText, Mail, FileCheck } from 'lucide-react'

const steps = [
  {
    icon: FileText,
    title: 'Déclarez',
    text: 'Remplissez le formulaire de déclaration de votre manifestation culturelle en quelques minutes.',
  },
  {
    icon: Mail,
    title: 'Recevez votre montant',
    text: "Un agent du BBDA évalue votre dossier et vous notifie par email la redevance à régler.",
  },
  {
    icon: FileCheck,
    title: 'Payez et téléchargez',
    text: 'Réglez la redevance, téléchargez votre quittance et promouvez votre événement.',
  },
]

export function HowItWorks() {
  return (
    <section className="bg-background py-16 md:py-20">
      <div className="mx-auto max-w-6xl px-4 md:px-6">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-balance font-serif text-3xl font-bold tracking-tight text-foreground md:text-4xl">
            Qu&apos;est-ce que BBDA Events ?
          </h2>
          <p className="mt-4 text-pretty leading-relaxed text-muted-foreground">
            BBDA Events numérise le processus de déclaration des événements culturels
            occasionnels — de la déclaration à la délivrance de la quittance — tout en
            offrant une vitrine publique pour la culture burkinabè.
          </p>
        </div>

        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {steps.map((step, i) => (
            <div
              key={step.title}
              className="relative rounded-2xl border border-border bg-card p-6"
            >
              <span className="absolute right-5 top-5 font-serif text-3xl font-bold text-secondary-foreground/15">
                0{i + 1}
              </span>
              <div className="flex size-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <step.icon className="size-6" />
              </div>
              <h3 className="mt-5 text-lg font-semibold text-foreground">{step.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                {step.text}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
