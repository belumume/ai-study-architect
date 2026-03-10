# Analytics Pro Study Companion

## Product Overview

**The Pitch:** A hyper-analytical study tracker that transforms academic effort into hard data. It enforces accountability through deep telemetry, distraction blocking, and precise time tracking visualized in high-contrast neon telemetry.

**For:** Medical students, law students, and competitive academics who treat studying like elite athletic training and demand granular data on their performance.

**Device:** mobile

**Design Direction:** Tactical cyberpunk telemetry. Deep black surfaces, razor-sharp edges, high-contrast neon data points, and terminal-grade typographic precision. Zero fluff, maximum data density.

**Inspired by:** Bloomberg Terminal, Strava, GitHub commit graphs.

---

## Screens

- **Dashboard:** High-level mission control showing daily focus limits, active streaks, and current weekly heatmap.
- **Active Focus Session:** Distraction-free timer interface with live physiological-style data streams (time elapsed, current session velocity).
- **Subject Detail:** Granular breakdown of a single subject comparing time invested against target goals via bar charts and scatter plots.
- **Weekly Analytics:** Deep-dive historical view with contribution graphs, day-of-week efficiency ratings, and focus degradation charts.

---

## Key Flows

**Initiate Deep Work:** Start a tracked, distraction-free study block.

1. User is on **Dashboard** -> sees pulsing `START SESSION` action block.
2. User taps `START SESSION` -> navigates to **Active Focus Session**.
3. Timer initiates instantly, screen locks into deep black state, system begins logging seconds in mono-font.

**Audit Subject Performance:** Review if sufficient time is being allocated to a weak subject.

1. User is on **Dashboard** -> taps 'Neuroanatomy' from the subject list.
2. User views **Subject Detail** -> sees target vs. actual time bar graph in stark chartreuse and muted gray.
3. User identifies a 4-hour deficit and recalibrates weekly schedule.

---

<details>
<summary>Design System</summary>

## Color Palette

- **Primary:** `#D4FF00` (Neon Chartreuse) - Primary actions, active states, key data highlights
- **Secondary:** `#00F2FE` (Cyan) - Secondary data points, comparative metrics
- **Background:** `#050505` (Void Black) - Deepest background
- **Surface:** `#121212` (Raised Black) - Base for cards and containers
- **Surface Highlight:** `#1E1E1E` (Active Black) - Hover states, pressed states
- **Text:** `#E0E0E0` (High Ash) - Primary reading text
- **Muted:** `#6B6B6B` (Low Ash) - Labels, inactive tracks, axes lines
- **Accent:** `#FF0055` (Crimson) - Overdue goals, broken streaks, destructive actions

## Typography

- **Headings:** `Space Grotesk`, 700, 24-32px, tracking -0.02em
- **Body:** `IBM Plex Sans`, 400, 16px, leading 1.5
- **Data/Numbers:** `JetBrains Mono`, 500, 14px-48px (scalable for timers), tracking -0.05em
- **Micro-labels:** `JetBrains Mono`, 700, 10px, uppercase, tracking 0.1em

**Style notes:** Razor-sharp corners (`0px` border radius). 1px solid borders in `#1E1E1E` define sections instead of shadows. Data elements glow slightly via CSS text-shadow (`0 0 8px rgba(212, 255, 0, 0.4)` on primary chartreuse).

## Design Tokens

```css
:root {
  --color-primary: #D4FF00;
  --color-secondary: #00F2FE;
  --color-background: #050505;
  --color-surface: #121212;
  --color-surface-hover: #1E1E1E;
  --color-text: #E0E0E0;
  --color-muted: #6B6B6B;
  --color-danger: #FF0055;
  
  --font-heading: 'Space Grotesk', sans-serif;
  --font-body: 'IBM Plex Sans', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  
  --radius: 0px;
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  
  --border-thin: 1px solid #1E1E1E;
}
```

</details>

---

<details>
<summary>Screen Specifications</summary>

### Dashboard

**Purpose:** Daily mission control and real-time status check.

