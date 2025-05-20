"""Network graph generation for RFM visualization."""
from __future__ import annotations

import logging
from typing import Dict, Any, Tuple, Optional

import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


class KINGraph:
    """Knowledge Integration Network (KIN) graph generator."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the KIN graph with the given configuration.
        
        Args:
            config: Configuration dictionary with KIN graph parameters
        """
        self.nodes = config.get("nodes", 10)
        self.edge_probability = config.get("edge_probability", 0.3)
        self.node_size = config.get("node_size", 3)
        self.node_color = config.get("node_color", "#f54242")
        self.edge_color = config.get("edge_color", "#f5a742")
        self.layout_type = config.get("layout", "spring")
        
        # Create the graph
        self.graph = self._create_graph()
        self.positions = self._compute_layout()
        
        logger.debug(f"Initialized KIN graph with {self.nodes} nodes, {len(self.graph.edges)} edges")
    
    def _create_graph(self) -> nx.Graph:
        """Create a random graph for the KIN.
        
        Returns:
            A NetworkX graph
        """
        # Create a random graph
        if self.layout_type == "circular":
            graph = nx.random_regular_graph(3, self.nodes, seed=42)
        else:
            graph = nx.gnp_random_graph(self.nodes, self.edge_probability, seed=42)
        
        # Ensure the graph is connected
        if not nx.is_connected(graph):
            components = list(nx.connected_components(graph))
            for i in range(1, len(components)):
                # Connect each component to the largest component
                node1 = next(iter(components[0]))
                node2 = next(iter(components[i]))
                graph.add_edge(node1, node2)
        
        # Add node attributes
        for node in graph.nodes:
            graph.nodes[node]["name"] = f"C{node}"
            graph.nodes[node]["importance"] = np.random.uniform(0.5, 1.0)
        
        # Add edge attributes
        for u, v in graph.edges:
            graph.edges[u, v]["weight"] = np.random.uniform(0.1, 1.0)
        
        return graph
    
    def _compute_layout(self) -> Dict[int, Tuple[float, float]]:
        """Compute the layout for the graph.
        
        Returns:
            A dictionary mapping node IDs to (x, y) coordinates
        """
        if self.layout_type == "spring":
            pos = nx.spring_layout(self.graph, seed=42)
        elif self.layout_type == "circular":
            pos = nx.circular_layout(self.graph)
        elif self.layout_type == "random":
            pos = nx.random_layout(self.graph, seed=42)
        else:
            pos = nx.spring_layout(self.graph, seed=42)
        
        return pos
    
    def draw(self, ax: plt.Axes, component: Dict[str, Any]) -> None:
        """Draw the KIN graph within the specified component.
        
        Args:
            ax: Matplotlib axes to draw on
            component: Component dictionary containing center and size
        """
        # Get component center and size
        center_x, center_y = component["center"]
        width, height = component["size"]
        
        # Scale factor for the graph to fit inside the component
        scale_x = width * 0.7
        scale_y = height * 0.7
        
        # Draw edges
        for u, v in self.graph.edges:
            x1, y1 = self.positions[u]
            x2, y2 = self.positions[v]
            
            # Transform coordinates to fit inside the component
            x1_transformed = center_x + x1 * scale_x
            y1_transformed = center_y + y1 * scale_y
            x2_transformed = center_x + x2 * scale_x
            y2_transformed = center_y + y2 * scale_y
            
            weight = self.graph.edges[u, v].get("weight", 1.0)
            ax.plot([x1_transformed, x2_transformed], [y1_transformed, y2_transformed], 
                   color=self.edge_color, linewidth=0.5 * weight, alpha=0.7, zorder=7)
        
        # Draw nodes
        for node in self.graph.nodes:
            x, y = self.positions[node]
            
            # Transform coordinates to fit inside the component
            x_transformed = center_x + x * scale_x
            y_transformed = center_y + y * scale_y
            
            importance = self.graph.nodes[node].get("importance", 1.0)
            ax.scatter(x_transformed, y_transformed, 
                      s=self.node_size * importance * 10, 
                      color=self.node_color, 
                      alpha=0.9, zorder=8)
        
        logger.debug(f"Drew KIN graph with {len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges")


def create_kin_graph(config: Dict[str, Any]) -> KINGraph:
    """Factory function to create a KIN graph based on configuration.
    
    Args:
        config: Configuration dictionary with KIN graph parameters
    
    Returns:
        A KIN graph
    """
    return KINGraph(config)