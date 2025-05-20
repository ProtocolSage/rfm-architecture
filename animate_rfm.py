#!/usr/bin/env python
"""
RFM Animation Script - Creates spectacular animated visualizations
of the Recursive Fractal Mind architecture with premium aesthetics.
"""
import os
import sys
import time
import logging
import argparse
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Add the current directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import necessary modules
from rfm.config.settings import ConfigLoader
from rfm.core.fractal import create_fractal
from rfm.core.network import create_kin_graph
from rfm.core.morphogen import create_morphogen
from rfm.viz.components import (
    create_components, NestedConsciousFields, PhiMetric, ProcessingScales, Component
)
from rfm.viz.layout import GoldenRatioLayout
from rfm.viz.effects import (
    GlowEffect, CosmicGradient, ParticleSystem, 
    DepthEffect, MathematicalBeauty, ConceptualVisualizer
)
from rfm.viz.animation_engine import (
    AnimationTimeline, BroadcastSequence, ParticleFlowSystem, 
    NestedFieldsAnimation, AnimationSequencer, AnimationExporter
)

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def create_animation(args):
    """Create an animated visualization of the RFM architecture.
    
    Args:
        args: Command line arguments
    
    Returns:
        0 on success, 1 on error
    """
    start_time = time.time()
    
    try:
        logger.info("Initializing RFM animation...")
        
        # Load configuration
        config = ConfigLoader.from_file(args.config)
        
        # Create figure with high-quality settings
        plt.rcParams['figure.dpi'] = 100
        plt.rcParams['savefig.dpi'] = args.dpi
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
        
        logger.info("Creating cosmic background...")
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
        logger.info("Creating fractal patterns...")
        fractal_config = {
            "type": "l_system",
            "depth": 4,
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
        logger.info("Generating morphogenetic patterns...")
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
        logger.info("Creating core components...")
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
        
        logger.info("Creating component connections...")
        for conn in connection_config:
            source = components[conn["source"]]
            target = components[conn["target"]]
            
            # Add regular connection arrow
            source.connect_to(target, ax, conn)
        
        # Create KIN graph with enhanced visuals
        logger.info("Creating knowledge graph...")
        kin_config = {
            "nodes": 25,
            "edge_probability": 0.4,
            "node_size": 4.0,
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
        logger.info("Creating processing scales...")
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
        logger.info("Creating conceptual visualizations...")
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
        logger.info("Adding title and effects...")
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
        
        # =================================================================
        # Set up animation
        # =================================================================
        logger.info("Setting up animation system...")
        
        # Create animation timeline
        duration = args.duration  # seconds
        fps = args.fps  # frames per second
        timeline = AnimationTimeline(duration=duration, fps=fps, easing="cubic")
        
        # Add keyframes to the timeline
        timeline.add_keyframe(0.0, {
            "particles": {
                "density": 0.8,
                "color": "#00c2c7"
            },
            "broadcast": {
                "num_pulses": 2,
                "pulse_color": "#00c2c7",
                "pulse_width": 1.5
            },
            "fields": {
                "breathing": True,
                "breathing_amplitude": 0.05,
                "shimmer": True
            }
        })
        
        timeline.add_keyframe(2.0, {
            "particles": {
                "density": 1.5,
                "color": "#00c2d8"
            },
            "broadcast": {
                "num_pulses": 3,
                "pulse_color": "#00d8d8",
                "pulse_width": 2.0
            },
            "fields": {
                "breathing": True,
                "breathing_amplitude": 0.08,
                "shimmer": True
            }
        })
        
        timeline.add_keyframe(3.5, {
            "particles": {
                "density": 1.2,
                "color": "#00c2c7"
            },
            "broadcast": {
                "num_pulses": 2,
                "pulse_color": "#00c2c7",
                "pulse_width": 1.5
            },
            "fields": {
                "breathing": True,
                "breathing_amplitude": 0.04,
                "shimmer": True
            }
        })
        
        timeline.add_keyframe(5.0, {
            "particles": {
                "density": 0.8,
                "color": "#00c2c7"
            },
            "broadcast": {
                "num_pulses": 2,
                "pulse_color": "#00c2c7",
                "pulse_width": 1.5
            },
            "fields": {
                "breathing": True,
                "breathing_amplitude": 0.05,
                "shimmer": True
            }
        })
        
        # Create animation systems
        particle_config = {
            "enabled": True,
            "color": "#00c2c7",
            "density": 1.0,
            "min_size": 0.5,
            "max_size": 2.5,
            "speed_factor": 1.0,
            "glow": True,
            "glow_strength": 3.0,
            "fade_length": 0.3,
            "turbulence": 0.1,
            "color_variance": 0.2
        }
        
        broadcast_config = {
            "enabled": True,
            "color": "#00c2c7",
            "glow_strength": 3.0,
            "glow_color": "#00c2c7",
            "max_pulses": 3,
            "speed": 1.0,
            "width": 2.0,
            "fade_out": True
        }
        
        fields_config = {
            "enabled": True,
            "breathing": True,
            "breathing_amplitude": 0.05,
            "breathing_frequency": 0.2,
            "shimmer": True,
            "shimmer_count": 5,
            "shimmer_speed": 1.0,
            "field_pulse": True,
            "field_pulse_frequency": 0.1
        }
        
        # Create animation objects
        particle_system = ParticleFlowSystem(particle_config)
        broadcast_system = BroadcastSequence(broadcast_config)
        fields_system = NestedFieldsAnimation(fields_config)
        
        # Set up animation sources and paths
        logger.info("Configuring animation paths...")
        
        # Add particle paths
        particle_system.add_connection_paths(components, connection_config)
        
        # Add broadcast paths
        broadcast_system.add_source(components["cif"].center, radius=35)
        broadcast_system.add_connection_paths(components, connection_config)
        
        # Add conscious fields
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
        fields_system.add_fields(conscious_fields_config, components["cif"].center)
        
        # Create animation sequencer
        sequencer = AnimationSequencer(timeline)
        sequencer.add_animation("particles", particle_system)
        sequencer.add_animation("broadcast", broadcast_system)
        sequencer.add_animation("fields", fields_system)
        
        # Create animation update function
        def update_animation(frame, params):
            """Update all animations.
            
            Args:
                frame: Frame number
                params: Animation parameters
            
            Returns:
                List of updated artists
            """
            return sequencer.update(frame, params, ax)
        
        # Create animation using timeline
        logger.info(f"Creating animation sequence ({duration}s at {fps} FPS)...")
        animation_obj = timeline.create_animation(fig, update_animation, interval=1000/fps)
        
        # Export or display the animation
        if args.output:
            # Create exporter
            logger.info("Setting up animation exporter...")
            exporter = AnimationExporter({"verbose": True, "dpi": args.dpi})
            
            # Get output format and filename
            output_path = args.output
            fmt = args.format.lower()
            
            # Add appropriate extension if not provided
            if not output_path.lower().endswith(f".{fmt}"):
                if fmt == "gif":
                    output_path += ".gif"
                elif fmt == "mp4":
                    output_path += ".mp4"
                elif fmt == "html":
                    output_path += ".html"
            
            # Export the animation
            logger.info(f"Exporting animation to {fmt.upper()}: {output_path}")
            exporter.export(
                animation_obj, 
                output_path, 
                fmt=fmt, 
                fps=fps, 
                dpi=args.dpi,
                bitrate=args.bitrate
            )
            
            logger.info(f"Animation saved to: {output_path}")
            
        # Show the animation if requested
        if args.show:
            logger.info("Displaying animation...")
            plt.show()
        
        # Clean up
        plt.close(fig)
        
        end_time = time.time()
        logger.info(f"Animation completed in {end_time - start_time:.2f} seconds")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.debug("Exception details:", exc_info=True)
        return 1


def main():
    """Main entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Generate an animated visualization of the RFM architecture")
    
    parser.add_argument("--output", default="rfm_animation", help="Output file path (without extension)")
    parser.add_argument("--format", choices=["gif", "mp4", "html"], default="gif", help="Output format")
    parser.add_argument("--dpi", type=int, default=150, help="DPI for output")
    parser.add_argument("--duration", type=float, default=8.0, help="Animation duration in seconds")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second")
    parser.add_argument("--bitrate", type=int, default=5000, help="Video bitrate (for MP4)")
    parser.add_argument("--show", action="store_true", help="Show animation in a window")
    parser.add_argument("--config", default="config.yaml", help="Path to configuration file")
    
    args = parser.parse_args()
    
    # Create the animation
    return create_animation(args)


if __name__ == "__main__":
    sys.exit(main())