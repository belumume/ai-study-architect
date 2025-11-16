import { describe, it, expect, vi } from 'vitest'
import {
  getErrorMessage,
  isNetworkError,
  isAuthError,
  isValidationError,
  logError,
  type ApiError,
} from './errorUtils'

describe('errorUtils', () => {
  describe('getErrorMessage', () => {
    it('should return fallback message for undefined error', () => {
      const result = getErrorMessage(undefined)
      expect(result).toBe('An unexpected error occurred')
    })

    it('should return custom fallback message', () => {
      const result = getErrorMessage(undefined, 'Custom error')
      expect(result).toBe('Custom error')
    })

    it('should handle network timeout errors', () => {
      const error: ApiError = {
        code: 'ECONNABORTED',
        message: 'timeout',
      }
      const result = getErrorMessage(error)
      expect(result).toBe('Request timed out. Please check your connection and try again.')
    })

    it('should handle network errors', () => {
      const error: ApiError = {
        message: 'Network Error',
      }
      const result = getErrorMessage(error)
      expect(result).toBe('Network error. Please check your internet connection.')
    })

    it('should handle 401 unauthorized errors', () => {
      const error: ApiError = {
        response: { status: 401 },
      }
      const result = getErrorMessage(error)
      expect(result).toBe('Your session has expired. Please log in again.')
    })

    it('should handle 403 forbidden errors', () => {
      const error: ApiError = {
        response: { status: 403 },
      }
      const result = getErrorMessage(error)
      expect(result).toBe('You do not have permission to perform this action.')
    })

    it('should handle 404 not found errors', () => {
      const error: ApiError = {
        response: { status: 404 },
      }
      const result = getErrorMessage(error)
      expect(result).toBe('The requested resource was not found.')
    })

    it('should handle 409 conflict errors', () => {
      const error: ApiError = {
        response: { status: 409 },
      }
      const result = getErrorMessage(error)
      expect(result).toBe('This item already exists.')
    })

    it('should handle 429 rate limit errors', () => {
      const error: ApiError = {
        response: { status: 429 },
      }
      const result = getErrorMessage(error)
      expect(result).toBe('Too many requests. Please wait a moment and try again.')
    })

    it('should handle 500 server errors', () => {
      const error: ApiError = {
        response: { status: 500 },
      }
      const result = getErrorMessage(error)
      expect(result).toBe('Server error. Please try again later.')
    })

    it('should handle string detail in response', () => {
      const error: ApiError = {
        response: {
          data: {
            detail: 'This is a test error',
          },
        },
      }
      const result = getErrorMessage(error)
      expect(result).toBe('This is a test error')
    })

    it('should handle array of validation errors', () => {
      const error: ApiError = {
        response: {
          data: {
            detail: [
              { msg: 'Field is required' },
              { msg: 'Invalid format' },
              'Simple error',
            ],
          },
        },
      }
      const result = getErrorMessage(error)
      expect(result).toContain('Field is required')
      expect(result).toContain('Invalid format')
      expect(result).toContain('Simple error')
    })

    it('should limit validation errors to 5 and show overflow', () => {
      const error: ApiError = {
        response: {
          data: {
            detail: Array(10).fill({ msg: 'Error' }),
          },
        },
      }
      const result = getErrorMessage(error)
      expect(result).toContain('(and 5 more)')
    })

    it('should sanitize API keys in error messages', () => {
      const error: ApiError = {
        response: {
          data: {
            detail: 'Failed with key sk-1234567890abcdef',
          },
        },
      }
      const result = getErrorMessage(error)
      expect(result).toContain('[REDACTED_KEY]')
      expect(result).not.toContain('sk-1234567890abcdef')
    })

    it('should sanitize file paths in error messages', () => {
      const error: ApiError = {
        response: {
          data: {
            detail: 'File not found at /home/user/secret.txt',
          },
        },
      }
      const result = getErrorMessage(error)
      expect(result).toContain('[REDACTED_PATH]')
      expect(result).not.toContain('/home/user/secret.txt')
    })

    it('should sanitize URLs with credentials', () => {
      const error: ApiError = {
        response: {
          data: {
            detail: 'Failed to connect to https://user:password@example.com',
          },
        },
      }
      const result = getErrorMessage(error)
      expect(result).toContain('[REDACTED_URL]')
      expect(result).not.toContain('user:password')
    })

    it('should sanitize email addresses', () => {
      const error: ApiError = {
        response: {
          data: {
            detail: 'Error for user test@example.com',
          },
        },
      }
      const result = getErrorMessage(error)
      expect(result).toContain('[REDACTED_EMAIL]')
      expect(result).not.toContain('test@example.com')
    })

    it('should handle object with msg property', () => {
      const error: ApiError = {
        response: {
          data: {
            detail: { msg: 'Object error message' },
          },
        },
      }
      const result = getErrorMessage(error)
      expect(result).toBe('Object error message')
    })

    it('should handle error field in response', () => {
      const error: ApiError = {
        response: {
          data: {
            error: 'Error field message',
          },
        },
      }
      const result = getErrorMessage(error)
      expect(result).toBe('Error field message')
    })

    it('should handle message field in response', () => {
      const error: ApiError = {
        response: {
          data: {
            message: 'Message field content',
          },
        },
      }
      const result = getErrorMessage(error)
      expect(result).toBe('Message field content')
    })
  })

  describe('isNetworkError', () => {
    it('should return true for Network Error', () => {
      const error: ApiError = {
        message: 'Network Error',
      }
      expect(isNetworkError(error)).toBe(true)
    })

    it('should return true for ECONNABORTED', () => {
      const error: ApiError = {
        code: 'ECONNABORTED',
      }
      expect(isNetworkError(error)).toBe(true)
    })

    it('should return true when no response', () => {
      const error: ApiError = {
        message: 'Something failed',
      }
      expect(isNetworkError(error)).toBe(true)
    })

    it('should return false when response exists', () => {
      const error: ApiError = {
        response: { status: 500 },
      }
      expect(isNetworkError(error)).toBe(false)
    })
  })

  describe('isAuthError', () => {
    it('should return true for 401 status', () => {
      const error: ApiError = {
        response: { status: 401 },
      }
      expect(isAuthError(error)).toBe(true)
    })

    it('should return false for other statuses', () => {
      const error: ApiError = {
        response: { status: 403 },
      }
      expect(isAuthError(error)).toBe(false)
    })

    it('should return false when no response', () => {
      const error: ApiError = {}
      expect(isAuthError(error)).toBe(false)
    })
  })

  describe('isValidationError', () => {
    it('should return true for 422 status', () => {
      const error: ApiError = {
        response: { status: 422 },
      }
      expect(isValidationError(error)).toBe(true)
    })

    it('should return true for 400 status', () => {
      const error: ApiError = {
        response: { status: 400 },
      }
      expect(isValidationError(error)).toBe(true)
    })

    it('should return false for other statuses', () => {
      const error: ApiError = {
        response: { status: 500 },
      }
      expect(isValidationError(error)).toBe(false)
    })
  })

  describe('logError', () => {
    it('should log error with context in development', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      const error = new Error('Test error')

      logError(error, 'test context')

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('Error in test context'),
        error
      )
      expect(consoleSpy).toHaveBeenCalledWith(
        'Structured error:',
        expect.objectContaining({
          context: 'test context',
        })
      )

      consoleSpy.mockRestore()
    })

    it('should use "unknown" as default context', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      const error = new Error('Test error')

      logError(error)

      expect(consoleSpy).toHaveBeenCalledWith(
        'Structured error:',
        expect.objectContaining({
          context: 'unknown',
        })
      )

      consoleSpy.mockRestore()
    })

    it('should include error type in log', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      const error: ApiError = {
        response: { status: 401 },
      }

      logError(error)

      expect(consoleSpy).toHaveBeenCalledWith(
        'Structured error:',
        expect.objectContaining({
          type: 'auth',
        })
      )

      consoleSpy.mockRestore()
    })
  })
})
