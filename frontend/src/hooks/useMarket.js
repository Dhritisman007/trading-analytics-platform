// src/hooks/useMarket.js
import { useQuery } from '@tanstack/react-query'
import { marketApi } from '../api/endpoints'

export const useMarket = (symbol = '^NSEI', period = '3mo', interval = '1d') =>
  useQuery({
    queryKey:       ['market', symbol, period, interval],
    queryFn:        () => marketApi.getData(symbol, period, interval),
    staleTime:      5 * 60 * 1000,
    refetchOnMount: true,
    retry:          2,
    gcTime:         10 * 60 * 1000,
  })

export const useSymbols = () =>
  useQuery({
    queryKey:  ['symbols'],
    queryFn:   marketApi.getSymbols,
    staleTime: Infinity,  // symbols never change
  })
