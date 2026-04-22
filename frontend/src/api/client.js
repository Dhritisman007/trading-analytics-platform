// src/api/client.js

import axios from 'axios'

// All requests go through Vite proxy → FastAPI backend
const client = axios.create({
  baseURL: '/api',
  timeout: 30000,  // 30s timeout — backtests can take a while
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor — log requests in development
client.interceptors.request.use(
  (config) => {
    if (import.meta.env.DEV) {
      console.log(`→ ${config.method?.toUpperCase()} ${config.url}`)
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor — consistent error handling
client.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status = error.response?.status

    // 502 = backend not running — show clear message
    if (status === 502 || status === 503 || !error.response) {
      return Promise.reject(
        new Error('Backend server is not running. Start uvicorn and retry.')
      )
    }

    const message =
      error.response?.data?.message ||
      error.response?.data?.detail ||
      error.message ||
      'An unexpected error occurred'

    console.error(`API Error: ${message}`)
    return Promise.reject(new Error(message))
  }
)

export default client