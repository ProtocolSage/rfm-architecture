"""Advanced visual effects for RFM visualization."""
from __future__ import annotations

import logging
import math
from typing import Dict, Any, List, Tuple, Optional, Union

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, to_rgba
from matplotlib.collections import LineCollection
from matplotlib.patches import FancyBboxPatch, Shadow, Ellipse
from matplotlib.patheffects import withStroke, Stroke, SimplePatchShadow, Normal
import matplotlib.patheffects as path_effects
from scipy.ndimage import gaussian_filter

logger = logging.getLogger(__name__)


class GlowEffect:
    """Creates ethereal glow effects around visual elements."""
    
    def __init__(self, color: str, alpha: float = 0.7, strength: float = 3.0):
        """Initialize the glow effect.
        
        Args:
            color: Base color for the glow
            alpha: Maximum opacity of the glow
            strength: Intensity of the glow effect
        """
        self.color = color
        self.alpha = alpha
        self.strength = strength
        
        # Convert color to RGBA
        self.rgba = to_rgba(color, alpha=1.0)
        
        logger.debug(f"Initialized glow effect with color {color}, strength {strength}")
    
    def apply_to_text(self, text_obj: plt.Text) -> None:
        """Apply glow effect to a text object.
        
        Args:
            text_obj: Matplotlib text object
        """
        # Create a sequence of path effects for the text
        effects = [
            # Main text
            Normal(),
            # Outer glow
            withStroke(linewidth=self.strength+2, foreground=self.color, alpha=self.alpha * 0.2),
            # Middle glow
            withStroke(linewidth=self.strength+1, foreground=self.color, alpha=self.alpha * 0.4),
            # Inner glow
            withStroke(linewidth=self.strength, foreground=self.color, alpha=self.alpha)
        ]
        
        # Apply the effects
        text_obj.set_path_effects(effects)
        
        logger.debug("Applied glow effect to text")
    
    def apply_to_patch(self, patch_obj: plt.Patch) -> None:
        """Apply glow effect to a patch object.
        
        Args:
            patch_obj: Matplotlib patch object
        """
        # Create shadow effect with the glow color
        shadow = SimplePatchShadow(
            offset=(0, 0),
            shadow_rgbFace=self.rgba[:3],
            alpha=self.alpha,
            rho=self.strength
        )
        
        # Apply the effects
        patch_obj.set_path_effects([Normal(), shadow])
        
        logger.debug("Applied glow effect to patch")


