// TypeScript type definitions for the AskDash application

export interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
}

export interface DatabaseConnection {
  id: number
  name: string
  db_type: 'postgresql' | 'mysql' | 'sqlite' | 'mariadb' | 'mssql'
  host: string | null
  port: number | null
  database_name: string
  username: string | null
  file_path: string | null
  schema_json: DatabaseSchema
  created_by: number
  created_by_username: string
  created_at: string
  updated_at: string
  is_owner: boolean
}

export interface DatabaseSchema {
  tables: {
    [tableName: string]: {
      columns: Column[]
      indexes: string[]
      primary_key: string[]
      foreign_keys: ForeignKey[]
    }
  }
  error?: string
}

export interface Column {
  name: string
  type: string
  nullable: boolean
  primary_key?: boolean
  default?: string | null
}

export interface ForeignKey {
  column: string
  references_table: string
  references_column: string
}

export interface TablePermission {
  id: number
  database_connection: number
  user: number
  user_username: string
  table_name: string
  permission_level: 'read' | 'write' | 'admin'
  granted_by: number
  granted_by_username: string
  granted_at: string
}

export interface ChatSession {
  id: number
  title: string
  database_connection: number
  database_name: string
  user: number
  messages: ChatMessage[]
  message_count: number
  created_at: string
  updated_at: string
}

export interface ChatSessionListItem {
  id: number
  title: string
  database_connection: number
  database_name: string
  message_count: number
  last_message: {
    content: string
    type: string
    created_at: string
  } | null
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  id: number
  session: number
  message_type: 'user' | 'assistant' | 'error'
  content: string
  sql_query: string | null
  query_results: Record<string, unknown>[]
  chart_type: ChartType | null
  chart_config: ChartConfig
  explanation: string | null
  insights: string | null
  created_at: string
}

export type ChartType = 'bar' | 'line' | 'pie' | 'scatter' | 'venn' | 'table' | 'none'

export interface VennSet {
  sets: string[]
  size: number
  label?: string
}

export interface ChartConfig {
  x_column?: string
  y_column?: string
  reason?: string
  sets?: VennSet[] // For Venn diagrams
}

export interface AskQuestionRequest {
  question: string
  database_id: number
  session_id?: number
  show_sql?: boolean
}

export interface AskQuestionResponse {
  answer: string
  sql_query: string | null
  results: Record<string, unknown>[]
  chart_type: ChartType | null
  chart_config: ChartConfig
  explanation: string | null
  insights: string | null
  session_id: number
  message_id: number
  error?: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access: string
  refresh: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  password2: string
  first_name?: string
  last_name?: string
}

export interface CreateDatabaseRequest {
  name: string
  db_type: DatabaseConnection['db_type']
  host?: string
  port?: number
  database_name: string
  username?: string
  password?: string
  file_path?: string
}

export interface LLMStatus {
  provider: string
  model: string
  available: boolean
}

// Permission Group Types
export interface PermissionGroupTable {
  id: number
  table_name: string
  permission_level: 'read' | 'write' | 'admin'
}

export interface UserGroupAssignment {
  id: number
  user: number
  user_username: string
  user_email: string
  group: number
  assigned_by: number
  assigned_by_username: string
  assigned_at: string
}

export interface PermissionGroup {
  id: number
  name: string
  description: string | null
  database_connection: number
  tables: PermissionGroupTable[]
  user_assignments: UserGroupAssignment[]
  table_count: number
  user_count: number
  created_by: number
  created_by_username: string
  created_at: string
  updated_at: string
}

export interface PermissionGroupListItem {
  id: number
  name: string
  description: string | null
  database_connection: number
  table_count: number
  user_count: number
  created_at: string
  updated_at: string
}

export interface CreatePermissionGroupRequest {
  name: string
  description?: string
  database_id: number
  tables?: { table_name: string; permission_level?: string }[]
}

export interface AddTablesToGroupRequest {
  tables: { table_name: string; permission_level?: string }[]
}

export interface AssignUserToGroupRequest {
  username: string
}
