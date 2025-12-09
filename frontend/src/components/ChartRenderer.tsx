import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import type { ChartType, ChartConfig } from '../types'

interface ChartRendererProps {
  type: ChartType
  data: Record<string, unknown>[]
  config: ChartConfig
}

// Color palette
const COLORS = [
  '#32CD32', // Primary green
  '#CD3280', // Secondary pink
  '#3280CD', // Blue
  '#CD8032', // Orange
  '#8032CD', // Purple
  '#32CDA0', // Teal
  '#CD3232', // Red
  '#80CD32', // Lime
]

export default function ChartRenderer({ type, data, config }: ChartRendererProps) {
  if (!data || data.length === 0) return null

  // Auto-detect columns if not specified
  const columns = Object.keys(data[0])
  const xColumn = config.x_column || columns[0]
  const yColumn = config.y_column || columns[1] || columns[0]

  // Find numeric columns for y-axis
  const numericColumns = columns.filter((col) => {
    const firstValue = data[0][col]
    return typeof firstValue === 'number' || !isNaN(Number(firstValue))
  })

  // Convert data for charts
  const chartData = data.map((row) => {
    const newRow: Record<string, unknown> = { ...row }
    numericColumns.forEach((col) => {
      newRow[col] = Number(row[col])
    })
    return newRow
  })

  switch (type) {
    case 'bar':
      return (
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey={xColumn}
              tick={{ fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: '#e5e7eb' }}
            />
            <YAxis
              tick={{ fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: '#e5e7eb' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
              }}
            />
            <Legend />
            {numericColumns.slice(0, 4).map((col, i) => (
              <Bar
                key={col}
                dataKey={col}
                fill={COLORS[i % COLORS.length]}
                radius={[4, 4, 0, 0]}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      )

    case 'line':
      return (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey={xColumn}
              tick={{ fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: '#e5e7eb' }}
            />
            <YAxis
              tick={{ fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: '#e5e7eb' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
              }}
            />
            <Legend />
            {numericColumns.slice(0, 4).map((col, i) => (
              <Line
                key={col}
                type="monotone"
                dataKey={col}
                stroke={COLORS[i % COLORS.length]}
                strokeWidth={2}
                dot={{ fill: COLORS[i % COLORS.length], strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )

    case 'pie':
      // For pie chart, we need a name and value
      const pieData = chartData.slice(0, 10).map((row, index) => ({
        name: String(row[xColumn]),
        value: Number(row[yColumn]) || 0,
        fill: COLORS[index % COLORS.length],
      }))

      return (
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) =>
                `${name} (${(percent * 100).toFixed(0)}%)`
              }
              outerRadius={100}
              dataKey="value"
            >
              {pieData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
              }}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      )

    case 'scatter':
      // For scatter, we need two numeric columns
      const xNumeric = numericColumns[0] || xColumn
      const yNumeric = numericColumns[1] || numericColumns[0] || yColumn

      return (
        <ResponsiveContainer width="100%" height={300}>
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              type="number"
              dataKey={xNumeric}
              name={xNumeric}
              tick={{ fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: '#e5e7eb' }}
            />
            <YAxis
              type="number"
              dataKey={yNumeric}
              name={yNumeric}
              tick={{ fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: '#e5e7eb' }}
            />
            <Tooltip
              cursor={{ strokeDasharray: '3 3' }}
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
              }}
            />
            <Legend />
            <Scatter
              name="Data"
              data={chartData}
              fill={COLORS[0]}
            />
          </ScatterChart>
        </ResponsiveContainer>
      )

    case 'table':
    case 'none':
    default:
      return null
  }
}
