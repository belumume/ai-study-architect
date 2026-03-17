import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { isAxiosError } from 'axios'
import authService, { User, LoginCredentials, RegisterData } from '../services/auth.service'

interface AuthContextType {
  user: User | null
  loading: boolean
  error: string | null
  login: (credentials: LoginCredentials) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => Promise<void>
  clearError: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  // Check if user is authenticated on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const isAuth = await authService.isAuthenticated()
        if (isAuth) {
          const currentUser = await authService.getCurrentUser()
          setUser(currentUser)
        }
      } catch (err) {
        // Auth check failed — interceptor already handles refresh/redirect
      } finally {
        setLoading(false)
      }
    }

    checkAuth()
  }, [])

  const login = async (credentials: LoginCredentials) => {
    try {
      setError(null)
      setLoading(true)
      await authService.login(credentials)

      // Get current user data after login
      try {
        const currentUser = await authService.getCurrentUser()
        setUser(currentUser)
        navigate('/')
      } catch (userErr) {
        // Even if getting user fails, we're logged in
        navigate('/')
      }
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        setError(err.response?.data?.detail || 'Login failed. Please try again.')
      } else {
        setError('Login failed. Please try again.')
      }
      throw err
    } finally {
      setLoading(false)
    }
  }

  const register = async (data: RegisterData) => {
    setError(null)
    setLoading(true)
    try {
      await authService.register(data)
    } catch (err: unknown) {
      setLoading(false)
      if (isAxiosError(err)) {
        setError(err.response?.data?.detail || 'Registration failed. Please try again.')
      } else {
        setError('Registration failed. Please try again.')
      }
      throw err
    }

    // Registration succeeded — attempt auto-login
    try {
      await login({ username: data.username, password: data.password })
    } catch {
      // Auto-login failed but account was created successfully
      setLoading(false)
      setError('Account created successfully. Please log in.')
      navigate('/login')
    }
  }

  const logout = async () => {
    try {
      setLoading(true)
      await authService.logout()
      setUser(null)
      navigate('/login')
    } catch (err) {
      // Silently handle logout errors
    } finally {
      setLoading(false)
    }
  }

  const clearError = () => {
    setError(null)
  }

  const value = {
    user,
    loading,
    error,
    login,
    register,
    logout,
    clearError,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
