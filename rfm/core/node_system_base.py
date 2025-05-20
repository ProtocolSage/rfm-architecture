"""
Base classes and utilities for the RFM Architecture node system.

This module provides the core data structures and utilities for modeling 
network architectures as node systems with connections.
"""

from __future__ import annotations

import uuid
import logging
import math
import json
from typing import Dict, List, Tuple, Optional, Set, Any, Union, Protocol, TypeVar, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum

import numpy as np

logger = logging.getLogger(__name__)


class NodeType(str, Enum):
    """Type classification for architecture nodes."""
    
    STANDARD = "standard"
    INPUT = "input"
    OUTPUT = "output"
    PROCESSOR = "processor"
    MEMORY = "memory"
    CONTROLLER = "controller"
    ROUTER = "router"
    CUSTOM = "custom"


class ConnectionType(str, Enum):
    """Type classification for node connections."""
    
    STANDARD = "standard"
    EXCITATORY = "excitatory" 
    INHIBITORY = "inhibitory"
    MODULATORY = "modulatory"
    BIDIRECTIONAL = "bidirectional"
    CUSTOM = "custom"


@dataclass
class Node:
    """
    Represents a node in the RFM Architecture system.
    
    A node can be any component in the architecture, such as a neuron, 
    module, or functional unit. Nodes can be connected to other nodes
    to form a network.
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: NodeType = NodeType.STANDARD
    description: str = ""
    position: Tuple[float, float, float] = field(default_factory=lambda: (0.0, 0.0, 0.0))
    color: str = "#42d7f5"  # Default cyan color
    size: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        data = asdict(self)
        
        # Convert enum to string
        if isinstance(data["type"], Enum):
            data["type"] = data["type"].value
            
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Node:
        """Create node from dictionary representation."""
        # Convert string type to enum if needed
        if "type" in data and isinstance(data["type"], str):
            try:
                data["type"] = NodeType(data["type"])
            except ValueError:
                # Default to CUSTOM for unrecognized types
                data["type"] = NodeType.CUSTOM
                
        return cls(**data)


@dataclass
class Connection:
    """
    Represents a connection between two nodes in the architecture.
    
    Connections can have different types (excitatory, inhibitory, etc.)
    and properties (strength, delay, etc.).
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    target_id: str = ""
    type: ConnectionType = ConnectionType.STANDARD
    strength: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert connection to dictionary representation."""
        data = asdict(self)
        
        # Convert enum to string
        if isinstance(data["type"], Enum):
            data["type"] = data["type"].value
            
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Connection:
        """Create connection from dictionary representation."""
        # Convert string type to enum if needed
        if "type" in data and isinstance(data["type"], str):
            try:
                data["type"] = ConnectionType(data["type"])
            except ValueError:
                # Default to CUSTOM for unrecognized types
                data["type"] = ConnectionType.CUSTOM
                
        return cls(**data)


@dataclass
class Architecture:
    """
    Represents a complete architecture with nodes and connections.
    
    This is the main data structure for the RFM Architecture system.
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Architecture"
    description: str = ""
    created: float = field(default_factory=lambda: import time; time.time())
    modified: float = field(default_factory=lambda: import time; time.time())
    nodes: List[Node] = field(default_factory=list)
    connections: List[Connection] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert architecture to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created": self.created,
            "modified": self.modified,
            "nodes": [node.to_dict() for node in self.nodes],
            "connections": [conn.to_dict() for conn in self.connections],
            "properties": self.properties
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Architecture:
        """Create architecture from dictionary representation."""
        # Copy the data to avoid modifying the input
        data_copy = data.copy()
        
        # Convert nodes and connections
        if "nodes" in data_copy:
            nodes_data = data_copy.pop("nodes")
            nodes = [Node.from_dict(node_data) for node_data in nodes_data]
        else:
            nodes = []
            
        if "connections" in data_copy:
            connections_data = data_copy.pop("connections")
            connections = [Connection.from_dict(conn_data) for conn_data in connections_data]
        else:
            connections = []
            
        # Create architecture instance
        arch = cls(**data_copy)
        arch.nodes = nodes
        arch.connections = connections
        
        return arch
    
    def add_node(self, node: Node) -> None:
        """Add a node to the architecture."""
        self.nodes.append(node)
        self.modified = import_time().time()
    
    def update_node(self, node_id: str, updated_data: Dict[str, Any]) -> Optional[Node]:
        """
        Update a node in the architecture.
        
        Args:
            node_id: ID of the node to update
            updated_data: Dictionary with updated values
            
        Returns:
            Updated node, or None if not found
        """
        for i, node in enumerate(self.nodes):
            if node.id == node_id:
                # Create a dictionary representation
                node_dict = node.to_dict()
                
                # Apply updates
                node_dict.update(updated_data)
                
                # Create new node from updated dict
                updated_node = Node.from_dict(node_dict)
                
                # Replace in list
                self.nodes[i] = updated_node
                
                self.modified = import_time().time()
                return updated_node
                
        return None
    
    def remove_node(self, node_id: str) -> bool:
        """
        Remove a node from the architecture.
        
        This also removes all connections to and from the node.
        
        Args:
            node_id: ID of the node to remove
            
        Returns:
            True if the node was removed, False if not found
        """
        # Find the node
        found = False
        self.nodes = [node for node in self.nodes if node.id != node_id]
        
        if not found:
            # Check if we removed anything
            found = len(self.nodes) < len(self.nodes)
            
        # Remove connections to and from the node
        self.connections = [
            conn for conn in self.connections 
            if conn.source_id != node_id and conn.target_id != node_id
        ]
        
        if found:
            self.modified = import_time().time()
            
        return found
    
    def add_connection(self, connection: Connection) -> None:
        """Add a connection to the architecture."""
        self.connections.append(connection)
        self.modified = import_time().time()
    
    def update_connection(self, connection_id: str, updated_data: Dict[str, Any]) -> Optional[Connection]:
        """
        Update a connection in the architecture.
        
        Args:
            connection_id: ID of the connection to update
            updated_data: Dictionary with updated values
            
        Returns:
            Updated connection, or None if not found
        """
        for i, connection in enumerate(self.connections):
            if connection.id == connection_id:
                # Create a dictionary representation
                conn_dict = connection.to_dict()
                
                # Apply updates
                conn_dict.update(updated_data)
                
                # Create new connection from updated dict
                updated_conn = Connection.from_dict(conn_dict)
                
                # Replace in list
                self.connections[i] = updated_conn
                
                self.modified = import_time().time()
                return updated_conn
                
        return None
    
    def remove_connection(self, connection_id: str) -> bool:
        """
        Remove a connection from the architecture.
        
        Args:
            connection_id: ID of the connection to remove
            
        Returns:
            True if the connection was removed, False if not found
        """
        original_count = len(self.connections)
        self.connections = [conn for conn in self.connections if conn.id != connection_id]
        
        removed = len(self.connections) < original_count
        if removed:
            self.modified = import_time().time()
            
        return removed
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None
    
    def get_connection(self, connection_id: str) -> Optional[Connection]:
        """Get a connection by ID."""
        for conn in self.connections:
            if conn.id == connection_id:
                return conn
        return None
    
    def get_connections_for_node(self, node_id: str) -> List[Connection]:
        """Get all connections involving a specific node."""
        return [
            conn for conn in self.connections
            if conn.source_id == node_id or conn.target_id == node_id
        ]
    
    def get_outgoing_connections(self, node_id: str) -> List[Connection]:
        """Get all outgoing connections from a node."""
        return [conn for conn in self.connections if conn.source_id == node_id]
    
    def get_incoming_connections(self, node_id: str) -> List[Connection]:
        """Get all incoming connections to a node."""
        return [conn for conn in self.connections if conn.target_id == node_id]
    
    def clear(self) -> None:
        """Clear all nodes and connections from the architecture."""
        self.nodes.clear()
        self.connections.clear()
        self.modified = import_time().time()
    
    def save_to_file(self, filepath: str) -> bool:
        """
        Save the architecture to a JSON file.
        
        Args:
            filepath: Path to save the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save architecture to {filepath}: {e}")
            return False
    
    @classmethod
    def load_from_file(cls, filepath: str) -> Optional[Architecture]:
        """
        Load an architecture from a JSON file.
        
        Args:
            filepath: Path to the file
            
        Returns:
            Loaded architecture, or None if loading failed
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load architecture from {filepath}: {e}")
            return None


