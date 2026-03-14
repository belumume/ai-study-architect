import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Play, RotateCcw } from 'lucide-react'

interface StartFocusCTAProps {
  readonly hasActiveSession: boolean
  readonly activeSessionId?: string
}

export function StartFocusCTA({ hasActiveSession, activeSessionId }: StartFocusCTAProps) {
  return (
    <div className="mt-6">
      <Button
        asChild
        className="w-full rounded-full bg-primary py-6 text-lg font-bold uppercase tracking-wider text-void shadow-[0_0_15px_rgba(212,255,0,0.3)] transition-shadow hover:bg-primary/90 hover:shadow-[0_0_25px_rgba(212,255,0,0.5)]"
      >
        <Link to={hasActiveSession && activeSessionId ? `/focus?resume=${activeSessionId}` : '/focus'}>
          {hasActiveSession ? (
            <>
              <RotateCcw className="mr-2 h-5 w-5" />
              Resume Session
            </>
          ) : (
            <>
              <Play className="mr-2 h-5 w-5" />
              Initiate Focus
            </>
          )}
        </Link>
      </Button>
    </div>
  )
}
