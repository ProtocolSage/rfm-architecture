"""
System Configuration Module for RFM Architecture.

This module provides a comprehensive UI for viewing and editing all aspects of
the RFM Architecture system configuration. It integrates with the configuration
schema and validator to provide a user-friendly interface for managing complex
configuration settings.
"""
import os
import json
from typing import Dict, Any, List, Optional, Tuple, Callable, Union
from pathlib import Path
import logging
import dearpygui.dearpygui as dpg

# Import configuration utilities
from rfm.config.settings import Config, ConfigLoader
from rfm.config.validator import ConfigValidator, ValidationResult

# Import UI components
from ..errors.decorators import error_boundary
from ..healing.decorators import self_healing
from ..theme.tokens import COLORS, SPACING

logger = logging.getLogger(__name__)

# Constants for UI
CONFIG_SECTIONS = [
    {"name": "layout", "label": "Layout", "description": "Grid and layout settings"},
    {"name": "components", "label": "Components", "description": "Component definitions"},
    {"name": "connections", "label": "Connections", "description": "Connection definitions"},
    {"name": "conscious_fields", "label": "Conscious Fields", "description": "Conscious field settings"},
    {"name": "fractals", "label": "Fractals", "description": "Fractal visualization settings"},
    {"name": "morphogen", "label": "Morphogen", "description": "Morphogenetic pattern settings"},
    {"name": "kin_graph", "label": "KIN Graph", "description": "Knowledge Integration Network settings"},
    {"name": "phi_metric", "label": "Phi Metric", "description": "Phi metric settings"},
    {"name": "processing_scales", "label": "Processing Scales", "description": "Processing scale settings"},
    {"name": "animation", "label": "Animation", "description": "Animation settings"},
    {"name": "styling", "label": "Styling", "description": "Global styling settings"}
]

# Field type mappings
FIELD_TYPES = {
    "str": "string",
    "int": "int",
    "float": "float",
    "bool": "bool",
    "list": "array",
    "dict": "object",
    "Dict": "object",
    "List": "array",
    "Any": "any",
    "Optional": "optional"
}


