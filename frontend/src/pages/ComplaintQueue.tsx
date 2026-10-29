/* Complaint Queue — filterable table of all cases */
import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { complaintsApi } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import type { Complaint, ComplaintFilters } from '../types';
import { PageHeader, DemoBanner, LoadingState, EmptyState, StatusBadge, UrgencyBadge, CellBadge, SlaCountdown, ConfidenceMeter, FilterBar, FilterSelect, FilterSearch } from '../components/common';
import { indianStates } from '../data/demo';

const statusOpts = [
  { value: 'SUBMITTED', label: 'Submitted' }, { value: 'TRIAGED', label: 'Triaged' },
  { value: 'ROUTED', label: 'Routed' }, { value: 'UNDER_REVIEW', label: 'Under Review' },
  { value: 'AWAITING_REPLY', label: 'Awaiting Reply' }, { value: 'RESOLVED', label: 'Resolved' },
  { value: 'ESCALATED', label: 'Escalated' }, { value: 'CLOSED', label: 'Closed' },
];
const urgencyOpts = [
  { value: 'CRITICAL', label: 'Critical' }, { value: 'HIGH', label: 'High' },
  { value: 'MEDIUM', label: 'Medium' }, { value: 'LOW', label: 'Low' },
];
const cellOpts = [
  { value: 'RB', label: 'Regulation Bureau' }, { value: 'PGRC', label: 'PGRC' },
  { value: 'ANTI_RAGGING', label: 'Anti-Ragging' }, { value: 'ICC', label: 'ICC' },
  { value: 'SCHOLARSHIP', label: 'Scholarship' },
];

export function ComplaintQueue() {
  const { isDemoMode } = useAuth();
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<ComplaintFilters>({});

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await complaintsApi.list(filters);
      setComplaints(res.results);
      setTotal(res.count);
    } catch {
      setError('Complaints could not be loaded. Please check the backend connection.');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => { load(); }, [load]);

  const updateFilter = (key: keyof ComplaintFilters, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value || undefined }));
  };

  return (
    <div className="page-content animate-fade-in">
      {isDemoMode && <DemoBanner />}
      <PageHeader title="Complaint Queue" subtitle={`${total} total cases across all bureaus and cells`}>
        <Link to="/complaints/new" className="btn btn--primary">+ New Complaint</Link>
      </PageHeader>

      <FilterBar>
        <FilterSearch value={filters.search || ''} onChange={v => updateFilter('search', v)} placeholder="Search by ID, title, description..." />
        <FilterSelect label="Status" value={filters.status || ''} onChange={v => updateFilter('status', v)} options={statusOpts} />
        <FilterSelect label="Urgency" value={filters.urgency || ''} onChange={v => updateFilter('urgency', v)} options={urgencyOpts} />
        <FilterSelect label="Cell" value={filters.cell || ''} onChange={v => updateFilter('cell', v)} options={cellOpts} />
        <FilterSelect label="State" value={filters.state || ''} onChange={v => updateFilter('state', v)} options={indianStates.map(s => ({ value: s, label: s }))} />
        <div className="filter-group">
          <label className="filter-label">Review</label>
          <label className="filter-checkbox">
            <input type="checkbox" checked={!!filters.needs_review} onChange={e => setFilters(prev => ({ ...prev, needs_review: e.target.checked || undefined }))} />
            <span>Needs Human Review</span>
          </label>
        </div>
      </FilterBar>

      {error ? <div className="alert alert--danger" role="alert">{error}</div> : loading ? <LoadingState /> : complaints.length === 0 ? (
        <EmptyState icon="📭" title="No complaints found" subtitle="Try adjusting your filters or submit a new complaint." />
      ) : (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Case ID</th><th>Title</th><th>Institution</th><th>Cell</th>
                  <th>Urgency</th><th>Status</th><th>Confidence</th><th>SLA</th>
                  <th>Review</th>
                </tr>
              </thead>
              <tbody>
                {complaints.map(c => (
                  <tr key={c.id}>
                    <td><Link to={`/cases/${c.id}`} className="case-link font-mono">{c.tracking_id || c.id}</Link></td>
                    <td className="cell-title">{c.title}{c.is_duplicate_flagged && <span className="badge badge--status-progress" style={{ marginLeft: 6 }}>⚠ Dup</span>}</td>
                    <td className="cell-inst">{c.institution_name}</td>
                    <td><CellBadge cell={c.cell} /></td>
                    <td><UrgencyBadge urgency={c.urgency} /></td>
                    <td><StatusBadge status={c.status} /></td>
                    <td><ConfidenceMeter value={c.routing_confidence} /></td>
                    <td><SlaCountdown deadline={c.sla_deadline} status={c.status} /></td>
                    <td>{c.needs_human_review ? <span className="badge badge--status-progress">⚖ Review</span> : <span className="text-muted">—</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
