import Link from 'next/link'
import { Phone, MapPin, Mail } from 'lucide-react'
import { BrandLogo } from '@/components/brand-logo'
import { FasoStripe } from '@/components/faso-stripe'

export function SiteFooter() {
  return (
    <footer className="border-t border-border bg-secondary/40">
      <FasoStripe />
      <div className="mx-auto max-w-6xl px-4 py-12 md:px-6">
        <div className="grid gap-10 md:grid-cols-4">
          <div className="md:col-span-2">
            <BrandLogo />
            <p className="mt-4 max-w-sm text-sm leading-relaxed text-muted-foreground">
              Déclarez. Promouvez. Célébrez. La plateforme officielle du BBDA pour
              la gestion et la promotion des événements culturels au Burkina Faso.
            </p>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-foreground">Navigation</h3>
            <ul className="mt-4 space-y-2 text-sm text-muted-foreground">
              <li><Link href="/" className="hover:text-primary">Accueil</Link></li>
              <li><Link href="/evenements" className="hover:text-primary">Événements</Link></li>
              <li><Link href="/support" className="hover:text-primary">Support</Link></li>
              <li><Link href="/contact" className="hover:text-primary">Contact</Link></li>
            </ul>
            <h3 className="mt-6 text-sm font-semibold text-foreground">Légal</h3>
            <ul className="mt-4 space-y-2 text-sm text-muted-foreground">
              <li><Link href="/legal/confidentialite" className="hover:text-primary">Confidentialité</Link></li>
              <li><Link href="/legal/cgu" className="hover:text-primary">CGU</Link></li>
              <li><Link href="/legal/organisateur" className="hover:text-primary">Politique organisateur</Link></li>
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-foreground">Coordonnées BBDA</h3>
            <ul className="mt-4 space-y-3 text-sm text-muted-foreground">
              <li className="flex items-start gap-2">
                <MapPin className="mt-0.5 size-4 shrink-0 text-primary" />
                01 BP 3926 Ouagadougou 01, Burkina Faso
              </li>
              <li className="flex items-center gap-2">
                <Phone className="size-4 shrink-0 text-primary" />
                25 32 47 50
              </li>
              <li className="flex items-center gap-2">
                <Mail className="size-4 shrink-0 text-primary" />
                contact@bbda.bf
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-10 border-t border-border pt-6 text-center text-xs text-muted-foreground">
          Copyright &copy; 2026 BBDA Events. Tous droits réservés.
        </div>
      </div>
    </footer>
  )
}
