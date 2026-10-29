import { NavLink } from 'react-router-dom';

interface NavItem {
  path: string;
  label: string;
  icon: string;
  badge?: number;
}

const navSections: { label: string; items: NavItem[] }[] = [
  {
    label: 'Overview',
    items: [
      { path: '/', label: 'Command Centre', icon: '📊' },
    ],
  },
  {
    label: 'Operations',
    items: [
      { path: '/complaints', label: 'Complaint Intake', icon: '📝' },
      { path: '/cases', label: 'Case Tracker', icon: '📋', badge: 12 },
      { path: '/triage', label: 'Triage Review', icon: '⚖️', badge: 5 },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { path: '/institutions', label: 'Institution 360', icon: '🏛️' },
      { path: '/compliance', label: 'Compliance Radar', icon: '📡' },
      { path: '/pulse', label: 'Systemic Pulse', icon: '💓' },
      { path: '/graph', label: 'Case Graph', icon: '🔗' },
    ],
  },
  {
    label: 'Administration',
    items: [
      { path: '/audit', label: 'Audit Log', icon: '🔒' },
      { path: '/import', label: 'CSV Import', icon: '📁' },
    ],
  },
];

export function Sidebar() {
  return (
    <aside className="sidebar" role="navigation" aria-label="Main Navigation">
      {/* Brand */}
      <div className="sidebar__brand">
        <div className="sidebar__brand-icon" aria-hidden="true">N</div>
        <div className="sidebar__brand-text">
          <span className="sidebar__brand-name">NIRIKSHAN 360</span>
          <span className="sidebar__brand-subtitle">AICTE Complaint Monitor</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar__nav">
        {navSections.map((section) => (
          <div key={section.label}>
            <div className="sidebar__section-label">{section.label}</div>
            {section.items.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                className={({ isActive }) =>
                  `sidebar__link ${isActive ? 'sidebar__link--active' : ''}`
                }
              >
                <span className="sidebar__link-icon" aria-hidden="true">{item.icon}</span>
                <span>{item.label}</span>
                {item.badge !== undefined && (
                  <span className="sidebar__link-badge" aria-label={`${item.badge} pending`}>
                    {item.badge}
                  </span>
                )}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      {/* Footer — Synthetic Data Warning */}
      <div className="sidebar__footer">
        <div className="sidebar__demo-badge">
          <span aria-hidden="true">⚠️</span>
          <span>SYNTHETIC DEMO DATA</span>
        </div>
      </div>
    </aside>
  );
}
