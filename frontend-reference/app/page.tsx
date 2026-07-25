import { SiteNav } from '@/components/site-nav'
import { SiteFooter } from '@/components/site-footer'
import { Hero } from '@/components/home/hero'
import { HowItWorks } from '@/components/home/how-it-works'
import { Solutions } from '@/components/home/solutions'
import { EventsPreview } from '@/components/home/events-preview'
import { AboutBbda } from '@/components/home/about-bbda'

export default function Page() {
  return (
    <>
      <SiteNav />
      <main>
        <Hero />
        <HowItWorks />
        <Solutions />
        <EventsPreview />
        <AboutBbda />
      </main>
      <SiteFooter />
    </>
  )
}
