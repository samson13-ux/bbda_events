import { SiteNav } from '@/components/site-nav'
import { SiteFooter } from '@/components/site-footer'
import { PageHeader } from '@/components/page-header'
import { EventsGrid } from '@/components/events-grid'

export const metadata = {
  title: 'Événements — BBDA Events',
  description:
    'Découvrez les concerts, festivals, galas et spectacles culturels déclarés et promus sur BBDA Events.',
}

export default function EvenementsPage() {
  return (
    <>
      <SiteNav />
      <main>
        <PageHeader
          eyebrow="Agenda culturel"
          title="Les événements du Faso"
          description="Concerts, festivals, galas, spectacles et expositions déclarés auprès du BBDA et promus auprès du public."
        />
        <section className="bg-background py-12 md:py-16">
          <div className="mx-auto max-w-6xl px-4 md:px-6">
            <EventsGrid />
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  )
}
