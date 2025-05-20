"""
Premium slider components for RFM Architecture UI.

This module provides enhanced slider components with premium styling and effects.
"""

import dearpygui.dearpygui as dpg
from typing import Optional, Callable, Any, List, Dict, Tuple
import time

from rfm_ui.theme import Colors, Spacing, Motion, get_theme


class PremiumSlider:
    """
    Premium styled slider with glow effects and animations.
    
    Features:
    - Smooth animations
    - Glow effect on active state
    - Custom styling with premium theming
    - Optional value formatting
    - Debounced callbacks for performance
    """
    
    def __init__(self, 
                parent_id: int,
                label: str,
                default_value: float,
                min_value: float,
                max_value: float,
                callback: Optional[Callable] = None,
                format: str = "%.3f",
                width: int = -1,
                height: int = -1,
                tag: Optional[str] = None,
                debounce_ms: int = 150,
                **kwargs):
        """
        Initialize the premium slider.
        
        Args:
            parent_id: DearPyGui ID of the parent container
            label: Slider label
            default_value: Initial value
            min_value: Minimum value
            max_value: Maximum value
            callback: Function to call when slider value changes
            format: Format string for displaying the value
            width: Width of the slider (-1 for auto)
            height: Height of the slider (-1 for auto)
            tag: Optional tag for the slider
            debounce_ms: Milliseconds to debounce callbacks (for performance)
            **kwargs: Additional arguments to pass to add_slider_float
        """
        self.parent_id = parent_id
        self.label = label
        self.default_value = default_value
        self.min_value = min_value
        self.max_value = max_value
        self.callback = callback
        self.format = format
        self.width = width
        self.height = height
        self.tag = tag
        self.debounce_ms = debounce_ms
        self.kwargs = kwargs
        
        self._last_callback_time = 0
        self._active = False
        self._slider_id = None
        self._last_value = default_value
        self._builtin_callback = self._on_slider_change
        
        # For animation
        self._glow_id = None
        self._value_text_id = None
        
        # Create the slider
        self._create()
        
    def _create(self) -> None:
        """Create the slider component."""
        # Create a group for the slider and value text
        with dpg.group(horizontal=True, parent=self.parent_id):
            # Create the slider
            self._slider_id = dpg.add_slider_float(
                label=self.label,
                default_value=self.default_value,
                min_value=self.min_value,
                max_value=self.max_value,
                format=self.format,
                width=self.width if self.width != -1 else -1,
                height=self.height,
                callback=self._builtin_callback,
                tag=self.tag,
                **self.kwargs
            )
            
            # Add value text for more prominent display
            value_str = self.format % self.default_value
            self._value_text_id = dpg.add_text(
                value_str,
                color=Colors.TEXT_SECONDARY
            )
            
        # Apply theme to the slider
        theme = get_theme()
        theme.apply_component_theme(self._slider_id, "slider_float_theme")
        
        # Register handler for hover effect
        with dpg.item_handler_registry() as handler:
            dpg.add_item_hover_handler(callback=self._on_hover_start)
            dpg.add_item_unhover_handler(callback=self._on_hover_end)
            
        dpg.bind_item_handler_registry(self._slider_id, handler)
    
    def _on_slider_change(self, sender, app_data, user_data=None) -> None:
        """
        Handle slider value change with debouncing.
        
        Args:
            sender: ID of the sender item
            app_data: New slider value
            user_data: User data (unused)
        """
        current_time = time.time() * 1000  # ms
        
        # Update value text immediately
        value_str = self.format % app_data
        if self._value_text_id:
            dpg.set_value(self._value_text_id, value_str)
            dpg.configure_item(
                self._value_text_id, 
                color=Colors.TEAL_ACCENT if self._active else Colors.TEXT_SECONDARY
            )
            
        # Store last value
        self._last_value = app_data
        
        # Apply glow effect when value changes
        self._apply_glow()
            
        # Check if we should call the callback (debounce)
        if (current_time - self._last_callback_time) >= self.debounce_ms:
            self._last_callback_time = current_time
            if self.callback:
                self.callback(sender, app_data, user_data)
    
    def _apply_glow(self) -> None:
        """Apply a glow effect to the slider."""
        # DearPyGui doesn't directly support outer glow effects
        # Instead, we'll change the slider grab color to create a visual effect
        
        # Create the glow theme if it doesn't exist
        if not self._glow_id:
            with dpg.theme() as self._glow_id:
                with dpg.theme_component(dpg.mvSliderFloat):
                    dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, Colors.TEAL_LIGHT, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, Colors.TEAL_LIGHT, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, Spacing.RADIUS_PILL, category=dpg.mvThemeCat_Core)
                    
        # Apply glow theme temporarily
        dpg.bind_item_theme(self._slider_id, self._glow_id)
        
        # Reset theme after a short delay (animation effect)
        def _reset_theme():
            if dpg.does_item_exist(self._slider_id):
                theme = get_theme()
                theme.apply_component_theme(self._slider_id, "slider_float_theme")
                
        dpg.set_frame_callback(Motion.DURATION_BASE // 16, _reset_theme)  # Convert ms to frames (approx)
    
    def _on_hover_start(self) -> None:
        """Handle hover start."""
        self._active = True
        if self._value_text_id and dpg.does_item_exist(self._value_text_id):
            dpg.configure_item(self._value_text_id, color=Colors.TEAL_ACCENT)
    
    def _on_hover_end(self) -> None:
        """Handle hover end."""
        self._active = False
        if self._value_text_id and dpg.does_item_exist(self._value_text_id):
            dpg.configure_item(self._value_text_id, color=Colors.TEXT_SECONDARY)
    
    def get_value(self) -> float:
        """
        Get the current slider value.
        
        Returns:
            Current value of the slider
        """
        if self._slider_id and dpg.does_item_exist(self._slider_id):
            return dpg.get_value(self._slider_id)
        return self._last_value
    
    def set_value(self, value: float) -> None:
        """
        Set the slider value.
        
        Args:
            value: New value for the slider
        """
        if self._slider_id and dpg.does_item_exist(self._slider_id):
            dpg.set_value(self._slider_id, value)
            value_str = self.format % value
            if self._value_text_id and dpg.does_item_exist(self._value_text_id):
                dpg.set_value(self._value_text_id, value_str)
            self._last_value = value


class PremiumSliderInt(PremiumSlider):
    """
    Premium styled integer slider with glow effects and animations.
    """
    
    def __init__(self, 
                parent_id: int,
                label: str,
                default_value: int,
                min_value: int,
                max_value: int,
                callback: Optional[Callable] = None,
                width: int = -1,
                height: int = -1,
                tag: Optional[str] = None,
                debounce_ms: int = 150,
                **kwargs):
        """
        Initialize the premium integer slider.
        
        Args:
            parent_id: DearPyGui ID of the parent container
            label: Slider label
            default_value: Initial value
            min_value: Minimum value
            max_value: Maximum value
            callback: Function to call when slider value changes
            width: Width of the slider (-1 for auto)
            height: Height of the slider (-1 for auto)
            tag: Optional tag for the slider
            debounce_ms: Milliseconds to debounce callbacks (for performance)
            **kwargs: Additional arguments to pass to add_slider_int
        """
        # Integer format
        format = "%d"
        super().__init__(
            parent_id=parent_id,
            label=label,
            default_value=default_value,
            min_value=min_value,
            max_value=max_value,
            callback=callback,
            format=format,
            width=width,
            height=height,
            tag=tag,
            debounce_ms=debounce_ms,
            **kwargs
        )
    
    def _create(self) -> None:
        """Create the integer slider component."""
        # Create a group for the slider and value text
        with dpg.group(horizontal=True, parent=self.parent_id):
            # Create the slider
            self._slider_id = dpg.add_slider_int(
                label=self.label,
                default_value=int(self.default_value),
                min_value=int(self.min_value),
                max_value=int(self.max_value),
                width=self.width if self.width != -1 else -1,
                height=self.height,
                callback=self._builtin_callback,
                tag=self.tag,
                **self.kwargs
            )
            
            # Add value text for more prominent display
            value_str = self.format % self.default_value
            self._value_text_id = dpg.add_text(
                value_str,
                color=Colors.TEXT_SECONDARY
            )
            
        # Apply theme to the slider
        theme = get_theme()
        theme.apply_component_theme(self._slider_id, "slider_theme")
        
        # Register handler for hover effect
        with dpg.item_handler_registry() as handler:
            dpg.add_item_hover_handler(callback=self._on_hover_start)
            dpg.add_item_unhover_handler(callback=self._on_hover_end)
            
        dpg.bind_item_handler_registry(self._slider_id, handler)
    
    def _apply_glow(self) -> None:
        """Apply a glow effect to the integer slider."""
        # Create the glow theme if it doesn't exist
        if not self._glow_id:
            with dpg.theme() as self._glow_id:
                with dpg.theme_component(dpg.mvSliderInt):
                    dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, Colors.TEAL_LIGHT, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, Colors.TEAL_LIGHT, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, Spacing.RADIUS_PILL, category=dpg.mvThemeCat_Core)
                    
        # Apply glow theme temporarily
        dpg.bind_item_theme(self._slider_id, self._glow_id)
        
        # Reset theme after a short delay (animation effect)
        def _reset_theme():
            if dpg.does_item_exist(self._slider_id):
                theme = get_theme()
                theme.apply_component_theme(self._slider_id, "slider_theme")
                
        dpg.set_frame_callback(Motion.DURATION_BASE // 16, _reset_theme)  # Convert ms to frames (approx)
    
    def get_value(self) -> int:
        """
        Get the current slider value.
        
        Returns:
            Current value of the slider as an integer
        """
        if self._slider_id and dpg.does_item_exist(self._slider_id):
            return int(dpg.get_value(self._slider_id))
        return int(self._last_value)
    
    def set_value(self, value: int) -> None:
        """
        Set the slider value.
        
        Args:
            value: New value for the slider (will be cast to integer)
        """
        if self._slider_id and dpg.does_item_exist(self._slider_id):
            value = int(value)
            dpg.set_value(self._slider_id, value)
            value_str = self.format % value
            if self._value_text_id and dpg.does_item_exist(self._value_text_id):
                dpg.set_value(self._value_text_id, value_str)
            self._last_value = value