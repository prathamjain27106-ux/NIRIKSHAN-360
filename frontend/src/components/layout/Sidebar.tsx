import { NavLink } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext';

interface NavItem { path: string; label: string; icon: string; badge?: number; roles?: string[] }

const navSections: { label: string; items: NavItem[] }[] = [
  {
    label: 'Overview',
    items: [{ path: '/', label: 'Command Centre', icon: '📊' }],
  },
  {
    label: 'Operations',
    items: [
      { path: '/complaints/new', label: 'Submit Complaint', icon: '📝' },
      { path: '/cases', label: 'Complaint Queue', icon: '📋', badge: 12 },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { path: '/institutions', label: 'Institution 360', icon: '🏛️' },
      { path: '/pulse', label: 'Systemic Pulse', icon: '💓' },
      { path: '/graph', label: 'Case Graph', icon: '🔗' },
    ],
  },
  {
    label: 'Administration',
    items: [
      { path: '/audit', label: 'Audit Log', icon: '🔒', roles: ['ADMIN', 'AUDITOR', 'BUREAU_HEAD'] },
    ],
  },
];

export function Sidebar() {
  const { user, isDemoMode } = useAuth();

  return (
    <aside className="sidebar" role="navigation" aria-label="Main Navigation">
      <div className="sidebar__brand">
        <div className="sidebar__brand-icon" aria-hidden="true">N</div>
        <div className="sidebar__brand-text">
          <span className="sidebar__brand-name">NIRIKSHAN 360</span>
          <span className="sidebar__brand-subtitle">AICTE Complaint Monitor</span>
        </div>
      </div>

      <nav className="sidebar__nav">
        {navSections.map((section) => (
          <div key={section.label}>
            <div className="sidebar__section-label">{section.label}</div>
            {section.items.filter(item => {
              if (!item.roles) return true;
              return user && item.roles.includes(user.role);
            }).map((item) => (
              <NavLink
                key={item.path} to={item.path} end={item.path === '/'}
                className={({ isActive }) => `sidebar__link ${isActive ? 'sidebar__link--active' : ''}`}
              >
                <span className="sidebar__link-icon" aria-hidden="true">{item.icon}</span>
                <span>{item.label}</span>
                {item.badge !== undefined && <span className="sidebar__link-badge" aria-label={`${item.badge} pending`}>{item.badge}</span>}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar__footer">
        {isDemoMode && (
          <div className="sidebar__demo-badge">
            <span aria-hidden="true">⚠️</span>
            <span>SYNTHETIC DEMO DATA</span>
          </div>
        )}
        {user && (
          <div className="sidebar__user-mini">
            <span className="sidebar__user-role-badge">{user.role.replace(/_/g, ' ')}</span>
            {user.cell && <span className="text-muted" style={{ fontSize: 'var(--text-xs)' }}>{user.cell}</span>}
          </div>
        )}
      </div>
    </aside>
  );
}
