"""
Preset management components for RFM Architecture.

This module provides UI components for saving, loading, and managing
architecture presets, allowing for quick configuration recall.
"""

import os
import sys
import uuid
import time
import logging
import json
from typing import Dict, List, Tuple, Optional, Set, Any, Callable, Union
import math
import random

import dearpygui.dearpygui as dpg
import numpy as np

from rfm_ui.theme import Colors, Spacing, Motion
from rfm_ui.components.panel import GlassPanel, CardPanel
from rfm_ui.errors import error_boundary

from rfm.core.node_system_base import (
    Node, Connection, Architecture, 
    NodeType, ConnectionType, EmotionalState,
    clone_architecture
)

logger = logging.getLogger(__name__)


class ArchitecturePreset:
    """Container for architecture presets."""
    
    def __init__(self, 
                architecture: Architecture,
                name: Optional[str] = None,
                description: Optional[str] = None,
                tags: Optional[List[str]] = None,
                preset_id: Optional[str] = None):
        """
        Initialize an architecture preset.
        
        Args:
            architecture: The architecture
            name: Optional name for the preset
            description: Optional description
            tags: Optional tags for categorization
            preset_id: Optional unique ID
        """
        self.architecture = architecture
        self.name = name or architecture.name
        self.description = description or architecture.description
        self.tags = tags or []
        self.id = preset_id or str(uuid.uuid4())
        self.created = time.time()
        self.modified = self.created
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
            "id": self.id,
            "created": self.created,
            "modified": self.modified,
            "architecture": self.architecture.to_dict()
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArchitecturePreset':
        """Create from dictionary."""
        # Extract architecture
        arch_data = data.get("architecture", {})
        architecture = Architecture.from_dict(arch_data)
        
        # Create instance
        preset = cls(
            architecture=architecture,
            name=data.get("name", "Unnamed Preset"),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            preset_id=data.get("id")
        )
        
        # Set timestamps
        preset.created = data.get("created", time.time())
        preset.modified = data.get("modified", preset.created)
        
        return preset


class PresetGroup:
    """Group of related presets."""
    
    def __init__(self, 
                name: str,
                description: Optional[str] = None,
                group_id: Optional[str] = None):
        """
        Initialize a preset group.
        
        Args:
            name: Name of the group
            description: Optional description
            group_id: Optional unique ID
        """
        self.name = name
        self.description = description or ""
        self.id = group_id or str(uuid.uuid4())
        self.presets: List[ArchitecturePreset] = []
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "id": self.id,
            "presets": [preset.to_dict() for preset in self.presets]
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PresetGroup':
        """Create from dictionary."""
        # Create group
        group = cls(
            name=data.get("name", "Unnamed Group"),
            description=data.get("description", ""),
            group_id=data.get("id")
        )
        
        # Add presets
        presets_data = data.get("presets", [])
        group.presets = [ArchitecturePreset.from_dict(preset_data) for preset_data in presets_data]
        
        return group
        
    def add_preset(self, preset: ArchitecturePreset) -> None:
        """Add a preset to the group."""
        self.presets.append(preset)
        
    def remove_preset(self, preset_id: str) -> bool:
        """
        Remove a preset from the group.
        
        Args:
            preset_id: ID of the preset to remove
            
        Returns:
            True if the preset was removed, False if not found
        """
        original_count = len(self.presets)
        self.presets = [preset for preset in self.presets if preset.id != preset_id]
        
        return len(self.presets) < original_count
        
    def get_preset(self, preset_id: str) -> Optional[ArchitecturePreset]:
        """
        Get a preset by ID.
        
        Args:
            preset_id: ID of the preset to retrieve
            
        Returns:
            The preset if found, None otherwise
        """
        for preset in self.presets:
            if preset.id == preset_id:
                return preset
                
        return None


