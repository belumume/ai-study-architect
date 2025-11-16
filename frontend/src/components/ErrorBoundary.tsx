import { Component, ErrorInfo, ReactNode } from 'react'
import { Box, Typography, Button, Paper, Alert } from '@mui/material'
import { ErrorOutline, Refresh } from '@mui/icons-material'

/**
 * Sanitize error messages to prevent sensitive information leakage
 */
function sanitizeErrorMessage(message: string): string {
  if (!message) return message

  // Redact potential API keys (patterns like sk-xxx, api_xxx, key_xxx)
  let sanitized = message.replace(/\b(sk|api|key)[-_][a-zA-Z0-9]{10,}\b/gi, '[REDACTED_KEY]')

  // Redact potential file paths
  sanitized = sanitized.replace(/([A-Z]:\\|\/)[^\s)]+/g, '[REDACTED_PATH]')

  // Redact potential URLs with credentials
  sanitized = sanitized.replace(/https?:\/\/[^:]+:[^@]+@[^\s]+/g, '[REDACTED_URL]')

  return sanitized
}

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

/**
 * Error Boundary component to catch React errors and display user-friendly fallback UI
 *
 * Wrap components that might throw errors:
 * <ErrorBoundary>
 *   <YourComponent />
 * </ErrorBoundary>
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    }
  }

  static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
      errorInfo: null,
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error details for debugging
    console.error('Error Boundary caught an error:', error, errorInfo)

    // Update state with error details
    this.setState({
      error,
      errorInfo,
    })

    // You could also log to an error reporting service here
    // e.g., Sentry.captureException(error, { extra: errorInfo })
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    })
  }

  handleReload = () => {
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      // Custom fallback UI if provided
      if (this.props.fallback) {
        return this.props.fallback
      }

      // Default fallback UI
      return (
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '400px',
            p: 3,
          }}
        >
          <Paper
            elevation={3}
            sx={{
              p: 4,
              maxWidth: 600,
              textAlign: 'center',
            }}
          >
            <ErrorOutline
              color="error"
              sx={{ fontSize: 64, mb: 2 }}
            />

            <Typography variant="h5" gutterBottom>
              Oops! Something went wrong
            </Typography>

            <Typography variant="body1" color="text.secondary" paragraph>
              We encountered an unexpected error. Don't worry, your data is safe.
              Try refreshing the page or click the button below to try again.
            </Typography>

            {import.meta.env.DEV && this.state.error && (
              <Alert severity="error" sx={{ mt: 2, mb: 2, textAlign: 'left' }}>
                <Typography variant="subtitle2" gutterBottom>
                  Error Details (Development Only):
                </Typography>
                <Typography variant="body2" component="pre" sx={{ fontSize: '0.75rem' }}>
                  {sanitizeErrorMessage(this.state.error.toString())}
                </Typography>
                {this.state.errorInfo && (
                  <Typography variant="body2" component="pre" sx={{ fontSize: '0.75rem', mt: 1 }}>
                    {this.state.errorInfo.componentStack}
                  </Typography>
                )}
              </Alert>
            )}

            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mt: 3 }}>
              <Button
                variant="outlined"
                startIcon={<Refresh />}
                onClick={this.handleReset}
              >
                Try Again
              </Button>
              <Button
                variant="contained"
                onClick={this.handleReload}
              >
                Reload Page
              </Button>
            </Box>
          </Paper>
        </Box>
      )
    }

    return this.props.children
  }
}

/**
 * Hook-based error handler for functional components
 * Use this for handling async errors that Error Boundary can't catch
 */
export function useErrorHandler() {
  const handleError = (error: unknown, userMessage?: string) => {
    console.error('Error occurred:', error)

    // Determine user-friendly message
    let message = userMessage || 'An unexpected error occurred'

    if (error instanceof Error) {
      // Check for common error types and provide better messages
      if (error.message.includes('Network')) {
        message = 'Network error. Please check your internet connection.'
      } else if (error.message.includes('timeout')) {
        message = 'Request timed out. Please try again.'
      } else if (error.message.includes('401') || error.message.includes('Unauthorized')) {
        message = 'Your session has expired. Please log in again.'
      } else if (error.message.includes('403') || error.message.includes('Forbidden')) {
        message = 'You do not have permission to perform this action.'
      } else if (error.message.includes('404') || error.message.includes('Not Found')) {
        message = 'The requested resource was not found.'
      } else if (error.message.includes('500') || error.message.includes('Server Error')) {
        message = 'Server error. Please try again later.'
      }
    }

    return message
  }

  return { handleError }
}
