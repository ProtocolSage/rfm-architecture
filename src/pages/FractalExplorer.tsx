import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import Card from '../components/ui/Card';
import { useSoundSystem } from '../hooks/useSoundSystem';

// Shader for Mandelbrot fractal
const fragmentShader = `
  precision highp float;
  
  uniform vec2 resolution;
  uniform float time;
  uniform vec2 center;
  uniform float zoom;
  uniform vec3 colorA;
  uniform vec3 colorB;
  uniform int maxIterations;
  
  vec3 hsb2rgb(vec3 c) {
    vec3 rgb = clamp(abs(mod(c.x*6.0+vec3(0.0,4.0,2.0), 6.0)-3.0)-1.0, 0.0, 1.0);
    rgb = rgb*rgb*(3.0-2.0*rgb);
    return c.z * mix(vec3(1.0), rgb, c.y);
  }
  
  void main() {
    vec2 uv = gl_FragCoord.xy / resolution.xy;
    vec2 c = center + (uv - 0.5) * vec2(3.0, 3.0) / zoom;
    
    vec2 z = vec2(0.0);
    float iteration = 0.0;
    
    for (int i = 0; i < 1000; i++) {
      if (i >= maxIterations) break;
      
      z = vec2(
        z.x * z.x - z.y * z.y,
        2.0 * z.x * z.y
      ) + c;
      
      if (dot(z, z) > 4.0) break;
      iteration += 1.0;
    }
    
    if (iteration >= float(maxIterations)) {
      gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
    } else {
      float smoothed = iteration + 1.0 - log(log(dot(z, z))) / log(2.0);
      float normalized = smoothed / float(maxIterations);
      
      float hue = 0.7 + 0.2 * sin(normalized * 8.0 + time * 0.25);
      float saturation = 0.8;
      float brightness = normalized < 0.1 ? 4.0 * normalized : 0.4 + 0.6 * normalized;
      
      vec3 hsb = vec3(hue, saturation, brightness);
      vec3 rgb = hsb2rgb(hsb);
      
      gl_FragColor = vec4(mix(colorA, mix(rgb, colorB, normalized), 0.7), 1.0);
    }
  }
`;

// React Three Fiber component for rendering fractal
const FractalPlane: React.FC<{
  center: [number, number];
  zoom: number;
  maxIterations: number;
  colorA: [number, number, number];
  colorB: [number, number, number];
  isAnimated: boolean;
  playSynth: (note: string | string[]) => void;
}> = ({ center, zoom, maxIterations, colorA, colorB, isAnimated, playSynth }) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const { viewport } = useThree();
  const uniforms = useRef({
    resolution: { value: new THREE.Vector2(window.innerWidth, window.innerHeight) },
    time: { value: 0.0 },
    center: { value: new THREE.Vector2(...center) },
    zoom: { value: zoom },
    colorA: { value: new THREE.Vector3(...colorA) },
    colorB: { value: new THREE.Vector3(...colorB) },
    maxIterations: { value: maxIterations }
  });
  
  useEffect(() => {
    if (meshRef.current) {
      const material = meshRef.current.material as THREE.ShaderMaterial;
      material.uniforms.center.value = new THREE.Vector2(...center);
      material.uniforms.zoom.value = zoom;
      material.uniforms.maxIterations.value = maxIterations;
      material.uniforms.colorA.value = new THREE.Vector3(...colorA);
      material.uniforms.colorB.value = new THREE.Vector3(...colorB);
      
      // Play a note when parameters change
      const notes = ['C4', 'E4', 'G4', 'B4'];
      const noteIndex = Math.floor(Math.random() * notes.length);
      playSynth(notes[noteIndex]);
    }
  }, [center, zoom, maxIterations, colorA, colorB, playSynth]);
  
  useFrame((state) => {
    if (meshRef.current && isAnimated) {
      const material = meshRef.current.material as THREE.ShaderMaterial;
      material.uniforms.time.value = state.clock.getElapsedTime();
    }
  });
  
  return (
    <mesh ref={meshRef} scale={[viewport.width, viewport.height, 1]}>
      <planeGeometry args={[1, 1]} />
      <shaderMaterial
        fragmentShader={fragmentShader}
        uniforms={uniforms.current}
        vertexShader={`
          void main() {
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
          }
        `}
      />
    </mesh>
  );
};

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

