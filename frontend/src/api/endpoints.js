// src/api/endpoints.js
// All API calls in one place — easy to update if backend URLs change

import client from './client'

// ── Market data ───────────────────────────────────────────────────────────────
export const marketApi = {
  getData: (symbol = '^NSEI', period = '3mo', interval = '1d') =>
    client.get('/market/', { params: { symbol, period, interval } }),

  getSymbols: () =>
    client.get('/market/symbols'),
}

// ── Technical indicators ──────────────────────────────────────────────────────
export const indicatorsApi = {
  getAll: (symbol = '^NSEI', period = '3mo', rsiWindow = 14, emaWindow = 20) =>
    client.get('/indicators/', {
      params: { symbol, period, rsi_window: rsiWindow, ema_window: emaWindow },
    }),

  getLatest: (symbol = '^NSEI') =>
    client.get('/indicators/latest', { params: { symbol } }),
}

// ── FVG detection ─────────────────────────────────────────────────────────────
export const fvgApi = {
  getAll: (symbol = '^NSEI', period = '3mo', onlyOpen = false) =>
    client.get('/fvg/', { params: { symbol, period, only_open: onlyOpen } }),

  getOpen: (symbol = '^NSEI') =>
    client.get('/fvg/open', { params: { symbol } }),
}

// ── ML predictions ────────────────────────────────────────────────────────────
export const predictApi = {
  get: (symbol = '^NSEI', topN = 10) =>
    client.get('/predict/', { params: { symbol, top_n: topN } }),

  getStatus: (symbol = '^NSEI') =>
    client.get('/predict/status', { params: { symbol } }),

  compare: () =>
    client.get('/predict/compare'),

  train: (symbol = '^NSEI', period = '2y') =>
    client.post('/predict/train', null, { params: { symbol, period } }),
}

// ── Risk management ───────────────────────────────────────────────────────────
export const riskApi = {
  analyze: (params) =>
    client.get('/risk/', { params }),

  quick: (capital, entryPrice, stopLoss, riskPct = 1.0) =>
    client.get('/risk/quick', {
      params: {
        capital,
        entry_price: entryPrice,
        stop_loss: stopLoss,
        risk_pct: riskPct,
      },
    }),

  atrStops: (symbol = '^NSEI', entryPrice, multiplier = 1.5) =>
    client.get('/risk/atr-stops', {
      params: { symbol, entry_price: entryPrice, atr_multiplier: multiplier },
    }),
}

// ── Backtesting ───────────────────────────────────────────────────────────────
export const backtestApi = {
  run: (strategy = 'rsi', symbol = '^NSEI', period = '2y', capital = 100000) =>
    client.get('/backtest/', {
      params: { strategy, symbol, period, initial_capital: capital },
    }),

  compare: (symbol = '^NSEI', period = '2y') =>
    client.get('/backtest/compare', { params: { symbol, period } }),

  getStrategies: () =>
    client.get('/backtest/strategies'),
}

// ── News & sentiment ──────────────────────────────────────────────────────────
export const newsApi = {
  getAll: (limit = 20, topic = null, sentiment = null) =>
    client.get('/news/', {
      params: { limit, topic, sentiment },
    }),

  getMood: () =>
    client.get('/news/mood'),

  getBreaking: () =>
    client.get('/news/breaking'),
}

// ── FII/DII flows ─────────────────────────────────────────────────────────────
export const fiiDiiApi = {
  getAll: (days = 30) =>
    client.get('/fii-dii/', { params: { days } }),

  getToday: () =>
    client.get('/fii-dii/today'),

  getChart: (days = 30) =>
    client.get('/fii-dii/chart', { params: { days } }),
}

// ── Live feed ─────────────────────────────────────────────────────────────────
export const liveApi = {
  getStatus: () =>
    client.get('/live/status'),

  getPrice: (symbol = '^NSEI') =>
    client.get(`/live/${symbol}`),
}

// ── Health ────────────────────────────────────────────────────────────────────
export const healthApi = {
  check: () => client.get('/health'),
}