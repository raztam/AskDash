import api from './api'
import type {
  User,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
} from '../types'
import { AxiosError } from 'axios'

// Helper to extract readable error messages from API responses
function extractErrorMessage(error: unknown): string {
  if (error instanceof AxiosError && error.response?.data) {
    const data = error.response.data

    // Handle object with field errors: {"password": ["Too short"], "email": ["Already exists"]}
    if (typeof data === 'object' && !Array.isArray(data)) {
      const messages: string[] = []
      for (const [field, errors] of Object.entries(data)) {
        if (Array.isArray(errors)) {
          messages.push(`${field}: ${errors.join(', ')}`)
        } else if (typeof errors === 'string') {
          messages.push(`${field}: ${errors}`)
        }
      }
      if (messages.length > 0) {
        return messages.join('\n')
      }
    }

    // Handle simple string error
    if (typeof data === 'string') {
      return data
    }

    // Handle {detail: "error"} format
    if (data.detail) {
      return data.detail
    }

    // Handle {message: "error"} format
    if (data.message) {
      return data.message
    }
  }

  if (error instanceof Error) {
    return error.message
  }

  return 'An unexpected error occurred'
}

export const authService = {
  async login(data: LoginRequest): Promise<LoginResponse> {
    try {
      const response = await api.post<LoginResponse>('/auth/login/', data)
      return response.data
    } catch (error) {
      throw new Error(extractErrorMessage(error))
    }
  },

  async register(data: RegisterRequest): Promise<User> {
    try {
      const response = await api.post<User>('/auth/register/', data)
      return response.data
    } catch (error) {
      throw new Error(extractErrorMessage(error))
    }
  },

  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/auth/user/')
    return response.data
  },

  async refreshToken(refreshToken: string): Promise<{ access: string }> {
    const response = await api.post<{ access: string }>('/auth/refresh/', {
      refresh: refreshToken,
    })
    return response.data
  },
}
