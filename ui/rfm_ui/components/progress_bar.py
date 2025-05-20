"""
Progress bar component for RFM Architecture UI.

This module provides a premium progress bar component with advanced styling
and animation for tracking long-running operations.
"""

import dearpygui.dearpygui as dpg
import time
import threading
import asyncio
from typing import Optional, Dict, Any, Callable, Tuple, List, Union

from rfm_ui.theme import Colors, Spacing, Motion, get_theme


class ProgressBar:
    """
    Premium styled progress bar with animation and color transitions.
    
    Features:
    - Smooth progress animation
    - Color changes based on progress
    - Optional status text and percentage display
    - Cancellation button
    - Compact, stylish design
    """
    
    def __init__(self, 
                parent_id: int,
                width: int = 400,
                height: int = 40,
                pos: Optional[Tuple[int, int]] = None,
                label: Optional[str] = None,
                show_percentage: bool = True,
                show_cancel: bool = True,
                on_cancel: Optional[Callable] = None,
                animation_speed: float = 1.0,
                tag: Optional[str] = None):
        """
        Initialize the progress bar component.
        
        Args:
            parent_id: DearPyGui ID of the parent container
            width: Width of the progress bar
            height: Height of the progress bar
            pos: Optional position (x, y)
            label: Optional label text
            show_percentage: Whether to show percentage text
            show_cancel: Whether to show cancel button
            on_cancel: Callback function when cancel button is clicked
            animation_speed: Speed of progress animation (1.0 = normal)
            tag: Optional tag for the progress bar component
        """
        self.parent_id = parent_id
        self.width = width
        self.height = height
        self.pos = pos
        self.label = label
        self.show_percentage = show_percentage
        self.show_cancel = show_cancel
        self.on_cancel = on_cancel
        self.animation_speed = animation_speed
        self.tag = tag or f"progress_bar_{int(time.time())}"
        
        # Progress state
        self._target_progress = 0.0  # Target progress (0.0 to 1.0)
        self._current_progress = 0.0  # Current displayed progress (animated)
        self._status_text = ""
        self._is_indeterminate = False
        self._is_error = False
        self._is_complete = False
        self._is_paused = False
        self._is_canceled = False
        
        # UI components
        self._window_id = None
        self._bar_bg_id = None
        self._bar_fg_id = None
        self._label_id = None
        self._percentage_id = None
        self._status_id = None
        self._cancel_btn_id = None
        self._group_id = None
        
        # Themes
        self._normal_theme = None
        self._warning_theme = None
        self._error_theme = None
        self._complete_theme = None
        self._paused_theme = None
        self._indeterminate_theme = None
        self._current_theme = None
        
        # Animation state
        self._last_update_time = 0
        self._indeterminate_offset = 0.0
        self._indeterminate_anim_speed = 1.0
        
        # Create the component
        self._create()
        
        # Start animation
        self._update_animation()
    
    def _create(self) -> None:
        """Create the progress bar component."""
        # Create themes for different states
        self._create_themes()
        
        # Create main container
        with dpg.group(parent=self.parent_id, horizontal=False, tag=self.tag) as self._group_id:
            # Top row with label and percentage
            if self.label or self.show_percentage:
                with dpg.group(horizontal=True, width=self.width):
                    # Label
                    if self.label:
                        self._label_id = dpg.add_text(
                            self.label,
                            color=Colors.TEXT_PRIMARY
                        )
                        
                    # Add spacer
                    dpg.add_spacer(width=10)
                    
                    # Right-aligned percentage
                    if self.show_percentage:
                        dpg.add_spacer(width=-1)  # Expands to fill space
                        self._percentage_id = dpg.add_text(
                            "0%",
                            color=Colors.TEXT_SECONDARY
                        )
            
            # Progress bar (background + foreground)
            with dpg.drawlist(width=self.width, height=self.height) as self._bar_bg_id:
                # Background
                dpg.draw_rectangle(
                    (0, 0),
                    (self.width, self.height),
                    color=(30, 30, 30, 255),
                    fill=(30, 30, 30, 255),
                    rounding=Spacing.RADIUS_SM
                )
                
                # Foreground
                self._bar_fg_id = dpg.draw_rectangle(
                    (0, 0),
                    (0, self.height),  # Will be updated in animation
                    color=Colors.TEAL_ACCENT,
                    fill=Colors.TEAL_ACCENT,
                    rounding=Spacing.RADIUS_SM
                )
            
            # Status text
            self._status_id = dpg.add_text(
                "",
                color=Colors.TEXT_SECONDARY,
                wrap=self.width
            )
            
            # Cancel button
            if self.show_cancel:
                self._cancel_btn_id = dpg.add_button(
                    label="Cancel",
                    callback=self._on_cancel_click,
                    width=80
                )
        
        # Apply initial theme
        dpg.bind_item_theme(self._bar_fg_id, self._normal_theme)
        self._current_theme = self._normal_theme
    
    def _create_themes(self) -> None:
        """Create themes for different progress bar states."""
        # Normal state theme
        with dpg.theme() as self._normal_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_Button, Colors.TEAL_ACCENT, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, Colors.TEAL_ACCENT_LIGHT, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, Colors.TEAL_ACCENT_DARK, category=dpg.mvThemeCat_Core)
        
        # Warning state theme (slower progress)
        with dpg.theme() as self._warning_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_Button, Colors.AMBER_ACCENT, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, Colors.AMBER_ACCENT_LIGHT, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, Colors.AMBER_ACCENT_DARK, category=dpg.mvThemeCat_Core)
        
        # Error state theme
        with dpg.theme() as self._error_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_Button, Colors.ERROR, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, Colors.ERROR_LIGHT, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, Colors.ERROR_DARK, category=dpg.mvThemeCat_Core)
        
        # Complete state theme
        with dpg.theme() as self._complete_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_Button, Colors.SUCCESS, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, Colors.SUCCESS_LIGHT, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, Colors.SUCCESS_DARK, category=dpg.mvThemeCat_Core)
        
        # Paused state theme
        with dpg.theme() as self._paused_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_Button, Colors.VIOLET_ACCENT, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, Colors.VIOLET_ACCENT_LIGHT, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, Colors.VIOLET_ACCENT_DARK, category=dpg.mvThemeCat_Core)
        
        # Indeterminate state theme
        with dpg.theme() as self._indeterminate_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_Button, Colors.BLUE_ACCENT, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, Colors.BLUE_ACCENT_LIGHT, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, Colors.BLUE_ACCENT_DARK, category=dpg.mvThemeCat_Core)
    
    def _update_animation(self) -> None:
        """Update the progress bar animation."""
        # Check if component still exists
        if not dpg.does_item_exist(self._group_id):
            return
            
        # Get current time
        current_time = time.time()
        delta_time = current_time - self._last_update_time
        self._last_update_time = current_time
        
        # Calculate animation step
        animation_step = delta_time * 3.0 * self.animation_speed  # Speed factor
        
        if self._is_indeterminate:
            # Update indeterminate animation
            self._indeterminate_offset += delta_time * self._indeterminate_anim_speed
            self._indeterminate_offset %= 1.0
            
            # Draw indeterminate pattern
            if dpg.does_item_exist(self._bar_fg_id):
                dpg.delete_item(self._bar_fg_id)
                
                # Create new foreground with gradient pattern
                self._bar_fg_id = dpg.draw_rectangle(
                    (0, 0),
                    (self.width, self.height),
                    parent=self._bar_bg_id,
                    color=Colors.BLUE_ACCENT,
                    fill=Colors.BLUE_ACCENT,
                    rounding=Spacing.RADIUS_SM
                )
                
                # Apply pattern (diagonal stripes)
                stripe_width = self.width * 0.2
                for i in range(10):
                    offset = (i * stripe_width * 2 + self._indeterminate_offset * self.width * 2) % (self.width * 2) - stripe_width
                    dpg.draw_quad(
                        (offset, 0),
                        (offset + stripe_width, 0),
                        (offset + stripe_width - self.height, self.height),
                        (offset - self.height, self.height),
                        parent=self._bar_bg_id,
                        color=(50, 50, 50, 100),
                        fill=(50, 50, 50, 100)
                    )
        else:
            # Animate towards target progress
            if self._current_progress < self._target_progress:
                self._current_progress = min(self._target_progress, self._current_progress + animation_step)
            elif self._current_progress > self._target_progress:
                self._current_progress = max(self._target_progress, self._current_progress - animation_step)
            
            # Update progress bar width
            if dpg.does_item_exist(self._bar_fg_id):
                width = int(self.width * self._current_progress)
                dpg.configure_item(
                    self._bar_fg_id,
                    p2=(width, self.height)
                )
            
            # Update percentage text
            if self.show_percentage and dpg.does_item_exist(self._percentage_id):
                dpg.set_value(self._percentage_id, f"{int(self._current_progress * 100)}%")
            
            # Update theme based on progress and state
            new_theme = self._determine_theme()
            if new_theme != self._current_theme:
                self._current_theme = new_theme
                if dpg.does_item_exist(self._bar_fg_id):
                    dpg.bind_item_theme(self._bar_fg_id, new_theme)
        
        # Continue animation
        dpg.set_frame_callback(1, lambda: self._update_animation())
    
    def _determine_theme(self) -> int:
        """
        Determine the appropriate theme based on progress and state.
        
        Returns:
            Theme ID to use
        """
        if self._is_error:
            return self._error_theme
        elif self._is_complete:
            return self._complete_theme
        elif self._is_paused:
            return self._paused_theme
        elif self._is_indeterminate:
            return self._indeterminate_theme
        elif self._target_progress < 0.3 and self._target_progress > 0:
            return self._warning_theme
        else:
            return self._normal_theme
    
    def _on_cancel_click(self) -> None:
        """Handle cancel button click."""
        if self.on_cancel:
            self.on_cancel()
            
        # Mark as canceled
        self._is_canceled = True
        self.set_status("Operation canceled")
        
        # Disable cancel button
        if dpg.does_item_exist(self._cancel_btn_id):
            dpg.configure_item(self._cancel_btn_id, enabled=False)
    
    def set_progress(self, progress: float) -> None:
        """
        Set the progress value.
        
        Args:
            progress: Progress value (0.0 to 1.0)
        """
        self._target_progress = max(0.0, min(1.0, progress))
        self._is_indeterminate = False
        
        # Auto-complete if reached 100%
        if self._target_progress >= 1.0 and not self._is_complete and not self._is_error:
            self._is_complete = True
            self.set_status("Operation completed")
    
    def set_indeterminate(self, enabled: bool = True) -> None:
        """
        Set the progress bar to indeterminate mode.
        
        Args:
            enabled: Whether indeterminate mode is enabled
        """
        self._is_indeterminate = enabled
    
    def set_status(self, text: str) -> None:
        """
        Set the status text.
        
        Args:
            text: Status text to display
        """
        self._status_text = text
        if dpg.does_item_exist(self._status_id):
            dpg.set_value(self._status_id, text)
    
    def set_error(self, error_text: Optional[str] = None) -> None:
        """
        Set the progress bar to error state.
        
        Args:
            error_text: Optional error text to display
        """
        self._is_error = True
        if error_text:
            self.set_status(f"Error: {error_text}")
    
    def set_paused(self, paused: bool = True) -> None:
        """
        Set the progress bar to paused state.
        
        Args:
            paused: Whether the progress bar is paused
        """
        self._is_paused = paused
        if paused:
            self.set_status("Operation paused")
    
    def is_canceled(self) -> bool:
        """
        Check if the operation has been canceled.
        
        Returns:
            True if canceled, False otherwise
        """
        return self._is_canceled
    
    def enable_cancel(self, enabled: bool = True) -> None:
        """
        Enable or disable the cancel button.
        
        Args:
            enabled: Whether the cancel button is enabled
        """
        if self.show_cancel and dpg.does_item_exist(self._cancel_btn_id):
            dpg.configure_item(self._cancel_btn_id, enabled=enabled)
    
    def show(self) -> None:
        """Show the progress bar."""
        if dpg.does_item_exist(self._group_id):
            dpg.configure_item(self._group_id, show=True)
    
    def hide(self) -> None:
        """Hide the progress bar."""
        if dpg.does_item_exist(self._group_id):
            dpg.configure_item(self._group_id, show=False)
            
    def reset(self) -> None:
        """Reset the progress bar to initial state."""
        self._target_progress = 0.0
        self._current_progress = 0.0
        self._is_indeterminate = False
        self._is_error = False
        self._is_complete = False
        self._is_paused = False
        self._is_canceled = False
        
        if dpg.does_item_exist(self._percentage_id):
            dpg.set_value(self._percentage_id, "0%")
            
        if dpg.does_item_exist(self._status_id):
            dpg.set_value(self._status_id, "")
            
        if self.show_cancel and dpg.does_item_exist(self._cancel_btn_id):
            dpg.configure_item(self._cancel_btn_id, enabled=True)


