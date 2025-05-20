"""
Architecture Editor UI components for RFM Architecture.

This module provides UI components for editing and visualizing
node system architectures using Dear PyGui.
"""

import os
import sys
import uuid
import time
import logging
import json
from typing import Dict, List, Tuple, Optional, Set, Any, Callable, Union
import math

import dearpygui.dearpygui as dpg
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg

from rfm_ui.theme import Colors, Spacing, Motion
from rfm_ui.components.panel import GlassPanel, CardPanel
from rfm_ui.errors import error_boundary

from rfm.core.node_system_base import (
    Node, Connection, Architecture, 
    NodeType, ConnectionType, EmotionalState,
    create_default_architecture, create_rfm_architecture
)
from rfm.core.node_graph import NodeGraph

logger = logging.getLogger(__name__)


class NodeEditor:
    """
    Editor component for creating and editing architecture nodes.
    
    This component provides UI controls for adding, editing, and removing
    nodes in an architecture.
    """
    
    def __init__(self, 
                parent_id: int,
                architecture: Optional[Architecture] = None,
                on_architecture_change: Optional[Callable[[Architecture], None]] = None,
                width: int = -1,
                tag: Optional[str] = None):
        """
        Initialize the node editor.
        
        Args:
            parent_id: DearPyGui ID of the parent container
            architecture: Optional architecture to edit
            on_architecture_change: Callback for architecture changes
            width: Width of the editor
            tag: Optional tag for the component
        """
        self.parent_id = parent_id
        self.architecture = architecture or Architecture()
        self.on_architecture_change = on_architecture_change
        self.width = width
        self.tag = tag or f"node_editor_{uuid.uuid4()}"
        
        # UI state
        self.selected_node_id: Optional[str] = None
        self.panel: Optional[GlassPanel] = None
        self.editor_container_id: Optional[int] = None
        self.node_list_id: Optional[int] = None
        
        # Create the panel
        self._create_panel()
        
    def _create_panel(self) -> None:
        """Create the editor panel."""
        # Create a glass panel for the editor
        self.panel = GlassPanel(
            parent_id=self.parent_id,
            label="Node Editor",
            width=self.width,
            height=-1,
            show_title_bar=True,
            tag=self.tag
        )
        
        # Get panel ID
        panel_id = self.panel.get_panel_id()
        
        # Create the editor UI
        with dpg.group(parent=panel_id, horizontal=False) as self.editor_container_id:
            # Add node toolbar
            with dpg.group(horizontal=True):
                # Add new node button
                dpg.add_button(
                    label="Add Node",
                    callback=self._on_add_node_clicked,
                    width=100
                )
                
                # Remove node button
                dpg.add_button(
                    label="Remove Node",
                    callback=self._on_remove_node_clicked,
                    width=100
                )
                
                # Duplicate node button
                dpg.add_button(
                    label="Duplicate",
                    callback=self._on_duplicate_node_clicked,
                    width=100
                )
                
            # Add separator
            dpg.add_separator()
            
            # Split into left and right columns
            with dpg.group(horizontal=True):
                # Left column: Node list
                with dpg.child_window(width=200, height=300):
                    # Add node list
                    dpg.add_text("Nodes")
                    self.node_list_id = dpg.add_listbox(
                        items=[],
                        width=-1,
                        num_items=10,
                        callback=self._on_node_selected
                    )
                
                # Right column: Node details
                with dpg.child_window(width=-1, height=300):
                    # Node details form
                    with dpg.group(horizontal=False, tag=f"{self.tag}_details_form"):
                        dpg.add_text("Node Details")
                        
                        # Name input
                        dpg.add_text("Name")
                        dpg.add_input_text(
                            tag=f"{self.tag}_name_input",
                            width=-1,
                            callback=self._on_node_name_changed
                        )
                        
                        # Type dropdown
                        dpg.add_text("Type")
                        dpg.add_combo(
                            items=[t.value for t in NodeType],
                            default_value=NodeType.STANDARD.value,
                            width=-1,
                            tag=f"{self.tag}_type_combo",
                            callback=self._on_node_type_changed
                        )
                        
                        # Description input
                        dpg.add_text("Description")
                        dpg.add_input_text(
                            multiline=True,
                            width=-1,
                            height=80,
                            tag=f"{self.tag}_description_input",
                            callback=self._on_node_description_changed
                        )
                        
                        # Position inputs
                        dpg.add_text("Position")
                        with dpg.group(horizontal=True):
                            dpg.add_input_float(
                                label="X",
                                width=60,
                                default_value=0.0,
                                tag=f"{self.tag}_pos_x_input",
                                callback=self._on_node_position_changed,
                                step=0.1,
                                format="%.2f"
                            )
                            dpg.add_input_float(
                                label="Y",
                                width=60,
                                default_value=0.0,
                                tag=f"{self.tag}_pos_y_input",
                                callback=self._on_node_position_changed,
                                step=0.1,
                                format="%.2f"
                            )
                            dpg.add_input_float(
                                label="Z",
                                width=60,
                                default_value=0.0,
                                tag=f"{self.tag}_pos_z_input",
                                callback=self._on_node_position_changed,
                                step=0.1,
                                format="%.2f"
                            )
                            
                        # Color picker
                        dpg.add_text("Color")
                        dpg.add_color_edit(
                            tag=f"{self.tag}_color_picker",
                            default_value=self._hex_to_rgba("#42d7f5"),
                            callback=self._on_node_color_changed,
                            alpha_bar=True
                        )
                        
                        # Size slider
                        dpg.add_text("Size")
                        dpg.add_slider_float(
                            tag=f"{self.tag}_size_slider",
                            default_value=1.0,
                            min_value=0.1,
                            max_value=3.0,
                            width=-1,
                            callback=self._on_node_size_changed,
                            format="%.2f"
                        )
            
        # Update the node list
        self._update_node_list()
        
        # Disable details initially
        self._enable_details_form(False)
        
    def _update_node_list(self) -> None:
        """Update the node list with current nodes."""
        if not self.node_list_id or not dpg.does_item_exist(self.node_list_id):
            return
            
        # Get node names
        node_items = []
        for node in self.architecture.nodes:
            name = node.name or f"Node {node.id[:6]}"
            node_items.append(name)
            
        # Update listbox
        dpg.configure_item(self.node_list_id, items=node_items)
        
        # Update selected node if needed
        if self.selected_node_id:
            # Find index of selected node
            selected_index = next(
                (i for i, node in enumerate(self.architecture.nodes) 
                 if node.id == self.selected_node_id),
                -1
            )
            
            if selected_index >= 0:
                dpg.set_value(self.node_list_id, node_items[selected_index])
                
    def _update_details_form(self) -> None:
        """Update the details form with selected node data."""
        if not self.selected_node_id:
            return
            
        # Find selected node
        node = self.architecture.get_node(self.selected_node_id)
        if not node:
            return
            
        # Update form fields
        dpg.set_value(f"{self.tag}_name_input", node.name)
        dpg.set_value(f"{self.tag}_type_combo", node.type.value if isinstance(node.type, NodeType) else node.type)
        dpg.set_value(f"{self.tag}_description_input", node.description)
        
        # Update position
        if node.position:
            dpg.set_value(f"{self.tag}_pos_x_input", node.position[0])
            dpg.set_value(f"{self.tag}_pos_y_input", node.position[1])
            dpg.set_value(f"{self.tag}_pos_z_input", node.position[2])
            
        # Update color
        dpg.set_value(f"{self.tag}_color_picker", self._hex_to_rgba(node.color))
        
        # Update size
        dpg.set_value(f"{self.tag}_size_slider", node.size)
        
    def _enable_details_form(self, enable: bool = True) -> None:
        """Enable or disable the details form."""
        form_items = dpg.get_item_children(f"{self.tag}_details_form", 1)
        
        for item in form_items:
            # Skip text items
            if dpg.get_item_type(item) == "mvAppItemType::mvText":
                continue
                
            dpg.configure_item(item, enabled=enable)
            
    @error_boundary
    def _on_add_node_clicked(self, sender, app_data) -> None:
        """Handle add node button click."""
        # Create a new node
        node = Node(
            id=str(uuid.uuid4()),
            name=f"Node {len(self.architecture.nodes) + 1}",
            type=NodeType.STANDARD,
            position=(0.0, 0.0, 0.0),
            color="#42d7f5",
            size=1.0
        )
        
        # Add to architecture
        self.architecture.add_node(node)
        
        # Update UI
        self._update_node_list()
        
        # Select the new node
        self._select_node(node.id)
        
        # Notify of change
        if self.on_architecture_change:
            self.on_architecture_change(self.architecture)
            
    @error_boundary
    def _on_remove_node_clicked(self, sender, app_data) -> None:
        """Handle remove node button click."""
        if not self.selected_node_id:
            return
            
        # Remove node from architecture
        self.architecture.remove_node(self.selected_node_id)
        
        # Clear selection
        self.selected_node_id = None
        
        # Update UI
        self._update_node_list()
        
        # Disable details form
        self._enable_details_form(False)
        
        # Notify of change
        if self.on_architecture_change:
            self.on_architecture_change(self.architecture)
            
    @error_boundary
    def _on_duplicate_node_clicked(self, sender, app_data) -> None:
        """Handle duplicate node button click."""
        if not self.selected_node_id:
            return
            
        # Find selected node
        node = self.architecture.get_node(self.selected_node_id)
        if not node:
            return
            
        # Create a copy with a new ID
        node_dict = node.to_dict()
        node_dict["id"] = str(uuid.uuid4())
        node_dict["name"] = f"{node.name} Copy"
        
        # Offset position slightly
        if node.position:
            x, y, z = node.position
            node_dict["position"] = (x + 0.2, y + 0.2, z)
            
        new_node = Node.from_dict(node_dict)
        
        # Add to architecture
        self.architecture.add_node(new_node)
        
        # Update UI
        self._update_node_list()
        
        # Select the new node
        self._select_node(new_node.id)
        
        # Notify of change
        if self.on_architecture_change:
            self.on_architecture_change(self.architecture)
            
    @error_boundary
    def _on_node_selected(self, sender, app_data) -> None:
        """Handle node selection from list."""
        if not app_data:
            return
            
        # Find the selected node
        selected_index = dpg.get_value(self.node_list_id)
        
        if 0 <= selected_index < len(self.architecture.nodes):
            # Get the node ID
            node_id = self.architecture.nodes[selected_index].id
            
            # Select the node
            self._select_node(node_id)
            
    def _select_node(self, node_id: str) -> None:
        """Select a node by ID."""
        # Set selected node
        self.selected_node_id = node_id
        
        # Enable details form
        self._enable_details_form(True)
        
        # Update details form
        self._update_details_form()
        
    @error_boundary
    def _on_node_name_changed(self, sender, app_data) -> None:
        """Handle node name change."""
        if not self.selected_node_id:
            return
            
        # Update node
        self.architecture.update_node(self.selected_node_id, {"name": app_data})
        
        # Update node list
        self._update_node_list()
        
        # Notify of change
        if self.on_architecture_change:
            self.on_architecture_change(self.architecture)
            
    @error_boundary
    def _on_node_type_changed(self, sender, app_data) -> None:
        """Handle node type change."""
        if not self.selected_node_id:
            return
            
        # Update node
        self.architecture.update_node(self.selected_node_id, {"type": app_data})
        
        # Notify of change
        if self.on_architecture_change:
            self.on_architecture_change(self.architecture)
            
    @error_boundary
    def _on_node_description_changed(self, sender, app_data) -> None:
        """Handle node description change."""
        if not self.selected_node_id:
            return
            
        # Update node
        self.architecture.update_node(self.selected_node_id, {"description": app_data})
        
        # Notify of change
        if self.on_architecture_change:
            self.on_architecture_change(self.architecture)
            
    @error_boundary
    def _on_node_position_changed(self, sender, app_data) -> None:
        """Handle node position change."""
        if not self.selected_node_id:
            return
            
        # Get current values
        x = dpg.get_value(f"{self.tag}_pos_x_input")
        y = dpg.get_value(f"{self.tag}_pos_y_input")
        z = dpg.get_value(f"{self.tag}_pos_z_input")
        
        # Update node
        self.architecture.update_node(self.selected_node_id, {"position": (x, y, z)})
        
        # Notify of change
        if self.on_architecture_change:
            self.on_architecture_change(self.architecture)
            
    @error_boundary
    def _on_node_color_changed(self, sender, app_data) -> None:
        """Handle node color change."""
        if not self.selected_node_id:
            return
            
        # Convert to hex color
        color_hex = self._rgba_to_hex(app_data)
        
        # Update node
        self.architecture.update_node(self.selected_node_id, {"color": color_hex})
        
        # Notify of change
        if self.on_architecture_change:
            self.on_architecture_change(self.architecture)
            
    @error_boundary
    def _on_node_size_changed(self, sender, app_data) -> None:
        """Handle node size change."""
        if not self.selected_node_id:
            return
            
        # Update node
        self.architecture.update_node(self.selected_node_id, {"size": app_data})
        
        # Notify of change
        if self.on_architecture_change:
            self.on_architecture_change(self.architecture)
            
    def _hex_to_rgba(self, hex_color: str) -> List[int]:
        """
        Convert hex color to RGBA.
        
        Args:
            hex_color: Hex color string (#RRGGBB or #RRGGBBAA)
            
        Returns:
            List of [r, g, b, a] values (0-255)
        """
        hex_color = hex_color.lstrip('#')
        
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            a = 255
        elif len(hex_color) == 8:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            a = int(hex_color[6:8], 16)
        else:
            # Default to cyan
            r, g, b, a = 66, 215, 245, 255
            
        return [r, g, b, a]
    
    def _rgba_to_hex(self, rgba: List[int]) -> str:
        """
        Convert RGBA to hex color.
        
        Args:
            rgba: List of [r, g, b, a] values (0-255)
            
        Returns:
            Hex color string (#RRGGBB)
        """
        r, g, b, a = rgba
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def set_architecture(self, architecture: Architecture) -> None:
        """
        Set the architecture to edit.
        
        Args:
            architecture: Architecture to edit
        """
        self.architecture = architecture
        
        # Clear selection
        self.selected_node_id = None
        
        # Update UI
        self._update_node_list()
        
        # Disable details form
        self._enable_details_form(False)
        
    def show(self) -> None:
        """Show the node editor."""
        if self.panel:
            self.panel.show()
            
    def hide(self) -> None:
        """Hide the node editor."""
        if self.panel:
            self.panel.hide()
            
    def toggle_visibility(self) -> None:
        """Toggle visibility of the node editor."""
        if self.panel:
            self.panel.toggle_visibility()


