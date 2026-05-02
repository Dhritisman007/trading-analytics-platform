// src/hooks/useWatchlist.js

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import client from '../api/client'

export const useWatchlist = () =>
  useQuery({
    queryKey: ['watchlist'],
    queryFn:  () => client.get('/watchlist/'),
    staleTime: Infinity,
  })

export const useAddToWatchlist = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (symbol) => client.post('/watchlist/', { symbol }),
    onSuccess:  () => qc.invalidateQueries({ queryKey: ['watchlist'] }),
  })
}

export const useRemoveFromWatchlist = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (symbol) => client.delete(`/watchlist/${symbol}`),
    onSuccess:  () => qc.invalidateQueries({ queryKey: ['watchlist'] }),
  })
}
