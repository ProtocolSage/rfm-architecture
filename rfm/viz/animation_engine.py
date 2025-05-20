"""Advanced animation engine for RFM visualization with premium aesthetics."""
from __future__ import annotations

import logging
import math
import time
from typing import Dict, Any, List, Tuple, Optional, Callable, Union
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch
from matplotlib.collections import LineCollection
from matplotlib.colors import to_rgba, LinearSegmentedColormap
from matplotlib.patheffects import withStroke, Normal, Stroke, SimplePatchShadow
import matplotlib.patheffects as path_effects

logger = logging.getLogger(__name__)


class AnimationTimeline:
    """Controls animation sequencing and parameter interpolation."""
    
    def __init__(self, duration: float = 5.0, fps: int = 30, easing: str = "cubic"):
        """Initialize the animation timeline.
        
        Args:
            duration: Total duration in seconds
            fps: Frames per second
            easing: Easing function type ("linear", "cubic", "elastic", "bounce")
        """
        self.duration = duration
        self.fps = fps
        self.easing_type = easing
        self.total_frames = int(duration * fps)
        self.keyframes = {}
        self.current_frame = 0
        
        # Store parameter values per frame
        self.parameter_cache = {}
        
        logger.debug(f"Created animation timeline with {self.total_frames} frames at {fps} FPS")
    
    def add_keyframe(self, time_sec: float, parameters: Dict[str, Any]) -> None:
        """Add a keyframe at the specified time.
        
        Args:
            time_sec: Time in seconds
            parameters: Parameter values at this keyframe
        """
        frame = int(time_sec * self.fps)
        if frame < 0 or frame > self.total_frames:
            logger.warning(f"Keyframe at {time_sec}s (frame {frame}) is outside timeline duration")
        
        self.keyframes[frame] = parameters
        
        # Clear cache since we've modified keyframes
        self.parameter_cache = {}
        
        logger.debug(f"Added keyframe at {time_sec}s (frame {frame})")
    
    def _apply_easing(self, t: float) -> float:
        """Apply easing function to the time parameter.
        
        Args:
            t: Time parameter (0-1)
        
        Returns:
            Eased time parameter (0-1)
        """
        if self.easing_type == "linear":
            return t
        
        elif self.easing_type == "cubic":
            # Cubic ease in/out
            if t < 0.5:
                return 4 * t * t * t
            else:
                return 1 - pow(-2 * t + 2, 3) / 2
        
        elif self.easing_type == "elastic":
            # Elastic ease out
            c4 = (2 * math.pi) / 3
            if t == 0 or t == 1:
                return t
            return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1
        
        elif self.easing_type == "bounce":
            # Bounce ease out
            n1 = 7.5625
            d1 = 2.75
            
            if t < 1 / d1:
                return n1 * t * t
            elif t < 2 / d1:
                t -= 1.5 / d1
                return n1 * t * t + 0.75
            elif t < 2.5 / d1:
                t -= 2.25 / d1
                return n1 * t * t + 0.9375
            else:
                t -= 2.625 / d1
                return n1 * t * t + 0.984375
        
        return t  # Default to linear
    
    def _interpolate_value(self, value1: Any, value2: Any, t: float) -> Any:
        """Interpolate between two values based on time parameter.
        
        Args:
            value1: First value
            value2: Second value
            t: Time parameter (0-1)
        
        Returns:
            Interpolated value
        """
        # Handle numeric types
        if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
            return value1 * (1 - t) + value2 * t
        
        # Handle color interpolation (hex strings)
        elif isinstance(value1, str) and isinstance(value2, str) and value1.startswith("#") and value2.startswith("#"):
            # Convert hex colors to RGBA
            rgba1 = np.array(to_rgba(value1))
            rgba2 = np.array(to_rgba(value2))
            # Interpolate
            rgba_interp = rgba1 * (1 - t) + rgba2 * t
            # Convert back to hex (approximate)
            r, g, b, a = rgba_interp
            return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
        
        # Handle lists/tuples (element-wise)
        elif isinstance(value1, (list, tuple)) and isinstance(value2, (list, tuple)) and len(value1) == len(value2):
            return [self._interpolate_value(v1, v2, t) for v1, v2 in zip(value1, value2)]
        
        # Fallback: return value2 if we've passed the halfway point, otherwise value1
        return value2 if t > 0.5 else value1
    
    def get_parameters(self, frame: int) -> Dict[str, Any]:
        """Get the interpolated parameters for the specified frame.
        
        Args:
            frame: Frame number
        
        Returns:
            Interpolated parameters
        """
        # Use cached values if available
        if frame in self.parameter_cache:
            return self.parameter_cache[frame]
        
        # No keyframes? Return empty dict
        if not self.keyframes:
            return {}
        
        # Find the surrounding keyframes
        keyframes = sorted(self.keyframes.keys())
        
        # If before first keyframe, use first keyframe values
        if frame <= keyframes[0]:
            result = self.keyframes[keyframes[0]]
            self.parameter_cache[frame] = result
            return result
        
        # If after last keyframe, use last keyframe values
        if frame >= keyframes[-1]:
            result = self.keyframes[keyframes[-1]]
            self.parameter_cache[frame] = result
            return result
        
        # Find the surrounding keyframes
        prev_frame = max([k for k in keyframes if k <= frame])
        next_frame = min([k for k in keyframes if k > frame])
        
        # Calculate the interpolation factor
        t = (frame - prev_frame) / (next_frame - prev_frame)
        
        # Apply easing function
        t = self._apply_easing(t)
        
        # Interpolate between the keyframe values
        prev_params = self.keyframes[prev_frame]
        next_params = self.keyframes[next_frame]
        
        # Build result dict
        result = {}
        all_keys = set(prev_params.keys()) | set(next_params.keys())
        
        for key in all_keys:
            if key in prev_params and key in next_params:
                result[key] = self._interpolate_value(prev_params[key], next_params[key], t)
            elif key in prev_params:
                result[key] = prev_params[key]
            else:
                result[key] = next_params[key]
        
        # Cache the result
        self.parameter_cache[frame] = result
        
        return result
    
    def create_animation(self, fig: plt.Figure, update_func: Callable[[int, Dict[str, Any]], List], 
                       interval: int = None, blit: bool = True) -> animation.Animation:
        """Create an animation using this timeline.
        
        Args:
            fig: Matplotlib figure
            update_func: Function to update the figure (takes frame number and parameters)
            interval: Interval between frames in ms (defaults to 1000 / fps)
            blit: Whether to use blitting for better performance
        
        Returns:
            Matplotlib animation object
        """
        if interval is None:
            interval = int(1000 / self.fps)
        
        def wrapped_update(frame):
            # Get the parameters for this frame
            params = self.get_parameters(frame)
            # Call the update function
            return update_func(frame, params)
        
        anim = animation.FuncAnimation(
            fig, wrapped_update, frames=self.total_frames,
            interval=interval, blit=blit
        )
        
        return anim


