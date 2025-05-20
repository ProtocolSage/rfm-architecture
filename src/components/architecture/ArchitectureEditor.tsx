import React, { useState, useCallback } from 'react';
import { Tab } from '@headlessui/react';
import { v4 as uuidv4 } from 'uuid';
import NodeEditor from './NodeEditor';
import ConnectionEditor from './ConnectionEditor';
import { SystemNode, Connection, Architecture } from '../../types/architecture';

interface ArchitectureEditorProps {
  architecture: Architecture;
  onArchitectureChange: (architecture: Architecture) => void;
}

const ArchitectureEditor: React.FC<ArchitectureEditorProps> = ({
  architecture,
  onArchitectureChange
}) => {
  const [selectedNodeId, setSelectedNodeId] = useState<string | undefined>(undefined);
  const [selectedConnectionId, setSelectedConnectionId] = useState<string | undefined>(undefined);

  // Node operations
  const handleCreateNode = useCallback((nodeData: Omit<SystemNode, 'id'>) => {
    const newNode: SystemNode = {
      id: uuidv4(),
      ...nodeData
    };
    
    onArchitectureChange({
      ...architecture,
      nodes: [...architecture.nodes, newNode]
    });
  }, [architecture, onArchitectureChange]);

  const handleUpdateNode = useCallback((nodeId: string, changes: Partial<SystemNode>) => {
    // If no changes, just select the node
    if (Object.keys(changes).length === 0) {
      setSelectedNodeId(nodeId);
      setSelectedConnectionId(undefined);
      return;
    }
    
    const updatedNodes = architecture.nodes.map(node => 
      node.id === nodeId ? { ...node, ...changes } : node
    );
    
    onArchitectureChange({
      ...architecture,
      nodes: updatedNodes
    });
  }, [architecture, onArchitectureChange]);

  const handleDeleteNode = useCallback((nodeId: string) => {
    // Remove the node
    const updatedNodes = architecture.nodes.filter(node => node.id !== nodeId);
    
    // Remove any connections involving the node
    const updatedConnections = architecture.connections.filter(
      conn => conn.sourceId !== nodeId && conn.targetId !== nodeId
    );
    
    onArchitectureChange({
      ...architecture,
      nodes: updatedNodes,
      connections: updatedConnections
    });
    
    setSelectedNodeId(undefined);
  }, [architecture, onArchitectureChange]);

  // Connection operations
  const handleCreateConnection = useCallback((sourceId: string, targetId: string, strength: number, type: string) => {
    const newConnection: Connection = {
      id: uuidv4(),
      sourceId,
      targetId,
      strength,
      type
    };
    
    onArchitectureChange({
      ...architecture,
      connections: [...architecture.connections, newConnection]
    });
  }, [architecture, onArchitectureChange]);

  const handleModifyConnection = useCallback((connectionId: string, changes: Partial<Connection>) => {
    // If no changes, just select the connection
    if (Object.keys(changes).length === 0) {
      setSelectedConnectionId(connectionId);
      setSelectedNodeId(undefined);
      return;
    }
    
    const updatedConnections = architecture.connections.map(conn => 
      conn.id === connectionId ? { ...conn, ...changes } : conn
    );
    
    onArchitectureChange({
      ...architecture,
      connections: updatedConnections
    });
  }, [architecture, onArchitectureChange]);

  const handleDeleteConnection = useCallback((connectionId: string) => {
    const updatedConnections = architecture.connections.filter(conn => conn.id !== connectionId);
    
    onArchitectureChange({
      ...architecture,
      connections: updatedConnections
    });
    
    setSelectedConnectionId(undefined);
  }, [architecture, onArchitectureChange]);

  // Neon styles
  const neonTextStyle = 'text-cyan-300';
  const neonBorderStyle = 'border-cyan-500/30';
  
  return (
    <div className="space-y-4">
      <h2 className={`text-2xl font-semibold ${neonTextStyle}`} style={{ textShadow: '0 0 3px #06b6d4' }}>
        Architecture Editor
      </h2>
      
      <Tab.Group>
        <Tab.List className="flex space-x-1 rounded-lg bg-gray-800 p-1">
          <Tab 
            className={({ selected }) =>
              `w-full rounded-lg py-2 text-sm font-medium leading-5 text-gray-100
               ring-white/60 ring-offset-2 ring-offset-gray-800 focus:outline-none focus:ring-2 transition-all
               ${selected 
                ? 'bg-cyan-700 shadow text-white' 
                : 'text-gray-400 hover:bg-gray-700/30 hover:text-white'}`
            }
          >
            Nodes
          </Tab>
          <Tab 
            className={({ selected }) =>
              `w-full rounded-lg py-2 text-sm font-medium leading-5 text-gray-100
               ring-white/60 ring-offset-2 ring-offset-gray-800 focus:outline-none focus:ring-2 transition-all
               ${selected 
                ? 'bg-cyan-700 shadow text-white' 
                : 'text-gray-400 hover:bg-gray-700/30 hover:text-white'}`
            }
          >
            Connections
          </Tab>
        </Tab.List>
        <Tab.Panels className="mt-2">
          <Tab.Panel className={`rounded-xl bg-gray-800/50 p-3 border ${neonBorderStyle}`}>
            <NodeEditor
              nodes={architecture.nodes}
              onCreateNode={handleCreateNode}
              onUpdateNode={handleUpdateNode}
              onDeleteNode={handleDeleteNode}
              selectedNodeId={selectedNodeId}
            />
          </Tab.Panel>
          <Tab.Panel className={`rounded-xl bg-gray-800/50 p-3 border ${neonBorderStyle}`}>
            <ConnectionEditor
              nodes={architecture.nodes}
              connections={architecture.connections}
              onCreateConnection={handleCreateConnection}
              onModifyConnection={handleModifyConnection}
              onDeleteConnection={handleDeleteConnection}
              selectedConnectionId={selectedConnectionId}
            />
          </Tab.Panel>
        </Tab.Panels>
      </Tab.Group>
      
      <div className="border border-cyan-500/20 rounded p-3">
        <h4 className={`text-sm font-medium ${neonTextStyle} mb-2`}>Architecture Summary</h4>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className={`${neonTextStyle}`}>Nodes: {architecture.nodes.length}</p>
            <div className="text-xs text-gray-400 mt-1">
              {architecture.nodes.slice(0, 5).map(node => (
                <div key={node.id} className="truncate">{node.name || node.id}</div>
              ))}
              {architecture.nodes.length > 5 && (
                <div>...and {architecture.nodes.length - 5} more</div>
              )}
            </div>
          </div>
          <div>
            <p className={`${neonTextStyle}`}>Connections: {architecture.connections.length}</p>
            <div className="text-xs text-gray-400 mt-1">
              {architecture.connections.slice(0, 5).map(conn => {
                const source = architecture.nodes.find(n => n.id === conn.sourceId)?.name || conn.sourceId;
                const target = architecture.nodes.find(n => n.id === conn.targetId)?.name || conn.targetId;
                return (
                  <div key={conn.id} className="truncate">{source} → {target}</div>
                );
              })}
              {architecture.connections.length > 5 && (
                <div>...and {architecture.connections.length - 5} more</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ArchitectureEditor;