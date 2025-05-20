"""Visual components for RFM visualization."""
from __future__ import annotations

import logging
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyArrowPatch
from matplotlib.patheffects import withStroke
from matplotlib.collections import LineCollection

logger = logging.getLogger(__name__)


class Component:
    """Base class for RFM components with enhanced visual effects."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize the component with the given configuration.
        
        Args:
            name: Component name
            config: Configuration dictionary with component parameters
        """
        self.name = name
        self.center = config.get("center", [50, 50])
        self.size = config.get("size", [20, 15])
        self.color = config.get("color", "#4287f5")
        self.label = config.get("label", name)
        self.description = config.get("description", "")
        self.zorder = config.get("zorder", 5)
        self.border_color = "#fdfdff"
        self.border_width = 1.5
        
        # Enhanced visual properties
        self.glass_effect = config.get("glass_effect", True)
        self.inner_glow = config.get("inner_glow", True)
        self.pulse_rate = config.get("pulse_rate", 0.0)  # 0 means no pulsing
        self.highlight = config.get("highlight", False)
        
        # Generate lighter color for gradient effect
        self.lighter_color = self._lighten_color(self.color, 0.3)
        
        logger.debug(f"Initialized component {name} at {self.center}")
    
    def _lighten_color(self, color: str, amount: float = 0.5) -> str:
        """Lighten a color by the given amount.
        
        Args:
            color: Hex color string
            amount: Amount to lighten (0-1)
        
        Returns:
            Lightened hex color string
        """
        # Convert hex to RGB
        color = color.lstrip('#')
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        
        # Lighten
        r = min(255, int(r + (255 - r) * amount))
        g = min(255, int(g + (255 - g) * amount))
        b = min(255, int(b + (255 - b) * amount))
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def draw(self, ax: plt.Axes) -> None:
        """Draw the component on the given axes with enhanced visual effects.
        
        Args:
            ax: Matplotlib axes to draw on
        """
        width, height = self.size
        
        # Create glass-morphism effect
        if self.glass_effect:
            # Add a larger, blurred ellipse below for the "glass" effect
            blur_ellipse = Ellipse(
                self.center, width * 1.05, height * 1.05,
                facecolor=self.lighter_color, edgecolor='none',
                alpha=0.2, zorder=self.zorder - 0.1
            )
            ax.add_patch(blur_ellipse)
        
        # Draw the main component ellipse
        ellipse = Ellipse(
            self.center, width, height,
            facecolor=self.color, edgecolor=self.border_color,
            linewidth=self.border_width, alpha=0.9, zorder=self.zorder
        )
        ax.add_patch(ellipse)
        
        # Add inner glow
        if self.inner_glow:
            # Add a smaller, brighter ellipse inside for "inner glow"
            glow_ellipse = Ellipse(
                self.center, width * 0.7, height * 0.7,
                facecolor=self.lighter_color, edgecolor='none',
                alpha=0.3, zorder=self.zorder + 0.1
            )
            ax.add_patch(glow_ellipse)
        
        # Add highlight if enabled
        if self.highlight:
            # Add a small highlight circle
            highlight_x = self.center[0] - width * 0.2
            highlight_y = self.center[1] + height * 0.2
            highlight = Ellipse(
                (highlight_x, highlight_y), width * 0.1, height * 0.1,
                facecolor='white', edgecolor='none',
                alpha=0.5, zorder=self.zorder + 0.2
            )
            ax.add_patch(highlight)
        
        # Draw the label with enhanced style
        ax.text(
            self.center[0], self.center[1], self.label,
            ha='center', va='center', color='white', fontsize=9,
            fontweight='bold', zorder=self.zorder + 1
        )
        
        logger.debug(f"Drew component {self.name} with enhanced visual effects")
    
    def connect_to(self, target: Component, ax: plt.Axes, config: Dict[str, Any]) -> None:
        """Connect this component to another component with an enhanced arrow.
        
        Args:
            target: Target component
            ax: Matplotlib axes to draw on
            config: Connection configuration
        """
        # Get connection parameters
        curve = config.get("curve", 0.1)
        width = config.get("width", 2)
        color = config.get("color", "#2c3e50")
        bidirectional = config.get("bidirectional", False)
        glow = config.get("glow", True)
        
        # Create the arrow with enhanced style
        arrow = FancyArrowPatch(
            self.center, target.center,
            arrowstyle='-|>' if not bidirectional else '<|-|>',
            connectionstyle=f'arc3,rad={curve}',
            linewidth=width, color=color,
            alpha=0.8,  # Slightly transparent
            zorder=min(self.zorder, target.zorder) - 1
        )
        
        # Add glow effect to the arrow
        if glow:
            arrow.set_path_effects([
                withStroke(linewidth=width+2, foreground=color, alpha=0.2),
                withStroke(linewidth=width+1, foreground=color, alpha=0.1)
            ])
        
        ax.add_patch(arrow)
        
        logger.debug(f"Connected {self.name} to {target.name} with enhanced arrow")