class BroadcastSequence:
    """Creates pulsing information broadcast animations."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the broadcast animation sequence.
        
        Args:
            config: Configuration dictionary with animation parameters
        """
        self.enabled = config.get("enabled", True)
        self.pulse_color = config.get("color", "#00c2c7")
        self.glow_strength = config.get("glow_strength", 3.0)
        self.glow_color = config.get("glow_color", self.pulse_color)
        self.max_pulses = config.get("max_pulses", 3)
        self.pulse_speed = config.get("speed", 1.0)
        self.pulse_width = config.get("width", 2.0)
        self.fade_out = config.get("fade_out", True)
        
        # Animation state
        self.pulses = []
        self.paths = []
        
        logger.debug(f"Initialized broadcast sequence with {self.max_pulses} pulses")
    
    def add_source(self, center: Tuple[float, float], radius: float = 30) -> None:
        """Add a source for pulse animation.
        
        Args:
            center: Center point (x, y)
            radius: Maximum radius for pulses
        """
        self.paths.append({"center": center, "radius": radius, "type": "radial"})
        logger.debug(f"Added radial pulse source at {center}")
    
    def add_path(self, start: Tuple[float, float], end: Tuple[float, float], 
               curve: float = 0.2, speed: float = None) -> None:
        """Add a path for pulses to travel along.
        
        Args:
            start: Start point (x, y)
            end: End point (x, y)
            curve: Path curvature (0-1)
            speed: Pulse speed (overrides default if provided)
        """
        self.paths.append({
            "start": start,
            "end": end,
            "curve": curve,
            "speed": speed or self.pulse_speed,
            "type": "path"
        })
        logger.debug(f"Added pulse path from {start} to {end}")
    
    def add_connection_paths(self, components: Dict[str, Any], connections: List[Dict[str, Any]]) -> None:
        """Add paths based on component connections.
        
        Args:
            components: Dictionary of components
            connections: List of connection configurations
        """
        for conn in connections:
            source_name = conn.get("source")
            target_name = conn.get("target")
            
            if source_name in components and target_name in components:
                source = components[source_name]
                target = components[target_name]
                
                # Extract centers
                if hasattr(source, "center"):
                    source_center = source.center
                elif isinstance(source, dict) and "center" in source:
                    source_center = source["center"]
                else:
                    logger.warning(f"Could not determine center for {source_name}")
                    continue
                
                if hasattr(target, "center"):
                    target_center = target.center
                elif isinstance(target, dict) and "center" in target:
                    target_center = target["center"]
                else:
                    logger.warning(f"Could not determine center for {target_name}")
                    continue
                
                # Add the path
                curve = conn.get("curve", 0.2)
                self.add_path(source_center, target_center, curve)
        
        logger.debug(f"Added {len(connections)} connection paths")
    
    def update(self, frame: int, params: Dict[str, Any], ax: plt.Axes) -> List:
        """Update the broadcast animation.
        
        Args:
            frame: Frame number
            params: Animation parameters
            ax: Matplotlib axes
        
        Returns:
            List of updated artists
        """
        if not self.enabled or not self.paths:
            return []
        
        # Get parameters (or use defaults)
        num_pulses = params.get("num_pulses", self.max_pulses)
        pulse_color = params.get("pulse_color", self.pulse_color)
        pulse_width = params.get("pulse_width", self.pulse_width)
        
        # Clear existing pulses
        for pulse in self.pulses:
            pulse.remove()
        self.pulses = []
        
        # Create artists list to return
        artists = []
        
        # Process each path
        for path_idx, path in enumerate(self.paths):
            path_type = path.get("type", "radial")
            
            if path_type == "radial":
                # Radial pulse from a center point
                center = path["center"]
                max_radius = path["radius"]
                
                # Create pulses at different stages
                for i in range(num_pulses):
                    # Calculate pulse phase (0-1)
                    phase = ((frame * self.pulse_speed / 30) + i / num_pulses) % 1.0
                    
                    # Calculate pulse radius
                    radius = phase * max_radius
                    
                    # Calculate pulse alpha (fade out toward edge)
                    alpha = 1.0 - phase if self.fade_out else 0.8
                    
                    # Create the pulse
                    pulse = Circle(
                        center, radius,
                        facecolor="none",
                        edgecolor=pulse_color,
                        linewidth=pulse_width,
                        alpha=alpha,
                        zorder=15
                    )
                    
                    # Add glow effect
                    if self.glow_strength > 0:
                        pulse.set_path_effects([
                            path_effects.SimpleLineShadow(
                                offset=(0, 0),
                                shadow_color=self.glow_color,
                                alpha=alpha * 0.7,
                                rho=self.glow_strength
                            ),
                            path_effects.Normal()
                        ])
                    
                    # Add to axes and track
                    ax.add_patch(pulse)
                    self.pulses.append(pulse)
                    artists.append(pulse)
            
            elif path_type == "path":
                # Path from start to end
                start = path["start"]
                end = path["end"]
                curve = path["curve"]
                speed = path["speed"]
                
                # Create control point for curved path
                if curve != 0:
                    # Calculate the midpoint
                    mid_x = (start[0] + end[0]) / 2
                    mid_y = (start[1] + end[1]) / 2
                    
                    # Calculate normal vector
                    dx = end[0] - start[0]
                    dy = end[1] - start[1]
                    dist = math.sqrt(dx**2 + dy**2)
                    
                    # Normalize and perpendicular
                    nx = -dy / dist if dist > 0 else 0
                    ny = dx / dist if dist > 0 else 0
                    
                    # Create control point
                    control_x = mid_x + nx * curve * dist
                    control_y = mid_y + ny * curve * dist
                else:
                    control_x = (start[0] + end[0]) / 2
                    control_y = (start[1] + end[1]) / 2
                
                # Create pulses at different positions along the path
                for i in range(num_pulses):
                    # Calculate pulse position (0-1)
                    position = ((frame * speed / 60) + i / num_pulses) % 1.0
                    
                    # Calculate point on quadratic Bezier curve
                    t = position
                    x = (1-t)**2 * start[0] + 2*(1-t)*t * control_x + t**2 * end[0]
                    y = (1-t)**2 * start[1] + 2*(1-t)*t * control_y + t**2 * end[1]
                    
                    # Calculate alpha (fade at endpoints)
                    alpha = min(position * 2, (1 - position) * 2) if self.fade_out else 0.8
                    alpha = max(0.2, alpha)
                    
                    # Create the pulse
                    pulse_radius = pulse_width * 2.5
                    pulse = Circle(
                        (x, y), pulse_radius,
                        facecolor=pulse_color,
                        edgecolor="none",
                        alpha=alpha,
                        zorder=15
                    )
                    
                    # Add glow effect
                    if self.glow_strength > 0:
                        pulse.set_path_effects([
                            path_effects.SimpleLineShadow(
                                offset=(0, 0),
                                shadow_color=self.glow_color,
                                alpha=alpha * 0.5,
                                rho=self.glow_strength
                            ),
                            path_effects.Normal()
                        ])
                    
                    # Add to axes and track
                    ax.add_patch(pulse)
                    self.pulses.append(pulse)
                    artists.append(pulse)
                    
                    # Add a trail (optional)
                    if np.random.random() < 0.5:  # Only add trails to some pulses
                        # Calculate point slightly behind on the curve
                        trail_t = max(0, t - 0.05)
                        trail_x = (1-trail_t)**2 * start[0] + 2*(1-trail_t)*trail_t * control_x + trail_t**2 * end[0]
                        trail_y = (1-trail_t)**2 * start[1] + 2*(1-trail_t)*trail_t * control_y + trail_t**2 * end[1]
                        
                        # Draw the trail
                        trail = ax.plot(
                            [trail_x, x], [trail_y, y],
                            color=pulse_color,
                            alpha=alpha * 0.6,
                            linewidth=pulse_width * 0.6,
                            solid_capstyle="round",
                            zorder=14
                        )[0]
                        
                        self.pulses.append(trail)
                        artists.append(trail)
        
        return artists


