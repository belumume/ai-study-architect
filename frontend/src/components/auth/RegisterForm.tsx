import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { useAuth } from '@/contexts/AuthContext'
import { RegisterData } from '@/services/auth.service'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Eye, EyeOff, Loader2 } from 'lucide-react'

interface RegisterFormData extends RegisterData {
  confirmPassword: string
}

export const RegisterForm: React.FC = () => {
  const { register: registerUser, error, clearError } = useAuth()
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<RegisterFormData>({
    defaultValues: {
      username: '',
      email: '',
      password: '',
      confirmPassword: '',
      full_name: '',
    },
  })

  const password = watch('password')

  const onSubmit = async (data: RegisterFormData) => {
    try {
      setIsLoading(true)
      clearError()
      const { confirmPassword, ...registerData } = data
      await registerUser(registerData)
    } catch {
      // Error handled in context
    } finally {
      setIsLoading(false)
    }
  }

  const inputClass =
    'border-border bg-raised text-text-primary placeholder:text-text-muted/50 focus-visible:ring-secondary'
  const labelClass =
    'mb-1 block font-mono text-xs uppercase tracking-widest text-text-muted'

  return (
    <Card className="w-full max-w-[400px] border-border bg-surface p-8">
      <h1 className="text-center font-display text-2xl font-bold uppercase tracking-wider text-text-primary">
        Sign Up
      </h1>
      <p className="mt-1 text-center font-body text-sm text-text-muted">
        Create your Study Architect account
      </p>

      {error && (
        <div className="mt-4 rounded-lg border border-tertiary/30 bg-tertiary/10 p-3 text-sm text-tertiary">
          {error}
          <button onClick={clearError} className="ml-2 text-text-muted hover:text-text-primary">
            x
          </button>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4">
        <div>
          <label htmlFor="username" className={labelClass}>Username</label>
          <Input
            id="username"
            autoComplete="username"
            autoFocus
            className={inputClass}
            {...register('username', {
              required: 'Username is required',
              minLength: { value: 3, message: 'Username must be at least 3 characters' },
              pattern: {
                value: /^[a-zA-Z0-9_-]+$/,
                message: 'Letters, numbers, underscores, and hyphens only',
              },
            })}
          />
          {errors.username && <p className="mt-1 text-xs text-tertiary">{errors.username.message}</p>}
        </div>

        <div>
          <label htmlFor="email" className={labelClass}>Email</label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            className={inputClass}
            {...register('email', {
              required: 'Email is required',
              pattern: { value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i, message: 'Invalid email' },
            })}
          />
          {errors.email && <p className="mt-1 text-xs text-tertiary">{errors.email.message}</p>}
        </div>

        <div>
          <label htmlFor="full_name" className={labelClass}>Full Name (optional)</label>
          <Input
            id="full_name"
            autoComplete="name"
            className={inputClass}
            {...register('full_name')}
          />
        </div>

        <div>
          <label htmlFor="password" className={labelClass}>Password</label>
          <div className="relative">
            <Input
              id="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="new-password"
              className={`${inputClass} pr-10`}
              {...register('password', {
                required: 'Password is required',
                minLength: { value: 8, message: 'At least 8 characters' },
                pattern: {
                  value: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,
                  message: 'Needs uppercase, lowercase, number, and special character',
                },
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
          {errors.password && <p className="mt-1 text-xs text-tertiary">{errors.password.message}</p>}
        </div>

        <div>
          <label htmlFor="confirmPassword" className={labelClass}>Confirm Password</label>
          <div className="relative">
            <Input
              id="confirmPassword"
              type={showConfirmPassword ? 'text' : 'password'}
              autoComplete="new-password"
              className={`${inputClass} pr-10`}
              {...register('confirmPassword', {
                required: 'Please confirm your password',
                validate: (value) => value === password || 'Passwords do not match',
              })}
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary"
              aria-label="Toggle password visibility"
            >
              {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {errors.confirmPassword && <p className="mt-1 text-xs text-tertiary">{errors.confirmPassword.message}</p>}
        </div>

        <Button
          type="submit"
          disabled={isLoading}
          className="w-full bg-primary text-void hover:bg-primary/90 disabled:opacity-50"
        >
          {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : 'Sign Up'}
        </Button>

        <p className="text-center font-body text-sm text-text-muted">
          Already have an account?{' '}
          <Link to="/login" className="text-secondary hover:underline">
            Sign in
          </Link>
        </p>
      </form>
    </Card>
  )
}