class ConnectionEditor:
    """
    Editor component for creating and editing connections between nodes.
    
    This component provides UI controls for adding, editing, and removing
    connections in an architecture.
    """
    
    def __init__(self, 
                parent_id: int,
                architecture: Optional[Architecture] = None,
                on_architecture_change: Optional[Callable[[Architecture], None]] = None,
                width: int = -1,
                tag: Optional[str] = None):
        """
        Initialize the connection editor.
        
        Args:
            parent_id: DearPyGui ID of the parent container
            architecture: Optional architecture to edit
            on_architecture_change: Callback for architecture changes
            width: Width of the editor
            tag: Optional tag for the component
        """
        self.parent_id = parent_id
        self.architecture = architecture or Architecture()
        self.on_architecture_change = on_architecture_change
        self.width = width
        self.tag = tag or f"connection_editor_{uuid.uuid4()}"
        
        # UI state
        self.selected_connection_id: Optional[str] = None
        self.panel: Optional[GlassPanel] = None
        self.editor_container_id: Optional[int] = None
        self.connection_list_id: Optional[int] = None
        
        # Create the panel
        self._create_panel()
        
    def _create_panel(self) -> None:
        """Create the editor panel."""
        # Create a glass panel for the editor
        self.panel = GlassPanel(
            parent_id=self.parent_id,
            label="Connection Editor",
            width=self.width,
            height=-1,
            show_title_bar=True,
            tag=self.tag
        )
        
        # Get panel ID
        panel_id = self.panel.get_panel_id()
        
        # Create the editor UI
        with dpg.group(parent=panel_id, horizontal=False) as self.editor_container_id:
            # Add connection toolbar
            with dpg.group(horizontal=True):
                # Add new connection button
                dpg.add_button(
                    label="Add Connection",
                    callback=self._on_add_connection_clicked,
                    width=120
                )
                
                # Remove connection button
                dpg.add_button(
                    label="Remove Connection",
                    callback=self._on_remove_connection_clicked,
                    width=120
                )
                
            # Add separator
            dpg.add_separator()
            
            # Split into left and right columns
            with dpg.group(horizontal=True):
                # Left column: Connection list
                with dpg.child_window(width=200, height=300):
                    # Add connection list
                    dpg.add_text("Connections")
                    self.connection_list_id = dpg.add_listbox(
                        items=[],
                        width=-1,
                        num_items=10,
                        callback=self._on_connection_selected
                    )
                
                # Right column: Connection details
                with dpg.child_window(width=-1, height=300):
                    # Connection details form
                    with dpg.group(horizontal=False, tag=f"{self.tag}_details_form"):
                        dpg.add_text("Connection Details")
                        
                        # Source node dropdown
                        dpg.add_text("Source Node")
                        dpg.add_combo(
                            items=[],
                            width=-1,
                            tag=f"{self.tag}_source_combo",
                            callback=self._on_connection_source_changed
                        )
                        
                        # Target node dropdown
                        dpg.add_text("Target Node")
                        dpg.add_combo(
                            items=[],
                            width=-1,
                            tag=f"{self.tag}_target_combo",
                            callback=self._on_connection_target_changed
                        )
                        
                        # Connection type
                        dpg.add_text("Type")
                        dpg.add_combo(
                            items=[t.value for t in ConnectionType],
                            default_value=ConnectionType.STANDARD.value,
                            width=-1,
                            tag=f"{self.tag}_type_combo",
                            callback=self._on_connection_type_changed
                        )
                        
                        # Connection strength
                        dpg.add_text("Strength")
                        dpg.add_slider_float(
                            tag=f"{self.tag}_strength_slider",
                            default_value=1.0,
                            min_value=0.1,
                            max_value=2.0,
                            width=-1,
                            callback=self._on_connection_strength_changed,
                            format="%.2f"
                        )
            
        # Update the connection list
        self._update_connection_list()
        
        # Disable details initially
        self._enable_details_form(False)
        
    def _update_connection_list(self) -> None:
        """Update the connection list with current connections."""
        if not self.connection_list_id or not dpg.does_item_exist(self.connection_list_id):
            return
            
        # Get connection names
        connection_items = []
        for conn in self.architecture.connections:
            # Get source and target nodes
            source_node = self.architecture.get_node(conn.source_id)
            target_node = self.architecture.get_node(conn.target_id)
            
            source_name = source_node.name if source_node else "Unknown"
            target_name = target_node.name if target_node else "Unknown"
            
            connection_items.append(f"{source_name} → {target_name}")
            
        # Update listbox
        dpg.configure_item(self.connection_list_id, items=connection_items)
        
        # Update node dropdowns
        self._update_node_dropdowns()
        
        # Update selected connection if needed
        if self.selected_connection_id:
            # Find index of selected connection
            selected_index = next(
                (i for i, conn in enumerate(self.architecture.connections) 
                 if conn.id == self.selected_connection_id),
                -1
            )
            
            if selected_index >= 0:
                dpg.set_value(self.connection_list_id, connection_items[selected_index])
                
    def _update_node_dropdowns(self) -> None:
        """Update the source and target node dropdowns."""
        # Get node names
        node_items = []
        node_ids = []
        
        for node in self.architecture.nodes:
            name = node.name or f"Node {node.id[:6]}"
            node_items.append(name)
            node_ids.append(node.id)
            
        # Update source dropdown
        if dpg.does_item_exist(f"{self.tag}_source_combo"):
            dpg.configure_item(f"{self.tag}_source_combo", items=node_items)
            
        # Update target dropdown
        if dpg.does_item_exist(f"{self.tag}_target_combo"):
            dpg.configure_item(f"{self.tag}_target_combo", items=node_items)
            
        # Store node IDs in user data
        if hasattr(self, "node_ids"):
            self.node_ids = node_ids
        else:
            setattr(self, "node_ids", node_ids)
            
    def _update_details_form(self) -> None:
        """Update the details form with selected connection data."""
        if not self.selected_connection_id:
            return
            
        # Find selected connection
        conn = self.architecture.get_connection(self.selected_connection_id)
        if not conn:
            return
            
        # Update form fields
        # Set source node
        if hasattr(self, "node_ids"):
            source_index = next(
                (i for i, node_id in enumerate(self.node_ids) 
                 if node_id == conn.source_id),
                -1
            )
            
            if source_index >= 0:
                dpg.set_value(f"{self.tag}_source_combo", source_index)
                
            # Set target node
            target_index = next(
                (i for i, node_id in enumerate(self.node_ids) 
                 if node_id == conn.target_id),
                -1
            )
            
            if target_index >= 0:
                dpg.set_value(f"{self.tag}_target_combo", target_index)
                
        # Set connection type
        dpg.set_value(
            f"{self.tag}_type_combo", 
            conn.type.value if isinstance(conn.type, ConnectionType) else conn.type
        )
        
        # Set connection strength
        dpg.set_value(f"{self.tag}_strength_slider", conn.strength)
        
    def _enable_details_form(self, enable: bool = True) -> None:
        """Enable or disable the details form."""
        form_items = dpg.get_item_children(f"{self.tag}_details_form", 1)
        
        for item in form_items:
            # Skip text items
            if dpg.get_item_type(item) == "mvAppItemType::mvText":
                continue
                
            dpg.configure_item(item, enabled=enable)
            
    @error_boundary
    def _on_add_connection_clicked(self, sender, app_data) -> None:
        """Handle add connection button click."""
        # Check if we have at least 2 nodes
        if len(self.architecture.nodes) < 2:
            # Show error message
            with dpg.window(label="Error", modal=True, width=300, height=100, pos=(400, 200)):
                dpg.add_text("Need at least 2 nodes to create a connection.")
                
                # OK button
                dpg.add_button(
                    label="OK",
                    callback=lambda: dpg.delete_item(dpg.get_item_parent(lambda s: dpg.delete_item(s)))
                )
                
            return
            
        # Create a new connection
        source_id = self.architecture.nodes[0].id
        target_id = self.architecture.nodes[1].id
        
        connection = Connection(
            id=str(uuid.uuid4()),
            source_id=source_id,
            target_id=target_id,
            type=ConnectionType.STANDARD,
            strength=1.0
        )
        
        # Add to architecture
        self.architecture.add_connection(connection)
        
        # Update UI
        self._update_connection_list()
        
        # Select the new connection
        self._select_connection(connection.id)
        
        # Notify of change
        if self.on_architecture_change:
            self.on_architecture_change(self.architecture)
            
    @error_boundary
    def _on_remove_connection_clicked(self, sender, app_data) -> None:
        """Handle remove connection button click."""
        if not self.selected_connection_id:
            return
            
        # Remove connection from architecture
        self.architecture.remove_connection(self.selected_connection_id)
        
        # Clear selection
        self.selected_connection_id = None
        
        # Update UI
        self._update_connection_list()
        
        # Disable details form
        self._enable_details_form(False)
        
        # Notify of change
        if self.on_architecture_change:
            self.on_architecture_change(self.architecture)
            
    @error_boundary
    def _on_connection_selected(self, sender, app_data) -> None:
        """Handle connection selection from list."""
        if not app_data:
            return
            
        # Find the selected connection
        selected_index = dpg.get_value(self.connection_list_id)
        
        if 0 <= selected_index < len(self.architecture.connections):
            # Get the connection ID
            connection_id = self.architecture.connections[selected_index].id
            
            # Select the connection
            self._select_connection(connection_id)
            
    def _select_connection(self, connection_id: str) -> None:
        """Select a connection by ID."""
        # Set selected connection
        self.selected_connection_id = connection_id
        
        # Enable details form
        self._enable_details_form(True)
        
        # Update details form
        self._update_details_form()
        
    @error_boundary
    def _on_connection_source_changed(self, sender, app_data) -> None:
        """Handle connection source change."""
        if not self.selected_connection_id or not hasattr(self, "node_ids"):
            return
            
        # Get source node ID
        if 0 <= app_data < len(self.node_ids):
            source_id = self.node_ids[app_data]
            
            # Update connection
            self.architecture.update_connection(
                self.selected_connection_id, 
                {"source_id": source_id}
            )
            
            # Update connection list
            self._update_connection_list()
            
            # Notify of change
            if self.on_architecture_change:
                self.on_architecture_change(self.architecture)
                
    @error_boundary
    def _on_connection_target_changed(self, sender, app_data) -> None:
        """Handle connection target change."""
        if not self.selected_connection_id or not hasattr(self, "node_ids"):
            return
            
        # Get target node ID
        if 0 <= app_data < len(self.node_ids):
            target_id = self.node_ids[app_data]
            
            # Update connection
            self.architecture.update_connection(
                self.selected_connection_id, 
                {"target_id": target_id}
            )
            
            # Update connection list
            self._update_connection_list()
            
            # Notify of change
            if self.on_architecture_change:
                self.on_architecture_change(self.architecture)
                
    @error_boundary
    def _on_connection_type_changed(self, sender, app_data) -> None:
        """Handle connection type change."""
        if not self.selected_connection_id:
            return
            
        # Update connection
        self.architecture.update_connection(
            self.selected_connection_id, 
            {"type": app_data}
        )
        
        # Notify of change
        if self.on_architecture_change:
            self.on_architecture_change(self.architecture)
            
    @error_boundary
    def _on_connection_strength_changed(self, sender, app_data) -> None:
        """Handle connection strength change."""
        if not self.selected_connection_id:
            return
            
        # Update connection
        self.architecture.update_connection(
            self.selected_connection_id, 
            {"strength": app_data}
        )
        
        # Notify of change
        if self.on_architecture_change:
            self.on_architecture_change(self.architecture)
            
    def set_architecture(self, architecture: Architecture) -> None:
        """
        Set the architecture to edit.
        
        Args:
            architecture: Architecture to edit
        """
        self.architecture = architecture
        
        # Clear selection
        self.selected_connection_id = None
        
        # Update UI
        self._update_connection_list()
        
        # Disable details form
        self._enable_details_form(False)
        
    def show(self) -> None:
        """Show the connection editor."""
        if self.panel:
            self.panel.show()
            
    def hide(self) -> None:
        """Hide the connection editor."""
        if self.panel:
            self.panel.hide()
            
    def toggle_visibility(self) -> None:
        """Toggle visibility of the connection editor."""
        if self.panel:
            self.panel.toggle_visibility()


