import { useLocation } from 'react-router-dom';

const pageTitles: Record<string, string> = {
  '/': 'Command Centre',
  '/complaints': 'Complaint Intake',
  '/cases': 'Case Tracker',
  '/triage': 'Triage Review',
  '/institutions': 'Institution 360',
  '/compliance': 'Compliance Radar',
  '/pulse': 'Systemic Pulse',
  '/graph': 'Case Graph',
  '/audit': 'Audit Log',
  '/import': 'CSV Import',
};

export function Header() {
  const location = useLocation();
  const currentTitle = pageTitles[location.pathname] || 'NIRIKSHAN 360';

  return (
    <header className="header" role="banner">
      <div className="header__breadcrumb" aria-label="Breadcrumb">
        <span>NIRIKSHAN 360</span>
        <span className="header__breadcrumb-separator" aria-hidden="true">/</span>
        <span className="header__breadcrumb-current">{currentTitle}</span>
      </div>

      <div className="header__actions">
        {/* Notification bell placeholder */}
        <button
          className="btn btn--secondary btn--sm"
          aria-label="Notifications"
          title="Notifications"
          style={{ padding: '6px 8px' }}
        >
          🔔
        </button>

        {/* User info */}
        <div className="header__user-info" tabIndex={0} role="button" aria-label="User menu">
          <div className="header__avatar" aria-hidden="true">SA</div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span className="header__user-name">System Admin</span>
            <span className="header__user-role">Administrator</span>
          </div>
        </div>
      </div>
    </header>
  );
}
