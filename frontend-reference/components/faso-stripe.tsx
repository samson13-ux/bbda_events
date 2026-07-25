/**
 * A thin woven "Faso Dan Fani" inspired accent bar using the
 * Burkina Faso national colours (green, gold, red).
 */
export function FasoStripe({ className }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={className}
      style={{
        height: 4,
        backgroundImage:
          'repeating-linear-gradient(90deg, var(--primary) 0 28px, var(--accent) 28px 40px, var(--destructive) 40px 52px, var(--accent) 52px 64px)',
      }}
    />
  )
}
