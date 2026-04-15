// src/hooks/usePredict.js
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { predictApi } from '../api/endpoints'

export const usePredict = (symbol = '^NSEI') =>
  useQuery({
    queryKey:  ['predict', symbol],
    queryFn:   () => predictApi.get(symbol),
    staleTime: 15 * 60 * 1000,  // 15 min — model doesn't change that fast
    retry:     1,
  })

export const useTrainModel = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ symbol, period }) => predictApi.train(symbol, period),
    onSuccess:  () => queryClient.invalidateQueries({ queryKey: ['predict'] }),
  })
}