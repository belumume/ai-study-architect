/**
 * Sentry Error Tracking Configuration
 *
 * Initializes Sentry for production error monitoring and reporting.
 * Only activates in production environments when VITE_SENTRY_DSN is configured.
 */

import * as Sentry from '@sentry/react'

/**
 * Initialize Sentry error tracking
 *
 * Configuration:
 * - VITE_SENTRY_DSN: Sentry project DSN (required for activation)
 * - VITE_SENTRY_ENVIRONMENT: Environment name (defaults to 'production')
 * - VITE_SENTRY_TRACES_SAMPLE_RATE: Performance monitoring sample rate (0.0 to 1.0)
 *
 * Features:
 * - Automatic error capture and reporting
 * - Performance monitoring with traces
 * - User session replay (in production)
 * - React error boundary integration
 * - HTTP breadcrumbs for debugging
 */
export function initSentry() {
  // Only initialize in production or if explicitly configured
  const sentryDsn = import.meta.env.VITE_SENTRY_DSN

  if (!sentryDsn) {
    console.log('[Sentry] Not initialized - VITE_SENTRY_DSN not configured')
    return
  }

  // Don't initialize in development unless explicitly configured
  if (import.meta.env.DEV && !import.meta.env.VITE_SENTRY_FORCE_DEV) {
    console.log('[Sentry] Skipped in development mode')
    return
  }

  try {
    Sentry.init({
      dsn: sentryDsn,

      // Environment
      environment: import.meta.env.VITE_SENTRY_ENVIRONMENT || 'production',

      // Release tracking (useful for tracking which version has issues)
      release: import.meta.env.VITE_APP_VERSION || undefined,

      // Performance Monitoring
      integrations: [
        // Captures browser performance metrics
        Sentry.browserTracingIntegration(),

        // Session replay for debugging (captures user interactions)
        Sentry.replayIntegration({
          // Privacy settings
          maskAllText: true,
          blockAllMedia: true,
        }),
      ],

      // Session replay sample rates
      replaysSessionSampleRate: 0.1, // 10% of sessions
      replaysOnErrorSampleRate: 1.0, // 100% of error sessions

      // Performance Monitoring sample rate (0.0 to 1.0)
      // In production, we'll capture 10% of transactions for performance monitoring
      tracesSampleRate: parseFloat(
        import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE || '0.1'
      ),

      // Filter out errors that shouldn't be reported
      beforeSend(event, hint) {
        // Filter out browser extension errors
        if (event.exception?.values?.[0]?.stacktrace?.frames?.some(
          frame => frame.filename?.includes('extension://')
        )) {
          return null
        }

        // Filter out errors from ad blockers
        if (event.message?.includes('adsbygoogle')) {
          return null
        }

        // Log to console in development
        if (import.meta.env.DEV) {
          console.error('[Sentry] Capturing error:', hint.originalException || event)
        }

        return event
      },

      // Breadcrumbs configuration
      maxBreadcrumbs: 50,

      // Attach stack traces to pure capture message calls
      attachStacktrace: true,

      // Normalize depth for nested objects
      normalizeDepth: 10,
    })

    console.log('[Sentry] Initialized successfully')
  } catch (error) {
    console.error('[Sentry] Initialization failed:', error)
  }
}

/**
 * Configure Sentry user context
 * Call this after user authentication to associate errors with users
 */
export function setSentryUser(user: { id: string; email?: string; username?: string }) {
  if (!import.meta.env.VITE_SENTRY_DSN) return

  Sentry.setUser({
    id: user.id,
    email: user.email,
    username: user.username,
  })
}

/**
 * Clear Sentry user context
 * Call this on logout
 */
export function clearSentryUser() {
  if (!import.meta.env.VITE_SENTRY_DSN) return

  Sentry.setUser(null)
}

/**
 * Manually capture an exception
 * Useful for try/catch blocks where you want to report but not crash
 */
export function captureException(error: unknown, context?: Record<string, unknown>) {
  if (!import.meta.env.VITE_SENTRY_DSN) {
    console.error('[Sentry] Would capture:', error, context)
    return
  }

  if (context) {
    Sentry.withScope(scope => {
      Object.entries(context).forEach(([key, value]) => {
        scope.setExtra(key, value)
      })
      Sentry.captureException(error)
    })
  } else {
    Sentry.captureException(error)
  }
}

/**
 * Capture a message (not an error)
 * Useful for logging important events
 */
export function captureMessage(message: string, level: Sentry.SeverityLevel = 'info') {
  if (!import.meta.env.VITE_SENTRY_DSN) {
    console.log(`[Sentry] Would capture message (${level}):`, message)
    return
  }

  Sentry.captureMessage(message, level)
}
