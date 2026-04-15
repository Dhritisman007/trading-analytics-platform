// src/hooks/useIndicators.js
import { useQuery } from '@tanstack/react-query'
import { indicatorsApi } from '../api/endpoints'

export const useIndicators = (symbol = '^NSEI', period = '3mo') =>
  useQuery({
    queryKey:  ['indicators', symbol, period],
    queryFn:   () => indicatorsApi.getAll(symbol, period),
    staleTime: 5 * 60 * 1000,
    retry:     2,
  })

export const useLatestSignals = (symbol = '^NSEI') =>
  useQuery({
    queryKey:    ['indicators-latest', symbol],
    queryFn:     () => indicatorsApi.getLatest(symbol),
    staleTime:   2 * 60 * 1000,
    refetchInterval: 5 * 60 * 1000,  // auto-refresh every 5 min
  })