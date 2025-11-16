/**
 * Utility functions for consistent error handling and user-friendly error messages
 */

export interface ApiError {
  response?: {
    status?: number
    data?: {
      detail?: string | any[]
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
      const messages = data.detail.map((e: any) =>
        typeof e === 'string' ? e : e.msg || 'Validation error'
      )
      return messages.join(', ')
    }

    // Handle string detail
    if (typeof data.detail === 'string') {
      return data.detail
    }

    // Handle object with msg
    if (typeof data.detail === 'object' && 'msg' in data.detail) {
      return data.detail.msg
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
  if (process.env.NODE_ENV === 'development') {
    console.error(`Error${context ? ` in ${context}` : ''}:`, error)
  }

  // In production, you could send to error tracking service (e.g., Sentry)
  // if (process.env.NODE_ENV === 'production') {
  //   Sentry.captureException(error, { extra: { context } })
  // }
}
