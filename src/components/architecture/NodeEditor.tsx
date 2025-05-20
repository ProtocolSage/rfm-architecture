import React, { useState, useEffect } from 'react';
import { SystemNode } from '../../types/architecture';

interface NodeEditorProps {
  nodes: SystemNode[];
  onCreateNode: (node: Omit<SystemNode, 'id'>) => void;
  onUpdateNode: (id: string, changes: Partial<SystemNode>) => void;
  onDeleteNode: (id: string) => void;
  selectedNodeId?: string;
}

const NodeEditor: React.FC<NodeEditorProps> = ({
  nodes,
  onCreateNode,
  onUpdateNode,
  onDeleteNode,
  selectedNodeId
}) => {
  // Form state for new nodes
  const [nodeName, setNodeName] = useState<string>('');
  const [nodeType, setNodeType] = useState<string>('default');
  const [nodeDescription, setNodeDescription] = useState<string>('');
  const [nodeColor, setNodeColor] = useState<string>('#06b6d4');
  const [nodeSize, setNodeSize] = useState<number>(1);
  const [nodeX, setNodeX] = useState<number>(0);
  const [nodeY, setNodeY] = useState<number>(0);
  const [nodeZ, setNodeZ] = useState<number>(0);
  
  // State for selected node (for editing)
  const [selectedNode, setSelectedNode] = useState<SystemNode | null>(null);

  // Load selected node for editing
  useEffect(() => {
    if (selectedNodeId) {
      const node = nodes.find(n => n.id === selectedNodeId);
      if (node) {
        setSelectedNode(node);
        setNodeName(node.name || '');
        setNodeType(node.type || 'default');
        setNodeDescription(node.description || '');
        setNodeColor(node.color || '#06b6d4');
        setNodeSize(node.size || 1);
        setNodeX(node.position?.[0] || 0);
        setNodeY(node.position?.[1] || 0);
        setNodeZ(node.position?.[2] || 0);
      }
    } else {
      setSelectedNode(null);
    }
  }, [selectedNodeId, nodes]);

  // Node types
  const nodeTypes = [
    { id: 'default', name: 'Default' },
    { id: 'consciousness', name: 'Consciousness' },
    { id: 'perception', name: 'Perception' },
    { id: 'memory', name: 'Memory' },
    { id: 'attention', name: 'Attention' },
    { id: 'emotion', name: 'Emotion' },
    { id: 'reasoning', name: 'Reasoning' },
    { id: 'planning', name: 'Planning' },
    { id: 'language', name: 'Language' },
    { id: 'sensory', name: 'Sensory' },
    { id: 'motor', name: 'Motor' },
    { id: 'custom', name: 'Custom' }
  ];

  // Handle form submission for new node
  const handleCreateNode = (e: React.FormEvent) => {
    e.preventDefault();
    const newNode = {
      name: nodeName,
      type: nodeType,
      description: nodeDescription,
      color: nodeColor,
      size: nodeSize,
      position: [nodeX, nodeY, nodeZ] as [number, number, number]
    };
    
    onCreateNode(newNode);
    
    // Reset form
    setNodeName('');
    setNodeType('default');
    setNodeDescription('');
    setNodeColor('#06b6d4');
    setNodeSize(1);
    setNodeX(0);
    setNodeY(0);
    setNodeZ(0);
  };

  // Handle updating an existing node
  const handleUpdateNode = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedNode) {
      onUpdateNode(selectedNode.id, {
        name: nodeName,
        type: nodeType,
        description: nodeDescription,
        color: nodeColor,
        size: nodeSize,
        position: [nodeX, nodeY, nodeZ] as [number, number, number]
      });
    }
  };

  // Neon styles
  const neonBorderStyle = 'border border-cyan-500/30 focus:ring-cyan-500 focus:border-cyan-500';
  const neonTextStyle = 'text-cyan-300';
  const neonBgStyle = 'bg-gray-900';
  const neonFocusRing = 'focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 focus:ring-cyan-500';

  return (
    <div className="space-y-4">
      <h3 className={`text-lg font-semibold ${neonTextStyle}`} style={{ textShadow: '0 0 2px #06b6d4' }}>
        Node Editor
      </h3>

      {/* Create New Node Form */}
      {!selectedNode && (
        <form onSubmit={handleCreateNode} className="space-y-3 border border-cyan-500/20 rounded p-3">
          <h4 className={`text-sm font-medium ${neonTextStyle}`}>Create New Node</h4>
          
          {/* Node Name */}
          <div>
            <label htmlFor="nodeName" className={`block text-xs ${neonTextStyle}`}>Node Name</label>
            <input
              type="text"
              id="nodeName"
              value={nodeName}
              onChange={(e) => setNodeName(e.target.value)}
              className={`mt-1 block w-full px-2 py-1 text-sm ${neonBorderStyle} ${neonBgStyle} text-gray-100 focus:outline-none rounded-md ${neonFocusRing}`}
              required
            />
          </div>
          
          {/* Node Type */}
          <div>
            <label htmlFor="nodeType" className={`block text-xs ${neonTextStyle}`}>Node Type</label>
            <select
              id="nodeType"
              value={nodeType}
              onChange={(e) => setNodeType(e.target.value)}
              className={`mt-1 block w-full pl-3 pr-10 py-1 text-sm ${neonBorderStyle} ${neonBgStyle} text-gray-100 focus:outline-none rounded-md ${neonFocusRing}`}
            >
              {nodeTypes.map(type => (
                <option key={type.id} value={type.id}>{type.name}</option>
              ))}
            </select>
          </div>
          
          {/* Node Description */}
          <div>
            <label htmlFor="nodeDescription" className={`block text-xs ${neonTextStyle}`}>Description</label>
            <textarea
              id="nodeDescription"
              value={nodeDescription}
              onChange={(e) => setNodeDescription(e.target.value)}
              rows={2}
              className={`mt-1 block w-full px-2 py-1 text-sm ${neonBorderStyle} ${neonBgStyle} text-gray-100 focus:outline-none rounded-md ${neonFocusRing}`}
            />
          </div>
          
          {/* Node Color */}
          <div>
            <label htmlFor="nodeColor" className={`block text-xs ${neonTextStyle}`}>Color</label>
            <div className="flex space-x-2">
              <input
                type="color"
                id="nodeColor"
                value={nodeColor}
                onChange={(e) => setNodeColor(e.target.value)}
                className="w-8 h-8 rounded cursor-pointer"
              />
              <input
                type="text"
                value={nodeColor}
                onChange={(e) => setNodeColor(e.target.value)}
                className={`block flex-1 px-2 py-1 text-sm ${neonBorderStyle} ${neonBgStyle} text-gray-100 focus:outline-none rounded-md ${neonFocusRing}`}
              />
            </div>
          </div>
          
          {/* Node Size */}
          <div>
            <label htmlFor="nodeSize" className={`block text-xs ${neonTextStyle}`}>
              Size: {nodeSize.toFixed(1)}
            </label>
            <input
              type="range"
              id="nodeSize"
              min="0.1"
              max="3"
              step="0.1"
              value={nodeSize}
              onChange={(e) => setNodeSize(parseFloat(e.target.value))}
              className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer range-cyan-sm"
            />
          </div>
          
          {/* Node Position */}
          <div>
            <label className={`block text-xs ${neonTextStyle}`}>Position</label>
            <div className="grid grid-cols-3 gap-2">
              <div>
                <label htmlFor="nodeX" className={`block text-xs ${neonTextStyle}`}>X</label>
                <input
                  type="number"
                  id="nodeX"
                  value={nodeX}
                  onChange={(e) => setNodeX(parseFloat(e.target.value))}
                  className={`block w-full px-2 py-1 text-sm ${neonBorderStyle} ${neonBgStyle} text-gray-100 focus:outline-none rounded-md ${neonFocusRing}`}
                />
              </div>
              <div>
                <label htmlFor="nodeY" className={`block text-xs ${neonTextStyle}`}>Y</label>
                <input
                  type="number"
                  id="nodeY"
                  value={nodeY}
                  onChange={(e) => setNodeY(parseFloat(e.target.value))}
                  className={`block w-full px-2 py-1 text-sm ${neonBorderStyle} ${neonBgStyle} text-gray-100 focus:outline-none rounded-md ${neonFocusRing}`}
                />
              </div>
              <div>
                <label htmlFor="nodeZ" className={`block text-xs ${neonTextStyle}`}>Z</label>
                <input
                  type="number"
                  id="nodeZ"
                  value={nodeZ}
                  onChange={(e) => setNodeZ(parseFloat(e.target.value))}
                  className={`block w-full px-2 py-1 text-sm ${neonBorderStyle} ${neonBgStyle} text-gray-100 focus:outline-none rounded-md ${neonFocusRing}`}
                />
              </div>
            </div>
          </div>
          
          <button
            type="submit"
            className={`w-full bg-cyan-600 hover:bg-cyan-700 text-white font-bold py-1 px-4 text-sm rounded focus:outline-none ${neonFocusRing} shadow-cyan-500/30 hover:shadow-lg hover:shadow-cyan-500/40`}
          >
            Create Node
          </button>
        </form>
      )}

      {/* Edit Existing Node */}
      {selectedNode && (
        <form onSubmit={handleUpdateNode} className="space-y-3 border border-cyan-500/20 rounded p-3">
          <div className="flex justify-between items-center">
            <h4 className={`text-sm font-medium ${neonTextStyle}`}>Edit Node</h4>
            <button
              type="button"
              onClick={() => onDeleteNode(selectedNode.id)}
              className="text-red-500 hover:text-red-400 text-xs"
            >
              Delete
            </button>
          </div>
          
          {/* Node Name */}
          <div>
            <label htmlFor="editNodeName" className={`block text-xs ${neonTextStyle}`}>Node Name</label>
            <input
              type="text"
              id="editNodeName"
              value={nodeName}
              onChange={(e) => setNodeName(e.target.value)}
              className={`mt-1 block w-full px-2 py-1 text-sm ${neonBorderStyle} ${neonBgStyle} text-gray-100 focus:outline-none rounded-md ${neonFocusRing}`}
              required
            />
          </div>
          
          {/* Node Type */}
          <div>
            <label htmlFor="editNodeType" className={`block text-xs ${neonTextStyle}`}>Node Type</label>
            <select
              id="editNodeType"
              value={nodeType}
              onChange={(e) => setNodeType(e.target.value)}
              className={`mt-1 block w-full pl-3 pr-10 py-1 text-sm ${neonBorderStyle} ${neonBgStyle} text-gray-100 focus:outline-none rounded-md ${neonFocusRing}`}
            >
              {nodeTypes.map(type => (
                <option key={type.id} value={type.id}>{type.name}</option>
              ))}
            </select>
          </div>
          
          {/* Node Description */}
          <div>
            <label htmlFor="editNodeDescription" className={`block text-xs ${neonTextStyle}`}>Description</label>
            <textarea
              id="editNodeDescription"
              value={nodeDescription}
              onChange={(e) => setNodeDescription(e.target.value)}
              rows={2}
              className={`mt-1 block w-full px-2 py-1 text-sm ${neonBorderStyle} ${neonBgStyle} text-gray-100 focus:outline-none rounded-md ${neonFocusRing}`}
            />
          </div>
          
          {/* Node Color */}
          <div>
            <label htmlFor="editNodeColor" className={`block text-xs ${neonTextStyle}`}>Color</label>
            <div className="flex space-x-2">
              <input
                type="color"
                id="editNodeColor"
                value={nodeColor}
                onChange={(e) => setNodeColor(e.target.value)}
                className="w-8 h-8 rounded cursor-pointer"
              />
              <input
                type="text"
                value={nodeColor}
                onChange={(e) => setNodeColor(e.target.value)}
                className={`block flex-1 px-2 py-1 text-sm ${neonBorderStyle} ${neonBgStyle} text-gray-100 focus:outline-none rounded-md ${neonFocusRing}`}
              />
            </div>
          </div>
          
          {/* Node Size */}
          <div>
            <label htmlFor="editNodeSize" className={`block text-xs ${neonTextStyle}`}>
              Size: {nodeSize.toFixed(1)}
            </label>
            <input
              type="range"
              id="editNodeSize"
              min="0.1"
              max="3"
              step="0.1"
              value={nodeSize}
              onChange={(e) => setNodeSize(parseFloat(e.target.value))}
              className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer range-cyan-sm"
            />
          </div>
          
          {/* Node Position */}
          <div>
            <label className={`block text-xs ${neonTextStyle}`}>Position</label>
            <div className="grid grid-cols-3 gap-2">
              <div>
                <label htmlFor="editNodeX" className={`block text-xs ${neonTextStyle}`}>X</label>
                <input
                  type="number"
                  id="editNodeX"
                  value={nodeX}
                  onChange={(e) => setNodeX(parseFloat(e.target.value))}
                  className={`block w-full px-2 py-1 text-sm ${neonBorderStyle} ${neonBgStyle} text-gray-100 focus:outline-none rounded-md ${neonFocusRing}`}
                />
              </div>
              <div>
                <label htmlFor="editNodeY" className={`block text-xs ${neonTextStyle}`}>Y</label>
                <input
                  type="number"
                  id="editNodeY"
                  value={nodeY}
                  onChange={(e) => setNodeY(parseFloat(e.target.value))}
                  className={`block w-full px-2 py-1 text-sm ${neonBorderStyle} ${neonBgStyle} text-gray-100 focus:outline-none rounded-md ${neonFocusRing}`}
                />
              </div>
              <div>
                <label htmlFor="editNodeZ" className={`block text-xs ${neonTextStyle}`}>Z</label>
                <input
                  type="number"
                  id="editNodeZ"
                  value={nodeZ}
                  onChange={(e) => setNodeZ(parseFloat(e.target.value))}
                  className={`block w-full px-2 py-1 text-sm ${neonBorderStyle} ${neonBgStyle} text-gray-100 focus:outline-none rounded-md ${neonFocusRing}`}
                />
              </div>
            </div>
          </div>
          
          <div className="flex space-x-2">
            <button
              type="submit"
              className={`flex-1 bg-cyan-600 hover:bg-cyan-700 text-white font-bold py-1 px-4 text-sm rounded focus:outline-none ${neonFocusRing} shadow-cyan-500/30 hover:shadow-lg hover:shadow-cyan-500/40`}
            >
              Update Node
            </button>
            <button
              type="button"
              onClick={() => setSelectedNode(null)}
              className="bg-gray-700 hover:bg-gray-600 text-white font-bold py-1 px-4 text-sm rounded focus:outline-none"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Nodes List */}
      <div className="border border-cyan-500/20 rounded p-3">
        <h4 className={`text-sm font-medium ${neonTextStyle} mb-2`}>All Nodes</h4>
        
        {nodes.length === 0 ? (
          <p className="text-xs text-gray-400 text-center py-2">No nodes defined yet</p>
        ) : (
          <div className="space-y-1 max-h-48 overflow-y-auto pr-1">
            {nodes.map(node => (
              <div
                key={node.id}
                className={`text-xs p-2 rounded cursor-pointer ${node.id === selectedNodeId ? 'bg-cyan-900/50' : 'hover:bg-gray-800'}`}
                onClick={() => onUpdateNode(node.id, {})} // Just to select it
                style={{ borderLeft: `3px solid ${node.color || '#06b6d4'}` }}
              >
                <div className="flex justify-between">
                  <span className="font-medium">{node.name || node.id}</span>
                  <span className="text-gray-400">{node.type}</span>
                </div>
                {node.description && (
                  <p className="text-gray-400 truncate mt-1">{node.description}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default NodeEditor;