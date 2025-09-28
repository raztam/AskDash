import React from "react";
import {
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  Typography,
  Box,
  Chip,
  IconButton,
  Tooltip,
} from "@mui/material";
import {
  Delete as DeleteIcon,
  Replay as ReplayIcon,
  AccessTime as TimeIcon,
} from "@mui/icons-material";
import { QueryHistory } from "../types";
import { queriesApi } from "../services/api";

interface QueryHistorySidebarProps {
  queries: QueryHistory[];
  selectedQueryId?: string;
  onQuerySelect: (query: QueryHistory) => void;
  onQueryRerun: (queryId: string) => void;
  onQueryDelete: (queryId: string) => void;
}

const QueryHistorySidebar: React.FC<QueryHistorySidebarProps> = ({
  queries,
  selectedQueryId,
  onQuerySelect,
  onQueryRerun,
  onQueryDelete,
}) => {
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getVisualizationColor = (type: string) => {
    const colors = {
      table: "#666",
      bar_chart: "#9ACD32",
      line_chart: "#7CB342",
      pie_chart: "#689F38",
      kpi: "#558B2F",
    };
    return colors[type as keyof typeof colors] || "#666";
  };

  if (queries.length === 0) {
    return (
      <Box sx={{ p: 2, textAlign: "center" }}>
        <Typography variant="body2" color="textSecondary">
          No queries yet. Start by asking a question about your data!
        </Typography>
      </Box>
    );
  }

  return (
    <List sx={{ width: "100%", p: 0 }}>
      {queries.map((query) => (
        <ListItem
          key={query.query_id}
          disablePadding
          sx={{
            mb: 1,
            borderRadius: 1,
            backgroundColor:
              selectedQueryId === query.query_id ? "#f0f8ff" : "transparent",
            border:
              selectedQueryId === query.query_id
                ? "1px solid #9ACD32"
                : "1px solid transparent",
          }}
        >
          <ListItemButton
            onClick={() => onQuerySelect(query)}
            sx={{ py: 1, px: 2 }}
          >
            <ListItemText
              primary={
                <Typography
                  variant="body2"
                  sx={{ fontWeight: "medium", mb: 0.5 }}
                >
                  {query.original_query.length > 60
                    ? `${query.original_query.substring(0, 60)}...`
                    : query.original_query}
                </Typography>
              }
              secondary={
                <Box>
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 1,
                      mb: 0.5,
                    }}
                  >
                    <Chip
                      label={query.visualization_type.replace("_", " ")}
                      size="small"
                      sx={{
                        backgroundColor: getVisualizationColor(
                          query.visualization_type
                        ),
                        color: "white",
                        fontSize: "0.7rem",
                        height: "20px",
                      }}
                    />
                    <Typography variant="caption" color="textSecondary">
                      {query.row_count} rows
                    </Typography>
                  </Box>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                    <TimeIcon sx={{ fontSize: 12 }} />
                    <Typography variant="caption" color="textSecondary">
                      {formatTime(query.timestamp)}
                    </Typography>
                  </Box>
                </Box>
              }
            />
            <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}>
              <Tooltip title="Rerun Query">
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    onQueryRerun(query.query_id);
                  }}
                  sx={{ color: "#9ACD32" }}
                >
                  <ReplayIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              <Tooltip title="Delete Query">
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    onQueryDelete(query.query_id);
                  }}
                  sx={{ color: "#f44336" }}
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
          </ListItemButton>
        </ListItem>
      ))}
    </List>
  );
};

export default QueryHistorySidebar;
