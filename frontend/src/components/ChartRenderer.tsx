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

// Helper to check if a column name is an ID column
const isIdColumn = (colName: string): boolean => {
  const lowerName = colName.toLowerCase()
  return (
    lowerName === 'id' ||
    lowerName.endsWith('_id') ||
    lowerName.startsWith('id_')
  )
}

// Simple Venn Diagram Component for 2-3 sets
function VennDiagram({ config }: { config: ChartConfig }) {
  const sets = config.sets || []

  if (sets.length === 0) {
    return <div className="text-gray-500 text-center py-8">No Venn diagram data available</div>
  }

  // Extract unique set names
  const setNames = [...new Set(sets.filter(s => s.sets.length === 1).map(s => s.sets[0]))]

  if (setNames.length < 2 || setNames.length > 3) {
    return <div className="text-gray-500 text-center py-8">Venn diagrams support 2-3 sets</div>
  }

  const getSetSize = (name: string) => {
    const set = sets.find(s => s.sets.length === 1 && s.sets[0] === name)
    return set?.size || 0
  }

  const getIntersectionSize = (names: string[]) => {
    const set = sets.find(s =>
      s.sets.length === names.length &&
      names.every(n => s.sets.includes(n))
    )
    return set?.size || 0
  }

  const is3Sets = setNames.length === 3

  return (
    <div className="relative w-full h-[300px] flex items-center justify-center">
      <svg viewBox="0 0 400 300" className="w-full h-full max-w-[400px]">
        {/* Set A - Left circle */}
        <circle
          cx={is3Sets ? 150 : 140}
          cy={is3Sets ? 140 : 150}
          r={80}
          fill={COLORS[0]}
          fillOpacity={0.3}
          stroke={COLORS[0]}
          strokeWidth={2}
        />
        {/* Set B - Right circle */}
        <circle
          cx={is3Sets ? 250 : 260}
          cy={is3Sets ? 140 : 150}
          r={80}
          fill={COLORS[1]}
          fillOpacity={0.3}
          stroke={COLORS[1]}
          strokeWidth={2}
        />
        {/* Set C - Bottom circle (for 3 sets) */}
        {is3Sets && (
          <circle
            cx={200}
            cy={220}
            r={80}
            fill={COLORS[2]}
            fillOpacity={0.3}
            stroke={COLORS[2]}
            strokeWidth={2}
          />
        )}

        {/* Labels */}
        <text x={is3Sets ? 90 : 80} y={is3Sets ? 100 : 120} className="text-sm font-medium" fill={COLORS[0]}>
          {setNames[0]}
        </text>
        <text x={is3Sets ? 280 : 300} y={is3Sets ? 100 : 120} className="text-sm font-medium" fill={COLORS[1]}>
          {setNames[1]}
        </text>
        {is3Sets && (
          <text x={200} y={280} textAnchor="middle" className="text-sm font-medium" fill={COLORS[2]}>
            {setNames[2]}
          </text>
        )}

        {/* Size labels */}
        <text x={is3Sets ? 110 : 100} y={is3Sets ? 140 : 150} textAnchor="middle" className="text-xs" fill="#333">
          {getSetSize(setNames[0]) - getIntersectionSize([setNames[0], setNames[1]])}
        </text>
        <text x={is3Sets ? 290 : 300} y={is3Sets ? 140 : 150} textAnchor="middle" className="text-xs" fill="#333">
          {getSetSize(setNames[1]) - getIntersectionSize([setNames[0], setNames[1]])}
        </text>
        <text x={200} y={is3Sets ? 140 : 150} textAnchor="middle" className="text-xs font-medium" fill="#333">
          {getIntersectionSize([setNames[0], setNames[1]])}
        </text>

        {is3Sets && (
          <>
            <text x={200} y={250} textAnchor="middle" className="text-xs" fill="#333">
              {getSetSize(setNames[2]) - getIntersectionSize([setNames[0], setNames[2]]) - getIntersectionSize([setNames[1], setNames[2]]) + getIntersectionSize(setNames)}
            </text>
            <text x={160} y={190} textAnchor="middle" className="text-xs" fill="#333">
              {getIntersectionSize([setNames[0], setNames[2]])}
            </text>
            <text x={240} y={190} textAnchor="middle" className="text-xs" fill="#333">
              {getIntersectionSize([setNames[1], setNames[2]])}
            </text>
            <text x={200} y={180} textAnchor="middle" className="text-xs font-bold" fill="#333">
              {getIntersectionSize(setNames)}
            </text>
          </>
        )}
      </svg>
    </div>
  )
}

export default function ChartRenderer({ type, data, config }: ChartRendererProps) {
  // Venn diagrams don't need data, they use config.sets
  if (type !== 'venn' && (!data || data.length === 0)) return null

  // Auto-detect columns if not specified
  const columns = Object.keys(data[0])

  // Filter out ID columns for display
  const displayColumns = columns.filter(col => !isIdColumn(col))

  const xColumn = config.x_column && !isIdColumn(config.x_column)
    ? config.x_column
    : displayColumns[0] || columns[0]
  const yColumn = config.y_column && !isIdColumn(config.y_column)
    ? config.y_column
    : displayColumns[1] || displayColumns[0] || columns[1] || columns[0]

  // Find numeric columns for y-axis, excluding ID columns
  const numericColumns = displayColumns.filter((col) => {
    if (isIdColumn(col)) return false
    const firstValue = data[0][col]
    return typeof firstValue === 'number' || !isNaN(Number(firstValue))
  })

  // Convert data for charts, only including non-ID columns
  const chartData = data.map((row) => {
    const newRow: Record<string, unknown> = {}
    displayColumns.forEach((col) => {
      if (numericColumns.includes(col)) {
        newRow[col] = Number(row[col])
      } else {
        newRow[col] = row[col]
      }
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

    case 'venn':
      return <VennDiagram config={config} />

    case 'table':
    case 'none':
    default:
      return null
  }
}
