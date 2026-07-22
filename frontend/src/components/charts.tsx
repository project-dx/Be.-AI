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
        <CartesianGrid strokeDasharray="3 3" stroke="#eee8dd" />
        <XAxis dataKey={xKey} tickFormatter={(v) => shortDate(String(v))} fontSize={11} stroke="#a8a297" />
        <YAxis domain={yDomain ?? [0, 'auto']} fontSize={11} stroke="#a8a297" unit={unit} />
        <Tooltip
          labelFormatter={(v) => shortDate(String(v))}
          contentStyle={{ borderRadius: 14, border: '1px solid #eae4d9', boxShadow: '0 8px 24px -8px rgba(67,63,56,0.18)', fontSize: 12 }}
        />
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
        <CartesianGrid strokeDasharray="3 3" stroke="#eee8dd" />
        <XAxis dataKey={xKey} fontSize={11} stroke="#a8a297" />
        <YAxis domain={yDomain ?? [0, 'auto']} fontSize={11} stroke="#a8a297" unit={unit} />
        <Tooltip
          contentStyle={{ borderRadius: 14, border: '1px solid #eae4d9', boxShadow: '0 8px 24px -8px rgba(67,63,56,0.18)', fontSize: 12 }}
        />
        {series.length > 1 && <Legend wrapperStyle={{ fontSize: 12 }} />}
        {series.map((s) => (
          <Bar key={s.key} dataKey={s.key} name={s.name} fill={s.color} radius={[8, 8, 0, 0]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  )
}

export const chartColors = {
  green: '#6aaf5c',
  blue: '#4d9ad0',
  orange: '#ee8a4f',
  pink: '#e85d8a',
  violet: '#9179c6',
  rose: '#e05c5c',
}
