import React, { useState } from "react";
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  Button,
  Container,
  Paper,
  Drawer,
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Snackbar,
} from "@mui/material";
import {
  Add as AddIcon,
  Menu as MenuIcon,
  Storage as StorageIcon,
} from "@mui/icons-material";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";

import QueryInput from "./components/QueryInput";
import DataVisualizer from "./components/DataVisualizer";
import QueryHistorySidebar from "./components/QueryHistorySidebar";
import DatabaseConnectionDialog from "./components/DatabaseConnectionDialog";

import { useDatabaseConnections } from "./hooks/useDatabaseConnections";
import { useQueryManager } from "./hooks/useQueryManager";
import { QueryHistory } from "./types";

const theme = createTheme({
  palette: {
    primary: {
      main: "#9ACD32",
    },
    secondary: {
      main: "#7CB342",
    },
  },
});

const DRAWER_WIDTH = 350;

function App() {
  // Custom hooks for state management
  const {
    connections,
    selectedConnection,
    setSelectedConnection,
    error: connectionError,
    setError: setConnectionError,
    handleConnectionCreated,
  } = useDatabaseConnections();

  const {
    queryHistory,
    currentResult,
    selectedQueryId,
    loading,
    error: queryError,
    snackbarMessage,
    setError: setQueryError,
    setSnackbarMessage,
    handleQuerySubmit,
    handleQuerySelect,
    handleQueryRerun,
    handleQueryDelete,
  } = useQueryManager(selectedConnection);

  // UI state
  const [connectionDialogOpen, setConnectionDialogOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showQuery, setShowQuery] = useState(false);

  // Combine errors from both hooks
  const error = connectionError || queryError;
  const setError = (errorMessage: string | null) => {
    setConnectionError(errorMessage);
    setQueryError(errorMessage);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: "flex", minHeight: "100vh" }}>
        <AppBar
          position="fixed"
          sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}
        >
          <Toolbar>
            <IconButton
              color="inherit"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              edge="start"
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>

            <StorageIcon sx={{ mr: 1 }} />
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              AskDash - AI Database Dashboard
            </Typography>

            <FormControl size="small" sx={{ minWidth: 200, mr: 2 }}>
              <InputLabel sx={{ color: "white" }}>Database</InputLabel>
              <Select
                value={selectedConnection}
                onChange={(e) => setSelectedConnection(e.target.value)}
                sx={{
                  color: "white",
                  "& .MuiOutlinedInput-notchedOutline": {
                    borderColor: "rgba(255, 255, 255, 0.23)",
                  },
                  "&:hover .MuiOutlinedInput-notchedOutline": {
                    borderColor: "rgba(255, 255, 255, 0.5)",
                  },
                }}
              >
                {connections.map((conn) => (
                  <MenuItem key={conn.connection_id} value={conn.connection_id}>
                    {conn.connection_id} ({conn.db_type})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Button
              color="inherit"
              startIcon={<AddIcon />}
              onClick={() => setConnectionDialogOpen(true)}
            >
              Add Database
            </Button>
          </Toolbar>
        </AppBar>

        <Drawer
          variant="persistent"
          anchor="left"
          open={sidebarOpen}
          sx={{
            width: DRAWER_WIDTH,
            flexShrink: 0,
            "& .MuiDrawer-paper": {
              width: DRAWER_WIDTH,
              boxSizing: "border-box",
              mt: 8,
            },
          }}
        >
          <Box sx={{ p: 2, borderBottom: "1px solid #eee" }}>
            <Typography variant="h6" color="primary">
              Query History
            </Typography>
          </Box>
          <QueryHistorySidebar
            queries={queryHistory}
            selectedQueryId={selectedQueryId}
            onQuerySelect={handleQuerySelect}
            onQueryRerun={handleQueryRerun}
            onQueryDelete={handleQueryDelete}
          />
        </Drawer>

        <Box
          component="main"
          sx={{
            flexGrow: 1,
            mt: 8,
            ml: sidebarOpen ? `${DRAWER_WIDTH}px` : 0,
            transition: "margin-left 0.2s",
          }}
        >
          <Container maxWidth="xl" sx={{ py: 3 }}>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
              <Box>
                <QueryInput
                  onSubmit={handleQuerySubmit}
                  loading={loading}
                  error={error}
                />
              </Box>

              {currentResult && (
                <Box>
                  <Paper sx={{ p: 3 }}>
                    <Typography variant="h6" sx={{ mb: 2, color: "#333" }}>
                      Query Result
                    </Typography>
                    <Box
                      sx={{
                        mb: 2,
                        p: 2,
                        backgroundColor: "#f5f5f5",
                        borderRadius: 1,
                      }}
                    >
                      <Typography
                        variant="body2"
                        color="textSecondary"
                        sx={{ mb: 1 }}
                      >
                        Query:
                      </Typography>
                      <Typography variant="body1">
                        {currentResult.original_query}
                      </Typography>
                      {/* Show SQL toggle button */}
                      <Button
                        variant="outlined"
                        size="small"
                        sx={{ mt: 2 }}
                        onClick={() => setShowQuery((prev) => !prev)}
                      >
                        {showQuery ? "Hide SQL" : "Show SQL"}
                      </Button>
                      {showQuery && currentResult.generated_sql && (
                        <Box sx={{ mt: 2 }}>
                          <Typography variant="body2" color="textSecondary">
                            SQL Query:
                          </Typography>
                          <Paper sx={{ p: 2, backgroundColor: "#fafafa" }}>
                            <pre style={{ margin: 0, fontSize: 14 }}>
                              {currentResult.generated_sql}
                            </pre>
                          </Paper>
                        </Box>
                      )}
                    </Box>
                    <DataVisualizer result={currentResult} />
                  </Paper>
                </Box>
              )}

              {!currentResult && !loading && selectedConnection && (
                <Box>
                  <Paper sx={{ p: 6, textAlign: "center" }}>
                    <StorageIcon sx={{ fontSize: 64, color: "#ccc", mb: 2 }} />
                    <Typography
                      variant="h5"
                      color="textSecondary"
                      sx={{ mb: 1 }}
                    >
                      Ready to explore your data
                    </Typography>
                    <Typography variant="body1" color="textSecondary">
                      Ask a question about your database using natural language.
                    </Typography>
                  </Paper>
                </Box>
              )}

              {!selectedConnection && connections.length === 0 && (
                <Box>
                  <Paper sx={{ p: 6, textAlign: "center" }}>
                    <StorageIcon sx={{ fontSize: 64, color: "#ccc", mb: 2 }} />
                    <Typography
                      variant="h5"
                      color="textSecondary"
                      sx={{ mb: 2 }}
                    >
                      Connect to your database
                    </Typography>
                    <Typography
                      variant="body1"
                      color="textSecondary"
                      sx={{ mb: 3 }}
                    >
                      Get started by connecting to your database. We support
                      MySQL, PostgreSQL, MariaDB, and SQLite.
                    </Typography>
                    <Button
                      variant="contained"
                      startIcon={<AddIcon />}
                      onClick={() => setConnectionDialogOpen(true)}
                      size="large"
                    >
                      Add Database Connection
                    </Button>
                  </Paper>
                </Box>
              )}
            </Box>
          </Container>
        </Box>

        <DatabaseConnectionDialog
          open={connectionDialogOpen}
          onClose={() => setConnectionDialogOpen(false)}
          onConnectionCreated={handleConnectionCreated}
        />

        <Snackbar
          open={!!snackbarMessage}
          autoHideDuration={6000}
          onClose={() => setSnackbarMessage("")}
          message={snackbarMessage}
        />
      </Box>
    </ThemeProvider>
  );
}

export default App;
