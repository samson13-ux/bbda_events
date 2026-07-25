'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Eye, EyeOff } from 'lucide-react'
import { Button } from '@/components/ui/button'

type Errors = Record<string, string>

const inputClass =
  'w-full rounded-md border border-input bg-card px-3 py-2.5 text-sm text-foreground shadow-sm outline-none transition-colors placeholder:text-muted-foreground/70 focus:border-primary focus:ring-2 focus:ring-primary/20'

export function LoginForm() {
  const [showPassword, setShowPassword] = useState(false)
  const [errors, setErrors] = useState<Errors>({})

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const data = new FormData(e.currentTarget)
    const next: Errors = {}
    const email = (data.get('email') as string)?.trim()
    const password = (data.get('password') as string) ?? ''

    if (!email) next.email = "L'email est requis."
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) next.email = 'Email invalide.'
    if (!password) next.password = 'Le mot de passe est requis.'

    setErrors(next)
    // Le traitement (connexion réelle) sera géré par votre backend.
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="rounded-2xl border border-border bg-card p-6 md:p-8">
      <div>
        <label htmlFor="email" className="mb-1.5 block text-sm font-medium text-foreground">
          Email<span className="ml-0.5 text-destructive">*</span>
        </label>
        <input
          id="email"
          name="email"
          type="email"
          className={inputClass}
          placeholder="vous@exemple.bf"
        />
        {errors.email && <p className="mt-1 text-xs text-destructive">{errors.email}</p>}
      </div>

      <div className="mt-5">
        <div className="mb-1.5 flex items-center justify-between">
          <label htmlFor="password" className="block text-sm font-medium text-foreground">
            Mot de passe<span className="ml-0.5 text-destructive">*</span>
          </label>
          <Link href="/mot-de-passe-oublie" className="text-xs font-medium text-primary hover:underline">
            Mot de passe oublié ?
          </Link>
        </div>
        <div className="relative">
          <input
            id="password"
            name="password"
            type={showPassword ? 'text' : 'password'}
            className={inputClass}
            placeholder="Votre mot de passe"
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
        {errors.password && <p className="mt-1 text-xs text-destructive">{errors.password}</p>}
      </div>

      <label className="mt-5 flex items-center gap-2.5 text-sm text-muted-foreground">
        <input type="checkbox" name="remember" className="size-4 accent-[var(--primary)]" />
        Rester connecté
      </label>

      <Button type="submit" size="lg" className="mt-6 w-full">
        Se connecter
      </Button>

      <p className="mt-4 text-center text-sm text-muted-foreground">
        Pas encore de compte ?{' '}
        <Link href="/inscription" className="font-medium text-primary hover:underline">
          Créer un compte
        </Link>
      </p>
    </form>
  )
}
