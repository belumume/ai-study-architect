import { cn } from '@/lib/utils'

type BrandMarkProps = Readonly<{
  /** Tailwind sizing classes. Defaults to h-7 w-7. */
  className?: string
}>

/**
 * Study Architect mark: a bold A (Architect) crossed by the acid-lime mastery bar.
 * Decorative by default — pair it with the wordmark, which carries the accessible name.
 */
export function BrandMark({ className }: BrandMarkProps) {
  return (
    <svg
      viewBox="11 10 78 79"
      className={cn('h-7 w-7', className)}
      aria-hidden="true"
      focusable="false"
    >
      <path
        className="fill-text-primary"
        fillRule="evenodd"
        d="M12 87 L45 12 L55 12 L88 87 Z M50 30 L42 54 L58 54 Z M42 60 L58 60 L76 87 L24 87 Z"
      />
      <path className="fill-primary" d="M26.52 54 L73.48 54 L76.12 60 L23.88 60 Z" />
    </svg>
  )
}
