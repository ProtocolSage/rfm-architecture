import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useSoundSystem } from '../../hooks/useSoundSystem';

interface SidebarProps {
  open: boolean;
}

// Navigation items
const navItems = [
  { 
    path: '/', 
    name: 'Dashboard', 
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
      </svg>
    )
  },
  { 
    path: '/explorer', 
    name: 'Fractal Explorer', 
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clipRule="evenodd" />
      </svg>
    )
  },
  { 
    path: '/architect', 
    name: 'Architecture Editor', 
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path d="M11 17a1 1 0 001.447.894l4-2A1 1 0 0017 15V9.236a1 1 0 00-1.447-.894l-4 2a1 1 0 00-.553.894V17zM15.211 6.276a1 1 0 000-1.788l-4.764-2.382a1 1 0 00-.894 0L4.789 4.488a1 1 0 000 1.788l4.764 2.382a1 1 0 00.894 0l4.764-2.382zM4.447 8.342A1 1 0 003 9.236V15a1 1 0 00.553.894l4 2A1 1 0 009 17v-5.764a1 1 0 00-.553-.894l-4-2z" />
      </svg>
    )
  },
  { 
    path: '/settings', 
    name: 'Settings', 
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
      </svg>
    )
  }
];

// Animation variants
const sidebarVariants = {
  open: { 
    width: 260,
    transition: { duration: 0.3, ease: "easeInOut" }
  },
  closed: { 
    width: 80,
    transition: { duration: 0.3, ease: "easeInOut", delay: 0.1 }
  }
};

const navItemVariants = {
  open: { 
    opacity: 1, 
    x: 0,
    transition: { duration: 0.2, ease: "easeOut" }
  },
  closed: { 
    opacity: 0, 
    x: -10,
    transition: { duration: 0.2, ease: "easeIn" }
  }
};

const Sidebar: React.FC<SidebarProps> = ({ open }) => {
  const location = useLocation();
  const { playSound } = useSoundSystem();

  const handleNavHover = () => {
    playSound('hover');
  };

  return (
    <motion.aside
      className="h-full glass-panel border-glass-strong backdrop-blur-md relative z-10 overflow-hidden"
      variants={sidebarVariants}
      initial="closed"
      animate={open ? "open" : "closed"}
    >
      {/* Logo & Branding */}
      <div className="px-6 py-8 flex items-center h-20">
        <div className="relative flex items-center">
          <svg width="32" height="32" viewBox="0 0 512 512" className="relative z-10">
            <g filter="url(#filter0_f)">
              <path d="M256 116L307.84 218.16L420 233.68L338 313.84L356.72 425.6L256 373.28L155.28 425.6L174 313.84L92 233.68L204.16 218.16L256 116Z" fill="#0A84FF"/>
            </g>
            <path d="M256 146L297.21 229.18L388 241.86L322 306.62L336.42 397.2L256 354.36L175.58 397.2L190 306.62L124 241.86L214.79 229.18L256 146Z" stroke="#00D170" strokeWidth="6" fill="none"/>
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
          
          <AnimatePresence>
            {open && (
              <motion.div
                className="ml-3"
                variants={navItemVariants}
                initial="closed"
                animate="open"
                exit="closed"
              >
                <p className="font-display text-lg tracking-wider">
                  <span className="neon-text-primary">RFM</span>
                </p>
                <p className="text-xs text-white/60">Architecture</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="px-3">
        <ul className="space-y-1">
          {navItems.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                onMouseEnter={handleNavHover}
                className={({ isActive }) => `
                  flex items-center px-3 py-3 rounded-lg transition-all duration-300 relative
                  ${isActive 
                    ? 'bg-glass-strong text-white shadow-neon-glow font-medium' 
                    : 'text-white/70 hover:text-white hover:bg-glass'}
                `}
                end={item.path === '/'}
              >
                {({ isActive }) => (
                  <>
                    <span className={`${isActive ? 'text-primary' : ''}`}>
                      {item.icon}
                    </span>
                    
                    <AnimatePresence>
                      {open && (
                        <motion.span
                          className="ml-3"
                          variants={navItemVariants}
                          initial="closed"
                          animate="open"
                          exit="closed"
                        >
                          {item.name}
                        </motion.span>
                      )}
                    </AnimatePresence>
                    
                    {isActive && (
                      <motion.div
                        className="absolute inset-0 rounded-lg pointer-events-none"
                        layoutId="sidebar-indicator"
                        transition={{ type: 'spring', duration: 0.5, bounce: 0.3 }}
                      >
                        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-3/4 bg-primary rounded-full shadow-neon-primary" />
                      </motion.div>
                    )}
                  </>
                )}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Footer */}
      <div className="absolute bottom-0 left-0 right-0 px-3 py-6">
        <AnimatePresence>
          {open && (
            <motion.div
              className="text-xs text-white/40 px-3"
              variants={navItemVariants}
              initial="closed"
              animate="open"
              exit="closed"
            >
              <p>RFM Architecture v1.0</p>
              <p>© 2025 Protocol Sage</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.aside>
  );
};

export default Sidebar;