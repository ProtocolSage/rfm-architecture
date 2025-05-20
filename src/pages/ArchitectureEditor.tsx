import React, { useState, useRef, useEffect } from 'react';
import { motion, useDragControls } from 'framer-motion';
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

// Node types
type NodeType = 'input' | 'process' | 'output' | 'data' | 'decision';

interface Node {
  id: string;
  type: NodeType;
  title: string;
  x: number;
  y: number;
  inputs: string[];
  outputs: string[];
  properties: Record<string, any>;
}

interface Connection {
  id: string;
  sourceId: string;
  targetId: string;
  sourceHandle: string;
  targetHandle: string;
}

const nodeTypeInfo = {
  input: {
    color: '#0a84ff',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M3 3a1 1 0 011-1h12a1 1 0 011 1v3a1 1 0 01-.293.707L12 11.414V15a1 1 0 01-.293.707l-2 2A1 1 0 018 17v-5.586L3.293 6.707A1 1 0 013 6V3z" clipRule="evenodd" />
      </svg>
    )
  },
  process: {
    color: '#00d170',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
      </svg>
    )
  },
  output: {
    color: '#bf5af2',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path d="M11 3a1 1 0 10-2 0v1a1 1 0 102 0V3zM15.657 5.757a1 1 0 00-1.414-1.414l-.707.707a1 1 0 001.414 1.414l.707-.707zM18 10a1 1 0 01-1 1h-1a1 1 0 110-2h1a1 1 0 011 1zM5.05 6.464A1 1 0 106.464 5.05l-.707-.707a1 1 0 00-1.414 1.414l.707.707zM5 10a1 1 0 01-1 1H3a1 1 0 110-2h1a1 1 0 011 1zM8 16v-1h4v1a2 2 0 11-4 0zM12 14c.015-.34.208-.646.477-.859a4 4 0 10-4.954 0c.27.213.462.519.476.859h4.002z" />
      </svg>
    )
  },
  data: {
    color: '#ff9f0a',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path d="M3 12v3c0 1.657 3.134 3 7 3s7-1.343 7-3v-3c0 1.657-3.134 3-7 3s-7-1.343-7-3z" />
        <path d="M3 7v3c0 1.657 3.134 3 7 3s7-1.343 7-3V7c0 1.657-3.134 3-7 3S3 8.657 3 7z" />
        <path d="M17 5c0 1.657-3.134 3-7 3S3 6.657 3 5s3.134-3 7-3 7 1.343 7 3z" />
      </svg>
    )
  },
  decision: {
    color: '#ff2d55',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
      </svg>
    )
  }
};

// Example architecture
const initialNodes: Node[] = [
  {
    id: 'input-1',
    type: 'input',
    title: 'User Input',
    x: 100,
    y: 150,
    inputs: [],
    outputs: ['data'],
    properties: {
      description: 'Handles user parameters and inputs'
    }
  },
  {
    id: 'process-1',
    type: 'process',
    title: 'Fractal Engine',
    x: 400,
    y: 150,
    inputs: ['params'],
    outputs: ['render', 'meta'],
    properties: {
      algorithm: 'Mandelbrot',
      iterations: 100
    }
  },
  {
    id: 'output-1',
    type: 'output',
    title: 'Visualization',
    x: 700,
    y: 100,
    inputs: ['image'],
    outputs: [],
    properties: {
      resolution: '1024x1024',
      colorMap: 'spectral'
    }
  },
  {
    id: 'data-1',
    type: 'data',
    title: 'Parameter Store',
    x: 250,
    y: 300,
    inputs: ['save'],
    outputs: ['load'],
    properties: {
      storage: 'local',
      format: 'JSON'
    }
  },
  {
    id: 'output-2',
    type: 'output',
    title: 'Analytics',
    x: 700,
    y: 300,
    inputs: ['data'],
    outputs: [],
    properties: {
      metrics: ['renderTime', 'complexity', 'memory']
    }
  }
];

