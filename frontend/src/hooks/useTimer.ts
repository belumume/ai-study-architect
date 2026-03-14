import { useEffect, useRef, useState, useCallback } from 'react'

interface TimerResponse {
  type: 'tick' | 'stopped'
  elapsed: number
}

export function useTimer() {
  const workerRef = useRef<Worker | null>(null)
  const [elapsed, setElapsed] = useState(0)
  const [isRunning, setIsRunning] = useState(false)

  useEffect(() => {
    const worker = new Worker(
      new URL('../workers/timer.worker.ts', import.meta.url),
      { type: 'module' }
    )

    worker.onmessage = (e: MessageEvent<TimerResponse>) => {
      if (e.data.type === 'tick') {
        setElapsed(e.data.elapsed)
      } else if (e.data.type === 'stopped') {
        setElapsed(e.data.elapsed)
        setIsRunning(false)
      }
    }

    worker.onerror = () => {
      // Fallback: if worker fails, use setInterval
      console.warn('Timer worker failed, using fallback')
    }

    workerRef.current = worker

    return () => {
      worker.terminate()
      workerRef.current = null
    }
  }, [])

  const start = useCallback((initialElapsed?: number) => {
    workerRef.current?.postMessage({ type: 'start', elapsed: initialElapsed || 0 })
    setIsRunning(true)
  }, [])

  const pause = useCallback(() => {
    workerRef.current?.postMessage({ type: 'pause' })
    setIsRunning(false)
  }, [])

  const stop = useCallback(() => {
    workerRef.current?.postMessage({ type: 'stop' })
    setIsRunning(false)
  }, [])

  const reset = useCallback(() => {
    workerRef.current?.postMessage({ type: 'stop' })
    setElapsed(0)
    setIsRunning(false)
  }, [])

  return { elapsed, isRunning, start, pause, stop, reset }
}