class CosmicGradient:
    """Creates deep space-inspired gradient backgrounds."""
    
    # Predefined cosmic color palettes
    PALETTES = {
        "nebula": ["#0a0014", "#1e0443", "#4c0772", "#700a9c", "#b93dff"],
        "stellar": ["#000327", "#00084d", "#001b94", "#0059d6", "#6ab4ff"],
        "cosmic": ["#000000", "#0d0221", "#220c56", "#3a1264", "#541873"],
        "aurora": ["#000809", "#004243", "#008080", "#00caca", "#97fff0"],
        "sunset": ["#090005", "#2d000c", "#6b002a", "#bc005c", "#ff63a5"]
    }
    
    def __init__(self, palette_name: str = "nebula", custom_colors: Optional[List[str]] = None,
                 alpha: float = 0.8, blend_mode: str = "soft"):
        """Initialize the cosmic gradient.
        
        Args:
            palette_name: Name of predefined palette or "custom"
            custom_colors: List of colors for custom palette
            alpha: Opacity of the gradient
            blend_mode: Blend mode ("soft", "hard", "glow")
        """
        self.alpha = alpha
        self.blend_mode = blend_mode
        
        # Select color palette
        if custom_colors:
            self.colors = custom_colors
        else:
            if palette_name not in self.PALETTES:
                logger.warning(f"Unknown palette '{palette_name}', using 'nebula'")
                palette_name = "nebula"
            self.colors = self.PALETTES[palette_name]
        
        # Create colormap
        self.cmap = LinearSegmentedColormap.from_list(
            f"cosmic_{palette_name}", self.colors, N=256
        )
        
        logger.debug(f"Initialized cosmic gradient with palette '{palette_name}'")
    
    def apply_background(self, ax: plt.Axes, style: str = "radial") -> None:
        """Apply cosmic gradient background to axes.
        
        Args:
            ax: Matplotlib axes
            style: Gradient style ("radial", "linear", "corner", "spiral")
        """
        # Get axes dimensions
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        width = xmax - xmin
        height = ymax - ymin
        center_x = (xmin + xmax) / 2
        center_y = (ymin + ymax) / 2
        
        # Create gradient mesh
        nx, ny = 500, 400
        x = np.linspace(xmin, xmax, nx)
        y = np.linspace(ymin, ymax, ny)
        X, Y = np.meshgrid(x, y)
        
        # Generate gradient values based on style
        if style == "radial":
            # Radial gradient from center
            radius = max(width, height) / 2
            dist = np.sqrt((X - center_x)**2 + (Y - center_y)**2) / radius
            Z = dist
        
        elif style == "linear":
            # Linear gradient from bottom to top
            Z = (Y - ymin) / height
        
        elif style == "corner":
            # Gradient from bottom-left to top-right
            Z = (X - xmin) / width * 0.5 + (Y - ymin) / height * 0.5
        
        elif style == "spiral":
            # Spiral gradient
            theta = np.arctan2(Y - center_y, X - center_x)
            dist = np.sqrt((X - center_x)**2 + (Y - center_y)**2) / max(width, height) * 2
            Z = (theta + np.pi) / (2 * np.pi) + dist
            Z = Z % 1.0
        
        else:
            logger.warning(f"Unknown gradient style '{style}', using 'radial'")
            radius = max(width, height) / 2
            dist = np.sqrt((X - center_x)**2 + (Y - center_y)**2) / radius
            Z = dist
        
        # Draw the gradient
        ax.imshow(
            Z,
            extent=[xmin, xmax, ymin, ymax],
            origin='lower',
            cmap=self.cmap,
            alpha=self.alpha,
            aspect='auto',
            zorder=0
        )
        
        logger.debug(f"Applied cosmic gradient background with style '{style}'")
    
    def apply_to_patch(self, patch: plt.Patch, style: str = "vertical") -> None:
        """Apply gradient fill to a patch.
        
        Args:
            patch: Matplotlib patch
            style: Gradient style ("vertical", "horizontal", "radial")
        """
        # Create array of RGBA colors for the gradient
        n_colors = 256
        colors = self.cmap(np.linspace(0, 1, n_colors))
        
        # Adjust the alpha
        colors[:, 3] = self.alpha
        
        # Create a custom colormap for this patch
        patch_cmap = LinearSegmentedColormap.from_list(
            "patch_gradient", colors, N=n_colors
        )
        
        # Set the face color to the first color in the gradient
        # (the actual gradient will be applied by the renderer)
        patch.set_facecolor(colors[0])
        
        # Use the set_* method specific to the patch type if available
        if hasattr(patch, "set_cmap"):
            patch.set_cmap(patch_cmap)
        
        logger.debug(f"Applied gradient to patch with style '{style}'")


