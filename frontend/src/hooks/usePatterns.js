// src/hooks/usePatterns.js

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import client from '../api/client'

export const usePatterns = (symbol = '^NSEI', period = '3mo') =>
  useQuery({
    queryKey:  ['patterns', symbol, period],
    queryFn:   () => client.get('/predict/patterns', { params: { symbol, period } }),
    staleTime: 30 * 60 * 1000,
  })

export const useLSTMPrediction = (symbol = '^NSEI') =>
  useQuery({
    queryKey:  ['lstm', symbol],
    queryFn:   () => client.get('/predict/lstm', { params: { symbol } }),
    staleTime: 15 * 60 * 1000,
    retry:     false,  // don't retry — model may not be trained yet
  })

export const useTrainLSTM = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (symbol) =>
      client.post('/predict/train/lstm', null, { params: { symbol, period: '2y' } }),
    onSuccess: () => {
      setTimeout(() => {
        qc.invalidateQueries({ queryKey: ['lstm'] })
      }, 180000)  // check again after 3 min
    },
  })
}

export const useGPTCommentary = (symbol = '^NSEI', enabled = true) =>
  useQuery({
    queryKey:  ['gpt-commentary', symbol],
    queryFn:   () => client.get('/predict/commentary', { params: { symbol } }),
    staleTime: 30 * 60 * 1000,
    enabled,
    retry:     false,
  })
