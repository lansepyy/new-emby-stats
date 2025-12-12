import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { AuthProvider } from './contexts/AuthContext'
import { ThemeProvider } from './contexts/ThemeContext'
import { FilterProvider } from './contexts/FilterContext'
import { ServerProvider } from './contexts/ServerContext'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider>
      <AuthProvider>
        <ServerProvider>
          <FilterProvider>
            <App />
          </FilterProvider>
        </ServerProvider>
      </AuthProvider>
    </ThemeProvider>
  </StrictMode>,
)
