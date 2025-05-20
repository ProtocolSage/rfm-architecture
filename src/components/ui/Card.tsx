import React, { ReactNode } from 'react';
import { motion, MotionProps, Variants } from 'framer-motion';
import { useSoundSystem } from '../../hooks/useSoundSystem';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  variant?: 'default' | 'primary' | 'secondary' | 'purple' | 'dark';
  glowEffect?: 'none' | 'subtle' | 'intense';
  isHoverable?: boolean;
  isInteractive?: boolean;
  onClick?: () => void;
  animate?: boolean;
  delay?: number;
  className?: string;
}

// Animation variants
const cardVariants: Variants = {
  hidden: { 
    opacity: 0, 
    y: 20,
    scale: 0.98,
  },
  visible: (delay: number) => ({ 
    opacity: 1, 
    y: 0,
    scale: 1,
    transition: {
      delay: delay * 0.1,
      duration: 0.4,
      ease: [0.25, 1, 0.5, 1],
    }
  }),
  hover: { 
    y: -5, 
    scale: 1.02,
    transition: {
      duration: 0.2,
      ease: "easeOut",
    }
  },
  tap: { 
    scale: 0.98,
    transition: {
      duration: 0.1,
      ease: "easeIn",
    }
  }
};

const Card: React.FC<CardProps & MotionProps> = ({
  children,
  variant = 'default',
  glowEffect = 'none',
  isHoverable = false,
  isInteractive = false,
  onClick,
  animate = true,
  delay = 0,
  className = '',
  ...props
}) => {
  const { playSound } = useSoundSystem();
  
  // Base classes for all cards
  const baseClasses = 'relative rounded-xl backdrop-blur-md overflow-hidden';
  
  // Variant-specific classes
  const variantClasses = {
    default: 'bg-glass border border-glass-strong',
    primary: 'bg-primary/10 border border-primary/30',
    secondary: 'bg-secondary/10 border border-secondary/30',
    purple: 'bg-accent-purple/10 border border-accent-purple/30',
    dark: 'bg-background-dark border border-glass',
  };
  
  // Glow-specific classes
  const glowClasses = {
    none: '',
    subtle: variant === 'default' 
      ? 'shadow-neon-glow' 
      : variant === 'primary' 
        ? 'shadow-neon-primary' 
        : variant === 'secondary' 
          ? 'shadow-neon-secondary' 
          : variant === 'purple' 
            ? 'shadow-neon-purple' 
            : '',
    intense: variant === 'default' 
      ? 'shadow-neon-glow' 
      : variant === 'primary' 
        ? 'shadow-[0_0_15px_theme(colors.primary.DEFAULT),0_0_30px_rgba(10,132,255,0.5)]' 
        : variant === 'secondary' 
          ? 'shadow-[0_0_15px_theme(colors.secondary.DEFAULT),0_0_30px_rgba(0,209,112,0.5)]' 
          : variant === 'purple' 
            ? 'shadow-[0_0_15px_theme(colors.accent.purple),0_0_30px_rgba(191,90,242,0.5)]' 
            : '',
  };
  
  // Interactive behaviors
  const handleClick = () => {
    if (isInteractive && onClick) {
      playSound('click');
      onClick();
    }
  };
  
  const handleHover = () => {
    if (isInteractive) {
      playSound('hover');
    }
  };
  
  return (
    <motion.div
      className={`
        ${baseClasses} 
        ${variantClasses[variant]} 
        ${glowClasses[glowEffect]} 
        ${isHoverable ? 'cursor-pointer transform transition-transform duration-300' : ''}
        ${className}
      `}
      variants={animate ? cardVariants : undefined}
      initial={animate ? "hidden" : undefined}
      animate={animate ? "visible" : undefined}
      whileHover={isHoverable ? "hover" : undefined}
      whileTap={isInteractive ? "tap" : undefined}
      custom={delay}
      onClick={handleClick}
      onMouseEnter={handleHover}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export default Card;