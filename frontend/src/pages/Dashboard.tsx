import type { CSSProperties } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Bar, Doughnut, Line } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
);

// ── Synthetic demo data ──
const kpis = [
  { label: 'Total Complaints', value: '1,247', change: '+12%', trend: 'up' as const, color: 'var(--accent)' },
  { label: 'Pending Triage', value: '38', change: '-8%', trend: 'down' as const, color: 'var(--status-warning)' },
  { label: 'SLA Breaches', value: '7', change: '+2', trend: 'up' as const, color: 'var(--status-danger)' },
  { label: 'Resolved (30d)', value: '312', change: '+23%', trend: 'up' as const, color: 'var(--status-success)' },
  { label: 'Avg Resolution', value: '4.2d', change: '-0.8d', trend: 'down' as const, color: 'var(--status-info)' },
];

const recentCases = [
  { id: 'NIR-2026-01234', institution: 'ABC Engineering College', cell: 'PGRC', status: 'Under Review', sla: '2d 14h', slaClass: 'safe' },
  { id: 'NIR-2026-01233', institution: 'XYZ Institute of Technology', cell: 'Anti-Ragging', status: 'Escalated', sla: '0d 3h', slaClass: 'danger' },
  { id: 'NIR-2026-01232', institution: 'PQR Medical College', cell: 'ICC', status: 'Pending Triage', sla: '6d 8h', slaClass: 'safe' },
  { id: 'NIR-2026-01231', institution: 'LMN Pharmacy Institute', cell: 'Scholarship', status: 'Routed', sla: '4d 1h', slaClass: 'warning' },
  { id: 'NIR-2026-01230', institution: 'DEF Business School', cell: 'RB', status: 'Resolved', sla: '—', slaClass: 'safe' },
];

const chartColors = {
  teal: 'hsl(174, 72%, 56%)',
  blue: 'hsl(210, 70%, 55%)',
  red: 'hsl(0, 65%, 55%)',
  purple: 'hsl(280, 60%, 60%)',
  amber: 'hsl(38, 85%, 55%)',
  green: 'hsl(152, 60%, 50%)',
};

const chartTextColor = 'hsl(220, 10%, 65%)';
const chartGridColor = 'hsl(220, 15%, 18%)';

