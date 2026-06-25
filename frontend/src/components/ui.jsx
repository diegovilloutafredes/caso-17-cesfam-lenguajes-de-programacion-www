// Primitivas de UI reutilizables (fieles a las clases del sistema de diseño).

export function Badge({ type = 'muted', children }) {
  return <span className={`badge ${type}`}>{children}</span>
}

export function Kpi({ icon, num, label, type = 'info' }) {
  return (
    <div className={`card kpi ${type}`}>
      <div className="kpi-icon">{icon}</div>
      <div>
        <div className="kpi-num">{num}</div>
        <div className="kpi-label">{label}</div>
      </div>
    </div>
  )
}

export function SearchBar({ value, onChange, placeholder, style }) {
  return (
    <div className="search-bar" style={style}>
      <input
        className="input"
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
    </div>
  )
}

export function PageHeader({ title, subtitle, children }) {
  return (
    <header className="page-header">
      <div>
        <h1>{title}</h1>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {children}
    </header>
  )
}

export function Empty({ children }) {
  return <p className="text-soft" style={{ padding: '12px 0' }}>{children}</p>
}
