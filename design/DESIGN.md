# Design System: Study Architect
**v1 Project ID:** `10211254190976208744` (Mobile, Analytics Pro)
**v2 Project ID:** `12437812792880778825` (Desktop, Mixed Directions)

## 1. Visual Theme & Atmosphere

**Aesthetic:** Tactical cyberpunk telemetry — a mission-control interface built for serious academics who treat studying like elite performance training. The visual language draws from Bloomberg Terminal's data density, Strava's gamified tracking, and GitHub's contribution graphs.

**Mood:** Relentlessly precise, operationally focused, zero-decorative. Every pixel serves a data purpose. The near-black canvas creates a void that makes neon data points feel like readings on night-vision instrumentation. The interface radiates quiet intensity — not flashy, but deeply functional.

**Density:** High information density tempered by generous vertical breathing room between sections. Data blocks are tightly packed within cards but sections are generously spaced (24-32px gaps). Mobile (v1) uses maximum density with full-bleed components; desktop (v2) uses a 1440px max-width container with 48-96px horizontal padding.

**Key Design Decisions:**
- Dark mode is the native state — light mode exists as a token variable but the entire identity is built around deep black
- Decorative corner markers (v1 dashboard) reinforce the tactical instrument feel — small L-shaped border fragments at card corners
- Neon text-shadow glows on key metrics create depth without traditional shadows
- Animated pulse indicators (`animate-pulse`) on active states signal live data

## 2. Color Palette & Roles

### Core Palette (Both Versions)

| Name | Hex | Role |
|------|-----|------|
| **Neon Chartreuse** | `#D4FF00` | Primary actions, positive metrics, goals met, active progress, CTAs. The signature color — every screen anchors around it. |
| **Electric Cyan** | `#00F2FE` | Secondary data points, comparative metrics, progress tracking, "in-progress" state. Coolness balances the chartreuse warmth. |
| **Void Black** | `#050505` | Deepest background. Creates the infinite-depth canvas. |
| **Raised Black** | `#121212` (v1) / `#0a0a0a` (v2) | Card and container surfaces. Lifted just enough to register as distinct from the void. |
| **Active Black** | `#1E1E1E` (v1) / `#1f1f1f` (v2) | Hover states, borders, inactive tracks, chart backgrounds. The structural skeleton of the interface. |
| **High Ash** | `#E0E0E0` | Primary readable text. High contrast against the void without being pure white. |
| **Low Ash** | `#6B6B6B` (v1) / `#888888` (v2) | Micro-labels, axis labels, inactive elements, timestamps. Recedes to let data shine. |

### Extended Palette (v2 Desktop Additions)

| Name | Hex | Role |
|------|-----|------|
| **Signal Crimson** | `#FF0055` | v1 danger: overdue goals, broken streaks, destructive actions |
| **Hot Magenta** | `#FF2D7B` | v2 danger/tertiary: overdue items, mastery deficit, weak concepts. Slightly warmer than crimson. |
| **Vivid Magenta** | `#FF00FF` | Accent for critical alerts in subject detail (concept map weak nodes) |
| **Trophy Gold** | `#FFD700` | Achievement badges, earned rewards, gamification highlights |
| **Blaze Orange** | `#ff6b00` | Streak fire icon, urgency without danger |

### Neon Glow Recipes
```css
/* Chartreuse glow — primary data, timers, CTA buttons */
text-shadow: 0 0 8px rgba(212, 255, 0, 0.4);
box-shadow: 0 0 8px rgba(212, 255, 0, 0.4);

/* Cyan glow — secondary metrics, progress rings */
text-shadow: 0 0 8px rgba(0, 242, 254, 0.4);
box-shadow: 0 0 10px rgba(0, 242, 254, 0.3);

/* Magenta glow — alerts, weak areas */
text-shadow: 0 0 8px rgba(255, 45, 123, 0.4);

/* Gold glow — achievements */
filter: drop-shadow(0 0 8px rgba(255, 215, 0, 0.5));

/* Background orbs — subtle ambient depth on desktop cards */
background: radial-gradient(circle at top-right, rgba(color, 0.1), transparent);
/* Implemented as: absolute positioned div, w-24 h-24, blur-2xl, color/10 opacity */
```

## 3. Typography Rules

### Font Stack
| Role | Family | Character |
|------|--------|-----------|
| **Display** | Space Grotesk | Geometric sans with character. Used for headings, section titles, brand identity. Bold (700), uppercase, tight tracking. |
| **Body** | IBM Plex Sans (v1 mobile) / Inter (v2 desktop) | Clean readability. Regular (400) to Semi-Bold (600). Natural case. |
| **Data/Mono** | JetBrains Mono | The workhorse. All numbers, metrics, timers, tables, micro-labels. Communicates precision and technical authority. |

