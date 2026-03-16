import axios from 'axios'
import tokenStorage from './tokenStorage'

// With Cloudflare Worker, we can use relative paths everywhere!
// Same-origin means no CORS, better security, and simpler code
const API_BASE_URL = import.meta.env.VITE_API_URL || ''

// Create axios instance with default config
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important for CSRF and httpOnly cookies
})

// Function to get CSRF token from cookies
function getCSRFToken(): string | null {
  const name = 'csrf_token='
  const decodedCookie = decodeURIComponent(document.cookie)
  const cookies = decodedCookie.split(';')

  for (let cookie of cookies) {
    cookie = cookie.trim()
    if (cookie.indexOf(name) === 0) {
      return cookie.substring(name.length)
    }
  }
  return null
}

// Refresh token queue: prevents concurrent refresh calls from racing
let isRefreshing = false
let refreshSubscribers: ((token: string | null) => void)[] = []

function onRefreshed(token: string | null) {
  refreshSubscribers.forEach((callback) => callback(token))
  refreshSubscribers = []
}

function addRefreshSubscriber(callback: (token: string | null) => void) {
  refreshSubscribers.push(callback)
}

// Request interceptor to add auth token (if using Bearer tokens)
api.interceptors.request.use(
  (config) => {
    const token = tokenStorage.getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // Remove Content-Type header for FormData (let browser set it with boundary)
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }

    // Add CSRF token for state-changing requests
    if (['post', 'put', 'patch', 'delete'].includes(config.method?.toLowerCase() || '')) {
      const csrfToken = getCSRFToken()
      if (csrfToken) {
        config.headers['X-CSRF-Token'] = csrfToken
      }
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  },
)

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Don't try to refresh on refresh/login endpoints or if already retried
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/refresh') &&
      !originalRequest.url?.includes('/auth/login')
    ) {
      originalRequest._retry = true

      // If a refresh is already in progress, queue this request
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          addRefreshSubscriber((token: string | null) => {
            if (token) {
              originalRequest.headers.Authorization = `Bearer ${token}`
              resolve(api(originalRequest))
            } else {
              reject(error)
            }
          })
        })
      }

      isRefreshing = true

      try {
        // Refresh using httpOnly cookie (sent automatically with withCredentials)
        const response = await api.post('/api/v1/auth/refresh')
        const newAccessToken = response.data.access_token || null

        // Update Bearer header for the original request
        if (newAccessToken) {
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        }

        // Notify all queued requests that refresh succeeded
        onRefreshed(newAccessToken)

        return api(originalRequest)
      } catch (refreshError) {
        // Refresh failed — clear tokens and redirect to login
        onRefreshed(null)
        tokenStorage.clearTokens()
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login'
        }
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  },
)

export default api
