import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import { api } from '@/services/api'

export interface Server {
  id: string
  name: string
  emby_url: string
  playback_db?: string
  users_db?: string
  auth_db?: string
  emby_api_key?: string
  is_default: boolean
  created_at?: string
  updated_at?: string
}

interface ServerContextType {
  servers: Server[]
  currentServer: Server | null
  isLoading: boolean
  setCurrentServer: (server: Server) => void
  refreshServers: () => Promise<void>
}

const ServerContext = createContext<ServerContextType | null>(null)

export function ServerProvider({ children }: { children: ReactNode }) {
  const [servers, setServers] = useState<Server[]>([])
  const [currentServer, setCurrentServerState] = useState<Server | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // 加载服务器列表
  useEffect(() => {
    const loadServers = async () => {
      try {
        const data = await api.getServers()
        setServers(data.servers || [])
        // 设置当前服务器
        const current = data.servers?.find((s: Server) => s.id === data.current_server_id) ||
                        data.servers?.find((s: Server) => s.is_default) ||
                        data.servers?.[0] ||
                        null
        setCurrentServerState(current)
      } catch (error) {
        console.error('Failed to load servers:', error)
      } finally {
        setIsLoading(false)
      }
    }

    loadServers()
  }, [])

  const setCurrentServer = (server: Server) => {
    setCurrentServerState(server)
    // 保存选择到本地存储或调用API
    localStorage.setItem('currentServerId', server.id)
  }

  const refreshServers = async () => {
    setIsLoading(true)
    try {
      const data = await api.getServers()
      setServers(data.servers || [])
      // 更新当前服务器
      const updatedCurrent = data.servers?.find((s: Server) => s.id === currentServer?.id) ||
                            data.servers?.find((s: Server) => s.is_default) ||
                            data.servers?.[0] ||
                            null
      setCurrentServerState(updatedCurrent)
    } catch (error) {
      console.error('Failed to refresh servers:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <ServerContext.Provider value={{ servers, currentServer, isLoading, setCurrentServer, refreshServers }}>
      {children}
    </ServerContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useServer() {
  const context = useContext(ServerContext)
  if (!context) {
    throw new Error('useServer must be used within ServerProvider')
  }
  return context
}
