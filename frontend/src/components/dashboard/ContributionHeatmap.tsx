import { useMemo } from 'react'

interface HeatmapDay {
  readonly date: string
  readonly minutes: number
}

interface ContributionHeatmapProps {
  readonly data: HeatmapDay[]
}

const CELL_SIZE = 16
const GAP = 3
const ROWS = 7
const COLS = 4

function getCellColor(minutes: number): string {
  if (minutes === 0) return '#121212'
  if (minutes < 30) return '#1a4d4f'
  if (minutes < 60) return '#00a9b5'
  if (minutes < 120) return '#00d9e8'
  return '#00F2FE'
}

function getCellOpacity(minutes: number): number {
  if (minutes === 0) return 0.15
  if (minutes < 30) return 0.4
  if (minutes < 60) return 0.7
  return 1.0
}

const DAY_LABELS = ['Mon', '', 'Wed', '', 'Fri', '', 'Sun']

export function ContributionHeatmap({ data }: ContributionHeatmapProps) {
  const grid = useMemo(() => {
    const cells: { x: number; y: number; minutes: number; date: string }[] = []

    data.forEach((day, i) => {
      const col = Math.floor(i / ROWS)
      const row = i % ROWS
      cells.push({
        x: col * (CELL_SIZE + GAP) + 40,
        y: row * (CELL_SIZE + GAP),
        minutes: day.minutes,
        date: day.date,
      })
    })

    return cells
  }, [data])

  const width = COLS * (CELL_SIZE + GAP) + 50
  const height = ROWS * (CELL_SIZE + GAP)

  return (
    <div className="space-y-2">
      <h2 className="font-display text-sm font-bold uppercase tracking-wider">
        28-Day Activity
      </h2>
      <svg width={width} height={height} className="overflow-visible">
        <defs>
          <filter id="heatmap-glow">
            <feGaussianBlur stdDeviation="1.5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Day labels */}
        {DAY_LABELS.map((label, i) => (
          label && (
            <text
              key={i}
              x={30}
              y={i * (CELL_SIZE + GAP) + CELL_SIZE / 2 + 4}
              textAnchor="end"
              className="fill-text-muted font-mono text-[9px]"
            >
              {label}
            </text>
          )
        ))}

        {/* Cells */}
        {grid.map((cell) => (
          <rect
            key={cell.date}
            x={cell.x}
            y={cell.y}
            width={CELL_SIZE}
            height={CELL_SIZE}
            rx={2}
            fill={getCellColor(cell.minutes)}
            fillOpacity={getCellOpacity(cell.minutes)}
            filter={cell.minutes >= 60 ? 'url(#heatmap-glow)' : undefined}
          >
            <title>{`${cell.date}: ${cell.minutes} min`}</title>
          </rect>
        ))}
      </svg>
    </div>
  )
}
