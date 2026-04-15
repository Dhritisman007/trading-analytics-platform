// src/utils/formatters.js

import { format, parseISO } from 'date-fns'

// ── Number formatting ─────────────────────────────────────────────────────────

export const formatPrice = (value) => {
  if (value == null) return '—'
  return new Intl.NumberFormat('en-IN', {
    style:                 'currency',
    currency:              'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

export const formatNumber = (value, decimals = 2) => {
  if (value == null) return '—'
  return Number(value).toFixed(decimals)
}

export const formatCrore = (value) => {
  if (value == null) return '—'
  const abs = Math.abs(value)
  const sign = value < 0 ? '-' : '+'
  return `${sign}₹${abs.toFixed(0)} Cr`
}

export const formatPct = (value) => {
  if (value == null) return '—'
  const sign = value >= 0 ? '+' : ''
  return `${sign}${Number(value).toFixed(2)}%`
}

export const formatLargeNumber = (value) => {
  if (value == null) return '—'
  if (Math.abs(value) >= 1_00_00_000) return `₹${(value / 1_00_00_000).toFixed(2)}Cr`
  if (Math.abs(value) >= 1_00_000)    return `₹${(value / 1_00_000).toFixed(2)}L`
  return `₹${value.toFixed(0)}`
}

// ── Date formatting ───────────────────────────────────────────────────────────

export const formatDate = (dateStr) => {
  if (!dateStr) return '—'
  try {
    return format(parseISO(dateStr), 'dd MMM yyyy')
  } catch {
    return dateStr
  }
}

export const formatDateTime = (dateStr) => {
  if (!dateStr) return '—'
  try {
    return format(parseISO(dateStr), 'dd MMM, hh:mm a')
  } catch {
    return dateStr
  }
}

export const formatChartDate = (dateStr) => {
  if (!dateStr) return ''
  try {
    return format(parseISO(dateStr), 'dd MMM')
  } catch {
    return dateStr
  }
}

// ── Colour helpers ────────────────────────────────────────────────────────────

export const getPriceColor = (value) => {
  if (value == null) return 'var(--color-text-secondary)'
  return value >= 0 ? '#1D9E75' : '#E24B4A'
}

export const getSentimentColor = (label) => {
  const map = {
    positive: '#1D9E75',
    negative: '#E24B4A',
    neutral:  '#888780',
  }
  return map[label] || '#888780'
}

export const getSignalColor = (signal) => {
  if (!signal) return '#888780'
  if (signal === 'BUY'  || signal.includes('BULLISH')) return '#1D9E75'
  if (signal === 'SELL' || signal.includes('BEARISH')) return '#E24B4A'
  return '#BA7517'
}