class ParticleSystem:
    """Creates flowing particle effects along paths."""
    
    def __init__(self, color: str = "#00c2c7", density: float = 0.5, 
                 speed: float = 1.0, size_range: Tuple[float, float] = (0.5, 2.0),
                 fade_length: float = 0.3, glow: bool = True):
        """Initialize the particle system.
        
        Args:
            color: Base color for particles
            density: Number of particles per unit length
            speed: Animation speed factor
            size_range: Range of particle sizes (min, max)
            fade_length: Length of particle trails (0-1)
            glow: Whether to add glow effect to particles
        """
        self.color = color
        self.density = density
        self.speed = speed
        self.size_range = size_range
        self.fade_length = fade_length
        self.glow = glow
        self.particles = []
        self.paths = []
        
        # Convert color to RGBA
        self.rgba = to_rgba(color, alpha=1.0)
        
        # Create colormap for particle trails
        trail_colors = [(0, 0, 0, 0), self.rgba]
        self.trail_cmap = LinearSegmentedColormap.from_list(
            "particle_trail", trail_colors, N=100
        )
        
        logger.debug(f"Initialized particle system with color {color}, density {density}")
    
    def add_path(self, start: Tuple[float, float], end: Tuple[float, float], 
                 curve: float = 0.0) -> None:
        """Add a path for particles to flow along.
        
        Args:
            start: Start point (x, y)
            end: End point (x, y)
            curve: Curvature of the path (-1.0 to 1.0)
        """
        # Store the path
        self.paths.append((start, end, curve))
        
        # Generate initial particles
        path_length = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
        num_particles = int(path_length * self.density)
        
        # Create particles with random positions along the path
        for _ in range(num_particles):
            pos = np.random.random()  # Position along path (0-1)
            size = np.random.uniform(*self.size_range)
            self.particles.append({
                "path_idx": len(self.paths) - 1,
                "position": pos,
                "size": size,
                "speed": np.random.uniform(0.8, 1.2) * self.speed * 0.01
            })
        
        logger.debug(f"Added path with {num_particles} particles")
    
    def draw(self, ax: plt.Axes, frame: int = 0) -> List:
        """Draw the particle system.
        
        Args:
            ax: Matplotlib axes
            frame: Animation frame number
        
        Returns:
            List of artists for animation
        """
        artists = []
        
        # Update particle positions
        for particle in self.particles:
            # Move the particle along its path
            particle["position"] = (particle["position"] + particle["speed"]) % 1.0
            
            # Get the path for this particle
            start, end, curve = self.paths[particle["path_idx"]]
            
            # Calculate particle position
            if curve == 0:
                # Linear path
                x = start[0] + (end[0] - start[0]) * particle["position"]
                y = start[1] + (end[1] - start[1]) * particle["position"]
            else:
                # Curved path (simple bezier)
                t = particle["position"]
                # Calculate control point
                mid_x = (start[0] + end[0]) / 2
                mid_y = (start[1] + end[1]) / 2
                normal_x = -(end[1] - start[1])
                normal_y = end[0] - start[0]
                length = math.sqrt(normal_x**2 + normal_y**2)
                normal_x /= length
                normal_y /= length
                cp_x = mid_x + normal_x * curve * length * 0.5
                cp_y = mid_y + normal_y * curve * length * 0.5
                
                # Quadratic Bezier formula
                x = (1-t)**2 * start[0] + 2*(1-t)*t * cp_x + t**2 * end[0]
                y = (1-t)**2 * start[1] + 2*(1-t)*t * cp_y + t**2 * end[1]
            
            # Draw the particle with trail
            if self.fade_length > 0:
                # Calculate trail start position
                trail_t = max(0, particle["position"] - self.fade_length)
                if curve == 0:
                    # Linear path
                    trail_x = start[0] + (end[0] - start[0]) * trail_t
                    trail_y = start[1] + (end[1] - start[1]) * trail_t
                else:
                    # Curved path
                    trail_x = (1-trail_t)**2 * start[0] + 2*(1-trail_t)*trail_t * cp_x + trail_t**2 * end[0]
                    trail_y = (1-trail_t)**2 * start[1] + 2*(1-trail_t)*trail_t * cp_y + trail_t**2 * end[1]
                
                # Draw trail as a line with gradient
                line = ax.plot(
                    [trail_x, x], [trail_y, y],
                    color=self.color,
                    alpha=0.6,
                    linewidth=particle["size"] * 0.7,
                    solid_capstyle='round',
                    zorder=3
                )[0]
                
                if self.glow:
                    line.set_path_effects([
                        path_effects.SimpleLineShadow(
                            offset=(0, 0),
                            shadow_color=self.color,
                            alpha=0.3,
                            rho=3
                        ),
                        path_effects.Normal()
                    ])
                
                artists.append(line)
            
            # Draw the particle
            particle_dot = ax.scatter(
                x, y,
                s=particle["size"] * 10,
                color=self.color,
                alpha=0.8,
                edgecolor='none',
                zorder=4
            )
            
            if self.glow:
                # Add glow effect to particle
                particle_dot.set_path_effects([
                    path_effects.SimpleLineShadow(
                        offset=(0, 0),
                        shadow_color=self.color,
                        alpha=0.5,
                        rho=5
                    ),
                    path_effects.Normal()
                ])
            
            artists.append(particle_dot)
        
        logger.debug(f"Drew {len(self.particles)} particles")
        return artists


