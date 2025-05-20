import React from 'react';
import { motion } from 'framer-motion';

const LoadingScreen: React.FC = () => {
  // Animation variants for the container
  const containerVariants = {
    initial: { opacity: 0 },
    animate: { 
      opacity: 1,
      transition: { 
        when: "beforeChildren",
        staggerChildren: 0.2,
        duration: 0.5
      }
    },
    exit: {
      opacity: 0,
      transition: {
        when: "afterChildren",
        staggerChildren: 0.1,
        staggerDirection: -1,
        duration: 0.5
      }
    }
  };

  // Animation variants for the logo
  const logoVariants = {
    initial: { scale: 0.8, opacity: 0 },
    animate: { 
      scale: 1, 
      opacity: 1,
      transition: {
        duration: 0.8,
        ease: [0.34, 1.56, 0.64, 1] // Spring-like effect
      }
    },
    exit: { 
      scale: 1.2, 
      opacity: 0,
      transition: {
        duration: 0.4
      }
    }
  };

  // Animation variants for the loading text
  const textVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { 
      opacity: 1, 
      y: 0,
      transition: {
        duration: 0.5
      }
    },
    exit: { 
      opacity: 0, 
      y: -20,
      transition: {
        duration: 0.3
      }
    }
  };

  // Animation variants for the fractal elements
  const fractalVariants = {
    initial: { opacity: 0, scale: 0 },
    animate: (i: number) => ({ 
      opacity: 1, 
      scale: 1,
      transition: {
        delay: i * 0.1,
        duration: 0.6,
        ease: [0.34, 1.56, 0.64, 1]
      }
    }),
    exit: (i: number) => ({ 
      opacity: 0, 
      scale: 0,
      transition: {
        delay: i * 0.05,
        duration: 0.4,
        ease: "easeInOut"
      }
    })
  };
  
  // Animated dots for loading indicator
  const dotsVariants = {
    initial: { opacity: 0 },
    animate: {
      opacity: [0, 1, 0],
      transition: {
        repeat: Infinity,
        duration: 1.5,
        ease: "easeInOut",
        times: [0, 0.5, 1]
      }
    }
  };

  return (
    <motion.div 
      className="fixed inset-0 flex flex-col items-center justify-center bg-background z-50"
      variants={containerVariants}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      {/* Fractal pattern background */}
      <div className="absolute inset-0 overflow-hidden opacity-20">
        {Array.from({ length: 8 }).map((_, i) => (
          <motion.div
            key={i}
            custom={i}
            variants={fractalVariants}
            className="absolute rounded-full border border-primary-light"
            style={{
              width: `${(i + 1) * 100}px`,
              height: `${(i + 1) * 100}px`,
              left: `calc(50% - ${(i + 1) * 50}px)`,
              top: `calc(50% - ${(i + 1) * 50}px)`,
              borderWidth: i % 2 === 0 ? '1px' : '2px',
              borderColor: i % 3 === 0 ? '#0a84ff' : i % 3 === 1 ? '#00d170' : '#bf5af2'
            }}
          />
        ))}
      </div>
      
      {/* Center logo and text */}
      <motion.div 
        className="relative z-10 flex flex-col items-center"
        variants={logoVariants}
      >
        <div className="w-32 h-32 rounded-xl glass-panel flex items-center justify-center border-2 border-primary shadow-neon-primary mb-8 relative overflow-hidden">
          <div className="absolute inset-0 bg-background-dark opacity-40"></div>
          <svg width="80" height="80" viewBox="0 0 512 512" className="relative z-10">
            <g filter="url(#filter0_f)">
              <path d="M256 116L307.84 218.16L420 233.68L338 313.84L356.72 425.6L256 373.28L155.28 425.6L174 313.84L92 233.68L204.16 218.16L256 116Z" fill="#0A84FF"/>
            </g>
            <path d="M256 146L297.21 229.18L388 241.86L322 306.62L336.42 397.2L256 354.36L175.58 397.2L190 306.62L124 241.86L214.79 229.18L256 146Z" fill="none" stroke="#00D170" strokeWidth="6"/>
            <g filter="url(#filter1_f)">
              <path d="M256 176L277.02 219.1L324 224.52L290 257.74L298.03 304.4L256 282.44L213.97 304.4L222 257.74L188 224.52L234.98 219.1L256 176Z" fill="#BF5AF2"/>
            </g>
            <defs>
              <filter id="filter0_f" x="82" y="106" width="348" height="329.6" filterUnits="userSpaceOnUse" colorInterpolationFilters="sRGB">
                <feGaussianBlur stdDeviation="5" />
              </filter>
              <filter id="filter1_f" x="178" y="166" width="156" height="148.4" filterUnits="userSpaceOnUse" colorInterpolationFilters="sRGB">
                <feGaussianBlur stdDeviation="5" />
              </filter>
            </defs>
          </svg>
        </div>
        
        <motion.h1 
          className="text-2xl font-display tracking-wider text-white mb-2"
          variants={textVariants}
        >
          <span className="neon-text-primary">RFM</span> <span className="text-white">Architecture</span>
        </motion.h1>
        
        <motion.div 
          className="flex space-x-2 items-center text-white/60"
          variants={textVariants}
        >
          <span>Initializing System</span>
          <motion.span variants={dotsVariants}>...</motion.span>
        </motion.div>
      </motion.div>
    </motion.div>
  );
};

export default LoadingScreen;