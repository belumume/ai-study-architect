import api from './api'

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

    const { access_token, refresh_token } = response.data
    localStorage.setItem('access_token', access_token)
    localStorage.setItem('refresh_token', refresh_token)

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
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        await api.post('/api/v1/auth/logout', { refresh_token: refreshToken })
      }
    } catch (error) {
      // Continue with local logout even if server request fails
    } finally {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
  }

  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token')
  }

  async getCSRFToken(): Promise<string> {
    const response = await api.get<{ csrf_token: string }>('/api/v1/csrf/token')
    return response.data.csrf_token
  }
}

export default new AuthService()