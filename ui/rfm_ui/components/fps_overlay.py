"""
FPS overlay component for RFM Architecture UI.

This module provides a premium FPS (frames per second) overlay with advanced styling.
"""

import dearpygui.dearpygui as dpg
from typing import Optional, List, Tuple
import time
import collections

from rfm_ui.theme import Colors, Spacing, Motion, get_theme


class FPSOverlay:
    """
    Premium styled FPS overlay with animation and color transitions.
    
    Features:
    - Real-time FPS display
    - Color changes based on performance thresholds
    - Animated highlight for critical values
    - Compact, non-intrusive design
    - Optional render time display
    """
    
    def __init__(self, 
                parent_id: int,
                pos: Optional[Tuple[int, int]] = None,
                width: int = 80,
                height: int = 40,
                show_ms: bool = True,
                warning_threshold: float = 30.0,
                critical_threshold: float = 15.0,
                history_size: int = 60,
                update_interval: float = 0.5,
                tag: Optional[str] = None):
        """
        Initialize the FPS overlay.
        
        Args:
            parent_id: DearPyGui ID of the parent container
            pos: Optional position (x, y)
            width: Width of the overlay
            height: Height of the overlay
            show_ms: Whether to show render time in milliseconds
            warning_threshold: FPS threshold for warning state
            critical_threshold: FPS threshold for critical state
            history_size: Number of frames to keep in history for averaging
            update_interval: Update interval in seconds
            tag: Optional tag for the overlay
        """
        self.parent_id = parent_id
        self.pos = pos
        self.width = width
        self.height = height
        self.show_ms = show_ms
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.history_size = history_size
        self.update_interval = update_interval
        self.tag = tag or "fps_overlay"
        
        # FPS tracking
        self._frame_times: collections.deque = collections.deque(maxlen=history_size)
        self._fps = 0.0
        self._render_time = 0.0
        self._last_update_time = 0.0
        
        # UI components
        self._overlay_id = None
        self._fps_text_id = None
        self._ms_text_id = None
        self._group_id = None
        
        # Theme components
        self._normal_theme = None
        self._warning_theme = None
        self._critical_theme = None
        self._current_theme = None
        
        # Animation state
        self._is_pulsing = False
        self._pulse_start_time = 0
        self._pulse_duration = Motion.DURATION_SLOW  # ms
        
        # Create the overlay
        self._create()
        
    def _create(self) -> None:
        """Create the FPS overlay component."""
        # Create themes for different states
        self._create_themes()
        
        # Create the overlay window
        with dpg.window(
            label="FPS",
            parent=self.parent_id,
            pos=self.pos,
            width=self.width,
            height=self.height,
            no_title_bar=True,
            no_resize=True,
            no_move=True,
            no_scrollbar=True,
            no_background=True,
            tag=self.tag
        ) as self._overlay_id:
            # Create a group for the FPS display
            with dpg.group(horizontal=False) as self._group_id:
                # FPS text
                self._fps_text_id = dpg.add_text(
                    "0 FPS",
                    color=Colors.TEXT_PRIMARY
                )
                
                # Render time text (optional)
                if self.show_ms:
                    self._ms_text_id = dpg.add_text(
                        "0.0 ms",
                        color=Colors.TEXT_SECONDARY
                    )
                    
        # Apply initial theme
        dpg.bind_item_theme(self._overlay_id, self._normal_theme)
        
        # Set up the update callback
        with dpg.item_handler_registry() as handler:
            dpg.add_item_visible_handler(callback=self._on_visible)
            
        dpg.bind_item_handler_registry(self._overlay_id, handler)
    
    def _create_themes(self) -> None:
        """Create themes for different FPS states."""
        # Normal state theme (good FPS)
        with dpg.theme() as self._normal_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_Text, Colors.TEAL_ACCENT, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (0, 0, 0, 128), category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, Spacing.RADIUS_MD, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, [Spacing.XS, Spacing.XS], category=dpg.mvThemeCat_Core)
        
        # Warning state theme (medium FPS)
        with dpg.theme() as self._warning_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_Text, Colors.AMBER_ACCENT, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (0, 0, 0, 128), category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, Spacing.RADIUS_MD, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, [Spacing.XS, Spacing.XS], category=dpg.mvThemeCat_Core)
        
        # Critical state theme (low FPS)
        with dpg.theme() as self._critical_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_Text, Colors.ERROR, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (0, 0, 0, 128), category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, Spacing.RADIUS_MD, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, [Spacing.XS, Spacing.XS], category=dpg.mvThemeCat_Core)
        
        # Set initial theme
        self._current_theme = self._normal_theme
    
    def _on_visible(self) -> None:
        """
        Handler for when the overlay becomes visible.
        Sets up the frame callback for updates.
        """
        dpg.set_frame_callback(1, self._update_callback)
    
    def _update_callback(self, sender, app_data) -> None:
        """
        Update callback for FPS calculations.
        Called every frame to update FPS display.
        
        Args:
            sender: Sender ID
            app_data: Unused
        """
        # Check if overlay still exists
        if not dpg.does_item_exist(self._overlay_id):
            return
            
        # Get current time
        current_time = time.time()
        
        # Add frame time
        self._frame_times.append(current_time)
        
        # Only update display periodically for better readability
        if current_time - self._last_update_time >= self.update_interval:
            self._last_update_time = current_time
            
            # Calculate FPS if we have enough frames
            if len(self._frame_times) >= 2:
                elapsed = self._frame_times[-1] - self._frame_times[0]
                if elapsed > 0:
                    self._fps = (len(self._frame_times) - 1) / elapsed
                    
                    # Update FPS text
                    if dpg.does_item_exist(self._fps_text_id):
                        dpg.set_value(self._fps_text_id, f"{self._fps:.1f} FPS")
                    
                    # Update theme based on FPS thresholds
                    self._update_theme()
        
        # Continue updates
        dpg.set_frame_callback(1, self._update_callback)
    
    def _update_theme(self) -> None:
        """Update the overlay theme based on current FPS."""
        new_theme = None
        
        # Determine theme based on FPS
        if self._fps <= self.critical_threshold:
            new_theme = self._critical_theme
            
            # Start pulsing animation for critical FPS
            if not self._is_pulsing:
                self._start_pulse_animation()
                
        elif self._fps <= self.warning_threshold:
            new_theme = self._warning_theme
            self._is_pulsing = False
        else:
            new_theme = self._normal_theme
            self._is_pulsing = False
        
        # Apply theme if changed
        if new_theme != self._current_theme:
            self._current_theme = new_theme
            dpg.bind_item_theme(self._overlay_id, new_theme)
    
    def _start_pulse_animation(self) -> None:
        """Start a pulsing animation for critical FPS."""
        self._is_pulsing = True
        self._pulse_start_time = time.time() * 1000  # ms
        
        def _pulse_callback():
            # Check if overlay still exists and we're still pulsing
            if not dpg.does_item_exist(self._overlay_id) or not self._is_pulsing:
                return
                
            current_time = time.time() * 1000
            elapsed = current_time - self._pulse_start_time
            
            # Calculate pulse factor (0.0 to 1.0 and back, based on progress)
            phase = (elapsed % self._pulse_duration) / self._pulse_duration
            factor = 1.0 - abs(2.0 * phase - 1.0)  # Triangle wave pattern
            
            # Apply pulsing effect by adjusting text brightness
            if dpg.does_item_exist(self._fps_text_id):
                # Blend between normal and bright red
                base_color = Colors.ERROR
                bright_color = (255, 100, 100, 255)
                
                color = (
                    int(base_color[0] + (bright_color[0] - base_color[0]) * factor),
                    int(base_color[1] + (bright_color[1] - base_color[1]) * factor),
                    int(base_color[2] + (bright_color[2] - base_color[2]) * factor),
                    255
                )
                
                dpg.configure_item(self._fps_text_id, color=color)
            
            # Continue animation
            if self._is_pulsing:
                dpg.set_frame_callback(1, _pulse_callback)
        
        # Start the animation
        dpg.set_frame_callback(1, _pulse_callback)
    
    def set_render_time(self, ms: float) -> None:
        """
        Set the render time to display.
        
        Args:
            ms: Render time in milliseconds
        """
        if not self.show_ms or not dpg.does_item_exist(self._ms_text_id):
            return
            
        self._render_time = ms
        dpg.set_value(self._ms_text_id, f"{ms:.1f} ms")
        
        # Color based on render time
        if ms > 100:
            dpg.configure_item(self._ms_text_id, color=Colors.ERROR)
        elif ms > 50:
            dpg.configure_item(self._ms_text_id, color=Colors.AMBER_ACCENT)
        else:
            dpg.configure_item(self._ms_text_id, color=Colors.TEXT_SECONDARY)
    
    def show(self) -> None:
        """Show the FPS overlay."""
        if dpg.does_item_exist(self._overlay_id):
            dpg.configure_item(self._overlay_id, show=True)
    
    def hide(self) -> None:
        """Hide the FPS overlay."""
        if dpg.does_item_exist(self._overlay_id):
            dpg.configure_item(self._overlay_id, show=False)
    
    def toggle_visibility(self) -> None:
        """Toggle the visibility of the FPS overlay."""
        if dpg.does_item_exist(self._overlay_id):
            is_visible = dpg.is_item_visible(self._overlay_id)
            dpg.configure_item(self._overlay_id, show=not is_visible)
            
    def get_latest_ms(self) -> float:
        """
        Get the latest render time in milliseconds.
        
        Returns:
            Latest render time in milliseconds
        """
        return self._render_time
    
    # --- Telemetry ---------------------------------------------------------------
    import json, psutil, threading, time, pathlib
    _METRIC_PATH = pathlib.Path.home() / ".rfm_ui_metrics.json"
    _METRIC_PATH.touch(exist_ok=True)
    
    def _telemetry_loop(self, get_frame_ms):
        proc = psutil.Process()
        last_jump = 0
        while True:
            time.sleep(5)                         # every 5 s
            frame = get_frame_ms()                # closure from overlay
            mem_mb = proc.memory_info().rss / 1e6
            stamp = time.time()
            # append metric row
            with self._METRIC_PATH.open("a") as f:
                f.write(json.dumps({"t": stamp, "ms": frame, "ram": mem_mb}) + "\n")
            # quick in-app warning if perf drops hard
            if frame - last_jump > 5:             # >5 ms regression
                if self._fps_text_id and dpg.does_item_exist(self._fps_text_id):
                    dpg.configure_item(self._fps_text_id, color=(255, 100, 100, 255))
            last_jump = frame
    
    def start_telemetry(self):
        """Start the telemetry thread to monitor performance."""
        threading.Thread(target=self._telemetry_loop,
                         args=(self.get_latest_ms,),
                         daemon=True).start()