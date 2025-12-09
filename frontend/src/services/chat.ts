import api from './api'
import type {
  ChatSession,
  ChatSessionListItem,
  AskQuestionRequest,
  AskQuestionResponse,
} from '../types'

export const chatService = {
  async getSessions(databaseId?: number): Promise<ChatSessionListItem[]> {
    const params = databaseId ? `?database_id=${databaseId}` : ''
    const response = await api.get<ChatSessionListItem[]>(`/sessions/${params}`)
    return response.data
  },

  async getSession(id: number): Promise<ChatSession> {
    const response = await api.get<ChatSession>(`/sessions/${id}/`)
    return response.data
  },

  async createSession(databaseId: number, title?: string): Promise<ChatSession> {
    const response = await api.post<ChatSession>('/sessions/', {
      database_connection: databaseId,
      title: title || 'New Chat',
    })
    return response.data
  },

  async deleteSession(id: number): Promise<void> {
    await api.delete(`/sessions/${id}/`)
  },

  async clearSessionMessages(id: number): Promise<void> {
    await api.delete(`/sessions/${id}/clear_messages/`)
  },

  async askQuestion(data: AskQuestionRequest): Promise<AskQuestionResponse> {
    const response = await api.post<AskQuestionResponse>('/ask/', data)
    return response.data
  },
}

export const llmService = {
  async getStatus(): Promise<{ provider: string; model: string; available: boolean }> {
    const response = await api.get<{ provider: string; model: string; available: boolean }>(
      '/llm/status/'
    )
    return response.data
  },
}
