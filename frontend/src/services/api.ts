import axios from "axios";
import {
  DatabaseConnection,
  DatabaseConnectionRequest,
  NaturalLanguageQuery,
  QueryResult,
  QueryHistory,
  SchemaInfo,
} from "../types";

const API_BASE_URL = "http://localhost:8001/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Connection API
export const connectionApi = {
  create: async (
    request: DatabaseConnectionRequest
  ): Promise<DatabaseConnection> => {
    const response = await api.post("/connections/", request);
    return response.data;
  },

  list: async (): Promise<DatabaseConnection[]> => {
    const response = await api.get("/connections/");
    return response.data;
  },

  delete: async (connectionId: string): Promise<void> => {
    await api.delete(`/connections/${connectionId}`);
  },

  test: async (
    connectionId: string
  ): Promise<{ connection_id: string; status: string }> => {
    const response = await api.get(`/connections/${connectionId}/test`);
    return response.data;
  },
};

// Schema API
export const schemaApi = {
  getSchema: async (connectionId: string): Promise<SchemaInfo> => {
    const response = await api.get(`/schema/${connectionId}`);
    return response.data;
  },

  listTables: async (
    connectionId: string
  ): Promise<{ tables: string[]; count: number }> => {
    const response = await api.get(`/schema/${connectionId}/tables`);
    return response.data;
  },

  getTableInfo: async (
    connectionId: string,
    tableName: string
  ): Promise<any> => {
    const response = await api.get(
      `/schema/${connectionId}/tables/${tableName}`
    );
    return response.data;
  },
};

// Queries API
export const queriesApi = {
  executeNaturalLanguage: async (
    request: NaturalLanguageQuery
  ): Promise<QueryResult> => {
    const response = await api.post("/queries/", request);
    return response.data;
  },

  getHistory: async (
    connectionId?: string,
    limit: number = 50
  ): Promise<QueryHistory[]> => {
    const params = new URLSearchParams();
    if (connectionId) params.append("connection_id", connectionId);
    params.append("limit", limit.toString());

    const response = await api.get(`/queries/history?${params}`);
    return response.data;
  },

  getQueryById: async (queryId: string): Promise<QueryHistory> => {
    const response = await api.get(`/queries/${queryId}`);
    return response.data;
  },

  rerunQuery: async (queryId: string): Promise<QueryResult> => {
    const response = await api.post(`/queries/${queryId}/rerun`);
    return response.data;
  },

  deleteQuery: async (queryId: string): Promise<void> => {
    await api.delete(`/queries/${queryId}`);
  },

  executeRawSql: async (
    connectionId: string,
    sql: string
  ): Promise<QueryResult> => {
    const response = await api.post("/queries/sql", null, {
      params: { connection_id: connectionId, sql },
    });
    return response.data;
  },
};

// Export API
export const exportApi = {
  exportToCsv: async (queryId: string): Promise<void> => {
    const response = await api.post(`/exports/csv/${queryId}`, null, {
      responseType: "blob",
    });

    // Create download link
    const blob = new Blob([response.data], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `query_${queryId.substring(0, 8)}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },

  exportToJson: async (queryId: string): Promise<void> => {
    const response = await api.post(`/exports/json/${queryId}`, null, {
      responseType: "blob",
    });

    // Create download link
    const blob = new Blob([response.data], { type: "application/json" });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `query_${queryId.substring(0, 8)}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },

  getQueryTemplates: async (): Promise<any> => {
    const response = await api.get("/exports/templates");
    return response.data;
  },
};

export default api;
