import React, { useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Alert,
  CircularProgress,
} from "@mui/material";
import { connectionApi } from "../services/api";
import { DatabaseConnection } from "../types";

interface DatabaseConnectionDialogProps {
  open: boolean;
  onClose: () => void;
  onConnectionCreated: (connection: DatabaseConnection) => void;
}

export const DatabaseConnectionDialog: React.FC<
  DatabaseConnectionDialogProps
> = ({ open, onClose, onConnectionCreated }) => {
  const [formData, setFormData] = useState({
    connection_id: "",
    db_type: "",
    host: "",
    port: "",
    username: "",
    password: "",
    database: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const generateConnectionName = () => {
    const { db_type, database, host } = formData;
    if (db_type && database) {
      const hostPart = host ? ` (${host})` : "";
      const name = `${db_type.toUpperCase()} - ${database}${hostPart}`;
      setFormData((prev) => ({ ...prev, connection_id: name }));
    }
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      setError(null);

      // Generate connection ID if not provided
      const connectionId =
        formData.connection_id ||
        `${formData.db_type}_${formData.database}_${Date.now()}`;

      const connectionData = {
        ...formData,
        connection_id: connectionId,
        port: formData.port ? parseInt(formData.port, 10) : undefined,
      };

      // Create the connection and get the response
      const createdConnection = await connectionApi.create(connectionData);

      // Pass the created connection back to parent
      onConnectionCreated(createdConnection);
      onClose();

      // Reset form
      setFormData({
        connection_id: "",
        db_type: "",
        host: "",
        port: "",
        username: "",
        password: "",
        database: "",
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to create connection");
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setFormData({
      connection_id: "",
      db_type: "",
      host: "",
      port: "",
      username: "",
      password: "",
      database: "",
    });
    setError(null);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Add Database Connection</DialogTitle>
      <DialogContent>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2, mt: 1 }}>
          {error && <Alert severity="error">{error}</Alert>}

          <Box sx={{ display: "flex", gap: 1, alignItems: "end" }}>
            <TextField
              label="Connection Name"
              value={formData.connection_id}
              onChange={(e) =>
                handleInputChange("connection_id", e.target.value)
              }
              placeholder="e.g., Production MySQL, Local SQLite"
              helperText="A friendly name for this connection"
              sx={{ flex: 1 }}
            />
            <Button
              variant="outlined"
              onClick={generateConnectionName}
              disabled={!formData.db_type || !formData.database}
              size="small"
            >
              Auto-generate
            </Button>
          </Box>

          <FormControl>
            <InputLabel>Database Type</InputLabel>
            <Select
              value={formData.db_type}
              label="Database Type"
              onChange={(e) => handleInputChange("db_type", e.target.value)}
            >
              <MenuItem value="mysql">MySQL</MenuItem>
              <MenuItem value="postgresql">PostgreSQL</MenuItem>
              <MenuItem value="sqlite">SQLite</MenuItem>
              <MenuItem value="mariadb">MariaDB</MenuItem>
            </Select>
          </FormControl>

          {formData.db_type === "sqlite" ? (
            <TextField
              label="Database File Path"
              value={formData.database}
              onChange={(e) => handleInputChange("database", e.target.value)}
              placeholder="/path/to/database.db"
            />
          ) : (
            <>
              <TextField
                label="Host"
                value={formData.host}
                onChange={(e) => handleInputChange("host", e.target.value)}
                placeholder="localhost"
              />
              <TextField
                label="Port"
                value={formData.port}
                onChange={(e) => handleInputChange("port", e.target.value)}
                placeholder="3306"
              />
              <TextField
                label="Database Name"
                value={formData.database}
                onChange={(e) => handleInputChange("database", e.target.value)}
              />
              <TextField
                label="Username"
                value={formData.username}
                onChange={(e) => handleInputChange("username", e.target.value)}
              />
              <TextField
                label="Password"
                type="password"
                value={formData.password}
                onChange={(e) => handleInputChange("password", e.target.value)}
              />
            </>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading || !formData.db_type || !formData.database}
        >
          {loading ? <CircularProgress size={20} /> : "Connect"}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default DatabaseConnectionDialog;
