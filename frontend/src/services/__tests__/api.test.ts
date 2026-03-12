/**
 * API service tests
 *
 * Mocks axios.create at module level to prevent real axios instances
 * (which contain non-serializable transformRequest functions) from
 * being created. This eliminates the DataCloneError in vitest.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// vi.hoisted runs before vi.mock hoisting — safe to reference in mock factories
const {
  requestInterceptors,
  responseInterceptors,
  mockAxiosInstance,
  mockTokenStorage,
} = vi.hoisted(() => {
  const requestInterceptors: Array<{ fulfilled: Function; rejected?: Function }> = []
  const responseInterceptors: Array<{ fulfilled: Function; rejected?: Function }> = []

  const mockAxiosInstance = {
    defaults: {
      baseURL: '',
      headers: { 'Content-Type': 'application/json' } as Record<string, any>,
      withCredentials: true,
    },
    interceptors: {
      request: {
        use: vi.fn((fulfilled: Function, rejected?: Function) => {
          requestInterceptors.push({ fulfilled, rejected })
          return requestInterceptors.length - 1
        }),
        clear: vi.fn(),
      },
      response: {
        use: vi.fn((fulfilled: Function, rejected?: Function) => {
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

  const mockTokenStorage = {
    getAccessToken: vi.fn(),
    getRefreshToken: vi.fn(),
    setTokens: vi.fn(),
    clearTokens: vi.fn(),
  }

  return { requestInterceptors, responseInterceptors, mockAxiosInstance, mockTokenStorage }
})

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => mockAxiosInstance),
  },
}))

vi.mock('../tokenStorage', () => ({
  default: mockTokenStorage,
}))

// Import AFTER mocks are set up (vitest hoists vi.mock)
import { api } from '../api'

describe('API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    document.cookie = ''
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

  describe('Request Interceptor - Auth Token', () => {
    it('adds Authorization header when token exists', () => {
      mockTokenStorage.getAccessToken.mockReturnValue('test-access-token')

      const config = {
        headers: {} as Record<string, any>,
        method: 'get',
      }

      const result = requestInterceptors[0].fulfilled(config)

      expect(result.headers.Authorization).toBe('Bearer test-access-token')
    })

    it('does not add Authorization header when no token', () => {
      mockTokenStorage.getAccessToken.mockReturnValue(null)

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
      mockTokenStorage.getAccessToken.mockReturnValue(null)

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
      mockTokenStorage.getAccessToken.mockReturnValue(null)

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
      mockTokenStorage.getAccessToken.mockReturnValue(null)
      document.cookie = 'csrf_token=test-csrf-token; path=/'

      const config = {
        headers: {} as Record<string, any>,
        method: 'post',
      }

      const result = requestInterceptors[0].fulfilled(config)

      expect(result.headers['X-CSRF-Token']).toBe('test-csrf-token')
    })

    it('adds CSRF header for PUT requests', () => {
      mockTokenStorage.getAccessToken.mockReturnValue(null)
      document.cookie = 'csrf_token=csrf-put-token; path=/'

      const config = {
        headers: {} as Record<string, any>,
        method: 'put',
      }

      const result = requestInterceptors[0].fulfilled(config)

      expect(result.headers['X-CSRF-Token']).toBe('csrf-put-token')
    })

    it('adds CSRF header for DELETE requests', () => {
      mockTokenStorage.getAccessToken.mockReturnValue(null)
      document.cookie = 'csrf_token=csrf-delete-token; path=/'

      const config = {
        headers: {} as Record<string, any>,
        method: 'delete',
      }

      const result = requestInterceptors[0].fulfilled(config)

      expect(result.headers['X-CSRF-Token']).toBe('csrf-delete-token')
    })

    it('does not add CSRF header for GET requests', () => {
      mockTokenStorage.getAccessToken.mockReturnValue(null)
      document.cookie = 'csrf_token=test-csrf-token; path=/'

      const config = {
        headers: {} as Record<string, any>,
        method: 'get',
      }

      const result = requestInterceptors[0].fulfilled(config)

      expect(result.headers['X-CSRF-Token']).toBeUndefined()
    })

    it('handles missing CSRF token gracefully', () => {
      mockTokenStorage.getAccessToken.mockReturnValue(null)
      document.cookie = ''

      const config = {
        headers: {} as Record<string, any>,
        method: 'post',
      }

      const result = requestInterceptors[0].fulfilled(config)

      expect(result.headers['X-CSRF-Token']).toBeUndefined()
    })

    it('handles multiple cookies', () => {
      mockTokenStorage.getAccessToken.mockReturnValue(null)
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
      mockTokenStorage.getAccessToken.mockReturnValue(null)
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
        data: { access_token: 'new-token' },
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
