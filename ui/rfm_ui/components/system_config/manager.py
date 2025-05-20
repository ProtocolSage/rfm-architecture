"""
System Configuration Manager for RFM Architecture.

This module provides a comprehensive UI for managing RFM Architecture configurations,
combining the editor and comparison tools into a unified interface.
"""
from __future__ import annotations

import os
import logging
from typing import Dict, Any, Optional, List

import dearpygui.dearpygui as dpg

from ..errors.decorators import error_boundary

from .constants import THEME
from .theme import get_theme
from .editor import SystemConfigEditor
from .comparison import ConfigComparisonTool

logger = logging.getLogger(__name__)


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
        
        # Theme
        self.theme = get_theme()
        self.theme.setup()
        
        # Sub-components
        self.editor = None
        self.comparison_tool = None
        
        # Initialize
        self._create_ui()
    
    @error_boundary
    def _create_ui(self) -> None:
        """Create the UI for the system configuration manager."""
        with dpg.group(parent=self.parent_tag, tag=self.main_window):
            # Apply theme
            self.theme.apply_to_item(self.main_window)
            
            # Header
            with dpg.group(horizontal=True):
                dpg.add_text(
                    "System Configuration Manager",
                    color=THEME["primary"],
                )
                
                # Version information
                dpg.add_text(
                    "v1.0",
                    color=THEME["text_secondary"],
                )
            
            dpg.add_text(
                "Manage and compare system configurations",
                color=THEME["text_secondary"],
            )
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
    
    def toggle(self) -> None:
        """Toggle visibility of the system configuration manager."""
        if dpg.is_item_visible(self.main_window):
            self.hide()
        else:
            self.show()
    
    def select_tab(self, tab_name: str) -> None:
        """
        Select a tab.
        
        Args:
            tab_name: Tab name ("editor" or "comparison")
        """
        if tab_name == "editor":
            dpg.set_value(self.tab_bar, self.editor_tab)
        elif tab_name == "comparison":
            dpg.set_value(self.tab_bar, self.comparison_tab)