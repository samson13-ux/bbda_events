import { LegalPage } from '@/components/legal-page'

export const metadata = {
  title: "Conditions générales d'utilisation — BBDA Events",
  description: "Conditions générales d'utilisation de la plateforme BBDA Events.",
}

export default function CguPage() {
  return (
    <LegalPage
      title="Conditions générales d'utilisation"
      updated="Janvier 2026"
      current="/legal/cgu"
      sections={[
        {
          heading: '1. Objet',
          body: [
            "Les présentes conditions régissent l'utilisation de la plateforme BBDA Events, destinée à la déclaration et à la promotion des événements culturels au Burkina Faso.",
          ],
        },
        {
          heading: '2. Accès au service',
          body: [
            "L'accès aux fonctionnalités de déclaration nécessite la création d'un compte. L'utilisateur s'engage à fournir des informations exactes et à jour.",
          ],
        },
        {
          heading: '3. Obligations de l’utilisateur',
          body: [
            "L'utilisateur s'engage à respecter la législation en vigueur, notamment en matière de droits d'auteur, et à déclarer l'ensemble des œuvres exploitées lors de ses événements.",
            "Toute déclaration frauduleuse ou incomplète engage la responsabilité de l'organisateur.",
          ],
        },
        {
          heading: '4. Responsabilité',
          body: [
            "Le BBDA s'efforce d'assurer la disponibilité de la plateforme mais ne saurait être tenu responsable des interruptions temporaires liées à la maintenance ou à des causes externes.",
          ],
        },
        {
          heading: '5. Modification des conditions',
          body: [
            "Le BBDA se réserve le droit de modifier les présentes conditions. Les utilisateurs seront informés de toute évolution significative.",
          ],
        },
      ]}
    />
  )
}
