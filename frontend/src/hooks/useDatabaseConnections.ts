import { useState, useEffect } from "react";
import { connectionApi } from "../services/api";
import { DatabaseConnection } from "../types";

export function useDatabaseConnections() {
  const [connections, setConnections] = useState<DatabaseConnection[]>([]);
  const [selectedConnection, setSelectedConnection] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  // Load connections on mount
  useEffect(() => {
    const loadConnections = async () => {
      try {
        const conns = await connectionApi.list();
        setConnections(conns);

        // Auto-select first connection if none selected
        if (conns.length > 0 && !selectedConnection) {
          setSelectedConnection(conns[0].connection_id);
        }
      } catch (error: any) {
        setError("Failed to load connections");
      }
    };

    loadConnections();
  }, [selectedConnection]);

  const handleConnectionCreated = async (newConnection: DatabaseConnection) => {
    try {
      // Add the new connection to the state
      setConnections((prev) => [...prev, newConnection]);

      // Auto-select the newly created connection
      setSelectedConnection(newConnection.connection_id);

      // Clear any errors
      setError(null);
    } catch (err: any) {
      setError("Failed to add new connection");
    }
  };

  return {
    connections,
    selectedConnection,
    setSelectedConnection,
    error,
    setError,
    handleConnectionCreated,
  };
}