class NestedConsciousFields:
    """Nested conscious fields visualization with glass-morphism effect."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the nested conscious fields with the given configuration.
        
        Args:
            config: Configuration dictionary with conscious fields parameters
        """
        self.fields = config
        self.use_glass_effect = True
        self.use_blur = True
        self.add_shimmer = True
        
        logger.debug(f"Initialized {len(self.fields)} nested conscious fields")
    
    def _lighten_color(self, color: str, amount: float = 0.5) -> str:
        """Lighten a color by the given amount.
        
        Args:
            color: Hex color string
            amount: Amount to lighten (0-1)
        
        Returns:
            Lightened hex color string
        """
        # Convert hex to RGB
        color = color.lstrip('#')
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        
        # Lighten
        r = min(255, int(r + (255 - r) * amount))
        g = min(255, int(g + (255 - g) * amount))
        b = min(255, int(b + (255 - b) * amount))
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def draw(self, ax: plt.Axes, center_component: Component) -> None:
        """Draw the nested conscious fields around the center component with glass-morphism effect.
        
        Args:
            ax: Matplotlib axes to draw on
            center_component: Center component (usually CIF)
        """
        center = center_component.center
        
        # Draw each field from largest to smallest
        for name, field_config in reversed(list(self.fields.items())):
            # Get field parameters
            size = field_config.get("size", [30, 30])
            alpha = field_config.get("alpha", 0.4)
            color = field_config.get("color", "#42d7f5")
            
            # Create glass morphism effect
            if self.use_glass_effect:
                # Add a slightly larger, blurred ellipse for the outer glow
                outer_glow = Ellipse(
                    center, size[0] * 1.05, size[1] * 1.05,
                    facecolor=color, edgecolor='none',
                    alpha=alpha * 0.3, zorder=3
                )
                ax.add_patch(outer_glow)
                
                # Add a very faint, larger halo
                halo = Ellipse(
                    center, size[0] * 1.15, size[1] * 1.15,
                    facecolor=color, edgecolor='none',
                    alpha=alpha * 0.1, zorder=2.9
                )
                ax.add_patch(halo)
            
            # Create and draw the main field
            field = Ellipse(
                center, size[0], size[1],
                facecolor=color, edgecolor='none',
                alpha=alpha, zorder=3
            )
            ax.add_patch(field)
            
            # Add inner glow effect
            inner_glow = Ellipse(
                center, size[0] * 0.85, size[1] * 0.85,
                facecolor=self._lighten_color(color, 0.3), edgecolor='none',
                alpha=alpha * 0.6, zorder=3.1
            )
            ax.add_patch(inner_glow)
            
            # Add shimmer highlights (small ellipses with high brightness)
            if self.add_shimmer:
                for i in range(3):  # Add a few shimmer spots
                    # Random position near the edge of the field
                    angle = np.random.uniform(0, 2 * np.pi)
                    dist = np.random.uniform(0.3, 0.8) * size[0] / 2
                    shimmer_x = center[0] + np.cos(angle) * dist
                    shimmer_y = center[1] + np.sin(angle) * dist
                    
                    # Random size for the shimmer
                    shimmer_size = np.random.uniform(1, 3)
                    
                    # Add the shimmer highlight
                    shimmer = Ellipse(
                        (shimmer_x, shimmer_y), shimmer_size, shimmer_size,
                        facecolor='white', edgecolor='none',
                        alpha=np.random.uniform(0.1, 0.4), zorder=3.2
                    )
                    ax.add_patch(shimmer)
        
        logger.debug("Drew nested conscious fields with glass-morphism effect")


