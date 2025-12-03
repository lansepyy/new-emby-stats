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

const API_BASE = '/api'

// 认证状态变更回调
let onAuthError: (() => void) | null = null

export function setAuthErrorHandler(handler: () => void) {
  onAuthError = handler
}

async function fetchAPI<T>(endpoint: string): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`)
  if (!res.ok) {
    // 401 错误触发认证失败
    if (res.status === 401) {
      onAuthError?.()
    }
    throw new Error(`API error: ${res.status}`)
  }
  return res.json()
}

export const api = {
  getOverview: (days: number): Promise<OverviewData> =>
    fetchAPI(`/overview?days=${days}`),

  getTrend: (days: number): Promise<TrendData> =>
    fetchAPI(`/trend?days=${days}`),

  getHourly: (days: number): Promise<HourlyData> =>
    fetchAPI(`/hourly?days=${days}`),

  getTopShows: (days: number, limit = 16): Promise<TopShowsData> =>
    fetchAPI(`/top-shows?days=${days}&limit=${limit}`),

  getTopContent: (days: number, limit = 18): Promise<TopContentData> =>
    fetchAPI(`/top-content?days=${days}&limit=${limit}`),

  getUsers: (days: number): Promise<UsersData> =>
    fetchAPI(`/users?days=${days}`),

  getClients: (days: number): Promise<ClientsData> =>
    fetchAPI(`/clients?days=${days}`),

  getPlaybackMethods: (days: number): Promise<PlaybackMethodsData> =>
    fetchAPI(`/playback-methods?days=${days}`),

  getDevices: (days: number): Promise<DevicesData> =>
    fetchAPI(`/devices?days=${days}`),

  getRecent: (limit = 48): Promise<RecentData> =>
    fetchAPI(`/recent?limit=${limit}`),

  getNowPlaying: (): Promise<NowPlayingData> =>
    fetchAPI('/now-playing'),

  // 认证相关
  checkAuth: async (): Promise<{ authenticated: boolean; username?: string }> => {
    const res = await fetch(`${API_BASE}/auth/check`)
    return res.json()
  },

  login: async (username: string, password: string): Promise<{ success: boolean; username?: string; message?: string }> => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })
    if (!res.ok) {
      const data = await res.json()
      return { success: false, message: data.detail || '登录失败' }
    }
    return res.json()
  },

  logout: async (): Promise<void> => {
    await fetch(`${API_BASE}/auth/logout`, { method: 'POST' })
  },
}

export default api