### Type Scale
| Usage | Family | Weight | Size | Tracking | Transform |
|-------|--------|--------|------|----------|-----------|
| Hero Metrics (timers) | JetBrains Mono | 500 | 48-80px | -0.05em | — |
| Large Data Points | JetBrains Mono | 700 | 24-40px | -0.05em | — |
| Section Headings | Space Grotesk | 700 | 18-24px | -0.02em to 0.1em | UPPERCASE |
| Card Headings | Space Grotesk | 700 | 14-18px | tight | UPPERCASE |
| Body Text | IBM Plex Sans / Inter | 400-500 | 14-16px | normal | — |
| Micro-Labels | JetBrains Mono | 700 | 10px | 0.1em | UPPERCASE |
| Axis Labels | JetBrains Mono | 400 | 10px | — | — |

### Type Character Notes
- Headings are **always uppercase** with Space Grotesk — this creates the military/tactical register
- All micro-labels (chart annotations, category labels, status indicators) use JetBrains Mono 10px uppercase with wide letter-spacing — the "instrument panel" voice
- Timer digits use negative tracking (-0.05em) for that dense, counter-like quality
- Body text (descriptions, insights) uses sentence case with IBM Plex Sans or Inter — the one place the interface breathes naturally

## 4. Component Stylings

### Buttons
- **Primary CTA (v1 mobile):** Full-width, 64px tall, sharp squared-off edges (0px radius). `#D4FF00` fill, `#050505` text. Space Grotesk bold uppercase. No shadow — the color IS the emphasis. Active state: `scale(0.98)` press effect.
- **Primary CTA (v2 desktop):** Rounded-full pill shape (9999px radius), `#4dffd2` or `#D4FF00` fill, dark text. Neon box-shadow glow on hover. More approachable than v1's militant squares.
- **Action Buttons (Engage/Review):** Ghost style — transparent background with color-matched border and text. `font-mono text-xs uppercase tracking-wider`. Background fills to `color/10` → `color/20` on hover. Sharp corners (v1) or subtle rounding (v2).
- **Icon Buttons:** 40px circles, transparent background, `hover:bg-white/5` subtle reveal.

### Cards & Containers
- **v1 (Mobile):** Zero border-radius. Defined entirely by `1px solid #1E1E1E` borders. Background `#121212`. Completely flat — no shadows whatsoever. Optional decorative corner markers (small L-shaped border fragments at each corner).
- **v2 (Desktop):** Subtly rounded corners (`rounded-xl` = 12px). Same 1px borders (`#1f1f1f`). Background `#0a0a0a`. Ambient background orbs: large blurred circles (`w-24 h-24 blur-2xl`) of the section's accent color at 10% opacity, positioned at top-right, overflow hidden.
- **Both:** Cards gain interactivity through `hover:border-color/50` transitions, never through elevation changes. The surface stays flat; color announces intent.

### Inputs & Forms
- **Search bars:** Rounded-lg with dark border, dark background, muted placeholder text. Inline icon left-aligned.
- **Segmented controls (tab switchers):** 1px bordered container, active tab filled with primary color + dark text. Inactive tabs are muted text only.

### Progress Bars
- **v1 (Mobile):** 2px tall, dead-flat, sharp-cornered. Track: `#1E1E1E`. Fill: color-matched (primary/secondary/danger based on state). Ultra-minimal.
- **v2 (Desktop):** 8px tall, rounded-full. Track: `#1f1f1f`. Fill: color-matched with neon glow on completed goals (`box-shadow: 0 0 10px-15px`). More visible and satisfying.

### Charts & Data Visualizations
- **Bar charts:** Sharp-cornered bars (v1) or subtle top rounding (v2). Background track in `#1E1E1E` shows target, colored bar overlays show actual. Hover reveals tooltips.
- **Line charts:** 1px SVG strokes in primary chartreuse. Gradient fill underneath fading to transparent. Crosshair on hover/scrub.
- **Donut/Ring charts:** 2px stroke weight (v1) or 15px stroke (v2). No fill. Center contains summary metric.
- **Heatmaps:** Grid of small squares using color opacity steps (20%, 40%, 60%, 80%, 100%) to encode intensity. Active day pulses.
- **Tooltips:** Dark surface background, 1px border, mono text. Positioned above the data point. Contains value in primary color.