export function Dashboard() {
  return (
    <div className="page-content animate-fade-in">
      <h1 className="page-title">Command Centre</h1>
      <p className="page-subtitle">
        Real-time overview of complaint operations across all AICTE bureaus and cells
        <span style={{ marginLeft: '0.75rem', fontSize: 'var(--text-xs)', color: 'var(--status-warning)', fontWeight: 600 }}>
          ⚠ SYNTHETIC DEMO DATA
        </span>
      </p>

      {/* KPI Cards */}
      <div className="kpi-grid stagger-children">
        {kpis.map((kpi) => (
          <div
            className="kpi-card"
            key={kpi.label}
            style={{ '--kpi-color': kpi.color } as CSSProperties}
          >
            <div className="kpi-card__label">{kpi.label}</div>
            <div className="kpi-card__value">{kpi.value}</div>
            <div className={`kpi-card__change kpi-card__change--${kpi.trend === 'up' ? 'up' : 'down'}`}>
              {kpi.trend === 'up' ? '↑' : '↓'} {kpi.change}
            </div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="charts-grid">
        {/* Complaints by Cell */}
        <div className="chart-container">
          <div className="chart-container__title">Complaints by Cell</div>
          <Doughnut
            data={{
              labels: ['PGRC', 'Anti-Ragging', 'RB', 'ICC', 'Scholarship'],
              datasets: [{
                data: [420, 310, 245, 158, 114],
                backgroundColor: [
                  chartColors.teal,
                  chartColors.red,
                  chartColors.blue,
                  chartColors.purple,
                  chartColors.amber,
                ],
                borderColor: 'hsl(220, 20%, 13%)',
                borderWidth: 2,
              }],
            }}
            options={{
              responsive: true,
              maintainAspectRatio: true,
              plugins: {
                legend: {
                  position: 'right',
                  labels: { color: chartTextColor, font: { family: 'Inter', size: 12 }, padding: 12 },
                },
              },
            }}
          />
        </div>

        {/* Monthly Trend */}
        <div className="chart-container">
          <div className="chart-container__title">Monthly Complaint Trend</div>
          <Line
            data={{
              labels: ['May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct'],
              datasets: [
                {
                  label: 'Received',
                  data: [185, 210, 195, 240, 220, 197],
                  borderColor: chartColors.teal,
                  backgroundColor: 'hsl(174, 72%, 56%, 0.1)',
                  fill: true,
                  tension: 0.4,
                  pointBackgroundColor: chartColors.teal,
                  pointRadius: 4,
                  pointHoverRadius: 6,
                },
                {
                  label: 'Resolved',
                  data: [160, 190, 180, 210, 200, 185],
                  borderColor: chartColors.green,
                  backgroundColor: 'hsl(152, 60%, 50%, 0.05)',
                  fill: true,
                  tension: 0.4,
                  pointBackgroundColor: chartColors.green,
                  pointRadius: 4,
                  pointHoverRadius: 6,
                },
              ],
            }}
            options={{
              responsive: true,
              maintainAspectRatio: true,
              scales: {
                x: { ticks: { color: chartTextColor }, grid: { color: chartGridColor } },
                y: { ticks: { color: chartTextColor }, grid: { color: chartGridColor }, beginAtZero: true },
              },
              plugins: {
                legend: { labels: { color: chartTextColor, font: { family: 'Inter', size: 12 } } },
              },
            }}
          />
        </div>

        {/* SLA Performance */}
        <div className="chart-container">
          <div className="chart-container__title">SLA Performance by Cell</div>
          <Bar
            data={{
              labels: ['PGRC', 'Anti-Ragging', 'RB', 'ICC', 'Scholarship'],
              datasets: [
                {
                  label: 'Within SLA',
                  data: [92, 85, 88, 90, 95],
                  backgroundColor: chartColors.green,
                  borderRadius: 4,
                },
                {
                  label: 'Breached',
                  data: [8, 15, 12, 10, 5],
                  backgroundColor: chartColors.red,
                  borderRadius: 4,
                },
              ],
            }}
            options={{
              responsive: true,
              maintainAspectRatio: true,
              scales: {
                x: { ticks: { color: chartTextColor }, grid: { display: false }, stacked: true },
                y: { ticks: { color: chartTextColor, callback: (v) => `${v}%` }, grid: { color: chartGridColor }, stacked: true, max: 100 },
              },
              plugins: {
                legend: { labels: { color: chartTextColor, font: { family: 'Inter', size: 12 } } },
              },
            }}
          />
        </div>

        {/* Urgency Distribution */}
        <div className="chart-container">
          <div className="chart-container__title">Urgency Distribution</div>
          <Bar
            data={{
              labels: ['Critical', 'High', 'Medium', 'Low'],
              datasets: [{
                label: 'Active Cases',
                data: [18, 67, 145, 82],
                backgroundColor: [
                  chartColors.red,
                  chartColors.amber,
                  chartColors.blue,
                  chartColors.green,
                ],
                borderRadius: 4,
              }],
            }}
            options={{
              responsive: true,
              maintainAspectRatio: true,
              indexAxis: 'y',
              scales: {
                x: { ticks: { color: chartTextColor }, grid: { color: chartGridColor } },
                y: { ticks: { color: chartTextColor }, grid: { display: false } },
              },
              plugins: {
                legend: { display: false },
              },
            }}
          />
        </div>
      </div>

      {/* Recent Cases Table */}
      <div className="card">
        <div className="card__header">
          <h2 className="card__title">Recent Cases</h2>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--status-warning)' }}>⚠ Synthetic data</span>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Case ID</th>
                <th>Institution</th>
                <th>Cell</th>
                <th>Status</th>
                <th>SLA Remaining</th>
              </tr>
            </thead>
            <tbody>
              {recentCases.map((c) => (
                <tr key={c.id}>
                  <td>
                    <span className="font-mono" style={{ color: 'var(--accent)', fontWeight: 600 }}>
                      {c.id}
                    </span>
                  </td>
                  <td>{c.institution}</td>
                  <td>
                    <span className={`badge badge--cell-${c.cell.toLowerCase().replace('-', '').replace(' ', '')}`}>
                      {c.cell}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${
                      c.status === 'Resolved' ? 'badge--status-resolved' :
                      c.status === 'Escalated' ? 'badge--status-escalated' :
                      c.status === 'Pending Triage' ? 'badge--status-open' :
                      'badge--status-progress'
                    }`}>
                      {c.status}
                    </span>
                  </td>
                  <td>
                    <span className={`sla-timer sla-timer--${c.slaClass}`}>
                      {c.sla !== '—' && <span className="sla-timer__dot" />}
                      {c.sla}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
