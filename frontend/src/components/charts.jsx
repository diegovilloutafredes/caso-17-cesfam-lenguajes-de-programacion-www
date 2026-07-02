import { Doughnut, Bar } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  ArcElement,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
} from 'chart.js'

ChartJS.register(
  ArcElement,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
)

// mismos colores que los tokens CSS
export const CHART = {
  success: '#00913F',
  warning: '#897200',
  danger: '#C5494B',
  primary: '#0D8CE8',
  accent: '#179FC8',
  info: '#255171',
  grid: '#E5E7EB',
}

export const baseOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { labels: { font: { family: 'Inter' } } } },
}

export { Doughnut, Bar }

export function ChartCard({ title, subtitle, children, actions }) {
  return (
    <div className="card">
      <div className="row-between mb-3">
        <div>
          <h2 className="mt-0" style={{ marginBottom: subtitle ? 2 : 0 }}>{title}</h2>
          {subtitle && <small className="text-soft">{subtitle}</small>}
        </div>
        {actions}
      </div>
      <div style={{ height: 260 }}>{children}</div>
    </div>
  )
}
