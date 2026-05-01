// src/hooks/useSMC.js

import { useQuery } from '@tanstack/react-query'
import { smcApi } from '../api/endpoints'

export const useSMCFull = (symbol = '^NSEI', period = '3mo') =>
    useQuery({
        queryKey: ['smc-full', symbol, period],
        queryFn: () => smcApi.getFull(symbol, period),
        staleTime: 30 * 60 * 1000,  // 30 min — SMC levels don't change fast
        retry: 2,
    })

export const useKillZones = () =>
    useQuery({
        queryKey: ['kill-zones'],
        queryFn: smcApi.getKillZones,
        staleTime: 60 * 1000,          // refresh every minute
        refetchInterval: 60 * 1000,
    })

export const useVolumeProfile = (symbol = '^NSEI', period = '3mo') =>
    useQuery({
        queryKey: ['volume-profile', symbol, period],
        queryFn: () => smcApi.getVolumeProfile(symbol, period),
        staleTime: 15 * 60 * 1000,
    })