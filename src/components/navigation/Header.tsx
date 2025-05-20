import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLocation } from 'react-router-dom';
import { useSoundSystem } from '../../hooks/useSoundSystem';

interface HeaderProps {
  sidebarOpen: boolean;
  toggleSidebar: () => void;
}

// Dynamically generate page title based on route
const getPageTitle = (pathname: string): string => {
  switch (pathname) {
    case '/':
      return 'Dashboard';
    case '/explorer':
      return 'Fractal Explorer';
    case '/architect':
      return 'Architecture Editor';
    case '/settings':
      return 'Settings';
    default:
      return pathname.split('/').pop()?.replace('-', ' ') || 'Dashboard';
  }
};

const Header: React.FC<HeaderProps> = ({ sidebarOpen, toggleSidebar }) => {
  const location = useLocation();
  const { playSound, enabled: soundEnabled, setEnabled: setSoundEnabled } = useSoundSystem();
  const [showNotification, setShowNotification] = useState(false);
  
  const pageTitle = getPageTitle(location.pathname);
  
  const handleButtonHover = () => {
    playSound('hover');
  };
  
  const handleButtonClick = () => {
    playSound('click');
  };
  
  const toggleNotification = () => {
    setShowNotification(!showNotification);
    playSound(showNotification ? 'click' : 'notification');
  };
  
  const toggleSound = () => {
    setSoundEnabled(!soundEnabled);
    if (soundEnabled) {
      // Play the sound before disabling
      playSound('click');
    }
  };

  return (
    <header className="h-20 glass-panel backdrop-blur-md border-b border-glass-strong z-20 px-6 flex items-center justify-between">
      {/* Left Section */}
      <div className="flex items-center">
        <motion.button
          className="w-10 h-10 rounded-lg flex items-center justify-center text-white/80 hover:text-white hover:bg-glass-strong transition-all duration-300"
          onClick={toggleSidebar}
          onMouseEnter={handleButtonHover}
          whileTap={{ scale: 0.95 }}
        >
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            className="h-5 w-5" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <motion.path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d={sidebarOpen 
                ? "M4 6h16M4 12h8m-8 6h16" 
                : "M4 6h16M4 12h16m-7 6h7"
              }
              initial={false}
              animate={{ d: sidebarOpen 
                ? "M4 6h16M4 12h8m-8 6h16" 
                : "M4 6h16M4 12h16m-7 6h7"
              }}
              transition={{ duration: 0.3 }}
            />
          </svg>
        </motion.button>
        
        <div className="ml-6">
          <motion.h1 
            className="text-xl font-display tracking-wide"
            key={pageTitle}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            transition={{ duration: 0.3 }}
          >
            {pageTitle}
          </motion.h1>
          <p className="text-xs text-white/60">
            {new Date().toLocaleDateString('en-US', { 
              weekday: 'long', 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric' 
            })}
          </p>
        </div>
      </div>
      
      {/* Right Section */}
      <div className="flex items-center space-x-2">
        {/* Sound Toggle */}
        <motion.button
          className={`w-10 h-10 rounded-lg flex items-center justify-center transition-all duration-300 ${
            soundEnabled 
              ? 'text-secondary hover:text-secondary-light' 
              : 'text-white/50 hover:text-white/80'
          }`}
          onClick={toggleSound}
          onMouseEnter={handleButtonHover}
          whileTap={{ scale: 0.95 }}
          title={soundEnabled ? "Disable sound effects" : "Enable sound effects"}
        >
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            className="h-5 w-5" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            {soundEnabled ? (
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M15.536 8.464a5 5 0 010 7.072M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" 
              />
            ) : (
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" 
              />
            )}
          </svg>
        </motion.button>
        
        {/* Notification Bell */}
        <div className="relative">
          <motion.button
            className="w-10 h-10 rounded-lg flex items-center justify-center text-white/80 hover:text-white hover:bg-glass-strong transition-all duration-300"
            onClick={toggleNotification}
            onMouseEnter={handleButtonHover}
            whileTap={{ scale: 0.95 }}
          >
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              className="h-5 w-5" 
              fill="none" 
              viewBox="0 0 24 24" 
              stroke="currentColor"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" 
              />
            </svg>
            
            {/* Notification Indicator */}
            <span className="absolute top-2 right-2 h-2 w-2 rounded-full bg-accent-pink"></span>
          </motion.button>
          
          {/* Notification Dropdown */}
          <AnimatePresence>
            {showNotification && (
              <motion.div
                className="absolute right-0 mt-2 w-72 glass-panel backdrop-blur-md border border-glass-strong rounded-xl shadow-neon-glow overflow-hidden z-50"
                initial={{ opacity: 0, y: -10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -10, scale: 0.95 }}
                transition={{ duration: 0.2 }}
              >
                <div className="px-4 py-3 border-b border-glass-strong">
                  <h3 className="text-sm font-medium">Notifications</h3>
                </div>
                <div className="max-h-60 overflow-y-auto">
                  <div className="px-4 py-3 hover:bg-glass-strong transition-colors border-b border-glass">
                    <p className="text-sm font-medium">System Update</p>
                    <p className="text-xs text-white/60 mt-1">
                      New version of RFM Architecture available.
                    </p>
                    <p className="text-xs text-accent-pink mt-1">2 minutes ago</p>
                  </div>
                  <div className="px-4 py-3 hover:bg-glass-strong transition-colors">
                    <p className="text-sm font-medium">Render Completed</p>
                    <p className="text-xs text-white/60 mt-1">
                      Your fractal rendering has completed successfully.
                    </p>
                    <p className="text-xs text-accent-teal mt-1">15 minutes ago</p>
                  </div>
                </div>
                <div className="px-4 py-2 border-t border-glass-strong">
                  <button 
                    className="text-xs text-primary hover:text-primary-light transition-colors"
                    onClick={() => {
                      handleButtonClick();
                      setShowNotification(false);
                    }}
                  >
                    Clear all notifications
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
        
        {/* User Profile */}
        <div className="relative">
          <button 
            className="w-10 h-10 rounded-full overflow-hidden gradient-border"
            onClick={handleButtonClick}
            onMouseEnter={handleButtonHover}
          >
            <div className="w-full h-full flex items-center justify-center bg-glass-strong text-white">
              PS
            </div>
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;