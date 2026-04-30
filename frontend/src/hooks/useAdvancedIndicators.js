// src/hooks/useAdvancedIndicators.js

import { useQuery } from '@tanstack/react-query'
import client from '../api/client'

export const useAdvancedIndicators = (
    symbol = '^NSEI',
    period = '3mo',
) =>
    useQuery({
        queryKey: ['advanced-indicators', symbol, period],
        queryFn: () =>
            client.get('/indicators/advanced', {
                params: { symbol, period },
            }),
        staleTime: 5 * 60 * 1000,
        retry: 2,
    })