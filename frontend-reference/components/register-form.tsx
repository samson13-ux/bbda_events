'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Eye, EyeOff, CheckCircle2 } from 'lucide-react'
import { Button } from '@/components/ui/button'

type Errors = Record<string, string>

const inputClass =
  'w-full rounded-md border border-input bg-card px-3 py-2.5 text-sm text-foreground shadow-sm outline-none transition-colors placeholder:text-muted-foreground/70 focus:border-primary focus:ring-2 focus:ring-primary/20'

function Field({
  label,
  htmlFor,
  required,
  error,
  children,
}: {
  label: string
  htmlFor: string
  required?: boolean
  error?: string
  children: React.ReactNode
}) {
  return (
    <div>
      <label htmlFor={htmlFor} className="mb-1.5 block text-sm font-medium text-foreground">
        {label}
        {required && <span className="ml-0.5 text-destructive">*</span>}
      </label>
      {children}
      {error && <p className="mt-1 text-xs text-destructive">{error}</p>}
    </div>
  )
}

export function RegisterForm() {
  const [showPassword, setShowPassword] = useState(false)
  const [errors, setErrors] = useState<Errors>({})
  const [submitted, setSubmitted] = useState(false)

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = e.currentTarget
    const data = new FormData(form)
    const next: Errors = {}

    const nom = (data.get('nom') as string)?.trim()
    const prenom = (data.get('prenom') as string)?.trim()
    const telephone = (data.get('telephone') as string)?.trim()
    const email = (data.get('email') as string)?.trim()
    const password = (data.get('password') as string) ?? ''
    const confirm = (data.get('confirm') as string) ?? ''
    const cgu = data.get('cgu')

    if (!nom) next.nom = 'Le nom est requis.'
    if (!prenom) next.prenom = 'Le prénom est requis.'
    if (!telephone) next.telephone = 'Le téléphone est requis.'
    if (!email) next.email = "L'email est requis."
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) next.email = 'Email invalide.'
    if (!password) next.password = 'Le mot de passe est requis.'
    else if (password.length < 8) next.password = 'Au moins 8 caractères.'
    if (confirm !== password) next.confirm = 'Les mots de passe ne correspondent pas.'
    if (!cgu) next.cgu = 'Vous devez accepter les conditions.'

    setErrors(next)
    if (Object.keys(next).length === 0) {
      setSubmitted(true)
      form.reset()
    }
  }

  if (submitted) {
    return (
      <div className="rounded-2xl border border-border bg-card p-8 text-center">
        <div className="mx-auto flex size-14 items-center justify-center rounded-full bg-primary/10 text-primary">
          <CheckCircle2 className="size-8" />
        </div>
        <h2 className="mt-5 font-serif text-2xl font-bold text-foreground">
          Compte créé avec succès
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          Un email de confirmation vous a été envoyé. Vous pouvez maintenant vous
          connecter pour déclarer votre premier événement.
        </p>
        <Button asChild className="mt-6">
          <Link href="/connexion">Se connecter</Link>
        </Button>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="rounded-2xl border border-border bg-card p-6 md:p-8">
      <div className="grid gap-5 sm:grid-cols-2">
        <Field label="Nom" htmlFor="nom" required error={errors.nom}>
          <input id="nom" name="nom" className={inputClass} placeholder="Ex. FOFANA" />
        </Field>
        <Field label="Prénom" htmlFor="prenom" required error={errors.prenom}>
          <input id="prenom" name="prenom" className={inputClass} placeholder="Ex. Samson" />
        </Field>
      </div>

      <div className="mt-5">
        <Field label="Qualité" htmlFor="qualite" required error={errors.qualite}>
          <select id="qualite" name="qualite" className={inputClass} defaultValue="Organisateur">
            <option value="Organisateur">Organisateur</option>
            <option value="Promoteur">Promoteur culturel</option>
            <option value="Association">Association</option>
            <option value="Autre">Autre</option>
          </select>
        </Field>
      </div>

      <div className="mt-5 grid gap-5 sm:grid-cols-2">
        <Field label="Téléphone" htmlFor="telephone" required error={errors.telephone}>
          <input
            id="telephone"
            name="telephone"
            type="tel"
            className={inputClass}
            placeholder="Ex. 70 00 00 00"
          />
        </Field>
        <Field label="Email" htmlFor="email" required error={errors.email}>
          <input
            id="email"
            name="email"
            type="email"
            className={inputClass}
            placeholder="vous@exemple.bf"
          />
        </Field>
      </div>

      <div className="mt-5 grid gap-5 sm:grid-cols-2">
        <Field label="Mot de passe" htmlFor="password" required error={errors.password}>
          <div className="relative">
            <input
              id="password"
              name="password"
              type={showPassword ? 'text' : 'password'}
              className={inputClass}
              placeholder="8 caractères minimum"
            />
            <button
              type="button"
              onClick={() => setShowPassword((s) => !s)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              aria-label={showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
            >
              {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
            </button>
          </div>
        </Field>
        <Field label="Confirmer le mot de passe" htmlFor="confirm" required error={errors.confirm}>
          <input
            id="confirm"
            name="confirm"
            type={showPassword ? 'text' : 'password'}
            className={inputClass}
            placeholder="Ressaisir le mot de passe"
          />
        </Field>
      </div>

      <div className="mt-6">
        <label className="flex items-start gap-2.5 text-sm text-muted-foreground">
          <input
            type="checkbox"
            name="cgu"
            className="mt-0.5 size-4 accent-[var(--primary)]"
          />
          <span>
            J&apos;accepte les{' '}
            <Link href="/legal/cgu" className="font-medium text-primary hover:underline">
              conditions générales d&apos;utilisation
            </Link>{' '}
            et la{' '}
            <Link href="/legal/confidentialite" className="font-medium text-primary hover:underline">
              politique de confidentialité
            </Link>{' '}
            du BBDA.
          </span>
        </label>
        {errors.cgu && <p className="mt-1 text-xs text-destructive">{errors.cgu}</p>}
      </div>

      <Button type="submit" size="lg" className="mt-6 w-full">
        Créer mon compte
      </Button>

      <p className="mt-4 text-center text-sm text-muted-foreground">
        Vous avez déjà un compte ?{' '}
        <Link href="/connexion" className="font-medium text-primary hover:underline">
          Se connecter
        </Link>
      </p>
    </form>
  )
}
