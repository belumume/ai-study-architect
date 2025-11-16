/**
 * API service tests
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'
import { api } from '../api'
import tokenStorage from '../tokenStorage'

// Mock tokenStorage
vi.mock('../tokenStorage', () => ({
  default: {
    getAccessToken: vi.fn(),
    getRefreshToken: vi.fn(),
    setTokens: vi.fn(),
    clearTokens: vi.fn(),
  },
}))

describe('API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    document.cookie = '' // Clear cookies
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Initialization', () => {
    it('creates axios instance with correct base URL', () => {
      expect(api.defaults.baseURL).toBeDefined()
    })

    it('sets default headers', () => {
      expect(api.defaults.headers['Content-Type']).toBe('application/json')
    })

    it('enables credentials for CSRF', () => {
      expect(api.defaults.withCredentials).toBe(true)
    })
  })

  describe('Request Interceptor - Auth Token', () => {
    it('adds Authorization header when token exists', async () => {
      const mockToken = 'test-access-token'
      vi.mocked(tokenStorage.getAccessToken).mockReturnValue(mockToken)

      const config = { headers: {} as any }
      const interceptor = api.interceptors.request.handlers[0]

      const result = await (interceptor as any).fulfilled(config)

      expect(result.headers.Authorization).toBe(`Bearer ${mockToken}`)
    })

    it('does not add Authorization header when no token exists', async () => {
      vi.mocked(tokenStorage.getAccessToken).mockReturnValue(null)

      const config = { headers: {} as any }
      const interceptor = api.interceptors.request.handlers[0]

      const result = await (interceptor as any).fulfilled(config)

      expect(result.headers.Authorization).toBeUndefined()
    })
  })

  describe('Request Interceptor - CSRF Token', () => {
    beforeEach(() => {
      // Set CSRF token in cookie
      document.cookie = 'csrf_token=test-csrf-token; path=/'
    })

    it('adds CSRF token for POST requests', async () => {
      const config = {
        method: 'post',
        headers: {} as any,
      }
      const interceptor = api.interceptors.request.handlers[0]

      const result = await (interceptor as any).fulfilled(config)

      expect(result.headers['X-CSRF-Token']).toBe('test-csrf-token')
    })

    it('adds CSRF token for PUT requests', async () => {
      const config = {
        method: 'put',
        headers: {} as any,
      }
      const interceptor = api.interceptors.request.handlers[0]

      const result = await (interceptor as any).fulfilled(config)

      expect(result.headers['X-CSRF-Token']).toBe('test-csrf-token')
    })

    it('adds CSRF token for DELETE requests', async () => {
      const config = {
        method: 'delete',
        headers: {} as any,
      }
      const interceptor = api.interceptors.request.handlers[0]

      const result = await (interceptor as any).fulfilled(config)

      expect(result.headers['X-CSRF-Token']).toBe('test-csrf-token')
    })

    it('does not add CSRF token for GET requests', async () => {
      const config = {
        method: 'get',
        headers: {} as any,
      }
      const interceptor = api.interceptors.request.handlers[0]

      const result = await (interceptor as any).fulfilled(config)

      expect(result.headers['X-CSRF-Token']).toBeUndefined()
    })

    it('handles missing CSRF token gracefully', async () => {
      document.cookie = '' // Clear CSRF token

      const config = {
        method: 'post',
        headers: {} as any,
      }
      const interceptor = api.interceptors.request.handlers[0]

      const result = await (interceptor as any).fulfilled(config)

      // Should not crash, just not set the header
      expect(result.headers['X-CSRF-Token']).toBeUndefined()
    })
  })

  describe('Request Interceptor - FormData', () => {
    it('removes Content-Type header for FormData', async () => {
      const formData = new FormData()
      formData.append('file', new Blob(['test']), 'test.txt')

      const config = {
        method: 'post',
        data: formData,
        headers: {
          'Content-Type': 'application/json',
        } as any,
      }
      const interceptor = api.interceptors.request.handlers[0]

      const result = await (interceptor as any).fulfilled(config)

      // Content-Type should be removed to let browser set boundary
      expect(result.headers['Content-Type']).toBeUndefined()
    })

    it('keeps Content-Type for non-FormData requests', async () => {
      const config = {
        method: 'post',
        data: { key: 'value' },
        headers: {
          'Content-Type': 'application/json',
        } as any,
      }
      const interceptor = api.interceptors.request.handlers[0]

      const result = await (interceptor as any).fulfilled(config)

      expect(result.headers['Content-Type']).toBe('application/json')
    })
  })

  describe('Response Interceptor - Success', () => {
    it('returns response for successful requests', async () => {
      const mockResponse = { data: { message: 'success' }, status: 200 }
      const interceptor = api.interceptors.response.handlers[0]

      const result = await (interceptor as any).fulfilled(mockResponse)

      expect(result).toEqual(mockResponse)
    })
  })

  describe('Response Interceptor - Token Refresh', () => {
    it('refreshes token on 401 error', async () => {
      const mockError = {
        response: { status: 401 },
        config: {
          url: '/api/v1/some-endpoint',
          headers: {} as any,
        },
      }

      const mockRefreshResponse = {
        data: { access_token: 'new-access-token' },
      }

      // Mock the refresh endpoint
      const postSpy = vi.spyOn(api, 'post').mockResolvedValueOnce(mockRefreshResponse)
      const apiSpy = vi.spyOn(api, 'request').mockResolvedValueOnce({ data: 'success' })

      const interceptor = api.interceptors.response.handlers[0]

      await (interceptor as any).rejected(mockError)

      // Should call refresh endpoint
      expect(postSpy).toHaveBeenCalledWith('/api/v1/auth/refresh')
    })

    it('does not retry refresh endpoint itself', async () => {
      const mockError = {
        response: { status: 401 },
        config: {
          url: '/api/v1/auth/refresh',
          headers: {} as any,
        },
      }

      const postSpy = vi.spyOn(api, 'post')
      const interceptor = api.interceptors.response.handlers[0]

      try {
        await (interceptor as any).rejected(mockError)
      } catch (error) {
        // Expected to reject
      }

      // Should not call refresh again
      expect(postSpy).not.toHaveBeenCalled()
    })

    it('does not retry login endpoint', async () => {
      const mockError = {
        response: { status: 401 },
        config: {
          url: '/api/v1/auth/login',
          headers: {} as any,
        },
      }

      const postSpy = vi.spyOn(api, 'post')
      const interceptor = api.interceptors.response.handlers[0]

      try {
        await (interceptor as any).rejected(mockError)
      } catch (error) {
        // Expected to reject
      }

      // Should not call refresh
      expect(postSpy).not.toHaveBeenCalled()
    })

    it('does not retry if already retried', async () => {
      const mockError = {
        response: { status: 401 },
        config: {
          url: '/api/v1/some-endpoint',
          headers: {} as any,
          _retry: true, // Already retried
        },
      }

      const postSpy = vi.spyOn(api, 'post')
      const interceptor = api.interceptors.response.handlers[0]

      try {
        await (interceptor as any).rejected(mockError)
      } catch (error) {
        // Expected to reject
      }

      // Should not call refresh again
      expect(postSpy).not.toHaveBeenCalled()
    })

    it('clears tokens and redirects on refresh failure', async () => {
      const mockError = {
        response: { status: 401 },
        config: {
          url: '/api/v1/some-endpoint',
          headers: {} as any,
        },
      }

      // Mock refresh endpoint to fail
      vi.spyOn(api, 'post').mockRejectedValueOnce(new Error('Refresh failed'))

      // Mock window.location
      delete (window as any).location
      window.location = { href: '', pathname: '/dashboard' } as any

      const interceptor = api.interceptors.response.handlers[0]

      try {
        await (interceptor as any).rejected(mockError)
      } catch (error) {
        // Expected to reject
      }

      // Should clear tokens
      expect(tokenStorage.clearTokens).toHaveBeenCalled()

      // Should redirect to login
      expect(window.location.href).toBe('/login')
    })

    it('does not redirect if already on login page', async () => {
      const mockError = {
        response: { status: 401 },
        config: {
          url: '/api/v1/some-endpoint',
          headers: {} as any,
        },
      }

      // Mock refresh endpoint to fail
      vi.spyOn(api, 'post').mockRejectedValueOnce(new Error('Refresh failed'))

      // Mock window.location
      delete (window as any).location
      window.location = { href: '', pathname: '/login' } as any

      const interceptor = api.interceptors.response.handlers[0]

      try {
        await (interceptor as any).rejected(mockError)
      } catch (error) {
        // Expected to reject
      }

      // Should not change location
      expect(window.location.href).toBe('')
    })
  })

  describe('Response Interceptor - Non-401 Errors', () => {
    it('passes through non-401 errors', async () => {
      const mockError = {
        response: { status: 500 },
        config: {
          url: '/api/v1/some-endpoint',
          headers: {} as any,
        },
      }

      const interceptor = api.interceptors.response.handlers[0]

      try {
        await (interceptor as any).rejected(mockError)
        expect.fail('Should have thrown error')
      } catch (error) {
        expect(error).toEqual(mockError)
      }
    })

    it('passes through 400 errors', async () => {
      const mockError = {
        response: { status: 400, data: { detail: 'Bad request' } },
        config: {
          url: '/api/v1/some-endpoint',
          headers: {} as any,
        },
      }

      const interceptor = api.interceptors.response.handlers[0]

      try {
        await (interceptor as any).rejected(mockError)
        expect.fail('Should have thrown error')
      } catch (error) {
        expect(error).toEqual(mockError)
      }
    })

    it('passes through 403 errors', async () => {
      const mockError = {
        response: { status: 403, data: { detail: 'Forbidden' } },
        config: {
          url: '/api/v1/some-endpoint',
          headers: {} as any,
        },
      }

      const interceptor = api.interceptors.response.handlers[0]

      try {
        await (interceptor as any).rejected(mockError)
        expect.fail('Should have thrown error')
      } catch (error) {
        expect(error).toEqual(mockError)
      }
    })
  })

  describe('CSRF Token Parsing', () => {
    it('parses CSRF token from cookies correctly', async () => {
      document.cookie = 'csrf_token=abc123; path=/'

      const config = {
        method: 'post',
        headers: {} as any,
      }
      const interceptor = api.interceptors.request.handlers[0]

      const result = await (interceptor as any).fulfilled(config)

      expect(result.headers['X-CSRF-Token']).toBe('abc123')
    })

    it('handles multiple cookies', async () => {
      document.cookie = 'other=value; csrf_token=xyz789; another=cookie'

      const config = {
        method: 'post',
        headers: {} as any,
      }
      const interceptor = api.interceptors.request.handlers[0]

      const result = await (interceptor as any).fulfilled(config)

      expect(result.headers['X-CSRF-Token']).toBe('xyz789')
    })

    it('handles encoded cookie values', async () => {
      document.cookie = 'csrf_token=encoded%20value; path=/'

      const config = {
        method: 'post',
        headers: {} as any,
      }
      const interceptor = api.interceptors.request.handlers[0]

      const result = await (interceptor as any).fulfilled(config)

      expect(result.headers['X-CSRF-Token']).toBe('encoded value')
    })
  })
})
