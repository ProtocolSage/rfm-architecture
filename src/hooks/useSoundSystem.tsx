import React, { createContext, useContext, useEffect, useState } from 'react';
import { Howl } from 'howler';
import * as Tone from 'tone';

type SoundType = 
  | 'click' 
  | 'hover' 
  | 'success' 
  | 'error' 
  | 'nav' 
  | 'startup' 
  | 'notification'
  | 'data' 
  | 'complete';

interface SoundContextType {
  enabled: boolean;
  setEnabled: (enabled: boolean) => void;
  volume: number;
  setVolume: (volume: number) => void;
  playSound: (type: SoundType) => void;
  playSynth: (note: string | string[], duration?: string) => void;
}

const SoundContext = createContext<SoundContextType | undefined>(undefined);

// Preload sounds as base64 to avoid file loading issues
const SOUNDS = {
  click: new Howl({
    src: ['data:audio/mp3;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA/+NAwAAAAAAAAAAAAFhpbmcAAAAPAAAAAwAAA3YAlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlP/zQsRbAAADSAHwAAABQQSxHAAAgAAAD//QAf8bRsOLj/+e/fxCEefnXUh8WzVPP6f4UMBbIDgkRaYVYRiEwiJKh4JkArAAAIAAACyAKZYbAAgICAgIaG5HQXWnQbAT//NixGYeox5wAZpAAA4hGBQBAQDIyABQCgIIAAaBgYBFMhDQhiAEIOBCkRAQQgFZPiEgZCzIVA/Ag4CEoxhBguCQVBEIx6RAiCAZKR4AAFkzLSmzBIqAAiJP3VhTVs6ZZ4vLXBGXPrZd+1WVup11pqoiSZCZ8/n+zBfLBEFQEAAACCAKQxuYCAICAgICGhuSUF1p0P/zYsR+OxMGQAGYeADeEYFAEBAMjIAFAKAYAAEDBg4AmJDGQhATAFCDgQARIhIGQtMEgEB8CjoYIYLgw4JhEFQSAsMSABCAgZKR4AAEiFZlUGQTBQEQkk+4sKbNnrBmnPGXMZpWm//GgxXZm07ILX3pWVxcfpzWQQSw1kAEBAQEBIQ3JJndHC8EYBgMBgTFRWZiggKIYEAEwQAa0DYgfMEiCQWIJvQ2UW8BI4vAaTfwFRgDAHJuAnVu6Mw/hIVABHQRIZmUmDDG//NixG4jKf3AAfiYADwQ0BpmAnPgdECr1vQXiTgFnRcXJGQYJL+kCXiRNAdCw7YmrgL40IHBJaTCnIPBbsRiUHKY6B6iISiSQFk2yvUEFUGIgIZ4nrXRrqF6JiQrGKhQ9R6qy+aYnGW1DPTFONXpQe///J6lPQpREYSuCGAAAAKwJYwUJOMvZ9fSy9//WX/wl0SJEn/zYsRMDpmeUAHTeAC6JEkicRJGnixI00SSLHnTRYk4v///oImUAYAAoAAAAAABgwQAxY0ESAFxsxYQaFOiiYlAHPCM8EqVYwDT5Cw4UPThUwxYCAgGYQWCQUIgpMTIGWJAtMQPGHIwwOORUTrWjDPYaQ5JFKoX7iAZYsMDL9UPYzuiEL6vP7ijmgkiw5TKcgFUDQoxAkkXTmxhGEV3m3qlXoWUKPFKEr//NixH8iSmoqfnMHLk4fO0wS7bZbDxxUCX5XqHplVV/pGYxzHNc5jWMaiIiIjMzMzP/MREv6ImJEAAAAABFOMIXEwAZYhgDYYAgGGAFAKAwIpBQCDRAiF0HDKVgPwMMEU1TCGwAoBRQMDAicDHgECBSEMmVhkUTuZKgKCkYs5Qc8tG4I0JfADQzJwD1mYI/iQsGIKRnEJ//zYsR9IusGXAGaeAGZrHdY7rmqysmtda89NVpuIJgAAiSCBgAACrw4LwQPAYEGI7D4/u7u4f/cWBgdjsOC8EQTGQ6A4f/+wCOiwAARJ8JQpN5+7YcbqtX/8tXfTVXuvIiIXKwgfmIiJiLHcnb2uu7iWl1X+nF4MRYwRCIiIiIiIiJmZmZmZlVVVQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='],
    volume: 0.5,
    preload: true
  }),
  hover: new Howl({
    src: ['data:audio/mp3;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA/+NAwAAAAAAAAAAAAFhpbmcAAAAPAAAAAgAAAiIAlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlP//////////////////////////////////////////'],
    volume: 0.2,
    preload: true
  }),
  success: new Howl({
    src: ['data:audio/mp3;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA/+NAwAAAAAAAAAAAAFhpbmcAAAAPAAAAAwAABDgAgoKCgoKCgoKCgoKSkpKSkpKSkpKSmpqampqampqamqKioqKioqKioqKzs7Ozs7Ozs7Oz//////////////////////////8AAAAATGF2YzU4LjEzAAAAAAAAAAAAAAAAJAX/////'],
    volume: 0.7,
    preload: true
  }),
  error: new Howl({
    src: ['data:audio/mp3;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA/+NAwAAAAAAAAAAAAFhpbmcAAAAPAAAABAAABVcAREREbW1tdZGRkZGRkbC3t7e3t7fa2tra2tr1FRUVFRUVNTU1NTU1WFhYWFhYdpaWlpaWlpeXl7Ozs7Ozs8PDw+Li4uLi4vb29vb29v//////////////////////////'],
    volume: 0.7,
    preload: true
  }),
  nav: new Howl({
    src: ['data:audio/mp3;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA/+NAwAAAAAAAAAAAAFhpbmcAAAAPAAAAAgAAAjIAlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlP//////////////////////////////////////////'],
    volume: 0.5,
    preload: true
  }),
  startup: new Howl({
    src: ['data:audio/mp3;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA/+NAwAAAAAAAAAAAAFhpbmcAAAAPAAAABQAAA+MATExMTExMTGRkZGRkZGR/f39/f39/f39/n5+fn5+fn5+fv7+/v7+/v7+/3Nzc3Nzc3Nzc3Pv7+/v7+/v7+///////////////////'],
    volume: 0.8,
    preload: true
  }),
  notification: new Howl({
    src: ['data:audio/mp3;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA/+NAwAAAAAAAAAAAAFhpbmcAAAAPAAAABAAABCAAWlpaWlpaWmZmZmZmZmaKioqKioqKioqKuLi4uLi4uLi4uOXl5eXl5eXl5eX////////////////////////////////////////'],
    volume: 0.6,
    preload: true
  }),
  data: new Howl({
    src: ['data:audio/mp3;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA/+NAwAAAAAAAAAAAAFhpbmcAAAAPAAAABgAACKQATk5OTk5OTk5OTl1dXV1dXV1dXV1ubm5ubm5ubm5ufX19fX19fX19fY6Ojo6Ojo6Ojo6enp6enp6enp6er6+vr6+vr6+vr7+/v7+/v7+/v7/P'],
    volume: 0.4,
    preload: true
  }),
  complete: new Howl({
    src: ['data:audio/mp3;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA/+NAwAAAAAAAAAAAAFhpbmcAAAAPAAAABwAACSAAMTExMTExMTExMUBAQEBAQEBAQEBOTk5OTk5OTk5OXV1dXV1dXV1dXWxsbGxsbGxsbGyBgYGBgYGBgYGBlpaWlpaWlpaWlqSkpKSkpKSkpKS5'],
    volume: 0.7,
    preload: true
  })
};

