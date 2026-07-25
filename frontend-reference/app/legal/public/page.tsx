import { LegalPage } from '@/components/legal-page'

export const metadata = {
  title: 'Politique du public — BBDA Events',
  description: 'Conditions applicables au public utilisant la plateforme BBDA Events.',
}

export default function PublicPage() {
  return (
    <LegalPage
      title="Politique du public"
      updated="Janvier 2026"
      current="/legal/public"
      sections={[
        {
          heading: '1. Consultation des événements',
          body: [
            "Le public peut consulter librement les événements culturels publiés sur BBDA Events, sans obligation de création de compte.",
          ],
        },
        {
          heading: '2. Exactitude des informations',
          body: [
            "Les informations relatives aux événements (dates, lieux, tarifs) sont fournies par les organisateurs. Le BBDA invite le public à les vérifier auprès des organisateurs avant tout déplacement.",
          ],
        },
        {
          heading: '3. Achat de billets',
          body: [
            "Lorsque disponible, l'achat de billets s'effectue selon les modalités définies par chaque organisateur. Le BBDA n'est pas partie aux transactions entre le public et les organisateurs.",
          ],
        },
        {
          heading: '4. Comportement',
          body: [
            "Le public s'engage à un usage respectueux de la plateforme et à ne pas diffuser de contenus illicites ou portant atteinte aux droits d'autrui.",
          ],
        },
        {
          heading: '5. Protection des données',
          body: [
            "Les données éventuellement collectées auprès du public sont traitées conformément à la politique de confidentialité du BBDA.",
          ],
        },
      ]}
    />
  )
}
