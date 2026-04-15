// src/components/ui/Badge.jsx
export const Badge = ({ label, color = '#888780', bgColor = null }) => (
  <span style={{
    display:       'inline-block',
    fontSize:      '11px',
    fontWeight:    '500',
    padding:       '2px 8px',
    borderRadius:  '20px',
    color,
    background:    bgColor || `${color}22`,
    border:        `0.5px solid ${color}44`,
  }}>
    {label}
  </span>
)