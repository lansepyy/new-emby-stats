import { createContext, useState, useEffect, type ReactNode } from 'react'

export interface Server {
  id: string
  name: string
  emby_url: string
  playback_db: string
  users_db: string
  auth_db: string
  emby_api_key: string
  is_default: boolean
  created_at?: string
  updated_at?: string
}

interface ServerContextType {
  servers: Server[]
  currentServer: Server | null
  setCurrentServer: (server: Server) => void
  refreshServers: () => Promise<void>
}

const ServerContext = createContext<ServerContextType | undefined>(undefined)

export function ServerProvider({ children }: { children: ReactNode }) {
  const [servers] = useState<Server[]>([])
  const [currentServer, setCurrentServer] = useState<Server | null>(null)

  const refreshServers = async () => {
    // Placeholder for future implementation
    // Would fetch servers from API
  }

  useEffect(() => {
    // Initialize servers on mount
    refreshServers()
  }, [])

  return (
    <ServerContext.Provider value={{ servers, currentServer, setCurrentServer, refreshServers }}>
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
