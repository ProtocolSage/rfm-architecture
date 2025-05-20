import { useState, useEffect } from 'react'
import { Routes, Route, useLocation } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'

// Pages
import Dashboard from './pages/Dashboard'
import FractalExplorer from './pages/FractalExplorer'
import ArchitectureEditor from './pages/ArchitectureEditor'
import Settings from './pages/Settings'

// Components
import MainLayout from './layouts/MainLayout'
import { useSoundSystem } from './hooks/useSoundSystem'
import GlowCursor from './components/effects/GlowCursor'
import LoadingScreen from './components/common/LoadingScreen'

function App() {
  const location = useLocation()
  const { playSound } = useSoundSystem()
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Simulate loading assets
    const timer = setTimeout(() => {
      setIsLoading(false)
      playSound('startup')
    }, 2000)

    return () => clearTimeout(timer)
  }, [playSound])

  // Play navigation sound on route change
  useEffect(() => {
    if (!isLoading) {
      playSound('nav')
    }
  }, [location.pathname, isLoading, playSound])

  if (isLoading) {
    return <LoadingScreen />
  }

  return (
    <>
      <GlowCursor />
      
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          <Route path="/" element={<MainLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="explorer" element={<FractalExplorer />} />
            <Route path="architect" element={<ArchitectureEditor />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </AnimatePresence>
    </>
  )
}

export default App