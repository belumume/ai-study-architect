import api from './api'
import tokenStorage from './tokenStorage'

export interface LoginCredentials {
  username: string
  password: string
}

export interface RegisterData {
  username: string
  email: string
  password: string
  full_name?: string
}

export interface User {
  id: number
  username: string
  email: string
  full_name?: string
  is_active: boolean
  created_at: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  id: number
  username: string
  email: string
  full_name?: string
  is_active: boolean
  created_at: string
}

class AuthService {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    // OAuth2 requires form data for login
    const formData = new FormData()
    formData.append('username', credentials.username)
    formData.append('password', credentials.password)

    const response = await api.post<AuthResponse>('/api/v1/auth/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })

    // Tokens are now stored in httpOnly cookies by the backend
    // No need to store them in sessionStorage/localStorage
    // This is more secure (XSS-proof) and follows industry standards

    return response.data
  }

  async register(data: RegisterData): Promise<User> {
    const response = await api.post<User>('/api/v1/auth/register', data)
    return response.data
  }

  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/api/v1/auth/me')
    return response.data
  }

  async logout(): Promise<void> {
    try {
      // Call logout endpoint to clear httpOnly cookies
      await api.post('/api/v1/auth/logout')
    } catch (error) {
      // Continue with local logout even if server request fails
    } finally {
      // Clear any local tokens (for backward compatibility)
      tokenStorage.clearTokens()
    }
  }

  async isAuthenticated(): Promise<boolean> {
    try {
      // Check if we're authenticated by calling the /me endpoint
      // The httpOnly cookies will be sent automatically
      await api.get('/api/v1/auth/me')
      return true
    } catch {
      return false
    }
  }

  async getCSRFToken(): Promise<string> {
    const response = await api.get<{ csrf_token: string }>('/api/v1/csrf/token')
    return response.data.csrf_token
  }
}

export default new AuthService()