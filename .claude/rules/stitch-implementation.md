---
paths: ["frontend/src/**"]
---
# Stitch to React Implementation Workflow

When implementing UI components from Stitch v3 designs:

1. Reference Stitch screenshot at `design/stitch/v3-evolved/{screen}/screen.png`
2. Reference Stitch HTML at `design/stitch/v3-evolved/{screen}/code.html` for Tailwind class patterns
3. Create modular React + TypeScript component with `Readonly<Props>` interface
4. Use design tokens from `@theme` in `src/index.css` — never hardcode hex colors
5. Use `cn()` from `@/lib/utils` for conditional class merging
6. Separate data to API hooks (TanStack Query) or Zustand stores — no inline fetch calls
7. Run `npm run typecheck && npm test` after each component
8. Compare implementation screenshot to Stitch reference — iterate if visual difference >5%

## Typography Rules
- Headings: `font-display text-[size] font-bold uppercase tracking-wider`
- Data/numbers: `font-mono text-[size]`
- Body text: `font-body text-[size]`
- Micro-labels: `font-mono text-[10px] uppercase tracking-widest text-text-muted`

## Neon Glow
- Primary glow: `glow-primary` class (or `text-shadow: 0 0 8px rgba(212, 255, 0, 0.4)`)
- Secondary glow: `glow-secondary` class
- Apply to key metrics and active elements only — not everything
