"""Morphogenetic pattern generation for RFM visualization."""
from __future__ import annotations

import logging
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.spatial import Voronoi
from matplotlib.patches import Polygon

logger = logging.getLogger(__name__)


class VoronoiMorphogen:
    """Voronoi diagram morphogenetic pattern generator."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Voronoi morphogen with the given configuration.
        
        Args:
            config: Configuration dictionary with Voronoi morphogen parameters
        """
        self.points = config.get("points", 15)
        self.color_start = config.get("color_start", "#00c2c7")
        self.color_end = config.get("color_end", "#b086ff")
        self.opacity = config.get("opacity", 0.2)
        self.blend_mode = config.get("blend_mode", "overlay")
        
        logger.debug(f"Initialized Voronoi morphogen with {self.points} points")
    
    def _generate_points(self, xmin: float, xmax: float, ymin: float, ymax: float) -> np.ndarray:
        """Generate random points for the Voronoi diagram.
        
        Args:
            xmin: Minimum x-coordinate
            xmax: Maximum x-coordinate
            ymin: Minimum y-coordinate
            ymax: Maximum y-coordinate
        
        Returns:
            Array of (x,y) coordinates
        """
        # Generate random points
        np.random.seed(42)
        x = np.random.uniform(xmin, xmax, self.points)
        y = np.random.uniform(ymin, ymax, self.points)
        
        # Add points at the edges to ensure bounded Voronoi cells
        buffer = max(xmax - xmin, ymax - ymin) * 0.5
        edge_points = [
            [xmin - buffer, ymin - buffer],
            [xmax + buffer, ymin - buffer],
            [xmin - buffer, ymax + buffer],
            [xmax + buffer, ymax + buffer],
        ]
        
        # Combine all points
        points = np.column_stack((x, y))
        points = np.vstack((points, edge_points))
        
        return points
    
    def _create_colormap(self) -> LinearSegmentedColormap:
        """Create a custom colormap for the Voronoi diagram.
        
        Returns:
            A matplotlib colormap
        """
        return LinearSegmentedColormap.from_list(
            "morphogen_cmap", [self.color_start, self.color_end], N=100
        )
    
    def draw(self, ax: plt.Axes) -> None:
        """Draw the Voronoi morphogen on the given axes.
        
        Args:
            ax: Matplotlib axes to draw on
        """
        # Get the axes dimensions
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        
        # Generate points
        points = self._generate_points(xmin, xmax, ymin, ymax)
        
        # Create Voronoi diagram
        vor = Voronoi(points)
        
        # Create colormap
        cmap = self._create_colormap()
        
        # Draw Voronoi cells
        for i, region_idx in enumerate(vor.point_region[:-4]):  # Skip edge points
            region = vor.regions[region_idx]
            if -1 not in region and len(region) > 2:  # Skip unbounded regions
                polygon = [vor.vertices[j] for j in region]
                
                # Draw the polygon
                cell = Polygon(
                    polygon,
                    facecolor=cmap(i / self.points),
                    edgecolor='none',
                    alpha=self.opacity,
                    zorder=2
                )
                ax.add_patch(cell)
        
        logger.debug("Drew Voronoi morphogen pattern")


class GradientMorphogen:
    """Gradient field morphogenetic pattern generator."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the gradient morphogen with the given configuration.
        
        Args:
            config: Configuration dictionary with gradient morphogen parameters
        """
        self.color_start = config.get("color_start", "#00c2c7")
        self.color_end = config.get("color_end", "#b086ff")
        self.opacity = config.get("opacity", 0.2)
        self.blend_mode = config.get("blend_mode", "overlay")
        self.radial = config.get("radial", True)
        
        logger.debug(f"Initialized gradient morphogen, radial={self.radial}")
    
    def _create_colormap(self) -> LinearSegmentedColormap:
        """Create a custom colormap for the gradient.
        
        Returns:
            A matplotlib colormap
        """
        return LinearSegmentedColormap.from_list(
            "morphogen_cmap", [self.color_start, self.color_end], N=100
        )
    
    def draw(self, ax: plt.Axes) -> None:
        """Draw the gradient morphogen on the given axes.
        
        Args:
            ax: Matplotlib axes to draw on
        """
        # Get the axes dimensions
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        
        # Create colormap
        cmap = self._create_colormap()
        
        # Create gradient mesh
        nx, ny = 100, 100
        x = np.linspace(xmin, xmax, nx)
        y = np.linspace(ymin, ymax, ny)
        X, Y = np.meshgrid(x, y)
        
        # Compute gradient values
        if self.radial:
            # Radial gradient from center
            center_x = (xmin + xmax) / 2
            center_y = (ymin + ymax) / 2
            radius = np.sqrt((xmax - center_x)**2 + (ymax - center_y)**2)
            Z = np.sqrt((X - center_x)**2 + (Y - center_y)**2) / radius
        else:
            # Linear gradient from bottom to top
            Z = (Y - ymin) / (ymax - ymin)
        
        # Draw the gradient
        im = ax.imshow(
            Z,
            cmap=cmap,
            extent=[xmin, xmax, ymin, ymax],
            alpha=self.opacity,
            origin='lower',
            zorder=2
        )
        
        logger.debug("Drew gradient morphogen pattern")


def create_morphogen(config: Dict[str, Any]) -> VoronoiMorphogen | GradientMorphogen:
    """Factory function to create a morphogen based on configuration.
    
    Args:
        config: Configuration dictionary with morphogen parameters
    
    Returns:
        A morphogen generator
    
    Raises:
        ValueError: If the morphogen type is unknown
    """
    morphogen_type = config.get("type", "voronoi")
    
    if morphogen_type == "voronoi":
        return VoronoiMorphogen(config)
    elif morphogen_type == "gradient":
        return GradientMorphogen(config)
    else:
        raise ValueError(f"Unknown morphogen type: {morphogen_type}")