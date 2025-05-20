import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import Card from '../components/ui/Card';
import { useSoundSystem } from '../hooks/useSoundSystem';

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: { 
    opacity: 1,
    transition: { 
      when: "beforeChildren",
      staggerChildren: 0.1,
      duration: 0.3
    }
  }
};

const Dashboard: React.FC = () => {
  const { playSound } = useSoundSystem();
  const [stats, setStats] = useState({
    activeFractals: 0,
    renderTime: 0,
    complexity: 0,
    totalRenders: 0,
  });
  
  // Simulate loading stats
  useEffect(() => {
    const timer = setTimeout(() => {
      setStats({
        activeFractals: 23,
        renderTime: 2.4,
        complexity: 78,
        totalRenders: 1254,
      });
      playSound('data');
    }, 1200);
    
    return () => clearTimeout(timer);
  }, [playSound]);
  
  // Recent fractal renders
  const recentFractals = [
    {
      id: 'fract-001',
      name: 'Emerald Spiral',
      type: 'Julia Set',
      timestamp: '2025-05-20T08:23:15',
      parameters: { c: '-0.8 + 0.156i', iterations: 500 },
      thumbnail: 'https://source.unsplash.com/random/300x200/?fractal,green'
    },
    {
      id: 'fract-002',
      name: 'Cosmic Vortex',
      type: 'Mandelbrot',
      timestamp: '2025-05-19T16:45:30',
      parameters: { zoom: 1500, centerX: -0.235, centerY: 0.827 },
      thumbnail: 'https://source.unsplash.com/random/300x200/?fractal,blue'
    },
    {
      id: 'fract-003',
      name: 'Neon Dendrite',
      type: 'L-System',
      timestamp: '2025-05-19T11:12:08',
      parameters: { angle: 22.5, iterations: 7, axiom: 'F+F+F+F' },
      thumbnail: 'https://source.unsplash.com/random/300x200/?fractal,pink'
    }
  ];
  
  const handleCardClick = (id: string) => {
    console.log(`Card clicked: ${id}`);
    playSound('click');
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-8"
    >
      {/* Header with Welcome Message */}
      <div className="mb-10">
        <h1 className="text-4xl font-display tracking-wide mb-2">
          <span className="neon-text-primary">Welcome back,</span> Protocol Sage
        </h1>
        <p className="text-white/60">
          Your Recursive Fractal Mind visualization toolkit is ready for exploration.
        </p>
      </div>
      
      {/* Statistics Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card variant="primary" glowEffect="subtle" delay={0}>
          <div className="p-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-white/90">Active Fractals</h3>
              <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-primary" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M11 17a1 1 0 001.447.894l4-2A1 1 0 0017 15V9.236a1 1 0 00-1.447-.894l-4 2a1 1 0 00-.553.894V17zM15.211 6.276a1 1 0 000-1.788l-4.764-2.382a1 1 0 00-.894 0L4.789 4.488a1 1 0 000 1.788l4.764 2.382a1 1 0 00.894 0l4.764-2.382zM4.447 8.342A1 1 0 003 9.236V15a1 1 0 00.553.894l4 2A1 1 0 009 17v-5.764a1 1 0 00-.553-.894l-4-2z" />
                </svg>
              </div>
            </div>
            <div className="mt-4">
              <motion.div 
                className="text-3xl font-display tracking-wider neon-text-primary"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5, duration: 0.5 }}
              >
                {stats.activeFractals}
              </motion.div>
              <p className="text-sm text-white/60 mt-1">Projects in workspace</p>
            </div>
          </div>
        </Card>
        
        <Card variant="secondary" glowEffect="subtle" delay={1}>
          <div className="p-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-white/90">Avg. Render Time</h3>
              <div className="w-10 h-10 rounded-full bg-secondary/20 flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-secondary" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
            <div className="mt-4">
              <motion.div 
                className="text-3xl font-display tracking-wider"
                style={{ color: '#00d170', textShadow: '0 0 10px rgba(0, 209, 112, 0.7)' }}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.6, duration: 0.5 }}
              >
                {stats.renderTime}s
              </motion.div>
              <p className="text-sm text-white/60 mt-1">Per 1000x1000 frame</p>
            </div>
          </div>
        </Card>
        
        <Card variant="purple" glowEffect="subtle" delay={2}>
          <div className="p-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-white/90">Complexity Score</h3>
              <div className="w-10 h-10 rounded-full bg-accent-purple/20 flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-accent-purple" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z" />
                  <path d="M12 2.252A8.014 8.014 0 0117.748 8H12V2.252z" />
                </svg>
              </div>
            </div>
            <div className="mt-4">
              <motion.div 
                className="text-3xl font-display tracking-wider"
                style={{ color: '#bf5af2', textShadow: '0 0 10px rgba(191, 90, 242, 0.7)' }}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.7, duration: 0.5 }}
              >
                {stats.complexity}%
              </motion.div>
              <p className="text-sm text-white/60 mt-1">Algorithm efficiency</p>
            </div>
          </div>
        </Card>
        
        <Card variant="default" glowEffect="subtle" delay={3}>
          <div className="p-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-white/90">Total Renders</h3>
              <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4 2a2 2 0 00-2 2v11a3 3 0 106 0V4a2 2 0 00-2-2H4zm1 14a1 1 0 100-2 1 1 0 000 2zm5-1.757l4.9-4.9a2 2 0 000-2.828L13.485 5.1a2 2 0 00-2.828 0L10 5.757v8.486zM16 18H9.071l6-6H16a2 2 0 012 2v2a2 2 0 01-2 2z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
            <div className="mt-4">
              <motion.div 
                className="text-3xl font-display tracking-wider text-white"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.8, duration: 0.5 }}
              >
                {stats.totalRenders.toLocaleString()}
              </motion.div>
              <p className="text-sm text-white/60 mt-1">Historical operations</p>
            </div>
          </div>
        </Card>
      </div>
      
      {/* Recent Fractals Section */}
      <div className="mt-12">
        <h2 className="text-xl font-medium mb-6 flex items-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-primary" viewBox="0 0 20 20" fill="currentColor">
            <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z" />
          </svg>
          Recent Fractal Renders
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {recentFractals.map((fractal, index) => (
            <Card 
              key={fractal.id} 
              variant="default" 
              glowEffect="subtle" 
              isHoverable
              isInteractive
              onClick={() => handleCardClick(fractal.id)}
              delay={index + 4}
              className="transform transition-all duration-300 hover:shadow-neon-primary overflow-hidden"
            >
              <div className="h-48 bg-background-dark relative overflow-hidden">
                <img 
                  src={fractal.thumbnail} 
                  alt={fractal.name} 
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-background via-background/60 to-transparent opacity-70"></div>
                <div className="absolute bottom-0 left-0 right-0 p-4">
                  <span className="px-2 py-1 rounded-full text-xs font-medium bg-glass backdrop-blur-sm">
                    {fractal.type}
                  </span>
                </div>
              </div>
              <div className="p-5">
                <h3 className="text-lg font-medium mb-2">{fractal.name}</h3>
                <p className="text-sm text-white/60 mb-3">
                  {new Date(fractal.timestamp).toLocaleString()}
                </p>
                <div className="flex justify-between items-center">
                  <div>
                    <span className="px-2 py-1 rounded-full text-xs font-medium bg-primary/20 text-primary">
                      View Details
                    </span>
                  </div>
                  <button 
                    className="w-8 h-8 rounded-full flex items-center justify-center bg-glass hover:bg-glass-strong transition-colors"
                    onClick={(e) => {
                      e.stopPropagation();
                      playSound('success');
                    }}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-white" viewBox="0 0 20 20" fill="currentColor">
                      <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                      <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
                    </svg>
                  </button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
      
      {/* Quick Actions Section */}
      <Card variant="dark" glowEffect="subtle" delay={8} className="mt-6">
        <div className="p-6">
          <h2 className="text-xl font-medium mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <button 
              className="p-4 rounded-xl bg-glass hover:bg-glass-strong transition-all duration-300 text-center flex flex-col items-center justify-center space-y-2"
              onClick={() => playSound('click')}
            >
              <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-primary" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
                </svg>
              </div>
              <span className="text-sm">New Fractal</span>
            </button>
            
            <button 
              className="p-4 rounded-xl bg-glass hover:bg-glass-strong transition-all duration-300 text-center flex flex-col items-center justify-center space-y-2"
              onClick={() => playSound('click')}
            >
              <div className="w-10 h-10 rounded-full bg-secondary/20 flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-secondary" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
                </svg>
              </div>
              <span className="text-sm">Run Batch</span>
            </button>
            
            <button 
              className="p-4 rounded-xl bg-glass hover:bg-glass-strong transition-all duration-300 text-center flex flex-col items-center justify-center space-y-2"
              onClick={() => playSound('click')}
            >
              <div className="w-10 h-10 rounded-full bg-accent-purple/20 flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-accent-purple" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M15 8a3 3 0 10-2.977-2.63l-4.94 2.47a3 3 0 100 4.319l4.94 2.47a3 3 0 10.895-1.789l-4.94-2.47a3.027 3.027 0 000-.74l4.94-2.47C13.456 7.68 14.19 8 15 8z" />
                </svg>
              </div>
              <span className="text-sm">Share</span>
            </button>
            
            <button 
              className="p-4 rounded-xl bg-glass hover:bg-glass-strong transition-all duration-300 text-center flex flex-col items-center justify-center space-y-2"
              onClick={() => playSound('click')}
            >
              <div className="w-10 h-10 rounded-full bg-accent-orange/20 flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-accent-orange" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                </svg>
              </div>
              <span className="text-sm">Help</span>
            </button>
          </div>
        </div>
      </Card>
    </motion.div>
  );
};

export default Dashboard;