def import_time():
    """Helper to import time module only when needed."""
    import time
    return time


# Utility functions for working with architectures

def calculate_network_metrics(architecture: Architecture) -> Dict[str, float]:
    """
    Calculate various network metrics for the architecture.
    
    Args:
        architecture: The architecture to analyze
        
    Returns:
        Dictionary with calculated metrics
    """
    node_count = len(architecture.nodes)
    connection_count = len(architecture.connections)
    
    if node_count == 0:
        return {
            "node_count": 0,
            "connection_count": 0,
            "density": 0.0,
            "average_degree": 0.0,
            "connectivity_ratio": 0.0
        }
    
    # Calculate network density (actual connections / possible connections)
    max_connections = node_count * (node_count - 1)  # Directed graph
    density = connection_count / max_connections if max_connections > 0 else 0
    
    # Calculate average degree (average number of connections per node)
    average_degree = connection_count / node_count
    
    # Calculate connectivity ratio (ratio of connected nodes to total nodes)
    connected_nodes = set()
    for conn in architecture.connections:
        connected_nodes.add(conn.source_id)
        connected_nodes.add(conn.target_id)
    connectivity_ratio = len(connected_nodes) / node_count if node_count > 0 else 0
    
    return {
        "node_count": node_count,
        "connection_count": connection_count,
        "density": density,
        "average_degree": average_degree,
        "connectivity_ratio": connectivity_ratio
    }


