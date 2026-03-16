/**
 * API service tests
 *
 * Mocks axios.create at module level to prevent real axios instances
 * (which contain non-serializable transformRequest functions) from
 * being created. This eliminates the DataCloneError in vitest.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// vi.hoisted runs before vi.mock hoisting — safe to reference in mock factories
const { requestInterceptors, responseInterceptors, mockAxiosInstance, mockClearLegacyTokens } =
  vi.hoisted(() => {
    type InterceptorFn = (...args: unknown[]) => unknown
    const requestInterceptors: Array<{ fulfilled: InterceptorFn; rejected?: InterceptorFn }> = []
    const responseInterceptors: Array<{ fulfilled: InterceptorFn; rejected?: InterceptorFn }> = []

    const mockAxiosInstance = {
      defaults: {
        baseURL: '',
        headers: { 'Content-Type': 'application/json' } as Record<string, any>,
        withCredentials: true,
      },
      interceptors: {
        request: {
          use: vi.fn((fulfilled: InterceptorFn, rejected?: InterceptorFn) => {
            requestInterceptors.push({ fulfilled, rejected })
            return requestInterceptors.length - 1
          }),
          clear: vi.fn(),
        },
        response: {
          use: vi.fn((fulfilled: InterceptorFn, rejected?: InterceptorFn) => {
            responseInterceptors.push({ fulfilled, rejected })
            return responseInterceptors.length - 1
          }),
          clear: vi.fn(),
        },
      },
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      patch: vi.fn(),
      request: vi.fn(),
    }

    const mockClearLegacyTokens = vi.fn()

    return { requestInterceptors, responseInterceptors, mockAxiosInstance, mockClearLegacyTokens }
  })

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => mockAxiosInstance),
  },
}))

vi.mock('../tokenStorage', () => ({
  clearLegacyTokens: mockClearLegacyTokens,
}))

// Import AFTER mocks are set up (vitest hoists vi.mock)
import { api, __resetRefreshStateForTesting } from '../api'

describe('API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Properly clear cookies (setting '' just adds an empty cookie)
    document.cookie.split(';').forEach((c) => {
      const name = c.split('=')[0].trim()
      if (name) document.cookie = `${name}=; max-age=0`
    })
  })

  describe('Initialization', () => {
    it('creates axios instance with correct config', () => {
      expect(api.defaults.headers['Content-Type']).toBe('application/json')
      expect(api.defaults.withCredentials).toBe(true)
    })

    it('registers request and response interceptors', () => {
      expect(requestInterceptors.length).toBeGreaterThan(0)
      expect(responseInterceptors.length).toBeGreaterThan(0)
    })
  })

  describe('Request Interceptor - Auth', () => {
    it('always deletes Authorization header (cookie-only auth)', () => {
      const config = {
        headers: { Authorization: 'Bearer stale-token' } as Record<string, any>,
        method: 'get',
      }

      const result = requestInterceptors[0].fulfilled(config)

      expect(result.headers.Authorization).toBeUndefined()
    })

    it('does not set Authorization header', () => {
      const config = {
        headers: {} as Record<string, any>,
        method: 'get',
      }

      const result = requestInterceptors[0].fulfilled(config)

      expect(result.headers.Authorization).toBeUndefined()
    })
  })

  describe('Request Interceptor - FormData', () => {
    it('removes Content-Type for FormData', () => {
      const formData = new FormData()
      const config = {
        headers: { 'Content-Type': 'application/json' } as Record<string, any>,
        data: formData,
        method: 'post',
      }

      const result = requestInterceptors[0].fulfilled(config)

      expect(result.headers['Content-Type']).toBeUndefined()
    })

    it('keeps Content-Type for JSON data', () => {
      const config = {
        headers: { 'Content-Type': 'application/json' } as Record<string, any>,
        data: { key: 'value' },
        method: 'post',
      }

      const result = requestInterceptors[0].fulfilled(config)

      expect(result.headers['Content-Type']).toBe('application/json')
    })
  })

  describe('Request Interceptor - CSRF Token', () => {
    it('adds CSRF header for POST requests', () => {
      document.cookie = 'csrf_token=test-csrf-token; path=/'

      const config = {
        headers: {} as Record<string, any>,
        method: 'post',
      }

      const result = requestInterceptors[0].fulfilled(config)

      expect(result.headers['X-CSRF-Token']).toBe('test-csrf-token')
    })

    it('adds CSRF header for PUT requests', () => {
      document.cookie = 'csrf_token=csrf-put-token; path=/'

      const config = {
        headers: {} as Record<string, any>,
        method: 'put',
      }

      const result = requestInterceptors[0].fulfilled(config)

      expect(result.headers['X-CSRF-Token']).toBe('csrf-put-token')
    })

    it('adds CSRF header for DELETE requests', () => {
      document.cookie = 'csrf_token=csrf-delete-token; path=/'

      const config = {
        headers: {} as Record<string, any>,
        method: 'delete',
      }

      const result = requestInterceptors[0].fulfilled(config)

      expect(result.headers['X-CSRF-Token']).toBe('csrf-delete-token')
    })

    it('does not add CSRF header for GET requests', () => {
      document.cookie = 'csrf_token=test-csrf-token; path=/'

      const config = {
        headers: {} as Record<string, any>,
        method: 'get',
      }

      const result = requestInterceptors[0].fulfilled(config)

      expect(result.headers['X-CSRF-Token']).toBeUndefined()
    })

    it('handles missing CSRF token gracefully', () => {
      document.cookie = 'csrf_token=; max-age=0'

      const config = {
        headers: {} as Record<string, any>,
        method: 'post',
      }

      const result = requestInterceptors[0].fulfilled(config)

      expect(result.headers['X-CSRF-Token']).toBeUndefined()
    })

    it('handles multiple cookies', () => {
      document.cookie = 'other=value'
      document.cookie = 'csrf_token=xyz789'
      document.cookie = 'another=cookie'

      const config = {
        headers: {} as Record<string, any>,
        method: 'post',
      }

      const result = requestInterceptors[0].fulfilled(config)

      expect(result.headers['X-CSRF-Token']).toBe('xyz789')
    })

    it('handles encoded cookie values', () => {
      document.cookie = 'csrf_token=encoded%20value; path=/'

      const config = {
        headers: {} as Record<string, any>,
        method: 'post',
      }

      const result = requestInterceptors[0].fulfilled(config)

      expect(result.headers['X-CSRF-Token']).toBe('encoded value')
    })
  })

  describe('Request Interceptor - Error Path', () => {
    it('rejects on request error', async () => {
      const error = new Error('Request setup failed')

      await expect(requestInterceptors[0].rejected!(error)).rejects.toThrow('Request setup failed')
    })
  })

  describe('Response Interceptor - Success', () => {
    it('passes through successful responses', () => {
      const response = { data: { message: 'success' }, status: 200 }

      const result = responseInterceptors[0].fulfilled(response)

      expect(result).toBe(response)
    })
  })

  describe('Response Interceptor - Error Handling', () => {
    it('rejects 401 errors from auth endpoints without retry', async () => {
      const error = {
        response: { status: 401 },
        config: { url: '/auth/login', _retry: false },
      }

      await expect(responseInterceptors[0].rejected!(error)).rejects.toEqual(error)
    })

    it('rejects 500 errors', async () => {
      const error = {
        response: { status: 500 },
        config: { url: '/api/v1/some-endpoint' },
      }

      await expect(responseInterceptors[0].rejected!(error)).rejects.toEqual(error)
    })

    it('rejects 400 errors', async () => {
      const error = {
        response: { status: 400, data: { detail: 'Bad request' } },
        config: { url: '/api/v1/some-endpoint' },
      }

      await expect(responseInterceptors[0].rejected!(error)).rejects.toEqual(error)
    })

    it('rejects 403 errors', async () => {
      const error = {
        response: { status: 403, data: { detail: 'Forbidden' } },
        config: { url: '/api/v1/some-endpoint' },
      }

      await expect(responseInterceptors[0].rejected!(error)).rejects.toEqual(error)
    })

    it('attempts token refresh on 401 from non-auth endpoints', async () => {
      mockAxiosInstance.post.mockResolvedValueOnce({
        data: { token_type: 'bearer' },
      })

      const originalConfig = {
        url: '/api/v1/some-endpoint',
        headers: {} as Record<string, any>,
        _retry: undefined as boolean | undefined,
      }

      const error = {
        response: { status: 401 },
        config: originalConfig,
      }

      // The interceptor calls api.post('/api/v1/auth/refresh')
      // then retries with the original config
      try {
        await responseInterceptors[0].rejected!(error)
      } catch {
        // May reject if mock setup isn't complete — that's fine,
        // we're testing that it attempted the refresh
      }

      expect(originalConfig._retry).toBe(true)
    })
  })

  describe('Refresh Queue (concurrent 401 handling)', () => {
    beforeEach(() => {
      __resetRefreshStateForTesting()
    })

    it('only makes one refresh call for concurrent 401s', async () => {
      // Control refresh timing — hold it pending so both 401s arrive before resolution
      let resolveRefresh!: (value: unknown) => void
      const refreshPromise = new Promise((resolve) => {
        resolveRefresh = resolve
      })
      mockAxiosInstance.post.mockReturnValueOnce(refreshPromise)

      const makeError = (url: string) => ({
        response: { status: 401 },
        config: {
          url,
          headers: {} as Record<string, any>,
          _retry: undefined as boolean | undefined,
        },
      })

      // First 401 starts refresh; second queues behind it
      const p1 = responseInterceptors[0].rejected!(makeError('/api/v1/a'))
      const p2 = responseInterceptors[0].rejected!(makeError('/api/v1/b'))

      // Only ONE refresh call made (second was queued, not duplicated)
      expect(mockAxiosInstance.post).toHaveBeenCalledTimes(1)
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/v1/auth/refresh')

      // Resolve to prevent hanging — retry calls api(config) which isn't callable
      // in this mock, so they'll reject. That's fine — we proved the queuing works.
      resolveRefresh({ data: { token_type: 'bearer' } })

      // Settle both promises (they'll reject due to mock limitations on api())
      await p1.catch(() => {})
      await p2.catch(() => {})
    })

    it('rejects queued requests on refresh failure and redirects', async () => {
      mockAxiosInstance.post.mockRejectedValueOnce(new Error('refresh failed'))

      const error = {
        response: { status: 401 },
        config: {
          url: '/api/v1/a',
          headers: {} as Record<string, any>,
          _retry: undefined as boolean | undefined,
        },
      }

      await expect(responseInterceptors[0].rejected!(error)).rejects.toThrow('refresh failed')

      expect(mockClearLegacyTokens).toHaveBeenCalled()
    })

    it('resets state after refresh so next 401 triggers new refresh', async () => {
      // First refresh succeeds (retry will fail — that's ok)
      mockAxiosInstance.post.mockResolvedValueOnce({ data: { token_type: 'bearer' } })

      const error1 = {
        response: { status: 401 },
        config: {
          url: '/api/v1/a',
          headers: {} as Record<string, any>,
          _retry: undefined as boolean | undefined,
        },
      }

      try {
        await responseInterceptors[0].rejected!(error1)
      } catch {
        // api(config) not callable in mock — expected
      }

      // Second 401 should trigger a NEW refresh call (isRefreshing was reset in finally)
      mockAxiosInstance.post.mockResolvedValueOnce({ data: { token_type: 'bearer' } })
      const error2 = {
        response: { status: 401 },
        config: {
          url: '/api/v1/b',
          headers: {} as Record<string, any>,
          _retry: undefined as boolean | undefined,
        },
      }

      try {
        await responseInterceptors[0].rejected!(error2)
      } catch {
        // same
      }

      // Two separate refresh calls — state was properly reset between them
      expect(mockAxiosInstance.post).toHaveBeenCalledTimes(2)
    })

    it('clears legacy tokens on refresh failure', async () => {
      mockAxiosInstance.post.mockRejectedValueOnce(new Error('fail'))

      try {
        await responseInterceptors[0].rejected!({
          response: { status: 401 },
          config: {
            url: '/api/v1/a',
            headers: {} as Record<string, any>,
            _retry: undefined as boolean | undefined,
          },
        })
      } catch {
        // expected
      }

      expect(mockClearLegacyTokens).toHaveBeenCalled()
    })

    it('clears legacy tokens on refresh success', async () => {
      mockAxiosInstance.post.mockResolvedValueOnce({ data: { token_type: 'bearer' } })

      try {
        await responseInterceptors[0].rejected!({
          response: { status: 401 },
          config: {
            url: '/api/v1/a',
            headers: {} as Record<string, any>,
            _retry: undefined as boolean | undefined,
          },
        })
      } catch {
        // api(config) not callable in mock
      }

      expect(mockClearLegacyTokens).toHaveBeenCalled()
    })
  })

  describe('API Methods', () => {
    it('supports GET requests', async () => {
      mockAxiosInstance.get.mockResolvedValueOnce({ data: { message: 'success' } })

      const result = await api.get('/test')

      expect(result.data).toEqual({ message: 'success' })
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/test')
    })

    it('supports POST requests', async () => {
      mockAxiosInstance.post.mockResolvedValueOnce({ data: { message: 'created' } })

      const result = await api.post('/test', { name: 'test' })

      expect(result.data).toEqual({ message: 'created' })
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/test', { name: 'test' })
    })

    it('supports PUT requests', async () => {
      mockAxiosInstance.put.mockResolvedValueOnce({ data: { message: 'updated' } })

      const result = await api.put('/test/1', { name: 'updated' })

      expect(result.data).toEqual({ message: 'updated' })
    })

    it('supports DELETE requests', async () => {
      mockAxiosInstance.delete.mockResolvedValueOnce({ data: { message: 'deleted' } })

      const result = await api.delete('/test/1')

      expect(result.data).toEqual({ message: 'deleted' })
    })

    it('supports PATCH requests', async () => {
      mockAxiosInstance.patch.mockResolvedValueOnce({ data: { message: 'patched' } })

      const result = await api.patch('/test/1', { status: 'active' })

      expect(result.data).toEqual({ message: 'patched' })
    })
  })
})
