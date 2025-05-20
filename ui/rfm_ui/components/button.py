"""
Premium button components for RFM Architecture UI.

This module provides enhanced button components with premium styling and effects.
"""

import dearpygui.dearpygui as dpg
from typing import Optional, Callable, Any, Dict
import time

from rfm_ui.theme import Colors, Spacing, Motion, get_theme


class PremiumButton:
    """
    Premium styled button with animations and effects.
    
    Features:
    - Smooth hover and click animations
    - Custom styling with premium theming
    - Optional icon support
    - Focus state with keyboard navigation
    """
    
    def __init__(self, 
                parent_id: int,
                label: str,
                callback: Optional[Callable] = None,
                width: int = -1,
                height: int = -1,
                tag: Optional[str] = None,
                user_data: Any = None,
                show_label: bool = True,
                icon: Optional[str] = None,
                enabled: bool = True,
                **kwargs):
        """
        Initialize the premium button.
        
        Args:
            parent_id: DearPyGui ID of the parent container
            label: Button label
            callback: Function to call when button is clicked
            width: Width of the button (-1 for auto)
            height: Height of the button (-1 for auto)
            tag: Optional tag for the button
            user_data: Optional user data to pass to the callback
            show_label: Whether to show the label (False for icon-only buttons)
            icon: Optional icon identifier
            enabled: Whether the button is initially enabled
            **kwargs: Additional arguments to pass to add_button
        """
        self.parent_id = parent_id
        self.label = label
        self.callback = callback
        self.width = width
        self.height = height
        self.tag = tag
        self.user_data = user_data
        self.show_label = show_label
        self.icon = icon
        self.enabled = enabled
        self.kwargs = kwargs
        
        # Interaction state
        self._active = False
        self._hovered = False
        self._button_id = None
        self._builtin_callback = self._on_button_click
        
        # Animation state
        self._hover_theme = None
        self._active_theme = None
        self._normal_theme = None
        self._disabled_theme = None
        
        # Create the button
        self._create()
        
    def _create(self) -> None:
        """Create the button component."""
        # Create the display label
        display_label = ""
        if self.show_label:
            display_label = self.label
            
        if self.icon and self.show_label:
            display_label = f"{self.icon} {self.label}"
        elif self.icon:
            display_label = self.icon
            
        # Create the button
        self._button_id = dpg.add_button(
            label=display_label,
            callback=self._builtin_callback if self.enabled else None,
            width=self.width,
            height=self.height,
            tag=self.tag,
            user_data=self.user_data,
            **self.kwargs
        )
        
        # Create themes for different states
        self._create_themes()
        
        # Apply appropriate theme based on initial state
        if self.enabled:
            dpg.bind_item_theme(self._button_id, self._normal_theme)
        else:
            dpg.bind_item_theme(self._button_id, self._disabled_theme)
        
        # Register hover/unhover handlers
        with dpg.item_handler_registry() as handler:
            dpg.add_item_hover_handler(callback=self._on_hover_start)
            dpg.add_item_unhover_handler(callback=self._on_hover_end)
            
        dpg.bind_item_handler_registry(self._button_id, handler)
    
    def _create_themes(self) -> None:
        """Create themes for different button states."""
        # Basic component colors
        bg_color = Colors.STONE
        hover_color = Colors.CONTROL_HOVER
        active_color = Colors.CONTROL_ACTIVE
        text_color = Colors.TEXT_PRIMARY
        disabled_color = Colors.STONE
        disabled_text_color = Colors.TEXT_DISABLED
        
        # Normal state theme
        with dpg.theme() as self._normal_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, bg_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, hover_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, active_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Text, text_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, Spacing.RADIUS_MD, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, [Spacing.MD, Spacing.SM], category=dpg.mvThemeCat_Core)
        
        # Hover state theme with slight glow effect 
        with dpg.theme() as self._hover_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, hover_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, hover_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, active_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Text, text_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, Spacing.RADIUS_MD, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, [Spacing.MD, Spacing.SM], category=dpg.mvThemeCat_Core)
        
        # Active state theme with more prominent color
        with dpg.theme() as self._active_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, active_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, active_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, active_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Text, text_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, Spacing.RADIUS_MD, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, [Spacing.MD, Spacing.SM], category=dpg.mvThemeCat_Core)
        
        # Disabled state theme (grayed out)
        with dpg.theme() as self._disabled_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, disabled_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, disabled_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, disabled_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Text, disabled_text_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, Spacing.RADIUS_MD, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, [Spacing.MD, Spacing.SM], category=dpg.mvThemeCat_Core)
    
    def _on_button_click(self, sender, app_data, user_data=None) -> None:
        """
        Handle button click with animation.
        
        Args:
            sender: ID of the sender item
            app_data: Button app data (unused)
            user_data: User data passed to the callback
        """
        # Simulate button press animation
        self._active = True
        
        # Apply the active theme momentarily
        if dpg.does_item_exist(self._button_id):
            dpg.bind_item_theme(self._button_id, self._active_theme)
            
        # Restore hover theme after a delay
        def _restore_theme():
            self._active = False
            if dpg.does_item_exist(self._button_id):
                if self._hovered:
                    dpg.bind_item_theme(self._button_id, self._hover_theme)
                else:
                    dpg.bind_item_theme(self._button_id, self._normal_theme)
        
        # Schedule theme restoration (animation duration)
        dpg.set_frame_callback(Motion.DURATION_BASE // 16, _restore_theme)  # Convert ms to frames (approx)
        
        # Call the user's callback
        if self.callback:
            # Allow user data override from button creation
            callback_user_data = user_data if user_data is not None else self.user_data
            self.callback(sender, app_data, callback_user_data)
    
    def _on_hover_start(self) -> None:
        """Handle hover start with animation."""
        if not self.enabled:
            return
            
        self._hovered = True
        
        # Don't override active state theme
        if not self._active and dpg.does_item_exist(self._button_id):
            dpg.bind_item_theme(self._button_id, self._hover_theme)
    
    def _on_hover_end(self) -> None:
        """Handle hover end with animation."""
        if not self.enabled:
            return
            
        self._hovered = False
        
        # Don't override active state theme
        if not self._active and dpg.does_item_exist(self._button_id):
            dpg.bind_item_theme(self._button_id, self._normal_theme)
    
    def enable(self) -> None:
        """Enable the button."""
        if not self.enabled and dpg.does_item_exist(self._button_id):
            self.enabled = True
            dpg.configure_item(self._button_id, callback=self._builtin_callback)
            dpg.bind_item_theme(self._button_id, self._normal_theme)
    
    def disable(self) -> None:
        """Disable the button."""
        if self.enabled and dpg.does_item_exist(self._button_id):
            self.enabled = False
            dpg.configure_item(self._button_id, callback=None)
            dpg.bind_item_theme(self._button_id, self._disabled_theme)


class AccentButton(PremiumButton):
    """
    Accent-colored premium button (teal).
    
    A button with the teal accent color for primary actions.
    """
    
    def _create_themes(self) -> None:
        """Create themes for different button states with accent colors."""
        # Accent component colors (teal)
        bg_color = Colors.TEAL_DARK
        hover_color = Colors.TEAL_ACCENT
        active_color = Colors.TEAL_LIGHT
        text_color = Colors.TEXT_PRIMARY
        disabled_color = (
            Colors.TEAL_DARK[0] // 2,
            Colors.TEAL_DARK[1] // 2,
            Colors.TEAL_DARK[2] // 2,
            Colors.TEAL_DARK[3]
        )
        disabled_text_color = Colors.TEXT_DISABLED
        
        # Normal state theme
        with dpg.theme() as self._normal_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, bg_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, hover_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, active_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Text, text_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, Spacing.RADIUS_MD, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, [Spacing.MD, Spacing.SM], category=dpg.mvThemeCat_Core)
        
        # Hover state theme with glow effect
        with dpg.theme() as self._hover_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, hover_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, hover_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, active_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Text, text_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, Spacing.RADIUS_MD, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, [Spacing.MD, Spacing.SM], category=dpg.mvThemeCat_Core)
        
        # Active state theme with more prominent color
        with dpg.theme() as self._active_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, active_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, active_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, active_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Text, text_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, Spacing.RADIUS_MD, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, [Spacing.MD, Spacing.SM], category=dpg.mvThemeCat_Core)
        
        # Disabled state theme (grayed out)
        with dpg.theme() as self._disabled_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, disabled_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, disabled_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, disabled_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Text, disabled_text_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, Spacing.RADIUS_MD, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, [Spacing.MD, Spacing.SM], category=dpg.mvThemeCat_Core)