class DepthEffect:
    """Creates depth and dimension effects for visualizations."""
    
    def __init__(self, shadow_color: str = "#000000", shadow_alpha: float = 0.3,
                 elevation: float = 3.0, blur_radius: float = 5.0):
        """Initialize the depth effect.
        
        Args:
            shadow_color: Color of shadows
            shadow_alpha: Opacity of shadows
            elevation: Height of elements above the "ground"
            blur_radius: Blur amount for shadows and DOF effects
        """
        self.shadow_color = shadow_color
        self.shadow_alpha = shadow_alpha
        self.elevation = elevation
        self.blur_radius = blur_radius
        
        logger.debug(f"Initialized depth effect with elevation {elevation}")
    
    def add_shadow(self, patch: plt.Patch, ax: plt.Axes, 
                   offset: Tuple[float, float] = (2, -2)) -> plt.Patch:
        """Add a shadow to a patch.
        
        Args:
            patch: Matplotlib patch
            ax: Matplotlib axes
            offset: Shadow offset (dx, dy)
        
        Returns:
            Shadow patch
        """
        # Create a shadow for the patch
        shadow = Shadow(
            patch,
            ox=offset[0],
            oy=offset[1],
            alpha=self.shadow_alpha
        )
        
        # Add the shadow to the axes
        ax.add_patch(shadow)
        
        logger.debug("Added shadow to patch")
        return shadow
    
    def apply_depth_of_field(self, ax: plt.Axes, focal_point: Tuple[float, float], 
                           focal_range: float, max_blur: float) -> None:
        """Apply depth of field blur effect.
        
        Args:
            ax: Matplotlib axes
            focal_point: Center of focus (x, y)
            focal_range: Range of sharp focus
            max_blur: Maximum blur amount
        """
        # This is a simplified concept - in a real implementation,
        # we would need to capture the rendered image, apply
        # depth-dependent blur, and display the result
        logger.debug("Applied depth of field effect")
    
    def create_parallax_layer(self, ax: plt.Axes, content_func, depth: float,
                           offset_range: Tuple[float, float] = (-5, 5)) -> None:
        """Create a parallax layer that moves at different rates.
        
        Args:
            ax: Matplotlib axes
            content_func: Function to draw content on the layer
            depth: Depth value (0-1, 0=closest, 1=furthest)
            offset_range: Range of motion (-dx to +dx, -dy to +dy)
        """
        # Create a new set of axes for this layer
        layer_ax = ax.figure.add_axes(
            ax.get_position(),
            frameon=False,
            sharex=ax,
            sharey=ax
        )
        
        # Draw content on the layer
        content_func(layer_ax)
        
        logger.debug(f"Created parallax layer at depth {depth}")