class ConfigEditorField:
    """A field editor for a configuration value."""
    
    def __init__(self, 
                key: str, 
                path: str, 
                value: Any, 
                field_type: str,
                parent_tag: int,
                on_change: Callable[[str, Any], None],
                description: Optional[str] = None,
                required: bool = False,
                constraints: Optional[Dict[str, Any]] = None):
        """
        Initialize a configuration field editor.
        
        Args:
            key: Field key
            path: Full path to the field in the configuration
            value: Current field value
            field_type: Type of the field
            parent_tag: Tag of the parent UI element
            on_change: Callback for value changes
            description: Optional field description
            required: Whether the field is required
            constraints: Optional field constraints
        """
        self.key = key
        self.path = path
        self.value = value
        self.field_type = field_type
        self.parent_tag = parent_tag
        self.on_change = on_change
        self.description = description or ""
        self.required = required
        self.constraints = constraints or {}
        
        self.tag = dpg.generate_uuid()
        self.input_tag = dpg.generate_uuid()
        
        self._create_ui()
    
    def _create_ui(self) -> None:
        """Create the UI for this field."""
        with dpg.group(parent=self.parent_tag, tag=self.tag, horizontal=False):
            # Field label
            label_text = f"{self.key}"
            if self.required:
                label_text += " *"
            
            with dpg.group(horizontal=True):
                dpg.add_text(label_text)
                
                # Add info icon if we have a description
                if self.description:
                    info_tag = dpg.generate_uuid()
                    dpg.add_text(parent=self.tag, tag=info_tag, default_value="(?)") 
                    with dpg.tooltip(info_tag):
                        dpg.add_text(self.description)
            
            # Create the appropriate input widget based on field type
            if self.field_type == "string":
                dpg.add_input_text(
                    parent=self.tag,
                    tag=self.input_tag,
                    default_value=str(self.value) if self.value is not None else "",
                    callback=self._on_text_change,
                    width=-1
                )
            
            elif self.field_type == "int":
                min_val = self.constraints.get("min", -1000000)
                max_val = self.constraints.get("max", 1000000)
                dpg.add_input_int(
                    parent=self.tag,
                    tag=self.input_tag,
                    default_value=int(self.value) if self.value is not None else 0,
                    min_value=min_val,
                    max_value=max_val,
                    callback=self._on_int_change,
                    width=-1
                )
            
            elif self.field_type == "float":
                min_val = self.constraints.get("min", -1000000.0)
                max_val = self.constraints.get("max", 1000000.0)
                dpg.add_input_float(
                    parent=self.tag,
                    tag=self.input_tag,
                    default_value=float(self.value) if self.value is not None else 0.0,
                    min_value=min_val,
                    max_value=max_val,
                    callback=self._on_float_change,
                    width=-1
                )
            
            elif self.field_type == "bool":
                dpg.add_checkbox(
                    parent=self.tag,
                    tag=self.input_tag,
                    default_value=bool(self.value) if self.value is not None else False,
                    callback=self._on_bool_change
                )
            
            elif self.field_type == "array":
                # For arrays, we'll just show a text representation for now
                # A more advanced editor could allow editing array elements
                array_str = json.dumps(self.value) if self.value is not None else "[]"
                dpg.add_input_text(
                    parent=self.tag,
                    tag=self.input_tag,
                    default_value=array_str,
                    callback=self._on_array_change,
                    width=-1
                )
            
            elif self.field_type == "object":
                # For objects, we'll just show a text representation for now
                # The actual editing is handled in the ConfigSectionEditor
                object_str = json.dumps(self.value) if self.value is not None else "{}"
                dpg.add_input_text(
                    parent=self.tag,
                    tag=self.input_tag,
                    default_value=object_str,
                    callback=self._on_object_change,
                    width=-1,
                    readonly=True
                )
                
                # Add a button to open the object editor
                dpg.add_button(
                    parent=self.tag,
                    label="Edit...",
                    callback=self._on_edit_object,
                    width=-1
                )
            
            elif self.field_type == "color":
                # Handle color fields (expected to be hex strings like "#FF0000")
                color_value = self.value if self.value else "#FFFFFF"
                # Convert hex to RGB float values
                try:
                    r, g, b = int(color_value[1:3], 16) / 255.0, int(color_value[3:5], 16) / 255.0, int(color_value[5:7], 16) / 255.0
                except (ValueError, IndexError):
                    r, g, b = 1.0, 1.0, 1.0
                
                dpg.add_color_edit(
                    parent=self.tag,
                    tag=self.input_tag,
                    default_value=[r, g, b],
                    callback=self._on_color_change,
                    width=-1
                )
            
            else:
                # Fallback to a text input for unknown types
                dpg.add_input_text(
                    parent=self.tag,
                    tag=self.input_tag,
                    default_value=str(self.value) if self.value is not None else "",
                    callback=self._on_text_change,
                    width=-1
                )
            
            # Add space between fields
            dpg.add_spacer(height=SPACING["sm"], parent=self.tag)
    
    def _on_text_change(self, sender, app_data) -> None:
        """Handle text input change."""
        self.value = app_data
        self.on_change(self.path, self.value)
    
    def _on_int_change(self, sender, app_data) -> None:
        """Handle integer input change."""
        self.value = int(app_data)
        self.on_change(self.path, self.value)
    
    def _on_float_change(self, sender, app_data) -> None:
        """Handle float input change."""
        self.value = float(app_data)
        self.on_change(self.path, self.value)
    
    def _on_bool_change(self, sender, app_data) -> None:
        """Handle boolean input change."""
        self.value = bool(app_data)
        self.on_change(self.path, self.value)
    
    def _on_array_change(self, sender, app_data) -> None:
        """Handle array input change."""
        try:
            self.value = json.loads(app_data)
            self.on_change(self.path, self.value)
        except json.JSONDecodeError:
            # If invalid JSON, don't update the value
            pass
    
    def _on_object_change(self, sender, app_data) -> None:
        """Handle object input change."""
        try:
            self.value = json.loads(app_data)
            self.on_change(self.path, self.value)
        except json.JSONDecodeError:
            # If invalid JSON, don't update the value
            pass
    
    def _on_edit_object(self, sender, app_data) -> None:
        """Handle edit object button click."""
        # This should be overridden by the parent to open a nested editor
        pass
    
    def _on_color_change(self, sender, app_data) -> None:
        """Handle color input change."""
        # Convert RGB floats to hex string
        r, g, b = app_data
        r_hex = int(r * 255)
        g_hex = int(g * 255)
        b_hex = int(b * 255)
        hex_color = f"#{r_hex:02x}{g_hex:02x}{b_hex:02x}"
        
        self.value = hex_color
        self.on_change(self.path, self.value)
    
    def update_value(self, value: Any) -> None:
        """
        Update the field value.
        
        Args:
            value: New field value
        """
        self.value = value
        
        # Update the UI based on field type
        if self.field_type == "string":
            dpg.set_value(self.input_tag, str(value) if value is not None else "")
        
        elif self.field_type == "int":
            dpg.set_value(self.input_tag, int(value) if value is not None else 0)
        
        elif self.field_type == "float":
            dpg.set_value(self.input_tag, float(value) if value is not None else 0.0)
        
        elif self.field_type == "bool":
            dpg.set_value(self.input_tag, bool(value) if value is not None else False)
        
        elif self.field_type == "array":
            dpg.set_value(self.input_tag, json.dumps(value) if value is not None else "[]")
        
        elif self.field_type == "object":
            dpg.set_value(self.input_tag, json.dumps(value) if value is not None else "{}")
        
        elif self.field_type == "color":
            color_value = value if value else "#FFFFFF"
            try:
                r, g, b = int(color_value[1:3], 16) / 255.0, int(color_value[3:5], 16) / 255.0, int(color_value[5:7], 16) / 255.0
                dpg.set_value(self.input_tag, [r, g, b])
            except (ValueError, IndexError):
                dpg.set_value(self.input_tag, [1.0, 1.0, 1.0])
        
        else:
            dpg.set_value(self.input_tag, str(value) if value is not None else "")


