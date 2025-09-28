import React from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  ButtonGroup,
} from "@mui/material";
import { FileDownload as DownloadIcon } from "@mui/icons-material";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
} from "recharts";
import { QueryResult, VisualizationType } from "../types";
import { exportApi } from "../services/api";

interface DataVisualizerProps {
  result: QueryResult;
}

const DataVisualizer: React.FC<DataVisualizerProps> = ({ result }) => {
  const { data, columns, visualization_type, query_id } = result;

  const colors = ["#9ACD32", "#7CB342", "#689F38", "#558B2F", "#33691E"];

  const handleExportCsv = async () => {
    try {
      await exportApi.exportToCsv(query_id);
    } catch (error) {
      console.error("Failed to export CSV:", error);
    }
  };

  const handleExportJson = async () => {
    try {
      await exportApi.exportToJson(query_id);
    } catch (error) {
      console.error("Failed to export JSON:", error);
    }
  };

  const renderKPI = () => {
    if (data.length === 0 || columns.length === 0) return null;

    const value = data[0][columns[0]];
    const label = columns[0].replace(/_/g, " ").toUpperCase();

    return (
      <Card
        sx={{
          textAlign: "center",
          p: 3,
          backgroundColor: "#9ACD32",
          color: "white",
        }}
      >
        <CardContent>
          <Typography variant="h3" component="div" sx={{ fontWeight: "bold" }}>
            {typeof value === "number" ? value.toLocaleString() : value}
          </Typography>
          <Typography variant="h6" sx={{ mt: 1, opacity: 0.9 }}>
            {label}
          </Typography>
        </CardContent>
      </Card>
    );
  };

  const renderBarChart = () => {
    if (data.length === 0 || columns.length < 2) return null;

    const chartData = data.map((row, index) => ({
      name: row[columns[0]] || `Item ${index + 1}`,
      value: Number(row[columns[1]]) || 0,
    }));

    return (
      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="value" fill="#9ACD32" />
        </BarChart>
      </ResponsiveContainer>
    );
  };

  const renderLineChart = () => {
    if (data.length === 0 || columns.length < 2) return null;

    const chartData = data.map((row, index) => ({
      name: row[columns[0]] || `Point ${index + 1}`,
      value: Number(row[columns[1]]) || 0,
    }));

    return (
      <ResponsiveContainer width="100%" height={400}>
        <LineChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#9ACD32"
            strokeWidth={3}
          />
        </LineChart>
      </ResponsiveContainer>
    );
  };

  const renderPieChart = () => {
    if (data.length === 0 || columns.length < 2) return null;

    const chartData = data.map((row) => ({
      name: row[columns[0]] || "Unknown",
      value: Number(row[columns[1]]) || 0,
    }));

    return (
      <ResponsiveContainer width="100%" height={400}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={(entry: any) =>
              `${entry.name} ${(entry.percent * 100).toFixed(0)}%`
            }
            outerRadius={120}
            fill="#8884d8"
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={colors[index % colors.length]}
              />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    );
  };

  const renderTable = () => {
    if (data.length === 0) return null;

    return (
      <TableContainer component={Paper} sx={{ maxHeight: 500 }}>
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              {columns.map((column) => (
                <TableCell
                  key={column}
                  sx={{ fontWeight: "bold", backgroundColor: "#f5f5f5" }}
                >
                  {column.replace(/_/g, " ").toUpperCase()}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {data.map((row, index) => (
              <TableRow key={index} hover>
                {columns.map((column) => (
                  <TableCell key={`${index}-${column}`}>
                    {row[column] !== null && row[column] !== undefined
                      ? String(row[column])
                      : "N/A"}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  const renderVisualization = () => {
    switch (visualization_type as VisualizationType) {
      case "kpi":
        return renderKPI();
      case "bar_chart":
        return renderBarChart();
      case "line_chart":
        return renderLineChart();
      case "pie_chart":
        return renderPieChart();
      case "table":
      default:
        return renderTable();
    }
  };

  return (
    <Box>
      <Box
        sx={{
          mb: 2,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Typography variant="body2" color="textSecondary">
          {result.row_count} rows • {result.execution_time.toFixed(2)}s •{" "}
          {visualization_type.replace("_", " ")}
        </Typography>
        <ButtonGroup size="small">
          <Button
            startIcon={<DownloadIcon />}
            onClick={handleExportCsv}
            sx={{ color: "#9ACD32" }}
          >
            CSV
          </Button>
          <Button
            startIcon={<DownloadIcon />}
            onClick={handleExportJson}
            sx={{ color: "#9ACD32" }}
          >
            JSON
          </Button>
        </ButtonGroup>
      </Box>
      {renderVisualization()}
    </Box>
  );
};

export default DataVisualizer;
