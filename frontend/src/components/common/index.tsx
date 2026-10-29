/* Reusable UI Components for NIRIKSHAN 360 */

import { type ReactNode, type CSSProperties, useState, useEffect } from 'react';
import type { ComplaintStatus, UrgencyLevel, CellType } from '../../types';

// ── Demo Banner ──
export function DemoBanner() {
  return (
    <div className="demo-banner" role="alert">
      <span className="demo-banner__icon">⚠</span>
      <span>DEMO DATA — This screen shows synthetic data for prototype demonstration. Not connected to any AICTE production system.</span>
    </div>
  );
}

// ── Status Badge ──
const statusColors: Record<ComplaintStatus, string> = {
  SUBMITTED: 'status-open', TRIAGED: 'status-open', ROUTED: 'status-progress',
  UNDER_REVIEW: 'status-progress', AWAITING_REPLY: 'status-progress',
  RESOLVED: 'status-resolved', ESCALATED: 'status-escalated', CLOSED: 'status-resolved',
};
const statusLabels: Record<ComplaintStatus, string> = {
  SUBMITTED: 'Submitted', TRIAGED: 'Triaged', ROUTED: 'Routed',
  UNDER_REVIEW: 'Under Review', AWAITING_REPLY: 'Awaiting Reply',
  RESOLVED: 'Resolved', ESCALATED: 'Escalated', CLOSED: 'Closed',
};

export function StatusBadge({ status }: { status: ComplaintStatus }) {
  return <span className={`badge badge--${statusColors[status]}`}>{statusLabels[status]}</span>;
}

// ── Urgency Badge ──
const urgencyColors: Record<UrgencyLevel, string> = {
  CRITICAL: 'status-escalated', HIGH: 'status-progress', MEDIUM: 'status-open', LOW: 'status-resolved',
};
export function UrgencyBadge({ urgency }: { urgency: UrgencyLevel }) {
  return <span className={`badge badge--${urgencyColors[urgency]}`}>{urgency}</span>;
}

// ── Cell Badge ──
const cellLabels: Record<string, string> = {
  RB: 'Regulation Bureau', PGRC: 'PGRC', ANTI_RAGGING: 'Anti-Ragging',
  ICC: 'ICC', SCHOLARSHIP: 'Scholarship',
};
const cellCssMap: Record<string, string> = {
  RB: 'cell-rb', PGRC: 'cell-pgrc', ANTI_RAGGING: 'cell-antiragging',
  ICC: 'cell-icc', SCHOLARSHIP: 'cell-scholarship',
};
export function CellBadge({ cell }: { cell: CellType | string }) {
  if (!cell) return <span className="badge" style={{ opacity: 0.5 }}>Unassigned</span>;
  return <span className={`badge badge--${cellCssMap[cell] || ''}`}>{cellLabels[cell] || cell}</span>;
}

// ── Confidence Meter ──
export function ConfidenceMeter({ value, showLabel = true }: { value: number; showLabel?: boolean }) {
  const color = value >= 85 ? 'var(--status-success)' : value >= 60 ? 'var(--status-warning)' : 'var(--status-danger)';
  return (
    <div className="confidence-meter" title={`Routing confidence: ${value}%`}>
      <div className="confidence-meter__bar">
        <div className="confidence-meter__fill" style={{ width: `${value}%`, background: color }} />
      </div>
      {showLabel && <span className="confidence-meter__label" style={{ color }}>{value}%</span>}
    </div>
  );
}

// ── SLA Countdown ──
export function SlaCountdown({ deadline, status }: { deadline: string; status: ComplaintStatus }) {
  const [timeLeft, setTimeLeft] = useState('');
  const [slaClass, setSlaClass] = useState('safe');

  useEffect(() => {
    if (['RESOLVED', 'CLOSED'].includes(status)) { setTimeLeft('—'); return; }
    const update = () => {
      const diff = new Date(deadline).getTime() - Date.now();
      if (diff <= 0) { setTimeLeft('BREACHED'); setSlaClass('danger'); return; }
      const days = Math.floor(diff / 86400000);
      const hours = Math.floor((diff % 86400000) / 3600000);
      setTimeLeft(`${days}d ${hours}h`);
      setSlaClass(days < 1 ? 'danger' : days < 3 ? 'warning' : 'safe');
    };
    update();
    const interval = setInterval(update, 60000);
    return () => clearInterval(interval);
  }, [deadline, status]);

  return (
    <span className={`sla-timer sla-timer--${slaClass}`}>
      {slaClass !== 'safe' && timeLeft !== '—' && <span className="sla-timer__dot" />}
      {timeLeft}
    </span>
  );
}

