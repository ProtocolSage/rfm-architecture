"""
Premium panel components for RFM Architecture UI.

This module provides enhanced panel components with premium styling and effects.
"""

import dearpygui.dearpygui as dpg
from typing import Optional, Callable, Any, List, Dict, Tuple
import time

from rfm_ui.theme import Colors, Spacing, Motion, get_theme


class GlassPanel:
    """
    Glass morphism panel with translucent effect.
    
    Features:
    - Glass-like translucent appearance
    - Rounded corners
    - Subtle shadow effect
    - Smooth transitions
    """
    
    def __init__(self, 
                parent_id: int,
                label: str = "",
                width: int = -1,
                height: int = -1,
                pos: Optional[Tuple[int, int]] = None,
                show_title_bar: bool = False,
                no_close: bool = True,
                tag: Optional[str] = None,
                on_close: Optional[Callable] = None,
                **kwargs):
        """
        Initialize the glass panel.
        
        Args:
            parent_id: DearPyGui ID of the parent container
            label: Panel label/title
            width: Width of the panel (-1 for auto)
            height: Height of the panel (-1 for auto)
            pos: Optional position (x, y) tuple
            show_title_bar: Whether to show the title bar
            no_close: Whether to disable the close button
            tag: Optional tag for the panel
            on_close: Function to call when panel is closed
            **kwargs: Additional arguments to pass to add_child_window
        """
        self.parent_id = parent_id
        self.label = label
        self.width = width
        self.height = height
        self.pos = pos
        self.show_title_bar = show_title_bar
        self.no_close = no_close
        self.tag = tag
        self.on_close = on_close
        self.kwargs = kwargs
        
        # Internal state
        self._panel_id = None
        self._glass_theme = None
        
        # Create the panel
        self._create()
        
    def _create(self) -> None:
        """Create the glass panel component."""
        # Create glass panel theme
        with dpg.theme() as self._glass_theme:
            with dpg.theme_component(dpg.mvChildWindow):
                # Semi-transparent background
                bg_alpha = 180  # 70% opacity
                panel_bg = (
                    Colors.CARBON[0],
                    Colors.CARBON[1],
                    Colors.CARBON[2],
                    bg_alpha
                )
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, panel_bg, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Border, Colors.STONE, category=dpg.mvThemeCat_Core)
                
                if self.show_title_bar:
                    title_bg = (
                        Colors.STONE[0],
                        Colors.STONE[1],
                        Colors.STONE[2],
                        bg_alpha
                    )
                    dpg.add_theme_color(dpg.mvThemeCol_TitleBg, title_bg, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, Colors.STONE, category=dpg.mvThemeCat_Core)
                
                # Style for glass effect
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, Spacing.RADIUS_LG, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, Spacing.RADIUS_LG, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, Spacing.RADIUS_MD, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, [Spacing.MD, Spacing.MD], category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize, 1, category=dpg.mvThemeCat_Core)
        
        # Create panel with appropriate settings
        self._panel_id = dpg.add_child_window(
            parent=self.parent_id,
            label=self.label,
            width=self.width,
            height=self.height,
            pos=self.pos,
            no_title_bar=not self.show_title_bar,
            no_close=self.no_close,
            tag=self.tag,
            **self.kwargs
        )
        
        # Apply glass theme
        dpg.bind_item_theme(self._panel_id, self._glass_theme)
        
        # Set up close handler if needed
        if not self.no_close and self.on_close:
            dpg.set_item_callback(self._panel_id, self._handle_close)
    
    def _handle_close(self, sender, app_data, user_data=None) -> None:
        """
        Handle panel close event.
        
        Args:
            sender: ID of the sender item
            app_data: Panel app data (unused)
            user_data: User data (unused)
        """
        if self.on_close:
            self.on_close(sender, app_data, user_data)
    
    def get_panel_id(self) -> int:
        """
        Get the panel container ID.
        
        Returns:
            ID of the panel container
        """
        return self._panel_id
    
    def show(self) -> None:
        """Show the panel."""
        if self._panel_id and dpg.does_item_exist(self._panel_id):
            dpg.configure_item(self._panel_id, show=True)
    
    def hide(self) -> None:
        """Hide the panel."""
        if self._panel_id and dpg.does_item_exist(self._panel_id):
            dpg.configure_item(self._panel_id, show=False)
    
    def toggle_visibility(self) -> None:
        """Toggle panel visibility."""
        if self._panel_id and dpg.does_item_exist(self._panel_id):
            is_visible = dpg.is_item_visible(self._panel_id)
            dpg.configure_item(self._panel_id, show=not is_visible)


class CardPanel(GlassPanel):
    """
    Card-style panel with shadow and solid background.
    
    A premium panel with a solid background, rounded corners, and shadow effect.
    """
    
    def _create(self) -> None:
        """Create the card panel component."""
        # Create card panel theme
        with dpg.theme() as self._glass_theme:
            with dpg.theme_component(dpg.mvChildWindow):
                # Solid background with shadow-like border
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, Colors.CARBON, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Border, Colors.STONE, category=dpg.mvThemeCat_Core)
                
                if self.show_title_bar:
                    dpg.add_theme_color(dpg.mvThemeCol_TitleBg, Colors.STONE, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, Colors.CONTROL_ACTIVE, category=dpg.mvThemeCat_Core)
                
                # Style for card effect
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, Spacing.RADIUS_LG, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, Spacing.RADIUS_LG, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, Spacing.RADIUS_MD, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, [Spacing.MD, Spacing.MD], category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize, 1, category=dpg.mvThemeCat_Core)
        
        # Create panel with appropriate settings
        self._panel_id = dpg.add_child_window(
            parent=self.parent_id,
            label=self.label,
            width=self.width,
            height=self.height,
            pos=self.pos,
            no_title_bar=not self.show_title_bar,
            no_close=self.no_close,
            tag=self.tag,
            **self.kwargs
        )
        
        # Apply card theme
        dpg.bind_item_theme(self._panel_id, self._glass_theme)
        
        # Set up close handler if needed
        if not self.no_close and self.on_close:
            dpg.set_item_callback(self._panel_id, self._handle_close)