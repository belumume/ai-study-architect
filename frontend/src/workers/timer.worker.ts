interface TimerMessage {
  type: 'start' | 'pause' | 'stop'
  elapsed?: number
}

interface TimerResponse {
  type: 'tick' | 'stopped'
  elapsed: number
}

let startTime: number | null = null
let isRunning = false

function tick() {
  if (!isRunning || startTime === null) return

  const elapsed = Date.now() - startTime
  const response: TimerResponse = { type: 'tick', elapsed }
  self.postMessage(response)

  setTimeout(tick, 1000)
}

self.onmessage = (e: MessageEvent<TimerMessage>) => {
  switch (e.data.type) {
    case 'start':
      startTime = Date.now() - (e.data.elapsed || 0)
      isRunning = true
      tick()
      break
    case 'pause':
      isRunning = false
      break
    case 'stop':
      isRunning = false
      if (startTime !== null) {
        const elapsed = Date.now() - startTime
        self.postMessage({ type: 'stopped', elapsed } satisfies TimerResponse)
      }
      startTime = null
      break
  }
}
