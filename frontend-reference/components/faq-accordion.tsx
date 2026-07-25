'use client'

import { useState } from 'react'
import { ChevronDown } from 'lucide-react'

const faqs = [
  {
    q: 'Comment déclarer un événement culturel auprès du BBDA ?',
    a: "Créez un compte organisateur, connectez-vous, puis remplissez le formulaire de déclaration en indiquant le type d'événement, la date, le lieu et le programme artistique. Votre dossier est ensuite instruit par les services du BBDA.",
  },
  {
    q: 'Quels documents dois-je fournir ?',
    a: "Selon le type d'événement : la programmation détaillée, la liste des œuvres exploitées, le contrat de location de salle et une pièce d'identité de l'organisateur. La liste complète s'affiche lors de la déclaration.",
  },
  {
    q: 'Comment sont calculés les droits d’auteur à verser ?',
    a: "Les redevances dépendent de la nature de l'événement, de la jauge et du prix des billets. Une estimation vous est présentée avant validation, et la quittance officielle est générée après paiement.",
  },
  {
    q: 'Puis-je promouvoir mon événement sur la plateforme ?',
    a: "Oui. Une fois votre déclaration validée, votre événement peut être publié sur la page publique « Événements » afin de toucher un large public.",
  },
  {
    q: 'Comment récupérer ma quittance ou mon attestation ?',
    a: "Toutes vos quittances et attestations sont disponibles dans votre espace organisateur, dans l'onglet « Mes déclarations », et téléchargeables au format PDF.",
  },
]

export function FaqAccordion() {
  const [open, setOpen] = useState<number | null>(0)

  return (
    <div className="divide-y divide-border overflow-hidden rounded-2xl border border-border bg-card">
      {faqs.map((faq, i) => {
        const isOpen = open === i
        return (
          <div key={faq.q}>
            <button
              onClick={() => setOpen(isOpen ? null : i)}
              className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left"
              aria-expanded={isOpen}
            >
              <span className="font-medium text-foreground">{faq.q}</span>
              <ChevronDown
                className={`size-5 shrink-0 text-primary transition-transform ${isOpen ? 'rotate-180' : ''}`}
              />
            </button>
            {isOpen && (
              <p className="px-5 pb-5 text-sm leading-relaxed text-muted-foreground">{faq.a}</p>
            )}
          </div>
        )
      })}
    </div>
  )
}