class ConfigSectionEditor:
    """Editor for a section of the configuration."""
    
    def __init__(self, 
                 section_name: str,
                 section_data: Dict[str, Any],
                 parent_tag: int,
                 on_change: Callable[[str, Any], None],
                 root_path: str = ""):
        """
        Initialize a configuration section editor.
        
        Args:
            section_name: Name of the section
            section_data: Data for the section
            parent_tag: Tag of the parent UI element
            on_change: Callback for configuration changes
            root_path: Root path for this section
        """
        self.section_name = section_name
        self.section_data = section_data or {}
        self.parent_tag = parent_tag
        self.on_change = on_change
        self.root_path = root_path
        self.path = f"{root_path}.{section_name}" if root_path else section_name
        
        self.tag = dpg.generate_uuid()
        self.fields: Dict[str, ConfigEditorField] = {}
        
        self._create_ui()
    
    @error_boundary
    def _create_ui(self) -> None:
        """Create the UI for this section."""
        with dpg.group(parent=self.parent_tag, tag=self.tag):
            # Create fields for all values in this section
            for key, value in self.section_data.items():
                # Skip empty or None values
                if value is None:
                    continue
                
                # Get field type
                field_type = self._get_field_type(value)
                field_path = f"{self.path}.{key}"
                
                # Define field constraints based on key and known schema
                constraints = self._get_field_constraints(key, field_type)
                
                # Define field description based on key
                description = self._get_field_description(key)
                
                # Determine if field is required
                required = self._is_field_required(key)
                
                # Add the field
                self.fields[key] = ConfigEditorField(
                    key=key,
                    path=field_path,
                    value=value,
                    field_type=field_type,
                    parent_tag=self.tag,
                    on_change=self.on_change,
                    description=description,
                    required=required,
                    constraints=constraints
                )
    
    def _get_field_type(self, value: Any) -> str:
        """
        Determine the field type based on the value.
        
        Args:
            value: The value to check
            
        Returns:
            Field type string
        """
        if isinstance(value, str):
            # Check if this looks like a color
            if value.startswith("#") and (len(value) == 7 or len(value) == 9):
                return "color"
            return "string"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, bool):
            return "bool"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        else:
            # Default to string for unknown types
            return "string"
    
    def _get_field_constraints(self, key: str, field_type: str) -> Dict[str, Any]:
        """
        Get constraints for a field based on its key and type.
        
        Args:
            key: Field key
            field_type: Field type
            
        Returns:
            Dictionary of constraints
        """
        constraints = {}
        
        # Define constraints based on field name and type
        if field_type == "int" or field_type == "float":
            if key in ["width", "height", "size", "zoom", "depth"]:
                constraints["min"] = 1
            elif key in ["opacity", "alpha"]:
                constraints["min"] = 0.0
                constraints["max"] = 1.0
            elif key in ["angle", "rotation"]:
                constraints["min"] = 0
                constraints["max"] = 360
        
        return constraints
    
    def _get_field_description(self, key: str) -> Optional[str]:
        """
        Get a description for a field based on its key.
        
        Args:
            key: Field key
            
        Returns:
            Field description or None
        """
        # Field descriptions based on common keys
        descriptions = {
            "width": "Width dimension",
            "height": "Height dimension",
            "position": "Position coordinates [x, y]",
            "size": "Size dimensions [width, height]",
            "color": "Color (hex format, e.g. #FF0000)",
            "label": "Display label",
            "description": "Descriptive text",
            "zorder": "Z-ordering for rendering (higher values appear on top)",
            "source": "Source component ID",
            "target": "Target component ID",
            "curve": "Curve factor for connections",
            "bidirectional": "Whether connection is bidirectional",
            "type": "Type identifier",
            "depth": "Recursion or nesting depth",
            "origin": "Origin coordinates [x, y]",
            "golden_ratio": "Golden ratio value for layout",
            "angle": "Angle in degrees",
            "alpha": "Opacity/alpha value (0-1)",
            "enabled": "Whether feature is enabled",
            "duration": "Duration in milliseconds",
            "fps": "Frames per second",
            "axiom": "Initial axiom for L-systems",
            "rules": "Production rules for L-systems",
            "center": "Center coordinates [x, y]",
            "zoom": "Zoom level",
            "max_iter": "Maximum iterations",
            "cmap": "Colormap name",
            "c_real": "Real part of complex parameter",
            "c_imag": "Imaginary part of complex parameter",
            "gap_ratio": "Gap ratio (0-1)",
            "pulse_count": "Number of pulses",
            "easing": "Easing function specification",
            "glow": "Whether glow effect is enabled",
            "background": "Background color",
            "border": "Border color",
            "blur": "Blur radius",
            "opacity": "Opacity value (0-1)"
        }
        
        return descriptions.get(key)
    
    def _is_field_required(self, key: str) -> bool:
        """
        Determine if a field is required based on its key.
        
        Args:
            key: Field key
            
        Returns:
            True if field is required, False otherwise
        """
        # Required fields based on section and key
        if self.section_name == "layout" and key in ["width", "height"]:
            return True
        elif self.section_name == "components" and key in ["position", "size"]:
            return True
        elif self.section_name == "connections" and key in ["source", "target"]:
            return True
        elif self.section_name == "fractals" and key in ["type", "parameters"]:
            return True
        
        return False
    
    def update_section(self, section_data: Dict[str, Any]) -> None:
        """
        Update the section data.
        
        Args:
            section_data: New section data
        """
        self.section_data = section_data or {}
        
        # Update existing fields
        for key, value in self.section_data.items():
            if key in self.fields:
                self.fields[key].update_value(value)
            else:
                # New field, recreate the UI
                self._create_ui()
                return
        
        # Check for removed fields
        for key in list(self.fields.keys()):
            if key not in self.section_data:
                # Field was removed, recreate the UI
                self._create_ui()
                return


