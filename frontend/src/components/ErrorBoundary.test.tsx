import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ErrorBoundary } from './ErrorBoundary'

// Component that throws an error
const ThrowError = ({ shouldThrow = true }: { shouldThrow?: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error message')
  }
  return <div>No error</div>
}

describe('ErrorBoundary', () => {
  // Suppress console.error for these tests since we're intentionally throwing errors
  const originalError = console.error
  beforeAll(() => {
    console.error = vi.fn()
  })

  afterAll(() => {
    console.error = originalError
  })

  it('should render children when there is no error', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>
    )

    expect(screen.getByText('No error')).toBeInTheDocument()
  })

  it('should render fallback UI when error is caught', () => {
    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )

    expect(screen.getByText(/Oops! Something went wrong/i)).toBeInTheDocument()
    expect(screen.getByText(/We encountered an unexpected error/i)).toBeInTheDocument()
  })

  it('should show Try Again button', () => {
    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )

    const tryAgainButton = screen.getByRole('button', { name: /try again/i })
    expect(tryAgainButton).toBeInTheDocument()
  })

  it('should show Reload Page button', () => {
    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )

    const reloadButton = screen.getByRole('button', { name: /reload page/i })
    expect(reloadButton).toBeInTheDocument()
  })

  it('should use custom fallback when provided', () => {
    const customFallback = <div>Custom error message</div>

    render(
      <ErrorBoundary fallback={customFallback}>
        <ThrowError />
      </ErrorBoundary>
    )

    expect(screen.getByText('Custom error message')).toBeInTheDocument()
    expect(screen.queryByText(/Oops! Something went wrong/i)).not.toBeInTheDocument()
  })

  it('should sanitize error messages in development mode', () => {
    // Set DEV mode
    import.meta.env.DEV = true

    const SensitiveError = () => {
      throw new Error('Error with sk-1234567890abcdef API key')
    }

    render(
      <ErrorBoundary>
        <SensitiveError />
      </ErrorBoundary>
    )

    // Error details should be shown but sanitized
    expect(screen.queryByText(/sk-1234567890abcdef/)).not.toBeInTheDocument()
    expect(screen.getByText(/\[REDACTED_KEY\]/)).toBeInTheDocument()
  })

  it('should not show error details in production mode', () => {
    // Set production mode
    import.meta.env.DEV = false

    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )

    // Error details section should not be visible
    expect(screen.queryByText('Error Details (Development Only):')).not.toBeInTheDocument()
  })

  it('should display ErrorOutline icon', () => {
    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )

    // Check that the error icon is rendered (MUI ErrorOutline component)
    const errorIcon = document.querySelector('[data-testid="ErrorOutlineIcon"]')
    expect(errorIcon || screen.getByTestId(/error/i)).toBeTruthy()
  })
})
