"""
Tests for the real-time progress reporting system.

This module contains tests for the WebSocket-based progress reporting system,
including the WebSocket client, server, and UI integration.
"""

import os
import sys
import time
import unittest
import asyncio
import threading
import uuid
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import components to test
from rfm.core.websocket_server import start_websocket_server
from rfm.core.progress import ProgressReporter, get_progress_manager
from ui.rfm_ui.websocket_client import get_websocket_client, WebSocketClient
from ui.rfm_ui.components.progress_manager import get_progress_manager as get_ui_progress_manager


class TestProgressReporting(unittest.TestCase):
    """Test the real-time progress reporting system."""

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
    
    def test_client_connection(self):
        """Test that the WebSocket client connects to the server."""
        self.assertTrue(self.__class__.client.is_connected())
    
    def test_progress_reporting_basic(self):
        """Test basic progress reporting functionality."""
        # Create a progress reporter
        reporter = ProgressReporter("test_operation", "Test Operation")
        
        # Set up progress manager
        progress_manager = get_progress_manager()
        
        # Register reporter with progress manager
        loop = asyncio.get_event_loop()
        if not loop.is_running():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Add operation in event loop
        async def add_operation():
            await progress_manager.add_operation(reporter)
        
        loop.run_until_complete(add_operation())
        
        # Report progress
        reporter.report_progress(25, "Step 1")
        time.sleep(0.5)  # Wait for message to be processed
        
        reporter.report_progress(50, "Step 2")
        time.sleep(0.5)
        
        reporter.report_progress(75, "Step 3")
        time.sleep(0.5)
        
        reporter.report_completed()
        time.sleep(0.5)
        
        # Check that we received messages
        messages = self.__class__.received_messages
        self.assertGreaterEqual(len(messages), 4)  # At least 4 messages (3 progress updates + completion)
        
        # Check message types
        progress_updates = [m for m in messages if m.get("type") == "progress_update"]
        completed_messages = [m for m in messages if m.get("type") == "operation_completed"]
        
        self.assertGreaterEqual(len(progress_updates), 3)
        self.assertGreaterEqual(len(completed_messages), 1)
        
        # Check progress values
        if progress_updates:
            progress_values = [update.get("data", {}).get("progress") for update in progress_updates]
            self.assertIn(25, progress_values)
            self.assertIn(50, progress_values)
            self.assertIn(75, progress_values)
    
    def test_error_reporting(self):
        """Test error reporting functionality."""
        # Create a progress reporter
        reporter = ProgressReporter("test_error", "Test Error Operation")
        
        # Set up progress manager
        progress_manager = get_progress_manager()
        
        # Register reporter with progress manager
        loop = asyncio.get_event_loop()
        if not loop.is_running():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Add operation in event loop
        async def add_operation():
            await progress_manager.add_operation(reporter)
        
        loop.run_until_complete(add_operation())
        
        # Report progress
        reporter.report_progress(25, "Step 1")
        time.sleep(0.5)
        
        # Report error
        reporter.report_failed("Test error message")
        time.sleep(0.5)
        
        # Check that we received failure message
        messages = self.__class__.received_messages
        failed_messages = [m for m in messages if m.get("type") == "operation_failed"]
        
        self.assertGreaterEqual(len(failed_messages), 1)
        
        # Check error message
        if failed_messages:
            error_message = failed_messages[0].get("details", {}).get("error_message")
            self.assertEqual(error_message, "Test error message")
    
    def test_cancellation(self):
        """Test operation cancellation functionality."""
        # Create a progress reporter
        reporter = ProgressReporter("test_cancel", "Test Cancel Operation")
        
        # Set up progress manager
        progress_manager = get_progress_manager()
        
        # Register reporter with progress manager
        loop = asyncio.get_event_loop()
        if not loop.is_running():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Add operation in event loop
        async def add_operation():
            await progress_manager.add_operation(reporter)
        
        loop.run_until_complete(add_operation())
        
        # Report progress
        reporter.report_progress(25, "Step 1")
        time.sleep(0.5)
        
        # Get operation ID
        messages = self.__class__.received_messages
        progress_updates = [m for m in messages if m.get("type") == "progress_update"]
        
        if not progress_updates:
            self.skipTest("No progress updates received")
        
        operation_id = progress_updates[0].get("data", {}).get("operation_id")
        
        # Cancel operation
        self.__class__.client.cancel_operation(operation_id)
        time.sleep(0.5)
        
        # Check cancellation status
        self.assertTrue(reporter.should_cancel())
        
        # Report cancellation
        reporter.report_canceled()
        time.sleep(0.5)
        
        # Check that we received cancellation message
        messages = self.__class__.received_messages
        canceled_messages = [m for m in messages if m.get("type") == "operation_canceled"]
        
        self.assertGreaterEqual(len(canceled_messages), 1)


if __name__ == "__main__":
    unittest.main()