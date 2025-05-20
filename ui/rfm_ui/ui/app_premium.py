"""
Premium application class for RFM Architecture UI.

This module provides an enhanced version of the main application class
with premium UI components and styling.
"""

import os
import sys
import time
import logging
import threading
import asyncio
from typing import Dict, Any, Optional, List, Callable, Tuple

import dearpygui.dearpygui as dpg
import numpy as np

from rfm_ui.errors import get_error_handler, error_boundary, error_context, FractalError, UIError
from rfm_ui.performance import get_performance_tracker
from rfm_ui.engine.core import FractalEngine
from rfm_ui.theme import get_theme
from rfm_ui.components import (
    PremiumSlider, 
    PremiumSliderInt,
    AccentButton,
    SecondaryButton,
    PremiumButton,
    GlassPanel,
    CardPanel,
    FPSOverlay
)
from .error_dialog import ErrorDialog


class PremiumRFMApp:
    """
    Premium UI application class for RFM Architecture.
    
    This class enhances the standard RFMApp with premium UI components
    and styling for a more polished user experience.
    """
    
    def __init__(self, 
                config_file: Optional[str] = None, 
                log_dir: Optional[str] = None,
                initial_params: Optional[Dict[str, Any]] = None):
        """
        Initialize the Premium RFM Architecture UI application.
        
        Args:
            config_file: Path to configuration file
            log_dir: Directory for logs
            initial_params: Initial parameters to load (from share link)
        """
        self.config_file = config_file or "config.yaml"
        self.log_dir = log_dir or "logs"
        self.initial_params = initial_params
        
        # Ensure log directory exists
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(self.log_dir, "rfm_ui.log")),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("rfm_ui")
        
        # Initialize error handler
        self.error_handler = get_error_handler(os.path.join(self.log_dir, "errors"))
        
        # Initialize performance tracker
        self.performance_tracker = get_performance_tracker(os.path.join(self.log_dir, "performance"))
        
        # Initialize fractal engine
        self.engine = FractalEngine()
        
        # UI state
        self.current_fractal_type = "mandelbrot"
        self.current_params = {}
        self.current_render = None
        self.render_time = 0
        self.is_rendering = False
        self.render_queue = asyncio.Queue()
        self.render_task = None
        self.last_render_time = 0
        self.fps = 0
        self.frame_times = []
        
        # Main UI components
        self.primary_window = "primary_window"
        self.parameters_window = "parameters_window"
        self.viewport_width = 1280
        self.viewport_height = 720
        self.render_width = 800
        self.render_height = 600
        
        # UI components
        self.error_dialog = None
        self.performance_visualizer = None
        self.fps_overlay = None
        self.parameter_panel = None
        self.render_panel = None
        
        # Premium UI components
        self.sliders = {}
        self.buttons = {}
        self.dropdowns = {}
        
        # Theme
        self.theme = get_theme(dark_mode=True)
        
    @error_boundary
    def initialize(self) -> bool:
        """
        Initialize the application.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        start_time = time.time()
        
        # Record app initialization
        perf_ctx = self.performance_tracker.start_operation(
            "app_initialization", {"config_file": self.config_file}
        )
        
        try:
            # Initialize Dear PyGui
            dpg.create_context()
            
            # Set up fonts
            self._setup_fonts()
            
            # Create viewport
            dpg.create_viewport(
                title="RFM Architecture Visualizer", 
                width=self.viewport_width, 
                height=self.viewport_height,
                vsync=True
            )
            
            # Apply premium theme
            self.theme.apply()
            
            # Set up UI
            self._setup_ui()
            
            # Set up error handler
            self.error_dialog = ErrorDialog()
            self.error_dialog.initialize()
            self.error_handler.register_handler(self.error_dialog.show_error)
            
            # Set up performance visualizer
            from rfm_ui.performance.visualizer import PerformanceVisualizer
            self.performance_visualizer = PerformanceVisualizer(self.performance_tracker)
            self.performance_visualizer.initialize()
            
            # Setup viewport
            dpg.setup_dearpygui()
            dpg.show_viewport()
            
            # Set default font
            if hasattr(self.theme, 'font_regular') and self.theme.font_regular:
                dpg.bind_font(self.theme.font_regular)
            
            # Apply initial parameters if provided
            if self.initial_params:
                self._apply_initial_parameters()
            
            # Start render task
            self._start_render_task()
            
            # Log initialization time
            self.logger.info(f"Application initialized in {time.time() - start_time:.2f} seconds")
            
            return True
        except Exception as e:
            self.logger.error(f"Error initializing application: {e}", exc_info=True)
            self.error_handler.handle_error(UIError(
                message=f"Failed to initialize application: {e}",
                component="app",
                severity=FractalError.ErrorSeverity.CRITICAL
            ))
            return False
        finally:
            # End performance tracking
            self.performance_tracker.end_operation(perf_ctx)
    
    def _setup_fonts(self) -> None:
        """Set up fonts for the application."""
        # Fonts are already set up in the theme module
        pass
            
    def _setup_ui(self) -> None:
        """Set up the main UI components with premium styling."""
        # Create main menu bar
        with dpg.viewport_menu_bar():
            with dpg.menu(label="File"):
                dpg.add_menu_item(label="New", callback=self._on_new)
                dpg.add_menu_item(label="Open", callback=self._on_open)
                dpg.add_menu_item(label="Save", callback=self._on_save)
                dpg.add_menu_item(label="Export", callback=self._on_export)
                dpg.add_separator()
                dpg.add_menu_item(label="Exit", callback=self._on_exit)
                
            with dpg.menu(label="View"):
                dpg.add_menu_item(label="Reset View", callback=self._on_reset_view)
                dpg.add_menu_item(label="Performance Monitor", callback=self._on_performance_monitor)
                
            with dpg.menu(label="Help"):
                dpg.add_menu_item(label="About", callback=self._on_about)
                dpg.add_menu_item(label="Documentation", callback=self._on_documentation)
        
        # Create main window
        with dpg.window(label="RFM Architecture Visualizer", tag=self.primary_window,
                       width=self.viewport_width, height=self.viewport_height,
                       no_title_bar=True, no_resize=True, no_move=True, no_close=True):
            
            # Split view: parameters on left, render on right
            with dpg.group(horizontal=True):
                # Parameters panel as glass panel
                self.parameter_panel = GlassPanel(
                    parent_id=dpg.last_item(),
                    label="Parameters",
                    width=400,
                    height=-1,
                    show_title_bar=True,
                    tag=self.parameters_window
                )
                parameters_id = self.parameter_panel.get_panel_id()
                
                # Render panel
                self.render_panel = CardPanel(
                    parent_id=dpg.last_item(),
                    label="Render",
                    width=-1,
                    height=-1,
                    show_title_bar=True,
                    tag="render_panel"
                )
                render_id = self.render_panel.get_panel_id()
                
        # Set up panel contents
        self._setup_parameters_ui(parameters_id)
        self._setup_render_ui(render_id)
                    
        # Set up handlers
        with dpg.handler_registry():
            dpg.add_key_press_handler(dpg.mvKey_F5, callback=self._on_refresh)
            dpg.add_key_press_handler(dpg.mvKey_P, callback=self._on_performance_monitor)
            
        # Add FPS overlay
        self.fps_overlay = FPSOverlay(
            parent_id=self.primary_window,
            pos=(10, 10),
            show_ms=True
        )
        
        # Start telemetry monitoring
        self.fps_overlay.start_telemetry()
            
    def _setup_parameters_ui(self, parent_id: int) -> None:
        """
        Set up the parameters UI panel with premium components.
        
        Args:
            parent_id: ID of the parent container
        """
        # Fractal type selection
        dpg.add_text("Fractal Type", parent=parent_id)
        self.dropdowns["fractal_type"] = dpg.add_combo(
            items=["Mandelbrot", "Julia", "L-System", "Cantor Dust"],
            default_value="Mandelbrot",
            callback=self._on_fractal_type_changed,
            width=-1,
            parent=parent_id,
            tag="fractal_type_combo"
        )
        
        dpg.add_separator(parent=parent_id)
        
        # Parameters section - will be dynamically populated
        with dpg.collapsing_header(label="Parameters", default_open=True, tag="parameters_header", parent=parent_id):
            pass  # Will be populated dynamically
            
        # Visualization section
        with dpg.collapsing_header(label="Visualization", default_open=True, parent=parent_id):
            dpg.add_text("Color Map", parent=dpg.last_item())
            self.dropdowns["colormap"] = dpg.add_combo(
                items=["viridis", "plasma", "inferno", "magma", "cividis", "turbo"],
                default_value="viridis",
                callback=self._on_param_changed,
                width=-1,
                parent=dpg.last_item(),
                tag="colormap_combo"
            )
            
            dpg.add_text("Resolution", parent=dpg.last_item())
            with dpg.group(horizontal=True, parent=dpg.last_item()):
                # Width input
                dpg.add_input_int(
                    default_value=800, 
                    callback=self._on_resolution_changed,
                    width=150,
                    tag="width_input"
                )
                dpg.add_text("×")
                # Height input
                dpg.add_input_int(
                    default_value=600, 
                    callback=self._on_resolution_changed,
                    width=150,
                    tag="height_input"
                )
                
            # High quality checkbox
            dpg.add_checkbox(
                label="High Quality", 
                default_value=True,
                callback=self._on_param_changed,
                parent=dpg.last_container(),
                tag="high_quality_checkbox"
            )
            
        # Advanced section
        with dpg.collapsing_header(label="Advanced", default_open=False, parent=parent_id):
            adv_container = dpg.last_item()
            dpg.add_text("Performance", parent=adv_container)
            
            # Max render time slider
            self.sliders["max_render_time"] = PremiumSliderInt(
                parent_id=adv_container,
                label="Max Render Time",
                default_value=1000,
                min_value=100,
                max_value=5000,
                callback=self._on_param_changed,
                tag="max_render_time_slider"
            )
            
            # Auto refresh checkbox
            dpg.add_checkbox(
                label="Auto Refresh", 
                default_value=True,
                callback=self._on_param_changed,
                parent=adv_container,
                tag="auto_refresh_checkbox"
            )
            
            # Refresh interval slider
            self.sliders["refresh_interval"] = PremiumSlider(
                parent_id=adv_container,
                label="Refresh Interval",
                default_value=200,
                min_value=50,
                max_value=1000,
                format="%.0f ms",
                callback=self._on_param_changed,
                tag="refresh_interval_slider"
            )
            
        # Presets section
        with dpg.collapsing_header(label="Presets", default_open=False, parent=parent_id):
            presets_container = dpg.last_item()
            
            # Buttons for presets
            with dpg.group(horizontal=True, parent=presets_container):
                # Load preset button
                self.buttons["load_preset"] = AccentButton(
                    parent_id=dpg.last_item(),
                    label="Load Preset",
                    callback=self._on_load_preset,
                    width=150
                )
                
                # Save preset button
                self.buttons["save_preset"] = SecondaryButton(
                    parent_id=dpg.last_item(),
                    label="Save Preset",
                    callback=self._on_save_preset,
                    width=150
                )
            
            # Preset list
            dpg.add_text("Available Presets", parent=presets_container)
            dpg.add_listbox(
                items=["Default", "Zoomed Mandelbrot", "Julia Swirl", "Dendrite"],
                callback=self._on_preset_selected,
                width=-1,
                num_items=4,
                parent=presets_container,
                tag="preset_listbox"
            )
            
        # Stats and info
        with dpg.collapsing_header(label="Statistics", default_open=True, parent=parent_id):
            stats_container = dpg.last_item()
            with dpg.table(header_row=False, parent=stats_container):
                dpg.add_table_column()
                dpg.add_table_column()
                
                # Row for render time
                with dpg.table_row():
                    dpg.add_text("Render Time:")
                    dpg.add_text("0 ms", tag="render_time_text")
                    
                # Row for FPS
                with dpg.table_row():
                    dpg.add_text("FPS:")
                    dpg.add_text("0", tag="fps_text")
                    
                # Row for parameters
                with dpg.table_row():
                    dpg.add_text("Parameters:")
                    dpg.add_text("0", tag="param_count_text")
        
        # Initial update
        self._update_parameter_ui("mandelbrot")
        
    def _setup_render_ui(self, parent_id: int) -> None:
        """
        Set up the render UI panel with premium components.
        
        Args:
            parent_id: ID of the parent container
        """
        # Create a drawing canvas for the fractal
        with dpg.texture_registry():
            dpg.add_dynamic_texture(
                width=self.render_width, 
                height=self.render_height, 
                default_value=np.zeros((self.render_height, self.render_width, 4), dtype=np.float32),
                tag="fractal_texture"
            )
            
        # Display the texture
        with dpg.group(horizontal=True, parent=parent_id):
            dpg.add_image("fractal_texture", tag="fractal_image")
            
        # Add controls below the render
        with dpg.group(horizontal=True, parent=parent_id, tag="render_controls"):
            # Refresh button
            self.buttons["refresh"] = AccentButton(
                parent_id=dpg.last_item(),
                label="Refresh",
                callback=self._on_refresh
            )
            
            # Reset button
            self.buttons["reset"] = PremiumButton(
                parent_id=dpg.last_item(),
                label="Reset",
                callback=self._on_reset
            )
            
            # Zoom buttons
            self.buttons["zoom_in"] = PremiumButton(
                parent_id=dpg.last_item(),
                label="Zoom In",
                callback=lambda: self._on_zoom(1.5)
            )
            
            self.buttons["zoom_out"] = PremiumButton(
                parent_id=dpg.last_item(),
                label="Zoom Out",
                callback=lambda: self._on_zoom(0.67)
            )
            
    @error_boundary
    def _apply_initial_parameters(self) -> None:
        """Apply initial parameters loaded from share link."""
        try:
            if not self.initial_params:
                return
                
            # Log information about initial parameters
            self.logger.info(f"Applying initial parameters from share link")
            
            # Get fractal type
            fractal_type = self.initial_params.get("type", "mandelbrot").lower()
            
            # Update UI for this fractal type
            if dpg.does_alias_exist("fractal_type_combo"):
                fractal_type_display = fractal_type.capitalize()
                if fractal_type == "l_system":
                    fractal_type_display = "L-System"
                elif fractal_type == "cantor dust":
                    fractal_type_display = "Cantor Dust"
                    
                dpg.set_value("fractal_type_combo", fractal_type_display)
                self._update_parameter_ui(fractal_type)
                
            # Update parameters based on fractal type
            if fractal_type == "mandelbrot":
                # Update sliders directly if using premium component
                if "center_x" in self.sliders:
                    self.sliders["center_x"].set_value(self.initial_params.get("center_x", -0.5))
                    self.sliders["center_y"].set_value(self.initial_params.get("center_y", 0.0))
                    self.sliders["zoom"].set_value(self.initial_params.get("zoom", 1.0))
                    self.sliders["max_iter"].set_value(self.initial_params.get("max_iter", 100))
                    
            elif fractal_type == "julia":
                # Update sliders directly if using premium component
                if "c_real" in self.sliders:
                    self.sliders["c_real"].set_value(self.initial_params.get("c_real", -0.7))
                    self.sliders["c_imag"].set_value(self.initial_params.get("c_imag", 0.27))
                    self.sliders["center_x"].set_value(self.initial_params.get("center_x", 0.0))
                    self.sliders["center_y"].set_value(self.initial_params.get("center_y", 0.0))
                    self.sliders["zoom"].set_value(self.initial_params.get("zoom", 1.5))
                    self.sliders["max_iter"].set_value(self.initial_params.get("max_iter", 100))
                    
            # Update colormap if available
            if dpg.does_alias_exist("colormap_combo") and "colormap" in self.initial_params:
                dpg.set_value("colormap_combo", self.initial_params["colormap"])
                
            # Update resolution if available
            if dpg.does_alias_exist("width_input") and "width" in self.initial_params:
                dpg.set_value("width_input", self.initial_params["width"])
                
            if dpg.does_alias_exist("height_input") and "height" in self.initial_params:
                dpg.set_value("height_input", self.initial_params["height"])
                
            # Update parameters
            self._build_params_from_ui()
            
            # Trigger render
            self._queue_render()
            
            # Show notification
            with dpg.window(label="Preset Loaded", modal=True, width=300, height=120, pos=(300, 300)):
                container_id = dpg.last_item()
                dpg.add_text("Successfully loaded preset from share link!", parent=container_id)
                
                # OK button
                AccentButton(
                    parent_id=container_id,
                    label="OK",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=container_id,
                    width=100
                )
                
        except Exception as e:
            self.logger.error(f"Error applying initial parameters: {e}", exc_info=True)
            self.error_handler.handle_error(UIError(
                message=f"Failed to apply preset parameters: {e}",
                component="app",
                severity=FractalError.ErrorSeverity.WARNING
            ))
    
    def _update_parameter_ui(self, fractal_type: str) -> None:
        """
        Update the parameter UI for the given fractal type using premium components.
        
        Args:
            fractal_type: Type of fractal to show parameters for
        """
        # Clear existing parameters
        if dpg.does_alias_exist("parameters_header"):
            for child in dpg.get_item_children("parameters_header", 1):
                dpg.delete_item(child)
                
        # Clear sliders dictionary for this category
        param_sliders = {}
        
        # Set parameters based on fractal type
        if fractal_type.lower() == "mandelbrot":
            with dpg.group(parent="parameters_header"):
                container_id = dpg.last_item()
                
                dpg.add_text("Center", parent=container_id)
                with dpg.group(horizontal=True, parent=container_id):
                    group_id = dpg.last_item()
                    
                    # Center X slider
                    param_sliders["center_x"] = PremiumSlider(
                        parent_id=group_id,
                        label="X",
                        default_value=-0.5,
                        min_value=-2.0,
                        max_value=1.0,
                        format="%.6f",
                        width=150,
                        callback=self._on_param_changed,
                        tag="center_x_input"
                    )
                    
                    # Center Y slider
                    param_sliders["center_y"] = PremiumSlider(
                        parent_id=group_id,
                        label="Y",
                        default_value=0.0,
                        min_value=-1.5,
                        max_value=1.5,
                        format="%.6f",
                        width=150,
                        callback=self._on_param_changed,
                        tag="center_y_input"
                    )
                
                # Zoom slider
                param_sliders["zoom"] = PremiumSlider(
                    parent_id=container_id,
                    label="Zoom",
                    default_value=1.0,
                    min_value=0.1,
                    max_value=1e10,
                    format="%.6f",
                    callback=self._on_param_changed,
                    tag="zoom_slider"
                )
                
                # Max iterations slider
                param_sliders["max_iter"] = PremiumSliderInt(
                    parent_id=container_id,
                    label="Max Iterations",
                    default_value=100,
                    min_value=10,
                    max_value=1000,
                    callback=self._on_param_changed,
                    tag="max_iter_slider"
                )
                
        elif fractal_type.lower() == "julia":
            with dpg.group(parent="parameters_header"):
                container_id = dpg.last_item()
                
                dpg.add_text("Complex Parameter", parent=container_id)
                with dpg.group(horizontal=True, parent=container_id):
                    group_id = dpg.last_item()
                    
                    # C-real parameter
                    param_sliders["c_real"] = PremiumSlider(
                        parent_id=group_id,
                        label="Real",
                        default_value=-0.7,
                        min_value=-2.0,
                        max_value=2.0,
                        format="%.6f",
                        width=150,
                        callback=self._on_param_changed,
                        tag="c_real_input"
                    )
                    
                    # C-imaginary parameter
                    param_sliders["c_imag"] = PremiumSlider(
                        parent_id=group_id,
                        label="Imaginary",
                        default_value=0.27,
                        min_value=-2.0,
                        max_value=2.0,
                        format="%.6f",
                        width=150,
                        callback=self._on_param_changed,
                        tag="c_imag_input"
                    )
                
                dpg.add_text("Center", parent=container_id)
                with dpg.group(horizontal=True, parent=container_id):
                    group_id = dpg.last_item()
                    
                    # Center X slider
                    param_sliders["center_x"] = PremiumSlider(
                        parent_id=group_id,
                        label="X",
                        default_value=0.0,
                        min_value=-2.0,
                        max_value=2.0,
                        format="%.6f",
                        width=150,
                        callback=self._on_param_changed,
                        tag="center_x_input"
                    )
                    
                    # Center Y slider
                    param_sliders["center_y"] = PremiumSlider(
                        parent_id=group_id,
                        label="Y",
                        default_value=0.0,
                        min_value=-2.0,
                        max_value=2.0,
                        format="%.6f",
                        width=150,
                        callback=self._on_param_changed,
                        tag="center_y_input"
                    )
                
                # Zoom slider
                param_sliders["zoom"] = PremiumSlider(
                    parent_id=container_id,
                    label="Zoom",
                    default_value=1.5,
                    min_value=0.1,
                    max_value=1e10,
                    format="%.6f",
                    callback=self._on_param_changed,
                    tag="zoom_slider"
                )
                
                # Max iterations slider
                param_sliders["max_iter"] = PremiumSliderInt(
                    parent_id=container_id,
                    label="Max Iterations",
                    default_value=100,
                    min_value=10,
                    max_value=1000,
                    callback=self._on_param_changed,
                    tag="max_iter_slider"
                )
                
                # Add Julia set preset selector
                dpg.add_text("Julia Presets", parent=container_id)
                self.dropdowns["julia_preset"] = dpg.add_combo(
                    items=["Custom", "Douady Rabbit", "Dendrite", "Siegel Disk"],
                    default_value="Custom",
                    callback=self._on_julia_preset_changed,
                    width=-1,
                    parent=container_id,
                    tag="julia_preset_combo"
                )
                
        elif fractal_type.lower() == "l_system":
            with dpg.group(parent="parameters_header"):
                container_id = dpg.last_item()
                
                dpg.add_text("Axiom", parent=container_id)
                dpg.add_input_text(
                    default_value="F", 
                    callback=self._on_param_changed,
                    width=-1,
                    parent=container_id,
                    tag="axiom_input"
                )
                
                dpg.add_text("Rules", parent=container_id)
                dpg.add_input_text(
                    default_value="F:F+F-F-F+F", 
                    callback=self._on_param_changed,
                    width=-1,
                    parent=container_id,
                    tag="rules_input"
                )
                
                # Angle slider
                param_sliders["angle"] = PremiumSlider(
                    parent_id=container_id,
                    label="Angle",
                    default_value=90.0,
                    min_value=0.0,
                    max_value=180.0,
                    format="%.1f°",
                    callback=self._on_param_changed,
                    tag="angle_slider"
                )
                
                # Iterations slider
                param_sliders["iterations"] = PremiumSliderInt(
                    parent_id=container_id,
                    label="Iterations",
                    default_value=4,
                    min_value=1,
                    max_value=10,
                    callback=self._on_param_changed,
                    tag="iterations_slider"
                )
                
                # Line width slider
                param_sliders["line_width"] = PremiumSlider(
                    parent_id=container_id,
                    label="Line Width",
                    default_value=1.0,
                    min_value=0.1,
                    max_value=5.0,
                    format="%.1f px",
                    callback=self._on_param_changed,
                    tag="line_width_slider"
                )
                
                dpg.add_text("Color", parent=container_id)
                dpg.add_color_edit(
                    default_value=[176, 134, 255, 255],
                    callback=self._on_param_changed,
                    width=-1,
                    parent=container_id,
                    tag="color_picker"
                )
                
        elif fractal_type.lower() == "cantor dust":
            with dpg.group(parent="parameters_header"):
                container_id = dpg.last_item()
                
                # Gap ratio slider
                param_sliders["gap_ratio"] = PremiumSlider(
                    parent_id=container_id,
                    label="Gap Ratio",
                    default_value=0.3,
                    min_value=0.1,
                    max_value=0.9,
                    format="%.2f",
                    callback=self._on_param_changed,
                    tag="gap_ratio_slider"
                )
                
                # Iterations slider
                param_sliders["iterations"] = PremiumSliderInt(
                    parent_id=container_id,
                    label="Iterations",
                    default_value=4,
                    min_value=1,
                    max_value=10,
                    callback=self._on_param_changed,
                    tag="iterations_slider"
                )
                
                dpg.add_text("Color", parent=container_id)
                dpg.add_color_edit(
                    default_value=[176, 134, 255, 255],
                    callback=self._on_param_changed,
                    width=-1,
                    parent=container_id,
                    tag="color_picker"
                )
                
        # Store parameter sliders
        self.sliders.update(param_sliders)
        
        # Build current params dictionary to update UI
        self._build_params_from_ui()
        
        # Update parameter count
        dpg.set_value("param_count_text", str(len(self.current_params)))
        
    def _build_params_from_ui(self) -> Dict[str, Any]:
        """
        Build parameter dictionary from UI values.
        
        Returns:
            Dictionary of parameters
        """
        params = {}
        
        # Get fractal type
        fractal_type = dpg.get_value("fractal_type_combo").lower()
        params["type"] = fractal_type
        
        # Get common parameters
        if dpg.does_alias_exist("colormap_combo"):
            params["colormap"] = dpg.get_value("colormap_combo")
            
        if dpg.does_alias_exist("high_quality_checkbox"):
            params["high_quality"] = dpg.get_value("high_quality_checkbox")
            
        # Get resolution
        if dpg.does_alias_exist("width_input") and dpg.does_alias_exist("height_input"):
            params["width"] = dpg.get_value("width_input")
            params["height"] = dpg.get_value("height_input")
            
        # Get type-specific parameters
        if fractal_type == "mandelbrot" or fractal_type == "julia":
            if dpg.does_alias_exist("center_x_input") and dpg.does_alias_exist("center_y_input"):
                params["center_x"] = dpg.get_value("center_x_input")
                params["center_y"] = dpg.get_value("center_y_input")
                
            if dpg.does_alias_exist("zoom_slider"):
                params["zoom"] = dpg.get_value("zoom_slider")
                
            if dpg.does_alias_exist("max_iter_slider"):
                params["max_iter"] = dpg.get_value("max_iter_slider")
                
            # Julia specific
            if fractal_type == "julia":
                if dpg.does_alias_exist("c_real_input") and dpg.does_alias_exist("c_imag_input"):
                    params["c_real"] = dpg.get_value("c_real_input")
                    params["c_imag"] = dpg.get_value("c_imag_input")
                    
        elif fractal_type == "l_system":
            if dpg.does_alias_exist("axiom_input"):
                params["axiom"] = dpg.get_value("axiom_input")
                
            if dpg.does_alias_exist("rules_input"):
                # Parse rules (format: "F:F+F-F-F+F")
                rules_str = dpg.get_value("rules_input")
                rules = {}
                for rule in rules_str.split(","):
                    if ":" in rule:
                        key, value = rule.split(":", 1)
                        rules[key.strip()] = value.strip()
                params["rules"] = rules
                
            if dpg.does_alias_exist("angle_slider"):
                params["angle"] = dpg.get_value("angle_slider")
                
            if dpg.does_alias_exist("iterations_slider"):
                params["iterations"] = dpg.get_value("iterations_slider")
                
            if dpg.does_alias_exist("line_width_slider"):
                params["line_width"] = dpg.get_value("line_width_slider")
                
            if dpg.does_alias_exist("color_picker"):
                color = dpg.get_value("color_picker")
                params["color"] = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                params["alpha"] = color[3] / 255.0
                
        elif fractal_type == "cantor dust":
            if dpg.does_alias_exist("gap_ratio_slider"):
                params["gap_ratio"] = dpg.get_value("gap_ratio_slider")
                
            if dpg.does_alias_exist("iterations_slider"):
                params["iterations"] = dpg.get_value("iterations_slider")
                
            if dpg.does_alias_exist("color_picker"):
                color = dpg.get_value("color_picker")
                params["color"] = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                params["alpha"] = color[3] / 255.0
                
        # Store current params
        self.current_params = params
        
        return params
        
    @error_boundary
    def _on_fractal_type_changed(self, sender, app_data) -> None:
        """
        Handle fractal type change.
        
        Args:
            sender: Sender widget ID
            app_data: New value
        """
        fractal_type = app_data.lower()
        
        # Update UI for new fractal type
        self._update_parameter_ui(fractal_type)
        
        # Update current fractal type
        self.current_fractal_type = fractal_type
        
        # Trigger render
        self._queue_render()
        
    @error_boundary
    def _on_param_changed(self, sender, app_data) -> None:
        """
        Handle parameter change.
        
        Args:
            sender: Sender widget ID
            app_data: New value
        """
        # Update parameters
        self._build_params_from_ui()
        
        # Update parameter count
        dpg.set_value("param_count_text", str(len(self.current_params)))
        
        # Check if auto-refresh is enabled
        if dpg.does_alias_exist("auto_refresh_checkbox") and dpg.get_value("auto_refresh_checkbox"):
            self._queue_render()
            
    @error_boundary
    def _on_julia_preset_changed(self, sender, app_data) -> None:
        """
        Handle Julia preset change.
        
        Args:
            sender: Sender widget ID
            app_data: New value
        """
        preset = app_data
        
        # Set parameters based on preset
        if preset == "Douady Rabbit":
            dpg.set_value("c_real_input", -0.123)
            dpg.set_value("c_imag_input", 0.745)
        elif preset == "Dendrite":
            dpg.set_value("c_real_input", 0.0)
            dpg.set_value("c_imag_input", 1.0)
        elif preset == "Siegel Disk":
            dpg.set_value("c_real_input", -0.391)
            dpg.set_value("c_imag_input", -0.587)
            
        # Update parameters
        self._build_params_from_ui()
        
        # Trigger render
        self._queue_render()
        
    @error_boundary
    def _on_resolution_changed(self, sender, app_data) -> None:
        """
        Handle resolution change.
        
        Args:
            sender: Sender widget ID
            app_data: New value
        """
        # Get new dimensions
        if sender == "width_input":
            self.render_width = app_data
        elif sender == "height_input":
            self.render_height = app_data
            
        # Update texture size
        dpg.set_value(
            "fractal_texture", 
            np.zeros((self.render_height, self.render_width, 4), dtype=np.float32)
        )
        
        # Update parameters
        self._build_params_from_ui()
        
        # Trigger render
        self._queue_render()
        
    @error_boundary
    def _on_refresh(self, sender=None, app_data=None) -> None:
        """Handle refresh button."""
        self._queue_render()
        
    @error_boundary
    def _on_reset(self, sender=None, app_data=None) -> None:
        """Handle reset button."""
        # Reset parameters based on fractal type
        fractal_type = self.current_fractal_type
        
        if fractal_type == "mandelbrot":
            # Update slider directly if using premium component
            if "center_x" in self.sliders:
                self.sliders["center_x"].set_value(-0.5)
                self.sliders["center_y"].set_value(0.0)
                self.sliders["zoom"].set_value(1.0)
            else:
                # Fallback to DPG directly
                dpg.set_value("center_x_input", -0.5)
                dpg.set_value("center_y_input", 0.0)
                dpg.set_value("zoom_slider", 1.0)
                
        elif fractal_type == "julia":
            # Update sliders directly if using premium component
            if "c_real" in self.sliders:
                self.sliders["c_real"].set_value(-0.7)
                self.sliders["c_imag"].set_value(0.27)
                self.sliders["center_x"].set_value(0.0)
                self.sliders["center_y"].set_value(0.0)
                self.sliders["zoom"].set_value(1.5)
            else:
                # Fallback to DPG directly
                dpg.set_value("c_real_input", -0.7)
                dpg.set_value("c_imag_input", 0.27)
                dpg.set_value("center_x_input", 0.0)
                dpg.set_value("center_y_input", 0.0)
                dpg.set_value("zoom_slider", 1.5)
                
            # Reset preset combo
            dpg.set_value("julia_preset_combo", "Custom")
            
        # Update parameters
        self._build_params_from_ui()
        
        # Trigger render
        self._queue_render()
        
    @error_boundary
    def _on_zoom(self, factor: float, sender=None, app_data=None) -> None:
        """
        Handle zoom in/out.
        
        Args:
            factor: Zoom factor (>1 for zoom in, <1 for zoom out)
            sender: Sender widget ID
            app_data: New value
        """
        if not dpg.does_alias_exist("zoom_slider"):
            return
            
        # Get current zoom
        current_zoom = dpg.get_value("zoom_slider")
        
        # Calculate new zoom
        new_zoom = current_zoom * factor
        
        # Update zoom slider (use premium component if available)
        if "zoom" in self.sliders:
            self.sliders["zoom"].set_value(new_zoom)
        else:
            dpg.set_value("zoom_slider", new_zoom)
        
        # Update parameters
        self._build_params_from_ui()
        
        # Trigger render
        self._queue_render()
        
    @error_boundary
    def _on_performance_monitor(self, sender=None, app_data=None) -> None:
        """Handle performance monitor button."""
        if self.performance_visualizer:
            self.performance_visualizer.toggle_visibility()
            
    @error_boundary
    def _on_new(self, sender=None, app_data=None) -> None:
        """Handle new menu item."""
        # Reset to default parameters
        self._on_reset()
        
    @error_boundary
    def _on_open(self, sender=None, app_data=None) -> None:
        """Handle open menu item."""
        # Show file dialog
        # For now, just use a placeholder message
        dpg.add_text("Open file dialog would appear here", parent=self.primary_window)
        
    @error_boundary
    def _on_save(self, sender=None, app_data=None) -> None:
        """Handle save menu item."""
        # Show file dialog
        # For now, just use a placeholder message
        dpg.add_text("Save file dialog would appear here", parent=self.primary_window)
        
    @error_boundary
    def _on_export(self, sender=None, app_data=None) -> None:
        """Handle export menu item."""
        # Show file dialog
        # For now, just use a placeholder message
        dpg.add_text("Export file dialog would appear here", parent=self.primary_window)
        
    @error_boundary
    def _on_exit(self, sender=None, app_data=None) -> None:
        """Handle exit menu item."""
        # Clean up
        self._cleanup()
        
        # Exit
        dpg.stop_dearpygui()
        
    @error_boundary
    def _on_reset_view(self, sender=None, app_data=None) -> None:
        """Handle reset view menu item."""
        self._on_reset()
        
    @error_boundary
    def _on_about(self, sender=None, app_data=None) -> None:
        """Handle about menu item."""
        # Show about dialog using premium components
        with dpg.window(label="About", modal=True, width=400, height=200, pos=(200, 200)):
            container_id = dpg.last_item()
            dpg.add_text("RFM Architecture Visualizer", parent=container_id)
            dpg.add_text("Version 0.1.0", parent=container_id)
            dpg.add_separator(parent=container_id)
            dpg.add_text("A visualization tool for Recursive Fractal Mind Architecture", parent=container_id)
            
            # Use accent button for the OK button
            AccentButton(
                parent_id=container_id,
                label="OK",
                callback=lambda: dpg.delete_item(container_id),
                width=100
            )
            
    @error_boundary
    def _on_documentation(self, sender=None, app_data=None) -> None:
        """Handle documentation menu item."""
        # Show documentation dialog using premium components
        with dpg.window(label="Documentation", modal=True, width=500, height=300, pos=(200, 200)):
            container_id = dpg.last_item()
            dpg.add_text("RFM Architecture Visualizer Documentation", parent=container_id)
            dpg.add_separator(parent=container_id)
            dpg.add_text("Please see the docs/ directory for complete documentation.", parent=container_id)
            
            # Use accent button for the OK button
            AccentButton(
                parent_id=container_id,
                label="OK",
                callback=lambda: dpg.delete_item(container_id),
                width=100
            )
            
    @error_boundary
    def _on_load_preset(self, sender=None, app_data=None) -> None:
        """Handle load preset button."""
        # Get selected preset
        if not dpg.does_alias_exist("preset_listbox"):
            return
            
        preset_name = dpg.get_value("preset_listbox")
        if not preset_name:
            return
            
        # Load preset parameters
        if preset_name == "Default":
            self._on_reset()
        elif preset_name == "Zoomed Mandelbrot":
            # Set fractal type
            dpg.set_value("fractal_type_combo", "Mandelbrot")
            self._on_fractal_type_changed(None, "Mandelbrot")
            
            # Set parameters (using premium sliders if available)
            if "center_x" in self.sliders:
                self.sliders["center_x"].set_value(-0.743643887037151)
                self.sliders["center_y"].set_value(0.131825904205330)
                self.sliders["zoom"].set_value(4000.0)
                self.sliders["max_iter"].set_value(500)
            else:
                dpg.set_value("center_x_input", -0.743643887037151)
                dpg.set_value("center_y_input", 0.131825904205330)
                dpg.set_value("zoom_slider", 4000.0)
                dpg.set_value("max_iter_slider", 500)
            
        elif preset_name == "Julia Swirl":
            # Set fractal type
            dpg.set_value("fractal_type_combo", "Julia")
            self._on_fractal_type_changed(None, "Julia")
            
            # Set parameters (using premium sliders if available)
            if "c_real" in self.sliders:
                self.sliders["c_real"].set_value(-0.8)
                self.sliders["c_imag"].set_value(0.156)
                self.sliders["center_x"].set_value(0.0)
                self.sliders["center_y"].set_value(0.0)
                self.sliders["zoom"].set_value(1.5)
                self.sliders["max_iter"].set_value(300)
            else:
                dpg.set_value("c_real_input", -0.8)
                dpg.set_value("c_imag_input", 0.156)
                dpg.set_value("center_x_input", 0.0)
                dpg.set_value("center_y_input", 0.0)
                dpg.set_value("zoom_slider", 1.5)
                dpg.set_value("max_iter_slider", 300)
                
            dpg.set_value("julia_preset_combo", "Custom")
            
        elif preset_name == "Dendrite":
            # Set fractal type
            dpg.set_value("fractal_type_combo", "Julia")
            self._on_fractal_type_changed(None, "Julia")
            
            # Set preset directly
            dpg.set_value("julia_preset_combo", "Dendrite")
            
        # Update parameters
        self._build_params_from_ui()
        
        # Trigger render
        self._queue_render()
        
    @error_boundary
    def _on_save_preset(self, sender=None, app_data=None) -> None:
        """Handle save preset button."""
        # Show save preset dialog using premium components
        with dpg.window(label="Save Preset", modal=True, width=400, height=200, pos=(200, 200)):
            container_id = dpg.last_item()
            dpg.add_text("Enter preset name:", parent=container_id)
            dpg.add_input_text(tag="preset_name_input", width=-1, parent=container_id)
            
            # Add option to create shareable link
            dpg.add_checkbox(
                label="Create shareable link",
                default_value=True,
                tag="create_share_link_checkbox",
                parent=container_id
            )
            
            with dpg.group(horizontal=True, parent=container_id):
                group_id = dpg.last_item()
                
                # Save button
                AccentButton(
                    parent_id=group_id,
                    label="Save",
                    callback=self._save_preset,
                    user_data=container_id,
                    width=100
                )
                
                # Cancel button
                SecondaryButton(
                    parent_id=group_id,
                    label="Cancel",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=container_id,
                    width=100
                )
                
    @error_boundary
    def _save_preset(self, sender, app_data, user_data) -> None:
        """
        Save a preset with the current parameters.
        
        Args:
            sender: Sender widget ID
            app_data: New value
            user_data: User data (dialog window ID)
        """
        preset_name = dpg.get_value("preset_name_input")
        if not preset_name:
            return
            
        # In a real application, we would save the preset to a file
        # For now, just add it to the preset list
        if dpg.does_alias_exist("preset_listbox"):
            items = dpg.get_item_configuration("preset_listbox")["items"]
            items.append(preset_name)
            dpg.configure_item("preset_listbox", items=items)
        
        # Check if share link should be created
        create_share_link = dpg.get_value("create_share_link_checkbox")
        if create_share_link:
            try:
                # Import share module
                from rfm_ui.utils.share import encode_preset
                
                # Create share link
                share_link = encode_preset(self.current_params)
                
                # Show share link dialog
                self._show_share_link_dialog(preset_name, share_link)
            except ImportError as e:
                self.logger.error(f"Failed to import share module: {e}")
                # Show error message
                with dpg.window(label="Error", modal=True, width=300, height=150, pos=(250, 250)):
                    error_container = dpg.last_item()
                    dpg.add_text("Failed to create share link:", parent=error_container)
                    dpg.add_text(str(e), parent=error_container)
                    
                    # OK button
                    AccentButton(
                        parent_id=error_container,
                        label="OK",
                        callback=lambda s, a, u: dpg.delete_item(u),
                        user_data=error_container,
                        width=100
                    )
                    
        # Close the dialog
        dpg.delete_item(user_data)
        
    @error_boundary
    def _show_share_link_dialog(self, preset_name: str, share_link: str) -> None:
        """
        Show dialog with shareable link.
        
        Args:
            preset_name: Name of the preset
            share_link: Encoded share link
        """
        # Create dialog
        with dpg.window(label=f"Share Link: {preset_name}", modal=True, width=500, height=200, pos=(200, 200)):
            container_id = dpg.last_item()
            
            dpg.add_text("Copy this link to share your preset:", parent=container_id)
            
            # Add link text with scroll area
            with dpg.child_window(width=-1, height=80, parent=container_id):
                dpg.add_input_text(
                    default_value=share_link,
                    width=-1,
                    height=-1,
                    multiline=True,
                    readonly=True,
                    tag="share_link_text"
                )
            
            # Add copy button
            with dpg.group(horizontal=True, parent=container_id):
                group_id = dpg.last_item()
                
                # Copy button
                AccentButton(
                    parent_id=group_id,
                    label="Copy to Clipboard",
                    callback=self._copy_share_link_to_clipboard,
                    width=150
                )
                
                # Close button
                SecondaryButton(
                    parent_id=group_id,
                    label="Close",
                    callback=lambda s, a, u: dpg.delete_item(container_id),
                    width=100
                )
                
    @error_boundary
    def _copy_share_link_to_clipboard(self, sender, app_data) -> None:
        """Copy share link to clipboard."""
        # Get share link
        share_link = dpg.get_value("share_link_text")
        
        try:
            # Try to import pyperclip
            import pyperclip
            pyperclip.copy(share_link)
            
            # Show success message
            with dpg.window(label="Success", modal=True, width=250, height=100, pos=(300, 300)):
                success_container = dpg.last_item()
                dpg.add_text("Link copied to clipboard!", parent=success_container)
                
                # OK button
                AccentButton(
                    parent_id=success_container,
                    label="OK",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=success_container,
                    width=100
                )
                
        except ImportError:
            # Show error message
            with dpg.window(label="Error", modal=True, width=300, height=150, pos=(300, 300)):
                error_container = dpg.last_item()
                dpg.add_text("Failed to copy to clipboard:", parent=error_container)
                dpg.add_text("pyperclip module not available", parent=error_container)
                
                # OK button
                AccentButton(
                    parent_id=error_container,
                    label="OK",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=error_container,
                    width=100
                )
        
    @error_boundary
    def _on_preset_selected(self, sender, app_data) -> None:
        """
        Handle preset selection.
        
        Args:
            sender: Sender widget ID
            app_data: New value
        """
        # Do nothing here, presets are loaded when the Load Preset button is clicked
        pass
        
    def _queue_render(self) -> None:
        """Queue a render operation."""
        if self.render_queue is None:
            return
            
        # Put parameters in the queue for rendering
        asyncio.run_coroutine_threadsafe(
            self.render_queue.put(self.current_params.copy()),
            asyncio.get_event_loop()
        )
        
    def _start_render_task(self) -> None:
        """Start the render task in the background."""
        self.render_queue = asyncio.Queue()
        
        async def render_task():
            while dpg.is_dearpygui_running():
                try:
                    # Get parameters from queue, waiting at most 100ms
                    try:
                        params = await asyncio.wait_for(self.render_queue.get(), 0.1)
                    except asyncio.TimeoutError:
                        # No new parameters, continue
                        await asyncio.sleep(0.01)
                        continue
                        
                    # Render the fractal
                    await self._render_fractal(params)
                    
                    # Mark task as done
                    self.render_queue.task_done()
                    
                except asyncio.CancelledError:
                    # Task was cancelled
                    break
                except Exception as e:
                    # Handle error
                    self.error_handler.handle_error(e)
                    await asyncio.sleep(0.1)
                    
        # Create and start the task
        self.render_task = asyncio.create_task(render_task())
        
    async def _render_fractal(self, params: Dict[str, Any]) -> None:
        """
        Render a fractal with the given parameters.
        
        Args:
            params: Parameters for rendering
        """
        # Skip if already rendering
        if self.is_rendering:
            return
            
        self.is_rendering = True
        
        try:
            # Start performance tracking
            perf_ctx = self.performance_tracker.start_operation(
                "render_fractal", 
                {"type": params.get("type", "mandelbrot")}
            )
            
            start_time = time.time()
            
            # Render the fractal
            with error_context("render_fractal", params):
                # Get render dimensions
                width = params.get("width", self.render_width)
                height = params.get("height", self.render_height)
                
                # Render using the engine
                rgba_array = await asyncio.to_thread(
                    self.engine.render, 
                    params
                )
                
                # Check if render was successful
                if rgba_array is None or rgba_array.size == 0:
                    raise UIError(
                        message="Fractal rendering failed",
                        component="fractal_renderer",
                        remediation="Try different parameters or restart the application"
                    )
                    
                # Update texture
                dpg.set_value("fractal_texture", rgba_array)
                
                # Update render time
                self.render_time = (time.time() - start_time) * 1000
                dpg.set_value("render_time_text", f"{self.render_time:.2f} ms")
                
                # Update FPS
                now = time.time()
                self.frame_times.append(now)
                
                # Keep only the last 20 frames
                if len(self.frame_times) > 20:
                    self.frame_times.pop(0)
                    
                if len(self.frame_times) > 1:
                    # Calculate FPS from frame times
                    fps = (len(self.frame_times) - 1) / (self.frame_times[-1] - self.frame_times[0])
                    self.fps = fps
                    dpg.set_value("fps_text", f"{fps:.1f}")
                    
                # Update FPS overlay
                if self.fps_overlay:
                    self.fps_overlay.set_render_time(self.render_time)
        finally:
            # End performance tracking
            if 'perf_ctx' in locals():
                self.performance_tracker.end_operation(perf_ctx)
                
            self.is_rendering = False
            
            # Reset texture if render failed
            if 'rgba_array' not in locals() or rgba_array is None:
                dpg.set_value(
                    "fractal_texture", 
                    np.zeros((self.render_height, self.render_width, 4), dtype=np.float32)
                )
        
    def _cleanup(self) -> None:
        """Clean up resources before exit."""
        # Cancel render task
        if self.render_task:
            self.render_task.cancel()
            
        # Close any open dialogs
        if self.error_dialog and self.error_dialog.is_showing:
            self.error_dialog._on_close()
            
        # Save performance data
        if self.performance_tracker:
            self.performance_tracker.set_current_as_baseline()
            
    def run(self) -> int:
        """
        Run the application.
        
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            if not dpg.is_dearpygui_running():
                dpg.start_dearpygui()
                
            while dpg.is_dearpygui_running():
                # Sleep to avoid high CPU usage
                time.sleep(0.01)
                
            return 0
        except Exception as e:
            self.logger.error(f"Error running application: {e}", exc_info=True)
            self.error_handler.handle_error(e)
            return 1
        finally:
            # Clean up
            self._cleanup()
            
            # Destroy DPG context
            if dpg.is_dearpygui_running():
                dpg.stop_dearpygui()
                
            if dpg.does_context_exist():
                dpg.destroy_context()