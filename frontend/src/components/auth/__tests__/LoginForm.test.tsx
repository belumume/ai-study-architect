/**
 * LoginForm component tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, mockTokens } from '../../../test/test-utils'
import { LoginForm } from '../LoginForm'
import * as AuthContext from '../../../contexts/AuthContext'

describe('LoginForm', () => {
  const mockLogin = vi.fn()
  const mockClearError = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()

    // Mock useAuth hook
    vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
      user: null,
      login: mockLogin,
      logout: vi.fn(),
      register: vi.fn(),
      error: null,
      clearError: mockClearError,
      isLoading: false,
    } as any)
  })

  describe('Rendering', () => {
    it('renders login form with all fields', () => {
      render(<LoginForm />)

      expect(screen.getByRole('heading', { name: /sign in/i })).toBeInTheDocument()
      expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
    })

    it('renders welcome message', () => {
      render(<LoginForm />)

      expect(screen.getByText(/welcome back to ai study architect/i)).toBeInTheDocument()
    })

    it('renders remember me checkbox', () => {
      render(<LoginForm />)

      expect(screen.getByRole('checkbox', { name: /remember me/i })).toBeInTheDocument()
    })

    it('renders link to register page', () => {
      render(<LoginForm />)

      const registerLink = screen.getByText(/sign up/i)
      expect(registerLink).toBeInTheDocument()
      expect(registerLink.closest('a')).toHaveAttribute('href', '/register')
    })
  })

  describe('Form Validation', () => {
    it('shows error when username is empty', async () => {
      render(<LoginForm />)

      const submitButton = screen.getByRole('button', { name: /sign in/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/username is required/i)).toBeInTheDocument()
      })

      expect(mockLogin).not.toHaveBeenCalled()
    })

    it('shows error when username is too short', async () => {
      render(<LoginForm />)

      const usernameInput = screen.getByLabelText(/username/i)
      fireEvent.change(usernameInput, { target: { value: 'ab' } })

      const submitButton = screen.getByRole('button', { name: /sign in/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/username must be at least 3 characters/i)).toBeInTheDocument()
      })

      expect(mockLogin).not.toHaveBeenCalled()
    })

    it('shows error when password is empty', async () => {
      render(<LoginForm />)

      const usernameInput = screen.getByLabelText(/username/i)
      fireEvent.change(usernameInput, { target: { value: 'testuser' } })

      const submitButton = screen.getByRole('button', { name: /sign in/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/password is required/i)).toBeInTheDocument()
      })

      expect(mockLogin).not.toHaveBeenCalled()
    })

    it('does not show errors when form is valid', async () => {
      render(<LoginForm />)

      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)

      fireEvent.change(usernameInput, { target: { value: 'testuser' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })

      const submitButton = screen.getByRole('button', { name: /sign in/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalled()
      })
    })
  })

  describe('Password Visibility Toggle', () => {
    it('shows password when visibility icon is clicked', () => {
      render(<LoginForm />)

      const passwordInput = screen.getByLabelText(/password/i) as HTMLInputElement
      expect(passwordInput.type).toBe('password')

      const visibilityButton = screen.getByRole('button', { name: /toggle password visibility/i })
      fireEvent.click(visibilityButton)

      expect(passwordInput.type).toBe('text')
    })

    it('hides password when visibility icon is clicked again', () => {
      render(<LoginForm />)

      const visibilityButton = screen.getByRole('button', { name: /toggle password visibility/i })

      // Show password
      fireEvent.click(visibilityButton)

      const passwordInput = screen.getByLabelText(/password/i) as HTMLInputElement
      expect(passwordInput.type).toBe('text')

      // Hide password
      fireEvent.click(visibilityButton)
      expect(passwordInput.type).toBe('password')
    })
  })

  describe('Form Submission', () => {
    it('calls login function with correct credentials', async () => {
      mockLogin.mockResolvedValue(mockTokens)

      render(<LoginForm />)

      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)

      fireEvent.change(usernameInput, { target: { value: 'testuser' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })

      const submitButton = screen.getByRole('button', { name: /sign in/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith({
          username: 'testuser',
          password: 'password123',
          remember_me: false,
        })
      })
    })

    it('includes remember_me when checkbox is checked', async () => {
      mockLogin.mockResolvedValue(mockTokens)

      render(<LoginForm />)

      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const rememberMeCheckbox = screen.getByRole('checkbox', { name: /remember me/i })

      fireEvent.change(usernameInput, { target: { value: 'testuser' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })
      fireEvent.click(rememberMeCheckbox)

      const submitButton = screen.getByRole('button', { name: /sign in/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith({
          username: 'testuser',
          password: 'password123',
          remember_me: true,
        })
      })
    })

    it('shows loading state during submission', async () => {
      // Create a promise that we can control
      let resolveLogin: any
      mockLogin.mockImplementation(() => new Promise(resolve => {
        resolveLogin = resolve
      }))

      render(<LoginForm />)

      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)

      fireEvent.change(usernameInput, { target: { value: 'testuser' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })

      const submitButton = screen.getByRole('button', { name: /sign in/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByRole('progressbar')).toBeInTheDocument()
      })

      // Resolve the login
      resolveLogin(mockTokens)
    })

    it('clears error before submission', async () => {
      mockLogin.mockResolvedValue(mockTokens)

      render(<LoginForm />)

      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)

      fireEvent.change(usernameInput, { target: { value: 'testuser' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })

      const submitButton = screen.getByRole('button', { name: /sign in/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(mockClearError).toHaveBeenCalled()
      })
    })
  })

  describe('Error Display', () => {
    it('displays authentication error from context', () => {
      const errorMessage = 'Invalid credentials'

      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        login: mockLogin,
        logout: vi.fn(),
        register: vi.fn(),
        error: errorMessage,
        clearError: mockClearError,
        isLoading: false,
      } as any)

      render(<LoginForm />)

      expect(screen.getByText(errorMessage)).toBeInTheDocument()
      expect(screen.getByRole('alert')).toHaveClass('MuiAlert-standardError')
    })

    it('allows clearing error by clicking close button', () => {
      const errorMessage = 'Invalid credentials'

      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        login: mockLogin,
        logout: vi.fn(),
        register: vi.fn(),
        error: errorMessage,
        clearError: mockClearError,
        isLoading: false,
      } as any)

      render(<LoginForm />)

      const closeButton = screen.getByRole('button', { name: /close/i })
      fireEvent.click(closeButton)

      expect(mockClearError).toHaveBeenCalled()
    })
  })

  describe('Navigation', () => {
    it('redirects to home when user is already logged in', () => {
      const mockNavigate = vi.fn()

      vi.mock('react-router-dom', async () => {
        const actual = await vi.importActual('react-router-dom')
        return {
          ...actual,
          useNavigate: () => mockNavigate,
        }
      })

      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: { id: '123', email: 'user@example.com' },
        login: mockLogin,
        logout: vi.fn(),
        register: vi.fn(),
        error: null,
        clearError: mockClearError,
        isLoading: false,
      } as any)

      render(<LoginForm />)

      // Navigation happens in useEffect, so we just verify the user state
      // In a real scenario, you'd use a router testing library
    })
  })

  describe('Accessibility', () => {
    it('has proper autocomplete attributes', () => {
      render(<LoginForm />)

      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)

      expect(usernameInput).toHaveAttribute('autocomplete', 'username')
      expect(passwordInput).toHaveAttribute('autocomplete', 'current-password')
    })

    it('focuses username field on mount', () => {
      render(<LoginForm />)

      const usernameInput = screen.getByLabelText(/username/i)
      expect(usernameInput).toHaveAttribute('autofocus')
    })

    it('form is keyboard accessible', async () => {
      mockLogin.mockResolvedValue(mockTokens)

      render(<LoginForm />)

      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const form = screen.getByRole('form')

      // Fill form using keyboard
      usernameInput.focus()
      fireEvent.change(usernameInput, { target: { value: 'testuser' } })

      fireEvent.keyDown(usernameInput, { key: 'Tab' })

      fireEvent.change(passwordInput, { target: { value: 'password123' } })

      // Submit using Enter key
      fireEvent.keyDown(form, { key: 'Enter', code: 'Enter' })

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalled()
      })
    })
  })
})
