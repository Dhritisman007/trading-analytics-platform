// src/hooks/useFiiDii.js
import { useQuery } from '@tanstack/react-query'
import { fiiDiiApi } from '../api/endpoints'

export const useFiiDii = (days = 30) =>
  useQuery({
    queryKey:  ['fii-dii', days],
    queryFn:   () => fiiDiiApi.getAll(days),
    staleTime: 60 * 60 * 1000,  // 1 hour — updates once daily
  })

export const useFiiDiiToday = () =>
  useQuery({
    queryKey:  ['fii-dii-today'],
    queryFn:   fiiDiiApi.getToday,
    staleTime: 60 * 60 * 1000,
  })