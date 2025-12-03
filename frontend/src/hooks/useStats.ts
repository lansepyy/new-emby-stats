import { useState, useEffect, useCallback } from 'react'
import { api } from '@/services/api'
import type {
  OverviewData,
  TrendData,
  HourlyData,
  TopShowsData,
  TopContentData,
  UsersData,
  ClientsData,
  PlaybackMethodsData,
  DevicesData,
  RecentData,
  NowPlayingData,
} from '@/types'

export function useOverview(days: number) {
  const [data, setData] = useState<OverviewData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    try {
      const result = await api.getOverview(days)
      setData(result)
      setError(null)
    } catch (e) {
      setError(e as Error)
    } finally {
      setLoading(false)
    }
  }, [days])

  useEffect(() => {
    fetch()
  }, [fetch])

  return { data, loading, error, refetch: fetch }
}

export function useTrend(days: number) {
  const [data, setData] = useState<TrendData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    try {
      const result = await api.getTrend(days)
      setData(result)
      setError(null)
    } catch (e) {
      setError(e as Error)
    } finally {
      setLoading(false)
    }
  }, [days])

  useEffect(() => {
    fetch()
  }, [fetch])

  return { data, loading, error, refetch: fetch }
}

export function useHourly(days: number) {
  const [data, setData] = useState<HourlyData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    try {
      const result = await api.getHourly(days)
      setData(result)
      setError(null)
    } catch (e) {
      setError(e as Error)
    } finally {
      setLoading(false)
    }
  }, [days])

  useEffect(() => {
    fetch()
  }, [fetch])

  return { data, loading, error, refetch: fetch }
}

export function useTopShows(days: number, limit = 16) {
  const [data, setData] = useState<TopShowsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    try {
      const result = await api.getTopShows(days, limit)
      setData(result)
      setError(null)
    } catch (e) {
      setError(e as Error)
    } finally {
      setLoading(false)
    }
  }, [days, limit])

  useEffect(() => {
    fetch()
  }, [fetch])

  return { data, loading, error, refetch: fetch }
}

export function useTopContent(days: number, limit = 18) {
  const [data, setData] = useState<TopContentData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    try {
      const result = await api.getTopContent(days, limit)
      setData(result)
      setError(null)
    } catch (e) {
      setError(e as Error)
    } finally {
      setLoading(false)
    }
  }, [days, limit])

  useEffect(() => {
    fetch()
  }, [fetch])

  return { data, loading, error, refetch: fetch }
}

export function useUsers(days: number) {
  const [data, setData] = useState<UsersData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    try {
      const result = await api.getUsers(days)
      setData(result)
      setError(null)
    } catch (e) {
      setError(e as Error)
    } finally {
      setLoading(false)
    }
  }, [days])

  useEffect(() => {
    fetch()
  }, [fetch])

  return { data, loading, error, refetch: fetch }
}

export function useClients(days: number) {
  const [data, setData] = useState<ClientsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    try {
      const result = await api.getClients(days)
      setData(result)
      setError(null)
    } catch (e) {
      setError(e as Error)
    } finally {
      setLoading(false)
    }
  }, [days])

  useEffect(() => {
    fetch()
  }, [fetch])

  return { data, loading, error, refetch: fetch }
}

export function usePlaybackMethods(days: number) {
  const [data, setData] = useState<PlaybackMethodsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    try {
      const result = await api.getPlaybackMethods(days)
      setData(result)
      setError(null)
    } catch (e) {
      setError(e as Error)
    } finally {
      setLoading(false)
    }
  }, [days])

  useEffect(() => {
    fetch()
  }, [fetch])

  return { data, loading, error, refetch: fetch }
}

export function useDevices(days: number) {
  const [data, setData] = useState<DevicesData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    try {
      const result = await api.getDevices(days)
      setData(result)
      setError(null)
    } catch (e) {
      setError(e as Error)
    } finally {
      setLoading(false)
    }
  }, [days])

  useEffect(() => {
    fetch()
  }, [fetch])

  return { data, loading, error, refetch: fetch }
}

export function useRecent(limit = 48) {
  const [data, setData] = useState<RecentData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    try {
      const result = await api.getRecent(limit)
      setData(result)
      setError(null)
    } catch (e) {
      setError(e as Error)
    } finally {
      setLoading(false)
    }
  }, [limit])

  useEffect(() => {
    fetch()
  }, [fetch])

  return { data, loading, error, refetch: fetch }
}

export function useNowPlaying(refreshInterval = 10000) {
  const [data, setData] = useState<NowPlayingData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetch = useCallback(async () => {
    try {
      const result = await api.getNowPlaying()
      setData(result)
      setError(null)
    } catch (e) {
      setError(e as Error)
      setData({ now_playing: [] })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetch()
    const timer = setInterval(fetch, refreshInterval)
    return () => clearInterval(timer)
  }, [fetch, refreshInterval])

  return { data, loading, error, refetch: fetch }
}
