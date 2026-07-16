import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { EmptyState } from './ui'
import { shortDate } from '../utils/labels'

interface SeriesDef {
  key: string
  name: string
  color: string
}

export function TrendLineChart({ data, series, xKey = 'date', yDomain, unit, height = 220 }: {
  data: object[]
  series: SeriesDef[]
  xKey?: string
  yDomain?: [number, number]
  unit?: string
  height?: number
}) {
  if (!data || data.length === 0) {
    return <EmptyState message="表示できるデータがまだありません。日報を入力するとグラフが表示されます" />
  }
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -18 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey={xKey} tickFormatter={(v) => shortDate(String(v))} fontSize={11} stroke="#64748b" />
        <YAxis domain={yDomain ?? [0, 'auto']} fontSize={11} stroke="#64748b" unit={unit} />
        <Tooltip labelFormatter={(v) => shortDate(String(v))} />
        {series.length > 1 && <Legend wrapperStyle={{ fontSize: 12 }} />}
        {series.map((s) => (
          <Line
            key={s.key}
            type="monotone"
            dataKey={s.key}
            name={s.name}
            stroke={s.color}
            strokeWidth={2}
            dot={{ r: 3 }}
            connectNulls
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}

export function SimpleBarChart({ data, series, xKey = 'label', yDomain, unit, height = 220 }: {
  data: object[]
  series: SeriesDef[]
  xKey?: string
  yDomain?: [number, number]
  unit?: string
  height?: number
}) {
  if (!data || data.length === 0) {
    return <EmptyState message="表示できるデータがまだありません" />
  }
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -18 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey={xKey} fontSize={11} stroke="#64748b" />
        <YAxis domain={yDomain ?? [0, 'auto']} fontSize={11} stroke="#64748b" unit={unit} />
        <Tooltip />
        {series.length > 1 && <Legend wrapperStyle={{ fontSize: 12 }} />}
        {series.map((s) => (
          <Bar key={s.key} dataKey={s.key} name={s.name} fill={s.color} radius={[6, 6, 0, 0]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  )
}

export const chartColors = {
  green: '#10b981',
  blue: '#3b82f6',
  orange: '#f59e0b',
  pink: '#ec4899',
  violet: '#8b5cf6',
  rose: '#f43f5e',
}
