/* Case Details — full case view with timeline */
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { complaintsApi } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import type { Complaint } from '../types';
import { PageHeader, DemoBanner, LoadingState, ErrorState, StatusBadge, UrgencyBadge, CellBadge, SlaCountdown, ConfidenceMeter, Timeline } from '../components/common';

export function CaseDetails() {
  const { id } = useParams<{ id: string }>();
  const { isDemoMode, user } = useAuth();
  const [complaint, setComplaint] = useState<Complaint | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    complaintsApi.get(id).then(setComplaint).catch(() => setError('Case not found')).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="page-content"><LoadingState message="Loading case..." /></div>;
  if (error || !complaint) return <div className="page-content"><ErrorState message={error || 'Case not found'} /></div>;

  const canEscalate = user?.role === 'ADMIN' || user?.role === 'BUREAU_HEAD';
  const canAssign = user?.role === 'ADMIN' || user?.role === 'ANALYST';
  const changeStatus = async (status: Complaint['status'], reason: string) => {
    if (!complaint) return;
    setActionError(null);
    try {
      setComplaint(await complaintsApi.updateStatus(complaint.id, status, reason));
    } catch {
      setActionError('The status could not be updated. Please try again.');
    }
  };

  return (
    <div className="page-content animate-fade-in">
      {isDemoMode && <DemoBanner />}
      <PageHeader title={complaint.tracking_id || complaint.id} subtitle={complaint.title}>
        <Link to="/cases" className="btn btn--secondary">← Back to Queue</Link>
      </PageHeader>

      {/* Status bar */}
      <div className="case-status-bar">
        <div className="case-status-bar__item"><span className="case-status-bar__label">Status</span><StatusBadge status={complaint.status} /></div>
        <div className="case-status-bar__item"><span className="case-status-bar__label">Urgency</span><UrgencyBadge urgency={complaint.urgency} /></div>
        <div className="case-status-bar__item"><span className="case-status-bar__label">Cell</span><CellBadge cell={complaint.cell} /></div>
        <div className="case-status-bar__item"><span className="case-status-bar__label">SLA</span><SlaCountdown deadline={complaint.sla_deadline} status={complaint.status} /></div>
        <div className="case-status-bar__item"><span className="case-status-bar__label">Confidence</span><ConfidenceMeter value={complaint.routing_confidence} /></div>
        {complaint.needs_human_review && <div className="case-status-bar__item"><span className="badge badge--status-progress">⚖ Needs Human Review</span></div>}
        {complaint.is_duplicate_flagged && <div className="case-status-bar__item"><span className="badge badge--status-progress">⚠ Potential Duplicate of {complaint.duplicate_of}</span></div>}
      </div>

      <div className="case-layout">
        {/* Main content */}
        <div className="case-main">
          <div className="card">
            <h3 className="card__title" style={{ marginBottom: 'var(--space-3)' }}>Description</h3>
            <p style={{ lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>{complaint.description}</p>
            <div className="case-meta">
              <span>📅 Submitted: {new Date(complaint.created_at || complaint.submitted_at || '').toLocaleString('en-IN')}</span>
              <span>🌐 Language: {complaint.language === 'hi' ? 'Hindi' : complaint.language === 'hinglish' ? 'Hinglish' : 'English'}</span>
              <span>📎 Evidence: {complaint.evidence_count} file(s)</span>
              <span>👤 Assigned: {complaint.assigned_to || 'Unassigned'}</span>
            </div>
          </div>

          {/* Institution Link */}
          <div className="card" style={{ marginTop: 'var(--space-4)' }}>
            <h3 className="card__title" style={{ marginBottom: 'var(--space-3)' }}>Institution</h3>
            <div className="flex items-center justify-between">
              <div>
                <p style={{ fontWeight: 600 }}>{complaint.institution_name}</p>
                <p className="text-muted" style={{ fontSize: 'var(--text-sm)' }}>{complaint.state}</p>
              </div>
              <Link to={`/institutions/${complaint.institution_id}`} className="btn btn--secondary btn--sm">View Institution 360</Link>
            </div>
          </div>

          {/* Identity Protection Notice */}
          <div className="card card--identity" style={{ marginTop: 'var(--space-4)' }}>
            <h3 className="card__title" style={{ marginBottom: 'var(--space-3)' }}>🔒 Complainant Identity</h3>
            <p className="text-muted" style={{ fontSize: 'var(--text-sm)' }}>
              Identity is encrypted with AES-GCM. Revealing requires two distinct authorized approvals and creates an audit event.
            </p>
            <div className="font-mono" style={{ background: 'var(--bg-primary)', padding: 'var(--space-3)', borderRadius: 'var(--radius-md)', marginTop: 'var(--space-3)', color: 'var(--text-muted)' }}>
              {complaint.complainant_encrypted}
            </div>
            {(user?.role === 'ADMIN' || user?.role === 'BUREAU_HEAD') && (
              <button className="btn btn--danger btn--sm" style={{ marginTop: 'var(--space-3)' }}>
                Request Identity Reveal (Requires Dual Approval)
              </button>
            )}
          </div>

          {/* Actions */}
          <div className="case-actions" style={{ marginTop: 'var(--space-4)' }}>
            {actionError && <div className="alert alert--danger" role="alert">{actionError}</div>}
            {canAssign && complaint.status !== 'RESOLVED' && complaint.status !== 'CLOSED' && (
              <button className="btn btn--primary">Assign to Me</button>
            )}
            {canEscalate && !['ESCALATED', 'RESOLVED', 'CLOSED'].includes(complaint.status) && (
              <button className="btn btn--danger" onClick={() => changeStatus('ESCALATED', 'Escalated for management review')}>Escalate</button>
            )}
            {canAssign && ['TRIAGED', 'ROUTED'].includes(complaint.status) && (
              <button className="btn btn--primary" onClick={() => changeStatus('UNDER_REVIEW', 'Investigation started')}>Start Review</button>
            )}
            {canAssign && ['UNDER_REVIEW', 'AWAITING_REPLY', 'ESCALATED'].includes(complaint.status) && (
              <button className="btn btn--primary" onClick={() => changeStatus('RESOLVED', 'Investigation completed')}>Mark Resolved</button>
            )}
            {complaint.needs_human_review && canAssign && (
              <button className="btn btn--primary">Approve Triage</button>
            )}
            {complaint.is_duplicate_flagged && canAssign && (
              <button className="btn btn--secondary">Review Duplicate Flag</button>
            )}
          </div>
        </div>

        {/* Timeline sidebar */}
        <div className="case-sidebar">
          <div className="card">
            <h3 className="card__title" style={{ marginBottom: 'var(--space-4)' }}>Case Journey</h3>
            <Timeline events={complaint.timeline} />
          </div>
        </div>
      </div>
    </div>
  );
}
