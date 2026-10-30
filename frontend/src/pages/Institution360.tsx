/* Institution 360 routes */
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { institutionsApi } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import type { Institution } from '../types';
import { PageHeader, DemoBanner, LoadingState } from '../components/common';
import Institution360Workspace from '../components/Institution360.jsx';

export function Institution360() {
  return <Institution360Workspace />;
}

export function InstitutionList() {
  const { isDemoMode } = useAuth();
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => { institutionsApi.list().then(setInstitutions).finally(() => setLoading(false)); }, []);

  const filtered = search
    ? institutions.filter(i => i.name.toLowerCase().includes(search.toLowerCase()) || i.state.toLowerCase().includes(search.toLowerCase()))
    : institutions;

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
          const normColor = inst.norm_check_status === 'COMPLIANT'
            ? 'var(--status-success)'
            : inst.norm_check_status === 'NON_COMPLIANT' ? 'var(--status-danger)' : 'var(--status-warning)';
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
