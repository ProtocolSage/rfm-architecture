"""
Core fractal rendering engine for RFM Architecture UI.

This module provides the core fractal rendering capabilities for the
RFM Architecture visualization.
"""

import time
import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple, Union, List, Set
from enum import Enum

from rfm_ui.errors import (
    error_boundary, error_context, validate_params, 
    FractalError, RenderError, ParameterError, 
    MandelbrotError, JuliaError, LSystemError, CantorError
)
from rfm_ui.performance import get_performance_tracker

# Import progress reporting modules
import asyncio
import uuid
from rfm_ui.websocket_client import get_websocket_client, WebSocketClient
from rfm.core.progress import ProgressReporter, get_progress_manager

logger = logging.getLogger(__name__)


# Define parameter schemas for validation
MANDELBROT_PARAMS_SCHEMA = {
    "center_x": {"type": (int, float), "required": False, "default": -0.5},
    "center_y": {"type": (int, float), "required": False, "default": 0.0},
    "zoom": {"type": (int, float), "required": False, "default": 1.0, "range": [0.000001, 1e12]},
    "max_iter": {"type": int, "required": False, "default": 100, "range": [10, 10000]},
    "width": {"type": int, "required": False, "default": 800, "range": [1, 10000]},
    "height": {"type": int, "required": False, "default": 600, "range": [1, 10000]},
    "colormap": {"type": str, "required": False, "default": "viridis", 
                "range": ["viridis", "plasma", "inferno", "magma", "cividis", "turbo"]},
    "high_quality": {"type": bool, "required": False, "default": True}
}

JULIA_PARAMS_SCHEMA = {
    "c_real": {"type": (int, float), "required": False, "default": -0.7},
    "c_imag": {"type": (int, float), "required": False, "default": 0.27},
    "center_x": {"type": (int, float), "required": False, "default": 0.0},
    "center_y": {"type": (int, float), "required": False, "default": 0.0},
    "zoom": {"type": (int, float), "required": False, "default": 1.5, "range": [0.000001, 1e12]},
    "max_iter": {"type": int, "required": False, "default": 100, "range": [10, 10000]},
    "width": {"type": int, "required": False, "default": 800, "range": [1, 10000]},
    "height": {"type": int, "required": False, "default": 600, "range": [1, 10000]},
    "colormap": {"type": str, "required": False, "default": "viridis", 
                "range": ["viridis", "plasma", "inferno", "magma", "cividis", "turbo"]},
    "high_quality": {"type": bool, "required": False, "default": True}
}

LSYSTEM_PARAMS_SCHEMA = {
    "axiom": {"type": str, "required": False, "default": "F"},
    "rules": {"type": dict, "required": False, "default": {"F": "F+F-F-F+F"}},
    "angle": {"type": (int, float), "required": False, "default": 90.0, "range": [0.0, 360.0]},
    "iterations": {"type": int, "required": False, "default": 4, "range": [1, 10]},
    "line_width": {"type": (int, float), "required": False, "default": 1.0, "range": [0.1, 10.0]},
    "color": {"type": str, "required": False, "default": "#b086ff"},
    "alpha": {"type": (int, float), "required": False, "default": 0.8, "range": [0.0, 1.0]},
    "width": {"type": int, "required": False, "default": 800, "range": [1, 10000]},
    "height": {"type": int, "required": False, "default": 600, "range": [1, 10000]},
}

CANTOR_PARAMS_SCHEMA = {
    "gap_ratio": {"type": (int, float), "required": False, "default": 0.3, "range": [0.1, 0.9]},
    "iterations": {"type": int, "required": False, "default": 4, "range": [1, 10]},
    "color": {"type": str, "required": False, "default": "#b086ff"},
    "alpha": {"type": (int, float), "required": False, "default": 0.8, "range": [0.0, 1.0]},
    "width": {"type": int, "required": False, "default": 800, "range": [1, 10000]},
    "height": {"type": int, "required": False, "default": 600, "range": [1, 10000]},
}


