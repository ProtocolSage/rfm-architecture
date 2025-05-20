import React, { useState, useEffect } from 'react';
import { Connection, SystemNode } from '../../types/architecture';

interface ConnectionEditorProps {
  nodes: SystemNode[];
  connections: Connection[];
  onCreateConnection: (sourceId: string, targetId: string, strength: number, type: string) => void;
  onModifyConnection: (connectionId: string, changes: Partial<Connection>) => void;
  onDeleteConnection: (connectionId: string) => void;
  selectedConnectionId?: string;
}

const ConnectionEditor: React.FC<ConnectionEditorProps> = ({
  nodes,
  connections,
  onCreateConnection,
  onModifyConnection,
  onDeleteConnection,
  selectedConnectionId
}) => {
  // Form state for new connections
  const [sourceNodeId, setSourceNodeId] = useState<string>('');
  const [targetNodeId, setTargetNodeId] = useState<string>('');
  const [connectionStrength, setConnectionStrength] = useState<number>(0.5);
  const [connectionType, setConnectionType] = useState<string>('default');
  
  // State for selected connection (for editing)
  const [selectedConnection, setSelectedConnection] = useState<Connection | null>(null);
  const [editStrength, setEditStrength] = useState<number>(0.5);
  const [editType, setEditType] = useState<string>('default');

  // Load selected connection for editing
  useEffect(() => {
    if (selectedConnectionId) {
      const connection = connections.find(c => c.id === selectedConnectionId);
      if (connection) {
        setSelectedConnection(connection);
        setEditStrength(connection.strength);
        setEditType(connection.type);
      }
    } else {
      setSelectedConnection(null);
    }
  }, [selectedConnectionId, connections]);

  // Connection types
  const connectionTypes = [
    { id: 'default', name: 'Default', color: '#06b6d4' },
    { id: 'inhibitory', name: 'Inhibitory', color: '#ef4444' },
    { id: 'excitatory', name: 'Excitatory', color: '#10b981' },
    { id: 'bidirectional', name: 'Bidirectional', color: '#8b5cf6' },
    { id: 'modulatory', name: 'Modulatory', color: '#f59e0b' }
  ];

  // Handle form submission for new connection
  const handleCreateConnection = (e: React.FormEvent) => {
    e.preventDefault();
    if (sourceNodeId && targetNodeId) {
      onCreateConnection(sourceNodeId, targetNodeId, connectionStrength, connectionType);
      // Reset form
      setSourceNodeId('');
      setTargetNodeId('');
      setConnectionStrength(0.5);
      setConnectionType('default');
    }
  };

  // Handle updating an existing connection
  const handleUpdateConnection = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedConnection) {
      onModifyConnection(selectedConnection.id, {
        strength: editStrength,
        type: editType
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
        Connection Editor
      </h3>

      {/* Create New Connection Form */}
      <form onSubmit={handleCreateConnection} className="space-y-3 border border-cyan-500/20 rounded p-3">
        <h4 className={`text-sm font-medium ${neonTextStyle}`}>Create New Connection</h4>
        
        {/* Source Node */}
        <div>
          <label htmlFor="sourceNode" className={`block text-xs ${neonTextStyle}`}>Source Node</label>
          <select
            id="sourceNode"
            value={sourceNodeId}
            onChange={(e) => setSourceNodeId(e.target.value)}
            className={`mt-1 block w-full pl-3 pr-10 py-1 text-sm ${neonBorderStyle} ${neonBgStyle} text-gray-100 focus:outline-none rounded-md ${neonFocusRing}`}
            required
          >
            <option value="">Select Source Node</option>
            {nodes.map(node => (
              <option key={`source-${node.id}`} value={node.id}>{node.name || node.id}</option>
            ))}
          </select>
        </div>
        
        {/* Target Node */}
        <div>
          <label htmlFor="targetNode" className={`block text-xs ${neonTextStyle}`}>Target Node</label>
          <select
            id="targetNode"
            value={targetNodeId}
            onChange={(e) => setTargetNodeId(e.target.value)}
            className={`mt-1 block w-full pl-3 pr-10 py-1 text-sm ${neonBorderStyle} ${neonBgStyle} text-gray-100 focus:outline-none rounded-md ${neonFocusRing}`}
            required
          >
            <option value="">Select Target Node</option>
            {nodes.map(node => (
              <option key={`target-${node.id}`} value={node.id}>{node.name || node.id}</option>
            ))}
          </select>
        </div>
        
        {/* Connection Strength */}
        <div>
          <label htmlFor="connectionStrength" className={`block text-xs ${neonTextStyle}`}>
            Strength: {connectionStrength.toFixed(2)}
          </label>
          <input
            type="range"
            id="connectionStrength"
            min="0"
            max="1"
            step="0.01"
            value={connectionStrength}
            onChange={(e) => setConnectionStrength(parseFloat(e.target.value))}
            className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer range-cyan-sm"
          />
        </div>
        
        {/* Connection Type */}
        <div>
          <label htmlFor="connectionType" className={`block text-xs ${neonTextStyle}`}>Connection Type</label>
          <select
            id="connectionType"
            value={connectionType}
            onChange={(e) => setConnectionType(e.target.value)}
            className={`mt-1 block w-full pl-3 pr-10 py-1 text-sm ${neonBorderStyle} ${neonBgStyle} text-gray-100 focus:outline-none rounded-md ${neonFocusRing}`}
          >
            {connectionTypes.map(type => (
              <option key={type.id} value={type.id}>{type.name}</option>
            ))}
          </select>
        </div>
        
        <button
          type="submit"
          className={`w-full bg-cyan-600 hover:bg-cyan-700 text-white font-bold py-1 px-4 text-sm rounded focus:outline-none ${neonFocusRing} shadow-cyan-500/30 hover:shadow-lg hover:shadow-cyan-500/40`}
        >
          Create Connection
        </button>
      </form>

      {/* Edit Existing Connection */}
      {selectedConnection && (
        <form onSubmit={handleUpdateConnection} className="space-y-3 border border-cyan-500/20 rounded p-3">
          <div className="flex justify-between items-center">
            <h4 className={`text-sm font-medium ${neonTextStyle}`}>Edit Connection</h4>
            <button
              type="button"
              onClick={() => onDeleteConnection(selectedConnection.id)}
              className="text-red-500 hover:text-red-400 text-xs"
            >
              Delete
            </button>
          </div>
          
          {/* Source to Target Display */}
          <div className="text-xs text-cyan-300/80">
            {nodes.find(n => n.id === selectedConnection.sourceId)?.name || selectedConnection.sourceId}
            {" → "}
            {nodes.find(n => n.id === selectedConnection.targetId)?.name || selectedConnection.targetId}
          </div>
          
          {/* Connection Strength */}
          <div>
            <label htmlFor="editStrength" className={`block text-xs ${neonTextStyle}`}>
              Strength: {editStrength.toFixed(2)}
            </label>
            <input
              type="range"
              id="editStrength"
              min="0"
              max="1"
              step="0.01"
              value={editStrength}
              onChange={(e) => setEditStrength(parseFloat(e.target.value))}
              className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer range-cyan-sm"
            />
          </div>
          
          {/* Connection Type */}
          <div>
            <label htmlFor="editType" className={`block text-xs ${neonTextStyle}`}>Connection Type</label>
            <select
              id="editType"
              value={editType}
              onChange={(e) => setEditType(e.target.value)}
              className={`mt-1 block w-full pl-3 pr-10 py-1 text-sm ${neonBorderStyle} ${neonBgStyle} text-gray-100 focus:outline-none rounded-md ${neonFocusRing}`}
            >
              {connectionTypes.map(type => (
                <option key={type.id} value={type.id}>{type.name}</option>
              ))}
            </select>
          </div>
          
          <button
            type="submit"
            className={`w-full bg-cyan-600 hover:bg-cyan-700 text-white font-bold py-1 px-4 text-sm rounded focus:outline-none ${neonFocusRing} shadow-cyan-500/30 hover:shadow-lg hover:shadow-cyan-500/40`}
          >
            Update Connection
          </button>
        </form>
      )}

      {/* Connections List */}
      <div className="border border-cyan-500/20 rounded p-3">
        <h4 className={`text-sm font-medium ${neonTextStyle} mb-2`}>All Connections</h4>
        
        {connections.length === 0 ? (
          <p className="text-xs text-gray-400 text-center py-2">No connections defined yet</p>
        ) : (
          <div className="space-y-1 max-h-48 overflow-y-auto pr-1">
            {connections.map(connection => {
              const sourceNode = nodes.find(n => n.id === connection.sourceId);
              const targetNode = nodes.find(n => n.id === connection.targetId);
              const connectionTypeObj = connectionTypes.find(t => t.id === connection.type);
              
              return (
                <div
                  key={connection.id}
                  className={`text-xs p-2 rounded cursor-pointer ${connection.id === selectedConnectionId ? 'bg-cyan-900/50' : 'hover:bg-gray-800'}`}
                  onClick={() => onModifyConnection(connection.id, {})} // Just to select it
                >
                  <div className="flex justify-between">
                    <span style={{ color: connectionTypeObj?.color || '#06b6d4' }}>
                      {sourceNode?.name || connection.sourceId} → {targetNode?.name || connection.targetId}
                    </span>
                    <span className="text-gray-400">{connection.strength.toFixed(2)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default ConnectionEditor;