import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/services/api'
import { useTimer } from '@/hooks/useTimer'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Loader2, Pause, Square, Play, ChevronLeft } from 'lucide-react'

interface Subject {
  id: string
  name: string
  color: string
}

function formatTime(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000)
  const h = Math.floor(totalSeconds / 3600)
  const m = Math.floor((totalSeconds % 3600) / 60)
  const s = totalSeconds % 60
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

export function FocusPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const queryClient = useQueryClient()
  const { elapsed, start, pause, stop } = useTimer()
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [selectedSubjectId, setSelectedSubjectId] = useState<string | null>(null)
  const [sessionStatus, setSessionStatus] = useState<'idle' | 'active' | 'paused' | 'stopped'>(
    'idle',
  )

  const { data: subjects } = useQuery<Subject[]>({
    queryKey: ['subjects'],
    queryFn: () => api.get('/api/v1/subjects/').then((r) => r.data),
  })

  // Check for resume parameter
  const resumeId = searchParams.get('resume')
  useEffect(() => {
    if (resumeId) {
      setSessionId(resumeId)
      setSessionStatus('active')
      start()
    }
  }, [resumeId, start])

  const startMutation = useMutation({
    mutationFn: (subjectId: string | null) =>
      api.post('/api/v1/sessions/start', {
        subject_id: subjectId,
        study_mode: 'practice',
      }),
    onSuccess: (response) => {
      setSessionId(response.data.id)
      setSessionStatus('active')
      start()
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })

  const pauseMutation = useMutation({
    mutationFn: () => api.patch(`/api/v1/sessions/${sessionId}/pause`),
    onSuccess: () => {
      pause()
      setSessionStatus('paused')
    },
    onError: () => {
      // Server rejected pause — timer keeps running
    },
  })

  const resumeMutation = useMutation({
    mutationFn: () => api.patch(`/api/v1/sessions/${sessionId}/resume`),
    onSuccess: () => {
      start(elapsed)
      setSessionStatus('active')
    },
  })

  const stopMutation = useMutation({
    mutationFn: () => api.patch(`/api/v1/sessions/${sessionId}/stop`),
    onSuccess: () => {
      stop()
      setSessionStatus('stopped')
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })

  // Save session on page unload
  useEffect(() => {
    if (!sessionId || sessionStatus !== 'active') return

    const handleUnload = () => {
      fetch(`/api/v1/sessions/${sessionId}/stop`, {
        method: 'PATCH',
        keepalive: true,
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
      })
    }

    window.addEventListener('beforeunload', handleUnload)
    return () => window.removeEventListener('beforeunload', handleUnload)
  }, [sessionId, sessionStatus])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === 'Space' && sessionStatus !== 'idle' && sessionStatus !== 'stopped') {
        e.preventDefault()
        if (sessionStatus === 'active') pauseMutation.mutate()
        else if (sessionStatus === 'paused') resumeMutation.mutate()
      }
      if (e.code === 'Escape' && (sessionStatus === 'active' || sessionStatus === 'paused')) {
        stopMutation.mutate()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [sessionStatus, pauseMutation, resumeMutation, stopMutation])

  const selectedSubject = subjects?.find((s) => s.id === selectedSubjectId)

  // Idle state — select subject and start
  if (sessionStatus === 'idle') {
    return (
      <div className="flex min-h-[calc(100vh-8rem)] flex-col items-center justify-center bg-zen-bg">
        <Card className="w-full max-w-md border-border bg-[#141414] p-8">
          <h1 className="text-center font-display text-xl font-bold uppercase tracking-wider text-zen-primary">
            Start Focus Session
          </h1>

          {subjects && subjects.length > 0 ? (
            <div className="mt-6 space-y-2">
              <p className="font-mono text-xs uppercase tracking-widest text-text-muted">
                Select Subject
              </p>
              {subjects.map((s) => (
                <button
                  key={s.id}
                  onClick={() => setSelectedSubjectId(s.id)}
                  className={`w-full rounded-lg border p-3 text-left transition-colors ${
                    selectedSubjectId === s.id
                      ? 'border-zen-primary bg-zen-primary/10'
                      : 'border-border hover:border-zen-primary/50'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <span className="h-3 w-3 rounded-full" style={{ backgroundColor: s.color }} />
                    <span className="font-body text-sm text-text-primary">{s.name}</span>
                  </span>
                </button>
              ))}
            </div>
          ) : (
            <p className="mt-4 text-center font-body text-sm text-text-muted">
              No subjects yet. You can start a general study session.
            </p>
          )}

          <Button
            onClick={() => startMutation.mutate(selectedSubjectId)}
            disabled={startMutation.isPending}
            className="mt-6 w-full bg-zen-primary text-void hover:bg-zen-primary/90"
          >
            {startMutation.isPending ? <Loader2 className="h-5 w-5 animate-spin" /> : 'Begin Focus'}
          </Button>
        </Card>
      </div>
    )
  }

  // Stopped state — show summary
  if (sessionStatus === 'stopped') {
    const totalMinutes = Math.floor(elapsed / 60000)
    return (
      <div className="flex min-h-[calc(100vh-8rem)] flex-col items-center justify-center bg-zen-bg">
        <Card className="w-full max-w-md border-border bg-[#141414] p-8 text-center">
          <h2 className="font-display text-xl font-bold uppercase tracking-wider text-zen-primary">
            Session Complete
          </h2>
          <p className="mt-4 font-mono text-5xl font-bold text-text-primary">
            {formatTime(elapsed)}
          </p>
          <p className="mt-2 font-mono text-sm text-text-muted">
            {totalMinutes < 1
              ? 'Session cancelled (< 1 min)'
              : `${totalMinutes} minutes of focused study`}
          </p>
          <Button
            onClick={() => navigate('/')}
            className="mt-6 w-full bg-zen-primary text-void hover:bg-zen-primary/90"
          >
            Return to Dashboard
          </Button>
        </Card>
      </div>
    )
  }

  // Active / Paused state — timer
  return (
    <div className="flex min-h-[calc(100vh-8rem)] flex-col items-center justify-center bg-zen-bg">
      {/* Back button */}
      <button
        onClick={() => navigate('/')}
        className="absolute left-6 top-20 flex items-center gap-1 text-text-muted hover:text-text-primary"
      >
        <ChevronLeft className="h-4 w-4" />
        <span className="font-body text-sm">Dashboard</span>
      </button>

      {/* Subject label */}
      {selectedSubject && (
        <p className="mb-4 font-mono text-xs uppercase tracking-widest text-zen-primary">
          TARGET: {selectedSubject.name}
        </p>
      )}

      {/* Timer */}
      <div className="relative">
        {/* Velocity ring */}
        <svg width="280" height="280" className="pointer-events-none absolute -left-10 -top-10">
          <circle cx="140" cy="140" r="130" fill="none" stroke="#1f1f1f" strokeWidth="2" />
          <circle
            cx="140"
            cy="140"
            r="130"
            fill="none"
            stroke={sessionStatus === 'paused' ? '#888888' : '#4dffd2'}
            strokeWidth="2"
            strokeDasharray={`${2 * Math.PI * 130}`}
            strokeDashoffset={`${2 * Math.PI * 130 * (1 - Math.min(1, elapsed / (60 * 60 * 1000)))}`}
            strokeLinecap="round"
            className="transition-all duration-1000"
            style={{ transform: 'rotate(-90deg)', transformOrigin: '50% 50%' }}
          />
        </svg>

        <p
          className={`relative z-10 font-mono text-7xl font-bold ${
            sessionStatus === 'paused' ? 'text-text-muted' : 'text-text-primary'
          }`}
        >
          {formatTime(elapsed)}
        </p>
      </div>

      {/* Controls */}
      <div className="mt-12 flex gap-4">
        {sessionStatus === 'active' ? (
          <Button
            onClick={() => pauseMutation.mutate()}
            disabled={pauseMutation.isPending}
            variant="outline"
            className="border-border px-8 py-6 text-text-primary hover:bg-raised"
            aria-label="Pause session (Space)"
          >
            <Pause className="mr-2 h-5 w-5" />
            Pause
          </Button>
        ) : (
          <Button
            onClick={() => resumeMutation.mutate()}
            disabled={resumeMutation.isPending}
            className="bg-zen-primary px-8 py-6 text-void hover:bg-zen-primary/90"
            aria-label="Resume session (Space)"
          >
            <Play className="mr-2 h-5 w-5" />
            Resume
          </Button>
        )}

        <Button
          onClick={() => stopMutation.mutate()}
          disabled={stopMutation.isPending}
          variant="outline"
          className="border-tertiary/50 px-8 py-6 text-tertiary hover:bg-tertiary/10"
          aria-label="Stop session (Escape)"
        >
          <Square className="mr-2 h-5 w-5" />
          Stop
        </Button>
      </div>

      {/* Keyboard hints */}
      <p className="mt-6 font-mono text-[10px] uppercase tracking-widest text-text-muted">
        Space = pause/resume | Escape = stop
      </p>
    </div>
  )
}
