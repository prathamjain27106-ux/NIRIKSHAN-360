/* Norm-Check, Compliance Radar, Case Graph, Systemic Pulse, Audit Log, Institution Replies */
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Chart as ChartJS, RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend, CategoryScale, LinearScale, BarElement } from 'chart.js';
import { Radar, Bar } from 'react-chartjs-2';
import { institutionsApi, graphApi, auditApi } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import type { NormCheckResult, ComplianceRadarData, CaseGraphData, AuditEvent, InstitutionReply } from '../types';
import { PageHeader, DemoBanner, LoadingState } from '../components/common';

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend, CategoryScale, LinearScale, BarElement);
const chartText = 'hsl(220,10%,65%)';

/* ── Norm-Check ── */
export function NormCheck() {
  const { id } = useParams<{ id: string }>();
  const { isDemoMode } = useAuth();
  const [checks, setChecks] = useState<NormCheckResult[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => { institutionsApi.normCheck(id || '').then(setChecks).finally(() => setLoading(false)); }, [id]);

  const statusIcon: Record<string, string> = { PASS: '✅', FAIL: '❌', INSUFFICIENT_EVIDENCE: '⚠️', NOT_APPLICABLE: '➖' };
  const statusColor: Record<string, string> = { PASS: 'var(--status-success)', FAIL: 'var(--status-danger)', INSUFFICIENT_EVIDENCE: 'var(--status-warning)', NOT_APPLICABLE: 'var(--text-muted)' };

  if (loading) return <div className="page-content"><LoadingState /></div>;
  return (
    <div className="page-content animate-fade-in">
      {isDemoMode && <DemoBanner />}
      <PageHeader title="Norm-Check" subtitle="Compliance verification against AICTE Approval Process Handbook norms">
        <Link to={`/institutions/${id}`} className="btn btn--secondary">← Institution 360</Link>
      </PageHeader>
      <div className="norm-grid">
        {checks.map((c, i) => (
          <div key={i} className="card norm-card">
            <div className="norm-card__header">
              <span style={{ fontSize: '1.5rem' }}>{statusIcon[c.status]}</span>
              <div>
                <h3 style={{ fontWeight: 600, color: statusColor[c.status] }}>{c.norm}</h3>
                <span className="text-muted" style={{ fontSize: 'var(--text-xs)' }}>{c.category}</span>
              </div>
            </div>
            <p style={{ margin: 'var(--space-3) 0', lineHeight: 1.6 }}>{c.detail}</p>
            <p className="text-muted" style={{ fontSize: 'var(--text-xs)' }}>Source: {c.source}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Compliance Radar ── */
export function ComplianceRadar() {
  const { id } = useParams<{ id: string }>();
  const { isDemoMode } = useAuth();
  const [data, setData] = useState<ComplianceRadarData | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => { institutionsApi.complianceRadar(id || '').then(setData).finally(() => setLoading(false)); }, [id]);

  if (loading || !data) return <div className="page-content"><LoadingState /></div>;
  return (
    <div className="page-content animate-fade-in">
      {isDemoMode && <DemoBanner />}
      <PageHeader title="Compliance Radar" subtitle={`Size-normalized review signals for ${data.institution_name}`}>
        <Link to={`/institutions/${id}`} className="btn btn--secondary">← Institution 360</Link>
      </PageHeader>
      <p className="text-muted" style={{ fontSize: 'var(--text-xs)', marginBottom: 'var(--space-4)' }}>
        ⚠ These are review signals, not verdicts. Human review is required for any consequential determination.
      </p>
      <div className="charts-grid">
        <div className="chart-container" style={{ maxWidth: 550 }}>
          <Radar data={{
            labels: data.dimensions.map(d => d.label),
            datasets: [
              { label: 'Institution', data: data.dimensions.map(d => d.value), backgroundColor: 'hsl(174,72%,56%,0.2)', borderColor: 'hsl(174,72%,56%)', pointBackgroundColor: 'hsl(174,72%,56%)' },
              { label: 'Benchmark', data: data.dimensions.map(d => d.benchmark), backgroundColor: 'hsl(220,10%,65%,0.1)', borderColor: 'hsl(220,10%,65%)', borderDash: [5, 5], pointBackgroundColor: 'hsl(220,10%,65%)' },
            ],
          }} options={{ scales: { r: { ticks: { color: chartText, backdropColor: 'transparent' }, grid: { color: 'hsl(220,15%,18%)' }, pointLabels: { color: chartText, font: { size: 12 } }, suggestedMin: 0, suggestedMax: 100 } }, plugins: { legend: { labels: { color: chartText } } } }} />
        </div>
        <div className="card">
          <h3 className="card__title" style={{ marginBottom: 'var(--space-3)' }}>Dimension Breakdown</h3>
          {data.dimensions.map((d, i) => (
            <div key={i} className="radar-row">
              <span className="radar-row__label">{d.label}</span>
              <div className="radar-row__bar">
                <div className="radar-row__fill" style={{ width: `${d.value}%`, background: d.value >= d.benchmark ? 'var(--status-success)' : 'var(--status-danger)' }} />
                <div className="radar-row__benchmark" style={{ left: `${d.benchmark}%` }} />
              </div>
              <span className="radar-row__value" style={{ color: d.value >= d.benchmark ? 'var(--status-success)' : 'var(--status-danger)' }}>{d.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ── Case Graph ── */
export function CaseGraph() {
  const { isDemoMode } = useAuth();
  const [data, setData] = useState<CaseGraphData | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => { graphApi.get().then(setData).finally(() => setLoading(false)); }, []);

  if (loading || !data) return <div className="page-content"><LoadingState /></div>;

  const nodeColor: Record<string, string> = { complaint: 'hsl(174,72%,56%)', institution: 'hsl(38,85%,55%)', cell: 'hsl(210,70%,55%)', person: 'hsl(280,60%,60%)' };
  return (
    <div className="page-content animate-fade-in">
      {isDemoMode && <DemoBanner />}
      <PageHeader title="Case Graph" subtitle="Relationship network across complaints, institutions, and cells" />
      {data.fallback && <div className="info-banner">ℹ Using SQL-based fallback graph (Neo4j credentials not configured)</div>}
      <div className="graph-container card">
        <svg viewBox="0 0 800 500" className="graph-svg">
          {/* Edges */}
          {data.edges.map((e, i) => {
            const src = data.nodes.findIndex(n => n.id === e.source);
            const tgt = data.nodes.findIndex(n => n.id === e.target);
            if (src < 0 || tgt < 0) return null;
            const positions = getNodePositions(data.nodes.length);
            return <g key={i}>
              <line x1={positions[src].x} y1={positions[src].y} x2={positions[tgt].x} y2={positions[tgt].y} stroke="hsl(220,15%,25%)" strokeWidth={1.5} />
              <text x={(positions[src].x + positions[tgt].x) / 2} y={(positions[src].y + positions[tgt].y) / 2 - 6} fill="hsl(220,10%,50%)" fontSize={9} textAnchor="middle">{e.label}</text>
            </g>;
          })}
          {/* Nodes */}
          {data.nodes.map((n, i) => {
            const pos = getNodePositions(data.nodes.length)[i];
            return <g key={n.id}>
              <circle cx={pos.x} cy={pos.y} r={n.type === 'institution' ? 28 : 22} fill={nodeColor[n.type] || '#888'} opacity={0.85} />
              <text x={pos.x} y={pos.y + 38} fill="hsl(220,10%,75%)" fontSize={10} textAnchor="middle" fontWeight={600}>{n.label.split('\n')[0]}</text>
              {n.label.split('\n')[1] && <text x={pos.x} y={pos.y + 50} fill="hsl(220,10%,55%)" fontSize={9} textAnchor="middle">{n.label.split('\n')[1]}</text>}
            </g>;
          })}
        </svg>
      </div>
    </div>
  );
}

function getNodePositions(count: number): { x: number; y: number }[] {
  const cx = 400, cy = 250, rx = 280, ry = 160;
  return Array.from({ length: count }, (_, i) => {
    const angle = (2 * Math.PI * i) / count - Math.PI / 2;
    return { x: cx + rx * Math.cos(angle), y: cy + ry * Math.sin(angle) };
  });
}

/* ── Systemic Pulse ── */
export function SystemicPulse() {
  const { isDemoMode } = useAuth();
  // Use demo dashboard metrics for the analytics
  const [metrics, setMetrics] = useState<Record<string, number> | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    import('../data/demo').then(m => { setMetrics(m.demoDashboardMetrics.state_distribution); setLoading(false); });
  }, []);

  if (loading || !metrics) return <div className="page-content"><LoadingState /></div>;
  const states = Object.entries(metrics).sort((a, b) => b[1] - a[1]);

  return (
    <div className="page-content animate-fade-in">
      {isDemoMode && <DemoBanner />}
      <PageHeader title="Systemic Pulse" subtitle="Cross-institution trend analytics and geographic distribution" />
      <div className="charts-grid">
        <div className="chart-container">
          <div className="chart-container__title">Complaints by State</div>
          <Bar data={{
            labels: states.map(([s]) => s),
            datasets: [{ label: 'Complaints', data: states.map(([, v]) => v), backgroundColor: 'hsl(174,72%,56%,0.7)', borderRadius: 4 }],
          }} options={{ indexAxis: 'y' as const, responsive: true, scales: { x: { ticks: { color: chartText }, grid: { color: 'hsl(220,15%,18%)' } }, y: { ticks: { color: chartText, font: { size: 11 } }, grid: { display: false } } }, plugins: { legend: { display: false } } }} />
        </div>
        <div className="card">
          <h3 className="card__title" style={{ marginBottom: 'var(--space-3)' }}>State Distribution Table</h3>
          <table className="data-table">
            <thead><tr><th>State</th><th>Complaints</th><th>% of Total</th></tr></thead>
            <tbody>{states.map(([state, count]) => {
              const total = states.reduce((s, [, v]) => s + v, 0);
              return <tr key={state}><td>{state}</td><td>{count}</td><td>{((count / total) * 100).toFixed(1)}%</td></tr>;
            })}</tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/* ── Audit Log ── */
export function AuditLog() {
  const { isDemoMode } = useAuth();
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => { auditApi.list().then(r => setEvents(r.results)).finally(() => setLoading(false)); }, []);

  if (loading) return <div className="page-content"><LoadingState /></div>;
  const actionColors: Record<string, string> = { ESCALATION: 'var(--status-danger)', RESOLUTION: 'var(--status-success)', TRIAGE: 'var(--status-info)', ROUTING: 'var(--accent)', CASE_ASSIGNED: 'var(--status-warning)', DUPLICATE_FLAG: 'var(--status-warning)', STATUS_CHANGE: 'var(--status-info)', IDENTITY_REVEAL_REQUEST: 'var(--status-danger)' };
  return (
    <div className="page-content animate-fade-in">
      {isDemoMode && <DemoBanner />}
      <PageHeader title="Audit Log" subtitle="Complete trail of all system actions and events" />
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead><tr><th>Timestamp</th><th>Action</th><th>Actor</th><th>Target</th><th>Detail</th></tr></thead>
          <tbody>{events.map(e => (
            <tr key={e.id}>
              <td className="font-mono" style={{ fontSize: 'var(--text-xs)', whiteSpace: 'nowrap' }}>{new Date(e.timestamp).toLocaleString('en-IN')}</td>
              <td><span className="badge" style={{ background: `${actionColors[e.action] || 'var(--text-muted)'}22`, color: actionColors[e.action] || 'var(--text-muted)' }}>{e.action}</span></td>
              <td>{e.actor}</td>
              <td><Link to={`/cases/${e.target_id}`} className="case-link font-mono">{e.target_id}</Link></td>
              <td style={{ maxWidth: 350 }}>{e.detail}</td>
            </tr>
          ))}</tbody>
        </table>
      </div>
    </div>
  );
}

/* ── Institution Replies ── */
export function InstitutionReplies() {
  const { id } = useParams<{ id: string }>();
  const { isDemoMode } = useAuth();
  const [replies, setReplies] = useState<InstitutionReply[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => { institutionsApi.replies(id || '').then(setReplies).finally(() => setLoading(false)); }, [id]);

  if (loading) return <div className="page-content"><LoadingState /></div>;
  return (
    <div className="page-content animate-fade-in">
      {isDemoMode && <DemoBanner />}
      <PageHeader title="Institution Right of Reply" subtitle="Responses submitted by institution representatives">
        <Link to={`/institutions/${id}`} className="btn btn--secondary">← Institution 360</Link>
      </PageHeader>
      {replies.length === 0 ? <div className="card" style={{ textAlign: 'center', padding: '3rem' }}><p className="text-muted">No replies submitted yet.</p></div> : (
        <div className="reply-list">{replies.map(r => (
          <div key={r.id} className="card reply-card">
            <div className="reply-card__header">
              <span className="reply-card__author">💬 {r.submitted_by}</span>
              <span className="text-muted" style={{ fontSize: 'var(--text-xs)' }}>{new Date(r.submitted_at).toLocaleString('en-IN')}</span>
              <span className={`badge ${r.status === 'ACCEPTED' ? 'badge--status-resolved' : r.status === 'REJECTED' ? 'badge--status-escalated' : 'badge--status-progress'}`}>{r.status.replace(/_/g, ' ')}</span>
            </div>
            <p style={{ marginTop: 'var(--space-3)', lineHeight: 1.7 }}>{r.content}</p>
            <div className="reply-card__ref">
              Re: <Link to={`/cases/${r.complaint_id}`} className="case-link font-mono">{r.complaint_id}</Link>
              {r.attachments.length > 0 && <span className="text-muted"> · {r.attachments.length} attachment(s)</span>}
            </div>
          </div>
        ))}</div>
      )}
    </div>
  );
}
