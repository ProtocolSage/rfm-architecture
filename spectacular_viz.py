#!/usr/bin/env python
"""Script to run the RFM visualization with spectacular effects."""

import sys
import os
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import time

# Add the current directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import necessary modules
from rfm.config.settings import ConfigLoader
from rfm.core.fractal import create_fractal
from rfm.core.network import create_kin_graph
from rfm.core.morphogen import create_morphogen
from rfm.viz.components import (
    create_components, NestedConsciousFields, PhiMetric, ProcessingScales
)
from rfm.viz.layout import GoldenRatioLayout
from rfm.viz.effects import (
    GlowEffect, CosmicGradient, ParticleSystem, 
    DepthEffect, MathematicalBeauty, ConceptualVisualizer
)

def spectacular_visualization():
    """Generate a spectacular static visualization."""
    print("Generating spectacular RFM visualization...")
    start_time = time.time()
    
    # Create figure with high-quality settings
    plt.rcParams['figure.dpi'] = 100
    plt.rcParams['savefig.dpi'] = 300
    plt.rcParams['figure.figsize'] = [14, 12]
    plt.rcParams['figure.facecolor'] = "#000000"
    plt.rcParams['axes.facecolor'] = "#000000"
    plt.rcParams['image.cmap'] = 'inferno'
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 12))
    ax.set_facecolor("#000000")
    
    # Set up axes
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_aspect('equal')
    ax.axis('off')
    
    print("Creating spectacular cosmic background...")
    # Apply cosmic gradient background with striking colors
    cosmic_bg = CosmicGradient(
        palette_name="nebula", 
        alpha=0.95,
        custom_colors=["#000000", "#0d0a2b", "#1e044d", "#4c0794", "#7a00c2", "#a02bff"]
    )
    cosmic_bg.apply_background(ax, style="spiral")
    
    # Create a second cosmic background layer for additional depth
    cosmic_bg2 = CosmicGradient(
        palette_name="nebula", 
        alpha=0.4,
        custom_colors=["#000000", "#0a0715", "#160a40", "#300a65", "#4b04a5", "#6b00ff"]
    )
    cosmic_bg2.apply_background(ax, style="radial")
    
    # Create mathematical beauty effects
    math_beauty = MathematicalBeauty()
    
    # Add golden spiral overlay
    math_beauty.draw_golden_spiral(
        ax, center=(50, 50), max_radius=45,
        num_turns=5.0, line_width=0.7, 
        color="#b086ff", alpha=0.25
    )
    
    # Create fractal background
    print("Creating spectacular fractal patterns...")
    fractal_config = {
        "type": "l_system",
        "depth": 5,
        "parameters": {
            "axiom": "F",
            "rules": {"F": "FF+[+F-F-F]-[-F+F+F]"},
            "angle": 25,
            "color": "#4287f5",
            "alpha": 0.15,
            "width": 0.4
        }
    }
    
    fractal = create_fractal(fractal_config)
    fractal.draw(ax)
    
    # Create depth effect
    depth_effect = DepthEffect(
        shadow_color="#000000", 
        shadow_alpha=0.6,
        elevation=5.0, 
        blur_radius=7.0
    )
    
    # Create morphogenetic patterns
    print("Generating spectacular morphogenetic patterns...")
    morphogen_config = {
        "type": "voronoi",
        "points": 25, 
        "color_start": "#00c2c7",
        "color_end": "#b086ff",
        "opacity": 0.3,
        "blend_mode": "overlay"
    }
    
    morphogen = create_morphogen(morphogen_config)
    morphogen.draw(ax)
    
    # Create components
    print("Creating spectacular components...")
    component_config = {
        "cif": {
            "center": [50, 50],
            "size": [28, 28],
            "color": "#42d7f5",
            "label": "Consciousness\nIntegration Field",
            "description": "Global workspace for information broadcast",
            "zorder": 10,
            "glass_effect": True,
            "inner_glow": True,
            "highlight": True
        },
        "perception": {
            "center": [25, 80],
            "size": [22, 16],
            "color": "#4287f5",
            "label": "Perception System",
            "description": "Sensory processing & pattern recognition",
            "zorder": 6,
            "glass_effect": True
        },
        "knowledge": {
            "center": [80, 70],
            "size": [22, 16],
            "color": "#f54242",
            "label": "Knowledge Integration\nNetwork",
            "description": "Dynamic semantic representation",
            "zorder": 6,
            "glass_effect": True
        },
        "metacognitive": {
            "center": [80, 30],
            "size": [22, 16],
            "color": "#42f584",
            "label": "Metacognitive\nExecutive",
            "description": "Reflective self-monitoring",
            "zorder": 6,
            "glass_effect": True
        },
        "evolutionary": {
            "center": [25, 20],
            "size": [22, 16],
            "color": "#9942f5",
            "label": "Evolutionary\nOptimizer",
            "description": "Structure adaptation",
            "zorder": 6,
            "glass_effect": True
        },
        "simulation": {
            "center": [50, 20],
            "size": [22, 14],
            "color": "#f5a742",
            "label": "Simulation Engine",
            "description": "Predictive world modeling",
            "zorder": 6,
            "glass_effect": True
        }
    }
    
    # Create glow effect for components
    glow = GlowEffect(color="#00c2c7", alpha=0.9, strength=5.0)
    
    # Create components with enhanced visual effects
    components = {}
    for name, config in component_config.items():
        components[name] = create_component(name, config)
        components[name].draw(ax)
        # Add shadow to component
        shadow = depth_effect.add_shadow(ax.patches[-3 if config.get("inner_glow") else -1], ax, offset=(3, -3))
    
    # Create connections between components with particles
    connection_config = [
        {"source": "perception", "target": "cif", "curve": 0.1, "width": 2, "color": "#4287f5", "bidirectional": True},
        {"source": "cif", "target": "knowledge", "curve": 0.1, "width": 2, "color": "#f54242", "bidirectional": True},
        {"source": "cif", "target": "metacognitive", "curve": 0.1, "width": 2, "color": "#42f584", "bidirectional": True},
        {"source": "metacognitive", "target": "evolutionary", "curve": 0.1, "width": 2, "color": "#9942f5", "bidirectional": True},
        {"source": "evolutionary", "target": "simulation", "curve": 0.1, "width": 2, "color": "#f5a742", "bidirectional": True},
        {"source": "simulation", "target": "cif", "curve": 0.3, "width": 1.5, "color": "#f5a742", "bidirectional": True}
    ]
    
    print("Creating spectacular connections...")
    # Create particle system for pathways
    particle_system = ParticleSystem(
        color="#00c2c7", 
        density=1.2,
        size_range=(0.8, 2.5), 
        glow=True
    )
    
    for conn in connection_config:
        source = components[conn["source"]]
        target = components[conn["target"]]
        
        # Add regular connection arrow
        source.connect_to(target, ax, conn)
        
        # Add particle flow along the path (simulated for static image)
        curve = conn.get("curve", 0.0)
        particle_system.add_path(source.center, target.center, curve)
    
    # Draw particles (static representation)
    for i in range(5):  # Draw multiple frames to get more particles
        particle_system.draw(ax, frame=i*10)
    
    # Create nested conscious fields with glass-morphism effect
    conscious_fields_config = {
        "primary": {
            "size": [28, 28],
            "alpha": 0.8,
            "color": "#42d7f5"
        },
        "reflective": {
            "size": [34, 34],
            "alpha": 0.6,
            "color": "#42f5b3"
        },
        "peripheral": {
            "size": [40, 40],
            "alpha": 0.4,
            "color": "#42f5f5"
        },
        "prospective": {
            "size": [46, 46],
            "alpha": 0.3,
            "color": "#42b3f5"
        }
    }
    
    print("Creating spectacular consciousness fields...")
    cfields = NestedConsciousFields(conscious_fields_config)
    cfields.draw(ax, components["cif"])
    
    # Add glow to some fields randomly
    for patch in ax.patches[-len(conscious_fields_config)*3:]:
        if np.random.random() < 0.7:  # Add glow to 70% of fields
            glow.apply_to_patch(patch)
    
    # Create KIN graph with enhanced visuals
    print("Creating spectacular knowledge graph...")
    kin_config = {
        "nodes": 25,
        "edge_probability": 0.4,
        "node_size": 4.5,
        "node_color": "#f54242",
        "edge_color": "#f5a742",
        "layout": "spring"
    }
    
    kin_graph = create_kin_graph(kin_config)
    # Pass the component as a dictionary for compatibility
    comp_dict = {
        "center": components["knowledge"].center,
        "size": components["knowledge"].size
    }
    kin_graph.draw(ax, comp_dict)
    
    # Create processing scales
    print("Creating spectacular processing scales...")
    scales_config = {
        "micro": {
            "radius": 15,
            "dash_pattern": [1, 1],
            "color": "#42f584"
        },
        "cognitive": {
            "radius": 25,
            "dash_pattern": [2, 1],
            "color": "#42f5b3"
        },
        "learning": {
            "radius": 35,
            "dash_pattern": [3, 2],
            "color": "#42d7f5"
        },
        "developmental": {
            "radius": 45,
            "dash_pattern": [5, 3],
            "color": "#4287f5"
        }
    }
    
    scales = ProcessingScales(scales_config)
    scales.draw(ax, components["cif"])
    
    # Create phi metric with enhanced effects
    phi_config = {
        "display": True,
        "position": [60, 55],
        "formula": True,
        "font_size": 12,
        "color": "#b086ff",
        "value": 0.85,
        "show_aura": True,
        "show_pulse": True,
        "show_wave": True
    }
    
    phi = PhiMetric(phi_config)
    phi.draw(ax, components["cif"])
    
    # Add glow to the phi metric text
    for text in ax.texts:
        if r"$\Phi" in text.get_text():
            glow.apply_to_text(text)
    
    # Create conceptual visualizer
    print("Creating spectacular conceptual visualizations...")
    conceptual = ConceptualVisualizer()
    
    # Add self-reference loop near metacognitive component
    if "metacognitive" in components:
        meta_comp = components["metacognitive"]
        offset = (meta_comp.size[0] * 0.3, meta_comp.size[1] * 0.3)
        loop_center = (meta_comp.center[0] + offset[0], meta_comp.center[1] + offset[1])
        conceptual.draw_self_reference_loop(
            ax, center=loop_center, radius=5,
            line_width=1.2, color="#42f584", alpha=0.8
        )
    
    # Add emergence pattern near evolutionary component
    if "evolutionary" in components:
        evo_comp = components["evolutionary"]
        conceptual.draw_emergence_pattern(
            ax, center=evo_comp.center, size=evo_comp.size[0] * 0.7,
            num_elements=18, small_color="#9942f5", large_color="#b086ff"
        )
    
    # Add integration visualization to CIF
    if "cif" in components:
        cif_comp = components["cif"]
        conceptual.draw_integration_network(
            ax, components, center=cif_comp.center, radius=30,
            line_color="#00c2c7", alpha=0.2
        )
    
    # Add Fibonacci-based grid in the background
    math_beauty.draw_fibonacci_grid(
        ax, origin=(5, 5), size=30, levels=4,
        line_width=0.4, color="#b086ff", alpha=0.15
    )
    
    # Add title and labels with glow effect
    print("Adding spectacular title and effects...")
    # Create layout to use its functionality
    layout = GoldenRatioLayout(ax, {"grid": {"width": 100, "height": 100}})
    layout.add_title("RECURSIVE FRACTAL MIND")
    layout.add_subtitle("A Self-Evolving AI Architecture")
    
    # Add glow to title and subtitle
    for text in ax.texts[-2:]:
        glow.apply_to_text(text)
    
    # Add attribution
    layout.add_attribution(
        "Visualization of complex self-organizing fractal mind architecture",
        fontsize=8
    )
    
    # Create "simulated" pulses to show animation effects in static image
    for i in range(5):
        radius = 5 + i * 10
        pulse = plt.Circle(
            (50, 50), radius,
            facecolor='none', 
            edgecolor="#00c2c7",
            linewidth=1.5 - i * 0.25, 
            alpha=0.7 - i * 0.15,
            zorder=15
        )
        ax.add_patch(pulse)
    
    # Save the spectacular visualization
    output_file = "rfm_spectacular_diagram.png"
    print(f"Saving spectacular visualization to {output_file}...")
    plt.savefig(
        output_file, 
        dpi=300, 
        bbox_inches='tight', 
        facecolor=ax.get_facecolor()
    )
    
    end_time = time.time()
    print(f"Spectacular visualization completed in {end_time - start_time:.2f} seconds!")
    print(f"The image has been saved to: {os.path.abspath(output_file)}")


# Import component creator for visualization
from rfm.viz.components import create_component

if __name__ == "__main__":
    spectacular_visualization()