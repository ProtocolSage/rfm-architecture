#!/usr/bin/env python
"""
Test script for UI progress reporting integration.

This script tests the integration of the progress reporting system with the UI
by simulating progress operations and verifying that the UI components update correctly.
"""

import os
import sys
import time
import threading
import asyncio
import dearpygui.dearpygui as dpg
import uuid
import logging
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ui_progress_test")

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import components to test
from rfm.core.websocket_server import start_websocket_server
from rfm.core.progress import ProgressReporter, get_progress_manager
from ui.rfm_ui.websocket_client import get_websocket_client
from ui.rfm_ui.components.progress_manager import WebSocketProgressManager
from ui.rfm_ui.theme import Colors


def run_server():
    """Run the WebSocket server in a separate thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Run the server
    async def run_server_async():
        from pathlib import Path
        try:
            # Create data directory
            data_dir = Path("./data/progress")
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Start server
            server = await start_websocket_server("localhost", 8765)
            logger.info("WebSocket server started on localhost:8765")
            
            # Keep server running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Server shutdown requested")
        except Exception as e:
            logger.error(f"Error running WebSocket server: {e}")
    
    # Start the server
    loop.run_until_complete(run_server_async())


def run_test_operations():
    """Run test operations to verify UI integration."""
    # Initialize WebSocket client
    client = get_websocket_client("ws://localhost:8765")
    
    # Start client
    client.start()
    logger.info("WebSocket client started")
    
    # Wait for connection
    time.sleep(2)
    
    # Create event loop for progress manager
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Create progress manager
    progress_manager = get_progress_manager()
    
    try:
        # Run operations in a loop
        for i in range(3):
            # Run a successful operation
            operation_id = f"test_success_{uuid.uuid4().hex[:8]}"
            name = f"Test Success Operation {i+1}"
            
            # Create progress reporter
            reporter = ProgressReporter("test_operation", name)
            
            # Register with progress manager
            async def add_operation():
                await progress_manager.add_operation(reporter)
            
            loop.run_until_complete(add_operation())
            
            # Report progress
            reporter.report_progress(0, "Starting operation")
            time.sleep(1)
            
            for step in range(1, 5):
                reporter.report_progress(step * 20, f"Step {step} completed")
                time.sleep(1)
            
            reporter.report_progress(100, "Operation completed")
            time.sleep(0.5)
            
            reporter.report_completed()
            time.sleep(2)
        
        # Run a failed operation
        operation_id = f"test_failure_{uuid.uuid4().hex[:8]}"
        name = "Test Failure Operation"
        
        # Create progress reporter
        reporter = ProgressReporter("test_operation", name)
        
        # Register with progress manager
        async def add_operation():
            await progress_manager.add_operation(reporter)
        
        loop.run_until_complete(add_operation())
        
        # Report progress
        reporter.report_progress(0, "Starting operation")
        time.sleep(1)
        
        reporter.report_progress(25, "Step 1 completed")
        time.sleep(1)
        
        # Report failure
        reporter.report_failed("Simulated error for testing")
        time.sleep(3)
        
        # Run an operation that will be canceled
        operation_id = f"test_cancel_{uuid.uuid4().hex[:8]}"
        name = "Test Cancel Operation"
        
        # Create progress reporter
        reporter = ProgressReporter("test_operation", name)
        
        # Register with progress manager
        async def add_operation():
            await progress_manager.add_operation(reporter)
        
        loop.run_until_complete(add_operation())
        
        # Report progress
        reporter.report_progress(0, "Starting operation")
        time.sleep(1)
        
        reporter.report_progress(25, "Step 1 completed")
        time.sleep(1)
        
        # Request cancellation
        reporter.request_cancellation()
        
        # Check and report cancellation
        if reporter.should_cancel():
            logger.info("Operation cancellation detected")
            reporter.report_canceled()
        
        time.sleep(3)
        
    finally:
        # Stop client
        client.stop()
        logger.info("WebSocket client stopped")


def ui_thread():
    """Run the UI thread to display progress."""
    # Create context
    dpg.create_context()
    
    # Create viewport
    dpg.create_viewport(title="Progress Reporting Test", width=800, height=600)
    
    # Set up UI
    with dpg.window(label="Progress Test", width=780, height=580):
        # Header
        dpg.add_text("Progress Reporting System Test")
        dpg.add_separator()
        
        # Info text
        dpg.add_text("This test will simulate several operations with different outcomes:")
        dpg.add_text("1. Three successful operations")
        dpg.add_text("2. One failed operation")
        dpg.add_text("3. One canceled operation")
        
        dpg.add_separator()
        
        # Add progress container
        with dpg.group(tag="progress_container"):
            pass
        
        dpg.add_separator()
        
        # Status text
        dpg.add_text("Status: Starting test...", tag="status_text")
        
        # Controls
        with dpg.group(horizontal=True):
            dpg.add_button(label="Start Test", callback=lambda: start_test_thread(), tag="start_button")
            dpg.add_button(label="Exit", callback=lambda: dpg.stop_dearpygui())
    
    # Setup progress manager
    websocket_client = get_websocket_client("ws://localhost:8765")
    websocket_client.start()
    
    # Create progress manager after UI is initialized
    def setup_progress_manager():
        progress_container = dpg.get_item_children("progress_container", slot=1)[0]
        progress_manager = WebSocketProgressManager(
            parent_id=progress_container,
            websocket_url="ws://localhost:8765",
            show_title=True,
            initial_visible=True
        )
        
        # Change status text when progress manager is created
        dpg.set_value("status_text", "Status: Ready - Press 'Start Test' to begin")
    
    dpg.set_frame_callback(1, setup_progress_manager)
    
    # Function to start test thread
    def start_test_thread():
        # Disable start button
        dpg.configure_item("start_button", enabled=False)
        
        # Update status
        dpg.set_value("status_text", "Status: Running tests...")
        
        # Start test operations in separate thread
        test_thread = threading.Thread(target=run_test_operations)
        test_thread.daemon = True
        test_thread.start()
        
        # Function to check if test thread is done
        def check_test_thread():
            if not test_thread.is_alive():
                dpg.set_value("status_text", "Status: Tests completed")
                dpg.configure_item("start_button", enabled=True)
                return
            
            # Check again in 1 second
            dpg.set_frame_callback(1, check_test_thread)
        
        # Start checking test thread status
        dpg.set_frame_callback(1, check_test_thread)
    
    # Setup viewport
    dpg.setup_dearpygui()
    dpg.show_viewport()
    
    # Start UI event loop
    try:
        dpg.start_dearpygui()
    finally:
        # Clean up
        dpg.destroy_context()


def main():
    """Main entry point."""
    # Start server in a separate thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(2)
    
    try:
        # Run UI thread (will block until UI is closed)
        ui_thread()
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    
    logger.info("Test completed")


if __name__ == "__main__":
    main()