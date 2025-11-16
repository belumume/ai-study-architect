/**
 * Utility functions for consistent error handling and user-friendly error messages
 */

/**
 * Sanitize error messages to prevent sensitive information leakage
 */
function sanitizeErrorMessage(message: string): string {
  if (!message) return message

  // Redact potential API keys (patterns like sk-xxx, api_xxx, key_xxx)
  let sanitized = message.replace(/\b(sk|api|key)[-_][a-zA-Z0-9]{10,}\b/gi, '[REDACTED_KEY]')

  // Redact potential file paths
  sanitized = sanitized.replace(/([A-Z]:\\|\/)[^\s)]+/g, '[REDACTED_PATH]')

  // Redact potential URLs with credentials
  sanitized = sanitized.replace(/https?:\/\/[^:]+:[^@]+@[^\s]+/g, '[REDACTED_URL]')

  // Redact email addresses
  sanitized = sanitized.replace(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g, '[REDACTED_EMAIL]')

  return sanitized
}

export interface ApiError {
  response?: {
    status?: number
    data?: {
      detail?: string | any[] | { msg: string }
      error?: string
      message?: string
    }
  }
  message?: string
  code?: string
}

/**
 * Convert an API error to a user-friendly message
 *
 * @param error - The error object from API call
 * @param fallbackMessage - Default message if error cannot be parsed
 * @returns User-friendly error message
 */
export function getErrorMessage(error: unknown, fallbackMessage = 'An unexpected error occurred'): string {
  if (!error) return fallbackMessage

  const apiError = error as ApiError

  // Check for network errors
  if (apiError.code === 'ECONNABORTED' || apiError.message?.includes('timeout')) {
    return 'Request timed out. Please check your connection and try again.'
  }

  if (apiError.message?.includes('Network Error')) {
    return 'Network error. Please check your internet connection.'
  }

  // HTTP status-based messages
  const status = apiError.response?.status

  if (status === 401) {
    return 'Your session has expired. Please log in again.'
  }

  if (status === 403) {
    return 'You do not have permission to perform this action.'
  }

  if (status === 404) {
    return 'The requested resource was not found.'
  }

  if (status === 409) {
    return 'This item already exists.'
  }

  if (status === 429) {
    return 'Too many requests. Please wait a moment and try again.'
  }

  if (status && status >= 500) {
    return 'Server error. Please try again later.'
  }

  // Parse response data
  const data = apiError.response?.data

  if (data?.detail) {
    // Handle array of validation errors
    if (Array.isArray(data.detail)) {
      const MAX_ERRORS_TO_SHOW = 5
      const errorMessages = data.detail.map((e: any) =>
        typeof e === 'string' ? e : e.msg || 'Validation error'
      )

      // Limit number of errors shown for better UX
      const limitedMessages = errorMessages.slice(0, MAX_ERRORS_TO_SHOW)
      const hasMore = errorMessages.length > MAX_ERRORS_TO_SHOW

      return limitedMessages.join(', ') + (hasMore ? ` (and ${errorMessages.length - MAX_ERRORS_TO_SHOW} more)` : '')
    }

    // Handle string detail
    if (typeof data.detail === 'string') {
      return sanitizeErrorMessage(data.detail)
    }

    // Handle object with msg
    if (typeof data.detail === 'object' && data.detail !== null && 'msg' in data.detail) {
      return sanitizeErrorMessage((data.detail as { msg: string }).msg)
    }
  }

  if (data?.error) {
    return data.error
  }

  if (data?.message) {
    return data.message
  }

  // Fallback to error message if available
  if (apiError.message && apiError.message !== 'Network Error') {
    return apiError.message
  }

  return fallbackMessage
}

/**
 * Check if an error is a network error
 */
export function isNetworkError(error: unknown): boolean {
  const apiError = error as ApiError
  return (
    apiError.message?.includes('Network Error') ||
    apiError.code === 'ECONNABORTED' ||
    !apiError.response
  )
}

/**
 * Check if an error is an authentication error
 */
export function isAuthError(error: unknown): boolean {
  const apiError = error as ApiError
  return apiError.response?.status === 401
}

/**
 * Check if an error is a validation error
 */
export function isValidationError(error: unknown): boolean {
  const apiError = error as ApiError
  return apiError.response?.status === 422 || apiError.response?.status === 400
}

/**
 * Log error to console in development, and potentially to error tracking service in production
 */
export function logError(error: unknown, context?: string) {
  const timestamp = new Date().toISOString()
  const apiError = error as ApiError

  // Structured error object for logging
  const errorLog = {
    timestamp,
    context: context || 'unknown',
    message: getErrorMessage(error),
    status: apiError.response?.status,
    type: isNetworkError(error) ? 'network' : isAuthError(error) ? 'auth' : 'other',
  }

  if (import.meta.env.DEV) {
    // Development: detailed console logging
    console.error(`[${timestamp}] Error${context ? ` in ${context}` : ''}:`, error)
    console.error('Structured error:', errorLog)
  } else {
    // Production: structured logging and error tracking
    console.error(JSON.stringify(errorLog))

    // Send to Sentry error tracking service
    // Dynamic import to avoid issues if Sentry is not configured
    import('../config/sentry')
      .then(({ captureException }) => {
        captureException(error, {
          context: errorLog.context,
          type: errorLog.type,
          status: errorLog.status,
          timestamp: errorLog.timestamp,
        })
      })
      .catch(err => {
        // Sentry reporting failed - log but don't crash
        console.error('[Sentry] Failed to report error:', err)
      })
  }
}
