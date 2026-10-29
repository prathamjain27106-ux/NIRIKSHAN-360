/* Submit Complaint Form */
import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { complaintsApi } from '../api/client';
import { indianStates } from '../data/demo';
import { useAuth } from '../auth/AuthContext';
import { PageHeader, DemoBanner } from '../components/common';
import type { ComplaintCategory, LanguageCode } from '../types';

const categories: { value: ComplaintCategory; label: string }[] = [
  { value: 'FEE_REFUND', label: 'Fee Refund' }, { value: 'CERTIFICATE_WITHHOLDING', label: 'Certificate Withholding' },
  { value: 'RAGGING', label: 'Ragging' }, { value: 'SEXUAL_HARASSMENT', label: 'Sexual Harassment' },
  { value: 'SCHOLARSHIP_ISSUE', label: 'Scholarship Issue' }, { value: 'APPROVAL_VIOLATION', label: 'Approval Violation' },
  { value: 'FACULTY_ISSUE', label: 'Faculty Issue' }, { value: 'INFRASTRUCTURE', label: 'Infrastructure' },
  { value: 'ADMISSION_IRREGULARITY', label: 'Admission Irregularity' }, { value: 'OTHER', label: 'Other' },
];

export function SubmitComplaint() {
  const { isDemoMode } = useAuth();
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    title: '', description: '', category: 'OTHER' as ComplaintCategory,
    institution_name: '', state: '', language: 'en' as LanguageCode,
    complainant_name: '', complainant_contact: '',
  });

  const update = (field: string, value: string) => setForm(prev => ({ ...prev, [field]: value }));

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const complaint = await complaintsApi.create(form);
      setSuccess(complaint.tracking_id || complaint.id);
    } catch {
      setError('The complaint could not be submitted. Please check the backend connection and try again.');
    }
    setSubmitting(false);
  };

  if (success) return (
    <div className="page-content animate-fade-in">
      <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>✅</div>
        <h2 style={{ color: 'var(--status-success)', marginBottom: '0.5rem' }}>Complaint Submitted</h2>
        <p style={{ fontSize: 'var(--text-lg)', fontFamily: 'var(--font-mono)', color: 'var(--accent)', margin: '1rem 0' }}>{success}</p>
        <p className="text-muted">Your complaint has been received and will be triaged shortly.</p>
        <div className="flex gap-3" style={{ justifyContent: 'center', marginTop: '1.5rem' }}>
          <button className="btn btn--primary" onClick={() => navigate(`/cases/${success}`)}>View Case</button>
          <button className="btn btn--secondary" onClick={() => { setSuccess(null); setForm({ title: '', description: '', category: 'OTHER', institution_name: '', state: '', language: 'en', complainant_name: '', complainant_contact: '' }); }}>Submit Another</button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="page-content animate-fade-in">
      {isDemoMode && <DemoBanner />}
      <PageHeader title="Submit Complaint" subtitle="File a new complaint against an AICTE-approved institution" />

      <form onSubmit={handleSubmit} className="complaint-form">
        {error && <div className="alert alert--danger" role="alert">{error}</div>}
        <div className="card">
          <h3 className="card__title" style={{ marginBottom: 'var(--space-4)' }}>Complaint Details</h3>
          <div className="form-grid">
            <div className="form-group form-group--full">
              <label className="form-label">Title *</label>
              <input className="form-input" placeholder="Brief summary of your complaint" value={form.title} onChange={e => update('title', e.target.value)} required />
            </div>
            <div className="form-group form-group--full">
              <label className="form-label">Description *</label>
              <textarea className="form-input form-textarea" placeholder="Provide detailed description of the issue..." value={form.description} onChange={e => update('description', e.target.value)} required rows={5} />
            </div>
            <div className="form-group">
              <label className="form-label">Category *</label>
              <select className="form-input form-select" value={form.category} onChange={e => update('category', e.target.value)} required>
                {categories.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Language</label>
              <select className="form-input form-select" value={form.language} onChange={e => update('language', e.target.value)}>
                <option value="en">English</option><option value="hi">Hindi</option><option value="hinglish">Hinglish</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Institution Name *</label>
              <input className="form-input" placeholder="Name of the institution" value={form.institution_name} onChange={e => update('institution_name', e.target.value)} required />
            </div>
            <div className="form-group">
              <label className="form-label">State *</label>
              <select className="form-input form-select" value={form.state} onChange={e => update('state', e.target.value)} required>
                <option value="">Select state</option>
                {indianStates.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          </div>
        </div>

        <div className="card" style={{ marginTop: 'var(--space-4)' }}>
          <h3 className="card__title" style={{ marginBottom: 'var(--space-4)' }}>Complainant Information</h3>
          <p className="text-muted" style={{ fontSize: 'var(--text-xs)', marginBottom: 'var(--space-3)' }}>🔒 Identity will be encrypted with AES-GCM. Reveal requires dual authorization.</p>
          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">Name</label>
              <input className="form-input" placeholder="Your name (encrypted at rest)" value={form.complainant_name} onChange={e => update('complainant_name', e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Contact</label>
              <input className="form-input" placeholder="Email or phone (encrypted at rest)" value={form.complainant_contact} onChange={e => update('complainant_contact', e.target.value)} />
            </div>
          </div>
        </div>

        <div style={{ marginTop: 'var(--space-4)', display: 'flex', gap: 'var(--space-3)', justifyContent: 'flex-end' }}>
          <button type="button" className="btn btn--secondary" onClick={() => navigate('/')}>Cancel</button>
          <button type="submit" className="btn btn--primary btn--lg" disabled={submitting}>{submitting ? 'Submitting…' : 'Submit Complaint'}</button>
        </div>
      </form>
    </div>
  );
}