class ParticleFlowSystem:
    """Advanced particle system for flowing energy effects."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the particle flow system.
        
        Args:
            config: Configuration dictionary with particle parameters
        """
        self.enabled = config.get("enabled", True)
        self.base_color = config.get("color", "#00c2c7")
        self.density = config.get("density", 1.0)
        self.min_size = config.get("min_size", 0.5)
        self.max_size = config.get("max_size", 2.5)
        self.speed_factor = config.get("speed_factor", 1.0)
        self.glow = config.get("glow", True)
        self.glow_strength = config.get("glow_strength", 3.0)
        self.fade_length = config.get("fade_length", 0.3)
        self.turbulence = config.get("turbulence", 0.1)
        self.color_variance = config.get("color_variance", 0.2)
        
        # Animation state
        self.paths = []
        self.particles = []
        self.artists = []
        
        logger.debug(f"Initialized particle flow system with density {self.density}")
    
    def add_path(self, start: Tuple[float, float], end: Tuple[float, float], 
               curve: float = 0.2, color: str = None) -> None:
        """Add a path for particles to flow along.
        
        Args:
            start: Start point (x, y)
            end: End point (x, y)
            curve: Path curvature (0-1)
            color: Path color (overrides default if provided)
        """
        # Create path entry
        path = {
            "start": start,
            "end": end,
            "curve": curve,
            "color": color or self.base_color,
            "particles": []
        }
        
        # Add path
        self.paths.append(path)
        
        # Create initial particles
        path_length = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
        num_particles = int(path_length * self.density)
        
        # Generate particles
        for _ in range(num_particles):
            self._create_particle(len(self.paths) - 1)
        
        logger.debug(f"Added particle path from {start} to {end} with {num_particles} particles")
    
    def add_connection_paths(self, components: Dict[str, Any], connections: List[Dict[str, Any]]) -> None:
        """Add paths based on component connections.
        
        Args:
            components: Dictionary of components
            connections: List of connection configurations
        """
        for conn in connections:
            source_name = conn.get("source")
            target_name = conn.get("target")
            
            if source_name in components and target_name in components:
                source = components[source_name]
                target = components[target_name]
                
                # Extract centers
                if hasattr(source, "center"):
                    source_center = source.center
                elif isinstance(source, dict) and "center" in source:
                    source_center = source["center"]
                else:
                    logger.warning(f"Could not determine center for {source_name}")
                    continue
                
                if hasattr(target, "center"):
                    target_center = target.center
                elif isinstance(target, dict) and "center" in target:
                    target_center = target["center"]
                else:
                    logger.warning(f"Could not determine center for {target_name}")
                    continue
                
                # Add the path
                curve = conn.get("curve", 0.2)
                color = conn.get("color", self.base_color)
                self.add_path(source_center, target_center, curve, color)
        
        logger.debug(f"Added {len(connections)} connection paths")
    
    def _create_particle(self, path_idx: int) -> Dict[str, Any]:
        """Create a particle on the specified path.
        
        Args:
            path_idx: Path index
        
        Returns:
            Particle data
        """
        path = self.paths[path_idx]
        
        # Create random position
        pos = np.random.random()
        
        # Calculate size with some variation
        size = np.random.uniform(self.min_size, self.max_size)
        
        # Calculate speed (smaller particles move faster)
        speed_factor = np.random.uniform(0.8, 1.2) * self.speed_factor
        base_speed = (self.max_size - size) / (self.max_size - self.min_size) * 0.5 + 0.5
        speed = base_speed * speed_factor * 0.03
        
        # Calculate color with some variation
        base_color = path.get("color", self.base_color)
        
        # Create particle
        particle = {
            "path_idx": path_idx,
            "position": pos,
            "size": size,
            "speed": speed,
            "color": base_color,
            "offset": np.random.uniform(-self.turbulence, self.turbulence) if self.turbulence > 0 else 0
        }
        
        # Add to path's particles
        path["particles"].append(particle)
        
        return particle
    
    def _vary_color(self, color: str, amount: float = 0.1) -> str:
        """Create a slight variation of the given color.
        
        Args:
            color: Base color (hex string)
            amount: Amount of variation (0-1)
        
        Returns:
            Varied color (hex string)
        """
        if not color.startswith("#"):
            return color
        
        # Convert hex to RGB
        r = int(color[1:3], 16) / 255.0
        g = int(color[3:5], 16) / 255.0
        b = int(color[5:7], 16) / 255.0
        
        # Add random variation
        r = max(0, min(1, r + np.random.uniform(-amount, amount)))
        g = max(0, min(1, g + np.random.uniform(-amount, amount)))
        b = max(0, min(1, b + np.random.uniform(-amount, amount)))
        
        # Brighten slightly
        factor = 1.1
        r = min(1, r * factor)
        g = min(1, g * factor) 
        b = min(1, b * factor)
        
        # Convert back to hex
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
    
    def update(self, frame: int, params: Dict[str, Any], ax: plt.Axes) -> List:
        """Update the particle flow animation.
        
        Args:
            frame: Frame number
            params: Animation parameters
            ax: Matplotlib axes
        
        Returns:
            List of updated artists
        """
        if not self.enabled or not self.paths:
            return []
        
        # Clear existing artists
        for artist in self.artists:
            if isinstance(artist, plt.Line2D):
                artist.remove()
            elif isinstance(artist, plt.PathCollection):
                artist.remove()
        
        self.artists = []
        
        # Get parameters (or use defaults)
        density = params.get("density", self.density)
        color = params.get("color", self.base_color)
        glow = params.get("glow", self.glow)
        glow_strength = params.get("glow_strength", self.glow_strength)
        
        # Process each path
        for path_idx, path in enumerate(self.paths):
            start = path["start"]
            end = path["end"]
            curve = path["curve"]
            path_color = path.get("color", color)
            
            # Calculate control point for curved path
            if curve != 0:
                # Calculate the midpoint
                mid_x = (start[0] + end[0]) / 2
                mid_y = (start[1] + end[1]) / 2
                
                # Calculate normal vector
                dx = end[0] - start[0]
                dy = end[1] - start[1]
                dist = math.sqrt(dx**2 + dy**2)
                
                # Normalize and perpendicular
                nx = -dy / dist if dist > 0 else 0
                ny = dx / dist if dist > 0 else 0
                
                # Create control point
                control_x = mid_x + nx * curve * dist
                control_y = mid_y + ny * curve * dist
            else:
                control_x = (start[0] + end[0]) / 2
                control_y = (start[1] + end[1]) / 2
            
            # Update existing particles
            particles = path["particles"]
            
            for particle in particles:
                # Move the particle along the path
                particle["position"] = (particle["position"] + particle["speed"]) % 1.0
                
                # Calculate point on quadratic Bezier curve
                t = particle["position"]
                offset = particle.get("offset", 0)
                
                # Calculate base position on curve
                x = (1-t)**2 * start[0] + 2*(1-t)*t * control_x + t**2 * end[0]
                y = (1-t)**2 * start[1] + 2*(1-t)*t * control_y + t**2 * end[1]
                
                # Add perpendicular offset if turbulence is enabled
                if offset != 0:
                    # Calculate tangent vector
                    tx = 2*(1-t)*(control_x-start[0]) + 2*t*(end[0]-control_x)
                    ty = 2*(1-t)*(control_y-start[1]) + 2*t*(end[1]-control_y)
                    
                    # Normalize
                    tmag = math.sqrt(tx**2 + ty**2)
                    if tmag > 0:
                        tx /= tmag
                        ty /= tmag
                    
                    # Perpendicular
                    nx = -ty
                    ny = tx
                    
                    # Add offset
                    x += nx * offset
                    y += ny * offset
                
                # Draw the particle
                size = particle["size"] * 10  # Scale up for scatterplot
                particle_color = self._vary_color(particle["color"], self.color_variance)
                
                # Create scatter point
                scatter = ax.scatter(
                    x, y,
                    s=size,
                    color=particle_color,
                    alpha=0.8,
                    edgecolor="none",
                    zorder=15
                )
                
                self.artists.append(scatter)
                
                # Add trail if fade_length > 0
                if self.fade_length > 0:
                    # Calculate trail start position
                    trail_t = max(0, t - self.fade_length)
                    
                    # Calculate point on curve
                    trail_x = (1-trail_t)**2 * start[0] + 2*(1-trail_t)*trail_t * control_x + trail_t**2 * end[0]
                    trail_y = (1-trail_t)**2 * start[1] + 2*(1-trail_t)*trail_t * control_y + trail_t**2 * end[1]
                    
                    # Add offset (simpler for trail)
                    if offset != 0:
                        trail_x += nx * offset * 0.7  # Reduce offset for trail
                        trail_y += ny * offset * 0.7
                    
                    # Draw trail as a gradient line
                    if t > 0.01 and trail_t < t - 0.01:  # Only draw if there's enough distance
                        # Create gradient colors
                        n_points = 10
                        alphas = np.linspace(0.1, 0.7, n_points)
                        
                        # Create line segments
                        t_vals = np.linspace(trail_t, t, n_points)
                        points = np.array([
                            [(1-tt)**2 * start[0] + 2*(1-tt)*tt * control_x + tt**2 * end[0],
                             (1-tt)**2 * start[1] + 2*(1-tt)*tt * control_y + tt**2 * end[1]]
                            for tt in t_vals
                        ])
                        
                        # Create segments
                        segments = np.column_stack([points[:-1], points[1:]])
                        
                        # Create line collection
                        lc = LineCollection(
                            segments.reshape(-1, 2, 2),
                            color=particle_color,
                            alpha=alphas[:-1] * 0.8,
                            linewidth=particle["size"] * 0.7,
                            zorder=14
                        )
                        
                        if glow:
                            glow_effect = path_effects.SimpleLineShadow(
                                offset=(0, 0),
                                shadow_color=particle_color,
                                alpha=0.4,
                                rho=glow_strength
                            )
                            lc.set_path_effects([glow_effect, path_effects.Normal()])
                        
                        ax.add_collection(lc)
                        self.artists.append(lc)
            
            # Add new particles to maintain density
            path_length = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
            target_particles = int(path_length * density)
            
            if len(particles) < target_particles:
                # Add more particles
                for _ in range(target_particles - len(particles)):
                    self._create_particle(path_idx)
            elif len(particles) > target_particles:
                # Remove excess particles
                excess = len(particles) - target_particles
                path["particles"] = particles[excess:]
        
        return self.artists


