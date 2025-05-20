"""
Premium theme for the System Configuration UI.

This module provides a premium visual theme for the System Configuration UI
with consistent styling, animations, and visual effects.
"""
from typing import Tuple, Dict, Any, List, Optional
import dearpygui.dearpygui as dpg

from .constants import THEME, STYLE, ANIMATIONS, SPACING, FONT_SIZES


class PremiumTheme:
    """
    Premium theme manager for the System Configuration UI.
    
    This class creates and manages a premium visual theme with
    consistent styling, animations, and visual effects.
    """
    
    def __init__(self):
        """Initialize the premium theme."""
        self.theme_id = None
        self.dark_theme_id = None
        self.button_theme_id = None
        self.input_theme_id = None
        self.active_item_theme_id = None
        self.error_theme_id = None
        self.fonts = {}
        
    def setup(self) -> None:
        """Set up the premium theme."""
        self._setup_fonts()
        self._create_themes()
        
    def _setup_fonts(self) -> None:
        """Set up fonts for the premium theme."""
        with dpg.font_registry():
            # Regular fonts
            self.fonts["regular"] = dpg.add_font("fonts/Roboto-Regular.ttf", FONT_SIZES["body"])
            self.fonts["small"] = dpg.add_font("fonts/Roboto-Regular.ttf", FONT_SIZES["small"])
            
            # Bold fonts
            self.fonts["bold"] = dpg.add_font("fonts/Roboto-Bold.ttf", FONT_SIZES["body"])
            self.fonts["title"] = dpg.add_font("fonts/Roboto-Bold.ttf", FONT_SIZES["title"])
            self.fonts["header"] = dpg.add_font("fonts/Roboto-Bold.ttf", FONT_SIZES["header"])
            
            # Monospace font
            self.fonts["mono"] = dpg.add_font("fonts/RobotoMono-Regular.ttf", FONT_SIZES["body"])
            
        # Set default font
        if self.fonts.get("regular"):
            dpg.bind_font(self.fonts["regular"])
            
    def _create_themes(self) -> None:
        """Create themes for different UI components."""
        # Main theme
        with dpg.theme() as self.theme_id:
            with dpg.theme_component(dpg.mvAll):
                # Colors
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, THEME["background"])
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, THEME["card"])
                dpg.add_theme_color(dpg.mvThemeCol_TitleBg, THEME["primary"])
                dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, THEME["primary"])
                dpg.add_theme_color(dpg.mvThemeCol_TitleBgCollapsed, THEME["primary"])
                dpg.add_theme_color(dpg.mvThemeCol_Text, THEME["text"])
                dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, THEME["text_secondary"])
                dpg.add_theme_color(dpg.mvThemeCol_Border, THEME["border"])
                dpg.add_theme_color(dpg.mvThemeCol_NavHighlight, THEME["primary"])
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, [40, 40, 45])
                dpg.add_theme_color(dpg.mvThemeCol_Button, THEME["primary"])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [
                    min(THEME["primary"][0] + 20, 255),
                    min(THEME["primary"][1] + 20, 255),
                    min(THEME["primary"][2] + 20, 255)
                ])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [
                    min(THEME["primary"][0] + 40, 255),
                    min(THEME["primary"][1] + 40, 255),
                    min(THEME["primary"][2] + 40, 255)
                ])
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, [30, 30, 35])
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, THEME["border"])
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, [80, 80, 90])
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabActive, THEME["primary"])
                dpg.add_theme_color(dpg.mvThemeCol_Header, THEME["primary"])
                dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered", [
                    min(THEME["primary"][0] + 20, 255),
                    min(THEME["primary"][1] + 20, 255),
                    min(THEME["primary"][2] + 20, 255)
                ])
                dpg.add_theme_color(dpg.mvThemeCol_Tab, THEME["primary"])
                dpg.add_theme_color(dpg.mvThemeCol_TabHovered, [
                    min(THEME["primary"][0] + 20, 255),
                    min(THEME["primary"][1] + 20, 255),
                    min(THEME["primary"][2] + 20, 255)
                ])
                dpg.add_theme_color(dpg.mvThemeCol_TabActive, [
                    min(THEME["primary"][0] + 40, 255),
                    min(THEME["primary"][1] + 40, 255),
                    min(THEME["primary"][2] + 40, 255)
                ])
                
                # Styles
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, STYLE["corner_radius"])
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, STYLE["corner_radius"])
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, STYLE["corner_radius"])
                dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, STYLE["corner_radius"])
                dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, STYLE["corner_radius"])
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, STYLE["button_padding"])
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, [SPACING["md"], SPACING["md"]])
                dpg.add_theme_style(dpg.mvStyleVar_ItemInnerSpacing, [SPACING["sm"], SPACING["sm"]])
                dpg.add_theme_style(dpg.mvStyleVar_IndentSpacing, SPACING["lg"])
                dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize, 12)
                dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, STYLE["border_width"])
                dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize, STYLE["border_width"])
                dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, STYLE["border_width"])
                dpg.add_theme_style(dpg.mvStyleVar_PopupBorderSize, STYLE["border_width"])
                
        # Dark theme (for modals and dialogs)
        with dpg.theme() as self.dark_theme_id:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, [15, 15, 18])
                dpg.add_theme_color(dpg.mvThemeCol_TitleBg, [30, 30, 35])
                dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, [40, 40, 45])
                dpg.add_theme_color(dpg.mvThemeCol_Border, [60, 60, 70])
                dpg.add_theme_color(dpg.mvThemeCol_Button, [50, 50, 60])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [70, 70, 80])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [90, 90, 100])
        
        # Button theme
        with dpg.theme() as self.button_theme_id:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, THEME["primary"])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [
                    min(THEME["primary"][0] + 20, 255),
                    min(THEME["primary"][1] + 20, 255),
                    min(THEME["primary"][2] + 20, 255)
                ])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [
                    min(THEME["primary"][0] + 40, 255),
                    min(THEME["primary"][1] + 40, 255),
                    min(THEME["primary"][2] + 40, 255)
                ])
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, STYLE["corner_radius"])
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, STYLE["button_padding"])
        
        # Input theme
        with dpg.theme() as self.input_theme_id:
            with dpg.theme_component(dpg.mvInputText):
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, [45, 45, 50])
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, STYLE["corner_radius"])
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, STYLE["input_padding"])
        
        # Active item theme
        with dpg.theme() as self.active_item_theme_id:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_Button, THEME["secondary"])
                dpg.add_theme_color(dpg.mvThemeCol_Text, [255, 255, 255])
                dpg.add_theme_color(dpg.mvThemeCol_Border, THEME["secondary"])
        
        # Error theme
        with dpg.theme() as self.error_theme_id:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, [THEME["error"][0] // 2, THEME["error"][1] // 2, THEME["error"][2] // 2])
                dpg.add_theme_color(dpg.mvThemeCol_Border, THEME["error"])
                dpg.add_theme_color(dpg.mvThemeCol_Text, THEME["error"])
    
    def apply_to_item(self, tag: int) -> None:
        """
        Apply the premium theme to an item.
        
        Args:
            tag: Item tag
        """
        if self.theme_id:
            dpg.bind_item_theme(tag, self.theme_id)
    
    def apply_dark_theme(self, tag: int) -> None:
        """
        Apply the dark theme to an item.
        
        Args:
            tag: Item tag
        """
        if self.dark_theme_id:
            dpg.bind_item_theme(tag, self.dark_theme_id)
    
    def apply_button_theme(self, tag: int) -> None:
        """
        Apply the button theme to an item.
        
        Args:
            tag: Item tag
        """
        if self.button_theme_id:
            dpg.bind_item_theme(tag, self.button_theme_id)
    
    def apply_input_theme(self, tag: int) -> None:
        """
        Apply the input theme to an item.
        
        Args:
            tag: Item tag
        """
        if self.input_theme_id:
            dpg.bind_item_theme(tag, self.input_theme_id)
    
    def apply_active_theme(self, tag: int) -> None:
        """
        Apply the active item theme to an item.
        
        Args:
            tag: Item tag
        """
        if self.active_item_theme_id:
            dpg.bind_item_theme(tag, self.active_item_theme_id)
    
    def apply_error_theme(self, tag: int) -> None:
        """
        Apply the error theme to an item.
        
        Args:
            tag: Item tag
        """
        if self.error_theme_id:
            dpg.bind_item_theme(tag, self.error_theme_id)
    
    def get_font(self, font_name: str) -> Optional[int]:
        """
        Get a font by name.
        
        Args:
            font_name: Font name
            
        Returns:
            Font tag or None if not found
        """
        return self.fonts.get(font_name)


# Singleton instance
_theme_instance = None


def get_theme() -> PremiumTheme:
    """
    Get the premium theme instance.
    
    Returns:
        PremiumTheme instance
    """
    global _theme_instance
    if _theme_instance is None:
        _theme_instance = PremiumTheme()
    return _theme_instance