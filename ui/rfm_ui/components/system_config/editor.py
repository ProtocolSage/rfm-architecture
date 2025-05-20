"""
System Configuration Editor module.

This module provides a comprehensive UI for editing RFM Architecture configurations.
"""
from __future__ import annotations

import os
import logging
import traceback
from typing import Dict, Any, List, Optional, Tuple, Callable, Set, Union
from dataclasses import dataclass, field

import dearpygui.dearpygui as dpg

from rfm.config.settings import Config

from ..errors.decorators import error_boundary
from ..healing.decorators import self_healing

from .constants import (
    CONFIG_SECTIONS,
    FIELD_DESCRIPTIONS,
    REQUIRED_FIELDS,
    THEME,
    SPACING,
)
from .validation import (
    validate_config,
    get_field_type,
    get_field_constraints,
    ValidationResults,
)
from .io import ConfigFileManager, LoadResult, SaveResult
from .theme import get_theme
from .controls import (
    PremiumTextInput,
    PremiumIntInput,
    PremiumFloatInput,
    PremiumColorInput,
    PremiumCheckbox,
    PremiumCombo,
    PremiumButton,
    PremiumFieldEditor,
)

logger = logging.getLogger(__name__)


class ConfigSectionEditor:
    """Editor for a section of the configuration."""
    
    def __init__(
        self,
        section_name: str,
        section_data: Dict[str, Any],
        parent_tag: int,
        on_change: Callable[[str, Any], None],
        on_edit_object: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        root_path: str = "",
        validation_results: Optional[ValidationResults] = None,
    ):
        """
        Initialize a configuration section editor.
        
        Args:
            section_name: Name of the section
            section_data: Data for the section
            parent_tag: Tag of the parent UI element
            on_change: Callback for configuration changes
            on_edit_object: Callback for editing nested objects
            root_path: Root path for this section
            validation_results: Optional validation results
        """
        self.section_name = section_name
        self.section_data = section_data or {}
        self.parent_tag = parent_tag
        self.on_change = on_change
        self.on_edit_object = on_edit_object
        self.root_path = root_path
        self.path = f"{root_path}.{section_name}" if root_path else section_name
        self.validation_results = validation_results
        
        self.tag = dpg.generate_uuid()
        self.content_tag = dpg.generate_uuid()
        self.search_tag = dpg.generate_uuid()
        self.search_text = ""
        
        self.fields: Dict[str, PremiumFieldEditor] = {}
        self.field_mapping: Dict[str, str] = {}
        
        self.theme = get_theme()
        
        self._create_ui()
    
    @error_boundary
    def _create_ui(self) -> None:
        """Create the UI for this section."""
        with dpg.group(parent=self.parent_tag, tag=self.tag, horizontal=False):
            # Add search box
            with dpg.group(horizontal=True):
                search_input = PremiumTextInput(
                    label="🔍",
                    callback=self._on_search,
                    width=-1,
                    parent=self.tag,
                    tag=self.search_tag,
                    on_enter=True,
                )
            
            # Scrollable content area
            with dpg.child_window(tag=self.content_tag, height=500, parent=self.tag):
                self._create_fields()
    
    def _on_search(self, sender, app_data) -> None:
        """
        Handle search input.
        
        Args:
            sender: Sender widget ID
            app_data: Search text
        """
        self.search_text = app_data.lower()
        
        # Filter fields based on search text
        for key, field in self.fields.items():
            if self.search_text and self.search_text not in key.lower():
                # Hide field if it doesn't match search
                dpg.hide_item(field.tag)
            else:
                # Show field if it matches search
                dpg.show_item(field.tag)
    
    def _create_fields(self) -> None:
        """Create fields for all values in this section."""
        # Get error fields
        error_fields = set()
        if self.validation_results:
            error_fields = self.validation_results.error_fields
        
        # Create fields for all values in this section
        for key, value in self.section_data.items():
            # Skip empty or None values
            if value is None:
                continue
            
            # Get field type
            field_type = get_field_type(value)
            field_path = f"{self.path}.{key}"
            
            # Update field mapping
            self.field_mapping[field_path] = f"{self.tag}_{key}"
            
            # Define field constraints based on key and known schema
            constraints = get_field_constraints(key, field_type)
            
            # Define field description based on key
            description = self._get_field_description(key)
            
            # Determine if field is required
            required = self._is_field_required(key)
            
            # Determine if field has an error
            has_error = f"{self.tag}_{key}" in error_fields
            
            # Add the field
            field = PremiumFieldEditor(
                key=key,
                path=field_path,
                value=value,
                field_type=field_type,
                parent_tag=self.content_tag,
                on_change=self.on_change,
                description=description,
                required=required,
                constraints=constraints,
                error=has_error,
            )
            
            # Store the field
            self.fields[key] = field
            
            # Add object edit callback if provided
            if field_type == "object" and self.on_edit_object:
                original_callback = field._on_edit_object
                
                def edit_object_callback():
                    self.on_edit_object(field_path, value)
                
                field._on_edit_object = edit_object_callback
    
    def _get_field_description(self, key: str) -> Optional[str]:
        """
        Get a description for a field based on its key.
        
        Args:
            key: Field key
            
        Returns:
            Field description or None
        """
        return FIELD_DESCRIPTIONS.get(key)
    
    def _is_field_required(self, key: str) -> bool:
        """
        Determine if a field is required based on its key.
        
        Args:
            key: Field key
            
        Returns:
            True if field is required, False otherwise
        """
        # Required fields based on section and key
        section_required = REQUIRED_FIELDS.get(self.section_name, set())
        return key in section_required
    
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
    
    def update_validation_results(self, validation_results: ValidationResults) -> None:
        """
        Update validation results.
        
        Args:
            validation_results: New validation results
        """
        self.validation_results = validation_results
        
        # Update field error states
        error_fields = validation_results.error_fields if validation_results else set()
        
        for key, field in self.fields.items():
            field_id = f"{self.tag}_{key}"
            has_error = field_id in error_fields
            field.set_error(has_error)


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
        
        # Field mapping for validation
        self.field_mapping: Dict[str, str] = {}
        self.validation_results: Optional[ValidationResults] = None
        
        # Undo/redo history
        self.undo_stack: List[Dict[str, Any]] = []
        self.redo_stack: List[Dict[str, Any]] = []
        self.max_history = 20
        
        # Theme
        self.theme = get_theme()
        self.theme.setup()
        
        # Create the UI
        self._create_ui()
        
        # Initial load
        self._load_default_config()
    
    @error_boundary
    def _create_ui(self) -> None:
        """Create the UI for the system configuration editor."""
        with dpg.group(parent=self.parent_tag, tag=self.main_window):
            # Apply theme
            self.theme.apply_to_item(self.main_window)
            
            # Menu bar
            with dpg.group(horizontal=True):
                # File operations
                PremiumButton(
                    label="Load",
                    callback=self._on_load_config,
                    parent=self.main_window,
                    icon="📂",
                    tooltip="Load configuration from file",
                )
                
                PremiumButton(
                    label="Save",
                    callback=self._on_save_config,
                    parent=self.main_window,
                    icon="💾",
                    tooltip="Save configuration to file",
                )
                
                dpg.add_spacer(width=10)
                
                # Edit operations
                PremiumButton(
                    label="Undo",
                    callback=self._on_undo,
                    parent=self.main_window,
                    icon="↩️",
                    tooltip="Undo last change",
                    primary=False,
                )
                
                PremiumButton(
                    label="Redo",
                    callback=self._on_redo,
                    parent=self.main_window,
                    icon="↪️",
                    tooltip="Redo last undone change",
                    primary=False,
                )
                
                dpg.add_spacer(width=10)
                
                # Validation and reset
                PremiumButton(
                    label="Validate",
                    callback=self._on_validate_config,
                    parent=self.main_window,
                    icon="✓",
                    tooltip="Validate configuration",
                )
                
                PremiumButton(
                    label="Reset",
                    callback=self._on_reset_config,
                    parent=self.main_window,
                    icon="❌",
                    tooltip="Reset to last saved configuration",
                    primary=False,
                )
            
            dpg.add_separator()
            
            # Main layout
            with dpg.group(horizontal=True):
                # Left sidebar for section navigation
                with dpg.child_window(width=250, height=500, tag=self.sidebar):
                    dpg.add_text("Configuration Sections", color=THEME["primary"])
                    dpg.add_separator()
                    
                    section_buttons = {}
                    for section in CONFIG_SECTIONS:
                        button_tag = dpg.generate_uuid()
                        section_buttons[section["name"]] = button_tag
                        
                        # Create button with color indicator
                        with dpg.group(horizontal=True):
                            dpg.add_text(
                                "▐",
                                color=section["color"],
                            )
                            section_button = dpg.add_button(
                                label=section["label"],
                                callback=self._on_section_select,
                                user_data=section["name"],
                                width=-1,
                                tag=button_tag,
                            )
                        
                        with dpg.tooltip(section_button):
                            dpg.add_text(section["description"])
                
                # Main content area for section editing
                with dpg.child_window(tag=self.content_area, width=-1, height=500):
                    # Content will be populated when a section is selected
                    pass
            
            # Status bar
            with dpg.group(horizontal=True, tag=self.status_bar):
                # Status text
                self.status_text = dpg.generate_uuid()
                dpg.add_text("No configuration loaded", tag=self.status_text)
                
                # Add timer for file watching
                dpg.add_timer(
                    callback=self._check_file_changes,
                    time=2.0,
                    tag=self.file_watcher_timer,
                )
    
    def _push_undo(self) -> None:
        """Push current configuration to undo stack."""
        if self.config:
            # Only push if we have changes
            if not self.undo_stack or self.undo_stack[-1] != self.config.to_dict():
                self.undo_stack.append(self.config.to_dict())
                
                # Clear redo stack when making a new change
                self.redo_stack.clear()
                
                # Limit history size
                if len(self.undo_stack) > self.max_history:
                    self.undo_stack.pop(0)
    
    def _on_undo(self) -> None:
        """Handle undo button."""
        if not self.undo_stack:
            return
        
        # Get current config for redo stack
        if self.config:
            self.redo_stack.append(self.config.to_dict())
        
        # Pop from undo stack
        config_dict = self.undo_stack.pop()
        
        # Load config from dict
        self.config = Config.from_dict(config_dict)
        
        # Update UI
        if self.active_section:
            self._update_section_editor(self.active_section)
        
        # Update status
        dpg.set_value(self.status_text, "Undid last change")
    
    def _on_redo(self) -> None:
        """Handle redo button."""
        if not self.redo_stack:
            return
        
        # Get current config for undo stack
        if self.config:
            self.undo_stack.append(self.config.to_dict())
        
        # Pop from redo stack
        config_dict = self.redo_stack.pop()
        
        # Load config from dict
        self.config = Config.from_dict(config_dict)
        
        # Update UI
        if self.active_section:
            self._update_section_editor(self.active_section)
        
        # Update status
        dpg.set_value(self.status_text, "Redid last undone change")
    
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
                with dpg.group(horizontal=True):
                    dpg.add_text(
                        section_info["label"],
                        color=section_info["color"],
                        tag=f"section_title_{section_name}",
                    )
                    
                    # Add icon if available
                    if "icon" in section_info:
                        dpg.add_text(f" {section_info['icon']}")
                    
                dpg.add_text(
                    section_info["description"],
                    color=THEME["text_secondary"],
                )
                dpg.add_separator()
        
        self._update_section_editor(section_name)
    
    def _update_section_editor(self, section_name: str) -> None:
        """
        Update the section editor.
        
        Args:
            section_name: Name of the section
        """
        # Get section data from config
        section_data = getattr(self.config, section_name, {})
        
        if section_name not in self.section_editors:
            # Create a new section editor
            self.section_editors[section_name] = ConfigSectionEditor(
                section_name=section_name,
                section_data=section_data,
                parent_tag=self.content_area,
                on_change=self._on_config_change,
                on_edit_object=self._on_edit_object,
                validation_results=self.validation_results,
            )
        else:
            # Update existing section editor
            self.section_editors[section_name].update_section(section_data)
            
            # Update validation results
            if self.validation_results:
                self.section_editors[section_name].update_validation_results(
                    self.validation_results
                )
    
    def _on_config_change(self, path: str, value: Any) -> None:
        """
        Handle configuration changes.
        
        Args:
            path: Path to the changed value
            value: New value
        """
        if not self.config:
            return
        
        # Push current state to undo stack
        self._push_undo()
        
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
        dpg.set_value(self.status_text, f"Configuration modified (unsaved)")
    
    def _on_edit_object(self, path: str, value: Dict[str, Any]) -> None:
        """
        Handle object editing.
        
        Args:
            path: Path to the object
            value: Object value
        """
        # Open a dialog for editing the object
        with dpg.window(
            label=f"Edit {path}",
            modal=True,
            width=600,
            height=400,
            pos=(100, 100),
        ):
            # Apply dark theme
            self.theme.apply_dark_theme(dpg.last_item())
            
            # Object editor
            editor_tag = dpg.generate_uuid()
            ConfigSectionEditor(
                section_name="object",  # Dummy section name
                section_data=value,
                parent_tag=dpg.last_item(),
                on_change=self._on_nested_object_change,
                root_path=path,  # Use path as root path for proper nesting
            )
            
            # Buttons
            with dpg.group(horizontal=True):
                PremiumButton(
                    label="OK",
                    callback=lambda: dpg.delete_item(dpg.get_item_parent(dpg.last_item())),
                    parent=dpg.last_item(),
                )
    
    def _on_nested_object_change(self, path: str, value: Any) -> None:
        """
        Handle changes in nested objects.
        
        Args:
            path: Path to the changed value
            value: New value
        """
        # Just use the normal config change handler
        self._on_config_change(path, value)
    
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
            height=400,
        ):
            # Apply dark theme
            self.theme.apply_dark_theme(dpg.last_item())
            
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
        
        # Load the config
        result = ConfigFileManager.load_config(file_path, validate=False)
        
        if result.has_error:
            # Show error message
            self._show_error_dialog(
                title="Error Loading Configuration",
                message=result.error_message or "Unknown error",
            )
            return
        
        self.config = result.config
        self.config_path = result.file_path
        
        # Clear undo/redo stacks
        self.undo_stack.clear()
        self.redo_stack.clear()
        
        # Push initial state to undo stack
        self._push_undo()
        
        # Update the UI
        if self.active_section:
            self._update_section_editor(self.active_section)
        
        # Update status
        dpg.set_value(
            self.status_text,
            f"Loaded configuration from {os.path.basename(file_path)}",
        )
        
        # Store the last modified time for file watching
        if self.config_path:
            try:
                self.last_modified_time = os.path.getmtime(self.config_path)
            except OSError:
                self.last_modified_time = None
    
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
            height=400,
        ):
            # Apply dark theme
            self.theme.apply_dark_theme(dpg.last_item())
            
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
        
        # Ensure the file has a YAML extension
        if not file_path.endswith(".yaml") and not file_path.endswith(".yml"):
            file_path += ".yaml"
        
        # Save the config
        result = ConfigFileManager.save_config(self.config, file_path)
        
        if result.has_error:
            # Show error message
            self._show_error_dialog(
                title="Error Saving Configuration",
                message=result.error_message or "Unknown error",
            )
            return
        
        self.config_path = result.file_path
        
        # Update status
        dpg.set_value(
            self.status_text,
            f"Saved configuration to {os.path.basename(file_path)}",
        )
        
        # Update the last modified time
        if self.config_path:
            try:
                self.last_modified_time = os.path.getmtime(self.config_path)
            except OSError:
                self.last_modified_time = None
    
    def _on_validate_config(self) -> None:
        """Handle validate config button."""
        if not self.config:
            return
        
        # Validate the configuration
        try:
            # Get field mapping from section editors
            self.field_mapping = {}
            for section_name, editor in self.section_editors.items():
                self.field_mapping.update(editor.field_mapping)
            
            # Validate the config
            self.validation_results = validate_config(self.config, self.field_mapping)
            
            # Update section editors
            for section_name, editor in self.section_editors.items():
                editor.update_validation_results(self.validation_results)
            
            # Show validation result
            if self.validation_results.is_valid:
                self._show_info_dialog(
                    title="Validation Result",
                    message="Configuration is valid!",
                )
            else:
                self._show_error_dialog(
                    title="Validation Result",
                    message=self.validation_results.get_summary(),
                )
        except Exception as e:
            logger.error(f"Error validating configuration: {e}", exc_info=True)
            self._show_error_dialog(
                title="Validation Error",
                message=f"Error validating configuration: {e}",
            )
    
    def _on_reset_config(self) -> None:
        """Handle reset config button."""
        # Ask for confirmation
        self._show_confirmation_dialog(
            title="Confirm Reset",
            message="Are you sure you want to reset the configuration? This will discard all unsaved changes.",
            callback=self._confirm_reset,
        )
    
    def _confirm_reset(self) -> None:
        """Confirm and perform configuration reset."""
        if not self.config_path:
            # Load default
            self._load_default_config()
            return
        
        # Reload from file
        result = ConfigFileManager.load_config(self.config_path, validate=False)
        
        if result.has_error:
            # Show error message
            self._show_error_dialog(
                title="Error Reloading Configuration",
                message=result.error_message or "Unknown error",
            )
            return
        
        self.config = result.config
        
        # Clear undo/redo stacks
        self.undo_stack.clear()
        self.redo_stack.clear()
        
        # Push initial state to undo stack
        self._push_undo()
        
        # Update the UI
        if self.active_section:
            self._update_section_editor(self.active_section)
        
        # Update status
        dpg.set_value(
            self.status_text,
            f"Reloaded configuration from {os.path.basename(self.config_path)}",
        )
    
    def _load_default_config(self) -> None:
        """Load the default configuration."""
        # Load from the standard locations
        result = ConfigFileManager.load_config(validate=False)
        
        self.config = result.config
        self.config_path = result.file_path
        
        # Clear undo/redo stacks
        self.undo_stack.clear()
        self.redo_stack.clear()
        
        # Push initial state to undo stack
        self._push_undo()
        
        # Update status
        if result.file_path:
            dpg.set_value(
                self.status_text,
                f"Loaded configuration from {os.path.basename(result.file_path)}",
            )
        else:
            dpg.set_value(
                self.status_text,
                "Created new configuration (unsaved)",
            )
        
        # Store the last modified time
        if self.config_path:
            try:
                self.last_modified_time = os.path.getmtime(self.config_path)
            except OSError:
                self.last_modified_time = None
    
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
                self._show_confirmation_dialog(
                    title="File Changed",
                    message=f"The configuration file has been modified externally. Do you want to reload it? Unsaved changes will be lost.",
                    callback=self._confirm_reload,
                )
                
                # Update the last modified time to avoid repeated dialogs
                self.last_modified_time = current_mtime
        except OSError:
            # File might have been deleted or moved
            self.last_modified_time = None
    
    def _confirm_reload(self) -> None:
        """Confirm and perform configuration reload."""
        if not self.config_path:
            return
        
        # Reload from file
        result = ConfigFileManager.load_config(self.config_path, validate=False)
        
        if result.has_error:
            # Show error message
            self._show_error_dialog(
                title="Error Reloading Configuration",
                message=result.error_message or "Unknown error",
            )
            return
        
        self.config = result.config
        
        # Clear undo/redo stacks
        self.undo_stack.clear()
        self.redo_stack.clear()
        
        # Push initial state to undo stack
        self._push_undo()
        
        # Update the UI
        if self.active_section:
            self._update_section_editor(self.active_section)
        
        # Update status
        dpg.set_value(
            self.status_text,
            f"Reloaded configuration from {os.path.basename(self.config_path)}",
        )
        
        # Update the last modified time
        if self.config_path:
            try:
                self.last_modified_time = os.path.getmtime(self.config_path)
            except OSError:
                self.last_modified_time = None
    
    def _show_error_dialog(self, title: str, message: str) -> None:
        """
        Show an error dialog.
        
        Args:
            title: Dialog title
            message: Error message
        """
        with dpg.window(
            label=title,
            modal=True,
            width=500,
            height=300,
        ):
            # Apply dark theme
            self.theme.apply_dark_theme(dpg.last_item())
            
            dpg.add_text(message, color=THEME["error"])
            
            with dpg.group(horizontal=True):
                PremiumButton(
                    label="OK",
                    callback=lambda: dpg.delete_item(dpg.get_item_parent(dpg.last_item())),
                    parent=dpg.last_item(),
                )
    
    def _show_info_dialog(self, title: str, message: str) -> None:
        """
        Show an information dialog.
        
        Args:
            title: Dialog title
            message: Information message
        """
        with dpg.window(
            label=title,
            modal=True,
            width=400,
            height=200,
        ):
            # Apply dark theme
            self.theme.apply_dark_theme(dpg.last_item())
            
            dpg.add_text(message, color=THEME["success"])
            
            with dpg.group(horizontal=True):
                PremiumButton(
                    label="OK",
                    callback=lambda: dpg.delete_item(dpg.get_item_parent(dpg.last_item())),
                    parent=dpg.last_item(),
                )
    
    def _show_confirmation_dialog(self, title: str, message: str, callback: Callable) -> None:
        """
        Show a confirmation dialog.
        
        Args:
            title: Dialog title
            message: Confirmation message
            callback: Callback for confirmation
        """
        with dpg.window(
            label=title,
            modal=True,
            width=400,
            height=200,
        ):
            # Apply dark theme
            self.theme.apply_dark_theme(dpg.last_item())
            
            dpg.add_text(message)
            
            with dpg.group(horizontal=True):
                PremiumButton(
                    label="Yes",
                    callback=lambda: (
                        callback(),
                        dpg.delete_item(dpg.get_item_parent(dpg.get_item_parent(dpg.last_item()))),
                    ),
                    parent=dpg.last_item(),
                )
                
                PremiumButton(
                    label="No",
                    callback=lambda: dpg.delete_item(dpg.get_item_parent(dpg.get_item_parent(dpg.last_item()))),
                    parent=dpg.last_item(),
                    primary=False,
                )