class PresetLibrary:
    """Library of architecture presets."""
    
    def __init__(self, 
                name: str = "Architecture Preset Library",
                library_path: Optional[str] = None):
        """
        Initialize a preset library.
        
        Args:
            name: Name of the library
            library_path: Optional path to the library file
        """
        self.name = name
        self.library_path = library_path
        self.groups: List[PresetGroup] = []
        self.default_group = PresetGroup(name="Default")
        self.groups.append(self.default_group)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "groups": [group.to_dict() for group in self.groups]
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PresetLibrary':
        """Create from dictionary."""
        # Create library
        library = cls(
            name=data.get("name", "Architecture Preset Library")
        )
        
        # Override default groups
        library.groups = []
        
        # Add groups
        groups_data = data.get("groups", [])
        library.groups = [PresetGroup.from_dict(group_data) for group_data in groups_data]
        
        # Add default group if not present
        if not library.groups:
            library.default_group = PresetGroup(name="Default")
            library.groups.append(library.default_group)
        else:
            library.default_group = library.groups[0]
            
        return library
        
    def save(self, filepath: Optional[str] = None) -> bool:
        """
        Save the library to a file.
        
        Args:
            filepath: Path to save to, defaults to library_path
            
        Returns:
            True if successful, False otherwise
        """
        filepath = filepath or self.library_path
        
        if not filepath:
            logger.error("No filepath specified for saving library")
            return False
            
        try:
            with open(filepath, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
                
            # Update library path
            self.library_path = filepath
            
            return True
        except Exception as e:
            logger.error(f"Error saving preset library: {e}")
            return False
            
    @classmethod
    def load(cls, filepath: str) -> Optional['PresetLibrary']:
        """
        Load a library from a file.
        
        Args:
            filepath: Path to load from
            
        Returns:
            Loaded library, or None if loading failed
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            # Create library
            library = cls.from_dict(data)
            
            # Set library path
            library.library_path = filepath
            
            return library
        except Exception as e:
            logger.error(f"Error loading preset library: {e}")
            return None
            
    def add_group(self, group: PresetGroup) -> None:
        """Add a group to the library."""
        self.groups.append(group)
        
    def remove_group(self, group_id: str) -> bool:
        """
        Remove a group from the library.
        
        Args:
            group_id: ID of the group to remove
            
        Returns:
            True if the group was removed, False if not found
        """
        # Don't remove default group
        if self.default_group.id == group_id:
            return False
            
        original_count = len(self.groups)
        self.groups = [group for group in self.groups if group.id != group_id]
        
        return len(self.groups) < original_count
        
    def get_group(self, group_id: str) -> Optional[PresetGroup]:
        """
        Get a group by ID.
        
        Args:
            group_id: ID of the group to retrieve
            
        Returns:
            The group if found, None otherwise
        """
        for group in self.groups:
            if group.id == group_id:
                return group
                
        return None
        
    def add_preset(self, preset: ArchitecturePreset, group_id: Optional[str] = None) -> None:
        """
        Add a preset to the library.
        
        Args:
            preset: Preset to add
            group_id: Optional ID of the group to add to, defaults to default group
        """
        if group_id:
            group = self.get_group(group_id)
            if group:
                group.add_preset(preset)
            else:
                self.default_group.add_preset(preset)
        else:
            self.default_group.add_preset(preset)
            
    def remove_preset(self, preset_id: str) -> bool:
        """
        Remove a preset from the library.
        
        Args:
            preset_id: ID of the preset to remove
            
        Returns:
            True if the preset was removed, False if not found
        """
        for group in self.groups:
            if group.remove_preset(preset_id):
                return True
                
        return False
        
    def get_preset(self, preset_id: str) -> Optional[Tuple[ArchitecturePreset, PresetGroup]]:
        """
        Get a preset by ID.
        
        Args:
            preset_id: ID of the preset to retrieve
            
        Returns:
            Tuple of (preset, group) if found, None otherwise
        """
        for group in self.groups:
            preset = group.get_preset(preset_id)
            if preset:
                return (preset, group)
                
        return None
        
    def find_presets_by_tag(self, tag: str) -> List[Tuple[ArchitecturePreset, PresetGroup]]:
        """
        Find presets by tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of (preset, group) tuples with matching tag
        """
        results = []
        
        for group in self.groups:
            for preset in group.presets:
                if tag in preset.tags:
                    results.append((preset, group))
                    
        return results
        
    def search_presets(self, query: str) -> List[Tuple[ArchitecturePreset, PresetGroup]]:
        """
        Search presets by name, description, or tags.
        
        Args:
            query: Search query
            
        Returns:
            List of (preset, group) tuples matching query
        """
        results = []
        query = query.lower()
        
        for group in self.groups:
            for preset in group.presets:
                # Check name
                if query in preset.name.lower():
                    results.append((preset, group))
                    continue
                    
                # Check description
                if query in preset.description.lower():
                    results.append((preset, group))
                    continue
                    
                # Check tags
                for tag in preset.tags:
                    if query in tag.lower():
                        results.append((preset, group))
                        break
                        
        return results


class PresetManager:
    """
    UI component for managing architecture presets.
    
    This component provides UI for saving, loading, and organizing
    architecture presets.
    """
    
    def __init__(self, 
                parent_id: int,
                on_load_preset: Optional[Callable[[Architecture], None]] = None,
                width: int = -1,
                height: int = -1,
                tag: Optional[str] = None):
        """
        Initialize the preset manager.
        
        Args:
            parent_id: DearPyGui ID of the parent container
            on_load_preset: Callback for when a preset is loaded
            width: Width of the component
            height: Height of the component
            tag: Optional tag for the component
        """
        self.parent_id = parent_id
        self.on_load_preset = on_load_preset
        self.width = width
        self.height = height
        self.tag = tag or f"preset_manager_{uuid.uuid4()}"
        
        # Preset library
        self.library = PresetLibrary()
        
        # UI state
        self.selected_group_id: Optional[str] = None
        self.selected_preset_id: Optional[str] = None
        
        # UI components
        self.panel: Optional[CardPanel] = None
        self.container_id: Optional[int] = None
        self.group_list_id: Optional[int] = None
        self.preset_list_id: Optional[int] = None
        
        # Create the panel
        self._create_panel()
        
        # Initialize with some example presets
        self._initialize_example_presets()
        
    def _create_panel(self) -> None:
        """Create the preset manager panel."""
        # Create a card panel for the preset manager
        self.panel = CardPanel(
            parent_id=self.parent_id,
            label="Preset Manager",
            width=self.width,
            height=self.height,
            show_title_bar=True,
            tag=self.tag
        )
        
        # Get panel ID
        panel_id = self.panel.get_panel_id()
        
        # Create the preset manager UI
        with dpg.group(parent=panel_id, horizontal=False) as self.container_id:
            # Add toolbar
            with dpg.group(horizontal=True):
                # Load library button
                dpg.add_button(
                    label="Load Library",
                    callback=self._on_load_library_clicked,
                    width=100
                )
                
                # Save library button
                dpg.add_button(
                    label="Save Library",
                    callback=self._on_save_library_clicked,
                    width=100
                )
                
                # Add group button
                dpg.add_button(
                    label="Add Group",
                    callback=self._on_add_group_clicked,
                    width=100
                )
                
                # Search input
                dpg.add_input_text(
                    hint="Search presets...",
                    width=200,
                    callback=self._on_search_changed,
                    tag=f"{self.tag}_search_input"
                )
                
            # Add separator
            dpg.add_separator()
            
            # Create two-column layout
            with dpg.group(horizontal=True):
                # Left column: Groups and presets
                with dpg.child_window(width=300, height=-1):
                    left_container = dpg.last_item()
                    
                    # Group list
                    dpg.add_text("Groups", parent=left_container)
                    self.group_list_id = dpg.add_listbox(
                        items=[],
                        width=-1,
                        num_items=5,
                        callback=self._on_group_selected,
                        parent=left_container
                    )
                    
                    # Preset list
                    dpg.add_text("Presets", parent=left_container)
                    self.preset_list_id = dpg.add_listbox(
                        items=[],
                        width=-1,
                        num_items=10,
                        callback=self._on_preset_selected,
                        parent=left_container
                    )
                    
                    # Add preset button
                    with dpg.group(horizontal=True, parent=left_container):
                        dpg.add_button(
                            label="Add Preset",
                            callback=self._on_add_preset_clicked,
                            width=100
                        )
                        
                        dpg.add_button(
                            label="Remove",
                            callback=self._on_remove_clicked,
                            width=100
                        )
                
                # Right column: Preset details
                with dpg.child_window(width=-1, height=-1):
                    right_container = dpg.last_item()
                    
                    # Preset details
                    dpg.add_text("Preset Details", parent=right_container)
                    
                    # Name input
                    dpg.add_text("Name", parent=right_container)
                    dpg.add_input_text(
                        tag=f"{self.tag}_name_input",
                        width=-1,
                        parent=right_container,
                        callback=self._on_preset_property_changed
                    )
                    
                    # Description input
                    dpg.add_text("Description", parent=right_container)
                    dpg.add_input_text(
                        tag=f"{self.tag}_description_input",
                        width=-1,
                        height=80,
                        multiline=True,
                        parent=right_container,
                        callback=self._on_preset_property_changed
                    )
                    
                    # Tags input
                    dpg.add_text("Tags (comma-separated)", parent=right_container)
                    dpg.add_input_text(
                        tag=f"{self.tag}_tags_input",
                        width=-1,
                        parent=right_container,
                        callback=self._on_preset_property_changed
                    )
                    
                    # Save changes button
                    dpg.add_button(
                        label="Save Changes",
                        callback=self._on_save_changes_clicked,
                        width=120,
                        parent=right_container
                    )
                    
                    # Load preset button
                    dpg.add_button(
                        label="Load Preset",
                        callback=self._on_load_preset_clicked,
                        width=120,
                        parent=right_container
                    )
            
        # Update UI
        self._update_group_list()
        
        # Disable details initially
        self._enable_details_form(False)
        
    def _initialize_example_presets(self) -> None:
        """Initialize with some example presets."""
        # Import from rfm.core
        from rfm.core.node_system_base import create_default_architecture, create_rfm_architecture
        
        # Add "Example" group
        example_group = PresetGroup(name="Example Presets", description="Example architecture presets")
        
        # Add some example presets
        default_preset = ArchitecturePreset(
            architecture=create_default_architecture(),
            name="Default Architecture",
            description="Default architecture with basic components",
            tags=["default", "basic", "example"]
        )
        
        rfm_preset = ArchitecturePreset(
            architecture=create_rfm_architecture(),
            name="RFM Architecture",
            description="Recursive Fractal Mind architecture model",
            tags=["rfm", "recursive", "fractal", "mind"]
        )
        
        # Add presets to group
        example_group.add_preset(default_preset)
        example_group.add_preset(rfm_preset)
        
        # Add group to library
        self.library.add_group(example_group)
        
        # Update UI
        self._update_group_list()
        
    def _update_group_list(self) -> None:
        """Update the group list with current library groups."""
        if not self.group_list_id or not dpg.does_item_exist(self.group_list_id):
            return
            
        # Get group names
        group_items = []
        for group in self.library.groups:
            group_items.append(group.name)
            
        # Update listbox
        dpg.configure_item(self.group_list_id, items=group_items)
        
        # Update selected group if needed
        if self.selected_group_id:
            # Find index of selected group
            selected_index = next(
                (i for i, group in enumerate(self.library.groups) 
                 if group.id == self.selected_group_id),
                -1
            )
            
            if selected_index >= 0:
                dpg.set_value(self.group_list_id, group_items[selected_index])
                
        # Update preset list
        self._update_preset_list()
        
    def _update_preset_list(self) -> None:
        """Update the preset list with presets from selected group."""
        if not self.preset_list_id or not dpg.does_item_exist(self.preset_list_id):
            return
            
        # Get selected group
        if self.selected_group_id:
            group = self.library.get_group(self.selected_group_id)
            if not group:
                # Fall back to default group
                group = self.library.default_group
        else:
            # Default to first group
            group = self.library.groups[0] if self.library.groups else None
            
        # Get search query
        search_query = ""
        if dpg.does_item_exist(f"{self.tag}_search_input"):
            search_query = dpg.get_value(f"{self.tag}_search_input") or ""
            
        # Get preset names
        preset_items = []
        
        if group and not search_query:
            # Show presets from selected group
            for preset in group.presets:
                preset_items.append(preset.name)
                
            # Update listbox
            dpg.configure_item(self.preset_list_id, items=preset_items)
            
            # Update selected preset if needed
            if self.selected_preset_id:
                # Find index of selected preset
                selected_index = next(
                    (i for i, preset in enumerate(group.presets) 
                     if preset.id == self.selected_preset_id),
                    -1
                )
                
                if selected_index >= 0:
                    dpg.set_value(self.preset_list_id, preset_items[selected_index])
        elif search_query:
            # Search across all groups
            results = self.library.search_presets(search_query)
            for preset, _ in results:
                preset_items.append(preset.name)
                
            # Update listbox
            dpg.configure_item(self.preset_list_id, items=preset_items)
            
    def _update_preset_details(self) -> None:
        """Update the preset details form for the selected preset."""
        if not self.selected_preset_id:
            return
            
        # Get selected preset
        preset_info = self.library.get_preset(self.selected_preset_id)
        if not preset_info:
            return
            
        preset, _ = preset_info
        
        # Update form fields
        dpg.set_value(f"{self.tag}_name_input", preset.name)
        dpg.set_value(f"{self.tag}_description_input", preset.description)
        dpg.set_value(f"{self.tag}_tags_input", ", ".join(preset.tags))
        
    def _enable_details_form(self, enable: bool = True) -> None:
        """Enable or disable the details form."""
        if not dpg.does_item_exist(f"{self.tag}_name_input"):
            return
            
        # Enable/disable form fields
        dpg.configure_item(f"{self.tag}_name_input", enabled=enable)
        dpg.configure_item(f"{self.tag}_description_input", enabled=enable)
        dpg.configure_item(f"{self.tag}_tags_input", enabled=enable)
        
        # Enable/disable buttons
        button_parent = dpg.get_item_parent(f"{self.tag}_name_input")
        if button_parent:
            children = dpg.get_item_children(button_parent, 1)
            for child in children:
                if dpg.get_item_type(child) == "mvAppItemType::mvButton":
                    dpg.configure_item(child, enabled=enable)
                    
    @error_boundary
    def _on_group_selected(self, sender, app_data) -> None:
        """Handle group selection from list."""
        # Get selected group index
        selected_index = dpg.get_value(self.group_list_id)
        
        if 0 <= selected_index < len(self.library.groups):
            # Get group ID
            group_id = self.library.groups[selected_index].id
            
            # Store selected group
            self.selected_group_id = group_id
            
            # Clear selected preset
            self.selected_preset_id = None
            
            # Update preset list
            self._update_preset_list()
            
            # Disable details form
            self._enable_details_form(False)
            
    @error_boundary
    def _on_preset_selected(self, sender, app_data) -> None:
        """Handle preset selection from list."""
        if not app_data and app_data != 0:
            return
            
        # Check if we're in search mode
        search_query = ""
        if dpg.does_item_exist(f"{self.tag}_search_input"):
            search_query = dpg.get_value(f"{self.tag}_search_input") or ""
            
        # Get selected preset index
        selected_index = dpg.get_value(self.preset_list_id)
        
        # Get the preset ID
        if search_query:
            # Search results mode
            results = self.library.search_presets(search_query)
            if 0 <= selected_index < len(results):
                preset, group = results[selected_index]
                self.selected_preset_id = preset.id
                self.selected_group_id = group.id
        else:
            # Normal mode
            if not self.selected_group_id:
                return
                
            group = self.library.get_group(self.selected_group_id)
            if not group or selected_index >= len(group.presets):
                return
                
            # Get preset ID
            preset_id = group.presets[selected_index].id
            
            # Store selected preset
            self.selected_preset_id = preset_id
            
        # Update details form
        self._update_preset_details()
        
        # Enable details form
        self._enable_details_form(True)
        
    @error_boundary
    def _on_search_changed(self, sender, app_data) -> None:
        """Handle search input change."""
        # Update preset list
        self._update_preset_list()
        
    @error_boundary
    def _on_preset_property_changed(self, sender, app_data) -> None:
        """Handle preset property change."""
        # Changes are applied when Save Changes is clicked
        pass
        
    @error_boundary
    def _on_save_changes_clicked(self, sender, app_data) -> None:
        """Handle save changes button click."""
        if not self.selected_preset_id:
            return
            
        # Get selected preset
        preset_info = self.library.get_preset(self.selected_preset_id)
        if not preset_info:
            return
            
        preset, _ = preset_info
        
        # Get form values
        name = dpg.get_value(f"{self.tag}_name_input")
        description = dpg.get_value(f"{self.tag}_description_input")
        tags_str = dpg.get_value(f"{self.tag}_tags_input")
        
        # Parse tags
        tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
        
        # Update preset
        preset.name = name
        preset.description = description
        preset.tags = tags
        preset.modified = time.time()
        
        # Update UI
        self._update_preset_list()
        
        # Show success message
        with dpg.window(label="Success", modal=True, width=300, height=100, pos=(400, 200)):
            result_id = dpg.last_item()
            
            dpg.add_text("Changes saved successfully.")
            dpg.add_button(
                label="OK",
                callback=lambda s, a, u: dpg.delete_item(u),
                user_data=result_id,
                width=100
            )
            
    @error_boundary
    def _on_load_preset_clicked(self, sender, app_data) -> None:
        """Handle load preset button click."""
        if not self.selected_preset_id:
            return
            
        # Get selected preset
        preset_info = self.library.get_preset(self.selected_preset_id)
        if not preset_info:
            return
            
        preset, _ = preset_info
        
        # Show confirmation dialog
        with dpg.window(label="Load Preset", modal=True, width=300, height=150, pos=(400, 200)):
            dialog_id = dpg.last_item()
            
            dpg.add_text(f"Load preset '{preset.name}'?")
            dpg.add_text("This will replace the current architecture.")
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Yes",
                    callback=self._load_selected_preset,
                    user_data=dialog_id,
                    width=100
                )
                dpg.add_button(
                    label="No",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=dialog_id,
                    width=100
                )
                
    def _load_selected_preset(self, sender, app_data, user_data) -> None:
        """Load the selected preset."""
        # Close dialog
        dpg.delete_item(user_data)
        
        # Get selected preset
        preset_info = self.library.get_preset(self.selected_preset_id)
        if not preset_info:
            return
            
        preset, _ = preset_info
        
        # Clone architecture
        architecture = clone_architecture(preset.architecture)
        
        # Notify callback
        if self.on_load_preset:
            self.on_load_preset(architecture)
            
        # Show success message
        with dpg.window(label="Success", modal=True, width=300, height=100, pos=(400, 200)):
            result_id = dpg.last_item()
            
            dpg.add_text(f"Preset '{preset.name}' loaded successfully.")
            dpg.add_button(
                label="OK",
                callback=lambda s, a, u: dpg.delete_item(u),
                user_data=result_id,
                width=100
            )
            
    @error_boundary
    def _on_add_preset_clicked(self, sender, app_data) -> None:
        """Handle add preset button click."""
        # Check if a group is selected
        if not self.selected_group_id:
            if self.library.groups:
                self.selected_group_id = self.library.groups[0].id
            else:
                return
                
        # Show dialog for adding a new preset
        with dpg.window(label="Add Preset", modal=True, width=450, height=400, pos=(400, 200)):
            dialog_id = dpg.last_item()
            
            # Tab bar for different sources
            with dpg.tab_bar():
                # Current architecture tab
                with dpg.tab(label="From Current Architecture"):
                    current_tab_id = dpg.last_item()
                    
                    dpg.add_text("Create a preset from the current architecture.", parent=current_tab_id)
                    
                    # Preset name
                    dpg.add_text("Name", parent=current_tab_id)
                    dpg.add_input_text(
                        tag=f"{self.tag}_new_preset_name",
                        width=-1,
                        default_value="New Preset",
                        parent=current_tab_id
                    )
                    
                    # Description
                    dpg.add_text("Description", parent=current_tab_id)
                    dpg.add_input_text(
                        tag=f"{self.tag}_new_preset_description",
                        width=-1,
                        height=80,
                        multiline=True,
                        parent=current_tab_id
                    )
                    
                    # Tags
                    dpg.add_text("Tags (comma-separated)", parent=current_tab_id)
                    dpg.add_input_text(
                        tag=f"{self.tag}_new_preset_tags",
                        width=-1,
                        parent=current_tab_id
                    )
                    
                    # Create button
                    dpg.add_button(
                        label="Create",
                        callback=self._on_create_preset_from_current,
                        user_data=dialog_id,
                        width=100,
                        parent=current_tab_id
                    )
                    
                # Template tab
                with dpg.tab(label="From Template"):
                    template_tab_id = dpg.last_item()
                    
                    dpg.add_text("Create a preset from a template.", parent=template_tab_id)
                    
                    # Template selector
                    dpg.add_text("Template", parent=template_tab_id)
                    dpg.add_combo(
                        items=["Default Architecture", "RFM Architecture", "Empty Architecture"],
                        default_value="Default Architecture",
                        width=-1,
                        tag=f"{self.tag}_new_preset_template",
                        parent=template_tab_id
                    )
                    
                    # Preset name
                    dpg.add_text("Name", parent=template_tab_id)
                    dpg.add_input_text(
                        tag=f"{self.tag}_new_preset_template_name",
                        width=-1,
                        default_value="New Template Preset",
                        parent=template_tab_id
                    )
                    
                    # Description
                    dpg.add_text("Description", parent=template_tab_id)
                    dpg.add_input_text(
                        tag=f"{self.tag}_new_preset_template_description",
                        width=-1,
                        height=80,
                        multiline=True,
                        parent=template_tab_id
                    )
                    
                    # Tags
                    dpg.add_text("Tags (comma-separated)", parent=template_tab_id)
                    dpg.add_input_text(
                        tag=f"{self.tag}_new_preset_template_tags",
                        width=-1,
                        parent=template_tab_id
                    )
                    
                    # Create button
                    dpg.add_button(
                        label="Create",
                        callback=self._on_create_preset_from_template,
                        user_data=dialog_id,
                        width=100,
                        parent=template_tab_id
                    )
                    
                # File tab
                with dpg.tab(label="From File"):
                    file_tab_id = dpg.last_item()
                    
                    dpg.add_text("Create a preset from a file.", parent=file_tab_id)
                    
                    # File path
                    dpg.add_text("File Path", parent=file_tab_id)
                    dpg.add_input_text(
                        tag=f"{self.tag}_new_preset_file_path",
                        width=-1,
                        hint="architecture.json",
                        parent=file_tab_id
                    )
                    
                    # Preset name
                    dpg.add_text("Name", parent=file_tab_id)
                    dpg.add_input_text(
                        tag=f"{self.tag}_new_preset_file_name",
                        width=-1,
                        default_value="New File Preset",
                        parent=file_tab_id
                    )
                    
                    # Description
                    dpg.add_text("Description", parent=file_tab_id)
                    dpg.add_input_text(
                        tag=f"{self.tag}_new_preset_file_description",
                        width=-1,
                        height=80,
                        multiline=True,
                        parent=file_tab_id
                    )
                    
                    # Tags
                    dpg.add_text("Tags (comma-separated)", parent=file_tab_id)
                    dpg.add_input_text(
                        tag=f"{self.tag}_new_preset_file_tags",
                        width=-1,
                        parent=file_tab_id
                    )
                    
                    # Create button
                    dpg.add_button(
                        label="Create",
                        callback=self._on_create_preset_from_file,
                        user_data=dialog_id,
                        width=100,
                        parent=file_tab_id
                    )
                    
            # Cancel button
            dpg.add_button(
                label="Cancel",
                callback=lambda s, a, u: dpg.delete_item(u),
                user_data=dialog_id,
                width=100
            )
            
    @error_boundary
    def _on_create_preset_from_current(self, sender, app_data, user_data) -> None:
        """Create a preset from the current architecture."""
        # Close dialog
        dpg.delete_item(user_data)
        
        # Placeholder for now - need an architecture instance
        # This would be provided by a callback in a real implementation
        
        # Show error message for now
        with dpg.window(label="Error", modal=True, width=300, height=100, pos=(400, 200)):
            result_id = dpg.last_item()
            
            dpg.add_text("No current architecture available.")
            dpg.add_text("Please provide an architecture via the set_current_architecture method.")
            dpg.add_button(
                label="OK",
                callback=lambda s, a, u: dpg.delete_item(u),
                user_data=result_id,
                width=100
            )
            
    @error_boundary
    def _on_create_preset_from_template(self, sender, app_data, user_data) -> None:
        """Create a preset from a template."""
        # Get template
        template = dpg.get_value(f"{self.tag}_new_preset_template")
        
        # Get name and description
        name = dpg.get_value(f"{self.tag}_new_preset_template_name")
        description = dpg.get_value(f"{self.tag}_new_preset_template_description")
        tags_str = dpg.get_value(f"{self.tag}_new_preset_template_tags")
        
        # Parse tags
        tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
        
        # Close dialog
        dpg.delete_item(user_data)
        
        # Create architecture from template
        from rfm.core.node_system_base import create_default_architecture, create_rfm_architecture
        
        if template == "Default Architecture":
            architecture = create_default_architecture()
        elif template == "RFM Architecture":
            architecture = create_rfm_architecture()
        else:  # Empty Architecture
            architecture = Architecture()
            
        # Create preset
        preset = ArchitecturePreset(
            architecture=architecture,
            name=name or template,
            description=description or f"Created from {template} template",
            tags=tags
        )
        
        # Add to library
        self.library.add_preset(preset, self.selected_group_id)
        
        # Update UI
        self._update_preset_list()
        
        # Show success message
        with dpg.window(label="Success", modal=True, width=300, height=100, pos=(400, 200)):
            result_id = dpg.last_item()
            
            dpg.add_text(f"Preset '{preset.name}' created successfully.")
            dpg.add_button(
                label="OK",
                callback=lambda s, a, u: dpg.delete_item(u),
                user_data=result_id,
                width=100
            )
            
    @error_boundary
    def _on_create_preset_from_file(self, sender, app_data, user_data) -> None:
        """Create a preset from a file."""
        # Get filepath
        filepath = dpg.get_value(f"{self.tag}_new_preset_file_path")
        
        # Get name and description
        name = dpg.get_value(f"{self.tag}_new_preset_file_name")
        description = dpg.get_value(f"{self.tag}_new_preset_file_description")
        tags_str = dpg.get_value(f"{self.tag}_new_preset_file_tags")
        
        # Parse tags
        tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
        
        # Close dialog
        dpg.delete_item(user_data)
        
        try:
            # Load architecture from file
            architecture = Architecture.load_from_file(filepath)
            
            if architecture:
                # Create preset
                preset = ArchitecturePreset(
                    architecture=architecture,
                    name=name or os.path.basename(filepath),
                    description=description or f"Loaded from {filepath}",
                    tags=tags
                )
                
                # Add to library
                self.library.add_preset(preset, self.selected_group_id)
                
                # Update UI
                self._update_preset_list()
                
                # Show success message
                with dpg.window(label="Success", modal=True, width=300, height=100, pos=(400, 200)):
                    result_id = dpg.last_item()
                    
                    dpg.add_text(f"Preset '{preset.name}' created successfully.")
                    dpg.add_button(
                        label="OK",
                        callback=lambda s, a, u: dpg.delete_item(u),
                        user_data=result_id,
                        width=100
                    )
            else:
                # Show error message
                with dpg.window(label="Error", modal=True, width=300, height=100, pos=(400, 200)):
                    result_id = dpg.last_item()
                    
                    dpg.add_text(f"Failed to load from {filepath}")
                    dpg.add_button(
                        label="OK",
                        callback=lambda s, a, u: dpg.delete_item(u),
                        user_data=result_id,
                        width=100
                    )
        except Exception as e:
            # Show error message
            with dpg.window(label="Error", modal=True, width=400, height=150, pos=(400, 200)):
                result_id = dpg.last_item()
                
                dpg.add_text(f"Error loading architecture: {str(e)}")
                dpg.add_button(
                    label="OK",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=result_id,
                    width=100
                )
                
    @error_boundary
    def _on_remove_clicked(self, sender, app_data) -> None:
        """Handle remove button click."""
        # Check what's selected
        if self.selected_preset_id:
            # Remove preset
            self._on_remove_preset_clicked()
        elif self.selected_group_id:
            # Remove group
            self._on_remove_group_clicked()
            
    @error_boundary
    def _on_remove_preset_clicked(self) -> None:
        """Handle remove preset button click."""
        if not self.selected_preset_id:
            return
            
        # Get selected preset
        preset_info = self.library.get_preset(self.selected_preset_id)
        if not preset_info:
            return
            
        preset, _ = preset_info
        
        # Show confirmation dialog
        with dpg.window(label="Remove Preset", modal=True, width=300, height=150, pos=(400, 200)):
            dialog_id = dpg.last_item()
            
            dpg.add_text(f"Remove preset '{preset.name}'?")
            dpg.add_text("This cannot be undone.")
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Yes",
                    callback=self._remove_selected_preset,
                    user_data=dialog_id,
                    width=100
                )
                dpg.add_button(
                    label="No",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=dialog_id,
                    width=100
                )
                
    def _remove_selected_preset(self, sender, app_data, user_data) -> None:
        """Remove the selected preset."""
        # Close dialog
        dpg.delete_item(user_data)
        
        # Remove preset
        self.library.remove_preset(self.selected_preset_id)
        
        # Clear selection
        self.selected_preset_id = None
        
        # Update UI
        self._update_preset_list()
        
        # Disable details form
        self._enable_details_form(False)
        
    @error_boundary
    def _on_remove_group_clicked(self) -> None:
        """Handle remove group button click."""
        if not self.selected_group_id:
            return
            
        # Get selected group
        group = self.library.get_group(self.selected_group_id)
        if not group:
            return
            
        # Don't allow removing default group
        if group.id == self.library.default_group.id:
            # Show error message
            with dpg.window(label="Error", modal=True, width=300, height=100, pos=(400, 200)):
                dpg.add_text("Cannot remove the default group.")
                dpg.add_button(
                    label="OK",
                    callback=lambda: dpg.delete_item(dpg.last_container()),
                    width=100
                )
                
            return
            
        # Show confirmation dialog
        with dpg.window(label="Remove Group", modal=True, width=300, height=150, pos=(400, 200)):
            dialog_id = dpg.last_item()
            
            dpg.add_text(f"Remove group '{group.name}'?")
            dpg.add_text(f"This will remove {len(group.presets)} presets.")
            dpg.add_text("This cannot be undone.")
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Yes",
                    callback=self._remove_selected_group,
                    user_data=dialog_id,
                    width=100
                )
                dpg.add_button(
                    label="No",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=dialog_id,
                    width=100
                )
                
    def _remove_selected_group(self, sender, app_data, user_data) -> None:
        """Remove the selected group."""
        # Close dialog
        dpg.delete_item(user_data)
        
        # Remove group
        self.library.remove_group(self.selected_group_id)
        
        # Clear selection
        self.selected_group_id = None
        self.selected_preset_id = None
        
        # Update UI
        self._update_group_list()
        
        # Disable details form
        self._enable_details_form(False)
        
    @error_boundary
    def _on_add_group_clicked(self, sender, app_data) -> None:
        """Handle add group button click."""
        # Show dialog for adding a new group
        with dpg.window(label="Add Group", modal=True, width=300, height=200, pos=(400, 200)):
            dialog_id = dpg.last_item()
            
            dpg.add_text("Group Name")
            dpg.add_input_text(
                tag=f"{self.tag}_new_group_name",
                width=-1,
                default_value="New Group"
            )
            
            dpg.add_text("Description")
            dpg.add_input_text(
                tag=f"{self.tag}_new_group_description",
                width=-1,
                height=80,
                multiline=True
            )
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Create",
                    callback=self._create_new_group,
                    user_data=dialog_id,
                    width=100
                )
                dpg.add_button(
                    label="Cancel",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=dialog_id,
                    width=100
                )
                
    def _create_new_group(self, sender, app_data, user_data) -> None:
        """Create a new group."""
        # Get name and description
        name = dpg.get_value(f"{self.tag}_new_group_name")
        description = dpg.get_value(f"{self.tag}_new_group_description")
        
        # Close dialog
        dpg.delete_item(user_data)
        
        # Create group
        group = PresetGroup(
            name=name,
            description=description
        )
        
        # Add to library
        self.library.add_group(group)
        
        # Update UI
        self._update_group_list()
        
        # Select new group
        self.selected_group_id = group.id
        self._update_preset_list()
        
    @error_boundary
    def _on_load_library_clicked(self, sender, app_data) -> None:
        """Handle load library button click."""
        # Show file dialog
        with dpg.window(label="Load Library", modal=True, width=400, height=150, pos=(400, 200)):
            dialog_id = dpg.last_item()
            
            dpg.add_text("Enter the filepath to load:")
            dpg.add_input_text(
                tag=f"{self.tag}_load_library_filepath",
                width=-1,
                hint="preset_library.json"
            )
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Load",
                    callback=self._load_library,
                    user_data=dialog_id,
                    width=100
                )
                dpg.add_button(
                    label="Cancel",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=dialog_id,
                    width=100
                )
                
    def _load_library(self, sender, app_data, user_data) -> None:
        """Load library from file."""
        # Get filepath
        filepath = dpg.get_value(f"{self.tag}_load_library_filepath")
        
        # Close dialog
        dpg.delete_item(user_data)
        
        # Load library
        library = PresetLibrary.load(filepath)
        
        if library:
            # Set library
            self.library = library
            
            # Clear selection
            self.selected_group_id = None
            self.selected_preset_id = None
            
            # Update UI
            self._update_group_list()
            
            # Disable details form
            self._enable_details_form(False)
            
            # Show success message
            with dpg.window(label="Success", modal=True, width=300, height=100, pos=(400, 200)):
                result_id = dpg.last_item()
                
                dpg.add_text(f"Successfully loaded library from {filepath}")
                dpg.add_button(
                    label="OK",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=result_id,
                    width=100
                )
        else:
            # Show error message
            with dpg.window(label="Error", modal=True, width=300, height=100, pos=(400, 200)):
                result_id = dpg.last_item()
                
                dpg.add_text(f"Failed to load library from {filepath}")
                dpg.add_button(
                    label="OK",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=result_id,
                    width=100
                )
                
    @error_boundary
    def _on_save_library_clicked(self, sender, app_data) -> None:
        """Handle save library button click."""
        # Show file dialog
        with dpg.window(label="Save Library", modal=True, width=400, height=150, pos=(400, 200)):
            dialog_id = dpg.last_item()
            
            dpg.add_text("Enter the filepath to save:")
            dpg.add_input_text(
                tag=f"{self.tag}_save_library_filepath",
                width=-1,
                hint="preset_library.json",
                default_value=self.library.library_path or "preset_library.json"
            )
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Save",
                    callback=self._save_library,
                    user_data=dialog_id,
                    width=100
                )
                dpg.add_button(
                    label="Cancel",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=dialog_id,
                    width=100
                )
                
    def _save_library(self, sender, app_data, user_data) -> None:
        """Save library to file."""
        # Get filepath
        filepath = dpg.get_value(f"{self.tag}_save_library_filepath")
        
        # Close dialog
        dpg.delete_item(user_data)
        
        # Save library
        success = self.library.save(filepath)
        
        # Show result
        if success:
            with dpg.window(label="Success", modal=True, width=300, height=100, pos=(400, 200)):
                result_id = dpg.last_item()
                
                dpg.add_text(f"Successfully saved library to {filepath}")
                dpg.add_button(
                    label="OK",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=result_id,
                    width=100
                )
        else:
            with dpg.window(label="Error", modal=True, width=300, height=100, pos=(400, 200)):
                result_id = dpg.last_item()
                
                dpg.add_text(f"Failed to save library to {filepath}")
                dpg.add_button(
                    label="OK",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=result_id,
                    width=100
                )
                
    def set_current_architecture(self, architecture: Architecture) -> None:
        """
        Set the current architecture.
        
        This allows creating presets from the current architecture.
        
        Args:
            architecture: The current architecture
        """
        self.current_architecture = architecture
        
    def show(self) -> None:
        """Show the preset manager."""
        if self.panel:
            self.panel.show()
            
    def hide(self) -> None:
        """Hide the preset manager."""
        if self.panel:
            self.panel.hide()
            
    def toggle_visibility(self) -> None:
        """Toggle visibility of the preset manager."""
        if self.panel:
            self.panel.toggle_visibility()