class ProgressManager:
    """
    Manages progress tracking for multiple operations.
    
    This class provides UI components for tracking and displaying progress
    of multiple concurrent operations.
    """
    
    def __init__(self, parent_id: int):
        """
        Initialize the progress manager.
        
        Args:
            parent_id: DearPyGui ID of the parent container
        """
        self.parent_id = parent_id
        self.progress_bars: Dict[str, ProgressBar] = {}
        self.collapsing_header_id = None
        self.container_id = None
        
        # Create UI container
        self._create_ui()
        
        # Hide initially (until there are operations)
        self.hide()
    
    def _create_ui(self) -> None:
        """Create the progress manager UI components."""
        with dpg.collapsing_header(
            label="Operations in Progress",
            parent=self.parent_id,
            default_open=True,
            tag=f"progress_manager_header_{int(time.time())}"
        ) as self.collapsing_header_id:
            # Container for progress bars
            self.container_id = dpg.add_group(horizontal=False)
    
    def add_operation(self, 
                    operation_id: str,
                    operation_name: str,
                    show_cancel: bool = True,
                    on_cancel: Optional[Callable] = None) -> ProgressBar:
        """
        Add an operation to track.
        
        Args:
            operation_id: Unique ID for the operation
            operation_name: Name/title of the operation
            show_cancel: Whether to show cancel button
            on_cancel: Callback when cancel button is clicked
            
        Returns:
            ProgressBar instance for the operation
        """
        # Create progress bar
        progress_bar = ProgressBar(
            parent_id=self.container_id,
            label=operation_name,
            show_cancel=show_cancel,
            on_cancel=on_cancel,
            tag=f"progress_bar_{operation_id}"
        )
        
        # Add to dictionary
        self.progress_bars[operation_id] = progress_bar
        
        # Show progress manager if hidden
        self.show()
        
        return progress_bar
    
    def remove_operation(self, operation_id: str) -> None:
        """
        Remove an operation from tracking.
        
        Args:
            operation_id: ID of the operation to remove
        """
        if operation_id in self.progress_bars:
            # Get progress bar
            progress_bar = self.progress_bars[operation_id]
            
            # Remove UI component
            tag = f"progress_bar_{operation_id}"
            if dpg.does_item_exist(tag):
                dpg.delete_item(tag)
                
            # Remove from dictionary
            del self.progress_bars[operation_id]
            
            # Hide if no operations left
            if not self.progress_bars:
                self.hide()
    
    def update_operation(self, 
                       operation_id: str,
                       progress: Optional[float] = None,
                       status: Optional[str] = None,
                       is_indeterminate: Optional[bool] = None,
                       is_error: Optional[bool] = None,
                       is_paused: Optional[bool] = None) -> None:
        """
        Update an operation's progress and status.
        
        Args:
            operation_id: ID of the operation to update
            progress: Optional progress value (0.0 to 1.0)
            status: Optional status text
            is_indeterminate: Optional indeterminate state
            is_error: Optional error state
            is_paused: Optional paused state
        """
        if operation_id in self.progress_bars:
            progress_bar = self.progress_bars[operation_id]
            
            if progress is not None:
                progress_bar.set_progress(progress)
                
            if status is not None:
                progress_bar.set_status(status)
                
            if is_indeterminate is not None:
                progress_bar.set_indeterminate(is_indeterminate)
                
            if is_error is not None and is_error:
                progress_bar.set_error()
                
            if is_paused is not None:
                progress_bar.set_paused(is_paused)
    
    def show(self) -> None:
        """Show the progress manager."""
        if dpg.does_item_exist(self.collapsing_header_id):
            dpg.configure_item(self.collapsing_header_id, show=True)
    
    def hide(self) -> None:
        """Hide the progress manager."""
        if dpg.does_item_exist(self.collapsing_header_id):
            dpg.configure_item(self.collapsing_header_id, show=False)
            
    def clear(self) -> None:
        """Clear all operations."""
        # Remove all progress bars
        for operation_id in list(self.progress_bars.keys()):
            self.remove_operation(operation_id)