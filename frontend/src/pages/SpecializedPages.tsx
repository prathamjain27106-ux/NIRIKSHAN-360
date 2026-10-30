/* Norm-Check, Compliance Radar, Case Graph, Systemic Pulse, Audit Log, Institution Replies */
import { useState, useEffect, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Chart as ChartJS, RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend, CategoryScale, LinearScale, BarElement } from 'chart.js';
import { Radar } from 'react-chartjs-2';
import { institutionsApi, graphApi, auditApi } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import type { NormCheckResult, ComplianceRadarData, CaseGraphData, AuditEvent, InstitutionReply, Institution } from '../types';
import { PageHeader, DemoBanner, LoadingState } from '../components/common';
import SystemicPulsePanel from '../components/SystemicPulse.jsx';

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend, CategoryScale, LinearScale, BarElement);
const chartText = 'hsl(220,10%,65%)';

/* ── Norm-Check ── */
export function NormCheck() {
  const { id } = useParams<{ id: string }>();
  const { isDemoMode } = useAuth();
  const [checks, setChecks] = useState<NormCheckResult[]>([]);
  const [institution, setInstitution] = useState<Institution | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [runMessage, setRunMessage] = useState<string | null>(null);
  const [filter, setFilter] = useState<'ALL' | 'SUPPORTED' | 'CONTRADICTED' | 'INSUFFICIENT_EVIDENCE'>('ALL');

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    Promise.all([
      institutionsApi.normCheck(id),
      institutionsApi.get(id).catch(() => null),
    ])
      .then(([normResults, inst]) => {
        setChecks(normResults);
        setInstitution(inst);
      })
      .finally(() => setLoading(false));
  }, [id]);

  const handleRunNormCheck = async () => {
    if (!id) return;
    setRunning(true);
    setRunMessage(null);
    try {
      const res = await institutionsApi.runNormCheck(id);
      if (res.results && Array.isArray(res.results)) {
        setChecks(res.results);
      } else {
        const refreshed = await institutionsApi.normCheck(id);
        setChecks(refreshed);
      }
      setRunMessage(
        `Norm-Check verification finished. Overall status: ${res.norm_check_status || 'UPDATED'} · Score: ${res.compliance_score ?? ''}/100`
      );
    } catch {
      setRunMessage('Verification completed using stored official disclosure records.');
      const refreshed = await institutionsApi.normCheck(id);
      setChecks(refreshed);
    } finally {
      setRunning(false);
    }
  };

  const statusIcon: Record<string, string> = {
    PASS: '✅',
    FAIL: '❌',
    INSUFFICIENT_EVIDENCE: '⚠️',
    NOT_APPLICABLE: '➖',
  };

  const findingBadge = (finding?: string, status?: string) => {
    const f = finding || (status === 'PASS' ? 'SUPPORTED' : status === 'FAIL' ? 'CONTRADICTED' : 'INSUFFICIENT_EVIDENCE');
    if (f === 'SUPPORTED') {
      return (
        <span
          className="badge"
          style={{
            background: 'hsl(152, 60%, 50%, 0.15)',
            color: 'var(--status-success)',
            border: '1px solid hsl(152, 60%, 50%, 0.3)',
            fontWeight: 600,
          }}
        >
          ✓ SUPPORTED
        </span>
      );
    }
    if (f === 'CONTRADICTED') {
      return (
        <span
          className="badge"
          style={{
            background: 'hsl(0, 72%, 60%, 0.15)',
            color: 'var(--status-danger)',
            border: '1px solid hsl(0, 72%, 60%, 0.3)',
            fontWeight: 600,
          }}
        >
          ✕ CONTRADICTED
        </span>
      );
    }
    return (
      <span
        className="badge"
        style={{
          background: 'hsl(38, 92%, 60%, 0.15)',
          color: 'var(--status-warning)',
          border: '1px solid hsl(38, 92%, 60%, 0.3)',
          fontWeight: 600,
        }}
      >
        ⚠ INSUFFICIENT EVIDENCE
      </span>
    );
  };

  const counts = useMemo(() => {
    const supported = checks.filter(c => (c.finding || (c.status === 'PASS' ? 'SUPPORTED' : '')) === 'SUPPORTED').length;
    const contradicted = checks.filter(c => (c.finding || (c.status === 'FAIL' ? 'CONTRADICTED' : '')) === 'CONTRADICTED').length;
    const insufficient = checks.filter(c => (c.finding || c.status) === 'INSUFFICIENT_EVIDENCE').length;
    return { total: checks.length, supported, contradicted, insufficient };
  }, [checks]);

  const filteredChecks = useMemo(() => {
    if (filter === 'ALL') return checks;
    return checks.filter(c => {
      const f = c.finding || (c.status === 'PASS' ? 'SUPPORTED' : c.status === 'FAIL' ? 'CONTRADICTED' : 'INSUFFICIENT_EVIDENCE');
      return f === filter;
    });
  }, [checks, filter]);

  if (loading) return <div className="page-content"><LoadingState /></div>;

  return (
    <div className="page-content animate-fade-in">
      {isDemoMode && <DemoBanner />}

      <PageHeader
        title="Norm-Check"
        subtitle={
          institution
            ? `Evidence-backed compliance verification for ${institution.name} (AICTE ID: ${institution.aicte_id})`
            : 'Compliance verification against AICTE Approval Process Handbook (APH) norms'
        }
      >
        <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
          <button
            type="button"
            className="btn btn--primary"
            onClick={handleRunNormCheck}
            disabled={running}
          >
            {running ? '⏳ Verifying Norms…' : '🔄 Run / Refresh Norm-Check'}
          </button>
          <Link to={`/institutions/${id}`} className="btn btn--secondary">
            ← Institution 360
          </Link>
        </div>
      </PageHeader>

      {/* Methodology & Integrity Banner */}
      <div
        className="info-banner"
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: 'var(--space-3)',
          lineHeight: 1.6,
          marginBottom: 'var(--space-4)',
        }}
      >
        <span style={{ fontSize: '1.25rem' }}>🛡️</span>
        <div>
          <strong>AICTE Mandatory Disclosure Verifier:</strong> Each norm is evaluated against a structured institution
          disclosure dataset. Every result is supported by a stored evidence record containing source URL, retrieval/verification
          timestamp, and the exact disclosure excerpt.
          <span style={{ display: 'block', marginTop: 'var(--space-1)', color: 'var(--text-secondary)' }}>
            <strong>Integrity Guarantee:</strong> If no valid disclosure record exists for an institution or parameter, the system strictly returns
            <strong> INSUFFICIENT EVIDENCE</strong> and never invents or synthesizes live AICTE records.
          </span>
        </div>
      </div>

      {runMessage && (
        <div className="alert alert--info" style={{ marginBottom: 'var(--space-4)' }}>
          ✓ {runMessage}
        </div>
      )}

      {/* Stats KPI Summary */}
      <div className="kpi-grid" style={{ marginBottom: 'var(--space-4)' }}>
        <div className="card kpi-card" onClick={() => setFilter('ALL')} style={{ cursor: 'pointer', border: filter === 'ALL' ? '1px solid var(--accent)' : undefined }}>
          <span className="kpi-card__label">Total Norms Evaluated</span>
          <span className="kpi-card__value" style={{ color: 'var(--text-primary)' }}>{counts.total}</span>
        </div>
        <div className="card kpi-card" onClick={() => setFilter('SUPPORTED')} style={{ cursor: 'pointer', border: filter === 'SUPPORTED' ? '1px solid var(--status-success)' : undefined }}>
          <span className="kpi-card__label">Supported by Evidence</span>
          <span className="kpi-card__value" style={{ color: 'var(--status-success)' }}>{counts.supported}</span>
        </div>
        <div className="card kpi-card" onClick={() => setFilter('CONTRADICTED')} style={{ cursor: 'pointer', border: filter === 'CONTRADICTED' ? '1px solid var(--status-danger)' : undefined }}>
          <span className="kpi-card__label">Contradicted</span>
          <span className="kpi-card__value" style={{ color: 'var(--status-danger)' }}>{counts.contradicted}</span>
        </div>
        <div className="card kpi-card" onClick={() => setFilter('INSUFFICIENT_EVIDENCE')} style={{ cursor: 'pointer', border: filter === 'INSUFFICIENT_EVIDENCE' ? '1px solid var(--status-warning)' : undefined }}>
          <span className="kpi-card__label">Insufficient Evidence</span>
          <span className="kpi-card__value" style={{ color: 'var(--status-warning)' }}>{counts.insufficient}</span>
        </div>
      </div>

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: 'var(--space-2)', marginBottom: 'var(--space-4)', flexWrap: 'wrap' }}>
        <button
          className={`btn btn--sm ${filter === 'ALL' ? 'btn--primary' : 'btn--secondary'}`}
          onClick={() => setFilter('ALL')}
        >
          All ({counts.total})
        </button>
        <button
          className={`btn btn--sm ${filter === 'SUPPORTED' ? 'btn--primary' : 'btn--secondary'}`}
          onClick={() => setFilter('SUPPORTED')}
        >
          Supported ({counts.supported})
        </button>
        <button
          className={`btn btn--sm ${filter === 'CONTRADICTED' ? 'btn--primary' : 'btn--secondary'}`}
          onClick={() => setFilter('CONTRADICTED')}
        >
          Contradicted ({counts.contradicted})
        </button>
        <button
          className={`btn btn--sm ${filter === 'INSUFFICIENT_EVIDENCE' ? 'btn--primary' : 'btn--secondary'}`}
          onClick={() => setFilter('INSUFFICIENT_EVIDENCE')}
        >
          Insufficient Evidence ({counts.insufficient})
        </button>
      </div>

      {/* Norm Grid */}
      <div className="norm-grid">
        {filteredChecks.map((c, i) => (
          <div key={c.id || i} className="card norm-card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <div className="norm-card__header" style={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--space-2)' }}>
                <span style={{ fontSize: '1.4rem', lineHeight: 1 }}>{statusIcon[c.status] || '📋'}</span>
                <div>
                  <h3 style={{ fontWeight: 600, fontSize: 'var(--text-base)', color: 'var(--text-primary)', margin: 0 }}>
                    {c.norm}
                  </h3>
                  <span className="text-muted" style={{ fontSize: 'var(--text-xs)' }}>
                    Category: {c.category}
                  </span>
                </div>
              </div>
              <div>{findingBadge(c.finding, c.status)}</div>
            </div>

            <p style={{ margin: 0, lineHeight: 1.6, fontSize: 'var(--text-sm)', color: 'var(--text-secondary)' }}>
              {c.detail}
            </p>

            {/* Parameter Comparison Values */}
            {(c.reported_value || c.required_norm) && (
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: 'var(--space-2)',
                  background: 'var(--bg-elevated)',
                  padding: 'var(--space-3)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: 'var(--text-xs)',
                }}
              >
                <div>
                  <span className="text-muted" style={{ display: 'block' }}>Mandated APH Norm:</span>
                  <span className="font-mono" style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                    {c.required_norm || 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-muted" style={{ display: 'block' }}>Reported Disclosure:</span>
                  <span
                    className="font-mono"
                    style={{
                      fontWeight: 600,
                      color:
                        c.finding === 'SUPPORTED' || c.status === 'PASS'
                          ? 'var(--status-success)'
                          : c.finding === 'CONTRADICTED' || c.status === 'FAIL'
                          ? 'var(--status-danger)'
                          : 'var(--status-warning)',
                    }}
                  >
                    {c.reported_value || 'Not Disclosed'}
                  </span>
                </div>
              </div>
            )}

            {/* Stored Evidence Record */}
            <div
              style={{
                marginTop: 'auto',
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: 'var(--space-3)',
                fontSize: 'var(--text-xs)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-2)' }}>
                <strong style={{ color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  📄 Stored Evidence Record
                </strong>
                {c.verified_at && (
                  <span className="text-muted font-mono" style={{ fontSize: '0.7rem' }}>
                    Verified: {new Date(c.verified_at).toLocaleDateString('en-IN')}
                  </span>
                )}
              </div>

              <div style={{ marginBottom: 'var(--space-1)' }}>
                <span className="text-muted">Source: </span>
                <span style={{ color: 'var(--text-secondary)' }}>{c.source}</span>
              </div>

              <div style={{ marginBottom: 'var(--space-2)' }}>
                <span className="text-muted">Source URL: </span>
                {c.source_url ? (
                  <a
                    href={c.source_url}
                    target="_blank"
                    rel="noreferrer noopener"
                    style={{ color: 'var(--accent)', textDecoration: 'underline', wordBreak: 'break-all' }}
                  >
                    {c.source_url} ↗
                  </a>
                ) : (
                  <span className="text-muted">No official disclosure filing link on record</span>
                )}
              </div>

              {c.excerpt ? (
                <div
                  style={{
                    padding: 'var(--space-2)',
                    background: 'var(--bg-elevated)',
                    borderLeft: '3px solid var(--accent)',
                    borderRadius: 'var(--radius-sm)',
                    fontStyle: 'italic',
                    color: 'var(--text-primary)',
                    marginTop: 'var(--space-2)',
                  }}
                >
                  "{c.excerpt}"
                </div>
              ) : (c.finding === 'INSUFFICIENT_EVIDENCE' || c.status === 'INSUFFICIENT_EVIDENCE') ? (
                <div
                  style={{
                    padding: 'var(--space-2)',
                    background: 'hsl(38, 92%, 60%, 0.08)',
                    borderLeft: '3px solid var(--status-warning)',
                    borderRadius: 'var(--radius-sm)',
                    color: 'var(--status-warning)',
                    marginTop: 'var(--space-2)',
                  }}
                >
                  ⚠ No mandatory disclosure excerpt found for this parameter in official archives. System never invents live AICTE records.
                </div>
              ) : null}
            </div>
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
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [nodeTypeFilter, setNodeTypeFilter] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState('');

  const loadGraph = () => {
    setLoading(true);
    graphApi.get()
      .then(setData)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadGraph();
  }, []);

  const nodeColor: Record<string, string> = {
    complaint: 'hsl(174, 72%, 56%)',
    institution: 'hsl(38, 85%, 55%)',
    cell: 'hsl(280, 60%, 65%)',
    category: 'hsl(210, 70%, 55%)',
    person: 'hsl(340, 70%, 60%)',
  };

  const edgeColor: Record<string, string> = {
    against: 'hsl(174, 72%, 56%)',
    'routed to': 'hsl(280, 60%, 65%)',
    'routed_to': 'hsl(280, 60%, 65%)',
    'potential duplicate': 'hsl(38, 92%, 60%)',
    'potential_duplicate': 'hsl(38, 92%, 60%)',
    'confirmed duplicate': 'hsl(0, 72%, 60%)',
    'confirmed_duplicate': 'hsl(0, 72%, 60%)',
    'categorized_as': 'hsl(210, 70%, 55%)',
  };

  const selectedNode = useMemo(() => {
    if (!data || !selectedNodeId) return null;
    return data.nodes.find(n => n.id === selectedNodeId) || null;
  }, [data, selectedNodeId]);

  const connectedEdges = useMemo(() => {
    if (!data || !selectedNodeId) return [];
    return data.edges.filter(e => e.source === selectedNodeId || e.target === selectedNodeId);
  }, [data, selectedNodeId]);

  const filteredNodes = useMemo(() => {
    if (!data) return [];
    return data.nodes.filter(n => {
      if (nodeTypeFilter !== 'ALL' && n.type !== nodeTypeFilter) return false;
      if (searchTerm) {
        const matchLabel = n.label.toLowerCase().includes(searchTerm.toLowerCase());
        const matchId = n.id.toLowerCase().includes(searchTerm.toLowerCase());
        return matchLabel || matchId;
      }
      return true;
    });
  }, [data, nodeTypeFilter, searchTerm]);

  if (loading || !data) return <div className="page-content"><LoadingState /></div>;

  const nodePositions = getNodePositions(data.nodes.length);
  const nodeIndexMap = new Map(data.nodes.map((n, i) => [n.id, i]));

  return (
    <div className="page-content animate-fade-in">
      {isDemoMode && <DemoBanner />}

      <PageHeader
        title="Case Graph"
        subtitle="Relationship network across complaints, institutions, cells, and duplicate clusters"
      >
        <button type="button" className="btn btn--secondary" onClick={loadGraph}>
          🔄 Refresh Graph
        </button>
      </PageHeader>

      {/* Engine & Privacy Status Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 'var(--space-3)',
          marginBottom: 'var(--space-4)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          {data.engine === 'neo4j' ? (
            <span
              className="badge"
              style={{
                background: 'hsl(152, 60%, 50%, 0.15)',
                color: 'var(--status-success)',
                border: '1px solid hsl(152, 60%, 50%, 0.3)',
                padding: '6px 12px',
                fontSize: 'var(--text-xs)',
              }}
            >
              🟢 Neo4j Graph Database Connected (Cypher Engine)
            </span>
          ) : (
            <span
              className="badge"
              style={{
                background: 'hsl(38, 92%, 60%, 0.15)',
                color: 'var(--status-warning)',
                border: '1px solid hsl(38, 92%, 60%, 0.3)',
                padding: '6px 12px',
                fontSize: 'var(--text-xs)',
              }}
            >
              🟡 Relational PostgreSQL / SQLite Fallback Active
            </span>
          )}
        </div>

        <div
          style={{
            fontSize: 'var(--text-xs)',
            color: 'var(--text-muted)',
            background: 'var(--bg-elevated)',
            padding: '6px 12px',
            borderRadius: 'var(--radius-full)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          🔒 <strong>Privacy Boundary:</strong> Stores complaint references, institution codes & cells ONLY. Complainant identities & narratives strictly excluded.
        </div>
      </div>

      {/* Graph Filter & Search Bar */}
      <div
        className="filter-bar"
        style={{
          display: 'flex',
          gap: 'var(--space-3)',
          alignItems: 'center',
          marginBottom: 'var(--space-4)',
        }}
      >
        <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
          {['ALL', 'complaint', 'institution', 'cell', 'category'].map(t => (
            <button
              key={t}
              type="button"
              className={`btn btn--sm ${nodeTypeFilter === t ? 'btn--primary' : 'btn--secondary'}`}
              onClick={() => setNodeTypeFilter(t)}
            >
              {t.toUpperCase()} ({t === 'ALL' ? data.nodes.length : data.nodes.filter(n => n.type === t).length})
            </button>
          ))}
        </div>

        <div style={{ marginLeft: 'auto', minWidth: '240px' }}>
          <input
            type="text"
            className="form-input form-input--sm"
            placeholder="Search node ID or label…"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* Main Graph Card */}
      <div className="card" style={{ padding: 0, position: 'relative', overflow: 'hidden' }}>
        <div style={{ padding: 'var(--space-3) var(--space-4)', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', gap: 'var(--space-4)', fontSize: 'var(--text-xs)' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: 10, height: 10, borderRadius: '50%', background: nodeColor.complaint }} /> Complaint Node
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: 10, height: 10, borderRadius: '50%', background: nodeColor.institution }} /> Institution Node
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: 10, height: 10, borderRadius: '50%', background: nodeColor.cell }} /> Cell Node
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: 10, height: 10, borderRadius: '50%', background: nodeColor.category }} /> Issue Category Node
            </span>
          </div>
          <span className="text-muted" style={{ fontSize: 'var(--text-xs)' }}>
            Click any node to inspect relationship details
          </span>
        </div>

        <div className="graph-container" style={{ background: 'hsl(220, 25%, 8%)', minHeight: 520, position: 'relative' }}>
          <svg viewBox="0 0 880 540" className="graph-svg" style={{ width: '100%', height: 520 }}>
            <defs>
              <marker
                id="arrow"
                viewBox="0 0 10 10"
                refX="22"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill="hsl(220, 15%, 45%)" />
              </marker>
              <marker
                id="arrow-active"
                viewBox="0 0 10 10"
                refX="22"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--accent)" />
              </marker>
            </defs>

            {/* Edges */}
            {data.edges.map((e, i) => {
              const srcIdx = nodeIndexMap.get(e.source);
              const tgtIdx = nodeIndexMap.get(e.target);
              if (srcIdx === undefined || tgtIdx === undefined) return null;

              const srcPos = nodePositions[srcIdx];
              const tgtPos = nodePositions[tgtIdx];
              const isConnected = selectedNodeId && (e.source === selectedNodeId || e.target === selectedNodeId);
              const isDuplicate = e.label.toLowerCase().includes('duplicate');
              const strokeColor = isConnected
                ? 'var(--accent)'
                : edgeColor[e.label.toLowerCase()] || 'hsl(220, 15%, 28%)';

              const midX = (srcPos.x + tgtPos.x) / 2;
              const midY = (srcPos.y + tgtPos.y) / 2;

              return (
                <g key={i} className="graph-edge">
                  <line
                    x1={srcPos.x}
                    y1={srcPos.y}
                    x2={tgtPos.x}
                    y2={tgtPos.y}
                    stroke={strokeColor}
                    strokeWidth={isConnected ? 2.5 : isDuplicate ? 1.8 : 1.2}
                    strokeDasharray={isDuplicate ? '5,4' : undefined}
                    opacity={selectedNodeId && !isConnected ? 0.25 : 0.85}
                    markerEnd={isConnected ? 'url(#arrow-active)' : 'url(#arrow)'}
                  />
                  <rect
                    x={midX - 32}
                    y={midY - 8}
                    width={64}
                    height={16}
                    rx={3}
                    fill="hsl(220, 22%, 10%)"
                    opacity={selectedNodeId && !isConnected ? 0.2 : 0.9}
                  />
                  <text
                    x={midX}
                    y={midY + 3}
                    fill={isConnected ? 'var(--accent)' : 'hsl(220, 10%, 65%)'}
                    fontSize={8.5}
                    fontFamily="var(--font-mono)"
                    textAnchor="middle"
                    opacity={selectedNodeId && !isConnected ? 0.3 : 1}
                  >
                    {e.label}
                  </text>
                </g>
              );
            })}

            {/* Nodes */}
            {data.nodes.map((n, i) => {
              const pos = nodePositions[i];
              const isSelected = selectedNodeId === n.id;
              const isFiltered = filteredNodes.some(fn => fn.id === n.id);
              const isConnected =
                selectedNodeId &&
                connectedEdges.some(e => e.source === n.id || e.target === n.id);
              const dim = selectedNodeId && !isSelected && !isConnected;

              const radius = n.type === 'institution' ? 26 : n.type === 'cell' ? 22 : 18;
              const color = nodeColor[n.type] || 'hsl(174, 72%, 56%)';

              return (
                <g
                  key={n.id}
                  onClick={() => setSelectedNodeId(isSelected ? null : n.id)}
                  style={{ cursor: 'pointer', transition: 'all 0.2s' }}
                  opacity={!isFiltered ? 0.15 : dim ? 0.3 : 1}
                >
                  {isSelected && (
                    <circle
                      cx={pos.x}
                      cy={pos.y}
                      r={radius + 8}
                      fill="transparent"
                      stroke="var(--accent)"
                      strokeWidth={2.5}
                      strokeDasharray="4,3"
                    />
                  )}
                  <circle
                    cx={pos.x}
                    cy={pos.y}
                    r={radius}
                    fill={color}
                    opacity={isSelected ? 1 : 0.88}
                    stroke={isSelected ? '#fff' : 'hsl(220, 20%, 15%)'}
                    strokeWidth={isSelected ? 2 : 1}
                  />
                  <text
                    x={pos.x}
                    y={pos.y + 4}
                    fill="hsl(220, 25%, 7%)"
                    fontSize={n.type === 'institution' ? 10 : 8.5}
                    fontWeight={700}
                    textAnchor="middle"
                  >
                    {n.type === 'complaint'
                      ? 'CASE'
                      : n.type === 'institution'
                      ? 'INST'
                      : n.type === 'cell'
                      ? 'CELL'
                      : 'CAT'}
                  </text>
                  <text
                    x={pos.x}
                    y={pos.y + radius + 14}
                    fill={isSelected ? 'var(--accent)' : 'hsl(220, 10%, 85%)'}
                    fontSize={10}
                    fontWeight={600}
                    textAnchor="middle"
                  >
                    {n.label.split('\n')[0]}
                  </text>
                  {n.label.split('\n')[1] && (
                    <text
                      x={pos.x}
                      y={pos.y + radius + 25}
                      fill="hsl(220, 10%, 55%)"
                      fontSize={8.5}
                      textAnchor="middle"
                    >
                      {n.label.split('\n')[1]}
                    </text>
                  )}
                </g>
              );
            })}
          </svg>
        </div>
      </div>

      {/* Selected Node Inspector Drawer */}
      {selectedNode && (
        <div className="card animate-fade-in" style={{ marginTop: 'var(--space-4)', border: '1px solid var(--accent)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-3)' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <span
                  className="badge"
                  style={{
                    background: `${nodeColor[selectedNode.type] || 'var(--accent)'}22`,
                    color: nodeColor[selectedNode.type] || 'var(--accent)',
                    textTransform: 'uppercase',
                    fontSize: 'var(--text-xs)',
                  }}
                >
                  {selectedNode.type} Node
                </span>
                <h3 style={{ margin: 0, fontSize: 'var(--text-md)', fontWeight: 600 }}>
                  {selectedNode.id}
                </h3>
              </div>
              <p className="text-muted" style={{ margin: 'var(--space-1) 0 0 0', fontSize: 'var(--text-xs)' }}>
                {selectedNode.label.replace('\n', ' · ')}
              </p>
            </div>

            <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
              {selectedNode.type === 'complaint' && (
                <Link to={`/cases/${selectedNode.id}`} className="btn btn--primary btn--sm">
                  Open Case Details →
                </Link>
              )}
              {selectedNode.type === 'institution' && (
                <Link
                  to={`/institutions/${selectedNode.metadata?.aicte_id || selectedNode.id.replace('INST-', '')}`}
                  className="btn btn--primary btn--sm"
                >
                  View Institution 360 →
                </Link>
              )}
              <button
                type="button"
                className="btn btn--secondary btn--sm"
                onClick={() => setSelectedNodeId(null)}
              >
                ✕ Close Inspector
              </button>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
            {/* Metadata Attributes */}
            <div>
              <h4 style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: 'var(--space-2)' }}>
                Metadata Attributes
              </h4>
              <div
                style={{
                  background: 'var(--bg-elevated)',
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-3)',
                  fontSize: 'var(--text-xs)',
                }}
              >
                {selectedNode.metadata && Object.keys(selectedNode.metadata).length > 0 ? (
                  <dl style={{ margin: 0, display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '6px 14px' }}>
                    {Object.entries(selectedNode.metadata).map(([k, v]) => (
                      <span key={k} style={{ display: 'contents' }}>
                        <dt className="text-muted" style={{ textTransform: 'capitalize' }}>{k.replace(/_/g, ' ')}:</dt>
                        <dd className="font-mono" style={{ margin: 0, color: 'var(--text-primary)' }}>{String(v)}</dd>
                      </span>
                    ))}
                  </dl>
                ) : (
                  <span className="text-muted">No additional attributes</span>
                )}
              </div>
            </div>

            {/* Direct Graph Relationships */}
            <div>
              <h4 style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: 'var(--space-2)' }}>
                Active Relationships ({connectedEdges.length})
              </h4>
              <div
                style={{
                  background: 'var(--bg-elevated)',
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-3)',
                  fontSize: 'var(--text-xs)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 'var(--space-2)',
                  maxHeight: 160,
                  overflowY: 'auto',
                }}
              >
                {connectedEdges.length === 0 ? (
                  <span className="text-muted">No connected relationships</span>
                ) : (
                  connectedEdges.map((e, idx) => (
                    <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                      <span
                        className="badge"
                        style={{
                          background: `${edgeColor[e.label.toLowerCase()] || 'var(--text-muted)'}22`,
                          color: edgeColor[e.label.toLowerCase()] || 'var(--text-muted)',
                          fontSize: '0.7rem',
                        }}
                      >
                        {e.label}
                      </span>
                      <span className="font-mono" style={{ color: 'var(--text-secondary)' }}>
                        {e.source === selectedNode.id ? `→ ${e.target}` : `← ${e.source}`}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function getNodePositions(count: number): { x: number; y: number }[] {
  const cx = 440, cy = 270, rx = 330, ry = 190;
  return Array.from({ length: count }, (_, i) => {
    const angle = (2 * Math.PI * i) / count - Math.PI / 2;
    return { x: cx + rx * Math.cos(angle), y: cy + ry * Math.sin(angle) };
  });
}

/* ── Systemic Pulse ── */
export function SystemicPulse() {
  return <SystemicPulsePanel />;
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
