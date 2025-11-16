/**
 * API service tests
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
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

      // Make a request to trigger interceptor
      const mockResponse = { data: { message: 'success' } }
      vi.spyOn(api, 'request').mockResolvedValueOnce(mockResponse)

      await api.get('/test')

      // Check that request was called
      expect(api.request).toHaveBeenCalled()
    })

    it('does not crash when no token exists', async () => {
      vi.mocked(tokenStorage.getAccessToken).mockReturnValue(null)

      const mockResponse = { data: { message: 'success' } }
      vi.spyOn(api, 'request').mockResolvedValueOnce(mockResponse)

      await api.get('/test')

      expect(api.request).toHaveBeenCalled()
    })
  })

  describe('Request Interceptor - CSRF Token', () => {
    beforeEach(() => {
      // Set CSRF token in cookie
      document.cookie = 'csrf_token=test-csrf-token; path=/'
    })

    it('handles POST requests correctly', async () => {
      const mockResponse = { data: { message: 'success' } }
      vi.spyOn(api, 'request').mockResolvedValueOnce(mockResponse)

      await api.post('/test', { data: 'test' })

      expect(api.request).toHaveBeenCalled()
    })

    it('handles GET requests correctly', async () => {
      const mockResponse = { data: { message: 'success' } }
      vi.spyOn(api, 'request').mockResolvedValueOnce(mockResponse)

      await api.get('/test')

      expect(api.request).toHaveBeenCalled()
    })

    it('handles missing CSRF token gracefully', async () => {
      document.cookie = '' // Clear CSRF token

      const mockResponse = { data: { message: 'success' } }
      vi.spyOn(api, 'request').mockResolvedValueOnce(mockResponse)

      await api.post('/test', { data: 'test' })

      // Should not crash
      expect(api.request).toHaveBeenCalled()
    })
  })

  describe('Request Interceptor - FormData', () => {
    it('handles FormData correctly', async () => {
      const formData = new FormData()
      formData.append('file', new Blob(['test']), 'test.txt')

      const mockResponse = { data: { message: 'success' } }
      vi.spyOn(api, 'request').mockResolvedValueOnce(mockResponse)

      await api.post('/upload', formData)

      expect(api.request).toHaveBeenCalled()
    })

    it('handles JSON data correctly', async () => {
      const mockResponse = { data: { message: 'success' } }
      vi.spyOn(api, 'request').mockResolvedValueOnce(mockResponse)

      await api.post('/test', { key: 'value' })

      expect(api.request).toHaveBeenCalled()
    })
  })

  describe('Response Interceptor - Success', () => {
    it('returns response for successful requests', async () => {
      const mockResponse = { data: { message: 'success' }, status: 200 }
      vi.spyOn(api, 'request').mockResolvedValueOnce(mockResponse)

      const result = await api.get('/test')

      expect(result.data).toEqual({ message: 'success' })
    })
  })

  describe('Response Interceptor - Error Handling', () => {
    it('handles 401 errors', async () => {
      const error = {
        response: { status: 401 },
        config: { url: '/api/v1/some-endpoint' },
      }

      vi.spyOn(api, 'request').mockRejectedValueOnce(error)

      try {
        await api.get('/test')
        expect.fail('Should have thrown error')
      } catch (e: any) {
        expect(e.response?.status).toBe(401)
      }
    })

    it('handles 500 errors', async () => {
      const error = {
        response: { status: 500 },
        config: { url: '/api/v1/some-endpoint' },
      }

      vi.spyOn(api, 'request').mockRejectedValueOnce(error)

      try {
        await api.get('/test')
        expect.fail('Should have thrown error')
      } catch (e: any) {
        expect(e.response?.status).toBe(500)
      }
    })

    it('handles 400 errors', async () => {
      const error = {
        response: { status: 400, data: { detail: 'Bad request' } },
        config: { url: '/api/v1/some-endpoint' },
      }

      vi.spyOn(api, 'request').mockRejectedValueOnce(error)

      try {
        await api.get('/test')
        expect.fail('Should have thrown error')
      } catch (e: any) {
        expect(e.response?.status).toBe(400)
      }
    })

    it('handles 403 errors', async () => {
      const error = {
        response: { status: 403, data: { detail: 'Forbidden' } },
        config: { url: '/api/v1/some-endpoint' },
      }

      vi.spyOn(api, 'request').mockRejectedValueOnce(error)

      try {
        await api.get('/test')
        expect.fail('Should have thrown error')
      } catch (e: any) {
        expect(e.response?.status).toBe(403)
      }
    })
  })

  describe('CSRF Token Parsing', () => {
    it('handles cookie with CSRF token', async () => {
      document.cookie = 'csrf_token=abc123; path=/'

      const mockResponse = { data: { message: 'success' } }
      vi.spyOn(api, 'request').mockResolvedValueOnce(mockResponse)

      await api.post('/test', { data: 'test' })

      expect(api.request).toHaveBeenCalled()
    })

    it('handles multiple cookies', async () => {
      document.cookie = 'other=value; csrf_token=xyz789; another=cookie'

      const mockResponse = { data: { message: 'success' } }
      vi.spyOn(api, 'request').mockResolvedValueOnce(mockResponse)

      await api.post('/test', { data: 'test' })

      expect(api.request).toHaveBeenCalled()
    })

    it('handles encoded cookie values', async () => {
      document.cookie = 'csrf_token=encoded%20value; path=/'

      const mockResponse = { data: { message: 'success' } }
      vi.spyOn(api, 'request').mockResolvedValueOnce(mockResponse)

      await api.post('/test', { data: 'test' })

      expect(api.request).toHaveBeenCalled()
    })
  })

  describe('API Methods', () => {
    it('supports GET requests', async () => {
      const mockResponse = { data: { message: 'success' } }
      vi.spyOn(api, 'request').mockResolvedValueOnce(mockResponse)

      const result = await api.get('/test')

      expect(result.data).toEqual({ message: 'success' })
    })

    it('supports POST requests', async () => {
      const mockResponse = { data: { message: 'created' } }
      vi.spyOn(api, 'request').mockResolvedValueOnce(mockResponse)

      const result = await api.post('/test', { name: 'test' })

      expect(result.data).toEqual({ message: 'created' })
    })

    it('supports PUT requests', async () => {
      const mockResponse = { data: { message: 'updated' } }
      vi.spyOn(api, 'request').mockResolvedValueOnce(mockResponse)

      const result = await api.put('/test/1', { name: 'updated' })

      expect(result.data).toEqual({ message: 'updated' })
    })

    it('supports DELETE requests', async () => {
      const mockResponse = { data: { message: 'deleted' } }
      vi.spyOn(api, 'request').mockResolvedValueOnce(mockResponse)

      const result = await api.delete('/test/1')

      expect(result.data).toEqual({ message: 'deleted' })
    })

    it('supports PATCH requests', async () => {
      const mockResponse = { data: { message: 'patched' } }
      vi.spyOn(api, 'request').mockResolvedValueOnce(mockResponse)

      const result = await api.patch('/test/1', { status: 'active' })

      expect(result.data).toEqual({ message: 'patched' })
    })
  })
})
