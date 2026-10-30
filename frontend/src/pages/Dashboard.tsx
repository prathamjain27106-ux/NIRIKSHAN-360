/* =================================================================
   Dashboard — Command Centre
   ================================================================= */

import { useState, useEffect } from 'react';
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement,
  PointElement, ArcElement, Title, Tooltip, Legend, Filler, RadialLinearScale,
} from 'chart.js';
import { Bar, Doughnut, Line } from 'react-chartjs-2';
import { dashboardApi } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import type { DashboardMetrics } from '../types';
import { MetricCard, DemoBanner, LoadingState } from '../components/common';
import { demoDashboardMetrics } from '../data/demo';

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, ArcElement, Title, Tooltip, Legend, Filler, RadialLinearScale);

const C = {
  teal: 'hsl(174,72%,56%)', blue: 'hsl(210,70%,55%)', red: 'hsl(0,65%,55%)',
  purple: 'hsl(280,60%,60%)', amber: 'hsl(38,85%,55%)', green: 'hsl(152,60%,50%)',
  text: 'hsl(220,10%,65%)', grid: 'hsl(220,15%,18%)',
};

export function Dashboard() {
  const { isDemoMode } = useAuth();
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isDemoMode) {
      setMetrics(demoDashboardMetrics);
      setLoading(false);
      return;
    }

    dashboardApi.metrics()
      .then(setMetrics)
      .catch(() => setError('Dashboard data could not be loaded. Please check the backend connection.'))
      .finally(() => setLoading(false));
  }, [isDemoMode]);

  if (loading) return <div className="page-content"><LoadingState message="Loading dashboard..." /></div>;
  if (error || !metrics) return <div className="page-content"><div className="alert alert--danger" role="alert">{error}</div></div>;

  return (
    <div className="page-content animate-fade-in">
      {isDemoMode && <DemoBanner />}
      <h1 className="page-title">Command Centre</h1>
      <p className="page-subtitle">Real-time overview of complaint operations across all AICTE bureaus and cells</p>

      <div className="kpi-grid stagger-children">
        <MetricCard label="Total Complaints" value={metrics.total_complaints.toLocaleString()} change="+12%" trend="up" color="var(--accent)" />
        <MetricCard label="Pending Triage" value={metrics.pending_triage} change="-8%" trend="down" color="var(--status-warning)" />
        <MetricCard label="SLA Breaches" value={metrics.sla_breaches} change="+2" trend="up" color="var(--status-danger)" />
        <MetricCard label="Resolved (30d)" value={metrics.resolved_30d} change="+23%" trend="up" color="var(--status-success)" />
        <MetricCard label="Avg Resolution" value={`${metrics.avg_resolution_days}d`} change="-0.8d" trend="down" color="var(--status-info)" />
      </div>

      <div className="charts-grid">
        <div className="chart-container">
          <div className="chart-container__title">Complaints by Cell</div>
          <Doughnut data={{
            labels: Object.keys(metrics.complaints_by_cell),
            datasets: [{ data: Object.values(metrics.complaints_by_cell), backgroundColor: [C.teal, C.red, C.blue, C.purple, C.amber], borderColor: 'hsl(220,20%,13%)', borderWidth: 2 }],
          }} options={{ responsive: true, plugins: { legend: { position: 'right', labels: { color: C.text, font: { family: 'Inter', size: 12 }, padding: 12 } } } }} />
        </div>

        <div className="chart-container">
          <div className="chart-container__title">Monthly Trend</div>
          <Line data={{
            labels: metrics.monthly_trend.map(m => m.month),
            datasets: [
              { label: 'Received', data: metrics.monthly_trend.map(m => m.received), borderColor: C.teal, backgroundColor: 'hsl(174,72%,56%,0.1)', fill: true, tension: 0.4, pointRadius: 4 },
              { label: 'Resolved', data: metrics.monthly_trend.map(m => m.resolved), borderColor: C.green, backgroundColor: 'hsl(152,60%,50%,0.05)', fill: true, tension: 0.4, pointRadius: 4 },
            ],
          }} options={{ responsive: true, scales: { x: { ticks: { color: C.text }, grid: { color: C.grid } }, y: { ticks: { color: C.text }, grid: { color: C.grid }, beginAtZero: true } }, plugins: { legend: { labels: { color: C.text } } } }} />
        </div>

        <div className="chart-container">
          <div className="chart-container__title">SLA Performance by Cell</div>
          <Bar data={{
            labels: metrics.sla_performance.map(s => s.cell),
            datasets: [
              { label: 'Within SLA', data: metrics.sla_performance.map(s => s.within_sla), backgroundColor: C.green, borderRadius: 4 },
              { label: 'Breached', data: metrics.sla_performance.map(s => s.breached), backgroundColor: C.red, borderRadius: 4 },
            ],
          }} options={{ responsive: true, scales: { x: { ticks: { color: C.text }, grid: { display: false }, stacked: true }, y: { ticks: { color: C.text, callback: v => `${v}%` }, grid: { color: C.grid }, stacked: true, max: 100 } }, plugins: { legend: { labels: { color: C.text } } } }} />
        </div>

        <div className="chart-container">
          <div className="chart-container__title">Urgency Distribution</div>
          <Bar data={{
            labels: Object.keys(metrics.complaints_by_urgency),
            datasets: [{ label: 'Active', data: Object.values(metrics.complaints_by_urgency), backgroundColor: [C.red, C.amber, C.blue, C.green], borderRadius: 4 }],
          }} options={{ responsive: true, indexAxis: 'y' as const, scales: { x: { ticks: { color: C.text }, grid: { color: C.grid } }, y: { ticks: { color: C.text }, grid: { display: false } } }, plugins: { legend: { display: false } } }} />
        </div>
      </div>
    </div>
  );
}
