/* Case Details — full case view with timeline, explainable triage, duplicate review & auditable overrides */
import { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { complaintsApi } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import type { Complaint, DuplicateCandidate } from '../types';
import {
  PageHeader, DemoBanner, LoadingState, ErrorState, StatusBadge,
  UrgencyBadge, CellBadge, SlaCountdown, ConfidenceMeter, Timeline,
} from '../components/common';

export function CaseDetails() {
  const { id } = useParams<{ id: string }>();
  const { isDemoMode, user } = useAuth();
  const [complaint, setComplaint] = useState<Complaint | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Human Override State
  const [showOverrideModal, setShowOverrideModal] = useState(false);
  const [overrideField, setOverrideField] = useState<'category' | 'urgency' | 'cell' | 'sla_deadline' | 'approve_triage'>('category');
  const [overrideValue, setOverrideValue] = useState('');
  const [overrideReason, setOverrideReason] = useState('');
  const [overrideSubmitting, setOverrideSubmitting] = useState(false);

  // Duplicates State
  const [showDuplicatesModal, setShowDuplicatesModal] = useState(false);
  const [duplicatesLoading, setDuplicatesLoading] = useState(false);
  const [duplicateCandidates, setDuplicateCandidates] = useState<DuplicateCandidate[]>([]);
  const [duplicatePolicy, setDuplicatePolicy] = useState('');
  const [actionNotes, setActionNotes] = useState('');
  const [selectedCandidate, setSelectedCandidate] = useState<string | null>(null);
  const [dupActionSubmitting, setDupActionSubmitting] = useState(false);

  const fetchCase = useCallback(async () => {
    if (!id) return;
    try {
      const data = await complaintsApi.get(id);
      setComplaint(data);
    } catch {
      setError('Case not found');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchCase();
  }, [fetchCase]);

  const loadDuplicates = async () => {
    if (!complaint) return;
    setDuplicatesLoading(true);
    setActionError(null);
    try {
      const res = await complaintsApi.getDuplicates(complaint.tracking_id || complaint.id);
      setDuplicateCandidates(res.candidates);
      setDuplicatePolicy(res.policy);
      setShowDuplicatesModal(true);
    } catch {
      setActionError('Could not load duplicate candidates.');
    } finally {
      setDuplicatesLoading(false);
    }
  };

  const handleLinkDuplicate = async (canonicalTrackingId: string) => {
    if (!complaint || !actionNotes.trim()) {
      setActionError('A valid officer justification is required to link duplicate cases.');
      return;
    }
    setDupActionSubmitting(true);
    setActionError(null);
    try {
      await complaintsApi.linkDuplicate(complaint.tracking_id || complaint.id, canonicalTrackingId, actionNotes);
      setActionSuccess(`Linked as duplicate of ${canonicalTrackingId}.`);
      setSelectedCandidate(null);
      setActionNotes('');
      setShowDuplicatesModal(false);
      await fetchCase();
    } catch {
      setActionError('Failed to link duplicate case.');
    } finally {
      setDupActionSubmitting(false);
    }
  };

  const handleDismissDuplicate = async (candidateTrackingId: string) => {
    if (!complaint || !actionNotes.trim()) {
      setActionError('A reason is required to dismiss a false-positive candidate.');
      return;
    }
    setDupActionSubmitting(true);
    setActionError(null);
    try {
      await complaintsApi.dismissDuplicate(complaint.tracking_id || complaint.id, candidateTrackingId, actionNotes);
      setActionSuccess(`Candidate ${candidateTrackingId} dismissed as false positive.`);
      setSelectedCandidate(null);
      setActionNotes('');
      setDuplicateCandidates(prev => prev.filter(c => (c.complaint.tracking_id || c.complaint.id) !== candidateTrackingId));
      await fetchCase();
    } catch {
      setActionError('Failed to dismiss candidate.');
    } finally {
      setDupActionSubmitting(false);
    }
  };

  const handleApplyOverride = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!complaint || !overrideReason.trim()) {
      setActionError('An auditable explanation is strictly required for human overrides.');
      return;
    }
    setOverrideSubmitting(true);
    setActionError(null);
    try {
      const res = await complaintsApi.override(
        complaint.tracking_id || complaint.id,
        overrideField,
        overrideValue,
        overrideReason,
      );
      setComplaint(res.complaint);
      setActionSuccess(`Human override applied: ${res.message}`);
      setShowOverrideModal(false);
      setOverrideReason('');
      setOverrideValue('');
    } catch {
      setActionError('Override could not be applied. Please check input values.');
    } finally {
      setOverrideSubmitting(false);
    }
  };

  if (loading) return <div className="page-content"><LoadingState message="Loading case..." /></div>;
  if (error || !complaint) return <div className="page-content"><ErrorState message={error || 'Case not found'} /></div>;

  const canEscalate = user?.role === 'ADMIN' || user?.role === 'BUREAU_HEAD';
  const canAssign = user?.role === 'ADMIN' || user?.role === 'ANALYST';
  const canOverride = user?.role === 'ADMIN' || user?.role === 'BUREAU_HEAD' || user?.role === 'ANALYST';

  const changeStatus = async (status: Complaint['status'], reason: string) => {
    if (!complaint) return;
    setActionError(null);
    setActionSuccess(null);
    try {
      setComplaint(await complaintsApi.updateStatus(complaint.tracking_id || complaint.id, status, reason));
      setActionSuccess(`Status changed to ${status}.`);
    } catch {
      setActionError('The status could not be updated. Please try again.');
    }
  };

  return (
    <div className="page-content animate-fade-in">
      {isDemoMode && <DemoBanner />}
      <PageHeader title={complaint.tracking_id || complaint.id} subtitle={complaint.title}>
        <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
          <button className="btn btn--secondary" onClick={loadDuplicates} disabled={duplicatesLoading}>
            🔍 {duplicatesLoading ? 'Scanning...' : 'Check Duplicates'}
          </button>
          {canOverride && (
            <button className="btn btn--primary" onClick={() => setShowOverrideModal(true)}>
              ⚖ Human Override
            </button>
          )}
          <Link to="/cases" className="btn btn--secondary">← Back to Queue</Link>
        </div>
      </PageHeader>

      {actionSuccess && <div className="alert alert--success" style={{ marginBottom: 'var(--space-3)' }}>{actionSuccess}</div>}
      {actionError && <div className="alert alert--danger" style={{ marginBottom: 'var(--space-3)' }}>{actionError}</div>}

      {/* Status bar */}
      <div className="case-status-bar">
        <div className="case-status-bar__item"><span className="case-status-bar__label">Status</span><StatusBadge status={complaint.status} /></div>
        <div className="case-status-bar__item"><span className="case-status-bar__label">Urgency</span><UrgencyBadge urgency={complaint.urgency} /></div>
        <div className="case-status-bar__item"><span className="case-status-bar__label">Cell</span><CellBadge cell={complaint.cell} /></div>
        <div className="case-status-bar__item"><span className="case-status-bar__label">SLA</span><SlaCountdown deadline={complaint.sla_deadline} status={complaint.status} /></div>
        <div className="case-status-bar__item"><span className="case-status-bar__label">Confidence</span><ConfidenceMeter value={complaint.routing_confidence} /></div>
        {complaint.needs_human_review && <div className="case-status-bar__item"><span className="badge badge--status-progress">⚖ Needs Human Review</span></div>}
        {complaint.is_duplicate_flagged && <div className="case-status-bar__item"><span className="badge badge--status-progress">⚠ Linked Duplicate of {complaint.duplicate_of}</span></div>}
      </div>

      <div className="case-layout">
        {/* Main content */}
        <div className="case-main">
          {/* Explainable Triage Card */}
          <div className="card" style={{ borderLeft: '4px solid var(--accent)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-2)' }}>
              <h3 className="card__title">🤖 Explainable Multilingual Triage</h3>
              <span className="badge" style={{ background: 'rgba(56, 189, 248, 0.15)', color: 'var(--accent)', fontSize: 'var(--text-xs)' }}>
                {complaint.triage_method || 'rule-based/assisted triage'}
              </span>
            </div>
            <p className="text-muted" style={{ fontSize: 'var(--text-sm)', marginBottom: 'var(--space-3)' }}>
              Confidence Score: <strong>{complaint.routing_confidence}%</strong> (Threshold: 75%).
              {complaint.needs_human_review ? ' ⚠ Uncertain recommendation requires human review.' : ' Automated classification meets confidence criteria.'}
            </p>
            {complaint.triage_reasons && complaint.triage_reasons.length > 0 && (
              <div style={{ background: 'var(--bg-primary)', padding: 'var(--space-3)', borderRadius: 'var(--radius-md)' }}>
                <div style={{ fontWeight: 600, fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '4px' }}>EXPLAINABILITY REASONS:</div>
                <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: 'var(--text-sm)', lineHeight: 1.6 }}>
                  {complaint.triage_reasons.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            )}
            {complaint.needs_human_review && canOverride && (
              <div style={{ marginTop: 'var(--space-3)', display: 'flex', gap: 'var(--space-2)' }}>
                <button
                  className="btn btn--primary btn--sm"
                  onClick={() => {
                    setOverrideField('approve_triage');
                    setOverrideValue('');
                    setOverrideReason('Officer confirmed triage classification upon human review.');
                    setShowOverrideModal(true);
                  }}
                >
                  ✓ Approve Triage
                </button>
                <button
                  className="btn btn--secondary btn--sm"
                  onClick={() => {
                    setOverrideField('category');
                    setShowOverrideModal(true);
                  }}
                >
                  ✎ Override Category / Cell
                </button>
              </div>
            )}
          </div>

          <div className="card" style={{ marginTop: 'var(--space-4)' }}>
            <h3 className="card__title" style={{ marginBottom: 'var(--space-3)' }}>Description</h3>
            <p style={{ lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>{complaint.description}</p>
            <div className="case-meta">
              <span>📅 Submitted: {new Date(complaint.created_at || complaint.submitted_at || '').toLocaleString('en-IN')}</span>
              <span>🌐 Language: {complaint.language === 'hi' ? 'Hindi' : complaint.language === 'hinglish' ? 'Hinglish' : 'English'}</span>
              <span>📎 Evidence: {complaint.evidence_count} file(s)</span>
              <span>👤 Assigned: {complaint.assigned_to_username || complaint.assigned_to || 'Unassigned'}</span>
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
              <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                {complaint.institution_id && (
                  <>
                    <Link to={`/institutions/${complaint.institution_id}`} className="btn btn--secondary btn--sm">View Institution 360</Link>
                    <Link to={`/norm-check/${complaint.institution_id}`} className="btn btn--secondary btn--sm">Norm-Check</Link>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Identity Protection Notice */}
          <div className="card card--identity" style={{ marginTop: 'var(--space-4)' }}>
            <h3 className="card__title" style={{ marginBottom: 'var(--space-3)' }}>🔒 Complainant Identity</h3>
            <p className="text-muted" style={{ fontSize: 'var(--text-sm)' }}>
              Identity is encrypted with AES-GCM. Revealing requires two distinct authorized approvals and creates an audit event.
            </p>
            <div className="font-mono" style={{ background: 'var(--bg-primary)', padding: 'var(--space-3)', borderRadius: 'var(--radius-md)', marginTop: 'var(--space-3)', color: 'var(--text-muted)' }}>
              {complaint.complainant_encrypted_display || complaint.complainant_encrypted}
            </div>
            {(user?.role === 'ADMIN' || user?.role === 'BUREAU_HEAD') && (
              <button className="btn btn--danger btn--sm" style={{ marginTop: 'var(--space-3)' }}>
                Request Identity Reveal (Requires Dual Approval)
              </button>
            )}
          </div>

          {/* Actions */}
          <div className="case-actions" style={{ marginTop: 'var(--space-4)' }}>
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
          </div>
        </div>

        {/* Timeline sidebar */}
        <div className="case-sidebar">
          <div className="card">
            <h3 className="card__title" style={{ marginBottom: 'var(--space-4)' }}>Case Journey & Audit Trail</h3>
            <Timeline events={complaint.timeline.map(e => ({
              id: e.id,
              timestamp: e.timestamp || (e as any).created_at,
              action: e.action,
              actor: (e as any).actor_name || e.actor || 'System',
              detail: e.detail,
              type: e.type || (e as any).event_type?.toLowerCase() || 'system',
            }))} />
          </div>
        </div>
      </div>

      {/* Human Override Modal */}
      {showOverrideModal && (
        <div className="modal-backdrop" style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div className="card" style={{ maxWidth: 500, width: '90%', padding: 'var(--space-4)' }}>
            <h3 className="card__title" style={{ marginBottom: 'var(--space-3)' }}>⚖ Auditable Human Override</h3>
            <p className="text-muted" style={{ fontSize: 'var(--text-sm)', marginBottom: 'var(--space-3)' }}>
              All overrides are permanently logged to the immutable audit trail with your identity and reason.
            </p>
            <form onSubmit={handleApplyOverride}>
              <div className="form-group" style={{ marginBottom: 'var(--space-3)' }}>
                <label className="form-label">Field to Override</label>
                <select className="form-input form-select" value={overrideField} onChange={e => setOverrideField(e.target.value as any)}>
                  <option value="category">Category</option>
                  <option value="urgency">Urgency / Priority</option>
                  <option value="cell">Destination Cell</option>
                  <option value="sla_deadline">SLA Deadline (ISO Date)</option>
                  <option value="approve_triage">Approve Triage (Clear Review Flag)</option>
                </select>
              </div>

              {overrideField === 'category' && (
                <div className="form-group" style={{ marginBottom: 'var(--space-3)' }}>
                  <label className="form-label">New Category</label>
                  <select className="form-input form-select" value={overrideValue} onChange={e => setOverrideValue(e.target.value)} required>
                    <option value="">Select Category</option>
                    <option value="FEE_REFUND">Fee Refund</option>
                    <option value="CERTIFICATE_WITHHOLDING">Certificate Withholding</option>
                    <option value="RAGGING">Ragging</option>
                    <option value="SEXUAL_HARASSMENT">Sexual Harassment</option>
                    <option value="SCHOLARSHIP_ISSUE">Scholarship Issue</option>
                    <option value="APPROVAL_VIOLATION">Approval Violation</option>
                    <option value="FACULTY_ISSUE">Faculty Issue</option>
                    <option value="INFRASTRUCTURE">Infrastructure</option>
                    <option value="ADMISSION_IRREGULARITY">Admission Irregularity</option>
                    <option value="OTHER">Other</option>
                  </select>
                </div>
              )}

              {overrideField === 'urgency' && (
                <div className="form-group" style={{ marginBottom: 'var(--space-3)' }}>
                  <label className="form-label">New Urgency</label>
                  <select className="form-input form-select" value={overrideValue} onChange={e => setOverrideValue(e.target.value)} required>
                    <option value="">Select Urgency</option>
                    <option value="CRITICAL">Critical</option>
                    <option value="HIGH">High</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="LOW">Low</option>
                  </select>
                </div>
              )}

              {overrideField === 'cell' && (
                <div className="form-group" style={{ marginBottom: 'var(--space-3)' }}>
                  <label className="form-label">New Destination Cell</label>
                  <select className="form-input form-select" value={overrideValue} onChange={e => setOverrideValue(e.target.value)} required>
                    <option value="">Select Cell</option>
                    <option value="RB">Regulation Bureau (RB)</option>
                    <option value="PGRC">Public Grievance Redressal Cell (PGRC)</option>
                    <option value="ANTI_RAGGING">Anti-Ragging Cell</option>
                    <option value="ICC">Internal Complaints Committee (ICC)</option>
                    <option value="SCHOLARSHIP">Scholarship Cell</option>
                  </select>
                </div>
              )}

              {overrideField === 'sla_deadline' && (
                <div className="form-group" style={{ marginBottom: 'var(--space-3)' }}>
                  <label className="form-label">New SLA Deadline</label>
                  <input type="datetime-local" className="form-input" value={overrideValue} onChange={e => setOverrideValue(e.target.value)} required />
                </div>
              )}

              <div className="form-group" style={{ marginBottom: 'var(--space-4)' }}>
                <label className="form-label">Justification / Reason (Required) *</label>
                <textarea
                  className="form-input form-textarea"
                  rows={3}
                  placeholder="Provide detailed reason for audit trail..."
                  value={overrideReason}
                  onChange={e => setOverrideReason(e.target.value)}
                  required
                />
              </div>

              <div style={{ display: 'flex', gap: 'var(--space-2)', justifyContent: 'flex-end' }}>
                <button type="button" className="btn btn--secondary" onClick={() => setShowOverrideModal(false)}>Cancel</button>
                <button type="submit" className="btn btn--primary" disabled={overrideSubmitting}>
                  {overrideSubmitting ? 'Applying...' : 'Apply Override'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Duplicate Candidates Review Modal */}
      {showDuplicatesModal && (
        <div className="modal-backdrop" style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, overflowY: 'auto', padding: 'var(--space-4)' }}>
          <div className="card" style={{ maxWidth: 750, width: '100%', maxHeight: '90vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-3)' }}>
              <h3 className="card__title">⚠ Duplicate Candidate Detection</h3>
              <button className="btn btn--secondary btn--sm" onClick={() => setShowDuplicatesModal(false)}>✕ Close</button>
            </div>
            <p className="text-muted" style={{ fontSize: 'var(--text-xs)', marginBottom: 'var(--space-3)' }}>
              {duplicatePolicy || 'Candidates presented with similarity breakdown. Officer confirmation required before linking. Cases are never auto-merged.'}
            </p>

            {duplicateCandidates.length === 0 ? (
              <p className="text-muted" style={{ padding: 'var(--space-4)', textAlign: 'center' }}>No probable duplicate candidates found.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                {duplicateCandidates.map(cand => {
                  const cTracking = cand.complaint.tracking_id || cand.complaint.id;
                  const isSelected = selectedCandidate === cTracking;
                  return (
                    <div key={cTracking} className="card" style={{ border: isSelected ? '2px solid var(--accent)' : '1px solid var(--border-color)', padding: 'var(--space-3)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div>
                          <span className="font-mono font-bold" style={{ color: 'var(--accent)' }}>{cTracking}</span>
                          <span style={{ marginLeft: 8, fontWeight: 600 }}>{cand.complaint.title}</span>
                          <div className="text-muted" style={{ fontSize: 'var(--text-xs)', marginTop: 2 }}>
                            {cand.complaint.institution_name} · {cand.complaint.category} · {cand.complaint.status}
                          </div>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <span className="badge" style={{ background: cand.similarity_score >= 70 ? 'rgba(239, 68, 68, 0.2)' : 'rgba(234, 179, 8, 0.2)', color: cand.similarity_score >= 70 ? 'var(--status-danger)' : 'var(--status-warning)', fontWeight: 600 }}>
                            {cand.similarity_score}% Match
                          </span>
                        </div>
                      </div>

                      <div style={{ marginTop: 'var(--space-2)', fontSize: 'var(--text-xs)', display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
                        <span className="badge">Inst: {cand.factors.institution_similarity}%</span>
                        <span className="badge">Category: {cand.factors.category_similarity}%</span>
                        <span className="badge">Date: {cand.factors.date_similarity}% ({cand.days_apart}d)</span>
                        <span className="badge">Text: {cand.factors.text_similarity}%</span>
                      </div>

                      <p style={{ marginTop: 'var(--space-2)', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                        {cand.similarity_explanation}
                      </p>

                      {isSelected ? (
                        <div style={{ marginTop: 'var(--space-3)', padding: 'var(--space-3)', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)' }}>
                          <label className="form-label" style={{ fontSize: 'var(--text-xs)' }}>Officer Confirmation Note (Required) *</label>
                          <textarea
                            className="form-input form-textarea"
                            rows={2}
                            placeholder="Enter justification for linking or dismissing..."
                            value={actionNotes}
                            onChange={e => setActionNotes(e.target.value)}
                          />
                          <div style={{ display: 'flex', gap: 'var(--space-2)', marginTop: 'var(--space-2)', justifyContent: 'flex-end' }}>
                            <button className="btn btn--secondary btn--sm" onClick={() => setSelectedCandidate(null)}>Cancel</button>
                            <button
                              className="btn btn--secondary btn--sm"
                              onClick={() => handleDismissDuplicate(cTracking)}
                              disabled={dupActionSubmitting}
                            >
                              Dismiss False Positive
                            </button>
                            <button
                              className="btn btn--primary btn--sm"
                              onClick={() => handleLinkDuplicate(cTracking)}
                              disabled={dupActionSubmitting}
                            >
                              Confirm & Link Duplicate
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div style={{ display: 'flex', gap: 'var(--space-2)', marginTop: 'var(--space-2)', justifyContent: 'flex-end' }}>
                          <button
                            className="btn btn--secondary btn--sm"
                            onClick={() => { setSelectedCandidate(cTracking); setActionNotes('Confirmed identical incident from the same institution.'); }}
                          >
                            Review & Link Case
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
