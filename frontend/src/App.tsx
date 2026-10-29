import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './auth/AuthContext';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { Login } from './pages/Login';
import { SubmitComplaint } from './pages/SubmitComplaint';
import { ComplaintQueue } from './pages/ComplaintQueue';
import { CaseDetails } from './pages/CaseDetails';
import { Institution360, InstitutionList } from './pages/Institution360';
import { NormCheck, ComplianceRadar, CaseGraph, SystemicPulse, AuditLog, InstitutionReplies } from './pages/SpecializedPages';
import './index.css';

function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return <div className="loading-state"><div className="loading-spinner" /><p>Loading...</p></div>;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function AppRoutes() {
  const { isAuthenticated } = useAuth();
  return (
    <Routes>
      <Route path="/login" element={isAuthenticated ? <Navigate to="/" replace /> : <Login />} />
      <Route path="/" element={<AuthGuard><Layout /></AuthGuard>}>
        <Route index element={<Dashboard />} />
        <Route path="complaints/new" element={<SubmitComplaint />} />
        <Route path="cases" element={<ComplaintQueue />} />
        <Route path="cases/:id" element={<CaseDetails />} />
        <Route path="institutions" element={<InstitutionList />} />
        <Route path="institutions/:id" element={<Institution360 />} />
        <Route path="norm-check/:id" element={<NormCheck />} />
        <Route path="compliance/:id" element={<ComplianceRadar />} />
        <Route path="graph" element={<CaseGraph />} />
        <Route path="pulse" element={<SystemicPulse />} />
        <Route path="audit" element={<AuditLog />} />
        <Route path="replies/:id" element={<InstitutionReplies />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
