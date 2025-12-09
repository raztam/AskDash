import api from './api'
import type {
  DatabaseConnection,
  CreateDatabaseRequest,
  TablePermission,
  PermissionGroup,
  CreatePermissionGroupRequest,
  AddTablesToGroupRequest,
  AssignUserToGroupRequest,
} from '../types'

export const databaseService = {
  async getAll(): Promise<DatabaseConnection[]> {
    const response = await api.get<DatabaseConnection[]>('/databases/')
    return response.data
  },

  async getById(id: number): Promise<DatabaseConnection> {
    const response = await api.get<DatabaseConnection>(`/databases/${id}/`)
    return response.data
  },

  async create(data: CreateDatabaseRequest): Promise<DatabaseConnection> {
    const response = await api.post<DatabaseConnection>('/databases/', data)
    return response.data
  },

  async update(id: number, data: Partial<CreateDatabaseRequest>): Promise<DatabaseConnection> {
    const response = await api.patch<DatabaseConnection>(`/databases/${id}/`, data)
    return response.data
  },

  async delete(id: number): Promise<void> {
    await api.delete(`/databases/${id}/`)
  },

  async testConnection(id: number): Promise<{ success: boolean; message: string }> {
    const response = await api.post<{ success: boolean; message: string }>(
      `/databases/${id}/test/`
    )
    return response.data
  },

  async refreshSchema(id: number): Promise<{ success: boolean; schema: unknown }> {
    const response = await api.post<{ success: boolean; schema: unknown }>(
      `/databases/${id}/refresh_schema/`
    )
    return response.data
  },

  async getTables(id: number): Promise<{ tables: string[] }> {
    const response = await api.get<{ tables: string[] }>(`/databases/${id}/tables/`)
    return response.data
  },

  // Permissions
  async getPermissions(databaseId: number): Promise<TablePermission[]> {
    const response = await api.get<TablePermission[]>(
      `/permissions/by_database/?database_id=${databaseId}`
    )
    return response.data
  },

  async grantPermission(data: {
    database_id: number
    username: string
    table_name: string
    permission_level: 'read' | 'write' | 'admin'
  }): Promise<TablePermission> {
    const response = await api.post<TablePermission>('/permissions/grant/', data)
    return response.data
  },

  async revokePermission(data: {
    database_id: number
    username: string
    table_name: string
  }): Promise<{ deleted: boolean }> {
    const response = await api.post<{ deleted: boolean }>('/permissions/revoke/', data)
    return response.data
  },

  // Permission Groups
  async getPermissionGroups(databaseId: number): Promise<PermissionGroup[]> {
    const response = await api.get<PermissionGroup[]>(
      `/permission-groups/by_database/?database_id=${databaseId}`
    )
    return response.data
  },

  async createPermissionGroup(data: CreatePermissionGroupRequest): Promise<PermissionGroup> {
    const response = await api.post<PermissionGroup>('/permission-groups/create_group/', data)
    return response.data
  },

  async deletePermissionGroup(groupId: number): Promise<void> {
    await api.delete(`/permission-groups/${groupId}/`)
  },

  async addTablesToGroup(
    groupId: number,
    data: AddTablesToGroupRequest
  ): Promise<{ added: unknown[]; group: PermissionGroup }> {
    const response = await api.post<{ added: unknown[]; group: PermissionGroup }>(
      `/permission-groups/${groupId}/add_tables/`,
      data
    )
    return response.data
  },

  async removeTableFromGroup(
    groupId: number,
    tableName: string
  ): Promise<{ deleted: boolean; group: PermissionGroup }> {
    const response = await api.post<{ deleted: boolean; group: PermissionGroup }>(
      `/permission-groups/${groupId}/remove_table/`,
      { table_name: tableName }
    )
    return response.data
  },

  async assignUserToGroup(
    groupId: number,
    data: AssignUserToGroupRequest
  ): Promise<{ assignment: unknown; created: boolean; group: PermissionGroup }> {
    const response = await api.post<{ assignment: unknown; created: boolean; group: PermissionGroup }>(
      `/permission-groups/${groupId}/assign_user/`,
      data
    )
    return response.data
  },

  async removeUserFromGroup(
    groupId: number,
    username: string
  ): Promise<{ deleted: boolean; group: PermissionGroup }> {
    const response = await api.post<{ deleted: boolean; group: PermissionGroup }>(
      `/permission-groups/${groupId}/remove_user/`,
      { username }
    )
    return response.data
  },
}
