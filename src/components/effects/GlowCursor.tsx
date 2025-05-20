import React, { useState, useEffect, useRef } from 'react';
import { useSoundSystem } from '../../hooks/useSoundSystem';
import { motion, useMotionValue, useSpring } from 'framer-motion';

const GlowCursor: React.FC = () => {
  const { playSound } = useSoundSystem();
  const [isPointer, setIsPointer] = useState(false);
  const [isClicking, setIsClicking] = useState(false);
  const cursorRef = useRef<HTMLDivElement>(null);
  const glowRef = useRef<HTMLDivElement>(null);
  
  // Use motion values for smooth cursor movement
  const cursorX = useMotionValue(-100);
  const cursorY = useMotionValue(-100);
  
  // Apply spring physics for smoother, slightly delayed movement
  const springConfig = { damping: 25, stiffness: 400 };
  const springX = useSpring(cursorX, springConfig);
  const springY = useSpring(cursorY, springConfig);

  useEffect(() => {
    const moveCursor = (e: MouseEvent) => {
      cursorX.set(e.clientX);
      cursorY.set(e.clientY);
      
      // Check if the cursor is over a clickable element
      const element = document.elementFromPoint(e.clientX, e.clientY);
      const clickableElements = ['BUTTON', 'A', 'INPUT', 'SELECT', 'TEXTAREA'];
      const isClickable = element && (
        clickableElements.includes(element.tagName) ||
        element.closest('button') ||
        element.closest('a') ||
        element.getAttribute('role') === 'button' ||
        window.getComputedStyle(element).cursor === 'pointer'
      );
      
      setIsPointer(!!isClickable);
    };
    
    const handleMouseDown = () => {
      setIsClicking(true);
      playSound('click');
    };
    
    const handleMouseUp = () => {
      setIsClicking(false);
    };
    
    const handleMouseEnter = (e: MouseEvent) => {
      // Check if the cursor entered a clickable element
      const element = document.elementFromPoint(e.clientX, e.clientY);
      if (element && element.tagName === 'BUTTON' || element?.closest('button')) {
        playSound('hover');
      }
    };
    
    window.addEventListener('mousemove', moveCursor);
    window.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mouseup', handleMouseUp);
    document.querySelectorAll('button, a, [role="button"]').forEach(el => {
      el.addEventListener('mouseenter', handleMouseEnter as EventListener);
    });
    
    return () => {
      window.removeEventListener('mousemove', moveCursor);
      window.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mouseup', handleMouseUp);
      document.querySelectorAll('button, a, [role="button"]').forEach(el => {
        el.removeEventListener('mouseenter', handleMouseEnter as EventListener);
      });
    };
  }, [cursorX, cursorY, playSound]);

  return (
    <>
      {/* Custom Cursor */}
      <motion.div
        ref={cursorRef}
        className="fixed pointer-events-none z-50 mix-blend-screen"
        style={{
          x: springX,
          y: springY,
          height: isClicking ? 12 : 16,
          width: isClicking ? 12 : 16,
          borderRadius: '50%',
          backgroundColor: isPointer ? 'rgba(0, 209, 112, 0.7)' : 'rgba(10, 132, 255, 0.7)',
          transform: 'translate(-50%, -50%)',
          transition: 'height 0.1s, width 0.1s, background-color 0.3s'
        }}
      />
      
      {/* Glow Effect */}
      <motion.div
        ref={glowRef}
        className="fixed pointer-events-none z-40 mix-blend-screen blur-sm"
        style={{
          x: springX,
          y: springY,
          height: isClicking ? 24 : 40,
          width: isClicking ? 24 : 40,
          borderRadius: '50%',
          backgroundColor: isPointer ? 'rgba(0, 209, 112, 0.2)' : 'rgba(10, 132, 255, 0.2)',
          transform: 'translate(-50%, -50%)',
          transition: 'height 0.15s, width 0.15s, background-color 0.3s'
        }}
      />
      
      {/* Hide native cursor */}
      <style jsx global>{`
        body {
          cursor: none !important;
        }
      `}</style>
    </>
  );
};

export default GlowCursor;