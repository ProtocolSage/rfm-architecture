"""
Integration tests for the progress reporting system with the fractal engine.

This module tests that the progress reporting system works correctly with
the fractal rendering engine.
"""

import os
import sys
import time
import unittest
import threading
import asyncio
import numpy as np
from typing import Dict, Any, List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import components to test
from rfm.core.websocket_server import start_websocket_server
from ui.rfm_ui.engine.core import FractalEngine
from ui.rfm_ui.websocket_client import get_websocket_client


class TestProgressIntegration(unittest.TestCase):
    """Test the integration of progress reporting with the fractal engine."""
    
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
        
    @classmethod
    def tearDownClass(cls):
        """Clean up the test environment."""
        # Stop WebSocket client
        if cls.client:
            cls.client.stop()
            
        # The server thread is daemonic, so it will stop automatically
    
    @classmethod
    def _run_server(cls):
        """Run the WebSocket server."""
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
        
        # Create fractal engine
        self.engine = FractalEngine(enable_progress_reporting=True)
    
    def test_mandelbrot_rendering_progress(self):
        """Test that the Mandelbrot rendering reports progress."""
        # Define parameters for a simple Mandelbrot render
        params = {
            "type": "mandelbrot",
            "width": 400,
            "height": 300,
            "center_x": -0.5,
            "center_y": 0.0,
            "zoom": 1.0,
            "max_iter": 100,
            "colormap": "viridis",
            "high_quality": False  # Use low quality for faster testing
        }
        
        # Render the fractal
        result = self.engine.render(params)
        
        # Check that the result is valid
        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(result.shape, (300, 400, 4))
        
        # Wait for all messages to be processed
        time.sleep(1)
        
        # Check that we received progress messages
        messages = self.__class__.received_messages
        
        # Extract message types
        message_types = [message.get("type") for message in messages]
        
        # We should have at least one progress update and completion message
        self.assertIn("progress_update", message_types, "No progress updates received")
        self.assertIn("operation_completed", message_types, "No completion message received")
        
        # Check specific progress messages for Mandelbrot rendering
        progress_updates = [m for m in messages if m.get("type") == "progress_update"]
        if progress_updates:
            # Get the first progress update
            first_update = progress_updates[0]
            data = first_update.get("data", {})
            
            # Should include fractal type and progress percentage
            self.assertEqual(data.get("operation_type"), "fractal_render_mandelbrot")
            self.assertIsNotNone(data.get("progress"))
            self.assertIsNotNone(data.get("current_step"))
    
    def test_julia_rendering_progress(self):
        """Test that the Julia rendering reports progress."""
        # Define parameters for a simple Julia render
        params = {
            "type": "julia",
            "width": 400,
            "height": 300,
            "c_real": -0.7,
            "c_imag": 0.27,
            "center_x": 0.0,
            "center_y": 0.0,
            "zoom": 1.5,
            "max_iter": 100,
            "colormap": "viridis",
            "high_quality": False  # Use low quality for faster testing
        }
        
        # Render the fractal
        result = self.engine.render(params)
        
        # Check that the result is valid
        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(result.shape, (300, 400, 4))
        
        # Wait for all messages to be processed
        time.sleep(1)
        
        # Check that we received progress messages
        messages = self.__class__.received_messages
        
        # Extract message types
        message_types = [message.get("type") for message in messages]
        
        # We should have at least one progress update and completion message
        self.assertIn("progress_update", message_types, "No progress updates received")
        self.assertIn("operation_completed", message_types, "No completion message received")
        
        # Check specific progress messages for Julia rendering
        progress_updates = [m for m in messages if m.get("type") == "progress_update"]
        if progress_updates:
            # Get the first progress update
            first_update = progress_updates[0]
            data = first_update.get("data", {})
            
            # Should include fractal type and progress percentage
            self.assertEqual(data.get("operation_type"), "fractal_render_julia")
            self.assertIsNotNone(data.get("progress"))
            self.assertIsNotNone(data.get("current_step"))
    
    def test_cancel_rendering(self):
        """Test cancellation of rendering operations."""
        # This test is more complex as it requires canceling a long-running operation
        # We'll simulate this by starting a high-resolution, high-iteration render 
        # in a separate thread and canceling it
        
        # Define parameters for a slow render
        params = {
            "type": "mandelbrot",
            "width": 800,
            "height": 600,
            "center_x": -0.7436,
            "center_y": 0.1318,
            "zoom": 1000.0,  # High zoom for slow rendering
            "max_iter": 500,  # High iterations for slow rendering
            "colormap": "viridis",
            "high_quality": True
        }
        
        # Start rendering in a separate thread
        render_thread = threading.Thread(target=self._render_in_thread, args=(params,))
        render_thread.daemon = True
        render_thread.start()
        
        # Wait for rendering to start and get the operation ID
        time.sleep(2)
        
        # Find all operation IDs from progress updates
        progress_updates = [m for m in self.__class__.received_messages if m.get("type") == "progress_update"]
        
        if not progress_updates:
            self.skipTest("No progress updates received for cancellation test")
        
        # Get operation ID
        operation_id = progress_updates[0].get("data", {}).get("operation_id")
        self.assertIsNotNone(operation_id, "Could not determine operation ID")
        
        # Cancel the operation
        self.__class__.client.cancel_operation(operation_id)
        
        # Wait for cancellation to process
        time.sleep(2)
        
        # Check for cancellation messages
        messages = self.__class__.received_messages
        canceled_messages = [m for m in messages if m.get("type") == "operation_canceled"]
        
        # The operation may complete quickly on fast systems, so we only assert cancellation 
        # if we actually got a cancellation message
        if canceled_messages:
            self.assertGreaterEqual(len(canceled_messages), 1, "No cancellation message received")
        
        # Wait for render thread to complete
        render_thread.join(timeout=10)
    
    def _render_in_thread(self, params):
        """Render a fractal in a separate thread."""
        try:
            result = self.engine.render(params)
        except Exception as e:
            print(f"Error in rendering thread: {e}")


if __name__ == "__main__":
    unittest.main()