class ArchitectureVisualizer:
    """
    Component for visualizing node architectures.
    
    This component provides a visual graph representation of the architecture.
    """
    
    def __init__(self, 
                parent_id: int,
                architecture: Optional[Architecture] = None,
                width: int = -1,
                height: int = 300,
                tag: Optional[str] = None):
        """
        Initialize the architecture visualizer.
        
        Args:
            parent_id: DearPyGui ID of the parent container
            architecture: Optional architecture to visualize
            width: Width of the visualizer
            height: Height of the visualizer
            tag: Optional tag for the component
        """
        self.parent_id = parent_id
        self.architecture = architecture or Architecture()
        self.width = width
        self.height = height
        self.tag = tag or f"arch_viz_{uuid.uuid4()}"
        
        # Visualization state
        self.node_graph = NodeGraph(self.architecture)
        self.selected_node_id: Optional[str] = None
        self.selected_connection_id: Optional[str] = None
        self.texture_id = f"{self.tag}_texture"
        self.container_id: Optional[int] = None
        self.image_id: Optional[int] = None
        self.last_architecture_id: Optional[str] = None
        self.last_update_time = 0
        self.need_update = True
        
        # Rendering parameters
        self.use_3d = False
        self.animate = False
        self.layout_method = "spring"
        
        # Initialize matplotlib
        matplotlib.use("agg")  # Use non-interactive backend
        
        # Create UI
        self._create_ui()
        
    def _create_ui(self) -> None:
        """Create the visualizer UI."""
        # Create container group
        with dpg.group(parent=self.parent_id, horizontal=False) as self.container_id:
            # Add toolbar
            with dpg.group(horizontal=True):
                # Layout method selector
                dpg.add_combo(
                    label="Layout",
                    items=["Spring", "Circular", "Hierarchical"],
                    default_value="Spring",
                    width=120,
                    callback=self._on_layout_changed
                )
                
                # 3D toggle
                dpg.add_checkbox(
                    label="3D View",
                    default_value=False,
                    callback=self._on_3d_toggled
                )
                
                # Animation toggle
                dpg.add_checkbox(
                    label="Animate",
                    default_value=False,
                    callback=self._on_animate_toggled
                )
                
                # Refresh button
                dpg.add_button(
                    label="Refresh",
                    callback=self._on_refresh_clicked
                )
                
                # Export button
                dpg.add_button(
                    label="Export",
                    callback=self._on_export_clicked
                )
                
            # Create texture for the visualization
            with dpg.texture_registry():
                dpg.add_raw_texture(
                    self.width, self.height, np.zeros((self.height, self.width, 4), dtype=np.float32),
                    format=dpg.mvFormat_Float_rgba,
                    tag=self.texture_id
                )
                
            # Add image display
            self.image_id = dpg.add_image(self.texture_id, width=self.width, height=self.height)
            
    def _render_architecture(self) -> None:
        """Render the architecture visualization."""
        # Skip if no architecture
        if not self.architecture or not self.architecture.nodes:
            return
            
        # Skip if not visible
        if not dpg.is_item_visible(self.container_id):
            return
            
        # Skip if no need to update
        if not self.need_update and self.architecture.id == self.last_architecture_id:
            # Check if architecture was modified
            if hasattr(self.architecture, "modified") and self.architecture.modified <= self.last_update_time:
                return
                
        # Create figure
        fig = plt.figure(figsize=(self.width / 100, self.height / 100), dpi=100, facecolor='#0a0d16')
        
        # Create axes based on view type
        if self.use_3d:
            ax = fig.add_subplot(111, projection='3d')
        else:
            ax = fig.add_subplot(111)
            
        # Draw architecture
        self.node_graph.set_architecture(self.architecture)
        
        # Highlight selected node and connection
        if self.selected_node_id:
            self.node_graph.highlight_node(self.selected_node_id)
            
        if self.selected_connection_id:
            self.node_graph.highlight_connection(self.selected_connection_id)
            
        # Draw the graph
        self.node_graph.draw(
            ax, 
            use_3d=self.use_3d, 
            animate=self.animate,
            layout_method=self.layout_method.lower()
        )
        
        # Convert figure to numpy array
        fig.tight_layout(pad=0)
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        
        # Get RGBA buffer
        buf = canvas.buffer_rgba()
        image_array = np.asarray(buf)
        
        # Convert to float32 normalized array (0-1)
        image_array = image_array.astype(np.float32) / 255.0
        
        # Update texture
        dpg.set_value(self.texture_id, image_array)
        
        # Close figure
        plt.close(fig)
        
        # Update state
        self.last_architecture_id = self.architecture.id
        self.last_update_time = time.time()
        self.need_update = False
        
        # Clear highlights
        self.node_graph.clear_highlights()
        
    def update(self) -> None:
        """Update the visualization."""
        self._render_architecture()
        
    @error_boundary
    def _on_layout_changed(self, sender, app_data) -> None:
        """Handle layout method change."""
        self.layout_method = app_data
        self.need_update = True
        self.update()
        
    @error_boundary
    def _on_3d_toggled(self, sender, app_data) -> None:
        """Handle 3D view toggle."""
        self.use_3d = app_data
        self.need_update = True
        self.update()
        
    @error_boundary
    def _on_animate_toggled(self, sender, app_data) -> None:
        """Handle animation toggle."""
        self.animate = app_data
        self.need_update = True
        self.update()
        
    @error_boundary
    def _on_refresh_clicked(self, sender, app_data) -> None:
        """Handle refresh button click."""
        self.need_update = True
        self.update()
        
    @error_boundary
    def _on_export_clicked(self, sender, app_data) -> None:
        """Handle export button click."""
        # Show file dialog
        with dpg.window(label="Export Architecture", modal=True, width=400, height=200, pos=(400, 200)):
            dialog_id = dpg.last_item()
            
            dpg.add_text("Export Options")
            
            # Filename input
            dpg.add_input_text(
                label="Filename",
                default_value="architecture.png",
                width=-1,
                tag=f"{self.tag}_export_filename"
            )
            
            # Image size
            with dpg.group(horizontal=True):
                dpg.add_input_int(
                    label="Width",
                    default_value=1600,
                    width=120,
                    tag=f"{self.tag}_export_width"
                )
                dpg.add_input_int(
                    label="Height",
                    default_value=1200,
                    width=120,
                    tag=f"{self.tag}_export_height"
                )
                
            # DPI
            dpg.add_input_int(
                label="DPI",
                default_value=300,
                width=120,
                tag=f"{self.tag}_export_dpi"
            )
            
            # Buttons
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Export",
                    callback=self._perform_export,
                    user_data=dialog_id
                )
                dpg.add_button(
                    label="Cancel",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=dialog_id
                )
                
    @error_boundary
    def _perform_export(self, sender, app_data, user_data) -> None:
        """Perform the export operation."""
        # Get export parameters
        filename = dpg.get_value(f"{self.tag}_export_filename")
        width = dpg.get_value(f"{self.tag}_export_width")
        height = dpg.get_value(f"{self.tag}_export_height")
        dpi = dpg.get_value(f"{self.tag}_export_dpi")
        
        # Export the image
        success = self.node_graph.export_image(
            filepath=filename,
            dpi=dpi,
            use_3d=self.use_3d,
            figsize=(width / dpi, height / dpi)
        )
        
        # Close dialog
        dpg.delete_item(user_data)
        
        # Show result
        if success:
            with dpg.window(label="Export Complete", modal=True, width=300, height=100, pos=(400, 200)):
                result_id = dpg.last_item()
                
                dpg.add_text(f"Successfully exported to {filename}")
                dpg.add_button(
                    label="OK",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=result_id
                )
        else:
            with dpg.window(label="Export Failed", modal=True, width=300, height=100, pos=(400, 200)):
                result_id = dpg.last_item()
                
                dpg.add_text(f"Failed to export to {filename}")
                dpg.add_button(
                    label="OK",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=result_id
                )
        
    def set_architecture(self, architecture: Architecture) -> None:
        """
        Set the architecture to visualize.
        
        Args:
            architecture: Architecture to visualize
        """
        self.architecture = architecture
        self.need_update = True
        self.update()
        
    def select_node(self, node_id: Optional[str]) -> None:
        """
        Select a node in the visualization.
        
        Args:
            node_id: ID of the node to select, or None to deselect
        """
        self.selected_node_id = node_id
        self.need_update = True
        self.update()
        
    def select_connection(self, connection_id: Optional[str]) -> None:
        """
        Select a connection in the visualization.
        
        Args:
            connection_id: ID of the connection to select, or None to deselect
        """
        self.selected_connection_id = connection_id
        self.need_update = True
        self.update()
        
    def resize(self, width: int, height: int) -> None:
        """
        Resize the visualization.
        
        Args:
            width: New width
            height: New height
        """
        self.width = width
        self.height = height
        
        # Update texture
        dpg.configure_item(
            self.texture_id,
            width=width,
            height=height,
            default_value=np.zeros((height, width, 4), dtype=np.float32)
        )
        
        # Update image
        if self.image_id and dpg.does_item_exist(self.image_id):
            dpg.configure_item(self.image_id, width=width, height=height)
            
        # Force update
        self.need_update = True
        self.update()


