import { useState } from 'react';
import SeverityBadge from './SeverityBadge';
import styles from './BugList.module.css';

const TYPE_MAP = {
  syntax: 'Syntax', logic: 'Logic', performance: 'Performance',
  security: 'Security', quality: 'Quality',
};

const BORDER = {
  critical: '#b91c1c', high: '#da3633', medium: '#9e6a03', low: '#238636',
};

function BugCard({ bug, index }) {
  const [open, setOpen] = useState(bug.severity === 'critical' || bug.severity === 'high');
  const sev   = (bug.severity || 'medium').toLowerCase();
  const btype = (bug.type || 'unknown').toLowerCase();
  const label = TYPE_MAP[btype] || btype.charAt(0).toUpperCase() + btype.slice(1);
  const border = BORDER[sev] || '#4f46e5';

  const lineInfo = bug.line_start
    ? `L${bug.line_start}${bug.line_end && bug.line_end !== bug.line_start ? `–${bug.line_end}` : ''}`
    : null;

  return (
    <div className={styles.card} style={{ borderLeft: `3px solid ${border}` }}>
      <button className={styles.header} onClick={() => setOpen(o => !o)}>
        <div className={styles.headerLeft}>
          <span className={styles.index}>#{index}</span>
          <span className={styles.typeLabel}>{label}</span>
          <SeverityBadge severity={sev} />
          {bug.filename && <code className={styles.mono}>{bug.filename}</code>}
          {lineInfo     && <code className={styles.mono}>{lineInfo}</code>}
        </div>
        <svg
          className={`${styles.chevron} ${open ? styles.open : ''}`}
          width="14" height="14" viewBox="0 0 24 24"
          fill="none" stroke="currentColor" strokeWidth="2"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {open && (
        <div className={styles.body}>
          <p className={styles.desc}>{bug.description || 'No description.'}</p>
          {bug.simple_explanation && (
            <p className={styles.explain}>{bug.simple_explanation}</p>
          )}
        </div>
      )}
    </div>
  );
}

export default function BugList({ bugs }) {
  if (!bugs || bugs.length === 0) {
    return (
      <div className={styles.empty}>
        <div className={styles.emptyIcon}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
               stroke="#3fb950" strokeWidth="2.5">
            <polyline points="20 6 9 17 4 12" />
          </svg>
        </div>
        <div>
          <p className={styles.emptyTitle}>No Issues Detected</p>
          <p className={styles.emptySubtitle}>AI analysis found no bugs in the submitted code.</p>
        </div>
      </div>
    );
  }

  const counts = { critical: 0, high: 0, medium: 0, low: 0 };
  bugs.forEach(b => { const s = (b.severity || 'medium').toLowerCase(); if (s in counts) counts[s]++; });

  return (
    <div>
      {/* Summary grid */}
      <div className={styles.grid}>
        {[
          { label: 'Critical', key: 'critical', color: '#ff7b72', bg: '#3b0000', border: '#b91c1c' },
          { label: 'High',     key: 'high',     color: '#f85149', bg: '#2d0d0d', border: '#da3633' },
          { label: 'Medium',   key: 'medium',   color: '#d29922', bg: '#2d1f0d', border: '#9e6a03' },
          { label: 'Low',      key: 'low',      color: '#3fb950', bg: '#0d2d1f', border: '#238636' },
        ].map(({ label, key, color, bg, border }) => (
          <div key={key} className={styles.metricCard} style={{ background: bg, border: `1px solid ${border}` }}>
            <span className={styles.metricVal} style={{ color }}>{counts[key]}</span>
            <span className={styles.metricLabel}>{label}</span>
          </div>
        ))}
      </div>

      <p className={styles.sectionLabel}>{bugs.length} issue{bugs.length !== 1 ? 's' : ''} found</p>

      {bugs.map((bug, i) => (
        <BugCard key={i} bug={bug} index={i + 1} />
      ))}
    </div>
  );
}
