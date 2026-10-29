import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';

export function Login() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    // Phase 1: Simulated login (no backend auth yet).
    // Phase 2 will wire this to the JWT /api/accounts/login/ endpoint.
    await new Promise((r) => setTimeout(r, 800));

    if (username === 'admin' && password === 'admin') {
      navigate('/');
    } else {
      setError('Invalid credentials. Demo: admin / admin');
    }
    setLoading(false);
  };

  return (
    <div className="login-page">
      <div className="login-card animate-fade-in">
        {/* Logo */}
        <div className="login-card__logo">
          <div className="login-card__logo-icon" aria-hidden="true">N</div>
          <span className="login-card__logo-text">NIRIKSHAN 360</span>
        </div>

        <h1 className="login-card__title">Sign In</h1>
        <p className="login-card__subtitle">
          AICTE Integrated Complaint Monitoring Dashboard
        </p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username" className="form-label">Username</label>
            <input
              id="username"
              type="text"
              className="form-input"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoComplete="username"
              autoFocus
            />
          </div>

          <div className="form-group">
            <label htmlFor="password" className="form-label">Password</label>
            <input
              id="password"
              type="password"
              className="form-input"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </div>

          {error && (
            <div style={{
              padding: 'var(--space-2) var(--space-3)',
              background: 'hsl(0, 72%, 60%, 0.1)',
              border: '1px solid hsl(0, 72%, 60%, 0.3)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--status-danger)',
              fontSize: 'var(--text-sm)',
              marginBottom: 'var(--space-4)',
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            className="btn btn--primary btn--lg w-full"
            disabled={loading}
            style={{ marginTop: 'var(--space-2)' }}
          >
            {loading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>

        {/* Demo notice */}
        <div style={{
          marginTop: 'var(--space-6)',
          padding: 'var(--space-3)',
          background: 'hsl(38, 92%, 60%, 0.08)',
          border: '1px solid hsl(38, 92%, 60%, 0.2)',
          borderRadius: 'var(--radius-md)',
          textAlign: 'center',
        }}>
          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--status-warning)', fontWeight: 600, marginBottom: '2px' }}>
            ⚠ PROTOTYPE — SYNTHETIC DEMO DATA
          </p>
          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
            Demo credentials: <span className="font-mono" style={{ color: 'var(--text-secondary)' }}>admin / admin</span>
          </p>
          <p style={{ fontSize: '0.625rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Not connected to any AICTE production system
          </p>
        </div>
      </div>
    </div>
  );
}
