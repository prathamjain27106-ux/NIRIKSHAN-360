import { useEffect, useMemo, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { complaintsApi, institutionsApi } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { DemoBanner, ErrorState, LoadingState, PageHeader, StatusBadge } from './common';

const CLOSED = new Set(['RESOLVED', 'CLOSED']);

export default function Institution360Workspace() {
  const { id } = useParams();
  const { isDemoMode } = useAuth();
  const [institution, setInstitution] = useState(null);
  const [complaints, setComplaints] = useState([]);
  const [evidence, setEvidence] = useState([]);
  const [replies, setReplies] = useState([]);
  const [tab, setTab] = useState('overview');
  const [now, setNow] = useState(Date.now());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return undefined;
    Promise.all([
      institutionsApi.get(id),
      complaintsApi.list({ institution: id }),
      institutionsApi.normCheck(id),
      institutionsApi.replies(id),
    ]).then(([profile, cases, norms, institutionReplies]) => {
      setInstitution(profile);
      setComplaints(cases.results || []);
      setEvidence(norms || []);
      setReplies(institutionReplies || []);
    }).finally(() => setLoading(false));
    return undefined;
  }, [id]);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  const active = complaints.filter((item) => !CLOSED.has(item.status));
  const overdue = active.filter((item) => item.is_overdue || item.sla_breached);
  const byCategory = useMemo(() => active.reduce((result, item) => {
    result[item.category] = (result[item.category] || 0) + 1;
    return result;
  }, {}), [active]);
  const nextDeadline = active
    .filter((item) => item.sla_deadline)
    .sort((a, b) => new Date(a.sla_deadline) - new Date(b.sla_deadline))[0];
  const countdown = nextDeadline
    ? Math.max(0, new Date(nextDeadline.sla_deadline).getTime() - now)
    : null;

  if (loading) return <div className="page-content"><LoadingState /></div>;
  if (!institution) return <div className="page-content"><ErrorState message="Institution not found" /></div>;

  return (
    <div className="page-content animate-fade-in">
      {isDemoMode && <DemoBanner />}
      <PageHeader title={institution.name} subtitle={`AICTE Permanent ID: ${institution.aicte_id}`}>
        <Link to="/institutions" className="btn btn--secondary">← All Institutions</Link>
      </PageHeader>
      <div className="filter-bar">
        {['overview', 'evidence', 'responses'].map((name) => (
          <button type="button" className={`btn ${tab === name ? 'btn--primary' : 'btn--secondary'}`} onClick={() => setTab(name)} key={name}>
            {name[0].toUpperCase() + name.slice(1)}
          </button>
        ))}
      </div>
      {tab === 'overview' && (
        <>
          <div className="kpi-grid">
            <div className="card kpi-card"><span className="kpi-card__label">Verified capacity</span><strong className="kpi-card__value">{institution.student_count?.toLocaleString() || '—'}</strong></div>
            <div className="card kpi-card"><span className="kpi-card__label">Intake limit</span><strong className="kpi-card__value">{(institution.intake_limit || institution.student_count)?.toLocaleString() || '—'}</strong></div>
            <div className="card kpi-card"><span className="kpi-card__label">Active complaints</span><strong className="kpi-card__value">{active.length}</strong></div>
            <div className="card kpi-card"><span className="kpi-card__label">Overdue cases</span><strong className="kpi-card__value" style={{ color: overdue.length ? 'var(--status-danger)' : undefined }}>{overdue.length}</strong></div>
            <div className="card kpi-card"><span className="kpi-card__label">Compliance</span><strong className="kpi-card__value">{institution.compliance_score}/100</strong><span className="text-muted">{institution.norm_check_status.replace(/_/g, ' ')}</span></div>
          </div>
          <div className="charts-grid">
            <div className="card"><h3 className="card__title">Active complaints by category</h3>{Object.keys(byCategory).length ? Object.entries(byCategory).map(([category, count]) => <div key={category} style={{ display: 'flex', justifyContent: 'space-between', padding: 'var(--space-2) 0' }}><span>{category.replace(/_/g, ' ')}</span><strong>{count}</strong></div>) : <p className="text-muted">No telemetry returned.</p>}</div>
            <div className="card"><h3 className="card__title">Live SLA tracker</h3>{countdown === null ? <p className="text-muted">No active deadline telemetry.</p> : <><p className="font-mono" style={{ fontSize: 'var(--text-2xl)', color: overdue.includes(nextDeadline) ? 'var(--status-danger)' : 'var(--accent)' }}>{Math.floor(countdown / 3600000)}h {Math.floor((countdown % 3600000) / 60000)}m {Math.floor((countdown % 60000) / 1000)}s</p><p className="text-muted">Next case: {nextDeadline.tracking_id}</p></>}</div>
          </div>
        </>
      )}
      {tab === 'evidence' && <div className="card"><h3 className="card__title">Confirmed evidence references</h3>{evidence.length ? <table className="data-table"><thead><tr><th>Norm</th><th>Finding</th><th>Reference</th><th>Verified</th></tr></thead><tbody>{evidence.map((item) => <tr key={item.id || item.norm}><td>{item.norm}</td><td>{item.finding}</td><td>{item.source_url ? <a href={item.source_url} target="_blank" rel="noreferrer">Source</a> : '—'}</td><td>{item.verified_at ? new Date(item.verified_at).toLocaleString('en-IN') : '—'}</td></tr>)}</tbody></table> : <p className="text-muted">No verified evidence telemetry returned.</p>}</div>}
      {tab === 'responses' && <div className="card"><h3 className="card__title">Formal institution responses</h3>{replies.length ? replies.map((reply) => <article key={reply.id} style={{ borderBottom: '1px solid var(--border-subtle)', padding: 'var(--space-3) 0' }}><div style={{ display: 'flex', justifyContent: 'space-between' }}><strong>{reply.submitted_by_name || 'Institution representative'}</strong><StatusBadge status={reply.status} /></div><p style={{ marginTop: 'var(--space-2)' }}>{reply.content}</p><small className="text-muted">{new Date(reply.created_at || reply.submitted_at).toLocaleString('en-IN')}</small></article>) : <p className="text-muted">No formal responses received.</p>}</div>}
    </div>
  );
}
