"""
Premium theme implementation for RFM Architecture UI.

This module applies the premium theme tokens to the UI framework (Dear PyGui),
creating a cohesive, high-end visual design system.
"""

import os
import json
from typing import Dict, Any, List, Tuple, Optional
import dearpygui.dearpygui as dpg

from .tokens import Colors, Typography, Spacing, Elevation, Motion


class PremiumTheme:
    """
    Premium theme implementation for RFM Architecture UI.
    
    This class applies theme tokens to create a cohesive, premium visual design
    using the Dear PyGui theming system.
    """
    
    def __init__(self, dark_mode: bool = True, custom_tokens: Optional[Dict[str, Any]] = None):
        """
        Initialize the premium theme.
        
        Args:
            dark_mode: Whether to use dark mode (True) or light mode (False)
            custom_tokens: Optional custom theme tokens to override defaults
        """
        self.dark_mode = dark_mode
        self.custom_tokens = custom_tokens or {}
        self.theme_id = None
        self.active_theme_id = None
        self.toggle_button_id = None
        self._setup_fonts()
        
    def _setup_fonts(self) -> None:
        """Set up fonts for the premium theme."""
        with dpg.font_registry():
            # Define paths to font files based on standard locations
            font_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "fonts")
            
            # Primary font (Inter)
            primary_regular_path = os.path.join(font_dir, "Inter-Regular.ttf")
            primary_medium_path = os.path.join(font_dir, "Inter-Medium.ttf")
            primary_semibold_path = os.path.join(font_dir, "Inter-SemiBold.ttf")
            
            # Secondary font (JetBrains Mono)
            secondary_regular_path = os.path.join(font_dir, "JetBrainsMono-Regular.ttf")
            
            # Fallback to system fonts if the custom fonts don't exist
            if not os.path.exists(primary_regular_path):
                primary_regular_path = os.path.join(font_dir, "Roboto-Regular.ttf")
                
            if not os.path.exists(primary_medium_path):
                primary_medium_path = primary_regular_path
                
            if not os.path.exists(primary_semibold_path):
                primary_semibold_path = primary_regular_path
                
            if not os.path.exists(secondary_regular_path):
                secondary_regular_path = os.path.join(font_dir, "RobotoMono-Regular.ttf")
                
            # Add fonts with appropriate sizes
            if os.path.exists(primary_regular_path):
                self.font_regular = dpg.add_font(primary_regular_path, Typography.FONT_SIZE_BASE)
                self.font_small = dpg.add_font(primary_regular_path, Typography.FONT_SIZE_SMALL)
                self.font_medium = dpg.add_font(primary_medium_path, Typography.FONT_SIZE_MEDIUM)
                self.font_large = dpg.add_font(primary_semibold_path, Typography.FONT_SIZE_LARGE)
                self.font_xl = dpg.add_font(primary_semibold_path, Typography.FONT_SIZE_XL)
            else:
                # Default font fallback if no fonts are available
                self.font_regular = 0
                self.font_small = 0
                self.font_medium = 0
                self.font_large = 0
                self.font_xl = 0
                
            # Add monospace font for code
            if os.path.exists(secondary_regular_path):
                self.font_mono = dpg.add_font(secondary_regular_path, Typography.FONT_SIZE_BASE)
            else:
                self.font_mono = 0
    
    def apply(self) -> None:
        """Apply the premium theme to the UI."""
        # Create theme
        with dpg.theme() as self.theme_id:
            # Global styles
            with dpg.theme_component(dpg.mvAll):
                # Background colors
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, Colors.BACKGROUND, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, Colors.CARBON, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_PopupBg, Colors.CARBON, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, Colors.CARBON, category=dpg.mvThemeCat_Core)
                
                # Text colors
                dpg.add_theme_color(dpg.mvThemeCol_Text, Colors.TEXT_PRIMARY, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, Colors.TEXT_DISABLED, category=dpg.mvThemeCat_Core)
                
                # Border colors
                dpg.add_theme_color(dpg.mvThemeCol_Border, Colors.STONE, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_BorderShadow, (0, 0, 0, 0), category=dpg.mvThemeCat_Core)
                
                # Frame colors (for controls)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, Colors.STONE, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, Colors.CONTROL_HOVER, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, Colors.CONTROL_ACTIVE, category=dpg.mvThemeCat_Core)
                
                # Title colors
                dpg.add_theme_color(dpg.mvThemeCol_TitleBg, Colors.CARBON, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, Colors.STONE, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_TitleBgCollapsed, Colors.CARBON, category=dpg.mvThemeCat_Core)
                
                # Tab colors
                dpg.add_theme_color(dpg.mvThemeCol_Tab, Colors.STONE, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_TabHovered, Colors.CONTROL_HOVER, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_TabActive, Colors.CONTROL_ACTIVE, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_TabUnfocused, Colors.STONE, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_TabUnfocusedActive, Colors.STONE, category=dpg.mvThemeCat_Core)
                
                # Button colors
                dpg.add_theme_color(dpg.mvThemeCol_Button, Colors.STONE, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, Colors.CONTROL_HOVER, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, Colors.CONTROL_ACTIVE, category=dpg.mvThemeCat_Core)
                
                # Header colors (for collapsing headers)
                dpg.add_theme_color(dpg.mvThemeCol_Header, Colors.STONE, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, Colors.CONTROL_HOVER, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, Colors.CONTROL_ACTIVE, category=dpg.mvThemeCat_Core)
                
                # Slider colors
                dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, Colors.TEAL_ACCENT, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, Colors.TEAL_LIGHT, category=dpg.mvThemeCat_Core)
                
                # Scrollbar colors
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, Colors.CARBON, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, Colors.STONE, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, Colors.CONTROL_HOVER, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabActive, Colors.CONTROL_ACTIVE, category=dpg.mvThemeCat_Core)
                
                # Check mark
                dpg.add_theme_color(dpg.mvThemeCol_CheckMark, Colors.TEAL_ACCENT, category=dpg.mvThemeCat_Core)
                
                # Global style settings
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, Spacing.RADIUS_LG, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, Spacing.RADIUS_MD, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, Spacing.RADIUS_MD, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, Spacing.RADIUS_MD, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, Spacing.RADIUS_SM, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_TabRounding, Spacing.RADIUS_SM, category=dpg.mvThemeCat_Core)
                
                # Spacing and sizes
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, [Spacing.MD, Spacing.MD], category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, [Spacing.SM, Spacing.XS], category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, [Spacing.SM, Spacing.SM], category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_ItemInnerSpacing, [Spacing.XS, Spacing.XS], category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_IndentSpacing, Spacing.MD, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize, Spacing.SM, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_GrabMinSize, Spacing.MD, category=dpg.mvThemeCat_Core)
            
            # Create special themes for different components
            
            # Accent buttons
            with dpg.theme_component(dpg.mvButton, enabled_state=True, parent=self.theme_id, tag="accent_button"):
                dpg.add_theme_color(dpg.mvThemeCol_Button, Colors.TEAL_DARK, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, Colors.TEAL_ACCENT, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, Colors.TEAL_LIGHT, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, Spacing.RADIUS_MD, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, [Spacing.MD, Spacing.SM], category=dpg.mvThemeCat_Core)
            
            # Secondary buttons
            with dpg.theme_component(dpg.mvButton, enabled_state=True, parent=self.theme_id, tag="secondary_button"):
                dpg.add_theme_color(dpg.mvThemeCol_Button, Colors.AMBER_DARK, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, Colors.AMBER_ACCENT, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, Colors.AMBER_LIGHT, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, Spacing.RADIUS_MD, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, [Spacing.MD, Spacing.SM], category=dpg.mvThemeCat_Core)
            
            # Slider theme
            with dpg.theme_component(dpg.mvSliderInt, enabled_state=True, parent=self.theme_id, tag="slider_theme"):
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, Colors.CARBON, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, Colors.TEAL_ACCENT, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, Colors.TEAL_LIGHT, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, Spacing.RADIUS_PILL, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_GrabMinSize, Spacing.MD, category=dpg.mvThemeCat_Core)
            
            # Apply the same slider theme to float sliders
            with dpg.theme_component(dpg.mvSliderFloat, enabled_state=True, parent=self.theme_id, tag="slider_float_theme"):
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, Colors.CARBON, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, Colors.TEAL_ACCENT, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, Colors.TEAL_LIGHT, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, Spacing.RADIUS_PILL, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_GrabMinSize, Spacing.MD, category=dpg.mvThemeCat_Core)
            
            # Header theme (for collapsing headers)
            with dpg.theme_component(dpg.mvCollapsingHeader, enabled_state=True, parent=self.theme_id, tag="header_theme"):
                dpg.add_theme_color(dpg.mvThemeCol_Header, Colors.STONE, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, Colors.CONTROL_HOVER, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, Colors.CONTROL_ACTIVE, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, [Spacing.SM, Spacing.SM], category=dpg.mvThemeCat_Core)
            
            # Input text theme
            with dpg.theme_component(dpg.mvInputText, enabled_state=True, parent=self.theme_id, tag="input_theme"):
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, Colors.CARBON, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, Colors.STONE, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, Colors.STONE, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, Spacing.RADIUS_MD, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, [Spacing.SM, Spacing.SM], category=dpg.mvThemeCat_Core)
            
            # Combo box theme
            with dpg.theme_component(dpg.mvCombo, enabled_state=True, parent=self.theme_id, tag="combo_theme"):
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, Colors.CARBON, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, Colors.STONE, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, Colors.STONE, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_PopupBg, Colors.CARBON, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, Spacing.RADIUS_MD, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, Spacing.RADIUS_MD, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, [Spacing.SM, Spacing.SM], category=dpg.mvThemeCat_Core)
            
            # Child window (panels) theme
            with dpg.theme_component(dpg.mvChildWindow, enabled_state=True, parent=self.theme_id, tag="panel_theme"):
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, Colors.CARBON, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, Spacing.RADIUS_LG, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, [Spacing.MD, Spacing.MD], category=dpg.mvThemeCat_Core)
            
            # Active/selected items (with glow effect)
            with dpg.theme_component(dpg.mvAll, item_type=dpg.mvAppItemType_All, enabled_state=True, 
                                    parent=self.theme_id, tag="active_item_theme"):
                dpg.add_theme_color(dpg.mvThemeCol_Text, Colors.TEAL_ACCENT, category=dpg.mvThemeCat_Core)
            
            # Warning theme
            with dpg.theme_component(dpg.mvText, enabled_state=True, parent=self.theme_id, tag="warning_theme"):
                dpg.add_theme_color(dpg.mvThemeCol_Text, Colors.WARNING, category=dpg.mvThemeCat_Core)
            
            # Error theme
            with dpg.theme_component(dpg.mvText, enabled_state=True, parent=self.theme_id, tag="error_theme"):
                dpg.add_theme_color(dpg.mvThemeCol_Text, Colors.ERROR, category=dpg.mvThemeCat_Core)
            
            # Success theme
            with dpg.theme_component(dpg.mvText, enabled_state=True, parent=self.theme_id, tag="success_theme"):
                dpg.add_theme_color(dpg.mvThemeCol_Text, Colors.SUCCESS, category=dpg.mvThemeCat_Core)
                
        # Set the theme as active
        self.active_theme_id = self.theme_id
        dpg.bind_theme(self.theme_id)
        
        # Set default font
        dpg.bind_font(self.font_regular)
    
    def apply_component_theme(self, item_id: int, theme_type: str) -> None:
        """
        Apply a specific component theme to an item.
        
        Args:
            item_id: ID of the item to theme
            theme_type: Type of theme to apply (e.g., "accent_button", "slider_theme")
        """
        if not dpg.does_item_exist(item_id):
            return
            
        # Look up component theme
        component_theme_id = dpg.get_item_alias(theme_type) if dpg.does_alias_exist(theme_type) else None
        
        if component_theme_id and dpg.does_item_exist(component_theme_id):
            dpg.bind_item_theme(item_id, component_theme_id)
    
    def create_theme_toggle(self, parent_id: int) -> int:
        """
        Create a theme toggle button (dark/light mode).
        
        Args:
            parent_id: ID of the parent container
            
        Returns:
            ID of the created toggle button
        """
        # Create toggle button (currently a placeholder since we're only implementing dark theme)
        self.toggle_button_id = dpg.add_button(
            label="Theme: Dark" if self.dark_mode else "Theme: Light",
            callback=self._toggle_theme,
            parent=parent_id
        )
        
        return self.toggle_button_id
    
    def _toggle_theme(self, sender, app_data) -> None:
        """Toggle between dark and light themes."""
        # Currently a placeholder - only dark theme is implemented
        # In the future, this would toggle between dark and light themes
        self.dark_mode = not self.dark_mode
        dpg.set_item_label(sender, "Theme: Dark" if self.dark_mode else "Theme: Light")
    
    def create_glass_panel(self, parent_id: int, label: str = "", **kwargs) -> int:
        """
        Create a glass-morphism effect panel.
        
        Args:
            parent_id: ID of the parent container
            label: Optional label for the panel
            **kwargs: Additional arguments to pass to add_child_window
            
        Returns:
            ID of the created panel
        """
        # Create a glass-morphism panel using a child window
        panel_id = dpg.add_child_window(parent=parent_id, label=label, **kwargs)
        
        # Apply glass panel theme
        with dpg.theme() as glass_theme:
            with dpg.theme_component(dpg.mvChildWindow):
                # Semi-transparent background
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (38, 38, 38, 180), category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, Spacing.RADIUS_LG, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, [Spacing.MD, Spacing.MD], category=dpg.mvThemeCat_Core)
                # Note: Dear PyGui doesn't support backdrop-filter directly,
                # so we approximate glass morphism with semi-transparency
        
        dpg.bind_item_theme(panel_id, glass_theme)
        return panel_id
    
    def create_glow_effect(self, item_id: int, color: Tuple[int, int, int, int] = Colors.TEAL_GLOW) -> None:
        """
        Apply a glow effect to an item.
        
        Args:
            item_id: ID of the item to apply glow effect to
            color: Color of the glow (RGBA)
        """
        # Note: DearPyGui doesn't directly support outer glow effects
        # This is a placeholder that would be implemented in a custom renderer
        # or with an advanced drawing approach
        pass
    
    def create_premium_button(self, parent_id: int, label: str, callback: callable, 
                             is_accent: bool = True, **kwargs) -> int:
        """
        Create a premium styled button.
        
        Args:
            parent_id: ID of the parent container
            label: Button label
            callback: Function to call when button is clicked
            is_accent: Whether to use accent styling (True) or secondary styling (False)
            **kwargs: Additional arguments to pass to add_button
            
        Returns:
            ID of the created button
        """
        # Create button
        button_id = dpg.add_button(parent=parent_id, label=label, callback=callback, **kwargs)
        
        # Apply appropriate theme
        theme_type = "accent_button" if is_accent else "secondary_button"
        self.apply_component_theme(button_id, theme_type)
        
        return button_id
    
    def create_premium_slider(self, parent_id: int, label: str, default_value: float, 
                             min_value: float, max_value: float, format: str = "%.3f",
                             callback: callable = None, **kwargs) -> int:
        """
        Create a premium styled slider.
        
        Args:
            parent_id: ID of the parent container
            label: Slider label
            default_value: Initial value
            min_value: Minimum value
            max_value: Maximum value
            format: Display format string
            callback: Function to call when slider value changes
            **kwargs: Additional arguments to pass to add_slider_float
            
        Returns:
            ID of the created slider
        """
        # Create slider
        slider_id = dpg.add_slider_float(
            parent=parent_id,
            label=label,
            default_value=default_value,
            min_value=min_value,
            max_value=max_value,
            format=format,
            callback=callback,
            **kwargs
        )
        
        # Apply slider theme
        self.apply_component_theme(slider_id, "slider_float_theme")
        
        return slider_id
    
    def create_premium_slider_int(self, parent_id: int, label: str, default_value: int, 
                                min_value: int, max_value: int, 
                                callback: callable = None, **kwargs) -> int:
        """
        Create a premium styled integer slider.
        
        Args:
            parent_id: ID of the parent container
            label: Slider label
            default_value: Initial value
            min_value: Minimum value
            max_value: Maximum value
            callback: Function to call when slider value changes
            **kwargs: Additional arguments to pass to add_slider_int
            
        Returns:
            ID of the created slider
        """
        # Create slider
        slider_id = dpg.add_slider_int(
            parent=parent_id,
            label=label,
            default_value=default_value,
            min_value=min_value,
            max_value=max_value,
            callback=callback,
            **kwargs
        )
        
        # Apply slider theme
        self.apply_component_theme(slider_id, "slider_theme")
        
        return slider_id
    
    def export_theme_tokens(self, file_path: str) -> bool:
        """
        Export theme tokens to a JSON file.
        
        Args:
            file_path: Path to save the JSON file
            
        Returns:
            True if export was successful, False otherwise
        """
        try:
            from .tokens import get_theme_tokens
            
            # Get theme tokens
            tokens = get_theme_tokens()
            
            # Convert RGBA tuples to hex strings for JSON serialization
            serializable_tokens = {}
            for category, values in tokens.items():
                serializable_tokens[category] = {}
                for key, value in values.items():
                    if isinstance(value, tuple) and len(value) == 4:
                        # Convert RGBA tuple to hex string
                        serializable_tokens[category][key] = Colors.to_hex(value)
                    else:
                        serializable_tokens[category][key] = value
            
            # Write to file
            with open(file_path, 'w') as f:
                json.dump(serializable_tokens, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Error exporting theme tokens: {e}")
            return False