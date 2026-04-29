// src/hooks/useFvg.js
import { useQuery } from '@tanstack/react-query'
import { fvgApi }   from '../api/endpoints'

export const useFvg = (symbol = '^NSEI', period = '3mo', onlyOpen = false) =>
  useQuery({
    queryKey:       ['fvg', symbol, period, onlyOpen],
    queryFn:        () => fvgApi.getAll(symbol, period, onlyOpen),
    staleTime:      10 * 60 * 1000,  // FVGs change slowly
    refetchOnMount: true,
    retry:          2,
    gcTime:         15 * 60 * 1000,
  })

export const useOpenFvgs = (symbol = '^NSEI') =>
  useQuery({
    queryKey:       ['fvg-open', symbol],
    queryFn:        () => fvgApi.getOpen(symbol),
    staleTime:      10 * 60 * 1000,
    refetchOnMount: true,
    retry:          2,
    gcTime:         15 * 60 * 1000,
  })
