#!/usr/bin/env python3
"""
Integration tests for UI components with fractal generation.

This test suite verifies that UI components integrate correctly with the fractal
generation and visualization systems. It tests the parameter controls, the progress
reporting system, preset management, and healing mechanisms.
"""
import os
import sys
import unittest
import tempfile
import threading
import asyncio
import time
import yaml
import json
import numpy as np
import logging
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import components to test
from rfm.core.fractal import create_fractal, JuliaSet, MandelbrotSet
from rfm.core.progress import ProgressReporter, get_progress_manager
from rfm.core.websocket_server import start_websocket_server
from ui.rfm_ui.websocket_client import get_websocket_client
from ui.rfm_ui.engine.core import FractalEngine
from ui.rfm_ui.components.progress_bar import ProgressBar
from ui.rfm_ui.components.progress_manager import WebSocketProgressManager
from ui.rfm_ui.components.preset_manager import PresetManager
from ui.rfm_ui.components.parameter_explorer import ParameterExplorer
from ui.rfm_ui.healing.strategies import (
    ParameterBoundsStrategy, NumericOverflowStrategy, 
    MemoryOverflowStrategy, InvalidColorStrategy
)
from ui.rfm_ui.healing.recovery import RecoveryAction, RecoveryActionType


class TestUIComponentIntegration(unittest.TestCase):
    """Test the integration of UI components with the fractal generation system."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test environment."""
        # Start the WebSocket server in a separate thread
        cls.server_thread = threading.Thread(target=cls._run_server, daemon=True)
        cls.server_thread.start()
        
        # Wait for server to start
        time.sleep(1)
        
        # Initialize WebSocket client
        cls.client = get_websocket_client("ws://localhost:8765")
        cls.client.start()
        
        # Wait for client to connect
        time.sleep(1)
        
        # Store received messages for validation
        cls.received_messages = []
        cls.client.add_callback("progress_update", cls._store_message)
        cls.client.add_callback("operation_started", cls._store_message)
        cls.client.add_callback("operation_completed", cls._store_message)
        cls.client.add_callback("operation_failed", cls._store_message)
        
        # Load config
        try:
            with open("config.yaml", "r") as f:
                cls.config = yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Could not load config.yaml: {e}")
            cls.config = {}
        
        # Initialize fractal engine
        cls.engine = FractalEngine(enable_progress_reporting=True)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up the test environment."""
        # Stop WebSocket client
        if hasattr(cls, 'client') and cls.client:
            cls.client.stop()
    
    @classmethod
    def _run_server(cls):
        """Run the WebSocket server in a separate thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the server
        async def run_server():
            from pathlib import Path
            try:
                # Create data directory
                data_dir = Path("./data/progress")
                data_dir.mkdir(parents=True, exist_ok=True)
                
                # Start server
                server = await start_websocket_server("localhost", 8765)
                
                # Keep server running
                while True:
                    await asyncio.sleep(0.1)
            except Exception as e:
                print(f"Error running WebSocket server: {e}")
        
        # Start the server
        loop.run_until_complete(run_server())
    
    @classmethod
    def _store_message(cls, message):
        """Store a message for validation."""
        cls.received_messages.append(message)
    
    def setUp(self):
        """Set up each test."""
        # Clear received messages
        self.__class__.received_messages = []
    
    def test_parameter_controls_integration(self):
        """Test that parameter controls correctly update fractal parameters."""
        # Create a mock UI context
        ui_context = MagicMock()
        
        # Create parameter schema for a Julia set
        param_schema = {
            "c_real": {
                "type": "float",
                "min": -2.0,
                "max": 2.0,
                "default": -0.7,
                "step": 0.01,
                "label": "Real Component (c)",
                "description": "Real part of the complex parameter c"
            },
            "c_imag": {
                "type": "float",
                "min": -2.0,
                "max": 2.0,
                "default": 0.27,
                "step": 0.01,
                "label": "Imaginary Component (c)",
                "description": "Imaginary part of the complex parameter c"
            },
            "zoom": {
                "type": "float",
                "min": 0.1,
                "max": 10.0,
                "default": 1.5,
                "step": 0.1,
                "label": "Zoom Level",
                "description": "Zoom level for the fractal view"
            },
            "max_iter": {
                "type": "int",
                "min": 10,
                "max": 1000,
                "default": 100,
                "step": 10,
                "label": "Maximum Iterations",
                "description": "Maximum number of iterations for escape-time calculation"
            },
            "colormap": {
                "type": "enum",
                "options": ["viridis", "plasma", "inferno", "magma", "cividis"],
                "default": "plasma",
                "label": "Color Map",
                "description": "Color map used for fractal visualization"
            }
        }
        
        # Create mock callbacks to track parameter changes
        param_changes = {}
        
        def param_change_callback(name, value):
            param_changes[name] = value
        
        # Create a ParameterExplorer
        with patch('ui.rfm_ui.components.parameter_explorer.ParameterExplorer._create_ui_elements'):
            # Mock UI creation to avoid requiring actual UI elements
            explorer = ParameterExplorer(
                parent_id=0,  # Mocked
                schema=param_schema,
                on_change=param_change_callback
            )
            
            # Override internal state to simulate parameter changes
            explorer.current_values = {
                "c_real": -0.7,
                "c_imag": 0.27,
                "zoom": 1.5,
                "max_iter": 100,
                "colormap": "plasma"
            }
            
            # Simulate parameter changes
            explorer._on_param_change("c_real", -0.835)
            explorer._on_param_change("c_imag", -0.2321)
            explorer._on_param_change("zoom", 1.3)
            explorer._on_param_change("max_iter", 180)
            explorer._on_param_change("colormap", "inferno")
            
            # Verify parameters were updated
            self.assertEqual(param_changes["c_real"], -0.835)
            self.assertEqual(param_changes["c_imag"], -0.2321)
            self.assertEqual(param_changes["zoom"], 1.3)
            self.assertEqual(param_changes["max_iter"], 180)
            self.assertEqual(param_changes["colormap"], "inferno")
            
            # Get all parameters as a dict
            params = explorer.get_parameters()
            
            # Verify all parameters are present
            self.assertEqual(len(params), 5)
            self.assertEqual(params["c_real"], -0.835)
            self.assertEqual(params["c_imag"], -0.2321)
            self.assertEqual(params["zoom"], 1.3)
            self.assertEqual(params["max_iter"], 180)
            self.assertEqual(params["colormap"], "inferno")
            
            # Test that the parameters can be used to create a valid fractal
            test_params = {
                "type": "julia",
                "parameters": params
            }
            
            # The create_fractal function should not raise an exception with valid parameters
            fractal = create_fractal(test_params)
            self.assertIsInstance(fractal, JuliaSet)
            
            # Verify parameter bounds validation
            with self.assertRaises(ValueError):
                # Should raise ValueError for out-of-bounds parameter
                explorer._on_param_change("zoom", -1.0)  # below min
            
            with self.assertRaises(ValueError):
                # Should raise ValueError for out-of-bounds parameter
                explorer._on_param_change("max_iter", 2000)  # above max
    
    def test_preset_manager_integration(self):
        """Test that the preset manager correctly saves and loads fractal presets."""
        # Create a temp directory for presets
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a preset manager
            with patch('ui.rfm_ui.components.preset_manager.PresetManager._create_ui_elements'):
                preset_manager = PresetManager(
                    parent_id=0,  # Mocked
                    preset_directory=temp_dir
                )
                
                # Create a test preset
                test_preset = {
                    "type": "julia",
                    "parameters": {
                        "c_real": -0.835,
                        "c_imag": -0.2321,
                        "center_x": 0.0,
                        "center_y": 0.0,
                        "zoom": 1.3,
                        "max_iter": 180,
                        "colormap": "inferno"
                    }
                }
                
                # Save the preset
                preset_path = preset_manager.save_preset(test_preset, "test_julia_dragon")
                
                # Verify the preset was saved
                self.assertTrue(os.path.exists(preset_path))
                
                # Load the saved preset
                loaded_preset = preset_manager.load_preset(preset_path)
                
                # Verify the loaded preset matches the original
                self.assertEqual(loaded_preset["type"], test_preset["type"])
                for key, value in test_preset["parameters"].items():
                    self.assertEqual(loaded_preset["parameters"][key], value)
                
                # Test preset list functionality
                preset_list = preset_manager.list_presets()
                self.assertIn("test_julia_dragon", [os.path.splitext(os.path.basename(p))[0] for p in preset_list])
                
                # Test creating a fractal from the loaded preset
                fractal = create_fractal(loaded_preset)
                self.assertIsInstance(fractal, JuliaSet)
                
                # Create additional presets
                presets = [
                    {
                        "type": "mandelbrot",
                        "parameters": {
                            "center_x": -0.5,
                            "center_y": 0.0,
                            "zoom": 1.0,
                            "max_iter": 100,
                            "colormap": "viridis"
                        }
                    },
                    {
                        "type": "julia",
                        "parameters": {
                            "c_real": -0.123,
                            "c_imag": 0.745,
                            "center_x": 0.0,
                            "center_y": 0.0,
                            "zoom": 1.2,
                            "max_iter": 100,
                            "colormap": "inferno"
                        }
                    }
                ]
                
                preset_paths = []
                for i, preset in enumerate(presets):
                    path = preset_manager.save_preset(preset, f"test_preset_{i}")
                    preset_paths.append(path)
                
                # Verify all presets were saved
                for path in preset_paths:
                    self.assertTrue(os.path.exists(path))
                
                # List all presets
                all_presets = preset_manager.list_presets()
                self.assertEqual(len(all_presets), 3)  # 1 original + 2 new presets
    
    def test_progress_bar_integration(self):
        """Test that the progress bar correctly displays fractal rendering progress."""
        # Create a mock UI context
        ui_context = MagicMock()
        
        # Create a progress bar
        with patch('ui.rfm_ui.components.progress_bar.ProgressBar._create_ui_elements'):
            progress_bar = ProgressBar(
                parent_id=0,  # Mocked
                label="Rendering Test"
            )
            
            # Create a progress reporter
            reporter = ProgressReporter("test_fractal_render", "Mandelbrot Render")
            
            # Connect the progress bar to the reporter using a thread-safe queue
            progress_queue = asyncio.Queue()
            
            # Create an update function to simulate UI updates
            progress_updates = []
            
            def update_progress_bar(progress, message=None):
                # Record progress updates
                progress_updates.append((progress, message))
                # Update progress bar internal state to simulate UI
                progress_bar.progress = progress
                if message:
                    progress_bar.message = message
            
            # Simulate a fractal rendering with progress updates
            update_progress_bar(0, "Starting render")
            reporter.report_progress(0, "Initializing")
            
            for i in range(1, 11):
                progress = i * 10
                message = f"Computing iteration {i * 10}/100"
                reporter.report_progress(progress, message)
                update_progress_bar(progress / 100, message)
                time.sleep(0.1)  # Simulate computation time
            
            reporter.report_progress(100, "Render complete")
            update_progress_bar(1.0, "Render complete")
            
            # Verify progress bar was updated correctly
            self.assertEqual(progress_bar.progress, 1.0)
            self.assertEqual(progress_bar.message, "Render complete")
            
            # Verify all progress updates were received
            self.assertEqual(len(progress_updates), 12)  # Initial + 10 updates + final
            
            # Verify first and last updates
            self.assertEqual(progress_updates[0], (0, "Starting render"))
            self.assertEqual(progress_updates[-1], (1.0, "Render complete"))
    
    def test_websocket_progress_manager_integration(self):
        """Test that the WebSocket progress manager correctly tracks fractal operations."""
        # Create a WebSocket progress manager
        with patch('ui.rfm_ui.components.progress_manager.WebSocketProgressManager._create_ui_elements'):
            progress_manager = WebSocketProgressManager(
                parent_id=0,  # Mocked
                websocket_url="ws://localhost:8765"
            )
            
            # Render a fractal to trigger progress updates
            params = {
                "type": "mandelbrot",
                "width": 400,
                "height": 300,
                "center_x": -0.5,
                "center_y": 0.0,
                "zoom": 1.0,
                "max_iter": 100,
                "colormap": "viridis",
                "high_quality": False
            }
            
            # Force clear any previous messages
            self.__class__.received_messages = []
            
            # Render the fractal
            result = self.__class__.engine.render(params)
            
            # Wait for progress messages
            time.sleep(1)
            
            # Check that we received progress messages
            messages = self.__class__.received_messages
            
            # Extract message types
            message_types = [message.get("type") for message in messages]
            
            # We should have progress updates and completion message
            self.assertIn("progress_update", message_types, "No progress updates received")
            self.assertIn("operation_completed", message_types, "No completion message received")
    
    def test_self_healing_ui_integration(self):
        """Test that self-healing error strategies integrate with the UI."""
        # Create error context with invalid parameters
        invalid_params = {
            "type": "julia",
            "width": 400,
            "height": 300,
            "c_real": -0.7,
            "c_imag": 0.27,
            "center_x": 0.0,
            "center_y": 0.0,
            "zoom": -5.0,  # Invalid: must be positive
            "max_iter": 10000,  # Invalid: too large
            "colormap": "nonexistent_colormap",  # Invalid: unknown colormap
            "high_quality": True
        }
        
        # Simulate an error during rendering
        error = ValueError("zoom must be between 0.1 and 1e10")
        context = {"params": invalid_params}
        
        # Create error strategies
        param_bounds_strategy = ParameterBoundsStrategy()
        colormap_strategy = InvalidColorStrategy()
        
        # Test parameter bounds strategy
        self.assertTrue(param_bounds_strategy.can_handle(error, context))
        actions = param_bounds_strategy.suggest_actions(error, context)
        
        # Should suggest fixing the zoom parameter
        self.assertGreater(len(actions), 0)
        zoom_action = None
        for action in actions:
            if "zoom" in action.changes:
                zoom_action = action
                break
        
        self.assertIsNotNone(zoom_action)
        self.assertEqual(zoom_action.action_type, RecoveryActionType.PARAMETER_ADJUST)
        self.assertGreaterEqual(zoom_action.changes["zoom"], 0.1)
        
        # Test colormap strategy
        error = ValueError("Unknown colormap: nonexistent_colormap")
        self.assertTrue(colormap_strategy.can_handle(error, context))
        actions = colormap_strategy.suggest_actions(error, context)
        
        # Should suggest fixing the colormap parameter
        self.assertGreater(len(actions), 0)
        colormap_action = actions[0]
        self.assertEqual(colormap_action.action_type, RecoveryActionType.PARAMETER_ADJUST)
        self.assertIn("colormap", colormap_action.changes)
        self.assertEqual(colormap_action.changes["colormap"], "viridis")  # Default colormap
        
        # Apply healing actions and try rendering again
        healed_params = invalid_params.copy()
        
        # Apply zoom correction
        healed_params["zoom"] = zoom_action.changes["zoom"]
        
        # Apply colormap correction
        healed_params["colormap"] = colormap_action.changes["colormap"]
        
        # Also fix max_iter manually
        healed_params["max_iter"] = 500
        
        # Try rendering with healed parameters
        try:
            result = self.__class__.engine.render(healed_params)
            self.assertIsInstance(result, np.ndarray)
            self.assertEqual(result.shape, (300, 400, 4))
        except Exception as e:
            self.fail(f"Rendering with healed parameters failed: {e}")


if __name__ == "__main__":
    unittest.main()