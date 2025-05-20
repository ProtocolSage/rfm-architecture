#!/usr/bin/env python
"""
Test script for WebSocket client and server communication.

This script tests the WebSocket client and server components of the 
real-time progress reporting system by sending test operations and
verifying that messages are correctly transmitted.
"""

import os
import sys
import time
import asyncio
import threading
import json
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("websocket_test")

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import components to test
from rfm.core.websocket_server import start_websocket_server
from rfm.core.progress import ProgressReporter, get_progress_manager
from ui.rfm_ui.websocket_client import get_websocket_client, WebSocketClient


def run_server():
    """Run the WebSocket server in a separate thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Run the server
    async def run_server_async():
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


def message_handler(message):
    """Handle received WebSocket messages."""
    message_type = message.get("type")
    
    if message_type == "progress_update":
        data = message.get("data", {})
        operation_id = data.get("operation_id")
        progress = data.get("progress")
        current_step = data.get("current_step")
        logger.info(f"Progress update for {operation_id}: {progress}% - {current_step}")
    
    elif message_type == "operation_started":
        operation = message.get("operation", {})
        operation_id = operation.get("operation_id")
        name = operation.get("name")
        logger.info(f"Operation started: {name} (ID: {operation_id})")
    
    elif message_type == "operation_completed":
        operation_id = message.get("operation_id")
        logger.info(f"Operation completed: {operation_id}")
    
    elif message_type == "operation_failed":
        operation_id = message.get("operation_id")
        details = message.get("details", {})
        error_message = details.get("error_message", "Unknown error")
        logger.info(f"Operation failed: {operation_id} - {error_message}")
    
    elif message_type == "operation_canceled":
        operation_id = message.get("operation_id")
        logger.info(f"Operation canceled: {operation_id}")
    
    elif message_type == "connection_status":
        status = message.get("status")
        logger.info(f"Connection status: {status}")


async def run_test_operations():
    """Run test operations to verify WebSocket communication."""
    # Initialize WebSocket client
    client = get_websocket_client("ws://localhost:8765")
    
    # Register message handlers
    client.add_callback("progress_update", message_handler)
    client.add_callback("operation_started", message_handler)
    client.add_callback("operation_completed", message_handler)
    client.add_callback("operation_failed", message_handler)
    client.add_callback("operation_canceled", message_handler)
    client.add_callback("connection_status", message_handler)
    
    # Start client
    client.start()
    logger.info("WebSocket client started")
    
    # Wait for connection
    await asyncio.sleep(2)
    
    if not client.is_connected():
        logger.error("Client failed to connect to server")
        return
    
    # Create progress manager
    progress_manager = get_progress_manager()
    
    try:
        # Run a successful operation
        logger.info("\n===== Running successful operation =====")
        
        # Create progress reporter for success test
        operation_id = f"test_success_{uuid.uuid4().hex[:8]}"
        reporter_success = ProgressReporter("test_operation", f"Test Success Operation {operation_id}")
        
        # Register with progress manager
        await progress_manager.add_operation(reporter_success)
        
        # Report progress
        reporter_success.report_progress(0, "Starting operation")
        await asyncio.sleep(0.5)
        
        reporter_success.report_progress(25, "Step 1 completed")
        await asyncio.sleep(0.5)
        
        reporter_success.report_progress(50, "Step 2 completed")
        await asyncio.sleep(0.5)
        
        reporter_success.report_progress(75, "Step 3 completed")
        await asyncio.sleep(0.5)
        
        reporter_success.report_progress(100, "Operation completed")
        await asyncio.sleep(0.5)
        
        reporter_success.report_completed()
        await asyncio.sleep(1)
        
        # Run a failed operation
        logger.info("\n===== Running failed operation =====")
        
        # Create progress reporter for failure test
        operation_id = f"test_failure_{uuid.uuid4().hex[:8]}"
        reporter_failure = ProgressReporter("test_operation", f"Test Failure Operation {operation_id}")
        
        # Register with progress manager
        await progress_manager.add_operation(reporter_failure)
        
        # Report progress
        reporter_failure.report_progress(0, "Starting operation")
        await asyncio.sleep(0.5)
        
        reporter_failure.report_progress(25, "Step 1 completed")
        await asyncio.sleep(0.5)
        
        # Report failure
        reporter_failure.report_failed("Simulated error for testing")
        await asyncio.sleep(1)
        
        # Run a canceled operation
        logger.info("\n===== Running canceled operation =====")
        
        # Create progress reporter for cancellation test
        operation_id = f"test_cancel_{uuid.uuid4().hex[:8]}"
        reporter_cancel = ProgressReporter("test_operation", f"Test Cancel Operation {operation_id}")
        
        # Register with progress manager
        await progress_manager.add_operation(reporter_cancel)
        
        # Report progress
        reporter_cancel.report_progress(0, "Starting operation")
        await asyncio.sleep(0.5)
        
        reporter_cancel.report_progress(25, "Step 1 completed")
        await asyncio.sleep(0.5)
        
        # Simulate user cancellation
        reporter_cancel.request_cancellation()
        await asyncio.sleep(0.5)
        
        # Check if operation should be canceled
        if reporter_cancel.should_cancel():
            logger.info("Operation cancellation detected")
            reporter_cancel.report_canceled()
        
        await asyncio.sleep(1)
        
        # List active operations
        client.list_operations()
        await asyncio.sleep(1)
        
        logger.info("\n===== Tests completed =====")
        
    finally:
        # Stop client
        client.stop()
        logger.info("WebSocket client stopped")


def main():
    """Main entry point."""
    # Start server in a separate thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(2)
    
    try:
        # Run test operations
        asyncio.run(run_test_operations())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    
    logger.info("Test completed")


if __name__ == "__main__":
    main()