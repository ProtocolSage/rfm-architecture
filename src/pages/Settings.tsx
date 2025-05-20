import React, { useState } from 'react';
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

const Settings: React.FC = () => {
  const { playSound, enabled: soundEnabled, setEnabled: setSoundEnabled, volume, setVolume } = useSoundSystem();
  const [activeTab, setActiveTab] = useState<'general' | 'appearance' | 'performance' | 'account'>('general');
  
  // General settings
  const [generalSettings, setGeneralSettings] = useState({
    defaultFractalType: 'Mandelbrot',
    autoSave: true,
    defaultIterations: 100,
    saveFormat: 'JSON',
  });
  
  // Appearance settings
  const [appearanceSettings, setAppearanceSettings] = useState({
    theme: 'dark',
    accentColor: '#0a84ff',
    animationIntensity: 'medium',
    fontFamily: 'Inter',
    uiTransparency: 0.8,
  });
  
  // Performance settings
  const [performanceSettings, setPerformanceSettings] = useState({
    useGPUAcceleration: true,
    renderQuality: 'high',
    multithreading: true,
    cacheFractals: true,
    maxMemoryUsage: 2048,
  });
  
  const handleTabChange = (tab: 'general' | 'appearance' | 'performance' | 'account') => {
    setActiveTab(tab);
    playSound('click');
  };
  
  const handleGeneralSettingChange = (key: string, value: any) => {
    setGeneralSettings({
      ...generalSettings,
      [key]: value
    });
    playSound('data');
  };
  
  const handleAppearanceSettingChange = (key: string, value: any) => {
    setAppearanceSettings({
      ...appearanceSettings,
      [key]: value
    });
    playSound('data');
  };
  
  const handlePerformanceSettingChange = (key: string, value: any) => {
    setPerformanceSettings({
      ...performanceSettings,
      [key]: value
    });
    playSound('data');
  };
  
  const handleSoundToggle = () => {
    setSoundEnabled(!soundEnabled);
    if (soundEnabled) {
      // Play sound before disabling
      playSound('click');
    }
  };
  
  const handleVolumeChange = (newVolume: number) => {
    setVolume(newVolume);
  };
  
  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-8"
    >
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-display tracking-wide">
          Settings
        </h1>
        <button 
          className="glass-button hover:shadow-neon-primary transition-all duration-300"
          onClick={() => playSound('success')}
        >
          Save Changes
        </button>
      </div>
      
      <div className="flex flex-col lg:flex-row gap-8">
        {/* Tabs */}
        <div className="lg:w-1/4">
          <Card variant="dark" glowEffect="subtle">
            <div className="p-4 space-y-2">
              {[
                { id: 'general', label: 'General', icon: (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                  </svg>
                ) },
                { id: 'appearance', label: 'Appearance', icon: (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M4 2a2 2 0 00-2 2v11a3 3 0 106 0V4a2 2 0 00-2-2H4zm1 14a1 1 0 100-2 1 1 0 000 2zm5-1.757l4.9-4.9a2 2 0 000-2.828L13.485 5.1a2 2 0 00-2.828 0L10 5.757v8.486zM16 18H9.071l6-6H16a2 2 0 012 2v2a2 2 0 01-2 2z" />
                  </svg>
                ) },
                { id: 'performance', label: 'Performance', icon: (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
                  </svg>
                ) },
                { id: 'account', label: 'Account', icon: (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                  </svg>
                ) }
              ].map(tab => (
                <button
                  key={tab.id}
                  className={`w-full flex items-center p-3 rounded-lg text-left transition-all duration-300 ${
                    activeTab === tab.id 
                      ? 'bg-glass-strong text-white font-medium shadow-neon-glow' 
                      : 'text-white/70 hover:text-white hover:bg-glass'
                  }`}
                  onClick={() => handleTabChange(tab.id as any)}
                  onMouseEnter={() => playSound('hover')}
                >
                  <span className={`${activeTab === tab.id ? 'text-primary' : ''} mr-3`}>
                    {tab.icon}
                  </span>
                  {tab.label}
                </button>
              ))}
            </div>
          </Card>
        </div>
        
        {/* Settings Content */}
        <div className="lg:w-3/4">
          <Card variant="default" glowEffect="subtle">
            <div className="p-6">
              {/* General Settings */}
              {activeTab === 'general' && (
                <div className="space-y-6">
                  <h2 className="text-xl font-medium mb-6">General Settings</h2>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-white/80 mb-2">
                        Default Fractal Type
                      </label>
                      <select
                        className="w-full bg-glass rounded-md border border-glass-strong px-3 py-2 text-white"
                        value={generalSettings.defaultFractalType}
                        onChange={(e) => handleGeneralSettingChange('defaultFractalType', e.target.value)}
                        onFocus={() => playSound('hover')}
                      >
                        <option value="Mandelbrot">Mandelbrot</option>
                        <option value="Julia">Julia</option>
                        <option value="Burning Ship">Burning Ship</option>
                        <option value="Newton">Newton</option>
                        <option value="Lyapunov">Lyapunov</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-white/80 mb-2">
                        Default Iterations
                      </label>
                      <input
                        type="number"
                        className="w-full bg-glass rounded-md border border-glass-strong px-3 py-2 text-white"
                        value={generalSettings.defaultIterations}
                        onChange={(e) => handleGeneralSettingChange('defaultIterations', parseInt(e.target.value))}
                        onFocus={() => playSound('hover')}
                        min={10}
                        max={10000}
                      />
                      <p className="text-xs text-white/60 mt-1">
                        Higher values increase detail but require more processing power.
                      </p>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-white/80 mb-2">
                        Save Format
                      </label>
                      <select
                        className="w-full bg-glass rounded-md border border-glass-strong px-3 py-2 text-white"
                        value={generalSettings.saveFormat}
                        onChange={(e) => handleGeneralSettingChange('saveFormat', e.target.value)}
                        onFocus={() => playSound('hover')}
                      >
                        <option value="JSON">JSON</option>
                        <option value="YAML">YAML</option>
                        <option value="XML">XML</option>
                        <option value="Binary">Binary</option>
                      </select>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-sm font-medium text-white/80">Auto Save</h3>
                        <p className="text-xs text-white/60">
                          Automatically save changes to parameters
                        </p>
                      </div>
                      <div 
                        className={`relative w-11 h-6 transition-colors duration-300 ease-in-out rounded-full ${
                          generalSettings.autoSave ? 'bg-primary' : 'bg-glass-strong'
                        }`}
                        onClick={() => handleGeneralSettingChange('autoSave', !generalSettings.autoSave)}
                      >
                        <span 
                          className={`absolute left-0.5 top-0.5 bg-white w-5 h-5 rounded-full transition-transform duration-300 ease-in-out ${
                            generalSettings.autoSave ? 'translate-x-5' : ''
                          }`}
                        />
                      </div>
                    </div>
                    
                    <div className="pt-4 border-t border-glass-strong">
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <h3 className="text-sm font-medium text-white/80">Sound Effects</h3>
                          <p className="text-xs text-white/60">
                            Enable or disable interface sounds
                          </p>
                        </div>
                        <div 
                          className={`relative w-11 h-6 transition-colors duration-300 ease-in-out rounded-full ${
                            soundEnabled ? 'bg-secondary' : 'bg-glass-strong'
                          }`}
                          onClick={handleSoundToggle}
                        >
                          <span 
                            className={`absolute left-0.5 top-0.5 bg-white w-5 h-5 rounded-full transition-transform duration-300 ease-in-out ${
                              soundEnabled ? 'translate-x-5' : ''
                            }`}
                          />
                        </div>
                      </div>
                      
                      {soundEnabled && (
                        <div>
                          <label className="block text-sm font-medium text-white/80 mb-2">
                            Volume: {Math.round(volume * 100)}%
                          </label>
                          <input
                            type="range"
                            min="0"
                            max="1"
                            step="0.01"
                            value={volume}
                            onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
                            className="w-full h-2 rounded-full appearance-none bg-glass-strong"
                            style={{
                              backgroundImage: `linear-gradient(to right, #00d170, #00d170 ${volume * 100}%, rgba(255, 255, 255, 0.1) ${volume * 100}%)`,
                            }}
                          />
                          <div className="flex justify-between text-xs text-white/60 mt-1">
                            <span>Off</span>
                            <span>Max</span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
              
              {/* Appearance Settings */}
              {activeTab === 'appearance' && (
                <div className="space-y-6">
                  <h2 className="text-xl font-medium mb-6">Appearance Settings</h2>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-white/80 mb-2">
                        Theme
                      </label>
                      <div className="grid grid-cols-3 gap-4">
                        {['dark', 'light', 'system'].map(theme => (
                          <div
                            key={theme}
                            className={`p-3 rounded-lg text-center cursor-pointer transition-all duration-300 ${
                              appearanceSettings.theme === theme 
                                ? 'glass-panel shadow-neon-primary border-2 border-primary' 
                                : 'bg-glass-strong hover:bg-glass'
                            }`}
                            onClick={() => handleAppearanceSettingChange('theme', theme)}
                            onMouseEnter={() => playSound('hover')}
                          >
                            <div className="flex justify-center mb-2">
                              {theme === 'dark' && (
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                  <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
                                </svg>
                              )}
                              {theme === 'light' && (
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                  <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd" />
                                </svg>
                              )}
                              {theme === 'system' && (
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                  <path fillRule="evenodd" d="M3 5a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2h-2.22l.123.489.804.804A1 1 0 0113 18H7a1 1 0 01-.707-1.707l.804-.804L7.22 15H5a2 2 0 01-2-2V5zm5.771 7H5V5h10v7H8.771z" clipRule="evenodd" />
                                </svg>
                              )}
                            </div>
                            <span className="text-xs capitalize">{theme}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-white/80 mb-2">
                        Accent Color
                      </label>
                      <div className="grid grid-cols-6 gap-3">
                        {[
                          { name: 'Blue', value: '#0a84ff' },
                          { name: 'Green', value: '#00d170' },
                          { name: 'Purple', value: '#bf5af2' },
                          { name: 'Pink', value: '#ff2d55' },
                          { name: 'Orange', value: '#ff9f0a' },
                          { name: 'Teal', value: '#5ac8fa' },
                        ].map(color => (
                          <div
                            key={color.value}
                            className={`p-2 rounded-lg flex flex-col items-center cursor-pointer transition-all duration-300 ${
                              appearanceSettings.accentColor === color.value 
                                ? 'glass-panel shadow-neon-glow border border-white/30' 
                                : 'bg-glass-strong hover:bg-glass'
                            }`}
                            onClick={() => handleAppearanceSettingChange('accentColor', color.value)}
                            onMouseEnter={() => playSound('hover')}
                          >
                            <div 
                              className="w-6 h-6 rounded-full mb-1" 
                              style={{ backgroundColor: color.value }}
                            />
                            <span className="text-xs">{color.name}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-white/80 mb-2">
                        Animation Intensity
                      </label>
                      <select
                        className="w-full bg-glass rounded-md border border-glass-strong px-3 py-2 text-white"
                        value={appearanceSettings.animationIntensity}
                        onChange={(e) => handleAppearanceSettingChange('animationIntensity', e.target.value)}
                        onFocus={() => playSound('hover')}
                      >
                        <option value="none">None</option>
                        <option value="subtle">Subtle</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                      </select>
                      <p className="text-xs text-white/60 mt-1">
                        Controls the intensity of UI animations and transitions.
                      </p>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-white/80 mb-2">
                        Font Family
                      </label>
                      <select
                        className="w-full bg-glass rounded-md border border-glass-strong px-3 py-2 text-white"
                        value={appearanceSettings.fontFamily}
                        onChange={(e) => handleAppearanceSettingChange('fontFamily', e.target.value)}
                        onFocus={() => playSound('hover')}
                      >
                        <option value="Inter">Inter</option>
                        <option value="SF Pro">SF Pro</option>
                        <option value="Roboto">Roboto</option>
                        <option value="JetBrains Mono">JetBrains Mono</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-white/80 mb-2">
                        UI Transparency: {Math.round(appearanceSettings.uiTransparency * 100)}%
                      </label>
                      <input
                        type="range"
                        min="0.2"
                        max="1"
                        step="0.05"
                        value={appearanceSettings.uiTransparency}
                        onChange={(e) => handleAppearanceSettingChange('uiTransparency', parseFloat(e.target.value))}
                        className="w-full h-2 rounded-full appearance-none bg-glass-strong"
                        style={{
                          backgroundImage: `linear-gradient(to right, #bf5af2, #bf5af2 ${(appearanceSettings.uiTransparency - 0.2) / 0.8 * 100}%, rgba(255, 255, 255, 0.1) ${(appearanceSettings.uiTransparency - 0.2) / 0.8 * 100}%)`,
                        }}
                      />
                      <div className="flex justify-between text-xs text-white/60 mt-1">
                        <span>More Transparent</span>
                        <span>More Solid</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              {/* Performance Settings */}
              {activeTab === 'performance' && (
                <div className="space-y-6">
                  <h2 className="text-xl font-medium mb-6">Performance Settings</h2>
                  
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-sm font-medium text-white/80">GPU Acceleration</h3>
                        <p className="text-xs text-white/60">
                          Use your GPU for faster rendering
                        </p>
                      </div>
                      <div 
                        className={`relative w-11 h-6 transition-colors duration-300 ease-in-out rounded-full ${
                          performanceSettings.useGPUAcceleration ? 'bg-primary' : 'bg-glass-strong'
                        }`}
                        onClick={() => handlePerformanceSettingChange('useGPUAcceleration', !performanceSettings.useGPUAcceleration)}
                      >
                        <span 
                          className={`absolute left-0.5 top-0.5 bg-white w-5 h-5 rounded-full transition-transform duration-300 ease-in-out ${
                            performanceSettings.useGPUAcceleration ? 'translate-x-5' : ''
                          }`}
                        />
                      </div>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-white/80 mb-2">
                        Render Quality
                      </label>
                      <select
                        className="w-full bg-glass rounded-md border border-glass-strong px-3 py-2 text-white"
                        value={performanceSettings.renderQuality}
                        onChange={(e) => handlePerformanceSettingChange('renderQuality', e.target.value)}
                        onFocus={() => playSound('hover')}
                      >
                        <option value="low">Low (Faster)</option>
                        <option value="medium">Medium (Balanced)</option>
                        <option value="high">High (Better Quality)</option>
                        <option value="ultra">Ultra (Maximum Quality)</option>
                      </select>
                      <p className="text-xs text-white/60 mt-1">
                        Higher quality requires more computational resources.
                      </p>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-sm font-medium text-white/80">Multithreading</h3>
                        <p className="text-xs text-white/60">
                          Use multiple CPU cores for rendering
                        </p>
                      </div>
                      <div 
                        className={`relative w-11 h-6 transition-colors duration-300 ease-in-out rounded-full ${
                          performanceSettings.multithreading ? 'bg-secondary' : 'bg-glass-strong'
                        }`}
                        onClick={() => handlePerformanceSettingChange('multithreading', !performanceSettings.multithreading)}
                      >
                        <span 
                          className={`absolute left-0.5 top-0.5 bg-white w-5 h-5 rounded-full transition-transform duration-300 ease-in-out ${
                            performanceSettings.multithreading ? 'translate-x-5' : ''
                          }`}
                        />
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-sm font-medium text-white/80">Cache Fractals</h3>
                        <p className="text-xs text-white/60">
                          Store rendered fractals in memory for faster access
                        </p>
                      </div>
                      <div 
                        className={`relative w-11 h-6 transition-colors duration-300 ease-in-out rounded-full ${
                          performanceSettings.cacheFractals ? 'bg-accent-purple' : 'bg-glass-strong'
                        }`}
                        onClick={() => handlePerformanceSettingChange('cacheFractals', !performanceSettings.cacheFractals)}
                      >
                        <span 
                          className={`absolute left-0.5 top-0.5 bg-white w-5 h-5 rounded-full transition-transform duration-300 ease-in-out ${
                            performanceSettings.cacheFractals ? 'translate-x-5' : ''
                          }`}
                        />
                      </div>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-white/80 mb-2">
                        Maximum Memory Usage (MB): {performanceSettings.maxMemoryUsage}
                      </label>
                      <input
                        type="range"
                        min="512"
                        max="8192"
                        step="512"
                        value={performanceSettings.maxMemoryUsage}
                        onChange={(e) => handlePerformanceSettingChange('maxMemoryUsage', parseInt(e.target.value))}
                        className="w-full h-2 rounded-full appearance-none bg-glass-strong"
                        style={{
                          backgroundImage: `linear-gradient(to right, #ff9f0a, #ff9f0a ${(performanceSettings.maxMemoryUsage - 512) / 7680 * 100}%, rgba(255, 255, 255, 0.1) ${(performanceSettings.maxMemoryUsage - 512) / 7680 * 100}%)`,
                        }}
                      />
                      <div className="flex justify-between text-xs text-white/60 mt-1">
                        <span>512MB</span>
                        <span>8GB</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              {/* Account Settings */}
              {activeTab === 'account' && (
                <div className="space-y-6">
                  <h2 className="text-xl font-medium mb-6">Account Settings</h2>
                  
                  <div className="glass-panel p-5 flex items-center space-x-4 rounded-xl mb-6">
                    <div className="w-14 h-14 rounded-full overflow-hidden gradient-border">
                      <div className="w-full h-full flex items-center justify-center bg-glass-strong text-lg font-medium">
                        PS
                      </div>
                    </div>
                    <div>
                      <h3 className="text-lg font-medium">Protocol Sage</h3>
                      <p className="text-sm text-white/60">Enterprise License</p>
                    </div>
                    <button 
                      className="ml-auto p-2 rounded-md bg-glass hover:bg-glass-strong transition-colors"
                      onClick={() => playSound('click')}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white/70" viewBox="0 0 20 20" fill="currentColor">
                        <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
                      </svg>
                    </button>
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-white/80 mb-2">
                        Email
                      </label>
                      <input
                        type="email"
                        className="w-full bg-glass rounded-md border border-glass-strong px-3 py-2 text-white"
                        value="contact@protocolsage.com"
                        readOnly
                        onFocus={() => playSound('hover')}
                      />
                    </div>
                    
                    <div>
                      <button 
                        className="px-4 py-2 rounded-md glass-panel hover:bg-glass-strong text-white/80 hover:text-white transition-colors"
                        onClick={() => playSound('click')}
                      >
                        Change Password
                      </button>
                    </div>
                    
                    <div className="pt-4 border-t border-glass-strong">
                      <h3 className="text-sm font-medium text-white/80 mb-3">License Information</h3>
                      <div className="glass-panel p-4 rounded-lg">
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm">License Type:</span>
                          <span className="text-sm font-medium">Enterprise</span>
                        </div>
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm">Valid Until:</span>
                          <span className="text-sm font-medium text-accent-teal">May 20, 2026</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm">Features:</span>
                          <span className="text-sm font-medium">All Premium Features</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="pt-4">
                      <h3 className="text-sm font-medium text-white/80 mb-3">Danger Zone</h3>
                      <div className="glass-panel p-4 rounded-lg border border-accent-pink/30 bg-accent-pink/5">
                        <p className="text-sm text-white/80 mb-4">
                          Deleting your account will remove all your data and settings permanently.
                        </p>
                        <button 
                          className="px-4 py-2 rounded-md bg-accent-pink/20 text-accent-pink hover:bg-accent-pink/30 transition-colors"
                          onClick={() => playSound('error')}
                        >
                          Delete Account
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </motion.div>
  );
};

export default Settings;