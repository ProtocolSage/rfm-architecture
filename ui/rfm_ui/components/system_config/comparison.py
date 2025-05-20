"""
Configuration comparison tools for RFM Architecture.

This module provides tools for comparing different RFM Architecture configurations.
"""
from __future__ import annotations

import os
import logging
from typing import Dict, Any, List, Optional, Tuple, Set, Union
from dataclasses import dataclass

import dearpygui.dearpygui as dpg

from rfm.config.settings import Config

from ..errors.decorators import error_boundary

from .constants import THEME, SPACING
from .io import ConfigFileManager
from .theme import get_theme
from .controls import PremiumButton, PremiumTextInput

logger = logging.getLogger(__name__)


@dataclass
class ConfigDiff:
    """Represents a difference between two configurations."""
    
    path: str
    type: str  # "added", "removed", "changed"
    left_value: Optional[Any] = None
    right_value: Optional[Any] = None


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
        self.status_text = dpg.generate_uuid()
        self.compare_button = dpg.generate_uuid()
        
        # Search functionality
        self.search_tag = dpg.generate_uuid()
        self.search_text = ""
        
        # Difference filtering
        self.filter_all = dpg.generate_uuid()
        self.filter_added = dpg.generate_uuid()
        self.filter_removed = dpg.generate_uuid()
        self.filter_changed = dpg.generate_uuid()
        
        self.filter_settings = {
            "added": True,
            "removed": True,
            "changed": True,
        }
        
        # Theme
        self.theme = get_theme()
        
        # Diff results
        self.diff_results: List[ConfigDiff] = []
        
        # Create the UI
        self._create_ui()
    
    @error_boundary
    def _create_ui(self) -> None:
        """Create the UI for the configuration comparison tool."""
        with dpg.group(parent=self.parent_tag, tag=self.main_window):
            # Apply theme
            self.theme.apply_to_item(self.main_window)
            
            # Header
            dpg.add_text("Configuration Comparison Tool", color=THEME["primary"])
            dpg.add_text(
                "Compare two configuration files to identify differences",
                color=THEME["text_secondary"],
            )
            dpg.add_separator()
            
            # Load file buttons
            with dpg.group(horizontal=True):
                with dpg.group(width=300):
                    PremiumButton(
                        label="Load Left Config",
                        callback=self._on_load_left,
                        width=-1,
                        parent=dpg.last_item(),
                        icon="📂",
                    )
                    dpg.add_text(
                        "No file loaded",
                        tag=self.left_path_text,
                        color=THEME["text_secondary"],
                    )
                
                dpg.add_separator(direction=1)
                
                with dpg.group(width=300):
                    PremiumButton(
                        label="Load Right Config",
                        callback=self._on_load_right,
                        width=-1,
                        parent=dpg.last_item(),
                        icon="📂",
                    )
                    dpg.add_text(
                        "No file loaded",
                        tag=self.right_path_text,
                        color=THEME["text_secondary"],
                    )
            
            dpg.add_separator()
            
            # Filters and search
            with dpg.group(horizontal=True):
                # Diff type filters
                with dpg.group():
                    dpg.add_text("Filter differences:", color=THEME["primary"])
                    
                    with dpg.group(horizontal=True):
                        dpg.add_checkbox(
                            label="Added",
                            callback=self._on_filter_change,
                            user_data="added",
                            default_value=True,
                            tag=self.filter_added,
                        )
                        dpg.add_checkbox(
                            label="Removed",
                            callback=self._on_filter_change,
                            user_data="removed",
                            default_value=True,
                            tag=self.filter_removed,
                        )
                        dpg.add_checkbox(
                            label="Changed",
                            callback=self._on_filter_change,
                            user_data="changed",
                            default_value=True,
                            tag=self.filter_changed,
                        )
                        dpg.add_checkbox(
                            label="All",
                            callback=self._on_filter_all,
                            default_value=True,
                            tag=self.filter_all,
                        )
                
                dpg.add_spacer(width=20)
                
                # Search box
                with dpg.group():
                    self.search_input = PremiumTextInput(
                        label="Search differences:",
                        callback=self._on_search,
                        width=300,
                        parent=dpg.last_item(),
                        tag=self.search_tag,
                        on_enter=True,
                    )
            
            # Compare button
            PremiumButton(
                label="Compare Configurations",
                callback=self._on_compare,
                width=-1,
                parent=self.main_window,
                icon="🔄",
                tag=self.compare_button,
                disabled=True,
            )
            
            # Status text
            dpg.add_text(
                "Load two configurations to compare",
                tag=self.status_text,
                color=THEME["text_secondary"],
            )
            
            # Diff display area
            with dpg.child_window(tag=self.diff_window, height=400, parent=self.main_window):
                dpg.add_text("Load two configurations to compare")
    
    def _on_filter_change(self, sender, app_data, user_data) -> None:
        """
        Handle filter changes.
        
        Args:
            sender: Sender ID
            app_data: New value
            user_data: Filter type
        """
        self.filter_settings[user_data] = app_data
        
        # Update the "All" checkbox
        all_checked = all(self.filter_settings.values())
        dpg.set_value(self.filter_all, all_checked)
        
        # Update the diff display
        self._filter_diffs()
    
    def _on_filter_all(self, sender, app_data) -> None:
        """
        Handle "All" filter changes.
        
        Args:
            sender: Sender ID
            app_data: New value
        """
        # Set all filters to the same value
        self.filter_settings = {k: app_data for k in self.filter_settings}
        
        # Update individual checkboxes
        dpg.set_value(self.filter_added, app_data)
        dpg.set_value(self.filter_removed, app_data)
        dpg.set_value(self.filter_changed, app_data)
        
        # Update the diff display
        self._filter_diffs()
    
    def _on_search(self, sender, app_data) -> None:
        """
        Handle search input.
        
        Args:
            sender: Sender ID
            app_data: Search text
        """
        self.search_text = app_data.lower()
        
        # Update the diff display
        self._filter_diffs()
    
    def _filter_diffs(self) -> None:
        """Filter diffs based on current filter settings and search text."""
        # Clear the diff window
        dpg.delete_item(self.diff_window, children_only=True)
        
        # Filter diffs
        filtered_diffs = []
        for diff in self.diff_results:
            # Check if diff type is enabled
            if not self.filter_settings.get(diff.type, True):
                continue
            
            # Check if diff matches search text
            if self.search_text:
                # Check path
                if self.search_text not in diff.path.lower():
                    # Check values
                    left_match = False
                    right_match = False
                    
                    if diff.left_value is not None:
                        left_match = self.search_text in str(diff.left_value).lower()
                    
                    if diff.right_value is not None:
                        right_match = self.search_text in str(diff.right_value).lower()
                    
                    if not (left_match or right_match):
                        continue
            
            filtered_diffs.append(diff)
        
        # Update status
        dpg.set_value(
            self.status_text,
            f"Showing {len(filtered_diffs)} of {len(self.diff_results)} differences",
        )
        
        # No diffs to display
        if not filtered_diffs:
            dpg.add_text("No differences match the current filters", parent=self.diff_window)
            return
        
        # Display the filtered diffs
        for diff in filtered_diffs:
            self._add_diff_to_ui(diff)
    
    def _add_diff_to_ui(self, diff: ConfigDiff) -> None:
        """
        Add a diff to the UI.
        
        Args:
            diff: Diff to add
        """
        with dpg.group(parent=self.diff_window):
            # Path with color based on diff type
            if diff.type == "added":
                path_color = THEME["success"]  # Green for added
            elif diff.type == "removed":
                path_color = THEME["error"]  # Red for removed
            else:
                path_color = THEME["warning"]  # Yellow for changed
            
            # Path and type
            with dpg.group(horizontal=True):
                dpg.add_text(f"{diff.path}", color=path_color)
                dpg.add_text(f"({diff.type})", color=path_color)
            
            # Values for changed items
            if diff.type == "changed":
                with dpg.table(header_row=True):
                    dpg.add_table_column(label="Side")
                    dpg.add_table_column(label="Value")
                    
                    with dpg.table_row():
                        dpg.add_text("Left", color=THEME["info"])
                        dpg.add_text(f"{diff.left_value}")
                    
                    with dpg.table_row():
                        dpg.add_text("Right", color=THEME["secondary"])
                        dpg.add_text(f"{diff.right_value}")
            
            # Separator
            dpg.add_separator()
    
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
            height=400,
        ):
            # Apply dark theme
            self.theme.apply_dark_theme(dpg.last_item())
            
            dpg.add_file_extension(".yaml", color=[0, 255, 0])
            dpg.add_file_extension(".yml", color=[0, 255, 0])
            dpg.add_file_extension(".json", color=[0, 255, 0])
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
            height=400,
        ):
            # Apply dark theme
            self.theme.apply_dark_theme(dpg.last_item())
            
            dpg.add_file_extension(".yaml", color=[0, 255, 0])
            dpg.add_file_extension(".yml", color=[0, 255, 0])
            dpg.add_file_extension(".json", color=[0, 255, 0])
            dpg.add_file_extension(".*")
    
    def _on_left_file_selected(self, sender, app_data) -> None:
        """Handle left file selection."""
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
        
        self.left_config = result.config
        
        # Update UI
        dpg.set_value(
            self.left_path_text,
            os.path.basename(file_path),
        )
        
        # Enable compare button if both configs are loaded
        if self.left_config and self.right_config:
            dpg.enable_item(self.compare_button)
    
    def _on_right_file_selected(self, sender, app_data) -> None:
        """Handle right file selection."""
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
        
        self.right_config = result.config
        
        # Update UI
        dpg.set_value(
            self.right_path_text,
            os.path.basename(file_path),
        )
        
        # Enable compare button if both configs are loaded
        if self.left_config and self.right_config:
            dpg.enable_item(self.compare_button)
    
    def _on_compare(self) -> None:
        """Handle compare button."""
        if not self.left_config or not self.right_config:
            return
        
        # Convert configs to dictionaries for easier comparison
        left_dict = self.left_config.to_dict() if self.left_config else {}
        right_dict = self.right_config.to_dict() if self.right_config else {}
        
        # Generate diff report
        self.diff_results = self._compare_configs(left_dict, right_dict)
        
        # Update the UI
        self._filter_diffs()
        
        # Update status
        if not self.diff_results:
            dpg.set_value(
                self.status_text,
                "No differences found",
            )
        else:
            dpg.set_value(
                self.status_text,
                f"Found {len(self.diff_results)} differences",
            )
    
    def _compare_configs(
        self, left: Dict[str, Any], right: Dict[str, Any], path: str = ""
    ) -> List[ConfigDiff]:
        """
        Compare two configurations.
        
        Args:
            left: Left configuration dictionary
            right: Right configuration dictionary
            path: Current path in the configuration
            
        Returns:
            List of differences
        """
        results = []
        
        # Compare keys in left that are not in right (removed)
        for key in left:
            if key not in right:
                results.append(
                    ConfigDiff(
                        path=f"{path}.{key}" if path else key,
                        type="removed",
                        left_value=left[key],
                    )
                )
        
        # Compare keys in right that are not in left (added)
        for key in right:
            if key not in left:
                results.append(
                    ConfigDiff(
                        path=f"{path}.{key}" if path else key,
                        type="added",
                        right_value=right[key],
                    )
                )
        
        # Compare keys in both (changed)
        for key in left:
            if key in right:
                # Get current path
                current_path = f"{path}.{key}" if path else key
                
                # If both are dictionaries, recurse
                if isinstance(left[key], dict) and isinstance(right[key], dict):
                    results.extend(
                        self._compare_configs(left[key], right[key], current_path)
                    )
                
                # If both are lists, compare items
                elif isinstance(left[key], list) and isinstance(right[key], list):
                    # Simple length comparison
                    if len(left[key]) != len(right[key]):
                        results.append(
                            ConfigDiff(
                                path=current_path,
                                type="changed",
                                left_value=f"list with {len(left[key])} items",
                                right_value=f"list with {len(right[key])} items",
                            )
                        )
                    else:
                        # For short lists, compare items
                        if len(left[key]) <= 5:
                            for i, (left_item, right_item) in enumerate(
                                zip(left[key], right[key])
                            ):
                                if left_item != right_item:
                                    results.append(
                                        ConfigDiff(
                                            path=f"{current_path}[{i}]",
                                            type="changed",
                                            left_value=left_item,
                                            right_value=right_item,
                                        )
                                    )
                
                # Otherwise compare values directly
                elif left[key] != right[key]:
                    results.append(
                        ConfigDiff(
                            path=current_path,
                            type="changed",
                            left_value=left[key],
                            right_value=right[key],
                        )
                    )
        
        return results
    
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