class SecondaryButton(PremiumButton):
    """
    Secondary-colored premium button (amber).
    
    A button with the amber accent color for secondary actions.
    """
    
    def _create_themes(self) -> None:
        """Create themes for different button states with secondary colors."""
        # Secondary component colors (amber)
        bg_color = Colors.AMBER_DARK
        hover_color = Colors.AMBER_ACCENT
        active_color = Colors.AMBER_LIGHT
        text_color = Colors.TEXT_PRIMARY
        disabled_color = (
            Colors.AMBER_DARK[0] // 2,
            Colors.AMBER_DARK[1] // 2,
            Colors.AMBER_DARK[2] // 2,
            Colors.AMBER_DARK[3]
        )
        disabled_text_color = Colors.TEXT_DISABLED
        
        # Normal state theme
        with dpg.theme() as self._normal_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, bg_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, hover_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, active_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Text, text_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, Spacing.RADIUS_MD, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, [Spacing.MD, Spacing.SM], category=dpg.mvThemeCat_Core)
        
        # Hover state theme with glow effect
        with dpg.theme() as self._hover_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, hover_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, hover_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, active_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Text, text_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, Spacing.RADIUS_MD, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, [Spacing.MD, Spacing.SM], category=dpg.mvThemeCat_Core)
        
        # Active state theme with more prominent color
        with dpg.theme() as self._active_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, active_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, active_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, active_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Text, text_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, Spacing.RADIUS_MD, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, [Spacing.MD, Spacing.SM], category=dpg.mvThemeCat_Core)
        
        # Disabled state theme (grayed out)
        with dpg.theme() as self._disabled_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, disabled_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, disabled_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, disabled_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Text, disabled_text_color, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, Spacing.RADIUS_MD, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, [Spacing.MD, Spacing.SM], category=dpg.mvThemeCat_Core)