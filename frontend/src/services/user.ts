import api from './api'
import type { User } from '../types'

export const userService = {
  async listUsers(): Promise<User[]> {
    const response = await api.get<User[]>('/users/')
    return response.data
  },

  async searchUsers(query: string): Promise<User[]> {
    const response = await api.get<User[]>(`/users/search/?q=${encodeURIComponent(query)}`)
    return response.data
  },
}