class PhiMetric:
    """Phi metric (integrated information) visualization with enhanced effects."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Phi metric with the given configuration.
        
        Args:
            config: Configuration dictionary with Phi metric parameters
        """
        self.display = config.get("display", True)
        self.position = config.get("position", [60, 55])
        self.formula = config.get("formula", True)
        self.font_size = config.get("font_size", 10)
        self.color = config.get("color", "#b086ff")
        self.phi_value = config.get("value", 0.85)
        self.show_aura = config.get("show_aura", True)
        self.show_pulse = config.get("show_pulse", True)
        self.show_wave = config.get("show_wave", True)
        
        logger.debug("Initialized enhanced Phi metric")
    
    def draw(self, ax: plt.Axes, cif_component: Component) -> None:
        """Draw the Phi metric annotation with enhanced visual effects.
        
        Args:
            ax: Matplotlib axes to draw on
            cif_component: CIF component (for reference)
        """
        if not self.display:
            return
        
        # Get position
        x, y = self.position
        
        # Draw aura/glow background
        if self.show_aura:
            # Add a subtle circular aura
            aura_radius = self.font_size * 1.5
            aura = Ellipse(
                (x, y), aura_radius, aura_radius,
                facecolor=self.color, edgecolor='none',
                alpha=0.1, zorder=9
            )
            ax.add_patch(aura)
            
            # Add a smaller, brighter inner aura
            inner_aura = Ellipse(
                (x, y), aura_radius * 0.7, aura_radius * 0.7,
                facecolor=self.color, edgecolor='none',
                alpha=0.2, zorder=9.1
            )
            ax.add_patch(inner_aura)
        
        # Draw wave pattern (representing information integration)
        if self.show_wave:
            # Create a wave pattern around the phi symbol
            theta = np.linspace(0, 2 * np.pi, 100)
            radius = self.font_size * 0.8
            
            # Create wavy radius
            wave_amplitude = radius * 0.15
            wave_frequency = 8
            wavy_radius = radius + wave_amplitude * np.sin(theta * wave_frequency)
            
            wave_x = x + wavy_radius * np.cos(theta)
            wave_y = y + wavy_radius * np.sin(theta)
            
            # Draw the wave
            ax.plot(
                wave_x, wave_y,
                color=self.color,
                alpha=0.4,
                linewidth=1.0,
                zorder=9.2
            )
        
        # Create the Phi text with enhanced formula
        if self.formula:
            # More detailed formula showing integrated information
            text = r"$\Phi \approx " + f"{self.phi_value:.2f}" + r"$"
            
            # Alternatively, for an even more complex formula:
            # text = r"$\Phi = " + f"{self.phi_value:.2f}" + r" \approx \max_{\mathcal{P}}(\text{EI}(\mathcal{M};\mathcal{P}))$"
        else:
            text = f"Φ ≈ {self.phi_value:.2f}"
        
        # Add text with enhanced effects
        text_obj = ax.text(
            x, y, text,
            ha='center', va='center', 
            color=self.color,
            fontsize=self.font_size, 
            fontweight='bold',
            path_effects=[
                withStroke(linewidth=3, foreground='black', alpha=0.7),
                withStroke(linewidth=5, foreground='black', alpha=0.3),
            ],
            zorder=10
        )
        
        # Add pulse markers (small dots at various distances)
        if self.show_pulse:
            for i in range(3):
                angle = np.random.uniform(0, 2 * np.pi)
                dist = np.random.uniform(1.8, 2.5) * self.font_size
                pulse_x = x + np.cos(angle) * dist
                pulse_y = y + np.sin(angle) * dist
                
                # Add a small pulse dot
                ax.scatter(
                    pulse_x, pulse_y,
                    s=5, color=self.color, alpha=0.8, zorder=9.3
                )
        
        logger.debug("Drew enhanced Phi metric annotation")


