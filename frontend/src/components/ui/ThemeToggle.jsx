// src/components/ui/ThemeToggle.jsx

import { Sun, Moon } from 'lucide-react'

export default function ThemeToggle({ isDark, onToggle }) {
    return (
        <button
            onClick={onToggle}
            title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
            style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '32px',
                height: '32px',
                borderRadius: 'var(--border-radius-md)',
                border: '0.5px solid var(--color-border-tertiary)',
                background: 'var(--color-background-secondary)',
                color: 'var(--color-text-secondary)',
                cursor: 'pointer',
                transition: 'all 0.15s',
                flexShrink: 0,
            }}
            onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-border-secondary)'
                e.currentTarget.style.color = 'var(--color-text-primary)'
            }}
            onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-border-tertiary)'
                e.currentTarget.style.color = 'var(--color-text-secondary)'
            }}
        >
            {isDark ? <Sun size={14} /> : <Moon size={14} />}
        </button>
    )
}