// src/hooks/useMarket.js
import { useQuery } from '@tanstack/react-query'
import { marketApi } from '../api/endpoints'

export const useMarket = (symbol = '^NSEI', period = '3mo') =>
  useQuery({
    queryKey:  ['market', symbol, period],
    queryFn:   () => marketApi.getData(symbol, period),
    staleTime: 5 * 60 * 1000,   // 5 minutes
    retry:     2,
  })

export const useSymbols = () =>
  useQuery({
    queryKey: ['symbols'],
    queryFn:  marketApi.getSymbols,
    staleTime: Infinity,  // symbols never change
  })
