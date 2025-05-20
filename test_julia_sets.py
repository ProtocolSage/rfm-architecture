#!/usr/bin/env python3
"""
Test script for Julia set fractal visualization.
This script loads presets from config.yaml and renders each Julia set variant.
"""
import os
import yaml
import logging
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages

from rfm.core.fractal import JuliaSet, create_fractal

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config(config_path='config.yaml'):
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}

def test_julia_set(preset_name, preset_config, save_dir='julia_test_output'):
    """Test a Julia set with the given parameters."""
    logger.info(f"Testing Julia set preset: {preset_name}")
    
    # Create the fractal
    julia = create_fractal(preset_config)
    
    # Set up the figure
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(-2, 2)
    ax.set_ylim(-2, 2)
    ax.set_title(f"Julia Set: {preset_name}")
    
    # Add parameter text
    params = preset_config.get("parameters", {})
    c_real = params.get("c_real", 0)
    c_imag = params.get("c_imag", 0)
    zoom = params.get("zoom", 1)
    max_iter = params.get("max_iter", 100)
    cmap = params.get("cmap", "viridis")
    
    param_text = (f"c = {c_real} + {c_imag}i\n"
                  f"zoom = {zoom}\n"
                  f"max_iter = {max_iter}\n"
                  f"colormap = {cmap}")
    
    ax.text(0.02, 0.02, param_text, transform=ax.transAxes, 
            fontsize=10, verticalalignment='bottom', 
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.5))
    
    # Draw the Julia set
    julia.draw(ax)
    
    # Save the figure
    os.makedirs(save_dir, exist_ok=True)
    filename = os.path.join(save_dir, f"{preset_name}.png")
    fig.savefig(filename, dpi=150, bbox_inches='tight')
    logger.info(f"Saved Julia set image to {filename}")
    
    plt.close(fig)
    return filename

def main():
    """Main function to test all Julia set presets."""
    config = load_config()
    if not config:
        logger.error("Failed to load config")
        return
    
    # Get all Julia set presets
    alternative_fractals = config.get("alternative_fractals", {})
    julia_presets = {name: preset for name, preset in alternative_fractals.items() 
                     if preset.get("type") == "julia"}
    
    if not julia_presets:
        logger.warning("No Julia set presets found in config")
        return
    
    logger.info(f"Found {len(julia_presets)} Julia set presets")
    
    # Create output directory
    output_dir = "julia_test_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create PDF to save all sets
    pdf_path = os.path.join(output_dir, "julia_sets_collection.pdf")
    with PdfPages(pdf_path) as pdf:
        for name, preset in julia_presets.items():
            # Create individual image
            test_julia_set(name, preset, output_dir)
            
            # Create figure for PDF
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.set_xlim(-2, 2)
            ax.set_ylim(-2, 2)
            ax.set_title(f"Julia Set: {name}")
            
            # Add parameter text
            params = preset.get("parameters", {})
            c_real = params.get("c_real", 0)
            c_imag = params.get("c_imag", 0)
            zoom = params.get("zoom", 1)
            max_iter = params.get("max_iter", 100)
            cmap = params.get("cmap", "viridis")
            
            param_text = (f"c = {c_real} + {c_imag}i\n"
                        f"zoom = {zoom}\n"
                        f"max_iter = {max_iter}\n"
                        f"colormap = {cmap}")
            
            ax.text(0.02, 0.02, param_text, transform=ax.transAxes, 
                    fontsize=10, verticalalignment='bottom', 
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.5))
            
            # Draw the Julia set
            julia = create_fractal(preset)
            julia.draw(ax)
            
            # Add to PDF
            pdf.savefig(fig)
            plt.close(fig)
    
    logger.info(f"All Julia sets saved to {pdf_path}")
    logger.info(f"Individual images saved to {output_dir} directory")

if __name__ == "__main__":
    main()