const FractalExplorer: React.FC = () => {
  const { playSound, playSynth } = useSoundSystem();
  const [settings, setSettings] = useState({
    center: [-0.5, 0] as [number, number],
    zoom: 1,
    maxIterations: 100,
    colorA: [0.1, 0.4, 0.9] as [number, number, number],
    colorB: [0.9, 0.1, 0.4] as [number, number, number],
    isAnimated: true
  });
  
  const [presets, setPresets] = useState([
    { 
      name: 'Default View', 
      center: [-0.5, 0], 
      zoom: 1,
      maxIterations: 100 
    },
    { 
      name: 'Mini Mandelbrot', 
      center: [-0.745, 0.186], 
      zoom: 15,
      maxIterations: 300 
    },
    { 
      name: 'Spiral Pattern', 
      center: [-0.761574, -0.0847596], 
      zoom: 80,
      maxIterations: 500 
    }
  ]);
  
  const handleZoomChange = (value: number) => {
    setSettings({ ...settings, zoom: value });
  };
  
  const handleIterationsChange = (value: number) => {
    setSettings({ ...settings, maxIterations: value });
  };
  
  const handlePresetSelect = (preset: typeof presets[0]) => {
    setSettings({
      ...settings,
      center: preset.center,
      zoom: preset.zoom,
      maxIterations: preset.maxIterations
    });
    playSound('success');
  };
  
  const toggleAnimation = () => {
    setSettings({ ...settings, isAnimated: !settings.isAnimated });
    playSound('click');
  };
  
  const handleColorChange = (type: 'A' | 'B', colorIndex: number, value: number) => {
    if (type === 'A') {
      const newColorA = [...settings.colorA] as [number, number, number];
      newColorA[colorIndex] = value;
      setSettings({ ...settings, colorA: newColorA });
    } else {
      const newColorB = [...settings.colorB] as [number, number, number];
      newColorB[colorIndex] = value;
      setSettings({ ...settings, colorB: newColorB });
    }
  };
  
  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-8 h-full"
    >
      <div className="flex flex-col lg:flex-row gap-8 h-full">
        {/* Fractal Viewer */}
        <div className="lg:w-2/3 h-[600px] relative">
          <Card
            variant="dark"
            glowEffect="intense"
            className="overflow-hidden h-full w-full"
          >
            <Canvas>
              <FractalPlane 
                center={settings.center}
                zoom={settings.zoom}
                maxIterations={settings.maxIterations}
                colorA={settings.colorA}
                colorB={settings.colorB}
                isAnimated={settings.isAnimated}
                playSynth={playSynth}
              />
              <OrbitControls enabled={false} />
            </Canvas>
            
            {/* Overlay Info */}
            <div className="absolute bottom-4 left-4 glass-panel px-3 py-2 text-xs text-white/70">
              <div>Center: [{settings.center[0].toFixed(6)}, {settings.center[1].toFixed(6)}]</div>
              <div>Zoom: {settings.zoom.toFixed(2)}x</div>
              <div>Iterations: {settings.maxIterations}</div>
            </div>
            
            {/* Animation Toggle */}
            <button
              className={`absolute top-4 right-4 glass-panel px-3 py-2 text-xs flex items-center space-x-2 transition-colors ${
                settings.isAnimated ? 'bg-secondary/20 text-secondary' : 'text-white/70'
              }`}
              onClick={toggleAnimation}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={settings.isAnimated ? "M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" : "M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"} />
              </svg>
              <span>{settings.isAnimated ? 'Animation On' : 'Animation Off'}</span>
            </button>
          </Card>
        </div>
        
        {/* Controls Panel */}
        <div className="lg:w-1/3">
          <Card variant="default" glowEffect="subtle" className="h-full">
            <div className="p-6 h-full flex flex-col">
              <h2 className="text-xl font-medium mb-6 flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-primary" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                </svg>
                Fractal Parameters
              </h2>
              
              {/* Zoom Control */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-white/80 mb-2">
                  Zoom Level: {settings.zoom.toFixed(2)}x
                </label>
                <input
                  type="range"
                  min="0.5"
                  max="100"
                  step="0.5"
                  value={settings.zoom}
                  onChange={(e) => handleZoomChange(parseFloat(e.target.value))}
                  className="w-full h-2 rounded-full appearance-none bg-glass-strong"
                  style={{
                    backgroundImage: `linear-gradient(to right, #0a84ff, #0a84ff ${(settings.zoom - 0.5) / 99.5 * 100}%, rgba(255, 255, 255, 0.1) ${(settings.zoom - 0.5) / 99.5 * 100}%)`,
                  }}
                />
              </div>
              
              {/* Iterations Control */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-white/80 mb-2">
                  Max Iterations: {settings.maxIterations}
                </label>
                <input
                  type="range"
                  min="50"
                  max="1000"
                  step="10"
                  value={settings.maxIterations}
                  onChange={(e) => handleIterationsChange(parseInt(e.target.value))}
                  className="w-full h-2 rounded-full appearance-none bg-glass-strong"
                  style={{
                    backgroundImage: `linear-gradient(to right, #00d170, #00d170 ${(settings.maxIterations - 50) / 950 * 100}%, rgba(255, 255, 255, 0.1) ${(settings.maxIterations - 50) / 950 * 100}%)`,
                  }}
                />
              </div>
              
              {/* Color Controls */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-white/80 mb-2">
                  Color Palette
                </label>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-white/60 mb-2">Primary Color</p>
                    <div className="glass-panel p-3 rounded-lg space-y-3">
                      {['R', 'G', 'B'].map((channel, index) => (
                        <div key={`colorA-${channel}`} className="flex items-center">
                          <span className="text-xs w-6">{channel}</span>
                          <input
                            type="range"
                            min="0"
                            max="1"
                            step="0.01"
                            value={settings.colorA[index]}
                            onChange={(e) => handleColorChange('A', index, parseFloat(e.target.value))}
                            className="flex-1 h-1 rounded-full appearance-none bg-glass-strong mx-2"
                            style={{
                              backgroundImage: `linear-gradient(to right, ${channel === 'R' ? '#ff2d55' : channel === 'G' ? '#00d170' : '#0a84ff'}, ${channel === 'R' ? '#ff2d55' : channel === 'G' ? '#00d170' : '#0a84ff'} ${settings.colorA[index] * 100}%, rgba(255, 255, 255, 0.1) ${settings.colorA[index] * 100}%)`,
                            }}
                          />
                          <span className="text-xs w-8 text-right">{settings.colorA[index].toFixed(2)}</span>
                        </div>
                      ))}
                      <div 
                        className="h-6 w-full rounded-md mt-2" 
                        style={{
                          background: `rgb(${settings.colorA[0] * 255}, ${settings.colorA[1] * 255}, ${settings.colorA[2] * 255})`
                        }}
                      />
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-white/60 mb-2">Secondary Color</p>
                    <div className="glass-panel p-3 rounded-lg space-y-3">
                      {['R', 'G', 'B'].map((channel, index) => (
                        <div key={`colorB-${channel}`} className="flex items-center">
                          <span className="text-xs w-6">{channel}</span>
                          <input
                            type="range"
                            min="0"
                            max="1"
                            step="0.01"
                            value={settings.colorB[index]}
                            onChange={(e) => handleColorChange('B', index, parseFloat(e.target.value))}
                            className="flex-1 h-1 rounded-full appearance-none bg-glass-strong mx-2"
                            style={{
                              backgroundImage: `linear-gradient(to right, ${channel === 'R' ? '#ff2d55' : channel === 'G' ? '#00d170' : '#0a84ff'}, ${channel === 'R' ? '#ff2d55' : channel === 'G' ? '#00d170' : '#0a84ff'} ${settings.colorB[index] * 100}%, rgba(255, 255, 255, 0.1) ${settings.colorB[index] * 100}%)`,
                            }}
                          />
                          <span className="text-xs w-8 text-right">{settings.colorB[index].toFixed(2)}</span>
                        </div>
                      ))}
                      <div 
                        className="h-6 w-full rounded-md mt-2" 
                        style={{
                          background: `rgb(${settings.colorB[0] * 255}, ${settings.colorB[1] * 255}, ${settings.colorB[2] * 255})`
                        }}
                      />
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Presets */}
              <div className="mt-auto">
                <h3 className="text-sm font-medium text-white/80 mb-3">Presets</h3>
                <div className="grid grid-cols-3 gap-3">
                  {presets.map((preset, index) => (
                    <button
                      key={index}
                      className="glass-panel p-3 rounded-lg text-center hover:bg-glass-strong transition-all text-xs hover:shadow-neon-primary"
                      onClick={() => handlePresetSelect(preset)}
                      onMouseEnter={() => playSound('hover')}
                    >
                      {preset.name}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </motion.div>
  );
};

export default FractalExplorer;