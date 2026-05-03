// src/hooks/useLiquidity.js

import { useQuery } from '@tanstack/react-query'
import client       from '../api/client'

export const useLiquidity = (symbol = '^NSEI', period = '3mo') =>
  useQuery({
    queryKey:  ['liquidity', symbol, period],
    queryFn:   () => client.get('/liquidity/', { params: { symbol, period } }),
    staleTime: 15 * 60 * 1000,
    retry:     2,
  })

export const useSweeps = (symbol = '^NSEI', period = '3mo') =>
  useQuery({
    queryKey:  ['sweeps', symbol, period],
    queryFn:   () => client.get('/liquidity/sweeps', { params: { symbol, period } }),
    staleTime: 15 * 60 * 1000,
  })
