// src/hooks/useIndicators.js
import { useQuery } from '@tanstack/react-query'
import { indicatorsApi } from '../api/endpoints'

export const useIndicators = (symbol = '^NSEI', period = '3mo', rsiWindow = 14, emaWindow = 20) =>
  useQuery({
    queryKey:       ['indicators', symbol, period, rsiWindow, emaWindow],
    queryFn:        () => indicatorsApi.getAll(symbol, period, rsiWindow, emaWindow),
    staleTime:      5 * 60 * 1000,
    refetchOnMount: true,                  // Always refetch on mount
    retry:          2,
    gcTime:         10 * 60 * 1000,       // Keep in cache for 10 min
  })

export const useLatestSignals = (symbol = '^NSEI') =>
  useQuery({
    queryKey:        ['indicators-latest', symbol],
    queryFn:         () => indicatorsApi.getLatest(symbol),
    staleTime:       2 * 60 * 1000,
    refetchOnMount:  true,                // Always refetch on mount
    refetchInterval: 5 * 60 * 1000,       // auto-refresh every 5 min
    gcTime:          10 * 60 * 1000,     // Keep in cache for 10 min
  })