class MathematicalBeauty:
    """Creates mathematically beautiful patterns and structures."""
    
    GOLDEN_RATIO = 1.618033988749895
    
    def __init__(self):
        """Initialize the mathematical beauty effects."""
        # Generate Fibonacci sequence
        self.fibonacci = [0, 1]
        for i in range(2, 20):
            self.fibonacci.append(self.fibonacci[i-1] + self.fibonacci[i-2])
        
        logger.debug("Initialized mathematical beauty effects")
    
    def draw_golden_spiral(self, ax: plt.Axes, center: Tuple[float, float],
                         max_radius: float, num_turns: float = 4.0,
                         line_width: float = 1.0, color: str = "#b086ff",
                         alpha: float = 0.4) -> None:
        """Draw a golden spiral overlay.
        
        Args:
            ax: Matplotlib axes
            center: Center point (x, y)
            max_radius: Maximum radius of the spiral
            num_turns: Number of turns in the spiral
            line_width: Width of the spiral line
            color: Color of the spiral
            alpha: Opacity of the spiral
        """
        # Generate points along the spiral
        theta = np.linspace(0, num_turns * 2 * np.pi, 1000)
        radius = max_radius * np.exp(-theta / (2 * np.pi / np.log(self.GOLDEN_RATIO)))
        x = center[0] + radius * np.cos(theta)
        y = center[1] + radius * np.sin(theta)
        
        # Draw the spiral
        ax.plot(x, y, linewidth=line_width, color=color, alpha=alpha, zorder=1)
        
        logger.debug(f"Drew golden spiral with {num_turns} turns")
    
    def draw_fibonacci_grid(self, ax: plt.Axes, origin: Tuple[float, float],
                          size: float, levels: int = 5,
                          line_width: float = 0.5, color: str = "#b086ff",
                          alpha: float = 0.2) -> None:
        """Draw a Fibonacci grid/rectangles.
        
        Args:
            ax: Matplotlib axes
            origin: Bottom-left corner (x, y)
            size: Size of the largest square
            levels: Number of subdivisions
            line_width: Width of the grid lines
            color: Color of the grid
            alpha: Opacity of the grid
        """
        # Start with a square of size "size"
        squares = [(origin[0], origin[1], size, size)]
        
        # Generate the sequence of squares
        x, y = origin
        width = height = size
        
        for i in range(levels):
            if i % 2 == 0:
                # Add square to the left
                new_width = height * (1 / self.GOLDEN_RATIO)
                x -= new_width
                squares.append((x, y, new_width, height))
                width = new_width
            else:
                # Add square below
                new_height = width * (1 / self.GOLDEN_RATIO)
                y -= new_height
                squares.append((x, y, width, new_height))
                height = new_height
        
        # Draw the squares
        for x, y, w, h in squares:
            rect = plt.Rectangle(
                (x, y), w, h,
                fill=False,
                edgecolor=color,
                linewidth=line_width,
                alpha=alpha,
                zorder=1
            )
            ax.add_patch(rect)
        
        logger.debug(f"Drew Fibonacci grid with {levels} levels")
    
    def apply_symmetry(self, ax: plt.Axes, content_func, 
                        center: Tuple[float, float],
                        symmetry_type: str = "radial",
                        num_reflections: int = 4) -> None:
        """Apply symmetry to visual elements.
        
        Args:
            ax: Matplotlib axes
            content_func: Function to draw content
            center: Center of symmetry (x, y)
            symmetry_type: Type of symmetry ("radial", "bilateral", "translational")
            num_reflections: Number of reflections (for radial symmetry)
        """
        if symmetry_type == "radial":
            # Draw the content at different rotations
            for i in range(num_reflections):
                angle = i * 2 * np.pi / num_reflections
                # Here we would transform the axes, draw content, and restore
                # For a full implementation, this would use transforms
                pass
        elif symmetry_type == "bilateral":
            # Draw the content and its mirror image
            # Again, would use transforms in a full implementation
            pass
        
        logger.debug(f"Applied {symmetry_type} symmetry with {num_reflections} reflections")
    
    def create_fractal_recursion(self, ax: plt.Axes, base_func, 
                               center: Tuple[float, float],
                               size: float, depth: int = 3,
                               scale_factor: float = 0.5) -> None:
        """Create fractal recursion visualization.
        
        Args:
            ax: Matplotlib axes
            base_func: Function to draw the base shape
            center: Center point (x, y)
            size: Size of the largest instance
            depth: Recursion depth
            scale_factor: Scale factor between recursion levels
        """
        def recursive_draw(c, s, d):
            if d <= 0:
                return
            
            # Draw the current instance
            base_func(ax, c, s)
            
            # Draw smaller instances
            new_size = s * scale_factor
            offsets = [
                (s/2, 0),   # right
                (-s/2, 0),  # left
                (0, s/2),   # top
                (0, -s/2)   # bottom
            ]
            
            for dx, dy in offsets:
                new_center = (c[0] + dx, c[1] + dy)
                recursive_draw(new_center, new_size, d - 1)
        
        # Start the recursion
        recursive_draw(center, size, depth)
        
        logger.debug(f"Created fractal recursion with depth {depth}")


