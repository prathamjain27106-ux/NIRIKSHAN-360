/* Institution 360 — comprehensive institution profile */
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { institutionsApi, complaintsApi } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import type { Institution, Complaint } from '../types';
import { PageHeader, DemoBanner, LoadingState, ErrorState, MetricCard, StatusBadge } from '../components/common';

export function Institution360() {
  const { id } = useParams<{ id: string }>();
  const { isDemoMode } = useAuth();
  const [inst, setInst] = useState<Institution | null>(null);
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    Promise.all([
      institutionsApi.get(id),
      complaintsApi.list({ institution: id }),
    ]).then(([i, c]) => { setInst(i); setComplaints(c.results); }).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="page-content"><LoadingState /></div>;
  if (!inst) return <div className="page-content"><ErrorState message="Institution not found" /></div>;

  const normColor = inst.norm_check_status === 'COMPLIANT' ? 'var(--status-success)' : inst.norm_check_status === 'NON_COMPLIANT' ? 'var(--status-danger)' : inst.norm_check_status === 'PARTIALLY_COMPLIANT' ? 'var(--status-warning)' : 'var(--text-muted)';

  return (
    <div className="page-content animate-fade-in">
      {isDemoMode && <DemoBanner />}
      <PageHeader title={inst.name} subtitle={`${inst.city}, ${inst.state} · AICTE ID: ${inst.aicte_id} · Est. ${inst.established_year}`}>
        <Link to="/institutions" className="btn btn--secondary">← All Institutions</Link>
      </PageHeader>

      <div className="kpi-grid stagger-children">
        <MetricCard label="Total Complaints" value={inst.total_complaints} color="var(--accent)" />
        <MetricCard label="Open Cases" value={inst.open_complaints} color="var(--status-warning)" />
        <MetricCard label="Resolved" value={inst.resolved_complaints} color="var(--status-success)" />
        <MetricCard label="Compliance Score" value={`${inst.compliance_score}/100`} color={normColor} />
        <MetricCard label="Students" value={inst.student_count.toLocaleString()} color="var(--status-info)" />
      </div>

      <div className="charts-grid">
        <div className="card">
          <h3 className="card__title" style={{ marginBottom: 'var(--space-3)' }}>Norm-Check Status</h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-4)' }}>
            <span className="badge" style={{ background: `${normColor}22`, color: normColor, fontSize: 'var(--text-sm)', padding: '4px 12px' }}>
              {inst.norm_check_status.replace(/_/g, ' ')}
            </span>
            {inst.last_inspection && <span className="text-muted" style={{ fontSize: 'var(--text-xs)' }}>Last inspection: {new Date(inst.last_inspection).toLocaleDateString('en-IN')}</span>}
          </div>
          <Link to={`/norm-check/${inst.id}`} className="btn btn--secondary btn--sm">View Full Norm-Check →</Link>
        </div>

        <div className="card">
          <h3 className="card__title" style={{ marginBottom: 'var(--space-3)' }}>Quick Actions</h3>
          <div className="flex flex-col gap-2">
            <Link to={`/compliance/${inst.id}`} className="btn btn--secondary">📡 Compliance Radar</Link>
            <Link to={`/replies/${inst.id}`} className="btn btn--secondary">💬 Institution Replies</Link>
            <Link to={`/graph?institution=${inst.id}`} className="btn btn--secondary">🔗 Case Graph</Link>
          </div>
        </div>
      </div>

      {/* Complaints list */}
      <div className="card" style={{ marginTop: 'var(--space-4)' }}>
        <h3 className="card__title" style={{ marginBottom: 'var(--space-3)' }}>Complaints Against This Institution</h3>
        {complaints.length === 0 ? <p className="text-muted">No complaints on file.</p> : (
          <table className="data-table">
            <thead><tr><th>ID</th><th>Title</th><th>Status</th><th>Urgency</th></tr></thead>
            <tbody>{complaints.map(c => (
              <tr key={c.id}><td><Link to={`/cases/${c.id}`} className="case-link font-mono">{c.tracking_id || c.id}</Link></td><td>{c.title}</td><td><StatusBadge status={c.status} /></td><td>{c.urgency}</td></tr>
            ))}</tbody>
          </table>
        )}
      </div>
    </div>
  );
}

/* Institution List */
export function InstitutionList() {
  const { isDemoMode } = useAuth();
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => { institutionsApi.list().then(setInstitutions).finally(() => setLoading(false)); }, []);

  const filtered = search ? institutions.filter(i => i.name.toLowerCase().includes(search.toLowerCase()) || i.state.toLowerCase().includes(search.toLowerCase())) : institutions;

  if (loading) return <div className="page-content"><LoadingState /></div>;

  return (
    <div className="page-content animate-fade-in">
      {isDemoMode && <DemoBanner />}
      <PageHeader title="Institution 360" subtitle={`${institutions.length} AICTE-approved institutions`} />
      <div className="filter-bar" style={{ marginBottom: 'var(--space-4)' }}>
        <div className="filter-group filter-group--search">
          <input className="form-input" placeholder="Search institutions..." value={search} onChange={e => setSearch(e.target.value)} />
        </div>
      </div>
      <div className="institution-grid">
        {filtered.map(inst => {
          const normColor = inst.norm_check_status === 'COMPLIANT' ? 'var(--status-success)' : inst.norm_check_status === 'NON_COMPLIANT' ? 'var(--status-danger)' : 'var(--status-warning)';
          return (
            <Link to={`/institutions/${inst.id}`} key={inst.id} className="institution-card card">
              <div className="institution-card__header">
                <h3 className="institution-card__name">{inst.name}</h3>
                <span className="badge" style={{ background: `${normColor}22`, color: normColor }}>{inst.norm_check_status.replace(/_/g, ' ')}</span>
              </div>
              <p className="text-muted" style={{ fontSize: 'var(--text-sm)' }}>{inst.city}, {inst.state} · {inst.type}</p>
              <div className="institution-card__stats">
                <span>📋 {inst.total_complaints} complaints</span>
                <span>⚠ {inst.open_complaints} open</span>
                <span>📊 Score: {inst.compliance_score}</span>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
