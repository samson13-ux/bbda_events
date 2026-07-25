'use client'

import { useState } from 'react'
import { CheckCircle2 } from 'lucide-react'
import { Button } from '@/components/ui/button'

type Errors = Record<string, string>

const inputClass =
  'w-full rounded-md border border-input bg-card px-3 py-2.5 text-sm text-foreground shadow-sm outline-none transition-colors placeholder:text-muted-foreground/70 focus:border-primary focus:ring-2 focus:ring-primary/20'

export function ContactForm() {
  const [errors, setErrors] = useState<Errors>({})
  const [sent, setSent] = useState(false)

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = e.currentTarget
    const data = new FormData(form)
    const next: Errors = {}

    const nom = (data.get('nom') as string)?.trim()
    const email = (data.get('email') as string)?.trim()
    const message = (data.get('message') as string)?.trim()

    if (!nom) next.nom = 'Le nom est requis.'
    if (!email) next.email = "L'email est requis."
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) next.email = 'Email invalide.'
    if (!message) next.message = 'Le message est requis.'

    setErrors(next)
    if (Object.keys(next).length === 0) {
      setSent(true)
      form.reset()
    }
  }

  if (sent) {
    return (
      <div className="rounded-2xl border border-border bg-card p-8 text-center">
        <div className="mx-auto flex size-14 items-center justify-center rounded-full bg-primary/10 text-primary">
          <CheckCircle2 className="size-8" />
        </div>
        <h2 className="mt-5 font-serif text-2xl font-bold text-foreground">Message envoyé</h2>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          Merci de nous avoir contactés. Notre équipe vous répondra dans les meilleurs délais.
        </p>
        <Button className="mt-6" onClick={() => setSent(false)}>
          Envoyer un autre message
        </Button>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="rounded-2xl border border-border bg-card p-6 md:p-8">
      <div className="grid gap-5 sm:grid-cols-2">
        <div>
          <label htmlFor="nom" className="mb-1.5 block text-sm font-medium text-foreground">
            Nom complet<span className="ml-0.5 text-destructive">*</span>
          </label>
          <input id="nom" name="nom" className={inputClass} placeholder="Votre nom" />
          {errors.nom && <p className="mt-1 text-xs text-destructive">{errors.nom}</p>}
        </div>
        <div>
          <label htmlFor="email" className="mb-1.5 block text-sm font-medium text-foreground">
            Email<span className="ml-0.5 text-destructive">*</span>
          </label>
          <input id="email" name="email" type="email" className={inputClass} placeholder="vous@exemple.bf" />
          {errors.email && <p className="mt-1 text-xs text-destructive">{errors.email}</p>}
        </div>
      </div>

      <div className="mt-5">
        <label htmlFor="sujet" className="mb-1.5 block text-sm font-medium text-foreground">
          Sujet
        </label>
        <select id="sujet" name="sujet" className={inputClass} defaultValue="Déclaration">
          <option value="Déclaration">Déclaration d&apos;événement</option>
          <option value="Paiement">Paiement et quittances</option>
          <option value="Compte">Mon compte</option>
          <option value="Autre">Autre demande</option>
        </select>
      </div>

      <div className="mt-5">
        <label htmlFor="message" className="mb-1.5 block text-sm font-medium text-foreground">
          Message<span className="ml-0.5 text-destructive">*</span>
        </label>
        <textarea
          id="message"
          name="message"
          rows={5}
          className={`${inputClass} resize-y`}
          placeholder="Décrivez votre demande…"
        />
        {errors.message && <p className="mt-1 text-xs text-destructive">{errors.message}</p>}
      </div>

      <Button type="submit" size="lg" className="mt-6 w-full sm:w-auto">
        Envoyer le message
      </Button>
    </form>
  )
}
