// src/components/panels/GPTCommentaryCard.jsx

import { Sparkles, RefreshCw } from 'lucide-react'
import { useGPTCommentary } from '../../hooks/usePatterns'

export default function GPTCommentaryCard({ symbol }) {
    const { data, isLoading, error, refetch, isRefetching } =
        useGPTCommentary(symbol)

    return (
        <div style={{
            background: 'var(--color-background-primary)',
            border: '0.5px solid var(--color-border-tertiary)',
            borderRadius: 'var(--border-radius-lg)',
            padding: '1rem 1.25rem',
        }}>
            {/* Header */}
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '12px',
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Sparkles size={14} style={{ color: '#BA7517' }} />
                    <p style={{ fontSize: '13px', fontWeight: '500', margin: 0 }}>
                        AI Market Commentary
                    </p>
                    <span style={{
                        fontSize: '9px',
                        padding: '2px 6px',
                        borderRadius: '20px',
                        background: '#FAEEDA',
                        color: '#633806',
                        fontWeight: '500',
                    }}>
                        GPT-4o-mini
                    </span>
                </div>

                <button
                    onClick={refetch}
                    disabled={isLoading || isRefetching}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: '28px',
                        height: '28px',
                        borderRadius: 'var(--border-radius-md)',
                        border: '0.5px solid var(--color-border-tertiary)',
                        background: 'transparent',
                        color: 'var(--color-text-secondary)',
                        cursor: 'pointer',
                    }}
                >
                    <RefreshCw
                        size={12}
                        style={{ animation: (isLoading || isRefetching) ? 'spin 1s linear infinite' : 'none' }}
                    />
                </button>
            </div>

            {/* Content */}
            {isLoading && (
                <div style={{
                    textAlign: 'center',
                    padding: '1.5rem',
                    color: 'var(--color-text-tertiary)',
                    fontSize: '12px',
                }}>
                    <div style={{
                        width: '20px',
                        height: '20px',
                        border: '2px solid var(--color-border-tertiary)',
                        borderTop: '2px solid #BA7517',
                        borderRadius: '50%',
                        animation: 'spin 0.8s linear infinite',
                        margin: '0 auto 8px',
                    }} />
                    Generating commentary...
                </div>
            )}

            {!isLoading && !data?.available && (
                <div style={{
                    padding: '1rem',
                    background: 'var(--color-background-secondary)',
                    borderRadius: 'var(--border-radius-md)',
                    fontSize: '12px',
                    color: 'var(--color-text-secondary)',
                }}>
                    <p style={{ margin: '0 0 4px', fontWeight: '500', color: data?.message?.includes('429') || data?.message?.includes('quota') ? 'var(--color-text-primary)' : 'inherit' }}>
                        {data?.message?.includes('429') || data?.message?.includes('quota')
                            ? 'OpenAI Quota Exceeded'
                            : 'GPT Commentary Unavailable'}
                    </p>
                    <p style={{ margin: 0 }}>
                        {data?.message || (
                            <>Add <code>OPENAI_API_KEY</code> to your environment variables to enable AI-powered market analysis.</>
                        )}
                    </p>
                </div>
            )}

            {!isLoading && data?.available && data?.commentary && (
                <div>
                    <p style={{
                        fontSize: '12px',
                        color: 'var(--color-text-secondary)',
                        lineHeight: '1.7',
                        margin: '0 0 8px',
                        whiteSpace: 'pre-wrap',
                    }}>
                        {data.commentary}
                    </p>
                    <p style={{
                        fontSize: '10px',
                        color: 'var(--color-text-tertiary)',
                        margin: 0,
                    }}>
                        Generated {data.generated_at
                            ? new Date(data.generated_at).toLocaleTimeString('en-IN')
                            : '—'} · {data.tokens_used} tokens ·
                        For educational purposes only
                    </p>
                </div>
            )}
        </div>
    )
}