class ArchitectureEditor:
    """
    Integrated editor for creating and editing node architectures.
    
    This component combines the node editor, connection editor, and
    visualizer into a complete architecture editing environment.
    """
    
    def __init__(self, 
                parent_id: int,
                architecture: Optional[Architecture] = None,
                on_architecture_change: Optional[Callable[[Architecture], None]] = None,
                width: int = -1,
                height: int = -1,
                tag: Optional[str] = None):
        """
        Initialize the architecture editor.
        
        Args:
            parent_id: DearPyGui ID of the parent container
            architecture: Optional architecture to edit
            on_architecture_change: Callback for architecture changes
            width: Width of the editor
            height: Height of the editor
            tag: Optional tag for the component
        """
        self.parent_id = parent_id
        self.architecture = architecture or create_default_architecture()
        self.on_architecture_change = on_architecture_change
        self.width = width
        self.height = height
        self.tag = tag or f"arch_editor_{uuid.uuid4()}"
        
        # UI components
        self.panel: Optional[CardPanel] = None
        self.container_id: Optional[int] = None
        self.tab_bar_id: Optional[int] = None
        self.node_editor: Optional[NodeEditor] = None
        self.connection_editor: Optional[ConnectionEditor] = None
        self.visualizer: Optional[ArchitectureVisualizer] = None
        
        # Create the panel
        self._create_panel()
        
        # Timer for periodic updates
        self._register_update_timer()
        
    def _create_panel(self) -> None:
        """Create the editor panel."""
        # Create a card panel for the editor
        self.panel = CardPanel(
            parent_id=self.parent_id,
            label="Architecture Editor",
            width=self.width,
            height=self.height,
            show_title_bar=True,
            tag=self.tag
        )
        
        # Get panel ID
        panel_id = self.panel.get_panel_id()
        
        # Create toolbar
        with dpg.group(parent=panel_id, horizontal=True):
            # New button
            dpg.add_button(
                label="New",
                callback=self._on_new_clicked,
                width=80
            )
            
            # Open button
            dpg.add_button(
                label="Open",
                callback=self._on_open_clicked,
                width=80
            )
            
            # Save button
            dpg.add_button(
                label="Save",
                callback=self._on_save_clicked,
                width=80
            )
            
            # Reset button
            dpg.add_button(
                label="Reset",
                callback=self._on_reset_clicked,
                width=80
            )
            
            # Create RFM template button
            dpg.add_button(
                label="RFM Template",
                callback=self._on_rfm_clicked,
                width=100
            )
        
        # Add separator
        dpg.add_separator(parent=panel_id)
        
        # Create tab bar
        with dpg.tab_bar(parent=panel_id) as self.tab_bar_id:
            # Visualization tab
            with dpg.tab(label="Visualization"):
                viz_tab_id = dpg.last_item()
                
                # Create visualizer
                viz_width = self.width - 20 if self.width > 0 else 600
                viz_height = self.height - 100 if self.height > 0 else 400
                
                self.visualizer = ArchitectureVisualizer(
                    parent_id=viz_tab_id,
                    architecture=self.architecture,
                    width=viz_width,
                    height=viz_height
                )
                
            # Node editor tab
            with dpg.tab(label="Nodes"):
                node_tab_id = dpg.last_item()
                
                # Create node editor
                self.node_editor = NodeEditor(
                    parent_id=node_tab_id,
                    architecture=self.architecture,
                    on_architecture_change=self._on_arch_changed,
                    width=self.width - 20 if self.width > 0 else -1
                )
                
            # Connection editor tab
            with dpg.tab(label="Connections"):
                conn_tab_id = dpg.last_item()
                
                # Create connection editor
                self.connection_editor = ConnectionEditor(
                    parent_id=conn_tab_id,
                    architecture=self.architecture,
                    on_architecture_change=self._on_arch_changed,
                    width=self.width - 20 if self.width > 0 else -1
                )
                
    def _register_update_timer(self) -> None:
        """Register a timer for periodic updates."""
        # Add a timer for visualization updates
        with dpg.item_handler_registry() as handler:
            dpg.add_item_visible_handler(
                callback=lambda s, a: self._update_visualizer() if a else None
            )
            
        # Apply handler to visualizer if available
        if self.visualizer and hasattr(self.visualizer, "container_id"):
            dpg.bind_item_handler_registry(self.visualizer.container_id, handler)
            
    def _update_visualizer(self) -> None:
        """Update the architecture visualization."""
        if self.visualizer:
            self.visualizer.update()
            
    @error_boundary
    def _on_arch_changed(self, architecture: Architecture) -> None:
        """
        Handle architecture changes from child components.
        
        Args:
            architecture: Updated architecture
        """
        # Update our architecture
        self.architecture = architecture
        
        # Update other components
        if self.visualizer and self.visualizer.architecture != architecture:
            self.visualizer.set_architecture(architecture)
            
        if self.node_editor and self.node_editor.architecture != architecture:
            self.node_editor.set_architecture(architecture)
            
        if self.connection_editor and self.connection_editor.architecture != architecture:
            self.connection_editor.set_architecture(architecture)
            
        # Notify parent if needed
        if self.on_architecture_change:
            self.on_architecture_change(architecture)
            
    @error_boundary
    def _on_new_clicked(self, sender, app_data) -> None:
        """Handle new button click."""
        # Show confirmation dialog
        with dpg.window(label="New Architecture", modal=True, width=300, height=150, pos=(400, 200)):
            dialog_id = dpg.last_item()
            
            dpg.add_text("Create a new empty architecture?")
            dpg.add_text("This will discard any unsaved changes.")
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Yes",
                    callback=self._create_new_architecture,
                    user_data=dialog_id,
                    width=100
                )
                dpg.add_button(
                    label="No",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=dialog_id,
                    width=100
                )
                
    def _create_new_architecture(self, sender, app_data, user_data) -> None:
        """Create a new empty architecture."""
        # Close dialog
        dpg.delete_item(user_data)
        
        # Create new architecture
        self.architecture = Architecture(
            id=str(uuid.uuid4()),
            name="New Architecture",
            description="",
            nodes=[],
            connections=[]
        )
        
        # Update components
        self._on_arch_changed(self.architecture)
        
    @error_boundary
    def _on_open_clicked(self, sender, app_data) -> None:
        """Handle open button click."""
        # Show file input dialog
        with dpg.window(label="Open Architecture", modal=True, width=400, height=150, pos=(400, 200)):
            dialog_id = dpg.last_item()
            
            dpg.add_text("Enter the filepath to load:")
            dpg.add_input_text(
                tag=f"{self.tag}_open_filepath",
                width=-1,
                hint="architecture.json"
            )
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Load",
                    callback=self._load_architecture,
                    user_data=dialog_id,
                    width=100
                )
                dpg.add_button(
                    label="Cancel",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=dialog_id,
                    width=100
                )
                
    def _load_architecture(self, sender, app_data, user_data) -> None:
        """Load architecture from file."""
        # Get filepath
        filepath = dpg.get_value(f"{self.tag}_open_filepath")
        
        # Close dialog
        dpg.delete_item(user_data)
        
        # Load from file
        try:
            architecture = Architecture.load_from_file(filepath)
            
            if architecture:
                # Update state
                self.architecture = architecture
                
                # Update components
                self._on_arch_changed(self.architecture)
                
                # Show success message
                with dpg.window(label="Success", modal=True, width=300, height=100, pos=(400, 200)):
                    result_id = dpg.last_item()
                    
                    dpg.add_text(f"Successfully loaded from {filepath}")
                    dpg.add_button(
                        label="OK",
                        callback=lambda s, a, u: dpg.delete_item(u),
                        user_data=result_id
                    )
            else:
                # Show error message
                with dpg.window(label="Error", modal=True, width=300, height=100, pos=(400, 200)):
                    result_id = dpg.last_item()
                    
                    dpg.add_text(f"Failed to load from {filepath}")
                    dpg.add_button(
                        label="OK",
                        callback=lambda s, a, u: dpg.delete_item(u),
                        user_data=result_id
                    )
        except Exception as e:
            # Show error message
            with dpg.window(label="Error", modal=True, width=400, height=150, pos=(400, 200)):
                result_id = dpg.last_item()
                
                dpg.add_text(f"Error loading architecture: {str(e)}")
                dpg.add_button(
                    label="OK",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=result_id
                )
                
    @error_boundary
    def _on_save_clicked(self, sender, app_data) -> None:
        """Handle save button click."""
        # Show file input dialog
        with dpg.window(label="Save Architecture", modal=True, width=400, height=150, pos=(400, 200)):
            dialog_id = dpg.last_item()
            
            dpg.add_text("Enter the filepath to save:")
            dpg.add_input_text(
                tag=f"{self.tag}_save_filepath",
                width=-1,
                hint="architecture.json",
                default_value=f"{self.architecture.name.lower().replace(' ', '_')}.json"
            )
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Save",
                    callback=self._save_architecture,
                    user_data=dialog_id,
                    width=100
                )
                dpg.add_button(
                    label="Cancel",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=dialog_id,
                    width=100
                )
                
    def _save_architecture(self, sender, app_data, user_data) -> None:
        """Save architecture to file."""
        # Get filepath
        filepath = dpg.get_value(f"{self.tag}_save_filepath")
        
        # Close dialog
        dpg.delete_item(user_data)
        
        # Save to file
        success = self.architecture.save_to_file(filepath)
        
        # Show result
        if success:
            with dpg.window(label="Success", modal=True, width=300, height=100, pos=(400, 200)):
                result_id = dpg.last_item()
                
                dpg.add_text(f"Successfully saved to {filepath}")
                dpg.add_button(
                    label="OK",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=result_id
                )
        else:
            with dpg.window(label="Error", modal=True, width=300, height=100, pos=(400, 200)):
                result_id = dpg.last_item()
                
                dpg.add_text(f"Failed to save to {filepath}")
                dpg.add_button(
                    label="OK",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=result_id
                )
                
    @error_boundary
    def _on_reset_clicked(self, sender, app_data) -> None:
        """Handle reset button click."""
        # Show confirmation dialog
        with dpg.window(label="Reset Architecture", modal=True, width=300, height=150, pos=(400, 200)):
            dialog_id = dpg.last_item()
            
            dpg.add_text("Reset to default architecture?")
            dpg.add_text("This will discard any unsaved changes.")
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Yes",
                    callback=self._reset_architecture,
                    user_data=dialog_id,
                    width=100
                )
                dpg.add_button(
                    label="No",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=dialog_id,
                    width=100
                )
                
    def _reset_architecture(self, sender, app_data, user_data) -> None:
        """Reset to default architecture."""
        # Close dialog
        dpg.delete_item(user_data)
        
        # Create default architecture
        self.architecture = create_default_architecture()
        
        # Update components
        self._on_arch_changed(self.architecture)
        
    @error_boundary
    def _on_rfm_clicked(self, sender, app_data) -> None:
        """Handle RFM template button click."""
        # Create RFM architecture
        self.architecture = create_rfm_architecture()
        
        # Update components
        self._on_arch_changed(self.architecture)
        
    def set_architecture(self, architecture: Architecture) -> None:
        """
        Set the architecture to edit.
        
        Args:
            architecture: Architecture to edit
        """
        self.architecture = architecture
        
        # Update components
        self._on_arch_changed(architecture)