def clone_architecture(architecture: Architecture, new_id: bool = True) -> Architecture:
    """
    Create a deep copy of an architecture.
    
    Args:
        architecture: The architecture to clone
        new_id: Whether to assign a new ID to the cloned architecture
        
    Returns:
        A new Architecture instance with the same data
    """
    # Convert to dict and back to create a deep copy
    arch_dict = architecture.to_dict()
    
    if new_id:
        arch_dict["id"] = str(uuid.uuid4())
        
    return Architecture.from_dict(arch_dict)


def merge_architectures(arch1: Architecture, arch2: Architecture) -> Architecture:
    """
    Merge two architectures into a new one.
    
    This creates a new architecture containing all nodes and connections
    from both input architectures. Node and connection IDs are preserved
    unless there are conflicts.
    
    Args:
        arch1: First architecture
        arch2: Second architecture
        
    Returns:
        A new merged Architecture
    """
    # Start with a clone of the first architecture
    merged = clone_architecture(arch1, new_id=True)
    merged.name = f"Merge of {arch1.name} and {arch2.name}"
    
    # Track existing node and connection IDs to avoid duplicates
    existing_node_ids = {node.id for node in merged.nodes}
    existing_conn_ids = {conn.id for conn in merged.connections}
    
    # Add nodes from the second architecture
    for node in arch2.nodes:
        if node.id in existing_node_ids:
            # Create a copy with a new ID
            node_dict = node.to_dict()
            node_dict["id"] = str(uuid.uuid4())
            merged.nodes.append(Node.from_dict(node_dict))
        else:
            merged.nodes.append(node)
            existing_node_ids.add(node.id)
    
    # Add connections from the second architecture
    for conn in arch2.connections:
        if conn.id in existing_conn_ids:
            # Create a copy with a new ID
            conn_dict = conn.to_dict()
            conn_dict["id"] = str(uuid.uuid4())
            merged.connections.append(Connection.from_dict(conn_dict))
        else:
            merged.connections.append(conn)
            existing_conn_ids.add(conn.id)
    
    return merged


# Default architecture templates

def create_default_architecture() -> Architecture:
    """
    Create a simple default architecture with some basic nodes and connections.
    
    Returns:
        A new Architecture instance with default nodes and connections
    """
    arch = Architecture(name="Default Architecture", 
                       description="A simple default architecture with basic components")
    
    # Create nodes
    input_node = Node(
        id=str(uuid.uuid4()),
        name="Input",
        type=NodeType.INPUT,
        description="Input processing node",
        position=(0.0, 0.0, 0.0),
        color="#4287f5"  # Blue
    )
    
    processor_node = Node(
        id=str(uuid.uuid4()),
        name="Processor",
        type=NodeType.PROCESSOR,
        description="Central processing node",
        position=(0.0, 1.0, 0.0),
        color="#f54242"  # Red
    )
    
    memory_node = Node(
        id=str(uuid.uuid4()),
        name="Memory",
        type=NodeType.MEMORY,
        description="Memory storage node",
        position=(1.0, 0.5, 0.0),
        color="#42f584"  # Green
    )
    
    output_node = Node(
        id=str(uuid.uuid4()),
        name="Output",
        type=NodeType.OUTPUT,
        description="Output processing node",
        position=(0.0, 2.0, 0.0),
        color="#f5a742"  # Orange
    )
    
    # Add nodes to architecture
    arch.nodes = [input_node, processor_node, memory_node, output_node]
    
    # Create connections
    conn1 = Connection(
        id=str(uuid.uuid4()),
        source_id=input_node.id,
        target_id=processor_node.id,
        type=ConnectionType.STANDARD,
        strength=1.0
    )
    
    conn2 = Connection(
        id=str(uuid.uuid4()),
        source_id=processor_node.id,
        target_id=memory_node.id,
        type=ConnectionType.STANDARD,
        strength=0.8
    )
    
    conn3 = Connection(
        id=str(uuid.uuid4()),
        source_id=memory_node.id,
        target_id=processor_node.id,
        type=ConnectionType.STANDARD,
        strength=0.8
    )
    
    conn4 = Connection(
        id=str(uuid.uuid4()),
        source_id=processor_node.id,
        target_id=output_node.id,
        type=ConnectionType.STANDARD,
        strength=1.0
    )
    
    # Add connections to architecture
    arch.connections = [conn1, conn2, conn3, conn4]
    
    return arch


