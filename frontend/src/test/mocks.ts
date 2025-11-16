/**
 * Mock data and API response handlers for testing
 */

import { vi } from 'vitest'

// Mock API responses
export const mockApiResponses = {
  auth: {
    login: {
      access_token: 'mock-access-token',
      refresh_token: 'mock-refresh-token',
      token_type: 'bearer',
    },
    register: {
      id: 'new-user-id',
      email: 'newuser@example.com',
      username: 'newuser',
      full_name: 'New User',
      is_active: true,
      is_verified: false,
      is_superuser: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    me: {
      id: 'user-123',
      email: 'test@example.com',
      username: 'testuser',
      full_name: 'Test User',
      is_active: true,
      is_verified: true,
      is_superuser: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      last_login_at: new Date().toISOString(),
    },
  },
  content: {
    list: [
      {
        id: 'content-1',
        title: 'Test Document',
        file_type: 'pdf',
        file_size: 1024000,
        created_at: new Date().toISOString(),
      },
    ],
    upload: {
      id: 'content-2',
      title: 'Uploaded Document',
      file_type: 'pdf',
      file_size: 2048000,
      created_at: new Date().toISOString(),
    },
  },
  chat: {
    message: {
      role: 'assistant',
      content: 'Hello! How can I help you today?',
    },
  },
}

// Mock axios for API calls
export const createMockAxios = () => {
  return {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    patch: vi.fn(),
    request: vi.fn(),
    defaults: {
      headers: {
        common: {},
        post: {},
        get: {},
        put: {},
        patch: {},
        delete: {},
      },
    },
    interceptors: {
      request: {
        use: vi.fn(),
        eject: vi.fn(),
      },
      response: {
        use: vi.fn(),
        eject: vi.fn(),
      },
    },
  }
}

// Mock successful API responses
export const mockApiSuccess = (data: any) => ({
  data,
  status: 200,
  statusText: 'OK',
  headers: {},
  config: {} as any,
})

// Mock API errors
export const mockApiError = (message: string, status: number = 400) => ({
  response: {
    data: {
      detail: message,
    },
    status,
    statusText: 'Error',
    headers: {},
    config: {} as any,
  },
  message,
  isAxiosError: true,
})

// Mock form data
export const mockFormData = {
  login: {
    username: 'testuser@example.com',
    password: 'password123',
  },
  register: {
    email: 'newuser@example.com',
    username: 'newuser',
    full_name: 'New User',
    password: 'securePassword123!',
  },
}

// Mock file for upload testing
export const createMockFile = (
  name: string = 'test.pdf',
  size: number = 1024,
  type: string = 'application/pdf'
) => {
  const blob = new Blob(['test content'], { type })
  return new File([blob], name, { type })
}
