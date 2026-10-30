import { useEffect, useState } from 'react';
import { complaintsApi } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { DemoBanner, LoadingState, PageHeader } from './common';

export default function SystemicPulse() {
  const { isDemoMode } = useAuth();
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    complaintsApi.systemicPulse()
      .then(setAnalysis)
      .catch(() => setError('Unable to load the live structural data stream.'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page-content"><LoadingState /></div>;
  if (error) return <div className="page-content"><div className="alert alert--danger">{error}</div></div>;

  const anomalies = analysis?.anomalies || [];
  return (
    <div className="page-content animate-fade-in">
      {isDemoMode && <DemoBanner />}
      <PageHeader title="Systemic Pulse" subtitle="Live institutional process signals and explainable correction paths" />
      {anomalies.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
          <div style={{ fontSize: '2rem' }}>✓</div>
          <h3 className="card__title">No operational anomalies detected</h3>
          <p className="text-muted">Current review activity is within configured institutional thresholds.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: 'var(--space-4)' }}>
          {anomalies.map((anomaly) => (
            <section className="card" key={anomaly.rule}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
                <div>
                  <span className="badge" style={{ color: 'var(--status-warning)', background: 'hsl(38,92%,60%,0.15)' }}>RULE TRIGGERED</span>
                  <h3 className="card__title" style={{ marginTop: 'var(--space-2)' }}>{anomaly.rule}</h3>
                </div>
                <strong style={{ color: 'var(--status-warning)' }}>{anomaly.confidence_percentage}% confidence</strong>
              </div>
              <p style={{ margin: 'var(--space-3) 0' }}>{anomaly.details}</p>
              <div className="kpi-grid">
                <div><span className="kpi-card__label">Current count</span><strong>{anomaly.current_count}</strong></div>
                <div><span className="kpi-card__label">Total cases</span><strong>{anomaly.total_count}</strong></div>
              </div>
              <button type="button" className="btn btn--primary" onClick={() => window.location.assign('/cases?needs_review=true')}>
                {anomaly.action}
              </button>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
