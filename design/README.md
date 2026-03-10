# Design Assets — Study Architect

## Stitch Design Pipeline

Study Architect's frontend design is generated and iterated using [Google Stitch](https://stitch.withgoogle.com/) (AI UI design tool).

### Workflow

```
Stitch (cloud) ──export──→ design/stitch/ ──react-components skill──→ frontend/src/
       ↑                                                                    │
       └──── iterate via stitch-loop skill / edit_screens MCP ←────────────┘
```

### Current Assets

**v1-analytics-pro/** — Initial Ideate mode output (Analytics Pro direction only)
- `dashboard/` — Main dashboard with activity heatmap, subject progress, daily timer
- `active_focus_session/` — Focus timer with telemetry indicators
- `subject_detail/` — Per-subject analytics with velocity chart and efficiency scores
- `weekly_analytics/` — Weekly review with peak performance, focus degradation, allocation
- `analytics_pro_study_companion_prd.html` — Generated PRD document (rendered)

**v2-mixed/** — TO BE GENERATED: Mixed directions (Analytics Pro + Zen Study + Gamification)

### Design System

- **Theme**: Dark mode, "tactical cyberpunk telemetry"
- **Colors**: Deep black surfaces, neon cyan/chartreuse (#ccf20d) accents
- **Typography**: Space Grotesk (headings), monospace (data)
- **See**: `PRD.md` for full design system with CSS tokens

### Stitch Project

- **ID**: `10211254190976208744`
- **MCP**: `mcp__stitch__*` tools for programmatic access
- **Skills**: react-components, design-md, enhance-prompt, stitch-loop, remotion, shadcn-ui
