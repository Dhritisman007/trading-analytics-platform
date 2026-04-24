// src/hooks/useNews.js
import { useQuery } from '@tanstack/react-query'
import { newsApi } from '../api/endpoints'

export const useNews = (limit = 20, topic = null) =>
  useQuery({
    queryKey:        ['news', limit, topic],
    queryFn:         () => newsApi.getAll(limit, topic),
    staleTime:       2 * 60 * 1000,       // 2 minutes
    refetchOnMount:  true,                // Always refetch on mount
    refetchInterval: 10 * 60 * 1000,      // auto-refresh every 10 min
    gcTime:          15 * 60 * 1000,     // Keep in cache for 15 min
  })

export const useMarketMood = () =>
  useQuery({
    queryKey:        ['news-mood'],
    queryFn:         newsApi.getMood,
    staleTime:       2 * 60 * 1000,       // 2 minutes
    refetchOnMount:  true,                // Always refetch on mount
    refetchInterval: 10 * 60 * 1000,      // auto-refresh every 10 min
    gcTime:          15 * 60 * 1000,     // Keep in cache for 15 min
  })