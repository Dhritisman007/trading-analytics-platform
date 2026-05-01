// src/components/panels/KillZoneOverlay.jsx

import { useKillZones } from '../../hooks/useSMC'

export default function KillZoneOverlay() {
    const { data } = useKillZones()
    const zones = data?.kill_zones || []

    if (!zones.length) return null

    const activeZone = zones.find((z) => z.active)

    return (
        <div style={{ marginBottom: '10px' }}>
            {/* Active kill zone banner */}
            {activeZone && (
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px 14px',
                    background: `${activeZone.color}15`,
                    border: `1px solid ${activeZone.color}40`,
                    borderRadius: 'var(--border-radius-md)',
                    marginBottom: '8px',
                }}>
                    <span style={{
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        background: activeZone.color,
                        display: 'inline-block',
                        animation: 'pulse 2s infinite',
                    }} />
                    <span style={{
                        fontSize: '12px',
                        fontWeight: '500',
                        color: activeZone.color,
                    }}>
                        🕐 {activeZone.name} kill zone active ({activeZone.start} – {activeZone.end} IST)
                    </span>
                    <span style={{
                        fontSize: '11px',
                        color: 'var(--color-text-secondary)',
                        flex: 1,
                    }}>
                        {activeZone.description}
                    </span>
                </div>
            )}

            {/* All kill zones timeline */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
                gap: '6px',
            }}>
                {zones.map((zone) => (
                    <div
                        key={zone.name}
                        style={{
                            padding: '7px 10px',
                            borderRadius: 'var(--border-radius-md)',
                            border: `0.5px solid ${zone.active ? zone.color : 'var(--color-border-tertiary)'}`,
                            background: zone.active ? `${zone.color}12` : 'var(--color-background-secondary)',
                            opacity: zone.active ? 1 : 0.65,
                        }}
                    >
                        <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px',
                            marginBottom: '2px',
                        }}>
                            <span style={{
                                width: '6px',
                                height: '6px',
                                borderRadius: '50%',
                                background: zone.color,
                                display: 'inline-block',
                                animation: zone.active ? 'pulse 2s infinite' : 'none',
                            }} />
                            <span style={{
                                fontSize: '11px',
                                fontWeight: '500',
                                color: zone.active ? zone.color : 'var(--color-text-primary)',
                            }}>
                                {zone.name}
                            </span>
                        </div>
                        <p style={{
                            fontSize: '10px',
                            color: 'var(--color-text-tertiary)',
                            margin: 0,
                        }}>
                            {zone.start} – {zone.end} IST
                        </p>
                    </div>
                ))}
            </div>
        </div>
    )
}