// ── Metric Card ──
export function MetricCard({ label, value, change, trend, color }: {
  label: string; value: string | number; change?: string; trend?: 'up' | 'down'; color?: string;
}) {
  return (
    <div className="kpi-card" style={{ '--kpi-color': color || 'var(--accent)' } as CSSProperties}>
      <div className="kpi-card__label">{label}</div>
      <div className="kpi-card__value">{value}</div>
      {change && (
        <div className={`kpi-card__change kpi-card__change--${trend || 'up'}`}>
          {trend === 'down' ? '↓' : '↑'} {change}
        </div>
      )}
    </div>
  );
}

// ── Loading Spinner ──
export function LoadingState({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="loading-state">
      <div className="loading-spinner" />
      <p>{message}</p>
    </div>
  );
}

// ── Error State ──
export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="empty-state">
      <div className="empty-state__icon">⚠️</div>
      <h3>Something went wrong</h3>
      <p>{message}</p>
      {onRetry && <button className="btn btn--primary" onClick={onRetry}>Try Again</button>}
    </div>
  );
}

// ── Empty State ──
export function EmptyState({ icon, title, subtitle }: { icon: string; title: string; subtitle: string }) {
  return (
    <div className="empty-state">
      <div className="empty-state__icon">{icon}</div>
      <h3>{title}</h3>
      <p>{subtitle}</p>
    </div>
  );
}

// ── Page Wrapper ──
export function PageHeader({ title, subtitle, children }: { title: string; subtitle?: string; children?: ReactNode }) {
  return (
    <div className="page-header-row">
      <div>
        <h1 className="page-title">{title}</h1>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>
      {children && <div className="page-header-actions">{children}</div>}
    </div>
  );
}

// ── Filter Bar ──
export function FilterBar({ children }: { children: ReactNode }) {
  return <div className="filter-bar">{children}</div>;
}

export function FilterSelect({ label, value, onChange, options }: {
  label: string; value: string; onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <div className="filter-group">
      <label className="filter-label">{label}</label>
      <select className="form-input form-select" value={value} onChange={e => onChange(e.target.value)}>
        <option value="">All</option>
        {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  );
}

export function FilterSearch({ value, onChange, placeholder }: {
  value: string; onChange: (v: string) => void; placeholder?: string;
}) {
  return (
    <div className="filter-group filter-group--search">
      <label className="filter-label">Search</label>
      <input
        type="search" className="form-input" placeholder={placeholder || 'Search cases...'}
        value={value} onChange={e => onChange(e.target.value)}
      />
    </div>
  );
}

// ── Timeline ──
export function Timeline({ events }: { events: { id: string; timestamp: string; action: string; actor: string; detail: string; type: string }[] }) {
  const typeIcons: Record<string, string> = {
    submission: '📝', triage: '⚖️', routing: '🔀', review: '🔍',
    escalation: '🚨', resolution: '✅', reply: '💬', system: '⚙️',
  };
  return (
    <div className="timeline">
      {events.map((ev, i) => (
        <div key={ev.id} className={`timeline__item timeline__item--${ev.type}`}>
          <div className="timeline__marker">
            <span className="timeline__icon">{typeIcons[ev.type] || '•'}</span>
            {i < events.length - 1 && <div className="timeline__line" />}
          </div>
          <div className="timeline__content">
            <div className="timeline__header">
              <strong>{ev.action}</strong>
              <span className="timeline__time">{new Date(ev.timestamp).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })}</span>
            </div>
            <p className="timeline__detail">{ev.detail}</p>
            <span className="timeline__actor">by {ev.actor}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