// Initialize Tone.js synth for more complex sounds
const synth = new Tone.PolySynth(Tone.Synth).toDestination();
synth.volume.value = -15; // Lower the volume a bit

export const SoundProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [enabled, setEnabled] = useState(true);
  const [volume, setVolume] = useState(0.7);
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    // Load settings from localStorage
    const storedEnabled = localStorage.getItem('sound-enabled');
    const storedVolume = localStorage.getItem('sound-volume');
    
    if (storedEnabled !== null) {
      setEnabled(storedEnabled === 'true');
    }
    
    if (storedVolume !== null) {
      setVolume(parseFloat(storedVolume));
    }

    setInitialized(true);
  }, []);

  useEffect(() => {
    if (initialized) {
      localStorage.setItem('sound-enabled', String(enabled));
      localStorage.setItem('sound-volume', String(volume));
      
      // Update volume for all sounds
      Object.values(SOUNDS).forEach(sound => {
        sound.volume(enabled ? volume : 0);
      });
      
      // Update synth volume
      synth.volume.value = enabled ? -15 + (volume * 20) : -100;
    }
  }, [enabled, volume, initialized]);

  const playSound = (type: SoundType) => {
    if (!enabled) return;
    
    const sound = SOUNDS[type];
    if (sound) {
      sound.play();
    }
  };

  const playSynth = (note: string | string[], duration: string = '16n') => {
    if (!enabled) return;
    
    // Start Tone.js context if it's not started yet
    if (Tone.context.state !== 'running') {
      Tone.start();
    }
    
    synth.triggerAttackRelease(note, duration);
  };

  const contextValue: SoundContextType = {
    enabled,
    setEnabled,
    volume,
    setVolume,
    playSound,
    playSynth
  };

  return (
    <SoundContext.Provider value={contextValue}>
      {children}
    </SoundContext.Provider>
  );
};

export const useSoundSystem = () => {
  const context = useContext(SoundContext);
  if (context === undefined) {
    throw new Error('useSoundSystem must be used within a SoundProvider');
  }
  return context;
};