class NestedFieldsAnimation:
    """Animated effects for nested conscious fields."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the nested fields animation.
        
        Args:
            config: Configuration dictionary with animation parameters
        """
        self.enabled = config.get("enabled", True)
        self.breathing = config.get("breathing", True)
        self.breathing_amplitude = config.get("breathing_amplitude", 0.05)
        self.breathing_frequency = config.get("breathing_frequency", 0.2)
        self.shimmer = config.get("shimmer", True)
        self.shimmer_count = config.get("shimmer_count", 5)
        self.shimmer_speed = config.get("shimmer_speed", 1.0)
        self.field_pulse = config.get("field_pulse", True)
        self.field_pulse_frequency = config.get("field_pulse_frequency", 0.1)
        
        # Animation state
        self.fields = []
        self.shimmers = []
        self.field_artists = []
        self.shimmer_artists = []
        
        logger.debug("Initialized nested fields animation")
    
    def add_fields(self, field_configs: Dict[str, Dict[str, Any]], center: Tuple[float, float]) -> None:
        """Add fields for animation.
        
        Args:
            field_configs: Dictionary of field configurations
            center: Center point for fields
        """
        # Sort fields by size (descending)
        sorted_fields = sorted(
            [(name, cfg) for name, cfg in field_configs.items()],
            key=lambda x: x[1].get("size", [0, 0])[0],
            reverse=True
        )
        
        # Create field entries
        for name, cfg in sorted_fields:
            # Get field parameters
            size = cfg.get("size", [30, 30])
            alpha = cfg.get("alpha", 0.4)
            color = cfg.get("color", "#42d7f5")
            
            # Create field entry
            field = {
                "name": name,
                "center": center,
                "size": size,
                "alpha": alpha,
                "color": color,
                "base_size": size,
                "scale_factor": 1.0
            }
            
            # Add to fields
            self.fields.append(field)
        
        logger.debug(f"Added {len(self.fields)} fields for animation")
    
    def update(self, frame: int, params: Dict[str, Any], ax: plt.Axes) -> List:
        """Update the nested fields animation.
        
        Args:
            frame: Frame number
            params: Animation parameters
            ax: Matplotlib axes
        
        Returns:
            List of updated artists
        """
        if not self.enabled or not self.fields:
            return []
        
        # Clear existing artists
        for artist in self.field_artists + self.shimmer_artists:
            artist.remove()
        
        self.field_artists = []
        self.shimmer_artists = []
        
        # Get parameters (or use defaults)
        breathing = params.get("breathing", self.breathing)
        breathing_amplitude = params.get("breathing_amplitude", self.breathing_amplitude)
        breathing_frequency = params.get("breathing_frequency", self.breathing_frequency)
        shimmer = params.get("shimmer", self.shimmer)
        field_pulse = params.get("field_pulse", self.field_pulse)
        
        # Calculate breathing phase
        breathing_phase = math.sin(frame * breathing_frequency) * breathing_amplitude
        
        # Process each field
        for i, field in enumerate(self.fields):
            center = field["center"]
            base_size = field["base_size"]
            color = field["color"]
            alpha = field["alpha"]
            
            # Calculate field pulse
            pulse_phase = 0
            if field_pulse:
                pulse_phase = math.sin(frame * self.field_pulse_frequency + i * math.pi / len(self.fields)) * 0.1
            
            # Calculate breathing effect
            if breathing:
                # Scale based on position in sequence
                scale_factor = 1.0 + breathing_phase * (1.0 - i / len(self.fields))
            else:
                scale_factor = 1.0
            
            # Apply pulse effect
            if field_pulse:
                scale_factor *= (1.0 + pulse_phase)
            
            # Update field scale
            field["scale_factor"] = scale_factor
            
            # Create ellipses for glass-morphism effect
            size_x, size_y = base_size
            
            # Create outer glow
            outer_glow = Ellipse(
                center, size_x * scale_factor * 1.05, size_y * scale_factor * 1.05,
                facecolor=color, edgecolor="none",
                alpha=alpha * 0.3, zorder=3
            )
            ax.add_patch(outer_glow)
            self.field_artists.append(outer_glow)
            
            # Create main field
            main_field = Ellipse(
                center, size_x * scale_factor, size_y * scale_factor,
                facecolor=color, edgecolor="none",
                alpha=alpha, zorder=3.1
            )
            ax.add_patch(main_field)
            self.field_artists.append(main_field)
            
            # Create inner glow
            inner_glow = Ellipse(
                center, size_x * scale_factor * 0.85, size_y * scale_factor * 0.85,
                facecolor=self._lighten_color(color, 0.3), edgecolor="none",
                alpha=alpha * 0.6, zorder=3.2
            )
            ax.add_patch(inner_glow)
            self.field_artists.append(inner_glow)
        
        # Create shimmer effects
        if shimmer:
            # Clear existing shimmers every few frames
            if frame % 10 == 0:
                self.shimmers = []
            
            # Add new shimmers
            if len(self.shimmers) < self.shimmer_count and np.random.random() < 0.3:
                # Choose a random field
                field_idx = np.random.randint(0, len(self.fields))
                field = self.fields[field_idx]
                
                # Create shimmer at random position on field
                angle = np.random.uniform(0, 2 * math.pi)
                size_x, size_y = field["base_size"]
                scale_factor = field["scale_factor"]
                dist = np.random.uniform(0.3, 0.9) * size_x * scale_factor / 2
                
                shimmer_x = field["center"][0] + math.cos(angle) * dist
                shimmer_y = field["center"][1] + math.sin(angle) * dist
                shimmer_size = np.random.uniform(1, 4)
                shimmer_alpha = np.random.uniform(0.2, 0.7)
                
                # Create shimmer
                shimmer = {
                    "position": (shimmer_x, shimmer_y),
                    "size": shimmer_size,
                    "alpha": shimmer_alpha,
                    "color": self._lighten_color(field["color"], 0.5),
                    "life": np.random.randint(5, 20),
                    "age": 0
                }
                
                self.shimmers.append(shimmer)
            
            # Draw and update shimmers
            new_shimmers = []
            for shimmer in self.shimmers:
                # Update age
                shimmer["age"] += 1
                
                # Draw shimmer if still alive
                if shimmer["age"] < shimmer["life"]:
                    # Calculate fade-out
                    life_factor = 1.0
                    if shimmer["age"] < 3:
                        life_factor = shimmer["age"] / 3
                    elif shimmer["age"] > shimmer["life"] - 3:
                        life_factor = (shimmer["life"] - shimmer["age"]) / 3
                    
                    # Draw shimmer
                    x, y = shimmer["position"]
                    size = shimmer["size"]
                    alpha = shimmer["alpha"] * life_factor
                    color = shimmer["color"]
                    
                    shimmer_circle = Ellipse(
                        (x, y), size, size,
                        facecolor="white", edgecolor="none",
                        alpha=alpha, zorder=3.5
                    )
                    ax.add_patch(shimmer_circle)
                    self.shimmer_artists.append(shimmer_circle)
                    
                    # Add to new list
                    new_shimmers.append(shimmer)
            
            # Update shimmers list
            self.shimmers = new_shimmers
        
        return self.field_artists + self.shimmer_artists
    
    def _lighten_color(self, color: str, amount: float = 0.5) -> str:
        """Lighten a color by the given amount.
        
        Args:
            color: Hex color string
            amount: Amount to lighten (0-1)
        
        Returns:
            Lightened hex color string
        """
        # Convert hex to RGB
        if not color.startswith("#"):
            return color
        
        r = int(color[1:3], 16) / 255.0
        g = int(color[3:5], 16) / 255.0
        b = int(color[5:7], 16) / 255.0
        
        # Lighten
        r = min(1.0, r + (1.0 - r) * amount)
        g = min(1.0, g + (1.0 - g) * amount)
        b = min(1.0, b + (1.0 - b) * amount)
        
        # Convert back to hex
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"


