import { LegalPage } from '@/components/legal-page'

export const metadata = {
  title: 'Politique de confidentialité — BBDA Events',
  description: 'Comment le BBDA collecte et protège vos données personnelles.',
}

export default function ConfidentialitePage() {
  return (
    <LegalPage
      title="Politique de confidentialité"
      updated="Janvier 2026"
      current="/legal/confidentialite"
      sections={[
        {
          heading: '1. Collecte des données',
          body: [
            "BBDA Events collecte les données que vous fournissez lors de la création de votre compte (nom, prénom, qualité, téléphone, email) ainsi que les informations relatives aux événements que vous déclarez.",
            'Ces données sont strictement nécessaires au traitement de vos déclarations et à la gestion des droits d’auteur.',
          ],
        },
        {
          heading: '2. Utilisation des données',
          body: [
            "Vos données sont utilisées pour instruire vos dossiers, générer vos quittances, assurer la promotion de vos événements et vous contacter en cas de besoin.",
            'Elles ne sont ni vendues ni cédées à des tiers à des fins commerciales.',
          ],
        },
        {
          heading: '3. Conservation',
          body: [
            "Les données sont conservées pendant la durée nécessaire à la gestion de vos droits et au respect des obligations légales du BBDA.",
          ],
        },
        {
          heading: '4. Vos droits',
          body: [
            "Vous disposez d'un droit d'accès, de rectification et de suppression de vos données. Pour l'exercer, contactez le BBDA via la page Contact.",
          ],
        },
        {
          heading: '5. Sécurité',
          body: [
            "Le BBDA met en œuvre des mesures techniques et organisationnelles pour protéger vos données contre tout accès non autorisé.",
          ],
        },
      ]}
    />
  )
}