**Layout:** Vertical scroll. Sticky top nav, hero metric (today's time), horizontal streak heatmap, vertical subject list.

**Key Elements:**
- **Today's Telemetry:** Large `JetBrains Mono` readout `04:22:15` in `#D4FF00`. Sublabel `DAILY TOTAL` in uppercase mono.
- **Contribution Matrix:** 7x4 grid of 8px squares (GitHub style). Colors range from `#121212` (0h) to bright `#00F2FE` (4h+).
- **Subject Ticker:** Vertical list of active subjects. Left-aligned subject name, right-aligned mono progress fraction `(3.5/5.0h)`. Progress bar underneath, 2px tall.

**States:**
- **Empty:** Matrix squares all `#121212`. Telemetry reads `00:00:00`.
- **Loading:** Matrix pulses sequentially in `#1E1E1E`.

**Components:**
- **Start Button:** Full width, fixed at bottom. `64px` tall, `#D4FF00` background, `#050505` text, bold `Space Grotesk`, reads `INITIATE FOCUS`.

**Interactions:**
- **Tap Subject:** Slides to Subject Detail.
- **Tap Start:** Ripples from center, expands to fill screen with deep black for Active Session.

### Active Focus Session

**Purpose:** Pure, unadulterated time tracking with zero distractions.

**Layout:** Centered monolithic timer. Minimal UI. No back button (requires swipe to exit to prevent accidental touches).

**Key Elements:**
- **Main Chronometer:** Massive `72px` `JetBrains Mono` timer dominating center screen. Pure white text.
- **Velocity Ring:** 1px circular SVG stroke wrapping the timer. Slowly fills `#D4FF00` over a 60-minute Pomodoro cycle.
- **Current Subject:** Micro-label above timer, `#00F2FE`, e.g., `TARGET: PHARMACOLOGY`.
- **Abort/Pause Track:** Slide-to-pause mechanism at bottom. `56px` track, `#121212` background.

**States:**
- **Paused:** Timer text turns `#6B6B6B`. Flashing `#FF0055` dot indicates break.
- **Overtime:** Timer text shifts to `#00F2FE` when exceeding planned session duration.

**Components:**
- **Slide-to-pause:** Chevron icon. User must drag right to pause, preventing accidental screen taps from breaking focus.

**Interactions:**
- **Slide complete:** Triggers haptic feedback, slides up summary modal.

### Subject Detail

**Purpose:** Granular analysis of specific subject performance and goal tracking.

**Layout:** Back button top left. Subject title. Macro stats row. Bar chart. Recent sessions list.

**Key Elements:**
- **Header:** `Space Grotesk` `32px`, e.g., `ORGANIC CHEMISTRY`.
- **Deficit/Surplus Indicator:** Mono text showing `+02:15:00` (green) or `-01:30:00` (red) against weekly goal.
- **7-Day Velocity Chart:** SVG bar chart. `24px` wide bars. Sharp corners. `#00F2FE` bars for actuals, `#1E1E1E` background tracks for target goals.
- **Session Log:** Table-style list. Columns: Date (mono), Duration (mono), Efficiency Score (percentage).

**States:**
- **Empty:** Bar chart shows flat lines. Log says `NO TELEMETRY RECORDED`.

**Components:**
- **Stat Block:** `120px` square cards. `1px solid #1E1E1E`. Top left micro-label, center massive mono value.

**Interactions:**
- **Tap Bar in Chart:** Shows tooltip with exact date and minute count.

### Weekly Analytics

**Purpose:** High-level performance review and pattern recognition.

**Layout:** Segmented control at top (WEEK | MONTH). Stacked graph cards.

**Key Elements:**
- **Focus Degradation Graph:** Line chart showing efficiency over the course of the day. X-axis: 00:00 to 24:00. Y-axis: Focus score. Line is 1px `#D4FF00`.
- **Subject Allocation:** Donut chart, `2px` stroke, showing distribution of study time across subjects in alternating `#D4FF00`, `#00F2FE`, and `#FFFFFF`.
- **Peak Performance Time:** Callout block identifying best study hour, e.g., `OPTIMAL: 06:00 - 09:00`.

**States:**
- **Loading:** Graphs draw themselves left-to-right using SVG dash-offset animation (800ms).

**Components:**
- **Chart Container:** `100%` width, `240px` height. `16px` padding.

**Interactions:**
- **Scrub Graph:** Press and hold on line chart creates a vertical crosshair and tooltip showing precise data point.

</details>

---

<details>
<summary>Build Guide</summary>

**Stack:** HTML + Tailwind CSS v3

**Build Order:**
1. **Dashboard** - Establishes the deep black canvas, grid systems, and core typography hierarchy (Space Grotesk + JetBrains Mono). Sets up the atomic design tokens in Tailwind config.
2. **Active Focus Session** - Prioritizes the most complex interactive element (the timer) and the critical path for the user. Forces the establishment of the absolute minimalist state.
3. **Subject Detail** - Introduces chart components, complex layouts, and data tables.
4. **Weekly Analytics** - Reuses chart components from Subject Detail, expanding on the data visualization library.

</details>