class AnimationSequencer:
    """Coordinates and synchronizes multiple animations."""
    
    def __init__(self, timeline: AnimationTimeline):
        """Initialize the animation sequencer.
        
        Args:
            timeline: Animation timeline
        """
        self.timeline = timeline
        self.animations = {}
        
        logger.debug("Initialized animation sequencer")
    
    def add_animation(self, name: str, animation_obj: Any) -> None:
        """Add an animation to the sequencer.
        
        Args:
            name: Animation name
            animation_obj: Animation object
        """
        self.animations[name] = animation_obj
        logger.debug(f"Added animation: {name}")
    
    def update(self, frame: int, params: Dict[str, Any], ax: plt.Axes) -> List:
        """Update all animations.
        
        Args:
            frame: Frame number
            params: Animation parameters
            ax: Matplotlib axes
        
        Returns:
            List of updated artists
        """
        all_artists = []
        
        # Process each animation
        for name, anim in self.animations.items():
            # Check if we have specific parameters for this animation
            anim_params = params.get(name, {})
            
            # Merge with global parameters
            merged_params = {**params, **anim_params}
            
            # Update the animation
            artists = anim.update(frame, merged_params, ax)
            all_artists.extend(artists)
        
        return all_artists


class AnimationExporter:
    """Handles exporting animations to different formats."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the animation exporter.
        
        Args:
            config: Configuration dictionary for the exporter
        """
        self.config = config or {}
        self.verbose = self.config.get("verbose", True)
        self.dpi = self.config.get("dpi", 300)
        
        # Check available writers
        self.available_writers = self._check_writers()
        
        logger.debug(f"Initialized animation exporter with available writers: {', '.join(self.available_writers)}")
    
    def _check_writers(self) -> List[str]:
        """Check available animation writers.
        
        Returns:
            List of available writer names
        """
        writers = []
        
        # Check Pillow (for GIF)
        try:
            from matplotlib.animation import PillowWriter
            writers.append("pillow")
        except ImportError:
            logger.debug("PillowWriter not available")
        
        # Check FFmpeg
        try:
            from matplotlib.animation import FFMpegWriter
            import subprocess
            
            # Check if ffmpeg is installed
            try:
                subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                writers.append("ffmpeg")
            except (subprocess.SubprocessError, FileNotFoundError):
                logger.debug("ffmpeg command not found")
        except ImportError:
            logger.debug("FFMpegWriter not available")
        
        # Check HTML
        try:
            from matplotlib.animation import HTMLWriter
            writers.append("html")
        except ImportError:
            logger.debug("HTMLWriter not available")
        
        return writers
    
    def export(self, anim: animation.Animation, output_path: str, fmt: str = None, **kwargs) -> str:
        """Export an animation to the specified format.
        
        Args:
            anim: Matplotlib animation
            output_path: Output file path
            fmt: Output format (auto-detected from extension if not provided)
            **kwargs: Additional parameters for the writer
        
        Returns:
            Path to the exported file
        
        Raises:
            ValueError: If the format is not supported or no suitable writer is available
        """
        # Determine format from extension if not provided
        if fmt is None:
            ext = Path(output_path).suffix.lower()
            if ext in (".gif"):
                fmt = "gif"
            elif ext in (".mp4", ".avi", ".mov"):
                fmt = "video"
            elif ext in (".html", ".htm"):
                fmt = "html"
            else:
                # Default to gif
                fmt = "gif"
                output_path = str(Path(output_path).with_suffix(".gif"))
        
        # Set DPI
        dpi = kwargs.get("dpi", self.dpi)
        
        # Export based on format
        if fmt == "gif":
            if "pillow" not in self.available_writers:
                raise ValueError("PillowWriter not available for GIF export")
            
            # Get writer parameters
            fps = kwargs.get("fps", 30)
            loop = kwargs.get("loop", 0)  # 0 = loop forever
            
            from matplotlib.animation import PillowWriter
            writer = PillowWriter(fps=fps, loop=loop)
            
            if self.verbose:
                print(f"Exporting animation to GIF: {output_path} (FPS: {fps}, DPI: {dpi})")
            
            anim.save(output_path, writer=writer, dpi=dpi)
        
        elif fmt == "video":
            if "ffmpeg" not in self.available_writers:
                raise ValueError("FFMpegWriter not available for video export")
            
            # Get writer parameters
            fps = kwargs.get("fps", 30)
            bitrate = kwargs.get("bitrate", 5000)
            codec = kwargs.get("codec", "h264")
            
            from matplotlib.animation import FFMpegWriter
            writer = FFMpegWriter(fps=fps, bitrate=bitrate, codec=codec)
            
            if self.verbose:
                print(f"Exporting animation to video: {output_path} (FPS: {fps}, DPI: {dpi}, Bitrate: {bitrate})")
            
            anim.save(output_path, writer=writer, dpi=dpi)
        
        elif fmt == "html":
            if "html" not in self.available_writers:
                raise ValueError("HTMLWriter not available for HTML export")
            
            # Get writer parameters
            fps = kwargs.get("fps", 30)
            embed_frames = kwargs.get("embed_frames", True)
            default_mode = kwargs.get("default_mode", "loop")
            
            from matplotlib.animation import HTMLWriter
            writer = HTMLWriter(fps=fps, embed_frames=embed_frames, default_mode=default_mode)
            
            if self.verbose:
                print(f"Exporting animation to HTML: {output_path} (FPS: {fps})")
            
            anim.save(output_path, writer=writer, dpi=dpi)
        
        else:
            raise ValueError(f"Unsupported export format: {fmt}")
        
        return output_path