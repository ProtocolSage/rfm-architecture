"""
Node graph visualization for RFM Architecture.

This module provides functionality for visualizing node architectures
as interactive graphs with connections.
"""

from __future__ import annotations

import math
import logging
import random
from typing import Dict, List, Tuple, Optional, Set, Any, Callable, Union
import colorsys

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
from matplotlib.colors import to_rgba, to_hex

from .node_system_base import Node, Connection, Architecture, NodeType, ConnectionType

logger = logging.getLogger(__name__)


class NodeGraph:
    """Node graph visualization for architecture networks."""
    
    def __init__(self, architecture: Optional[Architecture] = None):
        """
        Initialize the node graph visualizer.
        
        Args:
            architecture: Optional architecture to visualize
        """
        self.architecture = architecture or Architecture()
        self.layout_cache: Dict[str, Tuple[float, float, float]] = {}
        self.highlighted_nodes: Set[str] = set()
        self.highlighted_connections: Set[str] = set()
        self.custom_node_styles: Dict[str, Dict[str, Any]] = {}
        self.custom_connection_styles: Dict[str, Dict[str, Any]] = {}
        
    def set_architecture(self, architecture: Architecture) -> None:
        """
        Set the architecture to visualize.
        
        Args:
            architecture: Architecture to visualize
        """
        self.architecture = architecture
        self.layout_cache = {}  # Clear layout cache
        
    def draw(self, ax: plt.Axes, use_3d: bool = False, animate: bool = False,
             layout_method: str = "spring", highlight_active: bool = False) -> None:
        """
        Draw the architecture graph.
        
        Args:
            ax: Matplotlib axes to draw on
            use_3d: Whether to use 3D visualization
            animate: Whether to animate the visualization
            layout_method: Method to use for node layout
            highlight_active: Whether to highlight active nodes
        """
        if not self.architecture:
            logger.warning("No architecture to visualize")
            return
            
        # Clear the axes
        ax.clear()
        
        # Set up axes
        if use_3d:
            ax.remove()
            ax = plt.gcf().add_subplot(111, projection='3d')
        
        # Compute layout if needed
        self._compute_layout(layout_method)
        
        # Draw connections
        self._draw_connections(ax, use_3d, animate, highlight_active)
        
        # Draw nodes
        self._draw_nodes(ax, use_3d, animate, highlight_active)
        
        # Set limits and labels
        self._configure_axes(ax, use_3d)
        
    def _compute_layout(self, layout_method: str = "spring") -> None:
        """
        Compute node layout positions.
        
        Args:
            layout_method: Method to use for layout calculations
        """
        nodes = self.architecture.nodes
        connections = self.architecture.connections
        
        # If positions are already defined, use them
        if all(node.position != (0, 0, 0) for node in nodes) and len(nodes) > 1:
            for node in nodes:
                self.layout_cache[node.id] = node.position
            return
            
        # Otherwise, compute layout
        if layout_method == "spring":
            self._spring_layout()
        elif layout_method == "circular":
            self._circular_layout()
        elif layout_method == "hierarchical":
            self._hierarchical_layout()
        else:
            # Default to spring layout
            self._spring_layout()
            
    def _spring_layout(self, iterations: int = 100) -> None:
        """
        Compute spring layout for nodes.
        
        This uses a force-directed layout algorithm.
        
        Args:
            iterations: Number of iterations for layout calculation
        """
        nodes = self.architecture.nodes
        connections = self.architecture.connections
        
        if not nodes:
            return
            
        # Initialize positions randomly if not cached
        positions = {}
        for node in nodes:
            if node.id in self.layout_cache:
                positions[node.id] = self.layout_cache[node.id]
            else:
                positions[node.id] = (
                    random.uniform(-1, 1),
                    random.uniform(-1, 1),
                    random.uniform(-0.5, 0.5)
                )
                
        # Create connection lookup
        connection_lookup = {}
        for conn in connections:
            if conn.source_id not in connection_lookup:
                connection_lookup[conn.source_id] = []
            connection_lookup[conn.source_id].append(conn.target_id)
            
            if conn.target_id not in connection_lookup:
                connection_lookup[conn.target_id] = []
            connection_lookup[conn.target_id].append(conn.source_id)
        
        # Run force-directed layout
        for _ in range(iterations):
            # Calculate forces
            forces = {node.id: [0, 0, 0] for node in nodes}
            
            # Repulsive forces between all nodes
            for i, node1 in enumerate(nodes):
                for j, node2 in enumerate(nodes):
                    if i == j:
                        continue
                        
                    # Calculate distance
                    pos1 = positions[node1.id]
                    pos2 = positions[node2.id]
                    dx = pos1[0] - pos2[0]
                    dy = pos1[1] - pos2[1]
                    dz = pos1[2] - pos2[2]
                    
                    distance = max(0.1, math.sqrt(dx*dx + dy*dy + dz*dz))
                    
                    # Calculate repulsive force (inverse square)
                    force = 1.0 / (distance * distance)
                    
                    # Apply force
                    forces[node1.id][0] += force * dx / distance
                    forces[node1.id][1] += force * dy / distance
                    forces[node1.id][2] += force * dz / distance
            
            # Attractive forces between connected nodes
            for conn in connections:
                # Skip if either node is missing
                if conn.source_id not in positions or conn.target_id not in positions:
                    continue
                    
                # Calculate distance
                pos1 = positions[conn.source_id]
                pos2 = positions[conn.target_id]
                dx = pos1[0] - pos2[0]
                dy = pos1[1] - pos2[1]
                dz = pos1[2] - pos2[2]
                
                distance = max(0.1, math.sqrt(dx*dx + dy*dy + dz*dz))
                
                # Calculate attractive force (spring)
                force = 0.2 * distance * conn.strength
                
                # Apply force
                forces[conn.source_id][0] -= force * dx / distance
                forces[conn.source_id][1] -= force * dy / distance
                forces[conn.source_id][2] -= force * dz / distance
                
                forces[conn.target_id][0] += force * dx / distance
                forces[conn.target_id][1] += force * dy / distance
                forces[conn.target_id][2] += force * dz / distance
            
            # Update positions
            for node in nodes:
                pos = positions[node.id]
                force = forces[node.id]
                
                new_x = pos[0] + force[0] * 0.1
                new_y = pos[1] + force[1] * 0.1
                new_z = pos[2] + force[2] * 0.1
                
                # Limit to reasonable bounds
                new_x = max(-10, min(10, new_x))
                new_y = max(-10, min(10, new_y))
                new_z = max(-10, min(10, new_z))
                
                positions[node.id] = (new_x, new_y, new_z)
                
        # Store final positions in cache
        self.layout_cache = positions
        
    def _circular_layout(self) -> None:
        """
        Compute circular layout for nodes.
        
        This arranges nodes in a circle.
        """
        nodes = self.architecture.nodes
        
        if not nodes:
            return
            
        # Place nodes in a circle
        num_nodes = len(nodes)
        for i, node in enumerate(nodes):
            angle = 2 * math.pi * i / num_nodes
            x = math.cos(angle)
            y = math.sin(angle)
            z = 0.0
            
            self.layout_cache[node.id] = (x, y, z)
            
    def _hierarchical_layout(self) -> None:
        """
        Compute hierarchical layout for nodes.
        
        This arranges nodes in layers based on their connections.
        """
        nodes = self.architecture.nodes
        connections = self.architecture.connections
        
        if not nodes:
            return
            
        # Identify root nodes (no incoming connections)
        root_nodes = set(node.id for node in nodes)
        for conn in connections:
            if conn.target_id in root_nodes:
                root_nodes.remove(conn.target_id)
                
        # If no root nodes, use nodes with fewest incoming connections
        if not root_nodes:
            incoming_counts = {}
            for node in nodes:
                incoming_counts[node.id] = 0
                
            for conn in connections:
                incoming_counts[conn.target_id] = incoming_counts.get(conn.target_id, 0) + 1
                
            min_incoming = min(incoming_counts.values()) if incoming_counts else 0
            root_nodes = {node_id for node_id, count in incoming_counts.items() if count == min_incoming}
            
        # Assign layers
        layers = {}
        visited = set()
        
        def assign_layer(node_id, layer):
            if node_id in visited:
                return
                
            visited.add(node_id)
            layers[node_id] = max(layers.get(node_id, 0), layer)
            
            # Process outgoing connections
            for conn in connections:
                if conn.source_id == node_id:
                    assign_layer(conn.target_id, layer + 1)
        
        # Assign initial layers
        for root_id in root_nodes:
            assign_layer(root_id, 0)
            
        # Handle any unvisited nodes
        if len(visited) < len(nodes):
            remaining_nodes = [node.id for node in nodes if node.id not in visited]
            for node_id in remaining_nodes:
                assign_layer(node_id, 0)
                
        # Compute positions based on layers
        max_layer = max(layers.values()) if layers else 0
        layer_counts = {}
        
        for layer in range(max_layer + 1):
            layer_counts[layer] = sum(1 for l in layers.values() if l == layer)
            
        # Position nodes within layers
        layer_positions = {}
        for layer in range(max_layer + 1):
            layer_positions[layer] = 0
            
        for node in nodes:
            layer = layers.get(node.id, 0)
            count = layer_counts[layer]
            position = layer_positions[layer]
            
            # Calculate x,y coordinates
            y = 1.0 - 2.0 * layer / max(1, max_layer)
            x = -1.0 + 2.0 * position / max(1, count - 1) if count > 1 else 0
            
            self.layout_cache[node.id] = (x, y, 0.0)
            layer_positions[layer] += 1
            
    def _draw_nodes(self, ax: plt.Axes, use_3d: bool = False, 
                   animate: bool = False, highlight_active: bool = False) -> None:
        """
        Draw nodes on the axes.
        
        Args:
            ax: Matplotlib axes to draw on
            use_3d: Whether to use 3D visualization
            animate: Whether to animate the visualization
            highlight_active: Whether to highlight active nodes
        """
        nodes = self.architecture.nodes
        
        for node in nodes:
            # Get node position
            if node.id in self.layout_cache:
                x, y, z = self.layout_cache[node.id]
            else:
                x, y, z = node.position
                
            # Get node style
            size = node.size * 0.2
            color = node.color
            
            # Apply custom style if available
            if node.id in self.custom_node_styles:
                style = self.custom_node_styles[node.id]
                if "size" in style:
                    size = style["size"]
                if "color" in style:
                    color = style["color"]
                    
            # Apply highlighting
            alpha = 0.7
            edgecolor = "white"
            if node.id in self.highlighted_nodes:
                alpha = 1.0
                size *= 1.2
                edgecolor = "#00c2c7"
                
            # Draw node
            if use_3d:
                ax.scatter(x, y, z, s=size*1000, color=color, alpha=alpha, 
                           edgecolors=edgecolor, linewidths=2)
                ax.text(x, y, z, node.name, color="white", 
                        ha="center", va="center", fontsize=8)
            else:
                circle = plt.Circle((x, y), size, color=color, alpha=alpha, 
                                    edgecolor=edgecolor, linewidth=2, zorder=10)
                ax.add_patch(circle)
                ax.text(x, y, node.name, color="white", 
                        ha="center", va="center", fontsize=8, zorder=11)
                        
    def _draw_connections(self, ax: plt.Axes, use_3d: bool = False,
                         animate: bool = False, highlight_active: bool = False) -> None:
        """
        Draw connections on the axes.
        
        Args:
            ax: Matplotlib axes to draw on
            use_3d: Whether to use 3D visualization
            animate: Whether to animate the visualization
            highlight_active: Whether to highlight active nodes
        """
        connections = self.architecture.connections
        
        for conn in connections:
            # Skip if nodes are missing
            if conn.source_id not in self.layout_cache or conn.target_id not in self.layout_cache:
                continue
                
            # Get node positions
            source_x, source_y, source_z = self.layout_cache[conn.source_id]
            target_x, target_y, target_z = self.layout_cache[conn.target_id]
            
            # Get connection style
            color = "#2c3e50"  # Default connection color
            width = conn.strength * 2
            alpha = 0.6
            linestyle = "-"
            
            # Adjust style based on connection type
            if conn.type == ConnectionType.EXCITATORY:
                color = "#42f584"  # Green
            elif conn.type == ConnectionType.INHIBITORY:
                color = "#f54242"  # Red
                linestyle = "--"
            elif conn.type == ConnectionType.MODULATORY:
                color = "#42d7f5"  # Cyan
                linestyle = "-."
            elif conn.type == ConnectionType.BIDIRECTIONAL:
                color = "#f5a742"  # Orange
                
            # Apply custom style if available
            if conn.id in self.custom_connection_styles:
                style = self.custom_connection_styles[conn.id]
                if "color" in style:
                    color = style["color"]
                if "width" in style:
                    width = style["width"]
                if "linestyle" in style:
                    linestyle = style["linestyle"]
                    
            # Apply highlighting
            if conn.id in self.highlighted_connections:
                alpha = 1.0
                width *= 1.5
                
            # Draw connection
            if use_3d:
                ax.plot([source_x, target_x], [source_y, target_y], [source_z, target_z],
                        color=color, linewidth=width, alpha=alpha, linestyle=linestyle)
            else:
                # For bidirectional connections, add a curve
                if conn.type == ConnectionType.BIDIRECTIONAL:
                    # Calculate midpoint with offset
                    mid_x = (source_x + target_x) / 2
                    mid_y = (source_y + target_y) / 2
                    
                    # Calculate perpendicular offset
                    dx = target_x - source_x
                    dy = target_y - source_y
                    length = math.sqrt(dx*dx + dy*dy)
                    
                    if length > 0:
                        offset_x = -dy / length * 0.2
                        offset_y = dx / length * 0.2
                        
                        mid_x += offset_x
                        mid_y += offset_y
                        
                    # Create curved path
                    verts = [
                        (source_x, source_y),
                        (mid_x, mid_y),
                        (target_x, target_y)
                    ]
                    codes = [Path.MOVETO, Path.CURVE3, Path.CURVE3]
                    path = Path(verts, codes)
                    
                    # Draw path
                    patch = patches.PathPatch(path, facecolor="none", edgecolor=color,
                                             linewidth=width, alpha=alpha, linestyle=linestyle,
                                             zorder=5)
                    ax.add_patch(patch)
                    
                    # Add arrowhead at both ends
                    self._add_arrow(ax, source_x, source_y, mid_x, mid_y, color, width, alpha)
                    self._add_arrow(ax, target_x, target_y, mid_x, mid_y, color, width, alpha)
                else:
                    # Draw straight line with arrow
                    ax.plot([source_x, target_x], [source_y, target_y],
                           color=color, linewidth=width, alpha=alpha, linestyle=linestyle,
                           zorder=5)
                    
                    # Add arrowhead
                    self._add_arrow(ax, source_x, source_y, target_x, target_y, color, width, alpha)
                    
    def _add_arrow(self, ax: plt.Axes, x1: float, y1: float, x2: float, y2: float,
                 color: str, width: float, alpha: float) -> None:
        """
        Add an arrowhead to a line.
        
        Args:
            ax: Matplotlib axes
            x1, y1: Start point
            x2, y2: End point
            color: Arrow color
            width: Line width
            alpha: Transparency
        """
        # Calculate direction vector
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx*dx + dy*dy)
        
        if length < 0.01:
            return
            
        # Normalize
        dx /= length
        dy /= length
        
        # Calculate arrow points
        arrow_size = 0.1 * width
        arrow_x = x2 - dx * arrow_size * 2
        arrow_y = y2 - dy * arrow_size * 2
        
        # Perpendicular vector
        perp_x = -dy
        perp_y = dx
        
        # Arrow points
        left_x = arrow_x + perp_x * arrow_size
        left_y = arrow_y + perp_y * arrow_size
        right_x = arrow_x - perp_x * arrow_size
        right_y = arrow_y - perp_y * arrow_size
        
        # Draw arrow
        arrow = plt.Polygon([[x2, y2], [left_x, left_y], [right_x, right_y]],
                           closed=True, color=color, alpha=alpha, zorder=6)
        ax.add_patch(arrow)
        
    def _configure_axes(self, ax: plt.Axes, use_3d: bool = False) -> None:
        """
        Configure axes appearance.
        
        Args:
            ax: Matplotlib axes
            use_3d: Whether this is a 3D plot
        """
        # Set limits
        if use_3d:
            ax.set_xlim(-1.5, 1.5)
            ax.set_ylim(-1.5, 1.5)
            ax.set_zlim(-1.5, 1.5)
        else:
            ax.set_xlim(-1.5, 1.5)
            ax.set_ylim(-1.5, 1.5)
            
        # Set equal aspect ratio
        if not use_3d:
            ax.set_aspect('equal')
            
        # Remove axis labels
        ax.set_xticks([])
        ax.set_yticks([])
        if use_3d:
            ax.set_zticks([])
            
        # Set dark background
        ax.set_facecolor('#0a0d16')
        
        # Set title
        if self.architecture.name:
            ax.set_title(self.architecture.name, color='white', fontsize=14)
            
    def highlight_node(self, node_id: str, highlight: bool = True) -> None:
        """
        Highlight or unhighlight a node.
        
        Args:
            node_id: ID of the node to highlight
            highlight: Whether to highlight or unhighlight
        """
        if highlight:
            self.highlighted_nodes.add(node_id)
        else:
            self.highlighted_nodes.discard(node_id)
            
    def highlight_connection(self, connection_id: str, highlight: bool = True) -> None:
        """
        Highlight or unhighlight a connection.
        
        Args:
            connection_id: ID of the connection to highlight
            highlight: Whether to highlight or unhighlight
        """
        if highlight:
            self.highlighted_connections.add(connection_id)
        else:
            self.highlighted_connections.discard(connection_id)
            
    def clear_highlights(self) -> None:
        """Clear all highlighting."""
        self.highlighted_nodes.clear()
        self.highlighted_connections.clear()
        
    def set_node_style(self, node_id: str, style: Dict[str, Any]) -> None:
        """
        Set custom style for a node.
        
        Args:
            node_id: ID of the node
            style: Style dictionary with properties like color, size, etc.
        """
        self.custom_node_styles[node_id] = style
        
    def set_connection_style(self, connection_id: str, style: Dict[str, Any]) -> None:
        """
        Set custom style for a connection.
        
        Args:
            connection_id: ID of the connection
            style: Style dictionary with properties like color, width, etc.
        """
        self.custom_connection_styles[connection_id] = style
        
    def clear_custom_styles(self) -> None:
        """Clear all custom styles."""
        self.custom_node_styles.clear()
        self.custom_connection_styles.clear()
        
    def generate_color_palette(self, num_colors: int) -> List[str]:
        """
        Generate a color palette.
        
        Args:
            num_colors: Number of colors to generate
            
        Returns:
            List of hex color codes
        """
        palette = []
        
        for i in range(num_colors):
            hue = i / num_colors
            sat = 0.8
            val = 0.9
            
            r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
            color = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
            
            palette.append(color)
            
        return palette
        
    def color_nodes_by_type(self) -> None:
        """Color nodes by their type."""
        # Get unique node types
        node_types = set(node.type for node in self.architecture.nodes)
        
        # Generate colors
        colors = self.generate_color_palette(len(node_types))
        
        # Create type to color mapping
        type_colors = {}
        for i, node_type in enumerate(node_types):
            type_colors[node_type] = colors[i % len(colors)]
            
        # Set node colors
        for node in self.architecture.nodes:
            if node.type in type_colors:
                node_id = node.id
                self.set_node_style(node_id, {"color": type_colors[node.type]})
                
    def export_image(self, filepath: str, dpi: int = 300, 
                    use_3d: bool = False, figsize: Tuple[int, int] = (10, 8)) -> bool:
        """
        Export the node graph as an image.
        
        Args:
            filepath: Path to save the image
            dpi: Image resolution
            use_3d: Whether to use 3D visualization
            figsize: Figure size in inches
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create figure
            fig = plt.figure(figsize=figsize, facecolor='#0a0d16')
            
            # Create axes
            if use_3d:
                ax = fig.add_subplot(111, projection='3d')
            else:
                ax = fig.add_subplot(111)
                
            # Draw the graph
            self.draw(ax, use_3d=use_3d)
            
            # Save the figure
            plt.tight_layout()
            plt.savefig(filepath, dpi=dpi, facecolor='#0a0d16', edgecolor='none')
            plt.close(fig)
            
            return True
        except Exception as e:
            logger.error(f"Failed to export image: {e}")
            return False