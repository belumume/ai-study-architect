import axios from 'axios'
import tokenStorage from './tokenStorage'

const API_BASE_URL = import.meta.env.VITE_API_URL || ''  // Use env var for production, proxy for dev

// Create axios instance with default config
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important for CSRF
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

// Request interceptor to add auth token (if using Bearer tokens)
api.interceptors.request.use(
  (config) => {
    // Backend now supports both cookies and Bearer tokens
    // We'll rely on httpOnly cookies for better security
    // But still support Bearer tokens for backward compatibility
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
        // CSRF token added successfully
      } else {
        // No CSRF token available yet - will be fetched on first API call
      }
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Don't try to refresh on refresh endpoint or if already retried
    if (
      error.response?.status === 401 && 
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/refresh') &&
      !originalRequest.url?.includes('/auth/login')
    ) {
      originalRequest._retry = true

      try {
        // Try to refresh the token using the refresh cookie
        const response = await api.post('/api/v1/auth/refresh')
        
        // If using Bearer tokens (backward compatibility), update the header
        if (response.data.access_token) {
          originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`
        }
        
        // Retry original request (cookies will be automatically included)
        return api(originalRequest)
      } catch (refreshError) {
        // Refresh failed, redirect to login only if not already on login page
        tokenStorage.clearTokens()
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login'
        }
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default api