"""Fractal generation algorithms for the RFM visualization."""
from __future__ import annotations

import logging
import math
from typing import Dict, Any, List, Tuple, Optional, Callable

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch

from .progress import ProgressReporter

logger = logging.getLogger(__name__)


class LSystem:
    """L-system fractal generator for plant-like patterns."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the L-system with the given configuration.
        
        Args:
            config: Configuration dictionary with L-system parameters
        """
        self.axiom = config.get("axiom", "F")
        self.rules = config.get("rules", {"F": "F+F-F-F+F"})
        self.angle = config.get("angle", 90)
        self.depth = config.get("depth", 4)
        self.color = config.get("color", "#2c3e50")
        self.alpha = config.get("alpha", 0.2)
        self.width = config.get("width", 0.5)
        
        logger.debug(f"Initialized L-system with depth {self.depth}, angle {self.angle}")
    
    def generate(self, progress_reporter: Optional[ProgressReporter] = None) -> str:
        """Generate the L-system string by applying rules recursively.
        
        Args:
            progress_reporter: Optional progress reporter for tracking progress
            
        Returns:
            The expanded L-system string
        """
        result = self.axiom
        
        for i in range(self.depth):
            next_result = ""
            chars_processed = 0
            total_chars = len(result)
            
            for c in result:
                next_result += self.rules.get(c, c)
                
                # Report progress
                chars_processed += 1
                if progress_reporter and total_chars > 100 and chars_processed % 100 == 0:
                    iteration_progress = chars_processed / total_chars
                    overall_progress = (i + iteration_progress) / self.depth
                    progress_reporter.report_progress(
                        overall_progress * 50,  # 0-50% for generation
                        current_step=f"Generating L-system (iteration {i+1}/{self.depth})",
                        total_steps=self.depth,
                        current_step_progress=iteration_progress * 100
                    )
                    
                    # Check for cancellation
                    if progress_reporter.should_cancel():
                        logger.info("L-system generation canceled")
                        return result
            
            result = next_result
            logger.debug(f"L-system iteration {i+1}: length {len(result)}")
            
            # Report iteration completion
            if progress_reporter:
                progress_reporter.report_progress(
                    (i + 1) / self.depth * 50,  # 0-50% for generation
                    current_step=f"L-system iteration {i+1} complete",
                    total_steps=self.depth,
                    current_step_progress=100
                )
                
        return result
    
    def compute_coordinates(self, progress_reporter: Optional[ProgressReporter] = None) -> np.ndarray:
        """Compute coordinates for the L-system using turtle graphics.
        
        Args:
            progress_reporter: Optional progress reporter for tracking progress
            
        Returns:
            Array of (x,y) coordinates
        """
        # Generate the L-system string
        lsystem_str = self.generate(progress_reporter)
        
        # Initialize turtle state
        x, y = 0.0, 0.0
        heading = 0.0
        stack = []
        coords = [(x, y)]
        angle_rad = math.radians(self.angle)
        
        # Process each character in the L-system string
        total_chars = len(lsystem_str)
        for i, ch in enumerate(lsystem_str):
            if ch == 'F':  # Move forward
                x += math.cos(heading)
                y += math.sin(heading)
                coords.append((x, y))
            elif ch == '+':  # Turn left
                heading += angle_rad
            elif ch == '-':  # Turn right
                heading -= angle_rad
            elif ch == '[':  # Push state
                stack.append((x, y, heading))
            elif ch == ']':  # Pop state
                x, y, heading = stack.pop()
                coords.append((x, y))
            
            # Report progress for coordinate calculation phase
            if progress_reporter and total_chars > 100 and i % 100 == 0:
                progress = 50 + (i / total_chars) * 30  # 50-80% for coordinate calculation
                progress_reporter.report_progress(
                    progress,
                    current_step="Calculating L-system coordinates",
                    current_step_progress=(i / total_chars) * 100
                )
                
                # Check for cancellation
                if progress_reporter.should_cancel():
                    logger.info("L-system coordinate calculation canceled")
                    break
        
        # Convert to numpy array and normalize
        coords_array = np.array(coords)
        if len(coords_array) > 1:
            # Normalize to fit in the range [-0.5, 0.5]
            min_vals = np.min(coords_array, axis=0)
            max_vals = np.max(coords_array, axis=0)
            range_vals = max_vals - min_vals
            if np.all(range_vals > 0):
                coords_array = (coords_array - min_vals) / range_vals - 0.5
        
        # Report completion of coordinate calculation
        if progress_reporter:
            progress_reporter.report_progress(
                80,  # 80% complete after coordinate calculation
                current_step="L-system coordinates calculated",
                current_step_progress=100
            )
            
        return coords_array
    
    def draw(self, ax: plt.Axes, progress_reporter: Optional[ProgressReporter] = None) -> None:
        """Draw the L-system on the given axes.
        
        Args:
            ax: Matplotlib axes to draw on
            progress_reporter: Optional progress reporter for tracking progress
        """
        # Report starting drawing phase
        if progress_reporter:
            progress_reporter.report_progress(
                80,  # 80% complete after coordinate calculation
                current_step="Drawing L-system",
                current_step_progress=0
            )
            
        coords = self.compute_coordinates(progress_reporter)
        
        # Scale to fit the axes
        ax_xmin, ax_xmax = ax.get_xlim()
        ax_ymin, ax_ymax = ax.get_ylim()
        
        ax_width = ax_xmax - ax_xmin
        ax_height = ax_ymax - ax_ymin
        
        scale = min(ax_width, ax_height) * 0.8
        center_x = (ax_xmin + ax_xmax) / 2
        center_y = (ax_ymin + ax_ymax) / 2
        
        # Plot the coordinates
        x = center_x + coords[:, 0] * scale
        y = center_y + coords[:, 1] * scale
        
        ax.plot(x, y, '-', color=self.color, alpha=self.alpha, linewidth=self.width, zorder=1)
        logger.debug(f"Drew L-system with {len(coords)} segments")
        
        # Report drawing completion
        if progress_reporter:
            progress_reporter.report_progress(
                100,  # 100% complete
                current_step="L-system drawing complete",
                current_step_progress=100
            )