class SystemConfigEditor:
    """
    Main system configuration editor component.
    
    This component provides a UI for viewing and editing all aspects of the
    RFM Architecture system configuration.
    """
    
    def __init__(self, parent_tag: int):
        """
        Initialize the system configuration editor.
        
        Args:
            parent_tag: Tag of the parent UI element
        """
        self.parent_tag = parent_tag
        self.config: Optional[Config] = None
        self.config_path: Optional[str] = None
        
        # UI elements
        self.main_window = dpg.generate_uuid()
        self.sidebar = dpg.generate_uuid()
        self.content_area = dpg.generate_uuid()
        self.status_bar = dpg.generate_uuid()
        
        # Track the active section
        self.active_section: Optional[str] = None
        self.section_editors: Dict[str, ConfigSectionEditor] = {}
        
        # Listen for config file changes
        self.file_watcher_timer = dpg.generate_uuid()
        self.last_modified_time: Optional[float] = None
        
        # Create the UI
        self._create_ui()
        
        # Initial load
        self._load_default_config()
    
    @error_boundary
    def _create_ui(self) -> None:
        """Create the UI for the system configuration editor."""
        with dpg.group(parent=self.parent_tag, tag=self.main_window):
            # Menu bar
            with dpg.group(horizontal=True):
                dpg.add_button(label="Load Config", callback=self._on_load_config)
                dpg.add_button(label="Save Config", callback=self._on_save_config)
                dpg.add_button(label="Validate", callback=self._on_validate_config)
                dpg.add_button(label="Reset", callback=self._on_reset_config)
            
            dpg.add_separator()
            
            # Main layout
            with dpg.group(horizontal=True):
                # Left sidebar for section navigation
                with dpg.child_window(width=250, tag=self.sidebar):
                    dpg.add_text("Configuration Sections")
                    dpg.add_separator()
                    
                    for section in CONFIG_SECTIONS:
                        section_button = dpg.add_button(
                            label=section["label"],
                            callback=self._on_section_select,
                            user_data=section["name"],
                            width=-1
                        )
                        with dpg.tooltip(section_button):
                            dpg.add_text(section["description"])
                
                # Main content area for section editing
                with dpg.child_window(tag=self.content_area, width=-1):
                    # Content will be populated when a section is selected
                    pass
            
            # Status bar
            with dpg.group(horizontal=True, tag=self.status_bar):
                dpg.add_text("No configuration loaded")
                
                # Add timer for file watching
                dpg.add_timer(callback=self._check_file_changes, time=2.0, tag=self.file_watcher_timer)
    
    def _on_section_select(self, sender, app_data, user_data) -> None:
        """
        Handle section selection.
        
        Args:
            sender: UI element that triggered the callback
            app_data: Data from the sender
            user_data: User data from the sender (section name)
        """
        if not self.config:
            return
        
        section_name = user_data
        self.active_section = section_name
        
        # Clear the content area
        dpg.delete_item(self.content_area, children_only=True)
        
        # Add section title
        section_info = next((s for s in CONFIG_SECTIONS if s["name"] == section_name), None)
        if section_info:
            with dpg.group(parent=self.content_area):
                dpg.add_text(f"{section_info['label']} Configuration")
                dpg.add_text(section_info["description"], color=[150, 150, 150])
                dpg.add_separator()
        
        # Get section data from config
        section_data = getattr(self.config, section_name, {})
        
        if section_name not in self.section_editors:
            # Create a new section editor
            self.section_editors[section_name] = ConfigSectionEditor(
                section_name=section_name,
                section_data=section_data,
                parent_tag=self.content_area,
                on_change=self._on_config_change
            )
        else:
            # Update existing section editor
            self.section_editors[section_name].update_section(section_data)
    
    def _on_config_change(self, path: str, value: Any) -> None:
        """
        Handle configuration changes.
        
        Args:
            path: Path to the changed value
            value: New value
        """
        if not self.config:
            return
        
        # Parse the path to update the config object
        parts = path.split(".")
        target = self.config.to_dict()
        current = target
        
        # Navigate to the parent object
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Update the value
        current[parts[-1]] = value
        
        # Update the config object
        self.config = Config.from_dict(target)
        
        # Update status
        dpg.set_value(self.status_bar, f"Configuration modified (unsaved)")
    
    def _on_load_config(self) -> None:
        """Handle load config button."""
        # Create a file dialog to select a config file
        with dpg.file_dialog(
            directory_selector=False,
            show=True,
            modal=True,
            callback=self._on_file_selected,
            file_count=1,
            tag="file_dialog_load",
            width=700,
            height=400
        ):
            dpg.add_file_extension(".yaml", color=[0, 255, 0])
            dpg.add_file_extension(".yml", color=[0, 255, 0])
            dpg.add_file_extension(".*")
    
    def _on_file_selected(self, sender, app_data) -> None:
        """
        Handle file selection.
        
        Args:
            sender: UI element that triggered the callback
            app_data: Data from the sender (file path)
        """
        # Get the selected file path
        file_paths = app_data["selections"]
        if not file_paths:
            return
        
        file_path = file_paths[0]
        
        try:
            # Load the config from the file
            config = ConfigLoader.from_file(file_path, validate=False)
            self.config = config
            self.config_path = file_path
            
            # Update the UI
            if self.active_section:
                self._on_section_select(None, None, self.active_section)
            
            # Update status
            dpg.set_value(self.status_bar, f"Loaded configuration from {os.path.basename(file_path)}")
            
            # Store the last modified time for file watching
            self.last_modified_time = os.path.getmtime(file_path)
        
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            # Show error message
            with dpg.window(label="Error", modal=True, width=400, height=200):
                dpg.add_text(f"Error loading configuration: {e}")
                dpg.add_button(label="OK", callback=lambda: dpg.delete_item(dpg.get_item_parent(dpg.get_item_callback_sender())))
    
    def _on_save_config(self) -> None:
        """Handle save config button."""
        if not self.config:
            return
        
        # Create a file dialog to select a save location
        with dpg.file_dialog(
            directory_selector=False,
            show=True,
            modal=True,
            default_filename=os.path.basename(self.config_path) if self.config_path else "config.yaml",
            callback=self._on_save_location_selected,
            tag="file_dialog_save",
            width=700,
            height=400
        ):
            dpg.add_file_extension(".yaml", color=[0, 255, 0])
            dpg.add_file_extension(".yml", color=[0, 255, 0])
            dpg.add_file_extension(".*")
    
    def _on_save_location_selected(self, sender, app_data) -> None:
        """
        Handle save location selection.
        
        Args:
            sender: UI element that triggered the callback
            app_data: Data from the sender (file path)
        """
        if not self.config:
            return
        
        # Get the selected file path
        file_path = app_data["file_path_name"]
        if not file_path:
            return
        
        try:
            # Ensure the file has a YAML extension
            if not file_path.endswith(".yaml") and not file_path.endswith(".yml"):
                file_path += ".yaml"
            
            # Convert config to dict and save
            config_dict = self.config.to_dict()
            
            with open(file_path, "w") as f:
                yaml.dump(config_dict, f, default_flow_style=False)
            
            self.config_path = file_path
            
            # Update status
            dpg.set_value(self.status_bar, f"Saved configuration to {os.path.basename(file_path)}")
            
            # Update the last modified time
            self.last_modified_time = os.path.getmtime(file_path)
        
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            # Show error message
            with dpg.window(label="Error", modal=True, width=400, height=200):
                dpg.add_text(f"Error saving configuration: {e}")
                dpg.add_button(label="OK", callback=lambda: dpg.delete_item(dpg.get_item_parent(dpg.get_item_callback_sender())))
    
    def _on_validate_config(self) -> None:
        """Handle validate config button."""
        if not self.config:
            return
        
        # Validate the configuration
        is_valid, error_message = self.config.validate()
        
        # Show validation result
        with dpg.window(label="Validation Result", modal=True, width=500, height=300):
            if is_valid:
                dpg.add_text("Configuration is valid!", color=[0, 255, 0])
            else:
                dpg.add_text("Configuration has errors:", color=[255, 0, 0])
                dpg.add_separator()
                
                with dpg.child_window(height=-35):
                    dpg.add_text(error_message)
            
            dpg.add_button(
                label="OK", 
                callback=lambda: dpg.delete_item(dpg.get_item_parent(dpg.get_item_callback_sender())),
                width=-1
            )
    
    def _on_reset_config(self) -> None:
        """Handle reset config button."""
        # Ask for confirmation
        with dpg.window(label="Confirm Reset", modal=True, width=300, height=150):
            dpg.add_text("Are you sure you want to reset the configuration?")
            dpg.add_text("This will discard all unsaved changes.")
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Yes",
                    callback=self._confirm_reset,
                    width=140
                )
                dpg.add_button(
                    label="No",
                    callback=lambda: dpg.delete_item(dpg.get_item_parent(dpg.get_item_callback_sender())),
                    width=140
                )
    
    def _confirm_reset(self) -> None:
        """Confirm and perform configuration reset."""
        # Close the confirmation dialog
        dpg.delete_item(dpg.get_item_parent(dpg.get_item_callback_sender()))
        
        if self.config_path:
            # Reload from file
            try:
                self.config = ConfigLoader.from_file(self.config_path, validate=False)
                
                # Update the UI
                if self.active_section:
                    self._on_section_select(None, None, self.active_section)
                
                # Update status
                dpg.set_value(self.status_bar, f"Reloaded configuration from {os.path.basename(self.config_path)}")
            except Exception as e:
                logger.error(f"Error reloading configuration: {e}")
        else:
            # Load default
            self._load_default_config()
    
    def _load_default_config(self) -> None:
        """Load the default configuration."""
        try:
            # Try to load from the standard locations
            config_path = None
            for path in ["config.yaml", Path.home() / ".rfm" / "config.yaml"]:
                if os.path.exists(path):
                    config_path = path
                    break
            
            if config_path:
                self.config = ConfigLoader.from_file(config_path, validate=False)
                self.config_path = config_path
                
                # Update status
                dpg.set_value(self.status_bar, f"Loaded configuration from {os.path.basename(config_path)}")
                
                # Store the last modified time
                self.last_modified_time = os.path.getmtime(config_path)
            else:
                # No config file found, create a new empty config
                self.config = Config()
                self.config_path = None
                
                # Update status
                dpg.set_value(self.status_bar, "Created new configuration (unsaved)")
        
        except Exception as e:
            logger.error(f"Error loading default configuration: {e}")
            # Create an empty config
            self.config = Config()
            self.config_path = None
            
            # Update status
            dpg.set_value(self.status_bar, "Error loading default configuration, created new configuration (unsaved)")
    
    @self_healing(strategy="reload_on_error")
    def _check_file_changes(self) -> None:
        """Check for changes to the configuration file."""
        if not self.config_path or not self.last_modified_time:
            return
        
        try:
            # Check if the file has been modified
            current_mtime = os.path.getmtime(self.config_path)
            
            if current_mtime > self.last_modified_time:
                # File has changed, ask if we should reload
                with dpg.window(label="File Changed", modal=True, width=400, height=150):
                    dpg.add_text(f"The configuration file has been modified externally.")
                    dpg.add_text("Do you want to reload it? Unsaved changes will be lost.")
                    
                    with dpg.group(horizontal=True):
                        dpg.add_button(
                            label="Reload",
                            callback=self._confirm_reload,
                            width=185
                        )
                        dpg.add_button(
                            label="Keep Current",
                            callback=lambda: dpg.delete_item(dpg.get_item_parent(dpg.get_item_callback_sender())),
                            width=185
                        )
                
                # Update the last modified time to avoid repeated dialogs
                self.last_modified_time = current_mtime
        
        except Exception as e:
            logger.error(f"Error checking file changes: {e}")
    
    def _confirm_reload(self) -> None:
        """Confirm and perform configuration reload."""
        # Close the confirmation dialog
        dpg.delete_item(dpg.get_item_parent(dpg.get_item_callback_sender()))
        
        if self.config_path:
            # Reload from file
            try:
                self.config = ConfigLoader.from_file(self.config_path, validate=False)
                
                # Update the UI
                if self.active_section:
                    self._on_section_select(None, None, self.active_section)
                
                # Update status
                dpg.set_value(self.status_bar, f"Reloaded configuration from {os.path.basename(self.config_path)}")
                
                # Update the last modified time
                self.last_modified_time = os.path.getmtime(self.config_path)
            
            except Exception as e:
                logger.error(f"Error reloading configuration: {e}")


