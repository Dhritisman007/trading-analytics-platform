// src/hooks/useNews.js
import { useQuery } from '@tanstack/react-query'
import { newsApi } from '../api/endpoints'

export const useNews = (limit = 20, topic = null) =>
  useQuery({
    queryKey:        ['news', limit, topic],
    queryFn:         () => newsApi.getAll(limit, topic),
    staleTime:       5 * 60 * 1000,
    refetchInterval: 15 * 60 * 1000,  // auto-refresh every 15 min
  })

export const useMarketMood = () =>
  useQuery({
    queryKey:        ['news-mood'],
    queryFn:         newsApi.getMood,
    staleTime:       5 * 60 * 1000,
    refetchInterval: 15 * 60 * 1000,
  })