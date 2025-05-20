"""Animation functionality for RFM visualization."""
from __future__ import annotations

import logging
import math
from typing import Dict, Any, List, Tuple, Optional, Callable

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Circle

logger = logging.getLogger(__name__)


class BroadcastAnimation:
    """Information broadcast animation with radial pulses."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the broadcast animation with the given configuration.
        
        Args:
            config: Configuration dictionary with animation parameters
        """
        self.enabled = config.get("enabled", True)
        self.duration = config.get("duration", 400)  # ms
        self.fps = config.get("fps", 60)
        self.pulse_count = config.get("pulse_count", 3)
        self.easing = config.get("easing", "cubic-bezier(0.25, 0.1, 0.25, 1.0)")
        self.color = config.get("color", "#00c2c7")
        self.glow = config.get("glow", True)
        
        self.pulses = []
        self.animation = None
        
        logger.debug("Initialized broadcast animation")
    
    def _ease_out_cubic(self, t: float) -> float:
        """Cubic easing function.
        
        Args:
            t: Time parameter (0-1)
        
        Returns:
            Eased value
        """
        return 1 - (1 - t) ** 3
    
    def setup(self, ax: plt.Axes, components: Dict[str, Any]) -> animation.FuncAnimation:
        """Setup the animation.
        
        Args:
            ax: Matplotlib axes to draw on
            components: Dictionary of components
        
        Returns:
            Animation object
        """
        if not self.enabled:
            return None
        
        # Get the CIF component
        cif = components.get("cif")
        if not cif:
            logger.warning("Cannot create animation without CIF component")
            return None
        
        center = cif.center
        
        # Create pulse objects
        self.pulses = []
        max_radius = 50  # Maximum radius of pulses
        
        for i in range(self.pulse_count):
            # Create pulse with initial radius of 0
            pulse = Circle(
                center, 0,
                facecolor='none', edgecolor=self.color,
                linewidth=2, alpha=0.0, zorder=15
            )
            ax.add_patch(pulse)
            self.pulses.append(pulse)
        
        # Create animation
        frames = int(self.duration / 1000 * self.fps)
        interval = 1000 / self.fps
        
        self.animation = animation.FuncAnimation(
            ax.figure, self._animate,
            frames=frames, interval=interval,
            blit=True, repeat=True,
            fargs=(max_radius, center)
        )
        
        logger.debug(f"Setup animation with {frames} frames at {self.fps} fps")
        
        return self.animation
    
    def _animate(self, frame: int, max_radius: float = None, center: Tuple[float, float] = None) -> List[Circle]:
        """Animation function called for each frame.
        
        Args:
            frame: Frame number
            max_radius: Maximum radius of pulses (optional, can be set during setup)
            center: Center coordinates (optional, can be set during setup)
        
        Returns:
            List of artists to update
        """
        # Use provided parameters or defaults set during setup
        if max_radius is None:
            max_radius = 50  # Default value
        if center is None and len(self.pulses) > 0:
            # Try to get center from first pulse
            center = self.pulses[0].center
        
        frames_per_cycle = int(self.duration / 1000 * self.fps / self.pulse_count)
        
        for i, pulse in enumerate(self.pulses):
            # Calculate pulse phase (0-1)
            phase = (frame + i * frames_per_cycle / self.pulse_count) % frames_per_cycle / frames_per_cycle
            
            if phase < 1.0:
                # Pulse is active
                eased_phase = self._ease_out_cubic(phase)
                radius = eased_phase * max_radius
                alpha = 1.0 - eased_phase
                
                # Update pulse properties
                pulse.set_radius(radius)
                pulse.set_alpha(alpha)
            else:
                # Pulse is inactive
                pulse.set_radius(0)
                pulse.set_alpha(0)
        
        return self.pulses