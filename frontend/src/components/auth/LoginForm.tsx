import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { useAuth } from '@/contexts/AuthContext'
import { LoginCredentials } from '@/services/auth.service'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Eye, EyeOff, Loader2 } from 'lucide-react'

export const LoginForm: React.FC = () => {
  const { login, error, clearError, user } = useAuth()
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    if (user) navigate('/')
  }, [user, navigate])

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginCredentials>({
    defaultValues: { username: '', password: '', remember_me: false },
  })

  const onSubmit = async (data: LoginCredentials) => {
    try {
      setIsLoading(true)
      clearError()
      await login(data)
    } catch {
      // Error handled in context
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Card className="w-full max-w-[400px] border-border bg-surface p-8">
      <h1 className="text-center font-display text-2xl font-bold uppercase tracking-wider text-text-primary">
        Sign In
      </h1>
      <p className="mt-1 text-center font-body text-sm text-text-muted">
        Welcome back to Study Architect
      </p>

      {error && (
        <div className="mt-4 rounded-lg border border-tertiary/30 bg-tertiary/10 p-3 text-sm text-tertiary">
          {error}
          <button
            onClick={clearError}
            className="ml-2 text-text-muted hover:text-text-primary"
          >
            x
          </button>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} aria-label="Sign in form" className="mt-6 space-y-4">
        <div>
          <label htmlFor="username" className="mb-1 block font-mono text-xs uppercase tracking-widest text-text-muted">
            Username
          </label>
          <Input
            id="username"
            autoComplete="username"
            autoFocus
            className="border-border bg-raised text-text-primary placeholder:text-text-muted/50 focus-visible:ring-secondary"
            {...register('username', {
              required: 'Username is required',
              minLength: { value: 3, message: 'Username must be at least 3 characters' },
            })}
          />
          {errors.username && (
            <p className="mt-1 text-xs text-tertiary">{errors.username.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="password" className="mb-1 block font-mono text-xs uppercase tracking-widest text-text-muted">
            Password
          </label>
          <div className="relative">
            <Input
              id="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              className="border-border bg-raised pr-10 text-text-primary placeholder:text-text-muted/50 focus-visible:ring-secondary"
              {...register('password', {
                required: 'Password is required',
                minLength: { value: 6, message: 'Password must be at least 6 characters' },
              })}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary"
              aria-label="Toggle password visibility"
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {errors.password && (
            <p className="mt-1 text-xs text-tertiary">{errors.password.message}</p>
          )}
        </div>

        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            {...register('remember_me')}
            className="h-4 w-4 rounded border-border bg-raised accent-primary"
          />
          <span className="font-body text-sm text-text-muted">Remember me</span>
        </label>

        <Button
          type="submit"
          disabled={isLoading}
          className="w-full bg-primary text-void hover:bg-primary/90 disabled:opacity-50"
        >
          {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : 'Sign In'}
        </Button>

        <p className="text-center font-body text-sm text-text-muted">
          Don't have an account?{' '}
          <Link to="/register" className="text-secondary hover:underline">
            Sign up
          </Link>
        </p>
      </form>
    </Card>
  )
}