class MandelbrotSet:
    """Mandelbrot set fractal generator."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Mandelbrot set with the given configuration.
        
        Args:
            config: Configuration dictionary with Mandelbrot parameters
        """
        self.center = config.get("center", [-0.5, 0])
        self.zoom = config.get("zoom", 1.5)
        self.max_iter = config.get("max_iter", 100)
        self.cmap = config.get("cmap", "viridis")
        self.alpha = config.get("alpha", 0.2)
        
        logger.debug(f"Initialized Mandelbrot set with center {self.center}, zoom {self.zoom}")
    
    def compute(self, width: int, height: int, progress_reporter: Optional[ProgressReporter] = None) -> np.ndarray:
        """Compute the Mandelbrot set.
        
        Args:
            width: Width of the output image
            height: Height of the output image
            progress_reporter: Optional progress reporter for tracking progress
        
        Returns:
            Array of iteration counts
        """
        # Calculate the region to render
        x_min = self.center[0] - self.zoom
        x_max = self.center[0] + self.zoom
        y_min = self.center[1] - self.zoom * height / width
        y_max = self.center[1] + self.zoom * height / width
        
        # Create coordinate arrays
        x = np.linspace(x_min, x_max, width)
        y = np.linspace(y_min, y_max, height)
        X, Y = np.meshgrid(x, y)
        C = X + 1j * Y
        
        # Initialize arrays
        Z = np.zeros_like(C, dtype=complex)
        mask = np.ones_like(C, dtype=bool)
        iterations = np.zeros_like(C, dtype=int)
        
        # Report initial progress
        if progress_reporter:
            progress_reporter.report_progress(
                0,
                current_step="Computing Mandelbrot set",
                total_steps=self.max_iter,
                current_step_progress=0
            )
            
        # Compute the Mandelbrot set
        for i in range(self.max_iter):
            # Update only points that have not escaped
            Z[mask] = Z[mask] ** 2 + C[mask]
            
            # Check which points have escaped
            escaped = np.abs(Z) > 2.0
            iterations[escaped & mask] = i
            mask &= ~escaped
            
            # Report progress
            if progress_reporter and i % max(1, self.max_iter // 50) == 0:
                progress = (i / self.max_iter) * 95  # 0-95% for computation
                remaining_points = np.sum(mask)
                total_points = width * height
                escaped_points = total_points - remaining_points
                
                progress_reporter.report_progress(
                    progress,
                    current_step=f"Computing iteration {i+1}/{self.max_iter}",
                    total_steps=self.max_iter,
                    current_step_progress=100 * escaped_points / total_points,
                    details={
                        "remaining_points": int(remaining_points),
                        "escaped_points": int(escaped_points),
                        "current_iteration": i+1
                    }
                )
                
                # Check for cancellation
                if progress_reporter.should_cancel():
                    logger.info("Mandelbrot computation canceled")
                    break
            
            # Stop if all points have escaped
            if not np.any(mask):
                break
                
        # Report completion
        if progress_reporter:
            progress_reporter.report_progress(
                95,  # 95% complete after computation
                current_step="Mandelbrot computation complete",
                total_steps=self.max_iter,
                current_step_progress=100
            )
        
        return iterations
    
    def draw(self, ax: plt.Axes, progress_reporter: Optional[ProgressReporter] = None) -> None:
        """Draw the Mandelbrot set on the given axes.
        
        Args:
            ax: Matplotlib axes to draw on
            progress_reporter: Optional progress reporter for tracking progress
        """
        # Get the axes dimensions
        ax_xmin, ax_xmax = ax.get_xlim()
        ax_ymin, ax_ymax = ax.get_ylim()
        
        # Compute the Mandelbrot set
        width = 800
        height = int(width * (ax_ymax - ax_ymin) / (ax_xmax - ax_xmin))
        
        if progress_reporter:
            progress_reporter.report_progress(
                0,
                current_step="Setting up Mandelbrot rendering",
                current_step_progress=0
            )
            
        iterations = self.compute(width, height, progress_reporter)
        
        if progress_reporter:
            progress_reporter.report_progress(
                95,
                current_step="Rendering Mandelbrot set",
                current_step_progress=0
            )
            
        # Draw the Mandelbrot set
        extent = [ax_xmin, ax_xmax, ax_ymin, ax_ymax]
        ax.imshow(iterations, extent=extent, cmap=self.cmap, alpha=self.alpha, 
                  interpolation='bilinear', origin='lower', zorder=1)
        
        logger.debug("Drew Mandelbrot set")
        
        # Report completion
        if progress_reporter:
            progress_reporter.report_progress(
                100,  # 100% complete
                current_step="Mandelbrot rendering complete",
                current_step_progress=100
            )


class CantorDust:
    """Cantor dust fractal generator."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Cantor dust with the given configuration.
        
        Args:
            config: Configuration dictionary with Cantor dust parameters
        """
        self.depth = config.get("depth", 4)
        self.gap_ratio = config.get("gap_ratio", 0.3)
        self.color = config.get("color", "#2c3e50")
        self.alpha = config.get("alpha", 0.2)
        
        logger.debug(f"Initialized Cantor dust with depth {self.depth}, gap_ratio {self.gap_ratio}")
    
    def generate(self, x_min: float, x_max: float, y_min: float, y_max: float, depth: int, 
                progress_reporter: Optional[ProgressReporter] = None, 
                total_rectangles: Optional[List[int]] = None, 
                processed_rectangles: Optional[List[int]] = None,
                depth_offset: int = 0) -> List[Tuple[float, float, float, float]]:
        """Generate the Cantor dust rectangles recursively.
        
        Args:
            x_min: Minimum x-coordinate
            x_max: Maximum x-coordinate
            y_min: Minimum y-coordinate
            y_max: Maximum y-coordinate
            depth: Recursion depth
            progress_reporter: Optional progress reporter for tracking progress
            total_rectangles: Total number of rectangles for progress tracking
            processed_rectangles: Number of processed rectangles for progress tracking
            depth_offset: Depth offset for progress tracking
            
        Returns:
            List of (x_min, y_min, width, height) for each rectangle
        """
        # Initialize tracking variables on first call
        if total_rectangles is None:
            # Calculate total number of rectangles using geometric series sum
            # Each level has 8^depth rectangles
            total_rectangles = [sum(8**i for i in range(self.depth + 1))]
            processed_rectangles = [0]
            
            # Report initial progress
            if progress_reporter:
                progress_reporter.report_progress(
                    0,
                    current_step=f"Generating Cantor dust (depth {self.depth})",
                    total_steps=self.depth,
                    current_step_progress=0,
                    details={"total_rectangles": total_rectangles[0]}
                )
        
        # Base case: return the current rectangle
        if depth == 0:
            # Update progress
            if progress_reporter and total_rectangles and processed_rectangles:
                processed_rectangles[0] += 1
                progress = (processed_rectangles[0] / total_rectangles[0]) * 80  # 0-80% for generation
                
                # Report progress at intervals to avoid too many updates
                if processed_rectangles[0] % max(1, total_rectangles[0] // 100) == 0:
                    progress_reporter.report_progress(
                        progress,
                        current_step=f"Generating Cantor dust (depth {self.depth - depth_offset}/{self.depth})",
                        total_steps=self.depth,
                        current_step_progress=processed_rectangles[0] / total_rectangles[0] * 100,
                        details={
                            "processed_rectangles": processed_rectangles[0],
                            "total_rectangles": total_rectangles[0]
                        }
                    )
                    
                    # Check for cancellation
                    if progress_reporter.should_cancel():
                        logger.info("Cantor dust generation canceled")
                        return []
                
            return [(x_min, y_min, x_max - x_min, y_max - y_min)]
        
        # Calculate the gap
        x_gap = (x_max - x_min) * self.gap_ratio / 2
        y_gap = (y_max - y_min) * self.gap_ratio / 2
        
        # Calculate the new corners
        x_third = x_min + (x_max - x_min) / 3
        x_two_third = x_min + 2 * (x_max - x_min) / 3
        y_third = y_min + (y_max - y_min) / 3
        y_two_third = y_min + 2 * (y_max - y_min) / 3
        
        # Recursively generate the dust in the 8 corners
        rectangles = []
        
        # Check for cancellation before continuing recursion
        if progress_reporter and progress_reporter.should_cancel():
            logger.info("Cantor dust generation canceled")
            return rectangles
            
        rectangles.extend(self.generate(
            x_min, x_third, y_min, y_third, depth - 1, 
            progress_reporter, total_rectangles, processed_rectangles, depth_offset
        ))
        rectangles.extend(self.generate(
            x_third, x_two_third, y_min, y_third, depth - 1,
            progress_reporter, total_rectangles, processed_rectangles, depth_offset
        ))
        rectangles.extend(self.generate(
            x_two_third, x_max, y_min, y_third, depth - 1,
            progress_reporter, total_rectangles, processed_rectangles, depth_offset
        ))
        rectangles.extend(self.generate(
            x_min, x_third, y_third, y_two_third, depth - 1,
            progress_reporter, total_rectangles, processed_rectangles, depth_offset
        ))
        rectangles.extend(self.generate(
            x_two_third, x_max, y_third, y_two_third, depth - 1,
            progress_reporter, total_rectangles, processed_rectangles, depth_offset
        ))
        rectangles.extend(self.generate(
            x_min, x_third, y_two_third, y_max, depth - 1,
            progress_reporter, total_rectangles, processed_rectangles, depth_offset
        ))
        rectangles.extend(self.generate(
            x_third, x_two_third, y_two_third, y_max, depth - 1,
            progress_reporter, total_rectangles, processed_rectangles, depth_offset
        ))
        rectangles.extend(self.generate(
            x_two_third, x_max, y_two_third, y_max, depth - 1,
            progress_reporter, total_rectangles, processed_rectangles, depth_offset
        ))
        
        return rectangles
    
    def draw(self, ax: plt.Axes, progress_reporter: Optional[ProgressReporter] = None) -> None:
        """Draw the Cantor dust on the given axes.
        
        Args:
            ax: Matplotlib axes to draw on
            progress_reporter: Optional progress reporter for tracking progress
        """
        # Get the axes dimensions
        ax_xmin, ax_xmax = ax.get_xlim()
        ax_ymin, ax_ymax = ax.get_ylim()
        
        # Generate the Cantor dust
        if progress_reporter:
            progress_reporter.report_progress(
                0,
                current_step="Generating Cantor dust",
                total_steps=self.depth,
                current_step_progress=0
            )
            
        rectangles = self.generate(ax_xmin, ax_xmax, ax_ymin, ax_ymax, self.depth, progress_reporter)
        
        # Report drawing phase
        if progress_reporter:
            progress_reporter.report_progress(
                80,  # 80% complete after generation
                current_step="Drawing Cantor dust",
                total_steps=self.depth,
                current_step_progress=0,
                details={"rectangle_count": len(rectangles)}
            )
            
        # Draw the rectangles
        total_rectangles = len(rectangles)
        for i, rect in enumerate(rectangles):
            x, y, width, height = rect
            ax.add_patch(plt.Rectangle((x, y), width, height, 
                                      facecolor=self.color, edgecolor='none', 
                                      alpha=self.alpha, zorder=1))
            
            # Report drawing progress
            if progress_reporter and i % max(1, total_rectangles // 50) == 0:
                progress = 80 + (i / total_rectangles) * 20  # 80-100% for drawing
                progress_reporter.report_progress(
                    progress,
                    current_step=f"Drawing Cantor dust rectangles ({i}/{total_rectangles})",
                    total_steps=self.depth,
                    current_step_progress=i / total_rectangles * 100,
                    details={"rectangle_count": total_rectangles}
                )
                
                # Check for cancellation
                if progress_reporter.should_cancel():
                    logger.info("Cantor dust drawing canceled")
                    break
                    
        # Report completion
        if progress_reporter:
            progress_reporter.report_progress(
                100,  # 100% complete
                current_step="Cantor dust drawing complete",
                total_steps=self.depth,
                current_step_progress=100,
                details={"rectangle_count": total_rectangles}
            )
            
        logger.debug(f"Drew Cantor dust with {len(rectangles)} rectangles")


class JuliaSet:
    """Julia set fractal generator."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Julia set with the given configuration.
        
        Args:
            config: Configuration dictionary with Julia set parameters
        """
        self.c_real = config.get("c_real", -0.7)
        self.c_imag = config.get("c_imag", 0.27)
        self.center = config.get("center", [0, 0])
        self.zoom = config.get("zoom", 1.5)
        self.max_iter = config.get("max_iter", 100)
        self.cmap = config.get("cmap", "plasma")  # Different default colormap than Mandelbrot
        self.alpha = config.get("alpha", 0.2)
        
        logger.debug(f"Initialized Julia set with c={self.c_real}+{self.c_imag}j, center={self.center}, zoom={self.zoom}")
    
    def compute(self, width: int, height: int, progress_reporter: Optional[ProgressReporter] = None) -> np.ndarray:
        """Compute the Julia set.
        
        Args:
            width: Width of the output image
            height: Height of the output image
            progress_reporter: Optional progress reporter for tracking progress
        
        Returns:
            Array of iteration counts
        """
        # Calculate the region to render
        x_min = self.center[0] - self.zoom
        x_max = self.center[0] + self.zoom
        y_min = self.center[1] - self.zoom * height / width
        y_max = self.center[1] + self.zoom * height / width
        
        # Create coordinate arrays
        x = np.linspace(x_min, x_max, width)
        y = np.linspace(y_min, y_max, height)
        X, Y = np.meshgrid(x, y)
        Z = X + 1j * Y  # Initial Z values (coordinates in complex plane)
        C = complex(self.c_real, self.c_imag)  # Fixed C value for Julia set
        
        # Initialize arrays
        mask = np.ones_like(Z, dtype=bool)
        iterations = np.zeros_like(Z, dtype=int)
        
        # Report initial progress
        if progress_reporter:
            progress_reporter.report_progress(
                0,
                current_step="Computing Julia set",
                total_steps=self.max_iter,
                current_step_progress=0,
                details={
                    "c_value": f"{self.c_real}+{self.c_imag}j",
                    "width": width,
                    "height": height
                }
            )
            
        # Compute the Julia set
        for i in range(self.max_iter):
            # Update only points that have not escaped
            Z[mask] = Z[mask] ** 2 + C
            
            # Check which points have escaped
            escaped = np.abs(Z) > 2.0
            iterations[escaped & mask] = i
            mask &= ~escaped
            
            # Report progress
            if progress_reporter and i % max(1, self.max_iter // 50) == 0:
                progress = (i / self.max_iter) * 95  # 0-95% for computation
                remaining_points = np.sum(mask)
                total_points = width * height
                escaped_points = total_points - remaining_points
                
                progress_reporter.report_progress(
                    progress,
                    current_step=f"Computing Julia iteration {i+1}/{self.max_iter}",
                    total_steps=self.max_iter,
                    current_step_progress=100 * escaped_points / total_points,
                    details={
                        "remaining_points": int(remaining_points),
                        "escaped_points": int(escaped_points),
                        "current_iteration": i+1
                    }
                )
                
                # Check for cancellation
                if progress_reporter.should_cancel():
                    logger.info("Julia set computation canceled")
                    break
            
            # Stop if all points have escaped
            if not np.any(mask):
                break
                
        # Report completion
        if progress_reporter:
            progress_reporter.report_progress(
                95,  # 95% complete after computation
                current_step="Julia set computation complete",
                total_steps=self.max_iter,
                current_step_progress=100,
                details={
                    "c_value": f"{self.c_real}+{self.c_imag}j",
                    "width": width,
                    "height": height
                }
            )
        
        return iterations
    
    def draw(self, ax: plt.Axes, progress_reporter: Optional[ProgressReporter] = None) -> None:
        """Draw the Julia set on the given axes.
        
        Args:
            ax: Matplotlib axes to draw on
            progress_reporter: Optional progress reporter for tracking progress
        """
        # Get the axes dimensions
        ax_xmin, ax_xmax = ax.get_xlim()
        ax_ymin, ax_ymax = ax.get_ylim()
        
        # Compute the Julia set
        width = 800
        height = int(width * (ax_ymax - ax_ymin) / (ax_xmax - ax_xmin))
        
        if progress_reporter:
            progress_reporter.report_progress(
                0,
                current_step="Setting up Julia set rendering",
                current_step_progress=0,
                details={"c_value": f"{self.c_real}+{self.c_imag}j"}
            )
            
        iterations = self.compute(width, height, progress_reporter)
        
        if progress_reporter:
            progress_reporter.report_progress(
                95,
                current_step="Rendering Julia set",
                current_step_progress=0
            )
            
        # Draw the Julia set
        extent = [ax_xmin, ax_xmax, ax_ymin, ax_ymax]
        ax.imshow(iterations, extent=extent, cmap=self.cmap, alpha=self.alpha, 
                 interpolation='bilinear', origin='lower', zorder=1)
        
        # Report completion
        if progress_reporter:
            progress_reporter.report_progress(
                100,  # 100% complete
                current_step="Julia set rendering complete",
                current_step_progress=100
            )
            
        logger.debug(f"Drew Julia set with c={self.c_real}+{self.c_imag}j")


def create_fractal(config: Dict[str, Any]) -> LSystem | MandelbrotSet | CantorDust | JuliaSet:
    """Factory function to create a fractal based on configuration.
    
    Args:
        config: Configuration dictionary with fractal parameters
    
    Returns:
        A fractal generator
    
    Raises:
        ValueError: If the fractal type is unknown
    """
    fractal_type = config.get("type", "l_system")
    depth = config.get("depth", 4)
    parameters = config.get("parameters", {})
    
    # Add depth to parameters if not already present
    if "depth" not in parameters:
        parameters["depth"] = depth
    
    if fractal_type == "l_system":
        return LSystem(parameters)
    elif fractal_type == "mandelbrot":
        return MandelbrotSet(parameters)
    elif fractal_type == "julia":
        return JuliaSet(parameters)
    elif fractal_type == "cantor":
        return CantorDust(parameters)
    else:
        raise ValueError(f"Unknown fractal type: {fractal_type}")