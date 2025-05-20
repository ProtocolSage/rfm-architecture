#!/usr/bin/env python
"""
Resilience testing for the WebSocket progress reporting system.

This script runs various tests to evaluate the resilience of the WebSocket-based
progress reporting system under adverse conditions like network failures,
server restarts, and high load.
"""

import os
import sys
import time
import asyncio
import threading
import argparse
import logging
import random
import uuid
import json
import signal
import subprocess
from typing import Dict, Any, List, Optional, Set, Tuple
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("resilience_test.log")
    ]
)
logger = logging.getLogger("resilience_test")

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

# Import components to test
try:
    from rfm.core.logging_config import configure_logging, LogLevel, LogCategory
    from rfm.core.websocket_server_enhanced import ProgressServer, start_websocket_server
    from ui.rfm_ui.websocket_client_enhanced import WebSocketClient, ReconnectionConfig
except ImportError:
    logger.error("Failed to import required modules. Make sure you're running this script from the project root.")
    sys.exit(1)


class ResilienceTest:
    """Base class for resilience tests."""
    
    def __init__(self, 
                name: str,
                description: str,
                duration: float = 60.0,
                server_host: str = "localhost",
                server_port: int = 8765):
        """
        Initialize the resilience test.
        
        Args:
            name: Test name
            description: Test description
            duration: Test duration in seconds
            server_host: WebSocket server host
            server_port: WebSocket server port
        """
        self.name = name
        self.description = description
        self.duration = duration
        self.server_host = server_host
        self.server_port = server_port
        
        # Test state
        self.start_time = None
        self.end_time = None
        self.success = False
        self.error = None
        self.metrics = {}
        
        # Server process
        self.server_process = None
        
        # Clients
        self.clients: List[WebSocketClient] = []
        
        # Event loop
        self.event_loop = None
        
        # Results
        self.results = {
            "name": name,
            "description": description,
            "duration": duration,
            "success": False,
            "error": None,
            "metrics": {},
            "events": []
        }
        
    def setup(self) -> None:
        """Set up the test environment."""
        logger.info(f"Setting up test: {self.name}")
        
        # Configure logging
        configure_logging(
            app_name=f"resilience_test_{self.name}",
            log_dir="logs",
            console_level=LogLevel.INFO,
            file_level=LogLevel.DEBUG,
            json_format=True
        )
        
        # Create event loop
        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)
        
        # Record event
        self._record_event("setup", "Test setup completed")
        
    def teardown(self) -> None:
        """Clean up the test environment."""
        logger.info(f"Tearing down test: {self.name}")
        
        # Stop clients
        for client in self.clients:
            client.stop()
            
        # Stop server
        self._stop_server()
        
        # Close event loop
        if self.event_loop:
            self.event_loop.close()
            
        # Record event
        self._record_event("teardown", "Test teardown completed")
        
    def _start_server(self) -> None:
        """Start the WebSocket server."""
        # Check if server is already running
        if self.server_process and self.server_process.poll() is None:
            logger.info("Server already running")
            return
            
        # Start server in a separate process
        logger.info(f"Starting WebSocket server on {self.server_host}:{self.server_port}")
        
        # Create command
        cmd = [
            sys.executable,
            os.path.join(parent_dir, "run_websocket_server.py"),
            "--host", self.server_host,
            "--port", str(self.server_port),
            "--log-level", "debug"
        ]
        
        # Start process
        self.server_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to start
        time.sleep(2)
        
        # Check if server started
        if self.server_process.poll() is not None:
            # Server failed to start
            stdout, stderr = self.server_process.communicate()
            error_message = f"Server failed to start: {stderr}"
            logger.error(error_message)
            self.error = error_message
            raise RuntimeError(error_message)
            
        # Record event
        self._record_event("server_start", f"Server started on {self.server_host}:{self.server_port}")
        
    def _stop_server(self) -> None:
        """Stop the WebSocket server."""
        if not self.server_process:
            return
            
        # Check if server is running
        if self.server_process.poll() is None:
            # Send SIGTERM to server
            logger.info("Stopping WebSocket server")
            self.server_process.terminate()
            
            # Wait for server to stop
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill
                logger.warning("Server did not stop gracefully, killing process")
                self.server_process.kill()
                
            # Record event
            self._record_event("server_stop", "Server stopped")
            
        # Clean up
        self.server_process = None
        
    def _restart_server(self) -> None:
        """Restart the WebSocket server."""
        logger.info("Restarting WebSocket server")
        
        # Record event
        self._record_event("server_restart", "Restarting server")
        
        # Stop server
        self._stop_server()
        
        # Start server
        time.sleep(1)  # Brief pause
        self._start_server()
        
    def _create_client(self, 
                    client_id: Optional[str] = None, 
                    reconnection_config: Optional[ReconnectionConfig] = None,
                    authentication: Optional[Dict[str, str]] = None) -> WebSocketClient:
        """
        Create a new WebSocket client.
        
        Args:
            client_id: Optional client ID
            reconnection_config: Optional reconnection configuration
            authentication: Optional authentication parameters
            
        Returns:
            WebSocketClient instance
        """
        # Create client ID if not provided
        if client_id is None:
            client_id = f"test_client_{len(self.clients) + 1}"
            
        # Create client
        client = WebSocketClient(
            url=f"ws://{self.server_host}:{self.server_port}",
            reconnection_config=reconnection_config or ReconnectionConfig(),
            authentication={"client_id": client_id} if authentication is None else authentication,
            debug_mode=True
        )
        
        # Record event
        self._record_event("client_created", f"Client created: {client_id}")
        
        # Add to clients list
        self.clients.append(client)
        
        return client
        
    async def _run_operations(self, 
                          client: WebSocketClient, 
                          count: int = 5,
                          duration_range: Tuple[float, float] = (5.0, 15.0),
                          interval_range: Tuple[float, float] = (0.5, 2.0)) -> None:
        """
        Run operations on a client.
        
        Args:
            client: WebSocket client
            count: Number of operations to run
            duration_range: Range of operation durations in seconds
            interval_range: Range of intervals between operations in seconds
        """
        for i in range(count):
            # Generate operation ID
            operation_id = str(uuid.uuid4())
            operation_name = f"Test Operation {i+1}"
            
            # Generate random duration
            duration = random.uniform(*duration_range)
            
            # Start operation
            logger.info(f"Starting operation: {operation_name} (duration: {duration:.1f}s)")
            
            # Send operation started message
            await client.send_message({
                "type": "operation_started",
                "operation": {
                    "operation_id": operation_id,
                    "operation_type": "test",
                    "name": operation_name,
                    "details": {
                        "test_id": self.name,
                        "operation_number": i + 1,
                        "expected_duration": duration
                    }
                },
                "timestamp": time.time()
            })
            
            # Record event
            self._record_event("operation_start", f"Operation started: {operation_name}")
            
            # Calculate number of progress updates
            update_count = max(int(duration / 0.5), 5)  # At least 5 updates
            
            # Report progress updates
            for j in range(update_count):
                # Check if client is still connected
                if not client.is_connected():
                    # Wait for reconnection
                    logger.info(f"Waiting for client reconnection: {operation_name}")
                    await asyncio.sleep(1.0)
                    continue
                    
                # Calculate progress
                progress = (j + 1) / update_count * 100
                
                # Send progress update
                await client.send_message({
                    "type": "progress_update",
                    "data": {
                        "operation_id": operation_id,
                        "operation_type": "test",
                        "progress": progress,
                        "status": "running",
                        "current_step": f"Step {j+1}/{update_count}",
                        "timestamp": time.time()
                    }
                })
                
                # Wait before next update
                await asyncio.sleep(duration / update_count)
                
            # Complete operation
            logger.info(f"Completing operation: {operation_name}")
            
            # Send operation completed message
            await client.send_message({
                "type": "operation_completed",
                "operation_id": operation_id,
                "details": {
                    "duration": duration,
                    "test_id": self.name
                },
                "timestamp": time.time()
            })
            
            # Record event
            self._record_event("operation_complete", f"Operation completed: {operation_name}")
            
            # Wait before next operation
            interval = random.uniform(*interval_range)
            await asyncio.sleep(interval)
    
    def _record_event(self, event_type: str, description: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Record a test event.
        
        Args:
            event_type: Event type
            description: Event description
            details: Optional event details
        """
        # Create event
        event = {
            "type": event_type,
            "description": description,
            "timestamp": time.time(),
            "time": datetime.now().strftime("%H:%M:%S"),
            "details": details or {}
        }
        
        # Add to results
        self.results["events"].append(event)
        
    def _record_metric(self, name: str, value: Any) -> None:
        """
        Record a test metric.
        
        Args:
            name: Metric name
            value: Metric value
        """
        # Add to metrics
        self.metrics[name] = value
        self.results["metrics"][name] = value
        
    def _update_results(self, success: bool, error: Optional[str] = None) -> None:
        """
        Update test results.
        
        Args:
            success: Test success flag
            error: Optional error message
        """
        # Update results
        self.success = success
        self.error = error
        
        self.results["success"] = success
        self.results["error"] = error
        self.results["duration"] = (self.end_time - self.start_time) if self.end_time and self.start_time else self.duration
        
    def run(self) -> Dict[str, Any]:
        """
        Run the test.
        
        Returns:
            Test results
        """
        logger.info(f"Running test: {self.name}")
        logger.info(f"Description: {self.description}")
        
        # Set up test
        self.setup()
        
        try:
            # Start timing
            self.start_time = time.time()
            
            # Run test implementation
            self.event_loop.run_until_complete(self.run_test())
            
            # End timing
            self.end_time = time.time()
            
            # Set success if not already set
            if "success" not in self.results:
                self._update_results(True)
                
        except Exception as e:
            # Test failed
            logger.exception(f"Test failed: {e}")
            
            # Update results
            self._update_results(False, str(e))
            
        finally:
            # Clean up
            self.teardown()
            
        # Log results
        if self.success:
            logger.info(f"Test {self.name} passed!")
        else:
            logger.error(f"Test {self.name} failed: {self.error}")
            
        # Return results
        return self.results
    
    async def run_test(self) -> None:
        """Run the test implementation."""
        raise NotImplementedError("Subclasses must implement this method")


class ConnectionResilienceTest(ResilienceTest):
    """Test client reconnection capabilities."""
    
    def __init__(self, server_host: str = "localhost", server_port: int = 8765):
        """
        Initialize the connection resilience test.
        
        Args:
            server_host: WebSocket server host
            server_port: WebSocket server port
        """
        super().__init__(
            name="connection_resilience",
            description="Tests client reconnection capabilities during server restarts",
            duration=120.0,
            server_host=server_host,
            server_port=server_port
        )
        
    async def run_test(self) -> None:
        """Run the test implementation."""
        # Start server
        self._start_server()
        
        # Set up reconnection configuration
        reconnection_config = ReconnectionConfig(
            initial_delay=1.0,
            max_delay=10.0,
            multiplier=1.5,
            jitter=0.2,
            max_attempts=0  # Unlimited reconnection attempts
        )
        
        # Create client
        client = self._create_client(
            client_id="resilience_test_client",
            reconnection_config=reconnection_config
        )
        
        # Start client
        client.start()
        
        # Wait for client to connect
        for _ in range(10):
            if client.is_connected():
                break
            await asyncio.sleep(0.5)
            
        if not client.is_connected():
            raise RuntimeError("Client failed to connect to server")
            
        # Record event
        self._record_event("client_connected", "Client connected to server")
        
        # Start operations in background
        operations_task = asyncio.create_task(
            self._run_operations(
                client,
                count=10,
                duration_range=(8.0, 15.0),
                interval_range=(1.0, 3.0)
            )
        )
        
        # Wait for a few operations to start
        await asyncio.sleep(5)
        
        # Restart server multiple times
        for i in range(3):
            # Record event
            self._record_event("test_step", f"Server restart {i+1}/3")
            
            # Restart server
            self._restart_server()
            
            # Wait for client to reconnect
            reconnect_start_time = time.time()
            reconnected = False
            
            for _ in range(20):  # Wait up to 10 seconds
                if client.is_connected():
                    reconnected = True
                    reconnect_time = time.time() - reconnect_start_time
                    
                    # Record metric
                    self._record_metric(f"reconnect_time_{i+1}", reconnect_time)
                    
                    # Record event
                    self._record_event(
                        "client_reconnected", 
                        f"Client reconnected after {reconnect_time:.2f} seconds",
                        {"reconnect_attempt": i + 1}
                    )
                    
                    break
                    
                await asyncio.sleep(0.5)
                
            if not reconnected:
                self._record_event(
                    "reconnect_failed",
                    f"Client failed to reconnect after restart {i+1}"
                )
                self._update_results(False, f"Client failed to reconnect after restart {i+1}")
                return
                
            # Wait between restarts
            await asyncio.sleep(10)
            
        # Wait for operations to complete
        try:
            await asyncio.wait_for(operations_task, timeout=60)
        except asyncio.TimeoutError:
            logger.warning("Operations timed out, but test can still succeed")
            
        # Check final client state
        if client.is_connected():
            self._record_event("test_complete", "Client maintained connection through all server restarts")
            self._update_results(True)
        else:
            self._record_event("test_failed", "Client is not connected at end of test")
            self._update_results(False, "Client is not connected at end of test")


class OperationResilienceTest(ResilienceTest):
    """Test operation state preservation during reconnection."""
    
    def __init__(self, server_host: str = "localhost", server_port: int = 8765):
        """
        Initialize the operation resilience test.
        
        Args:
            server_host: WebSocket server host
            server_port: WebSocket server port
        """
        super().__init__(
            name="operation_resilience",
            description="Tests operation state preservation during reconnection",
            duration=180.0,
            server_host=server_host,
            server_port=server_port
        )
        
        # Operation tracking
        self.operations: Dict[str, Dict[str, Any]] = {}
        self.completed_operations: Set[str] = set()
        self.operation_statuses: Dict[str, Dict[str, Any]] = {}
        
    async def run_test(self) -> None:
        """Run the test implementation."""
        # Start server
        self._start_server()
        
        # Set up reconnection configuration
        reconnection_config = ReconnectionConfig(
            initial_delay=1.0,
            max_delay=10.0,
            multiplier=1.5,
            jitter=0.2,
            max_attempts=0  # Unlimited reconnection attempts
        )
        
        # Create client
        client = self._create_client(
            client_id="resilience_test_client",
            reconnection_config=reconnection_config
        )
        
        # Register operation callbacks
        client.add_callback("operation_started", self._on_operation_started)
        client.add_callback("progress_update", self._on_progress_update)
        client.add_callback("operation_completed", self._on_operation_completed)
        client.add_callback("operation_failed", self._on_operation_failed)
        client.add_callback("operation_canceled", self._on_operation_canceled)
        
        # Start client
        client.start()
        
        # Wait for client to connect
        for _ in range(10):
            if client.is_connected():
                break
            await asyncio.sleep(0.5)
            
        if not client.is_connected():
            raise RuntimeError("Client failed to connect to server")
            
        # Record event
        self._record_event("client_connected", "Client connected to server")
        
        # Start long-running operations
        long_operations = 3
        for i in range(long_operations):
            # Generate operation
            operation_id = str(uuid.uuid4())
            operation_name = f"Long Operation {i+1}"
            
            # Store operation
            self.operations[operation_id] = {
                "operation_id": operation_id,
                "name": operation_name,
                "duration": 60.0,  # 60 second operation
                "started": False,
                "completed": False,
                "updates": 0
            }
            
            # Start operation
            await client.send_message({
                "type": "operation_started",
                "operation": {
                    "operation_id": operation_id,
                    "operation_type": "test",
                    "name": operation_name,
                    "details": {
                        "test_id": self.name,
                        "operation_number": i + 1,
                        "expected_duration": 60.0
                    }
                },
                "timestamp": time.time()
            })
            
            # Brief delay between operations
            await asyncio.sleep(1.0)
            
        # Start progress update task
        update_task = asyncio.create_task(self._send_progress_updates(client))
        
        # Wait for operations to start
        await asyncio.sleep(5)
        
        # Restart server multiple times
        for i in range(3):
            # Record event
            self._record_event("test_step", f"Server restart {i+1}/3")
            
            # Restart server
            self._restart_server()
            
            # Wait for client to reconnect
            reconnect_start_time = time.time()
            reconnected = False
            
            for _ in range(20):  # Wait up to 10 seconds
                if client.is_connected():
                    reconnected = True
                    reconnect_time = time.time() - reconnect_start_time
                    
                    # Record metric
                    self._record_metric(f"reconnect_time_{i+1}", reconnect_time)
                    
                    # Record event
                    self._record_event(
                        "client_reconnected", 
                        f"Client reconnected after {reconnect_time:.2f} seconds",
                        {"reconnect_attempt": i + 1}
                    )
                    
                    break
                    
                await asyncio.sleep(0.5)
                
            if not reconnected:
                self._record_event(
                    "reconnect_failed",
                    f"Client failed to reconnect after restart {i+1}"
                )
                self._update_results(False, f"Client failed to reconnect after restart {i+1}")
                return
                
            # Check for operation resurrection
            resurrection_start_time = time.time()
            await asyncio.sleep(5)  # Wait for resurrection
            
            # Check operation status
            active_operation_count = 0
            for op_id, op_data in self.operations.items():
                if not op_data["completed"]:
                    # Should still be active
                    if op_id in client.operations:
                        client_op = client.operations[op_id]
                        if client_op.status in ("pending", "running", "paused"):
                            active_operation_count += 1
                            
                            # Record event
                            self._record_event(
                                "operation_resurrected",
                                f"Operation {op_data['name']} resurrected after restart {i+1}",
                                {
                                    "operation_id": op_id,
                                    "status": client_op.status,
                                    "progress": client_op.progress
                                }
                            )
                            
            self._record_metric(f"resurrected_operations_{i+1}", active_operation_count)
            
            # Record event
            self._record_event(
                "resurrection_check",
                f"Found {active_operation_count} active operations after restart {i+1}",
                {"expected": long_operations - len(self.completed_operations)}
            )
            
            # Wait between restarts
            await asyncio.sleep(20)
            
        # Wait for operations to complete
        try:
            await asyncio.wait_for(update_task, timeout=120)
        except asyncio.TimeoutError:
            logger.warning("Operations timed out")
            update_task.cancel()
            
        # Check completed operations
        completion_count = len(self.completed_operations)
        expected_completions = len(self.operations)
        
        # Record metrics
        self._record_metric("completed_operations", completion_count)
        self._record_metric("expected_completions", expected_completions)
        self._record_metric("completion_percentage", completion_count / expected_completions * 100)
        
        # Record event
        self._record_event(
            "test_complete",
            f"Completed {completion_count}/{expected_completions} operations",
            {"completion_percentage": completion_count / expected_completions * 100}
        )
        
        # Success if at least 75% of operations completed
        if completion_count / expected_completions >= 0.75:
            self._update_results(True)
        else:
            self._update_results(
                False,
                f"Only {completion_count}/{expected_completions} operations completed successfully"
            )
            
    async def _send_progress_updates(self, client: WebSocketClient) -> None:
        """
        Send progress updates for operations.
        
        Args:
            client: WebSocket client
        """
        # Continue until all operations complete
        while len(self.completed_operations) < len(self.operations):
            # Check for active operations
            for op_id, op_data in self.operations.items():
                # Skip completed operations
                if op_id in self.completed_operations:
                    continue
                    
                # Skip if client not connected
                if not client.is_connected():
                    break
                    
                # Check if operation exists in client
                if op_id in client.operations:
                    # Get client operation
                    client_op = client.operations[op_id]
                    
                    # Skip if not active
                    if client_op.status not in ("pending", "running", "paused"):
                        continue
                        
                    # Calculate progress based on time
                    elapsed = time.time() - client_op.start_time if client_op.start_time else 0
                    expected_duration = op_data["duration"]
                    progress = min(elapsed / expected_duration * 100, 99.0)  # Cap at 99%
                    
                    # Send progress update
                    await client.send_message({
                        "type": "progress_update",
                        "data": {
                            "operation_id": op_id,
                            "operation_type": "test",
                            "progress": progress,
                            "status": "running",
                            "current_step": f"Processing {progress:.0f}%",
                            "timestamp": time.time()
                        }
                    })
                    
                    # Track update
                    op_data["updates"] += 1
                    
                    # Check if operation should complete
                    if elapsed >= expected_duration:
                        # Complete operation
                        await client.send_message({
                            "type": "operation_completed",
                            "operation_id": op_id,
                            "details": {
                                "duration": elapsed,
                                "test_id": self.name,
                                "updates": op_data["updates"]
                            },
                            "timestamp": time.time()
                        })
                        
                        # Mark as completed locally
                        op_data["completed"] = True
                        self.completed_operations.add(op_id)
                        
                        # Record event
                        self._record_event(
                            "operation_complete",
                            f"Operation {op_data['name']} completed",
                            {
                                "operation_id": op_id,
                                "duration": elapsed,
                                "updates": op_data["updates"]
                            }
                        )
                        
            # Wait before next update round
            await asyncio.sleep(1.0)
            
    def _on_operation_started(self, data: Dict[str, Any]) -> None:
        """
        Handle operation started event.
        
        Args:
            data: Event data
        """
        operation = data.get("operation", {})
        operation_id = operation.get("operation_id")
        
        if not operation_id:
            return
            
        # Check if this is one of our operations
        if operation_id in self.operations:
            # Mark as started
            self.operations[operation_id]["started"] = True
            
            # Store status
            self.operation_statuses[operation_id] = {
                "status": "started",
                "timestamp": time.time()
            }
            
    def _on_progress_update(self, data: Dict[str, Any]) -> None:
        """
        Handle progress update event.
        
        Args:
            data: Event data
        """
        update_data = data.get("data", {})
        operation_id = update_data.get("operation_id")
        
        if not operation_id:
            return
            
        # Check if this is one of our operations
        if operation_id in self.operations:
            # Store status
            self.operation_statuses[operation_id] = {
                "status": "updated",
                "timestamp": time.time(),
                "progress": update_data.get("progress", 0)
            }
            
    def _on_operation_completed(self, data: Dict[str, Any]) -> None:
        """
        Handle operation completed event.
        
        Args:
            data: Event data
        """
        operation_id = data.get("operation_id")
        
        if not operation_id:
            return
            
        # Check if this is one of our operations
        if operation_id in self.operations:
            # Mark as completed
            self.operations[operation_id]["completed"] = True
            self.completed_operations.add(operation_id)
            
            # Store status
            self.operation_statuses[operation_id] = {
                "status": "completed",
                "timestamp": time.time()
            }
            
    def _on_operation_failed(self, data: Dict[str, Any]) -> None:
        """
        Handle operation failed event.
        
        Args:
            data: Event data
        """
        operation_id = data.get("operation_id")
        
        if not operation_id:
            return
            
        # Check if this is one of our operations
        if operation_id in self.operations:
            # Mark as completed (failed)
            self.operations[operation_id]["completed"] = True
            self.completed_operations.add(operation_id)
            
            # Store status
            self.operation_statuses[operation_id] = {
                "status": "failed",
                "timestamp": time.time(),
                "error": data.get("details", {}).get("error_message")
            }
            
    def _on_operation_canceled(self, data: Dict[str, Any]) -> None:
        """
        Handle operation canceled event.
        
        Args:
            data: Event data
        """
        operation_id = data.get("operation_id")
        
        if not operation_id:
            return
            
        # Check if this is one of our operations
        if operation_id in self.operations:
            # Mark as completed (canceled)
            self.operations[operation_id]["completed"] = True
            self.completed_operations.add(operation_id)
            
            # Store status
            self.operation_statuses[operation_id] = {
                "status": "canceled",
                "timestamp": time.time()
            }


class LoadResilienceTest(ResilienceTest):
    """Test system behavior under high load."""
    
    def __init__(self, server_host: str = "localhost", server_port: int = 8765):
        """
        Initialize the load resilience test.
        
        Args:
            server_host: WebSocket server host
            server_port: WebSocket server port
        """
        super().__init__(
            name="load_resilience",
            description="Tests system behavior under high load with many clients and operations",
            duration=180.0,
            server_host=server_host,
            server_port=server_port
        )
        
        # Load testing parameters
        self.client_count = 5
        self.operations_per_client = 10
        self.updates_per_operation = 20
        
        # Performance tracking
        self.operation_timings: Dict[str, Dict[str, float]] = {}
        self.client_timings: Dict[str, Dict[str, float]] = {}
        
    async def run_test(self) -> None:
        """Run the test implementation."""
        # Start server
        self._start_server()
        
        # Track client operations
        client_operations: Dict[str, List[str]] = {}
        completed_operations: Dict[str, Set[str]] = {}
        
        # Create clients
        for i in range(self.client_count):
            client_id = f"load_test_client_{i+1}"
            
            # Create client
            client = self._create_client(client_id=client_id)
            
            # Track client operations
            client_operations[client_id] = []
            completed_operations[client_id] = set()
            
            # Store client start time
            self.client_timings[client_id] = {
                "start_time": time.time()
            }
            
        # Start clients
        for client in self.clients:
            client.start()
            
        # Wait for clients to connect
        await asyncio.sleep(2)
        
        # Record event
        connected_clients = sum(1 for client in self.clients if client.is_connected())
        self._record_event(
            "clients_connected",
            f"{connected_clients}/{self.client_count} clients connected"
        )
        
        if connected_clients < self.client_count:
            self._update_results(False, f"Only {connected_clients}/{self.client_count} clients connected")
            return
            
        # Start operations for each client
        operation_tasks = []
        
        for i, client in enumerate(self.clients):
            client_id = f"load_test_client_{i+1}"
            
            # Create operations task
            task = asyncio.create_task(
                self._run_client_operations(
                    client,
                    client_id,
                    self.operations_per_client,
                    client_operations[client_id],
                    completed_operations[client_id]
                )
            )
            
            operation_tasks.append(task)
            
        # Wait for all operations to complete
        try:
            await asyncio.gather(*operation_tasks)
        except Exception as e:
            logger.exception(f"Error running operations: {e}")
            self._update_results(False, f"Error running operations: {e}")
            return
            
        # Record completion metrics
        total_operations = self.client_count * self.operations_per_client
        completed_count = sum(len(completed) for completed in completed_operations.values())
        completion_percentage = completed_count / total_operations * 100
        
        self._record_metric("total_operations", total_operations)
        self._record_metric("completed_operations", completed_count)
        self._record_metric("completion_percentage", completion_percentage)
        
        # Calculate timing metrics
        operation_durations = [
            timing["end_time"] - timing["start_time"]
            for timing in self.operation_timings.values()
            if "end_time" in timing
        ]
        
        if operation_durations:
            avg_duration = sum(operation_durations) / len(operation_durations)
            min_duration = min(operation_durations)
            max_duration = max(operation_durations)
            
            self._record_metric("avg_operation_duration", avg_duration)
            self._record_metric("min_operation_duration", min_duration)
            self._record_metric("max_operation_duration", max_duration)
            
        # Record event
        self._record_event(
            "test_complete",
            f"Completed {completed_count}/{total_operations} operations ({completion_percentage:.1f}%)"
        )
        
        # Success if at least 90% of operations completed
        if completion_percentage >= 90:
            self._update_results(True)
        else:
            self._update_results(
                False,
                f"Only {completed_count}/{total_operations} operations completed successfully"
            )
            
    async def _run_client_operations(self, 
                                 client: WebSocketClient,
                                 client_id: str,
                                 count: int,
                                 operations: List[str],
                                 completed_operations: Set[str]) -> None:
        """
        Run operations for a client.
        
        Args:
            client: WebSocket client
            client_id: Client ID
            count: Number of operations to run
            operations: List to store operation IDs
            completed_operations: Set to store completed operation IDs
        """
        for i in range(count):
            # Generate operation ID
            operation_id = str(uuid.uuid4())
            operation_name = f"{client_id} Operation {i+1}"
            
            # Store operation
            operations.append(operation_id)
            
            # Start operation
            await client.send_message({
                "type": "operation_started",
                "operation": {
                    "operation_id": operation_id,
                    "operation_type": "test",
                    "name": operation_name,
                    "details": {
                        "test_id": self.name,
                        "client_id": client_id,
                        "operation_number": i + 1
                    }
                },
                "timestamp": time.time()
            })
            
            # Store operation start time
            self.operation_timings[operation_id] = {
                "start_time": time.time(),
                "client_id": client_id
            }
            
            # Record event (but limit to avoid too many events)
            if i == 0 or i == count - 1:
                self._record_event(
                    "operation_start",
                    f"Started operation {operation_name}"
                )
                
            # Run operation with progress updates
            try:
                await self._run_operation_with_updates(
                    client,
                    operation_id,
                    operation_name,
                    self.updates_per_operation
                )
                
                # Mark as completed
                completed_operations.add(operation_id)
                
                # Store operation end time
                self.operation_timings[operation_id]["end_time"] = time.time()
                
            except Exception as e:
                logger.error(f"Error running operation {operation_name}: {e}")
                
                # Store operation error
                self.operation_timings[operation_id]["error"] = str(e)
                
            # Brief delay between operations
            await asyncio.sleep(random.uniform(0.2, 1.0))
            
        # Store client end time
        self.client_timings[client_id]["end_time"] = time.time()
        
    async def _run_operation_with_updates(self, 
                                      client: WebSocketClient,
                                      operation_id: str,
                                      operation_name: str,
                                      update_count: int) -> None:
        """
        Run an operation with progress updates.
        
        Args:
            client: WebSocket client
            operation_id: Operation ID
            operation_name: Operation name
            update_count: Number of progress updates
        """
        for i in range(update_count):
            # Calculate progress
            progress = (i + 1) / update_count * 100
            
            # Send progress update
            await client.send_message({
                "type": "progress_update",
                "data": {
                    "operation_id": operation_id,
                    "operation_type": "test",
                    "progress": progress,
                    "status": "running",
                    "current_step": f"Step {i+1}/{update_count}",
                    "timestamp": time.time()
                }
            })
            
            # Brief delay between updates
            await asyncio.sleep(random.uniform(0.05, 0.2))
            
        # Complete operation
        await client.send_message({
            "type": "operation_completed",
            "operation_id": operation_id,
            "details": {
                "test_id": self.name,
                "updates": update_count
            },
            "timestamp": time.time()
        })


def run_resilience_tests(args: argparse.Namespace) -> None:
    """
    Run resilience tests.
    
    Args:
        args: Command-line arguments
    """
    logger.info("Starting resilience tests")
    
    # Create results directory
    os.makedirs("test_results", exist_ok=True)
    
    # Create results file
    results_file = os.path.join(
        "test_results", 
        f"resilience_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    
    # Track all results
    all_results = []
    
    # Run tests
    test_classes = [
        ConnectionResilienceTest,
        OperationResilienceTest,
        LoadResilienceTest
    ]
    
    for test_class in test_classes:
        if args.tests and test_class.__name__.lower() not in args.tests:
            logger.info(f"Skipping test: {test_class.__name__}")
            continue
            
        # Create test instance
        test = test_class(server_host=args.host, server_port=args.port)
        
        # Run test
        results = test.run()
        
        # Store results
        all_results.append(results)
        
    # Save all results
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": time.time(),
            "date": datetime.now().isoformat(),
            "tests": all_results
        }, f, indent=2)
        
    # Print summary
    logger.info("Resilience tests completed")
    logger.info(f"Results saved to: {results_file}")
    
    # Print test results
    for result in all_results:
        status = "PASSED" if result["success"] else "FAILED"
        logger.info(f"{result['name']}: {status}")
        
        if not result["success"] and result["error"]:
            logger.info(f"  Error: {result['error']}")
            
    # Overall status
    if all(result["success"] for result in all_results):
        logger.info("ALL TESTS PASSED!")
    else:
        logger.info("SOME TESTS FAILED")
        

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run resilience tests for WebSocket progress reporting")
    
    parser.add_argument("--host", default="localhost", help="WebSocket server host")
    parser.add_argument("--port", type=int, default=8765, help="WebSocket server port")
    parser.add_argument("--tests", nargs="*", help="Specific tests to run (connection, operation, load)")
    
    args = parser.parse_args()
    
    # Normalize test names
    if args.tests:
        args.tests = [test.lower() for test in args.tests]
        
        # Convert to class name if needed
        test_map = {
            "connection": "connectionresiliencetest",
            "operation": "operationresiliencetest",
            "load": "loadresiliencetest"
        }
        
        args.tests = [test_map.get(test, test) for test in args.tests]
    
    # Run tests
    run_resilience_tests(args)