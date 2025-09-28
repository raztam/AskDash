export interface DatabaseConnection {
  connection_id: string;
  db_type: string;
  database: string;
  status: string;
  connected_at?: string;
}

export interface DatabaseConnectionRequest {
  connection_id: string;
  db_type: string;
  host?: string;
  port?: number;
  database: string;
  username?: string;
  password?: string;
  connection_string?: string;
}

export interface NaturalLanguageQuery {
  query: string;
  connection_id: string;
  context?: Record<string, any>;
}

export interface QueryResult {
  query_id: string;
  original_query: string;
  generated_sql: string;
  data: Record<string, any>[];
  columns: string[];
  row_count: number;
  execution_time: number;
  visualization_type: string;
  timestamp: string;
}

export interface QueryHistory {
  query_id: string;
  original_query: string;
  generated_sql: string;
  connection_id: string;
  timestamp: string;
  execution_time: number;
  row_count: number;
  visualization_type: string;
}

export interface SchemaInfo {
  tables: Record<string, TableInfo>;
  database_type: string;
  last_updated: string;
}

export interface TableInfo {
  columns: ColumnInfo[];
  foreign_keys: ForeignKeyInfo[];
  indexes: IndexInfo[];
}

export interface ColumnInfo {
  name: string;
  type: string;
  nullable: boolean;
  default?: any;
  primary_key: boolean;
}

export interface ForeignKeyInfo {
  constrained_columns: string[];
  referred_table: string;
  referred_columns: string[];
}

export interface IndexInfo {
  name: string;
  column_names: string[];
  unique: boolean;
}

export type VisualizationType =
  | "table"
  | "bar_chart"
  | "line_chart"
  | "pie_chart"
  | "kpi";
