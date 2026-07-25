export function PageHeader({
  eyebrow,
  title,
  description,
}: {
  eyebrow?: string
  title: string
  description?: string
}) {
  return (
    <section className="border-b border-border bg-primary">
      <div className="mx-auto max-w-6xl px-4 py-14 md:px-6 md:py-16">
        {eyebrow && (
          <p className="mb-3 text-sm font-semibold uppercase tracking-wide text-accent">
            {eyebrow}
          </p>
        )}
        <h1 className="text-balance font-serif text-3xl font-bold tracking-tight text-primary-foreground md:text-5xl">
          {title}
        </h1>
        {description && (
          <p className="mt-4 max-w-2xl text-pretty leading-relaxed text-primary-foreground/80">
            {description}
          </p>
        )}
      </div>
    </section>
  )
}