class ColorMapper:
    """Maps fractal iteration values to colors."""
    
    COLORMAPS = {
        "viridis": [
            (0.267004, 0.004874, 0.329415),
            (0.275191, 0.194905, 0.496005),
            (0.212395, 0.359683, 0.551710),
            (0.153364, 0.497000, 0.557724),
            (0.122312, 0.633153, 0.530398),
            (0.288921, 0.758394, 0.428426),
            (0.626579, 0.854645, 0.223353),
            (0.993248, 0.906157, 0.143936)
        ],
        "plasma": [
            (0.050383, 0.029803, 0.527975),
            (0.282623, 0.011569, 0.627943),
            (0.494943, 0.010313, 0.650430),
            (0.679386, 0.050959, 0.579665),
            (0.826782, 0.149214, 0.453647),
            (0.938793, 0.266241, 0.325190),
            (0.989830, 0.413328, 0.187932),
            (0.964278, 0.676080, 0.064386)
        ],
        "inferno": [
            (0.001462, 0.000466, 0.013866),
            (0.126204, 0.020775, 0.158400),
            (0.329283, 0.028694, 0.245365),
            (0.534242, 0.056225, 0.241961),
            (0.730058, 0.129412, 0.177335),
            (0.881260, 0.237000, 0.088535),
            (0.973718, 0.407057, 0.032864),
            (0.987053, 0.790532, 0.346471)
        ],
        "magma": [
            (0.001462, 0.000466, 0.013866),
            (0.128010, 0.044595, 0.169168),
            (0.331176, 0.076701, 0.274708),
            (0.547974, 0.100702, 0.309737),
            (0.751269, 0.145705, 0.264944),
            (0.914296, 0.235996, 0.164692),
            (0.989516, 0.383381, 0.116486),
            (0.974795, 0.713132, 0.480794)
        ],
        "cividis": [
            (0.000000, 0.135112, 0.304751),
            (0.072474, 0.214181, 0.362957),
            (0.143547, 0.281100, 0.394187),
            (0.232695, 0.341243, 0.392153),
            (0.341860, 0.389907, 0.367359),
            (0.481176, 0.429699, 0.317669),
            (0.632470, 0.473063, 0.252608),
            (0.825971, 0.528596, 0.134729)
        ],
        "turbo": [
            (0.188235, 0.149020, 0.631373),
            (0.027451, 0.450980, 0.756863),
            (0.015686, 0.658824, 0.588235),
            (0.133333, 0.839216, 0.356863),
            (0.470588, 0.941176, 0.094118),
            (0.784314, 0.890196, 0.058824),
            (0.996078, 0.670588, 0.109804),
            (0.996078, 0.333333, 0.274510)
        ]
    }
    
    @staticmethod
    def get_colormap(name: str) -> List[Tuple[float, float, float]]:
        """
        Get a colormap by name.
        
        Args:
            name: Name of the colormap
            
        Returns:
            List of RGB color tuples
            
        Raises:
            ValueError: If the colormap name is invalid
        """
        if name not in ColorMapper.COLORMAPS:
            # Return default colormap
            return ColorMapper.COLORMAPS["viridis"]
            
        return ColorMapper.COLORMAPS[name]
        
    @staticmethod
    def apply_colormap(iterations: np.ndarray, 
                      max_iter: int,
                      cmap_name: str = "viridis") -> np.ndarray:
        """
        Apply a colormap to iteration values.
        
        Args:
            iterations: Array of iteration values
            max_iter: Maximum number of iterations
            cmap_name: Name of the colormap to use
            
        Returns:
            Array of RGBA values
        """
        # Get colormap
        colormap = ColorMapper.get_colormap(cmap_name)
        
        # Normalize iterations
        normalized = np.where(iterations < max_iter, iterations / max_iter, 0)
        
        # Create rgba array
        height, width = iterations.shape
        rgba = np.zeros((height, width, 4), dtype=np.float32)
        
        # Apply colormap
        for i in range(height):
            for j in range(width):
                if iterations[i, j] >= max_iter:
                    # Black for points in the set
                    rgba[i, j] = [0, 0, 0, 1]
                else:
                    # Get color from colormap
                    t = normalized[i, j]
                    idx = int(t * (len(colormap) - 1))
                    frac = t * (len(colormap) - 1) - idx
                    
                    if idx < len(colormap) - 1:
                        # Interpolate between colors
                        c1 = colormap[idx]
                        c2 = colormap[idx + 1]
                        
                        r = c1[0] * (1 - frac) + c2[0] * frac
                        g = c1[1] * (1 - frac) + c2[1] * frac
                        b = c1[2] * (1 - frac) + c2[2] * frac
                        
                        rgba[i, j] = [r, g, b, 1]
                    else:
                        # Use last color
                        rgba[i, j] = [*colormap[-1], 1]
        
        return rgba