def create_rfm_architecture() -> Architecture:
    """
    Create a basic RFM (Recursive Fractal Mind) architecture.
    
    This creates an architecture based on the RFM model with consciousness
    integration field, perception system, etc.
    
    Returns:
        A new Architecture instance with RFM components
    """
    arch = Architecture(name="RFM Architecture", 
                       description="Recursive Fractal Mind architecture model")
    
    # Create nodes for key components
    cif_node = Node(
        id=str(uuid.uuid4()),
        name="Consciousness Integration Field",
        type=NodeType.CONTROLLER,
        description="Global workspace for information broadcast",
        position=(0.0, 0.0, 0.0),
        color="#42d7f5"  # Cyan
    )
    
    perception_node = Node(
        id=str(uuid.uuid4()),
        name="Perception System",
        type=NodeType.INPUT,
        description="Sensory processing & pattern recognition",
        position=(-2.0, 0.0, 0.0),
        color="#4287f5"  # Blue
    )
    
    knowledge_node = Node(
        id=str(uuid.uuid4()),
        name="Knowledge Integration Network",
        type=NodeType.MEMORY,
        description="Dynamic semantic representation",
        position=(2.0, 0.0, 0.0),
        color="#f54242"  # Red
    )
    
    metacognitive_node = Node(
        id=str(uuid.uuid4()),
        name="Metacognitive Executive",
        type=NodeType.CONTROLLER,
        description="Reflective self-monitoring",
        position=(0.0, 2.0, 0.0),
        color="#42f584"  # Green
    )
    
    evolutionary_node = Node(
        id=str(uuid.uuid4()),
        name="Evolutionary Optimizer",
        type=NodeType.PROCESSOR,
        description="Structure adaptation",
        position=(-2.0, 2.0, 0.0),
        color="#9942f5"  # Purple
    )
    
    simulation_node = Node(
        id=str(uuid.uuid4()),
        name="Simulation Engine",
        type=NodeType.PROCESSOR,
        description="Predictive world modeling",
        position=(2.0, 2.0, 0.0),
        color="#f5a742"  # Orange
    )
    
    # Add nodes to architecture
    arch.nodes = [
        cif_node, 
        perception_node, 
        knowledge_node, 
        metacognitive_node, 
        evolutionary_node, 
        simulation_node
    ]
    
    # Create connections between nodes
    connections = [
        # Connect perception to CIF
        Connection(
            id=str(uuid.uuid4()),
            source_id=perception_node.id,
            target_id=cif_node.id,
            type=ConnectionType.BIDIRECTIONAL,
            strength=1.0
        ),
        
        # Connect CIF to knowledge
        Connection(
            id=str(uuid.uuid4()),
            source_id=cif_node.id,
            target_id=knowledge_node.id,
            type=ConnectionType.BIDIRECTIONAL,
            strength=1.0
        ),
        
        # Connect CIF to metacognitive
        Connection(
            id=str(uuid.uuid4()),
            source_id=cif_node.id,
            target_id=metacognitive_node.id,
            type=ConnectionType.BIDIRECTIONAL,
            strength=1.0
        ),
        
        # Connect metacognitive to evolutionary
        Connection(
            id=str(uuid.uuid4()),
            source_id=metacognitive_node.id,
            target_id=evolutionary_node.id,
            type=ConnectionType.BIDIRECTIONAL,
            strength=0.8
        ),
        
        # Connect evolutionary to simulation
        Connection(
            id=str(uuid.uuid4()),
            source_id=evolutionary_node.id,
            target_id=simulation_node.id,
            type=ConnectionType.BIDIRECTIONAL,
            strength=0.8
        ),
        
        # Connect simulation to CIF
        Connection(
            id=str(uuid.uuid4()),
            source_id=simulation_node.id,
            target_id=cif_node.id,
            type=ConnectionType.BIDIRECTIONAL,
            strength=0.7
        )
    ]
    
    arch.connections = connections
    
    return arch


# Example emotional state parameters for architecture simulations
@dataclass
class EmotionalState:
    """
    Represents an emotional state for architecture simulation.
    
    This class provides parameters for modulating the architecture behavior
    based on emotional states, which can affect connection strengths,
    activation thresholds, etc.
    """
    
    arousal: float = 0.5  # General activation level (0.0 to 1.0)
    valence: float = 0.5  # Positive vs negative affect (-1.0 to 1.0)
    dominance: float = 0.5  # Feeling of control (0.0 to 1.0)
    certainty: float = 0.5  # Confidence level (0.0 to 1.0)
    
    def to_dict(self) -> Dict[str, float]:
        """Convert emotional state to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> EmotionalState:
        """Create emotional state from dictionary."""
        return cls(**data)