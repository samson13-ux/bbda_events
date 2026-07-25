import { LegalPage } from '@/components/legal-page'

export const metadata = {
  title: "Politique de l'organisateur — BBDA Events",
  description: "Engagements et obligations des organisateurs d'événements sur BBDA Events.",
}

export default function OrganisateurPage() {
  return (
    <LegalPage
      title="Politique de l'organisateur"
      updated="Janvier 2026"
      current="/legal/organisateur"
      sections={[
        {
          heading: '1. Déclaration préalable',
          body: [
            "Tout organisateur doit déclarer son événement auprès du BBDA avant sa tenue, en respectant les délais indiqués sur la plateforme.",
          ],
        },
        {
          heading: '2. Paiement des redevances',
          body: [
            "L'organisateur s'engage à s'acquitter des droits d'auteur dus au titre des œuvres exploitées, selon le barème en vigueur, et à conserver la quittance délivrée.",
          ],
        },
        {
          heading: '3. Programme artistique',
          body: [
            "L'organisateur fournit un programme artistique fidèle et complet. Toute modification substantielle doit être signalée au BBDA.",
          ],
        },
        {
          heading: '4. Promotion',
          body: [
            "En publiant son événement sur la page publique, l'organisateur autorise le BBDA à en assurer la promotion sur ses supports de communication.",
          ],
        },
        {
          heading: '5. Sanctions',
          body: [
            "Le non-respect de ces obligations peut entraîner la suspension du compte et l'engagement de poursuites conformément à la législation sur le droit d'auteur.",
          ],
        },
      ]}
    />
  )
}
