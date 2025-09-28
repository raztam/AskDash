import React, { useState } from "react";
import {
  Box,
  TextField,
  Button,
  Paper,
  Typography,
  IconButton,
  InputAdornment,
  CircularProgress,
  Alert,
} from "@mui/material";
import { Send as SendIcon, Clear as ClearIcon } from "@mui/icons-material";

interface QueryInputProps {
  onSubmit: (query: string) => void;
  loading?: boolean;
  error?: string | null;
}

const QueryInput: React.FC<QueryInputProps> = ({
  onSubmit,
  loading = false,
  error,
}) => {
  const [query, setQuery] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !loading) {
      onSubmit(query.trim());
      setQuery("");
    }
  };

  const handleClear = () => {
    setQuery("");
  };

  const exampleQueries = [
    "Show total sales by month for the last year",
    "What are the top 10 products by revenue?",
    "How many customers do we have by region?",
    "Show average order value by customer segment",
  ];

  return (
    <Box sx={{ width: "100%" }}>
      <Paper sx={{ p: 3, mb: 2 }}>
        <Typography variant="h6" sx={{ mb: 2, color: "#333" }}>
          Ask a question about your data
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            multiline
            rows={3}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type your question in natural language..."
            variant="outlined"
            disabled={loading}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <Box
                    sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}
                  >
                    {query && (
                      <IconButton
                        onClick={handleClear}
                        size="small"
                        disabled={loading}
                      >
                        <ClearIcon />
                      </IconButton>
                    )}
                    <IconButton
                      type="submit"
                      disabled={!query.trim() || loading}
                      sx={{ color: "#9ACD32" }}
                    >
                      {loading ? <CircularProgress size={20} /> : <SendIcon />}
                    </IconButton>
                  </Box>
                </InputAdornment>
              ),
            }}
            sx={{
              "& .MuiOutlinedInput-root": {
                "&.Mui-focused fieldset": {
                  borderColor: "#9ACD32",
                },
              },
            }}
          />
        </form>

        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle2" sx={{ mb: 1, color: "#666" }}>
            Try these example queries:
          </Typography>
          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
            {exampleQueries.map((example, index) => (
              <Button
                key={index}
                variant="outlined"
                size="small"
                onClick={() => setQuery(example)}
                disabled={loading}
                sx={{
                  borderColor: "#9ACD32",
                  color: "#9ACD32",
                  "&:hover": {
                    borderColor: "#7CB342",
                    backgroundColor: "rgba(154, 205, 50, 0.04)",
                  },
                  textTransform: "none",
                  fontSize: "0.8rem",
                }}
              >
                {example}
              </Button>
            ))}
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default QueryInput;
