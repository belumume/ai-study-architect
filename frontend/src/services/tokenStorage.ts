/**
 * Token Storage Utility
 * 
 * Uses sessionStorage instead of localStorage for better security.
 * Tokens are cleared when the browser tab is closed.
 * 
 * Security Note: While sessionStorage is more secure than localStorage,
 * the ideal solution would be httpOnly cookies. This is a compromise
 * that improves security without requiring backend changes.
 */

class TokenStorage {
  private readonly ACCESS_TOKEN_KEY = 'access_token'
  private readonly REFRESH_TOKEN_KEY = 'refresh_token'

  /**
   * Store access token
   */
  setAccessToken(token: string): void {
    if (token) {
      sessionStorage.setItem(this.ACCESS_TOKEN_KEY, token)
    }
  }

  /**
   * Store refresh token
   */
  setRefreshToken(token: string): void {
    if (token) {
      sessionStorage.setItem(this.REFRESH_TOKEN_KEY, token)
    }
  }

  /**
   * Get access token
   */
  getAccessToken(): string | null {
    return sessionStorage.getItem(this.ACCESS_TOKEN_KEY)
  }

  /**
   * Get refresh token
   */
  getRefreshToken(): string | null {
    return sessionStorage.getItem(this.REFRESH_TOKEN_KEY)
  }

  /**
   * Remove access token
   */
  removeAccessToken(): void {
    sessionStorage.removeItem(this.ACCESS_TOKEN_KEY)
  }

  /**
   * Remove refresh token
   */
  removeRefreshToken(): void {
    sessionStorage.removeItem(this.REFRESH_TOKEN_KEY)
  }

  /**
   * Clear all tokens
   */
  clearTokens(): void {
    sessionStorage.removeItem(this.ACCESS_TOKEN_KEY)
    sessionStorage.removeItem(this.REFRESH_TOKEN_KEY)
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!this.getAccessToken()
  }

  /**
   * Migrate tokens from localStorage to sessionStorage (one-time migration)
   */
  migrateFromLocalStorage(): void {
    const accessToken = localStorage.getItem(this.ACCESS_TOKEN_KEY)
    const refreshToken = localStorage.getItem(this.REFRESH_TOKEN_KEY)

    if (accessToken) {
      this.setAccessToken(accessToken)
      localStorage.removeItem(this.ACCESS_TOKEN_KEY)
    }

    if (refreshToken) {
      this.setRefreshToken(refreshToken)
      localStorage.removeItem(this.REFRESH_TOKEN_KEY)
    }
  }
}

export default new TokenStorage()