class ProcessingScales:
    """Multi-scale processing visualization with enhanced concentric rings."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the processing scales with the given configuration.
        
        Args:
            config: Configuration dictionary with processing scales parameters
        """
        self.scales = config
        self.use_gradients = True
        self.add_time_markers = True
        self.add_pulse_indicators = True
        
        logger.debug(f"Initialized {len(self.scales)} processing scales with enhanced effects")
    
    def _create_gradient_line(self, ax: plt.Axes, center: Tuple[float, float], 
                           radius: float, color: str, dash_pattern: Tuple[float, float],
                           linewidth: float = 0.8, alpha: float = 0.6) -> None:
        """Create a gradient line around a circle.
        
        Args:
            ax: Matplotlib axes to draw on
            center: Center point (x, y)
            radius: Radius of the circle
            color: Base color of the line
            dash_pattern: Dash pattern [on, off]
            linewidth: Width of the line
            alpha: Alpha of the line
        """
        # Create a circular line with varying color intensity
        theta = np.linspace(0, 2 * np.pi, 500)
        x = center[0] + radius * np.cos(theta)
        y = center[1] + radius * np.sin(theta)
        
        # Create points
        points = np.column_stack([x, y])
        
        # Create varying alpha values around the circle
        alphas = np.abs(np.sin(theta * 2)) * 0.4 + 0.2
        
        # Create a collection of line segments
        segments = np.column_stack([points[:-1], points[1:]])
        line_collection = LineCollection(
            segments.reshape(-1, 2, 2),
            linewidths=linewidth,
            color=color,
            alpha=alphas[:-1],
            zorder=2,
            linestyle='dashed'
        )
        
        ax.add_collection(line_collection)
    
    def draw(self, ax: plt.Axes, cif_component: Component) -> None:
        """Draw the processing scales around the center component with enhanced effects.
        
        Args:
            ax: Matplotlib axes to draw on
            cif_component: CIF component (usually at the center)
        """
        center = cif_component.center
        
        # Draw each scale with enhanced visuals
        for name, scale_config in self.scales.items():
            # Get scale parameters
            radius = scale_config.get("radius", 20)
            dash_pattern = scale_config.get("dash_pattern", [1, 1])
            color = scale_config.get("color", "#42f584")
            
            # Create and draw the scale ring with gradient effect if enabled
            if self.use_gradients:
                self._create_gradient_line(
                    ax, center, radius, color, dash_pattern,
                    linewidth=1.0, alpha=0.7
                )
            else:
                # Standard ring with dashed line
                ring = Ellipse(
                    center, radius * 2, radius * 2,
                    facecolor='none', edgecolor=color,
                    linestyle=(0, dash_pattern),
                    linewidth=0.8, alpha=0.6, zorder=2
                )
                ax.add_patch(ring)
            
            # Add time marker labels at regular intervals if enabled
            if self.add_time_markers and name and radius > 10:
                # Add the main label
                angle = np.random.uniform(0, 2 * np.pi)
                label_x = center[0] + radius * np.cos(angle)
                label_y = center[1] + radius * np.sin(angle)
                
                label = ax.text(
                    label_x, label_y, name, 
                    ha='center', va='center', color=color,
                    fontsize=7, alpha=0.8, zorder=2.5,
                    fontweight='bold'
                )
                
                # Add shadow effect to text
                label.set_path_effects([
                    withStroke(linewidth=2, foreground='black', alpha=0.5)
                ])
                
                # Add small time-scale markers around the circle
                num_markers = int(radius / 5)  # More markers for larger scales
                for i in range(num_markers):
                    marker_angle = i * 2 * np.pi / num_markers
                    marker_x = center[0] + radius * np.cos(marker_angle)
                    marker_y = center[1] + radius * np.sin(marker_angle)
                    
                    # Draw small marker tick
                    inner_x = center[0] + (radius - 1) * np.cos(marker_angle)
                    inner_y = center[1] + (radius - 1) * np.sin(marker_angle)
                    
                    ax.plot(
                        [inner_x, marker_x], [inner_y, marker_y],
                        color=color, linewidth=0.5, alpha=0.5, zorder=2
                    )
            
            # Add pulse indicators if enabled
            if self.add_pulse_indicators:
                pulse_angle = np.random.uniform(0, 2 * np.pi)
                pulse_x = center[0] + radius * np.cos(pulse_angle)
                pulse_y = center[1] + radius * np.sin(pulse_angle)
                
                # Draw pulse dot
                ax.scatter(
                    pulse_x, pulse_y,
                    s=15, color=color, alpha=0.8, zorder=2.6,
                    marker='o'
                )
                
                # Draw pulse wave (small ripple)
                for i in range(3):
                    ripple_radius = 1 + i * 0.8
                    ripple = Ellipse(
                        (pulse_x, pulse_y), ripple_radius, ripple_radius,
                        facecolor='none', edgecolor=color,
                        linewidth=0.5, alpha=0.5 - i * 0.1, zorder=2.5
                    )
                    ax.add_patch(ripple)
        
        logger.debug("Drew processing scales with enhanced effects")


def create_component(name: str, config: Dict[str, Any]) -> Component:
    """Factory function to create a component based on configuration.
    
    Args:
        name: Component name
        config: Configuration dictionary with component parameters
    
    Returns:
        A component
    """
    return Component(name, config)


def create_components(config: Dict[str, Dict[str, Any]]) -> Dict[str, Component]:
    """Factory function to create all components based on configuration.
    
    Args:
        config: Configuration dictionary with all components
    
    Returns:
        A dictionary of components
    """
    components = {}
    for name, component_config in config.items():
        components[name] = create_component(name, component_config)
    
    return components