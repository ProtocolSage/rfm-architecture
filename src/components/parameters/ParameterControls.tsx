import React, { useState, useEffect } from 'react';
import { EmotionalState, VisualizationParameters } from '../../types/parameters';

interface ParameterControlsProps {
  parameters: VisualizationParameters;
  onParametersChange: (parameters: VisualizationParameters) => void;
  presetOptions?: string[];
  onSavePreset?: (name: string, parameters: VisualizationParameters) => void;
  onLoadPreset?: (name: string) => void;
}

const ParameterControls: React.FC<ParameterControlsProps> = ({
  parameters,
  onParametersChange,
  presetOptions = [],
  onSavePreset,
  onLoadPreset
}) => {
  const [emotionalState, setEmotionalState] = useState<EmotionalState>(parameters.emotionalState);
  const [visualizationQuality, setVisualizationQuality] = useState<string>(parameters.quality);
  const [particleDensity, setParticleDensity] = useState<number>(parameters.particleDensity);
  const [energyLevel, setEnergyLevel] = useState<number>(parameters.energyLevel);
  const [animationSpeed, setAnimationSpeed] = useState<number>(parameters.animationSpeed);
  const [presetName, setPresetName] = useState<string>('');
  const [selectedPreset, setSelectedPreset] = useState<string>('');
  const [showSaveDialog, setShowSaveDialog] = useState<boolean>(false);

  // Update local state when parameters prop changes
  useEffect(() => {
    setEmotionalState(parameters.emotionalState);
    setVisualizationQuality(parameters.quality);
    setParticleDensity(parameters.particleDensity);
    setEnergyLevel(parameters.energyLevel);
    setAnimationSpeed(parameters.animationSpeed);
  }, [parameters]);

  // Handle emotional state changes
  const handleEmotionalStateChange = (property: keyof EmotionalState, value: number) => {
    const updatedEmotionalState = {
      ...emotionalState,
      [property]: value
    };
    setEmotionalState(updatedEmotionalState);
    
    // Update parent component
    onParametersChange({
      ...parameters,
      emotionalState: updatedEmotionalState
    });
  };

  // Handle quality change
  const handleQualityChange = (quality: string) => {
    setVisualizationQuality(quality);
    onParametersChange({
      ...parameters,
      quality
    });
  };

  // Handle particle density change
  const handleParticleDensityChange = (density: number) => {
    setParticleDensity(density);
    onParametersChange({
      ...parameters,
      particleDensity: density
    });
  };

  // Handle energy level change
  const handleEnergyLevelChange = (level: number) => {
    setEnergyLevel(level);
    onParametersChange({
      ...parameters,
      energyLevel: level
    });
  };

  // Handle animation speed change
  const handleAnimationSpeedChange = (speed: number) => {
    setAnimationSpeed(speed);
    onParametersChange({
      ...parameters,
      animationSpeed: speed
    });
  };

  // Handle save preset
  const handleSavePreset = () => {
    if (presetName && onSavePreset) {
      onSavePreset(presetName, parameters);
      setPresetName('');
      setShowSaveDialog(false);
    }
  };

  // Handle load preset
  const handleLoadPreset = () => {
    if (selectedPreset && onLoadPreset) {
      onLoadPreset(selectedPreset);
    }
  };

  // Quality options
  const qualityOptions = [
    { value: 'low', label: 'Low' },
    { value: 'medium', label: 'Medium' },
    { value: 'high', label: 'High' },
    { value: 'ultra', label: 'Ultra' }
  ];

  // Neon styles
  const neonBorderStyle = 'border border-cyan-500/30 focus:ring-cyan-500 focus:border-cyan-500';
  const neonTextStyle = 'text-cyan-300';
  const neonBgStyle = 'bg-gray-900';
  const neonFocusRing = 'focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 focus:ring-cyan-500';

  return (
    <div className="space-y-6">
      <h2 className={`text-2xl font-semibold ${neonTextStyle}`} style={{ textShadow: '0 0 3px #06b6d4' }}>
        Parameter Controls
      </h2>
      
      {/* Emotional State Controls */}
      <div className="space-y-4 border border-cyan-500/20 rounded p-4">
        <h3 className={`text-lg font-medium ${neonTextStyle}`}>Emotional State</h3>
        
        <div className="space-y-3">
          {/* Arousal Slider */}
          <div>
            <label htmlFor="arousal" className={`flex justify-between text-sm ${neonTextStyle}`}>
              <span>Arousal</span>
              <span>{emotionalState.arousal.toFixed(2)}</span>
            </label>
            <input
              type="range"
              id="arousal"
              min="-1"
              max="1"
              step="0.01"
              value={emotionalState.arousal}
              onChange={(e) => handleEmotionalStateChange('arousal', parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer range-cyan"
            />
            <div className="flex justify-between text-xs text-gray-400">
              <span>Calm</span>
              <span>Excited</span>
            </div>
          </div>
          
          {/* Valence Slider */}
          <div>
            <label htmlFor="valence" className={`flex justify-between text-sm ${neonTextStyle}`}>
              <span>Valence</span>
              <span>{emotionalState.valence.toFixed(2)}</span>
            </label>
            <input
              type="range"
              id="valence"
              min="-1"
              max="1"
              step="0.01"
              value={emotionalState.valence}
              onChange={(e) => handleEmotionalStateChange('valence', parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer range-cyan"
            />
            <div className="flex justify-between text-xs text-gray-400">
              <span>Negative</span>
              <span>Positive</span>
            </div>
          </div>
          
          {/* Dominance Slider */}
          <div>
            <label htmlFor="dominance" className={`flex justify-between text-sm ${neonTextStyle}`}>
              <span>Dominance</span>
              <span>{emotionalState.dominance.toFixed(2)}</span>
            </label>
            <input
              type="range"
              id="dominance"
              min="-1"
              max="1"
              step="0.01"
              value={emotionalState.dominance}
              onChange={(e) => handleEmotionalStateChange('dominance', parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer range-cyan"
            />
            <div className="flex justify-between text-xs text-gray-400">
              <span>Submissive</span>
              <span>Dominant</span>
            </div>
          </div>
          
          {/* Certainty Slider */}
          <div>
            <label htmlFor="certainty" className={`flex justify-between text-sm ${neonTextStyle}`}>
              <span>Certainty</span>
              <span>{emotionalState.certainty.toFixed(2)}</span>
            </label>
            <input
              type="range"
              id="certainty"
              min="0"
              max="1"
              step="0.01"
              value={emotionalState.certainty}
              onChange={(e) => handleEmotionalStateChange('certainty', parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer range-cyan"
            />
            <div className="flex justify-between text-xs text-gray-400">
              <span>Uncertain</span>
              <span>Certain</span>
            </div>
          </div>
        </div>
        
        {/* Emotion Presets */}
        <div className="grid grid-cols-3 gap-2 pt-2">
          <button
            onClick={() => {
              const joyState: EmotionalState = { arousal: 0.5, valence: 0.8, dominance: 0.6, certainty: 0.7 };
              setEmotionalState(joyState);
              onParametersChange({ ...parameters, emotionalState: joyState });
            }}
            className="py-1 px-2 text-xs rounded bg-cyan-700/30 hover:bg-cyan-700/50 text-cyan-300 transition-colors"
          >
            Joy
          </button>
          <button
            onClick={() => {
              const fearState: EmotionalState = { arousal: 0.9, valence: -0.7, dominance: -0.6, certainty: 0.3 };
              setEmotionalState(fearState);
              onParametersChange({ ...parameters, emotionalState: fearState });
            }}
            className="py-1 px-2 text-xs rounded bg-cyan-700/30 hover:bg-cyan-700/50 text-cyan-300 transition-colors"
          >
            Fear
          </button>
          <button
            onClick={() => {
              const angerState: EmotionalState = { arousal: 0.8, valence: -0.6, dominance: 0.7, certainty: 0.6 };
              setEmotionalState(angerState);
              onParametersChange({ ...parameters, emotionalState: angerState });
            }}
            className="py-1 px-2 text-xs rounded bg-cyan-700/30 hover:bg-cyan-700/50 text-cyan-300 transition-colors"
          >
            Anger
          </button>
          <button
            onClick={() => {
              const sadnessState: EmotionalState = { arousal: -0.5, valence: -0.7, dominance: -0.4, certainty: 0.5 };
              setEmotionalState(sadnessState);
              onParametersChange({ ...parameters, emotionalState: sadnessState });
            }}
            className="py-1 px-2 text-xs rounded bg-cyan-700/30 hover:bg-cyan-700/50 text-cyan-300 transition-colors"
          >
            Sadness
          </button>
          <button
            onClick={() => {
              const surpriseState: EmotionalState = { arousal: 0.8, valence: 0.2, dominance: 0.1, certainty: 0.1 };
              setEmotionalState(surpriseState);
              onParametersChange({ ...parameters, emotionalState: surpriseState });
            }}
            className="py-1 px-2 text-xs rounded bg-cyan-700/30 hover:bg-cyan-700/50 text-cyan-300 transition-colors"
          >
            Surprise
          </button>
          <button
            onClick={() => {
              const neutralState: EmotionalState = { arousal: 0, valence: 0, dominance: 0, certainty: 0.5 };
              setEmotionalState(neutralState);
              onParametersChange({ ...parameters, emotionalState: neutralState });
            }}
            className="py-1 px-2 text-xs rounded bg-cyan-700/30 hover:bg-cyan-700/50 text-cyan-300 transition-colors"
          >
            Neutral
          </button>
        </div>
      </div>
      
      {/* Visualization Parameters */}
      <div className="space-y-4 border border-cyan-500/20 rounded p-4">
        <h3 className={`text-lg font-medium ${neonTextStyle}`}>Visualization Settings</h3>
        
        <div className="space-y-3">
          {/* Quality Selection */}
          <div>
            <label htmlFor="quality" className={`block text-sm ${neonTextStyle} mb-1`}>
              Quality
            </label>
            <select
              id="quality"
              value={visualizationQuality}
              onChange={(e) => handleQualityChange(e.target.value)}
              className={`mt-1 block w-full pl-3 pr-10 py-2 text-base ${neonBorderStyle} ${neonBgStyle} text-gray-100 focus:outline-none sm:text-sm rounded-md ${neonFocusRing}`}
            >
              {qualityOptions.map(option => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>
          
          {/* Particle Density */}
          <div>
            <label htmlFor="particleDensity" className={`flex justify-between text-sm ${neonTextStyle}`}>
              <span>Particle Density</span>
              <span>{particleDensity.toFixed(1)}</span>
            </label>
            <input
              type="range"
              id="particleDensity"
              min="0.1"
              max="10"
              step="0.1"
              value={particleDensity}
              onChange={(e) => handleParticleDensityChange(parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer range-cyan"
            />
            <div className="flex justify-between text-xs text-gray-400">
              <span>Sparse</span>
              <span>Dense</span>
            </div>
          </div>
          
          {/* Energy Level */}
          <div>
            <label htmlFor="energyLevel" className={`flex justify-between text-sm ${neonTextStyle}`}>
              <span>Energy Level</span>
              <span>{energyLevel.toFixed(1)}</span>
            </label>
            <input
              type="range"
              id="energyLevel"
              min="0.1"
              max="10"
              step="0.1"
              value={energyLevel}
              onChange={(e) => handleEnergyLevelChange(parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer range-cyan"
            />
            <div className="flex justify-between text-xs text-gray-400">
              <span>Low</span>
              <span>High</span>
            </div>
          </div>
          
          {/* Animation Speed */}
          <div>
            <label htmlFor="animationSpeed" className={`flex justify-between text-sm ${neonTextStyle}`}>
              <span>Animation Speed</span>
              <span>{animationSpeed.toFixed(1)}x</span>
            </label>
            <input
              type="range"
              id="animationSpeed"
              min="0.1"
              max="5"
              step="0.1"
              value={animationSpeed}
              onChange={(e) => handleAnimationSpeedChange(parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer range-cyan"
            />
            <div className="flex justify-between text-xs text-gray-400">
              <span>Slow</span>
              <span>Fast</span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Preset Management */}
      {(onSavePreset || onLoadPreset) && (
        <div className="space-y-3 border border-cyan-500/20 rounded p-4">
          <h3 className={`text-lg font-medium ${neonTextStyle}`}>Presets</h3>
          
          <div className="flex space-x-2">
            {onLoadPreset && presetOptions.length > 0 && (
              <div className="flex-1">
                <select
                  value={selectedPreset}
                  onChange={(e) => setSelectedPreset(e.target.value)}
                  className={`block w-full pl-3 pr-10 py-2 text-sm ${neonBorderStyle} ${neonBgStyle} text-gray-100 focus:outline-none rounded-md ${neonFocusRing}`}
                >
                  <option value="">Select Preset</option>
                  {presetOptions.map(preset => (
                    <option key={preset} value={preset}>{preset}</option>
                  ))}
                </select>
              </div>
            )}
            
            {onLoadPreset && selectedPreset && (
              <button
                onClick={handleLoadPreset}
                className="py-2 px-4 text-sm rounded bg-cyan-600 hover:bg-cyan-700 text-white transition-colors"
              >
                Load
              </button>
            )}
            
            {onSavePreset && (
              <button
                onClick={() => setShowSaveDialog(true)}
                className="py-2 px-4 text-sm rounded bg-cyan-600 hover:bg-cyan-700 text-white transition-colors"
              >
                Save
              </button>
            )}
          </div>
          
          {/* Save Preset Dialog */}
          {showSaveDialog && (
            <div className="mt-3 p-3 border border-cyan-500/30 rounded bg-gray-800/50">
              <h4 className={`text-sm font-medium ${neonTextStyle} mb-2`}>Save Current Settings</h4>
              <input
                type="text"
                value={presetName}
                onChange={(e) => setPresetName(e.target.value)}
                placeholder="Preset name"
                className={`block w-full px-3 py-2 text-sm ${neonBorderStyle} ${neonBgStyle} text-gray-100 focus:outline-none rounded-md ${neonFocusRing} mb-2`}
              />
              <div className="flex space-x-2">
                <button
                  onClick={handleSavePreset}
                  disabled={!presetName}
                  className={`flex-1 py-1 px-3 text-sm rounded bg-cyan-600 hover:bg-cyan-700 text-white transition-colors ${!presetName ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  Save
                </button>
                <button
                  onClick={() => setShowSaveDialog(false)}
                  className="flex-1 py-1 px-3 text-sm rounded bg-gray-700 hover:bg-gray-600 text-white transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Current Parameter Summary */}
      <div className="bg-gray-800/30 rounded p-3 text-xs">
        <h4 className={`text-sm font-medium ${neonTextStyle} mb-2`}>Current Parameters</h4>
        <pre className="text-gray-300 overflow-x-auto">
          {JSON.stringify({
            emotionalState,
            quality: visualizationQuality,
            particleDensity,
            energyLevel,
            animationSpeed
          }, null, 2)}
        </pre>
      </div>
    </div>
  );
};

export default ParameterControls;