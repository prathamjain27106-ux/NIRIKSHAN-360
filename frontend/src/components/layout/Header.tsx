import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext';

const pageTitles: Record<string, string> = {
  '/': 'Command Centre', '/complaints/new': 'Submit Complaint', '/cases': 'Complaint Queue',
  '/institutions': 'Institution 360', '/pulse': 'Systemic Pulse', '/graph': 'Case Graph',
  '/audit': 'Audit Log',
};

export function Header() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, isDemoMode } = useAuth();

  const currentTitle = pageTitles[location.pathname] || 
    (location.pathname.startsWith('/cases/') ? 'Case Details' :
     location.pathname.startsWith('/institutions/') ? 'Institution 360' :
     location.pathname.startsWith('/norm-check/') ? 'Norm-Check' :
     location.pathname.startsWith('/compliance/') ? 'Compliance Radar' :
     location.pathname.startsWith('/replies/') ? 'Institution Replies' : 'NIRIKSHAN 360');

  const handleLogout = () => { logout(); navigate('/login'); };

  return (
    <header className="header" role="banner">
      <div className="header__breadcrumb" aria-label="Breadcrumb">
        <span>NIRIKSHAN 360</span>
        <span className="header__breadcrumb-separator" aria-hidden="true">/</span>
        <span className="header__breadcrumb-current">{currentTitle}</span>
        {isDemoMode && <span className="header__demo-tag">DEMO</span>}
      </div>

      <div className="header__actions">
        {user && (
          <>
            <div className="header__user-info" tabIndex={0} role="button" aria-label="User menu">
              <div className="header__avatar" aria-hidden="true">
                {(user.first_name?.[0] || user.username[0]).toUpperCase()}{(user.last_name?.[0] || '').toUpperCase()}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span className="header__user-name">{user.first_name || user.username} {user.last_name}</span>
                <span className="header__user-role">{user.role.replace(/_/g, ' ')}</span>
              </div>
            </div>
            <button className="btn btn--secondary btn--sm" onClick={handleLogout} title="Sign out">⏻</button>
          </>
        )}
      </div>
    </header>
  );
}
