"""Layout utilities for RFM visualization."""
from __future__ import annotations

import logging
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


class GoldenRatioLayout:
    """Layout system based on the golden ratio."""
    
    GOLDEN_RATIO = 1.618033988749895
    
    def __init__(self, ax: plt.Axes, config: Dict[str, Any]):
        """Initialize the layout with the given configuration.
        
        Args:
            ax: Matplotlib axes to draw on
            config: Configuration dictionary with layout parameters
        """
        self.ax = ax
        self.grid_width = config.get("grid", {}).get("width", 100)
        self.grid_height = config.get("grid", {}).get("height", 100)
        self.origin = config.get("grid", {}).get("origin", [50, 50])
        self.golden_ratio = config.get("grid", {}).get("golden_ratio", self.GOLDEN_RATIO)
        
        # Set up the axes
        self.ax.set_xlim(0, self.grid_width)
        self.ax.set_ylim(0, self.grid_height)
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        
        logger.debug(f"Initialized layout with grid {self.grid_width}x{self.grid_height}")
    
    def golden_section(self, length: float, ratio: float = None) -> Tuple[float, float]:
        """Divide a length according to the golden ratio.
        
        Args:
            length: Length to divide
            ratio: Ratio to use (defaults to golden ratio)
        
        Returns:
            Tuple of (larger_part, smaller_part)
        """
        ratio = ratio or self.golden_ratio
        smaller = length / (1 + ratio)
        larger = length - smaller
        return larger, smaller
    
    def golden_grid(self, n_divisions: int = 3) -> np.ndarray:
        """Create a grid with golden ratio spacing.
        
        Args:
            n_divisions: Number of divisions on each side
        
        Returns:
            2D array of grid line positions
        """
        # Generate Fibonacci-like sequence for grid lines
        fib = [0, 1]
        for i in range(2, n_divisions + 2):
            fib.append(fib[i-1] + fib[i-2])
        
        # Normalize to fit grid
        fib = np.array(fib) / fib[-1] * self.grid_width
        
        # Create grid
        X, Y = np.meshgrid(fib, fib)
        
        return X, Y
    
    def add_title(self, title: str, fontsize: int = 16) -> None:
        """Add a title to the visualization.
        
        Args:
            title: Title text
            fontsize: Font size
        """
        self.ax.text(
            self.grid_width / 2, self.grid_height - 5, title,
            ha='center', va='center', color='white',
            fontsize=fontsize, fontweight='bold'
        )
        
        logger.debug(f"Added title: {title}")
    
    def add_subtitle(self, subtitle: str, fontsize: int = 12) -> None:
        """Add a subtitle to the visualization.
        
        Args:
            subtitle: Subtitle text
            fontsize: Font size
        """
        self.ax.text(
            self.grid_width / 2, self.grid_height - 10, subtitle,
            ha='center', va='center', color='#b086ff',
            fontsize=fontsize, fontweight='normal'
        )
        
        logger.debug(f"Added subtitle: {subtitle}")
    
    def add_attribution(self, text: str, fontsize: int = 8) -> None:
        """Add attribution text to the visualization.
        
        Args:
            text: Attribution text
            fontsize: Font size
        """
        self.ax.text(
            5, 5, text,
            ha='left', va='bottom', color='#b086ff',
            fontsize=fontsize, alpha=0.7
        )
        
        logger.debug(f"Added attribution: {text}")
    
    def draw_grid(self, color: str = "#2c3e50", alpha: float = 0.1) -> None:
        """Draw a golden ratio grid for reference.
        
        Args:
            color: Grid line color
            alpha: Grid line alpha
        """
        X, Y = self.golden_grid()
        
        # Draw vertical lines
        for x in X[0]:
            self.ax.axvline(x, color=color, alpha=alpha, linestyle=':')
        
        # Draw horizontal lines
        for y in Y[:, 0]:
            self.ax.axhline(y, color=color, alpha=alpha, linestyle=':')
        
        logger.debug("Drew golden ratio grid")