const initialConnections: Connection[] = [
  {
    id: 'conn-1',
    sourceId: 'input-1',
    targetId: 'process-1',
    sourceHandle: 'data',
    targetHandle: 'params'
  },
  {
    id: 'conn-2',
    sourceId: 'process-1',
    targetId: 'output-1',
    sourceHandle: 'render',
    targetHandle: 'image'
  },
  {
    id: 'conn-3',
    sourceId: 'process-1',
    targetId: 'output-2',
    sourceHandle: 'meta',
    targetHandle: 'data'
  },
  {
    id: 'conn-4',
    sourceId: 'input-1',
    targetId: 'data-1',
    sourceHandle: 'data',
    targetHandle: 'save'
  },
  {
    id: 'conn-5',
    sourceId: 'data-1',
    targetId: 'process-1',
    sourceHandle: 'load',
    targetHandle: 'params'
  }
];

const ArchitectureEditor: React.FC = () => {
  const [nodes, setNodes] = useState<Node[]>(initialNodes);
  const [connections, setConnections] = useState<Connection[]>(initialConnections);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [connecting, setConnecting] = useState<{
    active: boolean;
    sourceId: string;
    sourceHandle: string;
    x: number;
    y: number;
  } | null>(null);
  const editorRef = useRef<HTMLDivElement>(null);
  const { playSound, playSynth } = useSoundSystem();
  
  // Calculate connection paths
  const getConnectionPath = (connection: Connection) => {
    const sourceNode = nodes.find(node => node.id === connection.sourceId);
    const targetNode = nodes.find(node => node.id === connection.targetId);
    
    if (!sourceNode || !targetNode) return '';
    
    // Source and target positions (center of the node)
    const sourceX = sourceNode.x + 150; // node width is 300px
    const sourceY = sourceNode.y + 60; // node height is 120px
    const targetX = targetNode.x;
    const targetY = targetNode.y + 60;
    
    // Control points for the curve
    const dx = Math.abs(targetX - sourceX) * 0.5;
    
    return `M ${sourceX} ${sourceY} C ${sourceX + dx} ${sourceY}, ${targetX - dx} ${targetY}, ${targetX} ${targetY}`;
  };
  
  // Handle node selection
  const handleNodeSelect = (nodeId: string) => {
    setSelectedNode(nodeId === selectedNode ? null : nodeId);
    playSound('click');
  };
  
  // Handle connection drag start
  const handleConnectionStart = (nodeId: string, handle: string, e: React.MouseEvent) => {
    if (editorRef.current) {
      const rect = editorRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      setConnecting({
        active: true,
        sourceId: nodeId,
        sourceHandle: handle,
        x,
        y
      });
      
      playSound('data');
    }
  };
  
  // Handle connection move
  const handleConnectionMove = (e: React.MouseEvent) => {
    if (connecting && editorRef.current) {
      const rect = editorRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      setConnecting({
        ...connecting,
        x,
        y
      });
    }
  };
  
  // Handle connection end
  const handleConnectionEnd = (nodeId: string, handle: string) => {
    if (connecting && connecting.sourceId !== nodeId) {
      // Create a new connection
      const newConnection: Connection = {
        id: `conn-${connections.length + 1}`,
        sourceId: connecting.sourceId,
        targetId: nodeId,
        sourceHandle: connecting.sourceHandle,
        targetHandle: handle
      };
      
      setConnections([...connections, newConnection]);
      playSynth(['C5', 'E5']);
    }
    
    setConnecting(null);
  };
  
  // Handle connection drop (when not over a node)
  const handleConnectionDrop = () => {
    if (connecting) {
      setConnecting(null);
      playSound('error');
    }
  };
  
  // Drag controls for nodes
  const dragControls = useDragControls();
  
  const handleDragStart = (e: React.PointerEvent, nodeId: string) => {
    dragControls.start(e);
    setSelectedNode(nodeId);
    playSound('hover');
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-8 h-full"
    >
      <div className="flex flex-col lg:flex-row gap-8 h-[calc(100vh-12rem)]">
        {/* Editor Canvas */}
        <div 
          ref={editorRef}
          className="lg:w-3/4 h-full relative glass-panel backdrop-blur-md rounded-xl overflow-hidden border border-glass-strong"
          onMouseMove={handleConnectionMove}
          onMouseUp={handleConnectionDrop}
        >
          {/* Grid background */}
          <div 
            className="absolute inset-0 pointer-events-none"
            style={{
              backgroundImage: `
                linear-gradient(to right, rgba(255,255,255,0.05) 1px, transparent 1px),
                linear-gradient(to bottom, rgba(255,255,255,0.05) 1px, transparent 1px)
              `,
              backgroundSize: '20px 20px'
            }}
          />
          
          {/* Connection lines */}
          <svg className="absolute inset-0 pointer-events-none">
            {connections.map(connection => (
              <path
                key={connection.id}
                d={getConnectionPath(connection)}
                stroke={
                  selectedNode === connection.sourceId || selectedNode === connection.targetId
                    ? '#ffffff'
                    : 'rgba(255, 255, 255, 0.4)'
                }
                strokeWidth={selectedNode === connection.sourceId || selectedNode === connection.targetId ? 3 : 2}
                fill="none"
                strokeDasharray={selectedNode === connection.sourceId || selectedNode === connection.targetId ? '0' : '5,5'}
              />
            ))}
            
            {/* Active connection line */}
            {connecting && (
              <path
                d={`M ${
                  nodes.find(node => node.id === connecting.sourceId)!.x + 150
                } ${
                  nodes.find(node => node.id === connecting.sourceId)!.y + 60
                } L ${connecting.x} ${connecting.y}`}
                stroke="#0a84ff"
                strokeWidth={3}
                fill="none"
                strokeDasharray="5,5"
              />
            )}
          </svg>
          
          {/* Nodes */}
          {nodes.map(node => (
            <motion.div
              key={node.id}
              className={`absolute w-[300px] glass-panel backdrop-blur-md border-2 rounded-xl overflow-hidden ${
                selectedNode === node.id 
                  ? 'shadow-neon-primary border-primary' 
                  : 'border-glass-strong'
              }`}
              style={{ left: node.x, top: node.y }}
              drag
              dragControls={dragControls}
              dragListener={false}
              dragMomentum={false}
              onDrag={(_, info) => {
                const newNodes = nodes.map(n => {
                  if (n.id === node.id) {
                    return {
                      ...n,
                      x: n.x + info.delta.x,
                      y: n.y + info.delta.y
                    };
                  }
                  return n;
                });
                setNodes(newNodes);
              }}
              onClick={() => handleNodeSelect(node.id)}
            >
              {/* Header */}
              <div 
                className="py-3 px-4 border-b border-glass-strong flex items-center justify-between cursor-move"
                onPointerDown={(e) => handleDragStart(e, node.id)}
                style={{ 
                  background: `linear-gradient(to right, ${nodeTypeInfo[node.type].color}20, transparent)` 
                }}
              >
                <div className="flex items-center">
                  <div 
                    className="w-8 h-8 rounded-full flex items-center justify-center mr-3"
                    style={{ backgroundColor: `${nodeTypeInfo[node.type].color}30` }}
                  >
                    <span style={{ color: nodeTypeInfo[node.type].color }}>
                      {nodeTypeInfo[node.type].icon}
                    </span>
                  </div>
                  <div>
                    <h3 className="font-medium">{node.title}</h3>
                    <p className="text-xs text-white/60">{node.type}</p>
                  </div>
                </div>
                <button 
                  className="w-7 h-7 rounded-md flex items-center justify-center bg-glass-strong hover:bg-glass text-white/60 hover:text-white transition-colors duration-200"
                  onClick={(e) => {
                    e.stopPropagation();
                    playSound('click');
                  }}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M6 10a2 2 0 11-4 0 2 2 0 014 0zM12 10a2 2 0 11-4 0 2 2 0 014 0zM16 12a2 2 0 100-4 2 2 0 000 4z" />
                  </svg>
                </button>
              </div>
              
              {/* Node content */}
              <div className="p-4">
                <div className="space-y-3">
                  {Object.entries(node.properties).map(([key, value]) => (
                    <div key={key} className="flex justify-between">
                      <span className="text-sm text-white/70">{key}:</span>
                      <span className="text-sm font-mono">
                        {typeof value === 'object' 
                          ? Array.isArray(value) 
                            ? value.join(', ') 
                            : JSON.stringify(value)
                          : String(value)
                        }
                      </span>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Connection points */}
              <div className="p-4 flex justify-between border-t border-glass-strong">
                {/* Input connections */}
                <div className="flex space-x-2">
                  {node.inputs.map(input => (
                    <div 
                      key={input}
                      className="group flex flex-col items-center"
                    >
                      <div 
                        className="w-4 h-4 rounded-full bg-glass-strong border border-white/30 group-hover:border-primary group-hover:shadow-neon-primary transition-all duration-200 cursor-pointer"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (connecting) {
                            handleConnectionEnd(node.id, input);
                          }
                        }}
                      />
                      <span className="text-xs text-white/60 mt-1">{input}</span>
                    </div>
                  ))}
                </div>
                
                {/* Output connections */}
                <div className="flex space-x-2">
                  {node.outputs.map(output => (
                    <div 
                      key={output}
                      className="group flex flex-col items-center"
                    >
                      <div 
                        className="w-4 h-4 rounded-full bg-glass-strong border border-white/30 group-hover:border-primary group-hover:shadow-neon-primary transition-all duration-200 cursor-pointer"
                        onMouseDown={(e) => {
                          e.stopPropagation();
                          handleConnectionStart(node.id, output, e);
                        }}
                      />
                      <span className="text-xs text-white/60 mt-1">{output}</span>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
        
        {/* Properties Panel */}
        <div className="lg:w-1/4">
          <Card variant="default" glowEffect="subtle" className="h-full">
            <div className="p-6 h-full flex flex-col">
              <h2 className="text-xl font-medium mb-6 flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-primary" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
                Properties
              </h2>
              
              {selectedNode ? (
                <div className="space-y-6">
                  <div className="glass-panel p-4 rounded-lg">
                    <h3 className="text-lg font-medium mb-2">
                      {nodes.find(n => n.id === selectedNode)?.title}
                    </h3>
                    <p className="text-sm text-white/60 italic mb-4">
                      Type: {nodes.find(n => n.id === selectedNode)?.type}
                    </p>
                    
                    <div className="space-y-4">
                      {Object.entries(nodes.find(n => n.id === selectedNode)?.properties || {}).map(([key, value]) => (
                        <div key={key}>
                          <label className="block text-sm font-medium text-white/80 mb-1">{key}</label>
                          <input 
                            type="text" 
                            className="w-full bg-glass rounded-md border border-glass-strong px-3 py-2 text-sm text-white"
                            value={typeof value === 'object' ? JSON.stringify(value) : String(value)}
                            onChange={() => {}}
                            onFocus={() => playSound('hover')}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div className="glass-panel p-4 rounded-lg">
                    <h3 className="text-sm font-medium mb-2">Connections</h3>
                    
                    <div className="space-y-2">
                      {connections
                        .filter(conn => conn.sourceId === selectedNode || conn.targetId === selectedNode)
                        .map(conn => (
                          <div 
                            key={conn.id} 
                            className="text-xs p-2 rounded bg-glass-strong flex justify-between items-center"
                          >
                            <span>
                              {conn.sourceId === selectedNode 
                                ? `→ ${nodes.find(n => n.id === conn.targetId)?.title || 'Unknown'}`
                                : `← ${nodes.find(n => n.id === conn.sourceId)?.title || 'Unknown'}`
                              }
                            </span>
                            <button 
                              className="text-white/60 hover:text-accent-pink"
                              onClick={() => {
                                setConnections(connections.filter(c => c.id !== conn.id));
                                playSound('click');
                              }}
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                              </svg>
                            </button>
                          </div>
                        ))
                      }
                    </div>
                  </div>
                  
                  <div className="flex space-x-2">
                    <button 
                      className="flex-1 py-2 rounded-lg bg-primary/20 text-primary hover:bg-primary/30 transition-colors"
                      onClick={() => playSound('click')}
                    >
                      Update
                    </button>
                    <button 
                      className="py-2 px-3 rounded-lg bg-accent-pink/20 text-accent-pink hover:bg-accent-pink/30 transition-colors"
                      onClick={() => {
                        setNodes(nodes.filter(n => n.id !== selectedNode));
                        setConnections(connections.filter(
                          c => c.sourceId !== selectedNode && c.targetId !== selectedNode
                        ));
                        setSelectedNode(null);
                        playSound('error');
                      }}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-center text-white/60">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <p className="mb-2">Select a node to edit its properties</p>
                  <p className="text-sm">You can connect nodes by dragging from output to input points</p>
                </div>
              )}
              
              <div className="mt-auto">
                <button 
                  className="w-full py-2 rounded-lg text-white glass-panel hover:bg-glass-strong transition-colors flex items-center justify-center space-x-2"
                  onClick={() => playSound('success')}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                  <span>Export Architecture</span>
                </button>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </motion.div>
  );
};

export default ArchitectureEditor;