"""
Node-based animation sequencer for RFM Architecture UI.

This module provides a node editor interface for creating animation sequences.
"""
import os
import sys
import json
import logging
import math
import time
from enum import Enum
from typing import Dict, Any, List, Tuple, Optional, Callable, Union
from dataclasses import dataclass, field, asdict

import dearpygui.dearpygui as dpg
import numpy as np

from rfm_ui.theme import get_theme
from rfm_ui.errors import error_boundary, UIError, FractalError


# Special node identifier prefixes
NODE_PREFIX = {
    "param": "param_",
    "keyframe": "keyframe_",
    "ease": "ease_",
    "wait": "wait_",
    "export": "export_"
}


@dataclass
class KeyFrame:
    """
    Represents a keyframe in an animation sequence.
    
    Attributes:
        t: Time position in seconds
        params: Dictionary of fractal parameters at this keyframe
        label: Optional label for the keyframe
    """
    t: float
    params: Dict[str, Any] = field(default_factory=dict)
    label: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert keyframe to dictionary for serialization."""
        return {
            "t": self.t,
            "params": self.params,
            "label": self.label
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'KeyFrame':
        """Create a keyframe from a dictionary."""
        return KeyFrame(
            t=data.get("t", 0.0),
            params=data.get("params", {}),
            label=data.get("label")
        )


class EasingType(Enum):
    """Types of easing functions for animation."""
    LINEAR = "linear"
    QUAD_IN = "quad_in"
    QUAD_OUT = "quad_out"
    QUAD_IN_OUT = "quad_in_out"
    CUBIC_IN = "cubic_in"
    CUBIC_OUT = "cubic_out"
    CUBIC_IN_OUT = "cubic_in_out"
    ELASTIC_IN = "elastic_in"
    ELASTIC_OUT = "elastic_out"
    ELASTIC_IN_OUT = "elastic_in_out"
    BOUNCE_IN = "bounce_in"
    BOUNCE_OUT = "bounce_out"
    BOUNCE_IN_OUT = "bounce_in_out"


@dataclass
class EasingLink:
    """
    Represents an easing link between two keyframes.
    
    Attributes:
        from_frame: Index of the source keyframe
        to_frame: Index of the target keyframe
        easing: Type of easing function to use
        params: Extra parameters for the easing function
    """
    from_frame: int
    to_frame: int
    easing: EasingType = EasingType.LINEAR
    params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert easing link to dictionary for serialization."""
        return {
            "from_frame": self.from_frame,
            "to_frame": self.to_frame,
            "easing": self.easing.value,
            "params": self.params
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'EasingLink':
        """Create an easing link from a dictionary."""
        easing_str = data.get("easing", "linear")
        try:
            easing = EasingType(easing_str)
        except ValueError:
            easing = EasingType.LINEAR
            
        return EasingLink(
            from_frame=data.get("from_frame", 0),
            to_frame=data.get("to_frame", 0),
            easing=easing,
            params=data.get("params", {})
        )


@dataclass
class WaitNode:
    """
    Represents a wait node in an animation sequence.
    
    Attributes:
        t: Time position in seconds
        duration: Duration of the wait in seconds
        label: Optional label for the wait node
    """
    t: float
    duration: float = 1.0
    label: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert wait node to dictionary for serialization."""
        return {
            "t": self.t,
            "duration": self.duration,
            "label": self.label
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'WaitNode':
        """Create a wait node from a dictionary."""
        return WaitNode(
            t=data.get("t", 0.0),
            duration=data.get("duration", 1.0),
            label=data.get("label")
        )


@dataclass
class ExportNode:
    """
    Represents an export node in an animation sequence.
    
    Attributes:
        t: Time position in seconds
        filename: Name of the file to export to
        format: Format of the export (png, jpg, etc.)
        label: Optional label for the export node
    """
    t: float
    filename: str
    format: str = "png"
    label: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert export node to dictionary for serialization."""
        return {
            "t": self.t,
            "filename": self.filename,
            "format": self.format,
            "label": self.label
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ExportNode':
        """Create an export node from a dictionary."""
        return ExportNode(
            t=data.get("t", 0.0),
            filename=data.get("filename", "frame.png"),
            format=data.get("format", "png"),
            label=data.get("label")
        )


@dataclass
class AnimationSequence:
    """
    Complete animation sequence containing keyframes and nodes.
    
    Attributes:
        keyframes: List of keyframes in the sequence
        easing_links: List of easing links between keyframes
        wait_nodes: List of wait nodes in the sequence
        export_nodes: List of export nodes in the sequence
        duration: Total duration of the sequence in seconds
        name: Name of the sequence
    """
    keyframes: List[KeyFrame] = field(default_factory=list)
    easing_links: List[EasingLink] = field(default_factory=list)
    wait_nodes: List[WaitNode] = field(default_factory=list)
    export_nodes: List[ExportNode] = field(default_factory=list)
    duration: float = 10.0
    name: str = "Animation"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert animation sequence to dictionary for serialization."""
        return {
            "keyframes": [kf.to_dict() for kf in self.keyframes],
            "easing_links": [el.to_dict() for el in self.easing_links],
            "wait_nodes": [wn.to_dict() for wn in self.wait_nodes],
            "export_nodes": [en.to_dict() for en in self.export_nodes],
            "duration": self.duration,
            "name": self.name
        }
    
    def to_json(self) -> str:
        """Convert animation sequence to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'AnimationSequence':
        """Create an animation sequence from a dictionary."""
        return AnimationSequence(
            keyframes=[KeyFrame.from_dict(kf) for kf in data.get("keyframes", [])],
            easing_links=[EasingLink.from_dict(el) for el in data.get("easing_links", [])],
            wait_nodes=[WaitNode.from_dict(wn) for wn in data.get("wait_nodes", [])],
            export_nodes=[ExportNode.from_dict(en) for en in data.get("export_nodes", [])],
            duration=data.get("duration", 10.0),
            name=data.get("name", "Animation")
        )
    
    @staticmethod
    def from_json(json_str: str) -> 'AnimationSequence':
        """Create an animation sequence from a JSON string."""
        data = json.loads(json_str)
        return AnimationSequence.from_dict(data)
    
    def add_keyframe(self, t: float, params: Dict[str, Any], label: Optional[str] = None) -> int:
        """
        Add a keyframe to the sequence.
        
        Args:
            t: Time position in seconds
            params: Dictionary of fractal parameters
            label: Optional label for the keyframe
            
        Returns:
            Index of the added keyframe
        """
        self.keyframes.append(KeyFrame(t, params, label))
        return len(self.keyframes) - 1
    
    def add_easing_link(self, from_idx: int, to_idx: int, 
                       easing: EasingType = EasingType.LINEAR,
                       params: Dict[str, Any] = None) -> int:
        """
        Add an easing link between two keyframes.
        
        Args:
            from_idx: Index of the source keyframe
            to_idx: Index of the target keyframe
            easing: Type of easing function to use
            params: Extra parameters for the easing function
            
        Returns:
            Index of the added easing link
        """
        if params is None:
            params = {}
            
        self.easing_links.append(EasingLink(from_idx, to_idx, easing, params))
        return len(self.easing_links) - 1
    
    def add_wait_node(self, t: float, duration: float = 1.0, label: Optional[str] = None) -> int:
        """
        Add a wait node to the sequence.
        
        Args:
            t: Time position in seconds
            duration: Duration of the wait in seconds
            label: Optional label for the wait node
            
        Returns:
            Index of the added wait node
        """
        self.wait_nodes.append(WaitNode(t, duration, label))
        return len(self.wait_nodes) - 1
    
    def add_export_node(self, t: float, filename: str, 
                       format: str = "png", label: Optional[str] = None) -> int:
        """
        Add an export node to the sequence.
        
        Args:
            t: Time position in seconds
            filename: Name of the file to export to
            format: Format of the export (png, jpg, etc.)
            label: Optional label for the export node
            
        Returns:
            Index of the added export node
        """
        self.export_nodes.append(ExportNode(t, filename, format, label))
        return len(self.export_nodes) - 1


class AnimationSequencer:
    """
    Node-based animation sequencer for RFM Architecture UI.
    
    This class provides a node editor interface for creating animation
    sequences between different fractal parameter states.
    """
    
    def __init__(self, on_update: Callable[[Dict[str, Any]], None]):
        """
        Initialize the animation sequencer.
        
        Args:
            on_update: Callback function that receives updated parameters
        """
        self.logger = logging.getLogger("anim_sequencer")
        self.on_update = on_update
        
        # State
        self.node_editor_id = None
        self.timeline_id = None
        self.sequence = AnimationSequence()
        self.current_time = 0.0
        self.is_playing = False
        self.play_start_time = 0.0
        self.play_speed = 1.0
        
        # UI elements
        self.nodes = {}
        self.links = {}
        self.controls = {}
        
        # Theme
        self.theme = get_theme()
        
    @error_boundary
    def build(self, parent_id: int) -> int:
        """
        Build the animation sequencer UI.
        
        Args:
            parent_id: ID of the parent container
            
        Returns:
            ID of the created node editor
        """
        # Create container for the sequencer
        with dpg.child_window(parent=parent_id, width=-1, height=-1):
            container_id = dpg.last_item()
            
            # Create toolbar
            with dpg.group(horizontal=True, parent=container_id):
                toolbar_id = dpg.last_item()
                
                # Playback controls
                dpg.add_button(label="Play", callback=self._on_play)
                dpg.add_button(label="Stop", callback=self._on_stop)
                dpg.add_button(label="Reset", callback=self._on_reset)
                
                # Speed control
                dpg.add_text("Speed:")
                dpg.add_slider_float(
                    default_value=1.0,
                    min_value=0.1,
                    max_value=5.0,
                    width=100,
                    callback=self._on_speed_changed
                )
                
                # Add node buttons
                dpg.add_separator(direction=dpg.mvDir_Right)
                dpg.add_button(label="Add Keyframe", callback=self._on_add_keyframe)
                dpg.add_button(label="Add Ease", callback=self._on_add_ease)
                dpg.add_button(label="Add Wait", callback=self._on_add_wait)
                dpg.add_button(label="Add Export", callback=self._on_add_export)
                
                # File operations
                dpg.add_separator(direction=dpg.mvDir_Right)
                dpg.add_button(label="Save", callback=self._on_save)
                dpg.add_button(label="Load", callback=self._on_load)
                dpg.add_button(label="Clear", callback=self._on_clear)
            
            # Create timeline
            with dpg.group(parent=container_id, horizontal=True):
                timeline_group = dpg.last_item()
                
                # Time indicator
                dpg.add_text("Time:")
                self.controls["time_text"] = dpg.add_text("0.00 s")
                
                # Timeline slider
                self.timeline_id = dpg.add_slider_float(
                    default_value=0.0,
                    min_value=0.0,
                    max_value=10.0,
                    width=-1,
                    format="%.2f s",
                    callback=self._on_timeline_changed
                )
            
            # Create node editor
            with dpg.node_editor(parent=container_id, callback=self._on_link_created) as self.node_editor_id:
                # Configure node editor
                self._configure_node_editor()
            
            # Add status bar
            with dpg.group(parent=container_id, horizontal=True):
                status_bar = dpg.last_item()
                dpg.add_text("Status:")
                self.controls["status_text"] = dpg.add_text("Ready")
        
        # Start update timer
        with dpg.item_handler_registry() as handler:
            dpg.add_item_visible_handler(callback=self._on_frame)
            
        dpg.bind_item_handler_registry(container_id, handler)
        
        # Create initial keyframe for current state
        self._add_default_nodes()
        
        return container_id
        
    def _configure_node_editor(self):
        """Configure the node editor appearance and behavior."""
        dpg.configure_item(
            self.node_editor_id,
            minimap=True,
            minimap_location=dpg.mvNodeMiniMap_Location_BottomRight
        )
        
    def _add_default_nodes(self):
        """Add default nodes to the node editor."""
        # Add a keyframe at the start
        self._add_keyframe_node(0.0, {}, "Start")
        
        # Add a keyframe at the end
        self._add_keyframe_node(10.0, {}, "End")
        
    def _add_keyframe_node(self, t: float, params: Dict[str, Any], label: Optional[str] = None) -> int:
        """
        Add a keyframe node to the node editor.
        
        Args:
            t: Time position in seconds
            params: Dictionary of fractal parameters
            label: Optional label for the keyframe
            
        Returns:
            ID of the created node
        """
        # Create node label
        if label is None:
            label = f"Keyframe {len(self.sequence.keyframes)}"
            
        # Add keyframe to sequence
        keyframe_idx = self.sequence.add_keyframe(t, params, label)
        
        # Create node
        with dpg.node(parent=self.node_editor_id, label=label) as node:
            # Position node based on time
            x = t * 100
            y = 100
            dpg.set_item_pos(node, [x, y])
            
            # Input attribute for linking
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input):
                dpg.add_text("In")
                
            # Parameters
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_text(f"Time: {t:.2f} s")
                dpg.add_input_float(
                    label="Time",
                    default_value=t,
                    callback=lambda s, a, u: self._on_keyframe_time_changed(keyframe_idx, a),
                    width=150
                )
                
                # Parameter count
                param_count = len(params)
                dpg.add_text(f"Parameters: {param_count}")
                
                # Edit button
                dpg.add_button(
                    label="Edit Parameters",
                    callback=lambda s, a, u: self._on_edit_params(keyframe_idx),
                    width=150
                )
                
            # Output attribute for linking
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                dpg.add_text("Out")
                
        # Store node
        self.nodes[f"{NODE_PREFIX['keyframe']}{keyframe_idx}"] = node
        
        return node
        
    def _add_ease_node(self, from_idx: int, to_idx: int, 
                     easing: EasingType = EasingType.LINEAR,
                     params: Dict[str, Any] = None) -> int:
        """
        Add an easing node to the node editor.
        
        Args:
            from_idx: Index of the source keyframe
            to_idx: Index of the target keyframe
            easing: Type of easing function to use
            params: Extra parameters for the easing function
            
        Returns:
            ID of the created node
        """
        if params is None:
            params = {}
            
        # Add easing link to sequence
        easing_idx = self.sequence.add_easing_link(from_idx, to_idx, easing, params)
        
        # Get keyframe positions
        from_t = self.sequence.keyframes[from_idx].t
        to_t = self.sequence.keyframes[to_idx].t
        
        # Create node
        with dpg.node(parent=self.node_editor_id, label=f"Ease {easing.value}") as node:
            # Position node between keyframes
            x = (from_t + to_t) * 50
            y = 200
            dpg.set_item_pos(node, [x, y])
            
            # Input attribute for linking
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input):
                dpg.add_text("In")
                
            # Easing parameters
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_text(f"From: Keyframe {from_idx}")
                dpg.add_text(f"To: Keyframe {to_idx}")
                
                # Easing type combo
                dpg.add_combo(
                    items=[e.value for e in EasingType],
                    default_value=easing.value,
                    callback=lambda s, a, u: self._on_easing_type_changed(easing_idx, a),
                    width=150
                )
                
            # Output attribute for linking
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                dpg.add_text("Out")
                
        # Store node
        self.nodes[f"{NODE_PREFIX['ease']}{easing_idx}"] = node
        
        # Create links
        self._create_link(
            f"{NODE_PREFIX['keyframe']}{from_idx}",
            f"{NODE_PREFIX['ease']}{easing_idx}",
            "out", "in"
        )
        
        self._create_link(
            f"{NODE_PREFIX['ease']}{easing_idx}",
            f"{NODE_PREFIX['keyframe']}{to_idx}",
            "out", "in"
        )
        
        return node
        
    def _add_wait_node(self, t: float, duration: float = 1.0, label: Optional[str] = None) -> int:
        """
        Add a wait node to the node editor.
        
        Args:
            t: Time position in seconds
            duration: Duration of the wait in seconds
            label: Optional label for the wait node
            
        Returns:
            ID of the created node
        """
        # Create node label
        if label is None:
            label = f"Wait {len(self.sequence.wait_nodes)}"
            
        # Add wait node to sequence
        wait_idx = self.sequence.add_wait_node(t, duration, label)
        
        # Create node
        with dpg.node(parent=self.node_editor_id, label=label) as node:
            # Position node based on time
            x = t * 100
            y = 300
            dpg.set_item_pos(node, [x, y])
            
            # Input attribute for linking
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input):
                dpg.add_text("In")
                
            # Parameters
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_text(f"Time: {t:.2f} s")
                dpg.add_input_float(
                    label="Time",
                    default_value=t,
                    callback=lambda s, a, u: self._on_wait_time_changed(wait_idx, a),
                    width=150
                )
                
                dpg.add_text(f"Duration: {duration:.2f} s")
                dpg.add_input_float(
                    label="Duration",
                    default_value=duration,
                    callback=lambda s, a, u: self._on_wait_duration_changed(wait_idx, a),
                    width=150
                )
                
            # Output attribute for linking
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                dpg.add_text("Out")
                
        # Store node
        self.nodes[f"{NODE_PREFIX['wait']}{wait_idx}"] = node
        
        return node
        
    def _add_export_node(self, t: float, filename: str, 
                       format: str = "png", label: Optional[str] = None) -> int:
        """
        Add an export node to the node editor.
        
        Args:
            t: Time position in seconds
            filename: Name of the file to export to
            format: Format of the export (png, jpg, etc.)
            label: Optional label for the export node
            
        Returns:
            ID of the created node
        """
        # Create node label
        if label is None:
            label = f"Export {len(self.sequence.export_nodes)}"
            
        # Add export node to sequence
        export_idx = self.sequence.add_export_node(t, filename, format, label)
        
        # Create node
        with dpg.node(parent=self.node_editor_id, label=label) as node:
            # Position node based on time
            x = t * 100
            y = 400
            dpg.set_item_pos(node, [x, y])
            
            # Input attribute for linking
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input):
                dpg.add_text("In")
                
            # Parameters
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_text(f"Time: {t:.2f} s")
                dpg.add_input_float(
                    label="Time",
                    default_value=t,
                    callback=lambda s, a, u: self._on_export_time_changed(export_idx, a),
                    width=150
                )
                
                dpg.add_text(f"Filename: {filename}")
                dpg.add_input_text(
                    label="Filename",
                    default_value=filename,
                    callback=lambda s, a, u: self._on_export_filename_changed(export_idx, a),
                    width=150
                )
                
                dpg.add_text(f"Format: {format}")
                dpg.add_combo(
                    label="Format",
                    items=["png", "jpg", "bmp"],
                    default_value=format,
                    callback=lambda s, a, u: self._on_export_format_changed(export_idx, a),
                    width=150
                )
                
            # Output attribute for linking
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                dpg.add_text("Out")
                
        # Store node
        self.nodes[f"{NODE_PREFIX['export']}{export_idx}"] = node
        
        return node
    
    def _create_link(self, from_node: str, to_node: str, 
                   from_attr: str, to_attr: str) -> int:
        """
        Create a link between two node attributes.
        
        Args:
            from_node: ID of the source node
            to_node: ID of the target node
            from_attr: Attribute of the source node ("in" or "out")
            to_attr: Attribute of the target node ("in" or "out")
            
        Returns:
            ID of the created link
        """
        # Get node IDs
        from_id = self.nodes.get(from_node)
        to_id = self.nodes.get(to_node)
        
        if from_id is None or to_id is None:
            self.logger.warning(f"Cannot create link: nodes not found")
            return None
            
        # Get attribute IDs
        from_attr_id = None
        to_attr_id = None
        
        for attr_id in dpg.get_item_children(from_id, 1):
            attr_type = dpg.get_item_configuration(attr_id)["attribute_type"]
            if from_attr == "in" and attr_type == dpg.mvNode_Attr_Input:
                from_attr_id = attr_id
                break
            elif from_attr == "out" and attr_type == dpg.mvNode_Attr_Output:
                from_attr_id = attr_id
                break
                
        for attr_id in dpg.get_item_children(to_id, 1):
            attr_type = dpg.get_item_configuration(attr_id)["attribute_type"]
            if to_attr == "in" and attr_type == dpg.mvNode_Attr_Input:
                to_attr_id = attr_id
                break
            elif to_attr == "out" and attr_type == dpg.mvNode_Attr_Output:
                to_attr_id = attr_id
                break
                
        if from_attr_id is None or to_attr_id is None:
            self.logger.warning(f"Cannot create link: attributes not found")
            return None
            
        # Create link
        link_id = dpg.add_node_link(from_attr_id, to_attr_id, parent=self.node_editor_id)
        
        # Store link
        link_key = f"{from_node}_{to_node}_{from_attr}_{to_attr}"
        self.links[link_key] = link_id
        
        return link_id
        
    def _on_link_created(self, sender, app_data):
        """
        Handle link creation in the node editor.
        
        Args:
            sender: ID of the sender
            app_data: Contains link data (from and to attribute IDs)
        """
        # Extract link information
        from_attr_id = app_data[0]
        to_attr_id = app_data[1]
        
        # Get node IDs
        from_node_id = dpg.get_item_parent(from_attr_id)
        to_node_id = dpg.get_item_parent(to_attr_id)
        
        # Get node types and indices from node tags
        from_node_tag = None
        to_node_tag = None
        
        for tag, node_id in self.nodes.items():
            if node_id == from_node_id:
                from_node_tag = tag
            if node_id == to_node_id:
                to_node_tag = tag
                
        if from_node_tag is None or to_node_tag is None:
            self.logger.warning(f"Cannot handle link: nodes not found")
            return
            
        # Update sequence based on link type
        # This is just a simple example; you would need to update your sequence data
        # based on the specific link type and node types
        self.logger.info(f"Link created: {from_node_tag} -> {to_node_tag}")
        
    def _on_frame(self, sender, app_data):
        """
        Handle frame update for animation playback.
        
        Args:
            sender: ID of the sender
            app_data: App data
        """
        if not self.is_playing:
            return
            
        # Calculate current time
        current_time = time.time()
        elapsed = (current_time - self.play_start_time) * self.play_speed
        
        # Update current time
        self.current_time = elapsed % self.sequence.duration
        
        # Update UI
        self._update_time_display()
        
        # Calculate parameters for current time
        params = self._calculate_params_at_time(self.current_time)
        
        # Update UI
        if self.on_update and params:
            self.on_update(params)
            
    def _update_time_display(self):
        """Update time display in the UI."""
        # Update time text
        dpg.set_value(self.controls["time_text"], f"{self.current_time:.2f} s")
        
        # Update timeline slider
        dpg.set_value(self.timeline_id, self.current_time)
        
    def _calculate_params_at_time(self, t: float) -> Dict[str, Any]:
        """
        Calculate interpolated parameters at a specific time.
        
        Args:
            t: Time in seconds
            
        Returns:
            Interpolated parameters at time t
        """
        # Find surrounding keyframes
        prev_keyframe = None
        next_keyframe = None
        
        for i, kf in enumerate(self.sequence.keyframes):
            if kf.t <= t and (prev_keyframe is None or kf.t > prev_keyframe.t):
                prev_keyframe = kf
                prev_idx = i
                
            if kf.t >= t and (next_keyframe is None or kf.t < next_keyframe.t):
                next_keyframe = kf
                next_idx = i
                
        # If no keyframes or only one keyframe, return its parameters
        if prev_keyframe is None and next_keyframe is None:
            return {}
        elif prev_keyframe is None:
            return next_keyframe.params
        elif next_keyframe is None:
            return prev_keyframe.params
            
        # If at a keyframe exactly, return its parameters
        if prev_keyframe.t == t:
            return prev_keyframe.params
        elif next_keyframe.t == t:
            return next_keyframe.params
            
        # Find easing between these keyframes
        easing = EasingType.LINEAR
        easing_params = {}
        
        for el in self.sequence.easing_links:
            if el.from_frame == prev_idx and el.to_frame == next_idx:
                easing = el.easing
                easing_params = el.params
                break
                
        # Interpolate parameters
        return self._interpolate_params(
            prev_keyframe.params,
            next_keyframe.params,
            (t - prev_keyframe.t) / (next_keyframe.t - prev_keyframe.t),
            easing,
            easing_params
        )
        
    def _interpolate_params(self, 
                          params1: Dict[str, Any],
                          params2: Dict[str, Any],
                          t: float,
                          easing: EasingType = EasingType.LINEAR,
                          easing_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Interpolate between two parameter sets.
        
        Args:
            params1: First parameter set
            params2: Second parameter set
            t: Interpolation factor (0-1)
            easing: Easing function to use
            easing_params: Extra parameters for the easing function
            
        Returns:
            Interpolated parameters
        """
        if easing_params is None:
            easing_params = {}
            
        # Apply easing function
        t_eased = self._apply_easing(t, easing, easing_params)
        
        # Interpolate parameters
        result = {}
        
        # Get all keys from both parameter sets
        all_keys = set(params1.keys()) | set(params2.keys())
        
        for key in all_keys:
            # If key is only in one set, use that value
            if key not in params1:
                result[key] = params2[key]
                continue
            elif key not in params2:
                result[key] = params1[key]
                continue
                
            # Get values from both sets
            val1 = params1[key]
            val2 = params2[key]
            
            # Interpolate based on value type
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                # Numeric interpolation
                result[key] = val1 + (val2 - val1) * t_eased
                
                # Convert back to int if both values are ints
                if isinstance(val1, int) and isinstance(val2, int):
                    result[key] = int(round(result[key]))
            else:
                # For non-numeric values, just switch at midpoint
                result[key] = val1 if t_eased < 0.5 else val2
                
        return result
        
    def _apply_easing(self, t: float, easing: EasingType, params: Dict[str, Any]) -> float:
        """
        Apply an easing function to a value.
        
        Args:
            t: Value to ease (0-1)
            easing: Easing function to use
            params: Extra parameters for the easing function
            
        Returns:
            Eased value (0-1)
        """
        # Clamp t to 0-1 range
        t = max(0, min(1, t))
        
        # Apply easing
        if easing == EasingType.LINEAR:
            return t
        elif easing == EasingType.QUAD_IN:
            return t * t
        elif easing == EasingType.QUAD_OUT:
            return t * (2 - t)
        elif easing == EasingType.QUAD_IN_OUT:
            return 2 * t * t if t < 0.5 else -1 + (4 - 2 * t) * t
        elif easing == EasingType.CUBIC_IN:
            return t * t * t
        elif easing == EasingType.CUBIC_OUT:
            t = t - 1
            return t * t * t + 1
        elif easing == EasingType.CUBIC_IN_OUT:
            return 4 * t * t * t if t < 0.5 else 0.5 * math.pow(2 * t - 2, 3) + 1
        elif easing == EasingType.ELASTIC_IN:
            return sin(13 * math.pi/2 * t) * math.pow(2, 10 * (t - 1))
        elif easing == EasingType.ELASTIC_OUT:
            return sin(-13 * math.pi/2 * (t + 1)) * math.pow(2, -10 * t) + 1
        elif easing == EasingType.ELASTIC_IN_OUT:
            return 0.5 * sin(13 * math.pi/2 * (2 * t)) * math.pow(2, 10 * ((2 * t) - 1)) if t < 0.5 else 0.5 * (sin(-13 * math.pi/2 * ((2 * t - 1) + 1)) * math.pow(2, -10 * (2 * t - 1)) + 2)
        elif easing == EasingType.BOUNCE_IN:
            return 1 - self._bounce_out(1 - t)
        elif easing == EasingType.BOUNCE_OUT:
            return self._bounce_out(t)
        elif easing == EasingType.BOUNCE_IN_OUT:
            return 0.5 * (1 - self._bounce_out(1 - 2 * t)) if t < 0.5 else 0.5 * self._bounce_out(2 * t - 1) + 0.5
        else:
            return t
    
    def _bounce_out(self, t: float) -> float:
        """
        Bounce out easing function.
        
        Args:
            t: Value to ease (0-1)
            
        Returns:
            Eased value (0-1)
        """
        if t < 4/11:
            return (121 * t * t) / 16
        elif t < 8/11:
            return (363 / 40 * t * t) - (99 / 10 * t) + 17/5
        elif t < 9/10:
            return (4356 / 361 * t * t) - (35442 / 1805 * t) + 16061/1805
        else:
            return (54 / 5 * t * t) - (513 / 25 * t) + 268/25
            
    def _on_play(self, sender, app_data):
        """
        Handle play button click.
        
        Args:
            sender: ID of the sender
            app_data: App data
        """
        if self.is_playing:
            return
            
        self.is_playing = True
        self.play_start_time = time.time() - (self.current_time / self.play_speed)
        
        dpg.set_value(self.controls["status_text"], "Playing...")
        
    def _on_stop(self, sender, app_data):
        """
        Handle stop button click.
        
        Args:
            sender: ID of the sender
            app_data: App data
        """
        if not self.is_playing:
            return
            
        self.is_playing = False
        
        dpg.set_value(self.controls["status_text"], "Stopped")
        
    def _on_reset(self, sender, app_data):
        """
        Handle reset button click.
        
        Args:
            sender: ID of the sender
            app_data: App data
        """
        self.is_playing = False
        self.current_time = 0.0
        
        # Update UI
        self._update_time_display()
        
        dpg.set_value(self.controls["status_text"], "Reset")
        
    def _on_speed_changed(self, sender, app_data):
        """
        Handle speed change.
        
        Args:
            sender: ID of the sender
            app_data: New speed value
        """
        # Calculate current time before speed change
        if self.is_playing:
            current_time = time.time()
            elapsed = (current_time - self.play_start_time) * self.play_speed
            self.current_time = elapsed % self.sequence.duration
            
        # Update speed
        self.play_speed = app_data
        
        # Update play start time to maintain current position
        if self.is_playing:
            self.play_start_time = time.time() - (self.current_time / self.play_speed)
            
        dpg.set_value(self.controls["status_text"], f"Speed: {self.play_speed:.1f}x")
        
    def _on_timeline_changed(self, sender, app_data):
        """
        Handle timeline slider change.
        
        Args:
            sender: ID of the sender
            app_data: New time value
        """
        # Update current time
        self.current_time = app_data
        
        # Update play start time to maintain position if playing
        if self.is_playing:
            self.play_start_time = time.time() - (self.current_time / self.play_speed)
            
        # Update time display
        self._update_time_display()
        
        # Calculate parameters for current time
        params = self._calculate_params_at_time(self.current_time)
        
        # Update UI
        if self.on_update and params:
            self.on_update(params)
            
        dpg.set_value(self.controls["status_text"], f"Time: {self.current_time:.2f} s")
        
    def _on_add_keyframe(self, sender, app_data):
        """
        Handle add keyframe button click.
        
        Args:
            sender: ID of the sender
            app_data: App data
        """
        # TODO: Get current parameters from UI
        params = {}
        
        # Add keyframe at current time
        self._add_keyframe_node(self.current_time, params)
        
        dpg.set_value(self.controls["status_text"], f"Added keyframe at {self.current_time:.2f} s")
        
    def _on_add_ease(self, sender, app_data):
        """
        Handle add ease button click.
        
        Args:
            sender: ID of the sender
            app_data: App data
        """
        # Show dialog to select keyframes
        with dpg.window(label="Add Ease", modal=True, width=300, height=200):
            container_id = dpg.last_item()
            
            # Keyframe selection
            dpg.add_text("From Keyframe:")
            from_combo = dpg.add_combo(
                items=[f"{i}: {kf.label or f'Keyframe {i}'}" for i, kf in enumerate(self.sequence.keyframes)],
                width=-1
            )
            
            dpg.add_text("To Keyframe:")
            to_combo = dpg.add_combo(
                items=[f"{i}: {kf.label or f'Keyframe {i}'}" for i, kf in enumerate(self.sequence.keyframes)],
                width=-1
            )
            
            # Easing type
            dpg.add_text("Easing Type:")
            easing_combo = dpg.add_combo(
                items=[e.value for e in EasingType],
                default_value=EasingType.LINEAR.value,
                width=-1
            )
            
            # Buttons
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Add",
                    callback=lambda: self._on_add_ease_confirm(
                        int(dpg.get_value(from_combo).split(":")[0]),
                        int(dpg.get_value(to_combo).split(":")[0]),
                        EasingType(dpg.get_value(easing_combo)),
                        container_id
                    )
                )
                
                dpg.add_button(
                    label="Cancel",
                    callback=lambda: dpg.delete_item(container_id)
                )
                
    def _on_add_ease_confirm(self, from_idx: int, to_idx: int, 
                           easing: EasingType, container_id: int):
        """
        Handle add ease confirmation.
        
        Args:
            from_idx: Index of the source keyframe
            to_idx: Index of the target keyframe
            easing: Easing type
            container_id: ID of the container to close
        """
        # Add ease node
        self._add_ease_node(from_idx, to_idx, easing)
        
        # Close dialog
        dpg.delete_item(container_id)
        
        dpg.set_value(self.controls["status_text"], f"Added {easing.value} ease from {from_idx} to {to_idx}")
        
    def _on_add_wait(self, sender, app_data):
        """
        Handle add wait button click.
        
        Args:
            sender: ID of the sender
            app_data: App data
        """
        # Add wait node at current time
        self._add_wait_node(self.current_time, 1.0)
        
        dpg.set_value(self.controls["status_text"], f"Added wait at {self.current_time:.2f} s")
        
    def _on_add_export(self, sender, app_data):
        """
        Handle add export button click.
        
        Args:
            sender: ID of the sender
            app_data: App data
        """
        # Add export node at current time
        self._add_export_node(self.current_time, f"frame_{int(self.current_time*30):04d}.png")
        
        dpg.set_value(self.controls["status_text"], f"Added export at {self.current_time:.2f} s")
        
    def _on_save(self, sender, app_data):
        """
        Handle save button click.
        
        Args:
            sender: ID of the sender
            app_data: App data
        """
        # Show save dialog
        with dpg.window(label="Save Animation", modal=True, width=300, height=150):
            container_id = dpg.last_item()
            
            dpg.add_text("Enter filename:")
            dpg.add_input_text(tag="save_filename", default_value="animation.json", width=-1)
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Save",
                    callback=lambda: self._on_save_confirm(
                        dpg.get_value("save_filename"),
                        container_id
                    )
                )
                
                dpg.add_button(
                    label="Cancel",
                    callback=lambda: dpg.delete_item(container_id)
                )
                
    def _on_save_confirm(self, filename: str, container_id: int):
        """
        Handle save confirmation.
        
        Args:
            filename: Name of the file to save to
            container_id: ID of the container to close
        """
        try:
            # Save animation sequence to file
            with open(filename, "w") as f:
                f.write(self.sequence.to_json())
                
            # Close dialog
            dpg.delete_item(container_id)
            
            dpg.set_value(self.controls["status_text"], f"Saved to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving animation: {e}")
            
            # Close dialog
            dpg.delete_item(container_id)
            
            # Show error dialog
            with dpg.window(label="Save Error", modal=True, width=300, height=150):
                error_id = dpg.last_item()
                
                dpg.add_text(f"Error saving animation:")
                dpg.add_text(str(e))
                
                dpg.add_button(
                    label="OK",
                    callback=lambda: dpg.delete_item(error_id)
                )
                
    def _on_load(self, sender, app_data):
        """
        Handle load button click.
        
        Args:
            sender: ID of the sender
            app_data: App data
        """
        # Show load dialog
        with dpg.window(label="Load Animation", modal=True, width=300, height=150):
            container_id = dpg.last_item()
            
            dpg.add_text("Enter filename:")
            dpg.add_input_text(tag="load_filename", default_value="animation.json", width=-1)
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Load",
                    callback=lambda: self._on_load_confirm(
                        dpg.get_value("load_filename"),
                        container_id
                    )
                )
                
                dpg.add_button(
                    label="Cancel",
                    callback=lambda: dpg.delete_item(container_id)
                )
                
    def _on_load_confirm(self, filename: str, container_id: int):
        """
        Handle load confirmation.
        
        Args:
            filename: Name of the file to load from
            container_id: ID of the container to close
        """
        try:
            # Load animation sequence from file
            with open(filename, "r") as f:
                data = f.read()
                
            # Clear existing sequence
            self._on_clear(None, None)
            
            # Parse sequence
            self.sequence = AnimationSequence.from_json(data)
            
            # Rebuild UI
            self._rebuild_ui()
            
            # Close dialog
            dpg.delete_item(container_id)
            
            dpg.set_value(self.controls["status_text"], f"Loaded from {filename}")
        except Exception as e:
            self.logger.error(f"Error loading animation: {e}")
            
            # Close dialog
            dpg.delete_item(container_id)
            
            # Show error dialog
            with dpg.window(label="Load Error", modal=True, width=300, height=150):
                error_id = dpg.last_item()
                
                dpg.add_text(f"Error loading animation:")
                dpg.add_text(str(e))
                
                dpg.add_button(
                    label="OK",
                    callback=lambda: dpg.delete_item(error_id)
                )
                
    def _on_clear(self, sender, app_data):
        """
        Handle clear button click.
        
        Args:
            sender: ID of the sender
            app_data: App data
        """
        # Clear all nodes from the node editor
        dpg.delete_item(self.node_editor_id, children_only=True)
        
        # Clear sequence
        self.sequence = AnimationSequence()
        
        # Clear nodes and links
        self.nodes = {}
        self.links = {}
        
        # Add default nodes
        self._add_default_nodes()
        
        dpg.set_value(self.controls["status_text"], "Cleared animation")
        
    def _rebuild_ui(self):
        """Rebuild UI from current sequence."""
        # Clear all nodes from the node editor
        dpg.delete_item(self.node_editor_id, children_only=True)
        
        # Clear nodes and links
        self.nodes = {}
        self.links = {}
        
        # Add keyframe nodes
        for i, kf in enumerate(self.sequence.keyframes):
            self._add_keyframe_node(kf.t, kf.params, kf.label)
            
        # Add easing nodes
        for i, el in enumerate(self.sequence.easing_links):
            self._add_ease_node(el.from_frame, el.to_frame, el.easing, el.params)
            
        # Add wait nodes
        for i, wn in enumerate(self.sequence.wait_nodes):
            self._add_wait_node(wn.t, wn.duration, wn.label)
            
        # Add export nodes
        for i, en in enumerate(self.sequence.export_nodes):
            self._add_export_node(en.t, en.filename, en.format, en.label)
            
        # Update timeline range
        dpg.configure_item(
            self.timeline_id,
            max_value=max(10.0, self.sequence.duration)
        )
        
    def _on_keyframe_time_changed(self, index: int, value: float):
        """
        Handle keyframe time change.
        
        Args:
            index: Index of the keyframe
            value: New time value
        """
        if index < 0 or index >= len(self.sequence.keyframes):
            return
            
        # Update keyframe time
        self.sequence.keyframes[index].t = value
        
        # Update node position
        node_id = self.nodes.get(f"{NODE_PREFIX['keyframe']}{index}")
        if node_id:
            x, y = dpg.get_item_pos(node_id)
            dpg.set_item_pos(node_id, [value * 100, y])
            
        dpg.set_value(self.controls["status_text"], f"Keyframe {index} time: {value:.2f} s")
        
    def _on_edit_params(self, index: int):
        """
        Handle edit parameters button click.
        
        Args:
            index: Index of the keyframe
        """
        if index < 0 or index >= len(self.sequence.keyframes):
            return
            
        keyframe = self.sequence.keyframes[index]
        
        # Show parameter editor dialog
        with dpg.window(label=f"Edit Parameters: {keyframe.label or f'Keyframe {index}'}", 
                       modal=True, width=400, height=300):
            container_id = dpg.last_item()
            
            # Show parameter editor UI
            # This is a simple example; you would need to create a more
            # comprehensive parameter editor for your specific use case
            for key, value in keyframe.params.items():
                if isinstance(value, float):
                    dpg.add_input_float(
                        label=key,
                        default_value=value,
                        callback=lambda s, a, u: self._on_param_changed(index, u[0], a),
                        user_data=(key,),
                        width=200
                    )
                elif isinstance(value, int):
                    dpg.add_input_int(
                        label=key,
                        default_value=value,
                        callback=lambda s, a, u: self._on_param_changed(index, u[0], a),
                        user_data=(key,),
                        width=200
                    )
                elif isinstance(value, str):
                    dpg.add_input_text(
                        label=key,
                        default_value=value,
                        callback=lambda s, a, u: self._on_param_changed(index, u[0], a),
                        user_data=(key,),
                        width=200
                    )
                elif isinstance(value, bool):
                    dpg.add_checkbox(
                        label=key,
                        default_value=value,
                        callback=lambda s, a, u: self._on_param_changed(index, u[0], a),
                        user_data=(key,)
                    )
                    
            # Add buttons
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Apply",
                    callback=lambda: dpg.delete_item(container_id)
                )
                
                dpg.add_button(
                    label="Cancel",
                    callback=lambda: dpg.delete_item(container_id)
                )
                
    def _on_param_changed(self, index: int, key: str, value: Any):
        """
        Handle parameter change.
        
        Args:
            index: Index of the keyframe
            key: Parameter key
            value: New parameter value
        """
        if index < 0 or index >= len(self.sequence.keyframes):
            return
            
        # Update parameter
        self.sequence.keyframes[index].params[key] = value
        
        dpg.set_value(self.controls["status_text"], f"Updated parameter {key}")
        
    def _on_wait_time_changed(self, index: int, value: float):
        """
        Handle wait time change.
        
        Args:
            index: Index of the wait node
            value: New time value
        """
        if index < 0 or index >= len(self.sequence.wait_nodes):
            return
            
        # Update wait time
        self.sequence.wait_nodes[index].t = value
        
        # Update node position
        node_id = self.nodes.get(f"{NODE_PREFIX['wait']}{index}")
        if node_id:
            x, y = dpg.get_item_pos(node_id)
            dpg.set_item_pos(node_id, [value * 100, y])
            
        dpg.set_value(self.controls["status_text"], f"Wait {index} time: {value:.2f} s")
        
    def _on_wait_duration_changed(self, index: int, value: float):
        """
        Handle wait duration change.
        
        Args:
            index: Index of the wait node
            value: New duration value
        """
        if index < 0 or index >= len(self.sequence.wait_nodes):
            return
            
        # Update wait duration
        self.sequence.wait_nodes[index].duration = value
        
        dpg.set_value(self.controls["status_text"], f"Wait {index} duration: {value:.2f} s")
        
    def _on_export_time_changed(self, index: int, value: float):
        """
        Handle export time change.
        
        Args:
            index: Index of the export node
            value: New time value
        """
        if index < 0 or index >= len(self.sequence.export_nodes):
            return
            
        # Update export time
        self.sequence.export_nodes[index].t = value
        
        # Update node position
        node_id = self.nodes.get(f"{NODE_PREFIX['export']}{index}")
        if node_id:
            x, y = dpg.get_item_pos(node_id)
            dpg.set_item_pos(node_id, [value * 100, y])
            
        dpg.set_value(self.controls["status_text"], f"Export {index} time: {value:.2f} s")
        
    def _on_export_filename_changed(self, index: int, value: str):
        """
        Handle export filename change.
        
        Args:
            index: Index of the export node
            value: New filename value
        """
        if index < 0 or index >= len(self.sequence.export_nodes):
            return
            
        # Update export filename
        self.sequence.export_nodes[index].filename = value
        
        dpg.set_value(self.controls["status_text"], f"Export {index} filename: {value}")
        
    def _on_export_format_changed(self, index: int, value: str):
        """
        Handle export format change.
        
        Args:
            index: Index of the export node
            value: New format value
        """
        if index < 0 or index >= len(self.sequence.export_nodes):
            return
            
        # Update export format
        self.sequence.export_nodes[index].format = value
        
        dpg.set_value(self.controls["status_text"], f"Export {index} format: {value}")
        
    def _on_easing_type_changed(self, index: int, value: str):
        """
        Handle easing type change.
        
        Args:
            index: Index of the easing link
            value: New easing type value
        """
        if index < 0 or index >= len(self.sequence.easing_links):
            return
            
        try:
            # Convert string to enum
            easing = EasingType(value)
            
            # Update easing type
            self.sequence.easing_links[index].easing = easing
            
            dpg.set_value(self.controls["status_text"], f"Easing {index} type: {value}")
        except ValueError:
            self.logger.warning(f"Invalid easing type: {value}")
    
    def play(self):
        """Start playing the animation sequence."""
        self._on_play(None, None)
        
    def stop(self):
        """Stop playing the animation sequence."""
        self._on_stop(None, None)
        
    def reset(self):
        """Reset the animation sequence to the beginning."""
        self._on_reset(None, None)