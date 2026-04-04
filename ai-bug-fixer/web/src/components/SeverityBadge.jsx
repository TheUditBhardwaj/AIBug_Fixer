import styles from './SeverityBadge.module.css';

const MAP = {
  critical: { label: 'CRITICAL', cls: styles.critical },
  high:     { label: 'HIGH',     cls: styles.high },
  medium:   { label: 'MEDIUM',   cls: styles.medium },
  low:      { label: 'LOW',      cls: styles.low },
};

export default function SeverityBadge({ severity }) {
  const s = (severity || 'medium').toLowerCase();
  const { label, cls } = MAP[s] || MAP.medium;
  return <span className={`${styles.badge} ${cls}`}>{label}</span>;
}
