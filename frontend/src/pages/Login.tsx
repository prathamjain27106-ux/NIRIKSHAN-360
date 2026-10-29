/* Login Page */
import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { demoAccounts } from '../data/demo';

export function Login() {
  const navigate = useNavigate();
  const { login, error: authError } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showAccounts, setShowAccounts] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
      navigate('/');
    } catch {
      setError(authError || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card animate-fade-in">
        <div className="login-card__logo">
          <div className="login-card__logo-icon" aria-hidden="true">N</div>
          <span className="login-card__logo-text">NIRIKSHAN 360</span>
        </div>
        <h1 className="login-card__title">Sign In</h1>
        <p className="login-card__subtitle">AICTE Integrated Complaint Monitoring Dashboard</p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username" className="form-label">Username</label>
            <input id="username" type="text" className="form-input" placeholder="Enter your username" value={username} onChange={e => setUsername(e.target.value)} required autoComplete="username" autoFocus />
          </div>
          <div className="form-group">
            <label htmlFor="password" className="form-label">Password</label>
            <input id="password" type="password" className="form-input" placeholder="Enter your password" value={password} onChange={e => setPassword(e.target.value)} required autoComplete="current-password" />
          </div>
          {error && <div className="form-error">{error}</div>}
          <button type="submit" className="btn btn--primary btn--lg w-full" disabled={loading} style={{ marginTop: 'var(--space-2)' }}>
            {loading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>

        {/* Demo Accounts */}
        <div className="login-demo-section">
          <button className="login-demo-toggle" onClick={() => setShowAccounts(!showAccounts)} type="button">
            ⚠ PROTOTYPE — {showAccounts ? 'Hide' : 'Show'} Demo Accounts
          </button>
          {showAccounts && (
            <div className="login-demo-accounts">
              <p className="login-demo-notice">Not connected to any AICTE production system</p>
              <table className="login-demo-table">
                <thead><tr><th>Username</th><th>Password</th><th>Role</th></tr></thead>
                <tbody>
                  {demoAccounts.map(a => (
                    <tr key={a.username} onClick={() => { setUsername(a.username); setPassword(a.password); }} style={{ cursor: 'pointer' }}>
                      <td className="font-mono">{a.username}</td>
                      <td className="font-mono">{a.password}</td>
                      <td>{a.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
