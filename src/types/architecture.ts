/**
 * Types related to system architecture and components
 */

/**
 * Represents a node in the system architecture
 */
export interface SystemNode {
  id: string;
  name?: string;
  type?: string;
  description?: string;
  position?: [number, number, number];
  color?: string;
  size?: number;
  properties?: Record<string, any>;
}

/**
 * Represents a connection between nodes
 */
export interface Connection {
  id: string;
  sourceId: string;
  targetId: string;
  type?: string;
  strength: number;
  properties?: Record<string, any>;
}

/**
 * Represents the complete architecture
 */
export interface Architecture {
  id?: string;
  name?: string;
  description?: string;
  nodes: SystemNode[];
  connections: Connection[];
  metadata?: Record<string, any>;
}

/**
 * Runtime state of the architecture
 */
export interface ArchitectureState {
  nodeActivations: Record<string, number>;
  connectionFlows: Record<string, number>;
  activeThoughts: string[];
  focusedNodes: string[];
  globalActivity: number;
}