class ConceptualVisualizer:
    """Creates visual metaphors for abstract AI concepts."""
    
    def __init__(self):
        """Initialize the conceptual visualizer."""
        logger.debug("Initialized conceptual visualizer")
    
    def draw_self_reference_loop(self, ax: plt.Axes, center: Tuple[float, float],
                               radius: float, line_width: float = 2.0,
                               color: str = "#00c2c7", alpha: float = 0.8) -> None:
        """Draw a self-reference loop.
        
        Args:
            ax: Matplotlib axes
            center: Center point (x, y)
            radius: Radius of the loop
            line_width: Width of the loop line
            color: Color of the loop
            alpha: Opacity of the loop
        """
        # Create a spiral that curls inward
        theta = np.linspace(0, 6 * np.pi, 1000)
        spiral_radius = radius * (1 - theta / (6 * np.pi) * 0.5)
        x = center[0] + spiral_radius * np.cos(theta)
        y = center[1] + spiral_radius * np.sin(theta)
        
        # Draw the spiral with an arrowhead at the end
        arrow = ax.plot(
            x, y,
            linewidth=line_width,
            color=color,
            alpha=alpha,
            zorder=5
        )[0]
        
        # Add arrowhead at the end of the spiral
        # For a full implementation, would add a custom FancyArrowPatch
        
        logger.debug("Drew self-reference loop")
    
    def draw_emergence_pattern(self, ax: plt.Axes, center: Tuple[float, float],
                             size: float, num_elements: int = 50,
                             small_color: str = "#4287f5",
                             large_color: str = "#b086ff") -> None:
        """Draw an emergence pattern visualization.
        
        Args:
            ax: Matplotlib axes
            center: Center point (x, y)
            size: Size of the pattern
            num_elements: Number of small elements
            small_color: Color of small elements
            large_color: Color of the emergent pattern
        """
        # Draw small elements
        for i in range(num_elements):
            # Calculate position with some pattern (e.g., circular)
            angle = i * 2 * np.pi / num_elements
            radius = size * 0.8
            x = center[0] + radius * np.cos(angle)
            y = center[1] + radius * np.sin(angle)
            
            # Draw small element
            ax.scatter(
                x, y,
                s=30,
                color=small_color,
                alpha=0.7,
                zorder=5
            )
        
        # Draw emergent pattern (here a simple circle)
        ax.add_patch(plt.Circle(
            center, size * 0.9,
            fill=False,
            edgecolor=large_color,
            linewidth=2.0,
            alpha=0.6,
            zorder=6
        ))
        
        logger.debug(f"Drew emergence pattern with {num_elements} elements")
    
    def draw_integration_network(self, ax: plt.Axes, components: Dict[str, Any],
                              center: Tuple[float, float], radius: float,
                              line_color: str = "#00c2c7", alpha: float = 0.3) -> None:
        """Draw an integration network showing how components unify.
        
        Args:
            ax: Matplotlib axes
            components: Dictionary of components
            center: Center point (x, y)
            radius: Radius of the integration network
            line_color: Color of connection lines
            alpha: Opacity of connection lines
        """
        # Draw lines from each component to the center
        for name, component in components.items():
            comp_center = component.center
            
            # Draw a curved line from component to center
            # For a full implementation, would use a proper Bezier curve
            ax.plot(
                [comp_center[0], center[0]],
                [comp_center[1], center[1]],
                color=line_color,
                alpha=alpha,
                linewidth=1.0,
                zorder=2
            )
        
        logger.debug(f"Drew integration network with {len(components)} components")