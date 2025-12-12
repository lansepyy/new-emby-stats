import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import { api } from '@/services/api'

export interface Server {
  id: string
  name: string
  emby_url: string
  is_default: boolean
  created_at: string
}

interface ServerContextType {
  servers: Server[]
  currentServer: Server | null
  setCurrentServer: (server: Server) => void
  refreshServers: () => Promise<void>
  isLoading: boolean
}

const ServerContext = createContext<ServerContextType | undefined>(undefined)

export function ServerProvider({ children }: { children: ReactNode }) {
  const [servers, setServers] = useState<Server[]>([])
  const [currentServer, setCurrentServerState] = useState<Server | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const refreshServers = async () => {
    try {
      setIsLoading(true)
      const data = await api.getServers()
      setServers(data.servers || [])
      
      // 如果没有当前服务器，设置默认服务器
      if (!currentServer && data.servers && data.servers.length > 0) {
        const defaultServer = data.servers.find((s: Server) => s.is_default) || data.servers[0]
        setCurrentServerState(defaultServer)
        localStorage.setItem('currentServerId', defaultServer.id)
      }
    } catch (error) {
      console.error('Failed to fetch servers:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const setCurrentServer = (server: Server) => {
    setCurrentServerState(server)
    localStorage.setItem('currentServerId', server.id)
  }

  useEffect(() => {
    const initServers = async () => {
      await refreshServers()
    }

    initServers()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <ServerContext.Provider
      value={{
        servers,
        currentServer,
        setCurrentServer,
        refreshServers,
        isLoading,
      }}
    >
      {children}
    </ServerContext.Provider>
  )
}

export function useServer() {
  const context = useContext(ServerContext)
  if (context === undefined) {
    throw new Error('useServer must be used within a ServerProvider')
  }
  return context
}
