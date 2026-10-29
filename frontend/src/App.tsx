import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { Login } from './pages/Login';
import './index.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="complaints" element={<PlaceholderPage title="Complaint Intake" subtitle="Submit and manage new complaints — Phase 3" />} />
          <Route path="cases" element={<PlaceholderPage title="Case Tracker" subtitle="Track complaint lifecycle across bureaus — Phase 3" />} />
          <Route path="triage" element={<PlaceholderPage title="Triage Review" subtitle="Review and approve low-confidence triage recommendations — Phase 3" />} />
          <Route path="institutions" element={<PlaceholderPage title="Institution 360" subtitle="Comprehensive institution profiles and compliance — Phase 4" />} />
          <Route path="compliance" element={<PlaceholderPage title="Compliance Radar" subtitle="Size-normalized compliance review signals — Phase 4" />} />
          <Route path="pulse" element={<PlaceholderPage title="Systemic Pulse" subtitle="Cross-institution trend analytics — Phase 5" />} />
          <Route path="graph" element={<PlaceholderPage title="Case Graph" subtitle="Relationship graph across complaints and institutions — Phase 6" />} />
          <Route path="audit" element={<PlaceholderPage title="Audit Log" subtitle="Complete audit trail of all system actions — Phase 2" />} />
          <Route path="import" element={<PlaceholderPage title="CSV Import" subtitle="Bulk import complaints from CSV files — Phase 6" />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

/** Placeholder for pages not yet implemented */
function PlaceholderPage({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="page-content animate-fade-in">
      <h1 className="page-title">{title}</h1>
      <p className="page-subtitle">{subtitle}</p>
      <div className="card" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
        <div style={{ fontSize: '3rem', marginBottom: '1rem', opacity: 0.3 }}>🚧</div>
        <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-md)' }}>
          This module will be implemented in a future phase.
        </p>
        <p style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)', marginTop: '0.5rem' }}>
          The backend API and full UI are part of the phased build plan.
        </p>
      </div>
    </div>
  );
}

export default App;
