import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import Sidebar from '../components/navigation/Sidebar';
import Header from '../components/navigation/Header';
import { useSoundSystem } from '../hooks/useSoundSystem';

// Animation variants
const pageVariants = {
  initial: { opacity: 0, x: -20 },
  animate: { 
    opacity: 1, 
    x: 0,
    transition: {
      duration: 0.4,
      ease: [0.25, 1, 0.5, 1],
      when: "beforeChildren",
      staggerChildren: 0.1
    }
  },
  exit: { 
    opacity: 0,
    x: 20,
    transition: {
      duration: 0.3
    }
  }
};

// Background stars component for a subtle animated background
const BackgroundStars: React.FC = () => {
  // Generate random stars
  const stars = Array.from({ length: 100 }, (_, i) => ({
    id: i,
    size: Math.random() * 2 + 1,
    x: Math.random() * 100,
    y: Math.random() * 100,
    delay: Math.random() * 5,
    duration: Math.random() * 3 + 2
  }));

  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
      {stars.map(star => (
        <motion.div
          key={star.id}
          className="absolute rounded-full bg-white"
          style={{
            width: star.size,
            height: star.size,
            left: `${star.x}%`,
            top: `${star.y}%`,
            opacity: 0.1 + Math.random() * 0.3,
          }}
          animate={{
            opacity: [0.1, 0.5, 0.1],
          }}
          transition={{
            duration: star.duration,
            delay: star.delay,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
      ))}
    </div>
  );
};

const MainLayout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const { playSound } = useSoundSystem();

  const toggleSidebar = () => {
    setSidebarOpen(prev => !prev);
    playSound('click');
  };

  return (
    <div className="min-h-screen flex flex-col bg-background text-white relative overflow-hidden">
      <BackgroundStars />
      
      {/* Glass-like radial gradient in the center */}
      <div 
        className="absolute pointer-events-none w-full h-full opacity-20 z-0"
        style={{
          background: 'radial-gradient(circle at 50% 30%, rgba(10, 132, 255, 0.3) 0%, transparent 70%)'
        }}
      />
      
      <Header sidebarOpen={sidebarOpen} toggleSidebar={toggleSidebar} />
      
      <div className="flex flex-1 overflow-hidden">
        <Sidebar open={sidebarOpen} />
        
        <motion.main 
          className="flex-1 p-6 overflow-auto"
          initial="initial"
          animate="animate"
          exit="exit"
          variants={pageVariants}
        >
          <div className="max-w-7xl mx-auto">
            <AnimatePresence mode="wait">
              <Outlet />
            </AnimatePresence>
          </div>
        </motion.main>
      </div>
    </div>
  );
};

export default MainLayout;