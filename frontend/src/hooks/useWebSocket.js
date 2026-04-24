// src/hooks/useWebSocket.js
import { useEffect, useRef, useState, useCallback } from 'react'
import { WS_URL } from '../utils/constants'

export const useWebSocket = () => {
  const [ticks, setTicks]       = useState({})
  const [connected, setConnected] = useState(false)
  const wsRef                   = useRef(null)
  const reconnectRef            = useRef(null)

  const connect = useCallback(() => {
    try {
      wsRef.current = new WebSocket(WS_URL)

      wsRef.current.onopen = () => {
        setConnected(true)
        console.log('WebSocket connected')
        if (reconnectRef.current) clearTimeout(reconnectRef.current)
      }

      wsRef.current.onmessage = (event) => {
        const msg = JSON.parse(event.data)
        if (msg.type === 'tick' || msg.type === 'snapshot') {
          setTicks((prev) => ({ ...prev, ...msg.data }))
        }
      }

      wsRef.current.onclose = () => {
        setConnected(false)
        // Auto-reconnect after 5 seconds
        reconnectRef.current = setTimeout(() => {
          connect()
        }, 5000)
      }

      wsRef.current.onerror = () => {
        wsRef.current?.close()
      }

    } catch (err) {
      console.warn('WebSocket unavailable:', err.message)
    }
  }, [])

  useEffect(() => {
    connect()
    return () => {
      if (reconnectRef.current) clearTimeout(reconnectRef.current)
      wsRef.current?.close()
    }
  }, [connect])

  // Helper: get live price for a symbol
  const getLivePrice = useCallback((instrumentKey) => {
    return ticks[instrumentKey] || null
  }, [ticks])

  return { ticks, connected, getLivePrice }
}