class FractalEngine:
    """Core engine for rendering fractals."""
    
    def __init__(self, enable_progress_reporting: bool = True, websocket_url: str = "ws://localhost:8765"):
        """
        Initialize the fractal engine.
        
        Args:
            enable_progress_reporting: Whether to enable progress reporting
            websocket_url: WebSocket server URL for progress reporting
        """
        self.logger = logging.getLogger("fractal_engine")
        self.performance_tracker = get_performance_tracker()
        self.enable_progress_reporting = enable_progress_reporting
        self.websocket_url = websocket_url
        self.websocket_client = None
        
        # Initialize WebSocket client if progress reporting is enabled
        if self.enable_progress_reporting:
            self.websocket_client = get_websocket_client(self.websocket_url)
            
            # Start WebSocket client if it's not already running
            if self.websocket_client and not self.websocket_client.is_connected():
                self.websocket_client.start()
                
    def _create_progress_reporter(self, fractal_type: str, params: Dict[str, Any]) -> Optional[ProgressReporter]:
        """
        Create a progress reporter for tracking rendering progress.
        
        Args:
            fractal_type: Type of fractal being rendered
            params: Rendering parameters
            
        Returns:
            ProgressReporter instance, or None if progress reporting is disabled
        """
        if not self.enable_progress_reporting:
            return None
            
        # Create operation ID and name
        operation_id = str(uuid.uuid4())
        
        # Create operation name based on fractal type
        if fractal_type == "mandelbrot":
            center_x = params.get("center_x", -0.5)
            center_y = params.get("center_y", 0.0)
            zoom = params.get("zoom", 1.0)
            name = f"Mandelbrot Set ({center_x:.2f}, {center_y:.2f}, zoom {zoom:.2f})"
        elif fractal_type == "julia":
            c_real = params.get("c_real", -0.7)
            c_imag = params.get("c_imag", 0.27)
            name = f"Julia Set (c={c_real:.2f}+{c_imag:.2f}i)"
        elif fractal_type == "l_system":
            iterations = params.get("iterations", 4)
            name = f"L-System (iterations={iterations})"
        elif fractal_type == "cantor dust":
            iterations = params.get("iterations", 4)
            name = f"Cantor Dust (iterations={iterations})"
        else:
            name = f"Fractal Rendering ({fractal_type})"
            
        # Create progress reporter
        reporter = ProgressReporter(f"fractal_render_{fractal_type}", name)
        
        # Connect reporter to WebSocket server
        try:
            # Start progress manager if not already running
            progress_manager = get_progress_manager()
            
            # Add reporter to progress manager using run_coroutine_threadsafe
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    progress_manager.add_operation(reporter),
                    loop
                )
            else:
                asyncio.run(progress_manager.add_operation(reporter))
        except Exception as e:
            self.logger.error(f"Error registering progress reporter: {e}")
            
        return reporter
        
    @error_boundary(reraise=True)
    def render(self, params: Dict[str, Any]) -> np.ndarray:
        """
        Render a fractal with the given parameters.
        
        Args:
            params: Parameters for rendering
            
        Returns:
            RGBA array of the rendered fractal
            
        Raises:
            RenderError: If rendering fails
        """
        # Record rendering performance
        perf_ctx = self.performance_tracker.start_operation(
            "render_fractal_engine", params
        )
        
        try:
            # Get fractal type
            fractal_type = params.get("type", "mandelbrot").lower()
            
            # Create progress reporter
            progress_reporter = self._create_progress_reporter(fractal_type, params)
            
            # Validate parameters
            self._validate_params(fractal_type, params)
            
            # Apply defaults
            params = self._apply_defaults(fractal_type, params)
            
            # Render based on fractal type
            with error_context(f"render_{fractal_type}", params):
                if fractal_type == "mandelbrot":
                    return self._render_mandelbrot(params, progress_reporter)
                elif fractal_type == "julia":
                    return self._render_julia(params, progress_reporter)
                elif fractal_type == "l_system":
                    return self._render_l_system(params, progress_reporter)
                elif fractal_type == "cantor dust":
                    return self._render_cantor_dust(params, progress_reporter)
                else:
                    if progress_reporter:
                        progress_reporter.report_failed(f"Unknown fractal type: {fractal_type}")
                        
                    raise RenderError(
                        message=f"Unknown fractal type: {fractal_type}",
                        fractal_type=fractal_type,
                        params=params,
                        remediation="Choose one of: mandelbrot, julia, l_system, cantor dust"
                    )
        except Exception as e:
            # Report failure to progress reporter
            if 'progress_reporter' in locals() and progress_reporter:
                progress_reporter.report_failed(str(e))
                
            # Re-raise the exception
            raise
        finally:
            # End performance tracking
            self.performance_tracker.end_operation(perf_ctx)
    
    def _validate_params(self, fractal_type: str, params: Dict[str, Any]) -> None:
        """
        Validate parameters for a fractal.
        
        Args:
            fractal_type: Type of fractal
            params: Parameters to validate
            
        Raises:
            ParameterError: If parameters are invalid
        """
        # Select schema based on fractal type
        if fractal_type == "mandelbrot":
            schema = MANDELBROT_PARAMS_SCHEMA
        elif fractal_type == "julia":
            schema = JULIA_PARAMS_SCHEMA
        elif fractal_type == "l_system":
            schema = LSYSTEM_PARAMS_SCHEMA
        elif fractal_type == "cantor dust":
            schema = CANTOR_PARAMS_SCHEMA
        else:
            # No schema for unknown fractal type
            return
            
        # Validate parameters
        validate_params(params, schema)
    
    def _apply_defaults(self, fractal_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply default values for missing parameters.
        
        Args:
            fractal_type: Type of fractal
            params: Parameters to apply defaults to
            
        Returns:
            Parameters with defaults applied
        """
        # Select schema based on fractal type
        if fractal_type == "mandelbrot":
            schema = MANDELBROT_PARAMS_SCHEMA
        elif fractal_type == "julia":
            schema = JULIA_PARAMS_SCHEMA
        elif fractal_type == "l_system":
            schema = LSYSTEM_PARAMS_SCHEMA
        elif fractal_type == "cantor dust":
            schema = CANTOR_PARAMS_SCHEMA
        else:
            # No schema for unknown fractal type
            return params
            
        # Create copy of parameters
        result = params.copy()
        
        # Apply defaults
        for name, constraints in schema.items():
            if name not in result and "default" in constraints:
                result[name] = constraints["default"]
                
        return result
    
    @error_boundary(reraise=True)
    def _render_mandelbrot(self, params: Dict[str, Any], 
                          progress_reporter: Optional[ProgressReporter] = None) -> np.ndarray:
        """
        Render a Mandelbrot set fractal.
        
        Args:
            params: Parameters for rendering
            progress_reporter: Optional progress reporter
            
        Returns:
            RGBA array of the rendered fractal
            
        Raises:
            MandelbrotError: If rendering fails
        """
        try:
            # Check if GPU backend is available
            from rfm.gpu_backend import mandelbrot as gpu_mandelbrot
            
            # Record GPU-based rendering performance
            perf_ctx = self.performance_tracker.start_operation(
                "render_mandelbrot_gpu", params
            )
            
            try:
                # Report initial progress
                if progress_reporter:
                    progress_reporter.report_progress(
                        0,
                        current_step="Initializing GPU-accelerated Mandelbrot rendering",
                        details={"backend": "gpu"}
                    )
                
                # Use GPU-accelerated rendering
                iterations = gpu_mandelbrot(params, progress_reporter)
                
                # Extract parameters for colormap
                max_iter = params.get("max_iter", 100)
                cmap = params.get("colormap", "viridis")
                
                # Report progress
                if progress_reporter:
                    progress_reporter.report_progress(
                        90,
                        current_step="Applying colormap to Mandelbrot set",
                        current_step_progress=0
                    )
                
                # Apply colormap
                rgba = ColorMapper.apply_colormap(iterations, max_iter, cmap)
                
                # Report completion
                if progress_reporter:
                    progress_reporter.report_completed()
                
                return rgba
            finally:
                self.performance_tracker.end_operation(perf_ctx)
                
        except ImportError:
            # GPU backend not available, use CPU fallback
            self.logger.warning("GPU backend not available, using CPU fallback")
            
            # Extract parameters
            width = params.get("width", 800)
            height = params.get("height", 600)
            center_x = params.get("center_x", -0.5)
            center_y = params.get("center_y", 0.0)
            zoom = params.get("zoom", 1.0)
            max_iter = params.get("max_iter", 100)
            cmap = params.get("colormap", "viridis")
            high_quality = params.get("high_quality", True)
            
            # Report initial progress
            if progress_reporter:
                progress_reporter.report_progress(
                    0,
                    current_step="Initializing CPU-based Mandelbrot rendering",
                    details={
                        "backend": "cpu",
                        "width": width,
                        "height": height,
                        "center": [center_x, center_y],
                        "zoom": zoom,
                        "max_iter": max_iter
                    }
                )
            
            # Calculate aspect ratio
            aspect_ratio = width / height
            
            # Calculate bounds
            x_range = 4.0 / zoom
            y_range = x_range / aspect_ratio
            
            x_min = center_x - x_range / 2
            x_max = center_x + x_range / 2
            y_min = center_y - y_range / 2
            y_max = center_y + y_range / 2
            
            # Report parameter setup complete
            if progress_reporter:
                progress_reporter.report_progress(
                    5,
                    current_step="Setting up Mandelbrot calculation",
                    current_step_progress=100
                )
            
            # Setup for vectorized calculation
            x = np.linspace(x_min, x_max, width)
            y = np.linspace(y_min, y_max, height)
            
            # Create complex coordinate grid
            X, Y = np.meshgrid(x, y)
            c = X + 1j * Y
            z = np.zeros_like(c)
            
            # Allocate iterations array
            iterations = np.zeros((height, width), dtype=np.float32)
            
            # Track points that have escaped
            escaped = np.zeros((height, width), dtype=bool)
            
            # Report start of calculation
            if progress_reporter:
                progress_reporter.report_progress(
                    10,
                    current_step="Beginning Mandelbrot iteration calculation",
                    current_step_progress=0,
                    total_steps=max_iter
                )
            
            # Vectorized Mandelbrot calculation
            for i in range(max_iter):
                # Update points that haven't escaped yet
                mask = ~escaped
                z[mask] = z[mask] * z[mask] + c[mask]
                
                # Mark points that have escaped
                new_escaped = mask & (np.abs(z) > 2)
                escaped = escaped | new_escaped
                
                # Record iteration count for newly escaped points
                iterations[new_escaped] = i + 1 - np.log(np.log(abs(z[new_escaped]))) / np.log(2)
                
                # Report progress at intervals
                if progress_reporter and i % max(1, max_iter // 50) == 0:
                    progress = 10 + (i / max_iter) * 80  # 10-90% for computation
                    remaining_points = np.sum(mask)
                    total_points = width * height
                    escaped_points = total_points - remaining_points
                    
                    progress_reporter.report_progress(
                        progress,
                        current_step=f"Computing Mandelbrot iteration {i+1}/{max_iter}",
                        total_steps=max_iter,
                        current_step_progress=(i + 1) / max_iter * 100,
                        details={
                            "escaped_points": int(escaped_points),
                            "remaining_points": int(remaining_points)
                        }
                    )
                
                # Check for cancellation
                if progress_reporter and progress_reporter.should_cancel():
                    progress_reporter.report_canceled()
                    # Return a simple gradient for canceled renders
                    gradient = np.zeros((height, width, 4), dtype=np.float32)
                    x_norm = np.linspace(0, 1, width)
                    y_norm = np.linspace(0, 1, height)
                    X_norm, Y_norm = np.meshgrid(x_norm, y_norm)
                    gradient[:, :, 0] = X_norm
                    gradient[:, :, 1] = Y_norm
                    gradient[:, :, 2] = 0.5
                    gradient[:, :, 3] = 0.5  # Semi-transparent to indicate cancellation
                    return gradient
                
                # Stop if all points have escaped
                if np.all(escaped):
                    break
                    
            # Report colormap application
            if progress_reporter:
                progress_reporter.report_progress(
                    90,
                    current_step="Applying colormap to Mandelbrot set",
                    current_step_progress=0
                )
            
            # Apply colormap
            rgba = ColorMapper.apply_colormap(iterations, max_iter, cmap)
            
            # Report completion
            if progress_reporter:
                progress_reporter.report_completed(
                    details={
                        "width": width,
                        "height": height,
                        "iterations": int(np.mean(iterations))
                    }
                )
            
            return rgba
    
    @error_boundary(reraise=True)
    def _render_julia(self, params: Dict[str, Any], 
                     progress_reporter: Optional[ProgressReporter] = None) -> np.ndarray:
        """
        Render a Julia set fractal.
        
        Args:
            params: Parameters for rendering
            progress_reporter: Optional progress reporter
            
        Returns:
            RGBA array of the rendered fractal
            
        Raises:
            JuliaError: If rendering fails
        """
        try:
            # Check if GPU backend is available
            from rfm.gpu_backend import julia as gpu_julia
            
            # Record GPU-based rendering performance
            perf_ctx = self.performance_tracker.start_operation(
                "render_julia_gpu", params
            )
            
            try:
                # Report initial progress
                if progress_reporter:
                    progress_reporter.report_progress(
                        0,
                        current_step="Initializing GPU-accelerated Julia rendering",
                        details={"backend": "gpu"}
                    )
                
                # Use GPU-accelerated rendering
                iterations = gpu_julia(params, progress_reporter)
                
                # Extract parameters for colormap
                max_iter = params.get("max_iter", 100)
                cmap = params.get("colormap", "viridis")
                
                # Report progress
                if progress_reporter:
                    progress_reporter.report_progress(
                        90,
                        current_step="Applying colormap to Julia set",
                        current_step_progress=0
                    )
                
                # Apply colormap
                rgba = ColorMapper.apply_colormap(iterations, max_iter, cmap)
                
                # Report completion
                if progress_reporter:
                    progress_reporter.report_completed()
                
                return rgba
            finally:
                self.performance_tracker.end_operation(perf_ctx)
                
        except ImportError:
            # GPU backend not available, use CPU fallback
            self.logger.warning("GPU backend not available, using CPU fallback")
            
            # Extract parameters
            width = params.get("width", 800)
            height = params.get("height", 600)
            c_real = params.get("c_real", -0.7)
            c_imag = params.get("c_imag", 0.27)
            center_x = params.get("center_x", 0.0)
            center_y = params.get("center_y", 0.0)
            zoom = params.get("zoom", 1.5)
            max_iter = params.get("max_iter", 100)
            cmap = params.get("colormap", "viridis")
            high_quality = params.get("high_quality", True)
            
            # Report initial progress
            if progress_reporter:
                progress_reporter.report_progress(
                    0,
                    current_step="Initializing CPU-based Julia rendering",
                    details={
                        "backend": "cpu",
                        "width": width,
                        "height": height,
                        "c_value": f"{c_real}+{c_imag}j",
                        "center": [center_x, center_y],
                        "zoom": zoom,
                        "max_iter": max_iter
                    }
                )
            
            # Create complex parameter
            c = complex(c_real, c_imag)
            
            # Calculate aspect ratio
            aspect_ratio = width / height
            
            # Calculate bounds
            x_range = 4.0 / zoom
            y_range = x_range / aspect_ratio
            
            x_min = center_x - x_range / 2
            x_max = center_x + x_range / 2
            y_min = center_y - y_range / 2
            y_max = center_y + y_range / 2
            
            # Report parameter setup complete
            if progress_reporter:
                progress_reporter.report_progress(
                    5,
                    current_step="Setting up Julia calculation",
                    current_step_progress=100
                )
            
            # Setup for vectorized calculation
            x = np.linspace(x_min, x_max, width)
            y = np.linspace(y_min, y_max, height)
            
            # Create complex coordinate grid
            X, Y = np.meshgrid(x, y)
            z = X + 1j * Y
            
            # Allocate iterations array
            iterations = np.zeros((height, width), dtype=np.float32)
            
            # Track points that have escaped
            escaped = np.zeros((height, width), dtype=bool)
            
            # Report start of calculation
            if progress_reporter:
                progress_reporter.report_progress(
                    10,
                    current_step="Beginning Julia iteration calculation",
                    current_step_progress=0,
                    total_steps=max_iter
                )
            
            # Vectorized Julia calculation
            for i in range(max_iter):
                # Update points that haven't escaped yet
                mask = ~escaped
                z[mask] = z[mask] * z[mask] + c
                
                # Mark points that have escaped
                new_escaped = mask & (np.abs(z) > 2)
                escaped = escaped | new_escaped
                
                # Record iteration count for newly escaped points
                iterations[new_escaped] = i + 1 - np.log(np.log(abs(z[new_escaped]))) / np.log(2)
                
                # Report progress at intervals
                if progress_reporter and i % max(1, max_iter // 50) == 0:
                    progress = 10 + (i / max_iter) * 80  # 10-90% for computation
                    remaining_points = np.sum(mask)
                    total_points = width * height
                    escaped_points = total_points - remaining_points
                    
                    progress_reporter.report_progress(
                        progress,
                        current_step=f"Computing Julia iteration {i+1}/{max_iter}",
                        total_steps=max_iter,
                        current_step_progress=(i + 1) / max_iter * 100,
                        details={
                            "escaped_points": int(escaped_points),
                            "remaining_points": int(remaining_points)
                        }
                    )
                
                # Check for cancellation
                if progress_reporter and progress_reporter.should_cancel():
                    progress_reporter.report_canceled()
                    # Return a simple gradient for canceled renders
                    gradient = np.zeros((height, width, 4), dtype=np.float32)
                    x_norm = np.linspace(0, 1, width)
                    y_norm = np.linspace(0, 1, height)
                    X_norm, Y_norm = np.meshgrid(x_norm, y_norm)
                    gradient[:, :, 0] = X_norm
                    gradient[:, :, 1] = 0.5
                    gradient[:, :, 2] = Y_norm
                    gradient[:, :, 3] = 0.5  # Semi-transparent to indicate cancellation
                    return gradient
                
                # Stop if all points have escaped
                if np.all(escaped):
                    break
                    
            # Report colormap application
            if progress_reporter:
                progress_reporter.report_progress(
                    90,
                    current_step="Applying colormap to Julia set",
                    current_step_progress=0
                )
            
            # Apply colormap
            rgba = ColorMapper.apply_colormap(iterations, max_iter, cmap)
            
            # Report completion
            if progress_reporter:
                progress_reporter.report_completed(
                    details={
                        "width": width,
                        "height": height,
                        "c_value": f"{c_real}+{c_imag}j",
                        "iterations": int(np.mean(iterations))
                    }
                )
            
            return rgba
    
    @error_boundary(reraise=True)
    def _render_l_system(self, params: Dict[str, Any], 
                        progress_reporter: Optional[ProgressReporter] = None) -> np.ndarray:
        """
        Render an L-System fractal.
        
        Args:
            params: Parameters for rendering
            progress_reporter: Optional progress reporter
            
        Returns:
            RGBA array of the rendered fractal
            
        Raises:
            LSystemError: If rendering fails
        """
        import matplotlib.pyplot as plt
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        import io
        from PIL import Image
        from rfm.core.fractal import LSystem
        
        # Extract parameters
        width = params.get("width", 800)
        height = params.get("height", 600)
        axiom = params.get("axiom", "F")
        rules = params.get("rules", {"F": "F+F-F-F+F"})
        angle = params.get("angle", 90.0)
        iterations = params.get("iterations", 4)
        line_width = params.get("line_width", 1.0)
        color = params.get("color", "#b086ff")
        alpha = params.get("alpha", 0.8)
        
        # Report initial progress
        if progress_reporter:
            progress_reporter.report_progress(
                0,
                current_step="Initializing L-System rendering",
                details={
                    "axiom": axiom,
                    "iterations": iterations,
                    "angle": angle
                }
            )
        
        try:
            # Create L-System with progress reporting
            lsystem_config = {
                "axiom": axiom,
                "rules": rules,
                "angle": angle,
                "depth": iterations,
                "color": color,
                "alpha": alpha,
                "width": line_width
            }
            
            lsystem = LSystem(lsystem_config)
            
            # Create figure
            dpi = 100
            figsize = (width / dpi, height / dpi)
            fig = Figure(figsize=figsize, dpi=dpi)
            canvas = FigureCanvasAgg(fig)
            ax = fig.add_subplot(111)
            
            # Set up axis
            ax.set_xlim(-1, 1)
            ax.set_ylim(-1, 1)
            ax.set_aspect('equal')
            ax.axis('off')
            
            # Calculate L-System
            if progress_reporter:
                progress_reporter.report_progress(
                    5,
                    current_step="Setting up L-System calculation",
                    current_step_progress=100
                )
            
            # Draw L-System with progress reporting
            lsystem.draw(ax, progress_reporter)
            
            # Check for cancellation
            if progress_reporter and progress_reporter.should_cancel():
                progress_reporter.report_canceled()
                # Return a blank image for canceled renders
                rgba_array = np.ones((height, width, 4), dtype=np.float32) * 0.5
                rgba_array[:, :, 3] = 0.5  # Semi-transparent
                return rgba_array
            
            # Report rendering to image
            if progress_reporter:
                progress_reporter.report_progress(
                    95,
                    current_step="Rendering L-System to image",
                    current_step_progress=0
                )
            
            # Render figure to array
            fig.tight_layout(pad=0)
            canvas.draw()
            
            # Convert to RGBA array
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=dpi, bbox_inches='tight', pad_inches=0)
            buf.seek(0)
            
            # Load image with PIL
            img = Image.open(buf)
            img = img.resize((width, height), Image.LANCZOS)
            rgba_array = np.array(img) / 255.0
            
            # Report completion
            if progress_reporter:
                progress_reporter.report_completed(
                    details={
                        "width": width,
                        "height": height,
                        "iterations": iterations
                    }
                )
            
            return rgba_array
        except Exception as e:
            # Report failure
            if progress_reporter:
                progress_reporter.report_failed(
                    str(e),
                    details={"exception_type": type(e).__name__}
                )
            
            raise LSystemError(
                message=f"Failed to render L-System: {str(e)}",
                fractal_type="l_system",
                params=params,
                original_exception=e,
                remediation="Check L-System parameters and rules syntax"
            )
    
    @error_boundary(reraise=True)
    def _render_cantor_dust(self, params: Dict[str, Any], 
                           progress_reporter: Optional[ProgressReporter] = None) -> np.ndarray:
        """
        Render a Cantor dust fractal.
        
        Args:
            params: Parameters for rendering
            progress_reporter: Optional progress reporter
            
        Returns:
            RGBA array of the rendered fractal
            
        Raises:
            CantorError: If rendering fails
        """
        import matplotlib.pyplot as plt
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        import io
        from PIL import Image
        from rfm.core.fractal import CantorDust
        
        # Extract parameters
        width = params.get("width", 800)
        height = params.get("height", 600)
        gap_ratio = params.get("gap_ratio", 0.3)
        iterations = params.get("iterations", 4)
        color = params.get("color", "#b086ff")
        alpha = params.get("alpha", 0.8)
        
        # Report initial progress
        if progress_reporter:
            progress_reporter.report_progress(
                0,
                current_step="Initializing Cantor dust rendering",
                details={
                    "iterations": iterations,
                    "gap_ratio": gap_ratio
                }
            )
        
        try:
            # Create Cantor dust with progress reporting
            cantor_config = {
                "depth": iterations,
                "gap_ratio": gap_ratio,
                "color": color,
                "alpha": alpha
            }
            
            cantor = CantorDust(cantor_config)
            
            # Create figure
            dpi = 100
            figsize = (width / dpi, height / dpi)
            fig = Figure(figsize=figsize, dpi=dpi)
            canvas = FigureCanvasAgg(fig)
            ax = fig.add_subplot(111)
            
            # Set up axis
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.set_aspect('equal')
            ax.axis('off')
            
            # Calculate Cantor dust
            if progress_reporter:
                progress_reporter.report_progress(
                    5,
                    current_step="Setting up Cantor dust calculation",
                    current_step_progress=100
                )
            
            # Draw Cantor dust with progress reporting
            cantor.draw(ax, progress_reporter)
            
            # Check for cancellation
            if progress_reporter and progress_reporter.should_cancel():
                progress_reporter.report_canceled()
                # Return a blank image for canceled renders
                rgba_array = np.ones((height, width, 4), dtype=np.float32) * 0.5
                rgba_array[:, :, 3] = 0.5  # Semi-transparent
                return rgba_array
            
            # Report rendering to image
            if progress_reporter:
                progress_reporter.report_progress(
                    95,
                    current_step="Rendering Cantor dust to image",
                    current_step_progress=0
                )
            
            # Render figure to array
            fig.tight_layout(pad=0)
            canvas.draw()
            
            # Convert to RGBA array
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=dpi, bbox_inches='tight', pad_inches=0)
            buf.seek(0)
            
            # Load image with PIL
            img = Image.open(buf)
            img = img.resize((width, height), Image.LANCZOS)
            rgba_array = np.array(img) / 255.0
            
            # Report completion
            if progress_reporter:
                progress_reporter.report_completed(
                    details={
                        "width": width,
                        "height": height,
                        "iterations": iterations
                    }
                )
            
            return rgba_array
        except Exception as e:
            # Report failure
            if progress_reporter:
                progress_reporter.report_failed(
                    str(e),
                    details={"exception_type": type(e).__name__}
                )
            
            raise CantorError(
                message=f"Failed to render Cantor dust: {str(e)}",
                fractal_type="cantor dust",
                params=params,
                original_exception=e,
                remediation="Check Cantor dust parameters"
            )