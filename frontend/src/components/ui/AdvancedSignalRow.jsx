// src/components/ui/AdvancedSignalRow.jsx

export default function AdvancedSignalRow({ label, signal, value, description }) {
    return (
        <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '8px 0',
            borderBottom: '0.5px solid var(--color-border-tertiary)',
        }}>
            {/* Signal dot */}
            <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: signal?.color || '#888780',
                flexShrink: 0,
            }} />

            {/* Label */}
            <span style={{
                fontSize: '12px',
                fontWeight: '500',
                color: 'var(--color-text-primary)',
                width: '100px',
                flexShrink: 0,
            }}>
                {label}
            </span>

            {/* Signal badge */}
            <span style={{
                fontSize: '10px',
                fontWeight: '500',
                padding: '2px 8px',
                borderRadius: '20px',
                background: `${signal?.color || '#888780'}18`,
                color: signal?.color || '#888780',
                flexShrink: 0,
            }}>
                {signal?.signal || '—'}
            </span>

            {/* Value */}
            {value && (
                <span style={{
                    fontSize: '11px',
                    color: 'var(--color-text-secondary)',
                    flexShrink: 0,
                }}>
                    {value}
                </span>
            )}

            {/* Description */}
            <span style={{
                fontSize: '11px',
                color: 'var(--color-text-tertiary)',
                flex: 1,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
            }}>
                {description || signal?.description}
            </span>
        </div>
    )
}