class ConfigComparisonTool:
    """Tool for comparing configurations."""
    
    def __init__(self, parent_tag: int):
        """
        Initialize the configuration comparison tool.
        
        Args:
            parent_tag: Tag of the parent UI element
        """
        self.parent_tag = parent_tag
        self.left_config: Optional[Config] = None
        self.right_config: Optional[Config] = None
        
        # UI elements
        self.main_window = dpg.generate_uuid()
        self.left_path_text = dpg.generate_uuid()
        self.right_path_text = dpg.generate_uuid()
        self.diff_window = dpg.generate_uuid()
        
        # Create the UI
        self._create_ui()
    
    @error_boundary
    def _create_ui(self) -> None:
        """Create the UI for the configuration comparison tool."""
        with dpg.group(parent=self.parent_tag, tag=self.main_window):
            # Header
            dpg.add_text("Configuration Comparison Tool")
            dpg.add_text("Compare two configuration files to identify differences", color=[150, 150, 150])
            dpg.add_separator()
            
            # Load file buttons
            with dpg.group(horizontal=True):
                with dpg.group():
                    dpg.add_button(label="Load Left Config", callback=self._on_load_left)
                    dpg.add_text("No file loaded", tag=self.left_path_text)
                
                dpg.add_separator(direction=1)
                
                with dpg.group():
                    dpg.add_button(label="Load Right Config", callback=self._on_load_right)
                    dpg.add_text("No file loaded", tag=self.right_path_text)
            
            dpg.add_separator()
            
            # Compare button
            dpg.add_button(label="Compare Configurations", callback=self._on_compare, enabled=False)
            
            # Diff display area
            with dpg.child_window(tag=self.diff_window, height=400):
                dpg.add_text("Load two configurations to compare")
    
    def _on_load_left(self) -> None:
        """Handle load left config button."""
        with dpg.file_dialog(
            directory_selector=False,
            show=True,
            modal=True,
            callback=self._on_left_file_selected,
            file_count=1,
            tag="file_dialog_left",
            width=700,
            height=400
        ):
            dpg.add_file_extension(".yaml", color=[0, 255, 0])
            dpg.add_file_extension(".yml", color=[0, 255, 0])
            dpg.add_file_extension(".*")
    
    def _on_load_right(self) -> None:
        """Handle load right config button."""
        with dpg.file_dialog(
            directory_selector=False,
            show=True,
            modal=True,
            callback=self._on_right_file_selected,
            file_count=1,
            tag="file_dialog_right",
            width=700,
            height=400
        ):
            dpg.add_file_extension(".yaml", color=[0, 255, 0])
            dpg.add_file_extension(".yml", color=[0, 255, 0])
            dpg.add_file_extension(".*")
    
    def _on_left_file_selected(self, sender, app_data) -> None:
        """Handle left file selection."""
        file_paths = app_data["selections"]
        if not file_paths:
            return
        
        file_path = file_paths[0]
        
        try:
            # Load the config from the file
            self.left_config = ConfigLoader.from_file(file_path, validate=False)
            
            # Update UI
            dpg.set_value(self.left_path_text, os.path.basename(file_path))
            
            # Enable compare button if both configs are loaded
            if self.left_config and self.right_config:
                dpg.enable_item("Compare Configurations")
        
        except Exception as e:
            logger.error(f"Error loading left configuration: {e}")
            # Show error message
            with dpg.window(label="Error", modal=True, width=400, height=200):
                dpg.add_text(f"Error loading configuration: {e}")
                dpg.add_button(label="OK", callback=lambda: dpg.delete_item(dpg.get_item_parent(dpg.get_item_callback_sender())))
    
    def _on_right_file_selected(self, sender, app_data) -> None:
        """Handle right file selection."""
        file_paths = app_data["selections"]
        if not file_paths:
            return
        
        file_path = file_paths[0]
        
        try:
            # Load the config from the file
            self.right_config = ConfigLoader.from_file(file_path, validate=False)
            
            # Update UI
            dpg.set_value(self.right_path_text, os.path.basename(file_path))
            
            # Enable compare button if both configs are loaded
            if self.left_config and self.right_config:
                dpg.enable_item("Compare Configurations")
        
        except Exception as e:
            logger.error(f"Error loading right configuration: {e}")
            # Show error message
            with dpg.window(label="Error", modal=True, width=400, height=200):
                dpg.add_text(f"Error loading configuration: {e}")
                dpg.add_button(label="OK", callback=lambda: dpg.delete_item(dpg.get_item_parent(dpg.get_item_callback_sender())))
    
    def _on_compare(self) -> None:
        """Handle compare button."""
        if not self.left_config or not self.right_config:
            return
        
        # Convert configs to dictionaries
        left_dict = self.left_config.to_dict()
        right_dict = self.right_config.to_dict()
        
        # Generate diff report
        diff_results = self._compare_configs(left_dict, right_dict)
        
        # Clear the diff window
        dpg.delete_item(self.diff_window, children_only=True)
        
        if not diff_results:
            dpg.add_text("No differences found", parent=self.diff_window, color=[0, 255, 0])
            return
        
        # Display the differences
        dpg.add_text(f"Found {len(diff_results)} differences", parent=self.diff_window)
        dpg.add_separator(parent=self.diff_window)
        
        for diff in diff_results:
            with dpg.group(parent=self.diff_window):
                # Path with color based on diff type
                if diff["type"] == "added":
                    path_color = [0, 255, 0]  # Green for added
                elif diff["type"] == "removed":
                    path_color = [255, 0, 0]  # Red for removed
                else:
                    path_color = [255, 255, 0]  # Yellow for changed
                
                dpg.add_text(f"{diff['path']} ({diff['type']})", color=path_color)
                
                # Show values for changed items
                if diff["type"] == "changed":
                    dpg.add_text(f"  Left: {diff['left_value']}", color=[150, 150, 255])
                    dpg.add_text(f"  Right: {diff['right_value']}", color=[255, 150, 150])
                
                # Separator between diff entries
                dpg.add_separator(parent=self.diff_window)
    
    def _compare_configs(self, left: Dict[str, Any], right: Dict[str, Any], 
                        path: str = "") -> List[Dict[str, Any]]:
        """
        Compare two configurations.
        
        Args:
            left: Left configuration dictionary
            right: Right configuration dictionary
            path: Current path in the configuration
            
        Returns:
            List of diff results
        """
        results = []
        
        # Compare keys in left that are not in right (removed)
        for key in left:
            if key not in right:
                results.append({
                    "path": f"{path}.{key}" if path else key,
                    "type": "removed",
                    "left_value": left[key]
                })
        
        # Compare keys in right that are not in left (added)
        for key in right:
            if key not in left:
                results.append({
                    "path": f"{path}.{key}" if path else key,
                    "type": "added",
                    "right_value": right[key]
                })
        
        # Compare keys in both (changed)
        for key in left:
            if key in right:
                # Get current path
                current_path = f"{path}.{key}" if path else key
                
                # If both are dictionaries, recurse
                if isinstance(left[key], dict) and isinstance(right[key], dict):
                    results.extend(self._compare_configs(left[key], right[key], current_path))
                
                # If both are lists, compare items
                elif isinstance(left[key], list) and isinstance(right[key], list):
                    # Simple length comparison for now
                    if len(left[key]) != len(right[key]):
                        results.append({
                            "path": current_path,
                            "type": "changed",
                            "left_value": f"list with {len(left[key])} items",
                            "right_value": f"list with {len(right[key])} items"
                        })
                    else:
                        # For short lists, compare items
                        if len(left[key]) <= 5:
                            for i, (left_item, right_item) in enumerate(zip(left[key], right[key])):
                                if left_item != right_item:
                                    results.append({
                                        "path": f"{current_path}[{i}]",
                                        "type": "changed",
                                        "left_value": left_item,
                                        "right_value": right_item
                                    })
                
                # Otherwise compare values directly
                elif left[key] != right[key]:
                    results.append({
                        "path": current_path,
                        "type": "changed",
                        "left_value": left[key],
                        "right_value": right[key]
                    })
        
        return results


