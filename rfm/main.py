"""Main entry point for RFM visualization."""
from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from rfm.config.settings import ConfigLoader
from rfm.core.fractal import create_fractal
from rfm.core.network import create_kin_graph
from rfm.core.morphogen import create_morphogen
from rfm.viz.components import (
    create_components, NestedConsciousFields, PhiMetric, ProcessingScales
)
from rfm.viz.animation import BroadcastAnimation
from rfm.viz.layout import GoldenRatioLayout
from rfm.viz.effects import (
    GlowEffect, CosmicGradient, ParticleSystem, 
    DepthEffect, MathematicalBeauty, ConceptualVisualizer
)
from rfm.cli import parse_args

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the RFM visualization."""
    start_time = time.time()
    
    # Parse command-line arguments
    try:
        args = parse_args()
    except SystemExit:
        # If argument parsing fails, try to use environment variables
        import os
        import argparse
        
        class EnvArgs:
            pass
        
        args = EnvArgs()
        args.output = os.environ.get("RFM_OUTPUT", "rfm_diagram.svg")
        args.format = os.environ.get("RFM_FORMAT", "svg")
        args.dpi = int(os.environ.get("RFM_DPI", "300"))
        args.show = os.environ.get("RFM_SHOW", "0") == "1"
        args.animate = os.environ.get("RFM_ANIMATE", "0") == "1"
        args.dark_mode = os.environ.get("RFM_DARK_MODE", "0") == "1"
        args.log_level = os.environ.get("RFM_LOG_LEVEL", "info")
        args.config = os.environ.get("RFM_CONFIG", "config.yaml")
    
    # Set up logging
    logging_level = getattr(logging, args.log_level.upper())
    logging.basicConfig(
        level=logging_level,
        format="%(levelname)s: %(message)s"
    )
    
    logger.info("Initializing RFM visualization")
    
    try:
        # Load configuration
        config = ConfigLoader.from_file(args.config)
        
        # Set up style for dark or light mode
        plt.style.use('dark_background' if args.dark_mode else 'default')
        
        # Create figure with high-quality settings
        plt.rcParams['figure.dpi'] = 100
        plt.rcParams['savefig.dpi'] = args.dpi
        plt.rcParams['figure.figsize'] = (14, 12)
        plt.rcParams['figure.facecolor'] = config.styling.get("background", "#0a0d16")
        plt.rcParams['axes.facecolor'] = config.styling.get("background", "#0a0d16")
        plt.rcParams['image.cmap'] = 'inferno'
        
        # Create figure
        fig, ax = plt.subplots(figsize=(14, 12))
        bg_color = config.styling.get("background", "#0a0d16") if args.dark_mode else "white"
        ax.set_facecolor(bg_color)
        
        logger.info("Creating cosmic background...")
        # Apply cosmic gradient background with more striking colors
        cosmic_bg = CosmicGradient(
            palette_name="nebula", 
            alpha=0.95 if args.dark_mode else 0.8,
            custom_colors=["#000000", "#0d0a2b", "#1e044d", "#4c0794", "#7a00c2", "#a02bff"]
        )
        cosmic_bg.apply_background(ax, style="spiral")
        
        # Create layout with mathematical beauty
        layout = GoldenRatioLayout(ax, config.layout)
        
        # Create mathematical beauty effects
        math_beauty = MathematicalBeauty()
        
        # Add golden spiral overlay
        math_beauty.draw_golden_spiral(
            ax, center=(50, 50), max_radius=45,
            num_turns=3.0, line_width=0.5, 
            color="#b086ff", alpha=0.15
        )
        
        logger.info("Creating fractal patterns...")
        # Create fractal background with depth effect
        fractal = create_fractal(config.fractals)
        fractal.draw(ax)
        
        # Create depth effect
        depth_effect = DepthEffect(
            shadow_color="#000000", 
            shadow_alpha=0.4,
            elevation=3.0, 
            blur_radius=5.0
        )
        
        logger.info("Generating morphogenetic patterns...")
        # Create morphogenetic patterns
        morphogen = create_morphogen(config.morphogen)
        morphogen.draw(ax)
        
        # Create particle system for pathways
        particle_system = ParticleSystem(
            color="#00c2c7", 
            density=0.5,
            size_range=(0.5, 2.0), 
            glow=True
        )
        
        logger.info("Creating core components...")
        # Create glow effect for components
        glow = GlowEffect(color="#00c2c7", alpha=0.7, strength=3.0)
        
        # Create components with enhanced visual effects
        components = create_components(config.components)
        for name, component in components.items():
            component.draw(ax)
            # Add shadow to component
            depth_effect.add_shadow(ax.patches[-1], ax, offset=(2, -2))
        
        logger.info("Creating component connections...")
        # Create connections between components with particles
        for conn in config.connections:
            source = components[conn["source"]]
            target = components[conn["target"]]
            
            # Add regular connection arrow
            source.connect_to(target, ax, conn)
            
            # Add particle flow along the path
            curve = conn.get("curve", 0.0)
            particle_system.add_path(source.center, target.center, curve)
        
        # Draw particles (initial frame)
        if args.animate:
            particle_artists = particle_system.draw(ax, frame=0)
        
        logger.info("Creating nested conscious fields...")
        # Create nested conscious fields with glass-morphism effect
        if "cif" in components:
            cfields = NestedConsciousFields(config.conscious_fields)
            cfields.draw(ax, components["cif"])
            
            # Add glow to the innermost field
            for patch in ax.patches[-len(config.conscious_fields):]:
                if np.random.random() < 0.5:  # Add glow to some fields randomly
                    glow.apply_to_patch(patch)
        
        logger.info("Creating knowledge integration network...")
        # Create KIN graph with enhanced visuals
        if "knowledge" in components:
            kin_graph = create_kin_graph(config.kin_graph)
            # Pass the component as a dictionary for compatibility
            comp_dict = {
                "center": components["knowledge"].center,
                "size": components["knowledge"].size
            }
            kin_graph.draw(ax, comp_dict)
        
        logger.info("Creating processing scales...")
        # Create processing scales
        if "cif" in components:
            scales = ProcessingScales(config.processing_scales)
            scales.draw(ax, components["cif"])
        
        # Create phi metric with glow
        if "cif" in components:
            phi = PhiMetric(config.phi_metric)
            phi.draw(ax, components["cif"])
            
            # Add glow to the phi metric text
            for text in ax.texts:
                if "$\\Phi" in text.get_text():
                    glow.apply_to_text(text)
        
        logger.info("Creating conceptual visualizations...")
        # Create conceptual visualizer
        conceptual = ConceptualVisualizer()
        
        # Add self-reference loop near metacognitive component
        if "metacognitive" in components:
            meta_comp = components["metacognitive"]
            offset = (meta_comp.size[0] * 0.3, meta_comp.size[1] * 0.3)
            loop_center = (meta_comp.center[0] + offset[0], meta_comp.center[1] + offset[1])
            conceptual.draw_self_reference_loop(
                ax, center=loop_center, radius=5,
                line_width=1.0, color="#42f584", alpha=0.6
            )
        
        # Add emergence pattern near evolutionary component
        if "evolutionary" in components:
            evo_comp = components["evolutionary"]
            conceptual.draw_emergence_pattern(
                ax, center=evo_comp.center, size=evo_comp.size[0] * 0.7,
                num_elements=12, small_color="#9942f5", large_color="#b086ff"
            )
        
        # Add integration visualization to CIF
        if "cif" in components:
            cif_comp = components["cif"]
            conceptual.draw_integration_network(
                ax, components, center=cif_comp.center, radius=30,
                line_color="#00c2c7", alpha=0.15
            )
        
        # Create broadcast animation with enhanced effects
        animation_obj = None
        if args.animate and "cif" in components:
            logger.info("Setting up animations...")
            broadcast = BroadcastAnimation(config.animation.get("broadcast", {}))
            animation_obj = broadcast.setup(ax, components)
            
            # Create a function to update both broadcast and particles
            def update_all(frame):
                # Get CIF component center
                cif_center = components["cif"].center
                max_radius = 50  # Maximum radius for pulses
                
                # Call the animation function with the required arguments
                broadcast_artists = broadcast.animation._func(frame, max_radius, cif_center)
                particle_artists = particle_system.draw(ax, frame)
                return broadcast_artists + particle_artists
            
            # Create a combined animation
            frames = 100
            interval = 50
            combined_animation = animation.FuncAnimation(
                fig, update_all, frames=frames, interval=interval,
                blit=True, repeat=True
            )
            
            animation_obj = combined_animation
        
        # Add Fibonacci-based grid in the background
        math_beauty.draw_fibonacci_grid(
            ax, origin=(5, 5), size=30, levels=3,
            line_width=0.3, color="#b086ff", alpha=0.1
        )
        
        # Add title and labels with glow effect
        layout.add_title("RECURSIVE FRACTAL MIND")
        layout.add_subtitle("A Self-Evolving AI Architecture")
        
        # Add glow to title
        for text in ax.texts[-2:]:
            glow.apply_to_text(text)
        
        # Add attribution
        layout.add_attribution(
            "Visualization of complex self-organizing fractal mind architecture",
            fontsize=8
        )
        
        # Save or show the figure
        if args.output:
            output_file = f"{args.output}.{args.format}"
            logger.info(f"Saving visualization to {output_file}")
            
            # For animated output, save as a GIF if possible
            if args.animate and args.format.lower() in ['gif', 'mp4']:
                if args.format.lower() == 'gif':
                    try:
                        from matplotlib.animation import PillowWriter
                        animation_obj.save(
                            output_file, 
                            writer=PillowWriter(fps=20),
                            dpi=args.dpi
                        )
                        logger.info(f"Saved animation to {output_file}")
                    except ImportError:
                        logger.warning("Pillow not available for GIF export, saving static image.")
                        plt.savefig(
                            output_file.replace('.gif', '.png'), 
                            dpi=args.dpi, 
                            bbox_inches='tight', 
                            facecolor=ax.get_facecolor()
                        )
                elif args.format.lower() == 'mp4':
                    try:
                        from matplotlib.animation import FFMpegWriter
                        animation_obj.save(
                            output_file, 
                            writer=FFMpegWriter(fps=20, bitrate=5000),
                            dpi=args.dpi
                        )
                        logger.info(f"Saved animation to {output_file}")
                    except ImportError:
                        logger.warning("FFmpeg not available for MP4 export, saving static image.")
                        plt.savefig(
                            output_file.replace('.mp4', '.png'), 
                            dpi=args.dpi, 
                            bbox_inches='tight', 
                            facecolor=ax.get_facecolor()
                        )
            else:
                # Save static image
                plt.savefig(
                    output_file, 
                    dpi=args.dpi, 
                    bbox_inches='tight', 
                    facecolor=ax.get_facecolor()
                )
        
        if args.show:
            plt.show()
        
        end_time = time.time()
        logger.info(f"RFM visualization completed in {end_time - start_time:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.debug("Exception details:", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())