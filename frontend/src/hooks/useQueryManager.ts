import { useState, useEffect } from "react";
import { queriesApi } from "../services/api";
import { QueryHistory, QueryResult, NaturalLanguageQuery } from "../types";

export function useQueryManager(selectedConnection: string) {
  const [queryHistory, setQueryHistory] = useState<QueryHistory[]>([]);
  const [currentResult, setCurrentResult] = useState<QueryResult | null>(null);
  const [selectedQueryId, setSelectedQueryId] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [snackbarMessage, setSnackbarMessage] = useState<string>("");

  // Load query history when connection changes
  useEffect(() => {
    if (selectedConnection) {
      const loadQueryHistory = async () => {
        try {
          const history = await queriesApi.getHistory(selectedConnection);
          setQueryHistory(history);
        } catch (error: any) {
          console.error("Failed to load query history:", error);
        }
      };

      loadQueryHistory();
    }
  }, [selectedConnection]);

  const handleQuerySubmit = async (query: string) => {
    if (!selectedConnection) {
      setError("Please select a database connection first");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const request: NaturalLanguageQuery = {
        query,
        connection_id: selectedConnection,
      };

      const result = await queriesApi.executeNaturalLanguage(request);
      setCurrentResult(result);
      setSelectedQueryId(result.query_id);

      // Add new query to history
      const newHistoryItem: QueryHistory = {
        query_id: result.query_id,
        original_query: query,
        generated_sql: result.generated_sql,
        timestamp: result.timestamp,
        connection_id: selectedConnection,
        execution_time: result.execution_time,
        row_count: result.row_count,
        visualization_type: result.visualization_type,
      };
      setQueryHistory((prev) => [newHistoryItem, ...prev]);

      setSnackbarMessage("Query executed successfully!");
    } catch (error: any) {
      setError(error.response?.data?.detail || "Failed to execute query");
    } finally {
      setLoading(false);
    }
  };

  const handleQuerySelect = async (query: QueryHistory) => {
    setLoading(true);
    setError(null);

    try {
      // Get the full query result data
      const result = await queriesApi.rerunQuery(query.query_id);
      setCurrentResult(result);
      setSelectedQueryId(query.query_id);
      setSnackbarMessage("Query loaded successfully!");
    } catch (error: any) {
      setError(error.response?.data?.detail || "Failed to load query");
    } finally {
      setLoading(false);
    }
  };

  const handleQueryRerun = async (queryId: string) => {
    setLoading(true);
    setError(null);

    try {
      const result = await queriesApi.rerunQuery(queryId);
      setCurrentResult(result);
      setSelectedQueryId(result.query_id);

      // Update the timestamp in history for the rerun query
      setQueryHistory((prev) =>
        prev.map((q) =>
          q.query_id === queryId
            ? { ...q, timestamp: new Date().toISOString() }
            : q
        )
      );

      setSnackbarMessage("Query rerun successfully!");
    } catch (error: any) {
      setError(error.response?.data?.detail || "Failed to rerun query");
    } finally {
      setLoading(false);
    }
  };

  const handleQueryDelete = async (queryId: string) => {
    try {
      await queriesApi.deleteQuery(queryId);

      // Remove from local state
      setQueryHistory((prev) => prev.filter((q) => q.query_id !== queryId));

      // Clear current result if it's the deleted query
      if (selectedQueryId === queryId) {
        setCurrentResult(null);
        setSelectedQueryId("");
      }

      setSnackbarMessage("Query deleted successfully!");
    } catch (error: any) {
      setError("Failed to delete query");
    }
  };

  return {
    queryHistory,
    currentResult,
    selectedQueryId,
    loading,
    error,
    snackbarMessage,
    setError,
    setSnackbarMessage,
    handleQuerySubmit,
    handleQuerySelect,
    handleQueryRerun,
    handleQueryDelete,
  };
}
