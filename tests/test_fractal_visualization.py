#!/usr/bin/env python3
"""
Integration tests for fractal visualization components.

Tests the integration between fractal generation and visualization components,
ensuring that fractals render correctly with different visualization techniques.
"""
import os
import sys
import unittest
import tempfile
import numpy as np
import matplotlib.pyplot as plt
import yaml
import logging
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import components to test
from rfm.core.fractal import create_fractal, JuliaSet, MandelbrotSet, LSystem, CantorDust
from ui.rfm_ui.engine.core import FractalEngine
from rfm.viz.effects import apply_color_effect, apply_blur_effect, apply_glow_effect
from rfm.viz.animation import generate_transition_frames


class TestFractalVisualization(unittest.TestCase):
    """Tests the integration between fractal generators and visualization components."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test environment."""
        # Load configuration
        try:
            with open("config.yaml", "r") as f:
                cls.config = yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Could not load config.yaml: {e}")
            cls.config = {}
            
        # Create output directory for test artifacts
        cls.output_dir = os.path.join(os.path.dirname(__file__), "output", "viz_tests")
        os.makedirs(cls.output_dir, exist_ok=True)
        
        # Initialize the fractal engine
        cls.engine = FractalEngine(enable_progress_reporting=False)
    
    def setUp(self):
        """Set up each test."""
        # Create a matplotlib figure for testing
        self.fig, self.ax = plt.subplots(figsize=(6, 6))
        self.ax.set_xlim(-2, 2)
        self.ax.set_ylim(-2, 2)
    
    def tearDown(self):
        """Clean up after each test."""
        # Close the matplotlib figure
        plt.close(self.fig)
    
    def test_all_fractal_types_rendering(self):
        """Test that all fractal types can be rendered correctly."""
        fractal_types = ["mandelbrot", "julia", "l_system", "cantor"]
        
        for fractal_type in fractal_types:
            with self.subTest(fractal_type=fractal_type):
                # Create basic config for this fractal type
                if fractal_type == "mandelbrot":
                    config = {
                        "type": fractal_type,
                        "parameters": {
                            "center": [-0.5, 0],
                            "zoom": 1.5,
                            "max_iter": 50,
                            "cmap": "viridis"
                        }
                    }
                elif fractal_type == "julia":
                    config = {
                        "type": fractal_type,
                        "parameters": {
                            "c_real": -0.7,
                            "c_imag": 0.27,
                            "center": [0, 0],
                            "zoom": 1.5,
                            "max_iter": 50,
                            "cmap": "plasma"
                        }
                    }
                elif fractal_type == "l_system":
                    config = {
                        "type": fractal_type,
                        "parameters": {
                            "axiom": "F",
                            "rules": {"F": "F+F-F-F+F"},
                            "angle": 90,
                            "depth": 3,
                            "color": "#2c3e50",
                            "alpha": 0.2
                        }
                    }
                elif fractal_type == "cantor":
                    config = {
                        "type": fractal_type,
                        "parameters": {
                            "depth": 3,
                            "gap_ratio": 0.3,
                            "color": "#2c3e50",
                            "alpha": 0.2
                        }
                    }
                
                # Create the fractal
                fractal = create_fractal(config)
                
                # Clear the axes and set limits
                self.ax.clear()
                self.ax.set_xlim(-2, 2)
                self.ax.set_ylim(-2, 2)
                
                # Draw the fractal
                fractal.draw(self.ax)
                
                # Save the figure for inspection
                output_path = os.path.join(self.output_dir, f"{fractal_type}_basic.png")
                self.fig.savefig(output_path, dpi=100)
                
                # Check that the image was created
                self.assertTrue(os.path.exists(output_path))
                self.assertGreater(os.path.getsize(output_path), 0)
    
    def test_julia_set_visualization_with_effects(self):
        """Test rendering a Julia set with various visual effects."""
        # Create a Julia set from presets if available
        preset_name = "julia_dragon"
        if self.__class__.config and "alternative_fractals" in self.__class__.config:
            preset = self.__class__.config["alternative_fractals"].get(preset_name)
            if preset:
                # Create from preset
                fractal = create_fractal(preset)
            else:
                # Create with default parameters
                fractal = JuliaSet({
                    "c_real": -0.835,
                    "c_imag": -0.2321,
                    "center": [0, 0],
                    "zoom": 1.3,
                    "max_iter": 100,
                    "cmap": "hot",
                    "alpha": 0.3
                })
        else:
            # Create with default parameters
            fractal = JuliaSet({
                "c_real": -0.835,
                "c_imag": -0.2321,
                "center": [0, 0],
                "zoom": 1.3,
                "max_iter": 100,
                "cmap": "hot",
                "alpha": 0.3
            })
        
        # Create params for engine rendering
        params = {
            "type": "julia",
            "width": 400,
            "height": 400,
            "c_real": fractal.c_real,
            "c_imag": fractal.c_imag,
            "center_x": 0.0,
            "center_y": 0.0,
            "zoom": fractal.zoom,
            "max_iter": fractal.max_iter,
            "colormap": fractal.cmap,
            "high_quality": False
        }
        
        # Render the fractal using the engine
        result = self.__class__.engine.render(params)
        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(result.shape, (400, 400, 4))
        
        # Save the original render
        base_path = os.path.join(self.output_dir, f"{preset_name}_original.png")
        self.__class__.engine.save_image(result, base_path)
        
        # Test different visualization effects
        
        # 1. Color effect
        color_effect_params = {
            "saturation": 1.5,
            "brightness": 1.2,
            "contrast": 1.3
        }
        color_result = apply_color_effect(result.copy(), color_effect_params)
        color_path = os.path.join(self.output_dir, f"{preset_name}_color_effect.png")
        self.__class__.engine.save_image(color_result, color_path)
        
        # 2. Blur effect
        blur_effect_params = {
            "radius": 3,
            "sigma": 1.5
        }
        blur_result = apply_blur_effect(result.copy(), blur_effect_params)
        blur_path = os.path.join(self.output_dir, f"{preset_name}_blur_effect.png")
        self.__class__.engine.save_image(blur_result, blur_path)
        
        # 3. Glow effect
        glow_effect_params = {
            "radius": 10,
            "intensity": 0.5,
            "color": [0.0, 0.8, 1.0]
        }
        glow_result = apply_glow_effect(result.copy(), glow_effect_params)
        glow_path = os.path.join(self.output_dir, f"{preset_name}_glow_effect.png")
        self.__class__.engine.save_image(glow_result, glow_path)
        
        # Verify all images were created
        for path in [base_path, color_path, blur_path, glow_path]:
            self.assertTrue(os.path.exists(path))
            self.assertGreater(os.path.getsize(path), 0)
    
    def test_fractal_animation_transition(self):
        """Test generating transition frames between two fractals."""
        # Create two different Julia sets
        start_params = {
            "type": "julia",
            "width": 200,  # Smaller size for faster testing
            "height": 200,
            "c_real": -0.7,
            "c_imag": 0.27,
            "center_x": 0.0,
            "center_y": 0.0,
            "zoom": 1.5,
            "max_iter": 50,
            "colormap": "viridis",
            "high_quality": False
        }
        
        end_params = start_params.copy()
        end_params.update({
            "c_real": -0.835,
            "c_imag": -0.2321,
            "zoom": 1.2,
            "colormap": "plasma"
        })
        
        # Render start and end frames
        start_frame = self.__class__.engine.render(start_params)
        end_frame = self.__class__.engine.render(end_params)
        
        # Generate transition frames
        n_frames = 5  # Small number for testing
        frames = generate_transition_frames(
            start_frame, end_frame, 
            start_params, end_params,
            n_frames
        )
        
        # Check that we got the expected number of frames
        self.assertEqual(len(frames), n_frames)
        
        # Save frames for inspection
        for i, frame in enumerate(frames):
            frame_path = os.path.join(self.output_dir, f"transition_frame_{i}.png")
            self.__class__.engine.save_image(frame, frame_path)
            
            # Verify frame was saved
            self.assertTrue(os.path.exists(frame_path))
            self.assertGreater(os.path.getsize(frame_path), 0)
    
    def test_integration_with_matplotlib_colormaps(self):
        """Test that fractals integrate correctly with matplotlib colormaps."""
        # Test a selection of different colormaps
        colormaps = ["viridis", "plasma", "inferno", "magma", "cividis", 
                     "twilight", "cool", "hot", "jet", "rainbow"]
        
        # Basic Mandelbrot parameters
        base_params = {
            "type": "mandelbrot",
            "parameters": {
                "center": [-0.5, 0],
                "zoom": 1.5,
                "max_iter": 50,
                "alpha": 0.2
            }
        }
        
        for cmap in colormaps:
            with self.subTest(colormap=cmap):
                # Set the colormap
                params = base_params.copy()
                params["parameters"] = params["parameters"].copy()
                params["parameters"]["cmap"] = cmap
                
                # Create fractal
                fractal = create_fractal(params)
                
                # Clear the axes
                self.ax.clear()
                self.ax.set_xlim(-2, 2)
                self.ax.set_ylim(-2, 2)
                
                # Draw the fractal
                fractal.draw(self.ax)
                
                # Save the figure
                output_path = os.path.join(self.output_dir, f"mandelbrot_{cmap}.png")
                self.fig.savefig(output_path, dpi=100)
                
                # Check that the image was created
                self.assertTrue(os.path.exists(output_path))
                self.assertGreater(os.path.getsize(output_path), 0)
    
    def test_direct_pixel_manipulation(self):
        """Test rendering to raw numpy arrays and manipulating pixels."""
        # Render a simple Mandelbrot set to array
        params = {
            "type": "mandelbrot",
            "width": 200,
            "height": 200,
            "center_x": -0.5,
            "center_y": 0.0,
            "zoom": 1.5,
            "max_iter": 50,
            "colormap": "viridis",
            "high_quality": False
        }
        
        # Render to numpy array
        result = self.__class__.engine.render(params)
        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(result.shape, (200, 200, 4))
        
        # Perform direct pixel manipulations
        
        # 1. Invert colors
        inverted = 1.0 - result[:,:,:3]  # Only invert RGB, not alpha
        inverted_result = np.copy(result)
        inverted_result[:,:,:3] = inverted
        
        # 2. Add a diagonal line
        diagonal = np.copy(result)
        for i in range(min(diagonal.shape[0], diagonal.shape[1])):
            diagonal[i, i, :3] = [1.0, 0.0, 0.0]  # Red diagonal
        
        # 3. Apply a simple kernel (edge detection)
        from scipy.ndimage import convolve
        # Convert to grayscale
        gray = np.mean(result[:,:,:3], axis=2)
        # Apply edge detection kernel
        kernel = np.array([[-1, -1, -1],
                          [-1,  8, -1],
                          [-1, -1, -1]])
        edges = convolve(gray, kernel)
        # Normalize to [0, 1]
        edges = (edges - edges.min()) / (edges.max() - edges.min())
        # Create RGB image
        edge_result = np.zeros_like(result)
        edge_result[:,:,0] = edges
        edge_result[:,:,1] = edges
        edge_result[:,:,2] = edges
        edge_result[:,:,3] = 1.0  # Full alpha
        
        # Save each result
        self.__class__.engine.save_image(inverted_result, 
                                         os.path.join(self.output_dir, "pixel_inverted.png"))
        self.__class__.engine.save_image(diagonal, 
                                         os.path.join(self.output_dir, "pixel_diagonal.png"))
        self.__class__.engine.save_image(edge_result, 
                                         os.path.join(self.output_dir, "pixel_edge_detect.png"))
        
        # Verify files were created
        for filename in ["pixel_inverted.png", "pixel_diagonal.png", "pixel_edge_detect.png"]:
            path = os.path.join(self.output_dir, filename)
            self.assertTrue(os.path.exists(path))
            self.assertGreater(os.path.getsize(path), 0)


if __name__ == "__main__":
    unittest.main()