class EmotionalStateEditor:
    """
    Editor component for manipulating emotional state parameters.
    
    This component provides UI controls for adjusting emotional state
    parameters like arousal, valence, dominance, and certainty.
    """
    
    def __init__(self, 
                parent_id: int,
                emotional_state: Optional[EmotionalState] = None,
                on_state_change: Optional[Callable[[EmotionalState], None]] = None,
                width: int = -1,
                tag: Optional[str] = None):
        """
        Initialize the emotional state editor.
        
        Args:
            parent_id: DearPyGui ID of the parent container
            emotional_state: Optional initial emotional state
            on_state_change: Callback for state changes
            width: Width of the editor
            tag: Optional tag for the component
        """
        self.parent_id = parent_id
        self.emotional_state = emotional_state or EmotionalState()
        self.on_state_change = on_state_change
        self.width = width
        self.tag = tag or f"emotion_editor_{uuid.uuid4()}"
        
        # UI state
        self.panel: Optional[GlassPanel] = None
        self.editor_container_id: Optional[int] = None
        
        # Create the panel
        self._create_panel()
        
    def _create_panel(self) -> None:
        """Create the editor panel."""
        # Create a glass panel for the editor
        self.panel = GlassPanel(
            parent_id=self.parent_id,
            label="Emotional State Editor",
            width=self.width,
            height=-1,
            show_title_bar=True,
            tag=self.tag
        )
        
        # Get panel ID
        panel_id = self.panel.get_panel_id()
        
        # Create the editor UI
        with dpg.group(parent=panel_id, horizontal=False) as self.editor_container_id:
            # Add description
            dpg.add_text("Adjust emotional state parameters:")
            
            # Add sliders for emotional state parameters
            
            # Arousal slider
            dpg.add_text("Arousal (Activation Level)")
            dpg.add_slider_float(
                tag=f"{self.tag}_arousal_slider",
                default_value=self.emotional_state.arousal,
                min_value=0.0,
                max_value=1.0,
                width=-1,
                callback=self._on_arousal_changed,
                format="%.2f"
            )
            
            # Valence slider
            dpg.add_text("Valence (Positive/Negative)")
            dpg.add_slider_float(
                tag=f"{self.tag}_valence_slider",
                default_value=self.emotional_state.valence,
                min_value=-1.0,
                max_value=1.0,
                width=-1,
                callback=self._on_valence_changed,
                format="%.2f"
            )
            
            # Dominance slider
            dpg.add_text("Dominance (Control)")
            dpg.add_slider_float(
                tag=f"{self.tag}_dominance_slider",
                default_value=self.emotional_state.dominance,
                min_value=0.0,
                max_value=1.0,
                width=-1,
                callback=self._on_dominance_changed,
                format="%.2f"
            )
            
            # Certainty slider
            dpg.add_text("Certainty (Confidence)")
            dpg.add_slider_float(
                tag=f"{self.tag}_certainty_slider",
                default_value=self.emotional_state.certainty,
                min_value=0.0,
                max_value=1.0,
                width=-1,
                callback=self._on_certainty_changed,
                format="%.2f"
            )
            
            # Add preset selector
            dpg.add_separator()
            dpg.add_text("Presets")
            
            with dpg.group(horizontal=True):
                # Preset selection
                dpg.add_combo(
                    items=["Custom", "Neutral", "Happy", "Sad", "Angry", "Fearful", "Surprised", "Curious"],
                    default_value="Custom",
                    width=150,
                    callback=self._on_preset_selected
                )
                
                # Save preset button
                dpg.add_button(
                    label="Save Preset",
                    callback=self._on_save_preset_clicked,
                    width=100
                )
                
    @error_boundary
    def _on_arousal_changed(self, sender, app_data) -> None:
        """Handle arousal slider change."""
        # Update state
        self.emotional_state.arousal = app_data
        
        # Notify of change
        if self.on_state_change:
            self.on_state_change(self.emotional_state)
            
    @error_boundary
    def _on_valence_changed(self, sender, app_data) -> None:
        """Handle valence slider change."""
        # Update state
        self.emotional_state.valence = app_data
        
        # Notify of change
        if self.on_state_change:
            self.on_state_change(self.emotional_state)
            
    @error_boundary
    def _on_dominance_changed(self, sender, app_data) -> None:
        """Handle dominance slider change."""
        # Update state
        self.emotional_state.dominance = app_data
        
        # Notify of change
        if self.on_state_change:
            self.on_state_change(self.emotional_state)
            
    @error_boundary
    def _on_certainty_changed(self, sender, app_data) -> None:
        """Handle certainty slider change."""
        # Update state
        self.emotional_state.certainty = app_data
        
        # Notify of change
        if self.on_state_change:
            self.on_state_change(self.emotional_state)
            
    @error_boundary
    def _on_preset_selected(self, sender, app_data) -> None:
        """Handle preset selection."""
        # Apply preset
        if app_data == "Neutral":
            self._apply_preset(0.5, 0.0, 0.5, 0.5)
        elif app_data == "Happy":
            self._apply_preset(0.8, 0.9, 0.7, 0.8)
        elif app_data == "Sad":
            self._apply_preset(0.3, -0.7, 0.2, 0.4)
        elif app_data == "Angry":
            self._apply_preset(0.9, -0.8, 0.8, 0.7)
        elif app_data == "Fearful":
            self._apply_preset(0.8, -0.7, 0.1, 0.2)
        elif app_data == "Surprised":
            self._apply_preset(0.9, 0.3, 0.4, 0.2)
        elif app_data == "Curious":
            self._apply_preset(0.6, 0.5, 0.6, 0.3)
            
    def _apply_preset(self, arousal: float, valence: float, dominance: float, certainty: float) -> None:
        """
        Apply an emotional state preset.
        
        Args:
            arousal: Arousal value
            valence: Valence value
            dominance: Dominance value
            certainty: Certainty value
        """
        # Update sliders
        dpg.set_value(f"{self.tag}_arousal_slider", arousal)
        dpg.set_value(f"{self.tag}_valence_slider", valence)
        dpg.set_value(f"{self.tag}_dominance_slider", dominance)
        dpg.set_value(f"{self.tag}_certainty_slider", certainty)
        
        # Update state
        self.emotional_state.arousal = arousal
        self.emotional_state.valence = valence
        self.emotional_state.dominance = dominance
        self.emotional_state.certainty = certainty
        
        # Notify of change
        if self.on_state_change:
            self.on_state_change(self.emotional_state)
            
    @error_boundary
    def _on_save_preset_clicked(self, sender, app_data) -> None:
        """Handle save preset button click."""
        # Show dialog for preset name
        with dpg.window(label="Save Preset", modal=True, width=300, height=150, pos=(400, 200)):
            dialog_id = dpg.last_item()
            
            dpg.add_text("Enter preset name:")
            dpg.add_input_text(
                tag=f"{self.tag}_preset_name_input",
                width=-1
            )
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Save",
                    callback=self._save_preset,
                    user_data=dialog_id,
                    width=100
                )
                dpg.add_button(
                    label="Cancel",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=dialog_id,
                    width=100
                )
                
    def _save_preset(self, sender, app_data, user_data) -> None:
        """Save the current emotional state as a preset."""
        # Get preset name
        preset_name = dpg.get_value(f"{self.tag}_preset_name_input")
        
        # Close dialog
        dpg.delete_item(user_data)
        
        # In a real application, we would save the preset to a file or database
        # For now, just show a message
        with dpg.window(label="Preset Saved", modal=True, width=300, height=100, pos=(400, 200)):
            result_id = dpg.last_item()
            
            dpg.add_text(f"Preset '{preset_name}' saved!")
            dpg.add_button(
                label="OK",
                callback=lambda s, a, u: dpg.delete_item(u),
                user_data=result_id,
                width=100
            )
            
    def set_emotional_state(self, emotional_state: EmotionalState) -> None:
        """
        Set the emotional state to edit.
        
        Args:
            emotional_state: Emotional state to edit
        """
        self.emotional_state = emotional_state
        
        # Update sliders
        dpg.set_value(f"{self.tag}_arousal_slider", emotional_state.arousal)
        dpg.set_value(f"{self.tag}_valence_slider", emotional_state.valence)
        dpg.set_value(f"{self.tag}_dominance_slider", emotional_state.dominance)
        dpg.set_value(f"{self.tag}_certainty_slider", emotional_state.certainty)
        
    def show(self) -> None:
        """Show the emotional state editor."""
        if self.panel:
            self.panel.show()
            
    def hide(self) -> None:
        """Hide the emotional state editor."""
        if self.panel:
            self.panel.hide()
            
    def toggle_visibility(self) -> None:
        """Toggle visibility of the emotional state editor."""
        if self.panel:
            self.panel.toggle_visibility()