import { cn } from '@/lib/utils'

export function BrandLogo({ className }: { className?: string }) {
  return (
    <div className={cn('flex items-center gap-2.5', className)}>
      <div className="flex size-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
        {/* Stylised kora / star mark */}
        <svg
          viewBox="0 0 24 24"
          className="size-5"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M12 2 14.5 9H22l-6 4.5L18.5 22 12 17l-6.5 5L8 13.5 2 9h7.5L12 2Z" />
        </svg>
      </div>
      <div className="leading-tight">
        <span className="block font-serif text-lg font-bold tracking-tight text-foreground">
          BBDA <span className="text-primary">Events</span>
        </span>
        <span className="block text-[10px] font-medium uppercase tracking-[0.15em] text-muted-foreground">
          Bureau Burkinabè du Droit d&apos;Auteur
        </span>
      </div>
    </div>
  )
}
