// src/hooks/usePredict.js
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { predictApi } from '../api/endpoints'

export const usePredict = (symbol = '^NSEI') =>
  useQuery({
    queryKey:       ['predict', symbol],
    queryFn:        () => predictApi.get(symbol),
    staleTime:      10 * 60 * 1000,  // 10 min — model doesn't change that fast
    refetchOnMount: true,             // Always refetch on mount
    retry:          1,
    gcTime:         20 * 60 * 1000,  // Keep in cache for 20 min
  })

export const useTrainModel = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ symbol, period }) => predictApi.train(symbol, period),
    onSuccess:  () => queryClient.invalidateQueries({ queryKey: ['predict'] }),
  })
}