### Tables (Telemetry Logs)
- Header row: Uppercase mono micro-labels, muted color, darker background.
- Data rows: Mono text, `hover:bg-surface-hover` highlight. Border between rows.
- Efficiency/delta values: Color-coded (primary = good, danger = bad, muted = neutral).

### Navigation
- **v1 (Mobile):** Fixed bottom nav bar with icon + mono micro-label. Active state: primary color + top indicator line (2px `#D4FF00` bar).
- **v2 (Desktop):** Top navigation bar with horizontal text links. Active state: bottom border in primary color. Optional pill-shaped streak counter with icon.
- **Breadcrumbs (v2):** Mono text, `/` separator, current page in primary color.

### Achievement Badges
- Circular icon containers (48px) with color-matched border and 20% opacity background fill.
- Gold glow effect on unlocked badges.
- Locked badges: `opacity-50 grayscale`, lock icon, muted text.

## 5. Layout Principles

### Whitespace Strategy
- **Macro spacing** (between sections): 24-32px gaps. Generous enough to prevent data overload.
- **Micro spacing** (within cards): 16px padding standard, 12-24px between elements.
- **Vertical rhythm:** Sections separated by thin horizontal borders (`1px solid #1E1E1E`) or explicit gaps, never by dramatic whitespace alone.

### Grid Systems
- **v1 Mobile (390px):** Single column, full-bleed. Cards span edge-to-edge with 16px page padding. Horizontal scroll for stat blocks (120px snap targets).
- **v2 Desktop (1280-1440px):** 12-column grid with responsive breakpoints. Common splits: 60/40 or 7/5 column ratio. 4-column metric cards at top. Max-width container centered.

### Sticky Elements
- Headers are always sticky (`sticky top-0 z-50`) with `backdrop-blur` and semi-transparent background (`bg-background-dark/95`).
- Mobile bottom nav is fixed (`fixed bottom-0`).
- Desktop CTA buttons scroll with content.

### Responsive Behavior
- v1 screens are mobile-native (390px viewport)
- v2 screens are desktop-native (1280px viewport)
- Both use the same design language — v2 simply has more horizontal space for side-by-side layouts and larger data visualizations

## 6. Animation & Motion

| Element | Animation | Duration | Easing |
|---------|-----------|----------|--------|
| Active recording dot | `animate-pulse` | Default (1.5s) | ease-in-out |
| Progress ring fill | `stroke-dashoffset` transition | 1000ms | ease-linear |
| Button press | `scale(0.98)` | instant | — |
| Chart line drawing | SVG `dash-offset` | 800ms | — |
| Card hover | `border-color` transition | 150ms | ease |
| Tooltip appear | `opacity 0→1` | 150ms | ease |
| Background orb | Static (no animation) | — | — |

**Motion philosophy:** Minimal and purposeful. Animations serve data (progress filling, recording indicator), never decoration. The interface should feel responsive but clinical — like instruments updating, not UI entertaining.

## 7. Design Tokens (Tailwind Config)

```javascript
// Canonical Tailwind configuration (v2 desktop, production target)
tailwind.config = {
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "primary": "#D4FF00",
        "secondary": "#00F2FE",
        "tertiary": "#FF2D7B",
        "accent": "#FF00FF",
        "gold": "#FFD700",
        "background-light": "#f8f8f5",
        "background-dark": "#050505",
        "surface": "#0a0a0a",
        "border-color": "#1f1f1f",
        "text-muted": "#888888"
      },
      fontFamily: {
        "display": ["Space Grotesk", "sans-serif"],
        "body": ["Inter", "sans-serif"],
        "mono": ["JetBrains Mono", "monospace"]
      },
      borderRadius: {
        "DEFAULT": "0.25rem",
        "lg": "0.5rem",
        "xl": "0.75rem",
        "full": "9999px"
      }
    }
  }
}
```

## 8. Stitch Prompting Guide

When generating new screens with Stitch, use this vocabulary to maintain consistency:

**Must include in every prompt:**
- "Dark mode, deep black (#050505) background"
- "Neon chartreuse (#D4FF00) primary accents"
- "Space Grotesk for headings, JetBrains Mono for data"
- "Cyberpunk telemetry aesthetic"
- "1px borders in #1f1f1f, no heavy shadows"

**Tone modifiers:**
- "Clinical precision" — for data-heavy screens
- "Tactical instrument" — for dashboard/control panels
- "Immersive focus" — for timer/session screens
- "Data-dense but breathable" — for analytics screens

**Avoid in prompts:**
- Rounded, playful, friendly, pastel, gradient-heavy, skeuomorphic
- Heavy drop shadows, card elevation, material design
- Bright white backgrounds, colorful illustrations
