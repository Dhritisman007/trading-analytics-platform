// src/hooks/useFiiDii.js
import { useQuery } from '@tanstack/react-query'
import { fiiDiiApi } from '../api/endpoints'

export const useFiiDii = (days = 30) =>
  useQuery({
    queryKey:       ['fii-dii', days],
    queryFn:        () => fiiDiiApi.getAll(days),
    staleTime:      5 * 60 * 1000,       // 5 minutes
    refetchOnMount: true,                 // Always refetch on mount
    gcTime:         10 * 60 * 1000,      // Keep in cache for 10 min
  })

export const useFiiDiiToday = () =>
  useQuery({
    queryKey:       ['fii-dii-today'],
    queryFn:        fiiDiiApi.getToday,
    staleTime:      5 * 60 * 1000,       // 5 minutes
    refetchOnMount: true,                 // Always refetch on mount
    gcTime:         10 * 60 * 1000,      // Keep in cache for 10 min
  })