class SystemConfigManager:
    """
    Main system configuration manager.
    
    This component combines the configuration editor and comparison tool
    into a comprehensive system configuration management UI.
    """
    
    def __init__(self, parent_tag: int):
        """
        Initialize the system configuration manager.
        
        Args:
            parent_tag: Tag of the parent UI element
        """
        self.parent_tag = parent_tag
        
        # UI elements
        self.main_window = dpg.generate_uuid()
        self.tab_bar = dpg.generate_uuid()
        self.editor_tab = dpg.generate_uuid()
        self.comparison_tab = dpg.generate_uuid()
        
        # Sub-components
        self.editor = None
        self.comparison_tool = None
        
        # Create the UI
        self._create_ui()
    
    @error_boundary
    def _create_ui(self) -> None:
        """Create the UI for the system configuration manager."""
        with dpg.group(parent=self.parent_tag, tag=self.main_window):
            # Header
            dpg.add_text("System Configuration Manager")
            dpg.add_text("Manage and compare system configurations", color=[150, 150, 150])
            dpg.add_separator()
            
            # Tab bar
            with dpg.tab_bar(tag=self.tab_bar):
                # Editor tab
                with dpg.tab(label="Configuration Editor", tag=self.editor_tab):
                    # Create the editor
                    self.editor = SystemConfigEditor(self.editor_tab)
                
                # Comparison tab
                with dpg.tab(label="Configuration Comparison", tag=self.comparison_tab):
                    # Create the comparison tool
                    self.comparison_tool = ConfigComparisonTool(self.comparison_tab)
    
    def show(self) -> None:
        """Show the system configuration manager."""
        dpg.show_item(self.main_window)
    
    def hide(self) -> None:
        """Hide the system configuration manager."""
        dpg.hide_item(self.main_window)


# Demo function to run the system configuration manager
def run_system_config_manager():
    """Run the system configuration manager as a standalone application."""
    # Initialize DearPyGui
    dpg.create_context()
    dpg.create_viewport(title="RFM Architecture System Configuration Manager", width=1200, height=800)
    
    # Add a window for the application
    with dpg.window(label="System Config Manager", tag="main_window"):
        # Create the system configuration manager
        config_manager = SystemConfigManager(dpg.last_item())
    
    # Set up the viewport
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("main_window", True)
    
    # Start the main loop
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    run_system_config_manager()