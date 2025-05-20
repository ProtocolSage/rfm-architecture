#!/usr/bin/env python3
"""
Chaos Testing for WebSocket Server Resilience

This script conducts chaos tests on the WebSocket server to verify its resilience
under adverse conditions including network disruptions, resource constraints,
and malformed inputs.
"""

import argparse
import asyncio
import json
import logging
import os
import random
import signal
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Union, Any, Callable

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
sys.path.insert(0, project_dir)

try:
    from ui.rfm_ui.websocket_client_enhanced import (
        WebSocketClient, ConnectionState, MessageType, OperationStatus, ReconnectionConfig
    )
    from rfm.core.logging_config import (
        configure_logging, LogLevel, LogCategory
    )
except ImportError:
    print("Error: Failed to import required modules. Make sure you're running this script from the project root.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger("chaos-test")


class ChaosType(str, Enum):
    """Types of chaos to inject."""
    
    NETWORK_DISCONNECT = "network_disconnect"  # Simulate network disconnection
    SERVER_CRASH = "server_crash"              # Simulate server crash
    HIGH_LOAD = "high_load"                    # Simulate high load
    DISK_FULL = "disk_full"                    # Simulate disk full condition
    MEMORY_PRESSURE = "memory_pressure"        # Simulate memory pressure
    MALFORMED_DATA = "malformed_data"          # Send malformed data
    SLOW_RESPONSE = "slow_response"            # Simulate slow server responses
    

@dataclass
class ChaosTestConfig:
    """Configuration for chaos tests."""
    
    name: str
    description: str
    chaos_type: ChaosType
    duration: float                  # Test duration in seconds
    frequency: float = 10.0          # Chaos frequency in seconds
    intensity: float = 1.0           # Chaos intensity (0.0 to 1.0)
    server_host: str = "localhost"   # Server host
    server_port: int = 8765          # Server port
    server_script: str = "run_websocket_server.py"  # Server script to run
    client_count: int = 1            # Number of clients to create
    operations_per_client: int = 3   # Operations per client
    report_dir: Optional[str] = None  # Directory for test reports
    custom_params: Dict[str, Any] = field(default_factory=dict)  # Custom parameters
    jwt_token: Optional[str] = None  # JWT token for authentication


class ChaosTest:
    """Base class for chaos tests."""
    
    def __init__(self, config: ChaosTestConfig):
        """
        Initialize the chaos test.
        
        Args:
            config: Test configuration
        """
        self.config = config
        self.server_process: Optional[subprocess.Popen] = None
        self.clients: List[WebSocketClient] = []
        self.operations: Dict[str, Dict[str, Any]] = {}
        self.stop_event = asyncio.Event()
        
        # Set up report directory
        self.report_dir = Path(config.report_dir or os.path.join(project_dir, "reports", "chaos"))
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        # Test metrics
        self.metrics = {
            "start_time": 0.0,
            "end_time": 0.0,
            "chaos_events": [],
            "connection_events": [],
            "operation_events": [],
            "errors": [],
            "client_metrics": {}
        }
        
        logger.info(f"Initialized chaos test: {config.name} - {config.description}")
        logger.info(f"Configuration: {config}")
    
    def log_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """
        Log a test event with timestamp.
        
        Args:
            event_type: Type of event
            details: Event details
        """
        event = {
            "timestamp": time.time(),
            "type": event_type,
            **details
        }
        
        if event_type.startswith("chaos_"):
            self.metrics["chaos_events"].append(event)
        elif event_type.startswith("connection_"):
            self.metrics["connection_events"].append(event)
        elif event_type.startswith("operation_"):
            self.metrics["operation_events"].append(event)
        elif event_type.startswith("error_"):
            self.metrics["errors"].append(event)
            
        # Log all events
        logger.info(f"Event: {event_type} - {json.dumps(details)}")
    
    async def start_server(self) -> bool:
        """
        Start the WebSocket server.
        
        Returns:
            True if server started successfully, False otherwise
        """
        logger.info(f"Starting WebSocket server: {self.config.server_script}")
        
        try:
            # Build command
            cmd = [
                sys.executable,
                os.path.join(project_dir, self.config.server_script),
                f"--host={self.config.server_host}",
                f"--port={self.config.server_port}",
                "--log-level=debug"
            ]
            
            # Start server process
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Wait for server to start
            await asyncio.sleep(2)
            
            # Verify server is running
            if self.server_process.poll() is not None:
                stdout, stderr = self.server_process.communicate()
                logger.error(f"Failed to start server: {stderr}")
                return False
            
            logger.info(f"WebSocket server started on {self.config.server_host}:{self.config.server_port}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            return False
    
    def stop_server(self) -> None:
        """Stop the WebSocket server."""
        if self.server_process:
            logger.info("Stopping WebSocket server...")
            try:
                # Try graceful shutdown first
                self.server_process.terminate()
                
                # Wait for process to terminate
                try:
                    self.server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if timeout
                    logger.warning("Server did not terminate gracefully, killing...")
                    self.server_process.kill()
                    self.server_process.wait(timeout=2)
            except Exception as e:
                logger.error(f"Error stopping server: {e}")
            
            self.server_process = None
    
    def create_client(self, client_id: str) -> WebSocketClient:
        """
        Create a WebSocket client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            WebSocketClient instance
        """
        # Configure reconnection with exponential backoff
        reconnection_config = ReconnectionConfig(
            initial_delay=0.5,
            max_delay=10.0,
            multiplier=1.5,
            jitter=0.2,
            max_attempts=0  # Infinite retries
        )
        
        # Create authentication if token provided
        authentication = None
        if self.config.jwt_token:
            authentication = {
                "client_id": client_id,
                "token": self.config.jwt_token
            }
        
        # Create client
        client = WebSocketClient(
            url=f"ws://{self.config.server_host}:{self.config.server_port}",
            reconnection_config=reconnection_config,
            authentication=authentication,
            log_level=LogLevel.INFO,
            debug_mode=True
        )
        
        # Register callbacks
        client.add_callback(MessageType.CONNECTION_STATUS, 
                          lambda data: self.on_connection_status(client_id, data))
        client.add_callback(MessageType.OPERATION_STARTED, 
                          lambda data: self.on_operation_started(client_id, data))
        client.add_callback(MessageType.PROGRESS_UPDATE, 
                          lambda data: self.on_progress_update(client_id, data))
        client.add_callback(MessageType.OPERATION_COMPLETED, 
                          lambda data: self.on_operation_completed(client_id, data))
        client.add_callback(MessageType.OPERATION_FAILED, 
                          lambda data: self.on_operation_failed(client_id, data))
        client.add_callback(MessageType.ERROR, 
                          lambda data: self.on_error(client_id, data))
        
        return client
    
    def on_connection_status(self, client_id: str, data: Dict[str, Any]) -> None:
        """
        Handle connection status changes.
        
        Args:
            client_id: Client identifier
            data: Connection status data
        """
        status = data.get("status")
        details = data.get("details", {})
        
        # Log event
        self.log_event(f"connection_{status}", {
            "client_id": client_id,
            "details": details
        })
        
        # Update client metrics
        if client_id not in self.metrics["client_metrics"]:
            self.metrics["client_metrics"][client_id] = {
                "connections": 0,
                "disconnections": 0,
                "reconnections": 0
            }
            
        if status == ConnectionState.CONNECTED:
            self.metrics["client_metrics"][client_id]["connections"] += 1
        elif status == ConnectionState.DISCONNECTED:
            self.metrics["client_metrics"][client_id]["disconnections"] += 1
        elif status == ConnectionState.RECONNECTING:
            self.metrics["client_metrics"][client_id]["reconnections"] += 1
    
    def on_operation_started(self, client_id: str, data: Dict[str, Any]) -> None:
        """
        Handle operation started events.
        
        Args:
            client_id: Client identifier
            data: Operation data
        """
        operation = data.get("operation", {})
        operation_id = operation.get("operation_id")
        
        if operation_id:
            # Store operation
            self.operations[operation_id] = {
                "client_id": client_id,
                "operation_id": operation_id,
                "operation_type": operation.get("operation_type"),
                "name": operation.get("name"),
                "start_time": time.time(),
                "status": "started"
            }
            
            # Log event
            self.log_event("operation_started", {
                "client_id": client_id,
                "operation_id": operation_id,
                "operation_type": operation.get("operation_type"),
                "name": operation.get("name")
            })
    
    def on_progress_update(self, client_id: str, data: Dict[str, Any]) -> None:
        """
        Handle progress update events.
        
        Args:
            client_id: Client identifier
            data: Progress data
        """
        update_data = data.get("data", {})
        operation_id = update_data.get("operation_id")
        
        if operation_id:
            # Log significant progress updates
            progress = update_data.get("progress", 0)
            if progress % 25 == 0 or progress == 100:  # Log at 0%, 25%, 50%, 75%, 100%
                self.log_event("operation_progress", {
                    "client_id": client_id,
                    "operation_id": operation_id,
                    "progress": progress,
                    "current_step": update_data.get("current_step")
                })
                
            # Update operation status
            if operation_id in self.operations:
                self.operations[operation_id]["progress"] = progress
                self.operations[operation_id]["last_update_time"] = time.time()
    
    def on_operation_completed(self, client_id: str, data: Dict[str, Any]) -> None:
        """
        Handle operation completed events.
        
        Args:
            client_id: Client identifier
            data: Operation data
        """
        operation_id = data.get("operation_id")
        
        if operation_id and operation_id in self.operations:
            # Update operation status
            self.operations[operation_id]["status"] = "completed"
            self.operations[operation_id]["end_time"] = time.time()
            
            # Calculate duration
            start_time = self.operations[operation_id].get("start_time")
            if start_time:
                self.operations[operation_id]["duration"] = time.time() - start_time
            
            # Log event
            self.log_event("operation_completed", {
                "client_id": client_id,
                "operation_id": operation_id,
                "duration": self.operations[operation_id].get("duration")
            })
    
    def on_operation_failed(self, client_id: str, data: Dict[str, Any]) -> None:
        """
        Handle operation failed events.
        
        Args:
            client_id: Client identifier
            data: Operation data
        """
        operation_id = data.get("operation_id")
        
        if operation_id and operation_id in self.operations:
            # Update operation status
            self.operations[operation_id]["status"] = "failed"
            self.operations[operation_id]["end_time"] = time.time()
            self.operations[operation_id]["error"] = data.get("details", {}).get("error_message")
            
            # Calculate duration
            start_time = self.operations[operation_id].get("start_time")
            if start_time:
                self.operations[operation_id]["duration"] = time.time() - start_time
            
            # Log event
            self.log_event("operation_failed", {
                "client_id": client_id,
                "operation_id": operation_id,
                "error": self.operations[operation_id].get("error"),
                "duration": self.operations[operation_id].get("duration")
            })
    
    def on_error(self, client_id: str, data: Dict[str, Any]) -> None:
        """
        Handle error events.
        
        Args:
            client_id: Client identifier
            data: Error data
        """
        # Log event
        self.log_event("error_client", {
            "client_id": client_id,
            "error_code": data.get("error_code"),
            "error_message": data.get("error_message")
        })
    
    async def simulate_operation(self, 
                               client: WebSocketClient, 
                               client_id: str,
                               operation_index: int) -> None:
        """
        Simulate a long-running operation with progress updates.
        
        Args:
            client: WebSocket client
            client_id: Client identifier
            operation_index: Operation index
        """
        # Generate operation ID
        operation_id = f"{client_id}_op_{operation_index}"
        
        # Create operation details
        operation_types = ["fractal_render", "animation_export", "parameter_optimization"]
        operation_type = random.choice(operation_types)
        operation_name = f"{operation_type.replace('_', ' ').title()} {operation_id[-8:]}"
        
        # Start operation message
        operation = {
            "operation_id": operation_id,
            "operation_type": operation_type,
            "name": operation_name,
            "status": "pending",
            "progress": 0,
            "start_time": time.time(),
            "details": {
                "parameters": {
                    "resolution": random.choice([512, 1024, 2048]),
                    "iterations": random.choice([100, 500, 1000]),
                    "precision": random.choice(["single", "double"])
                }
            }
        }
        
        # Create message
        start_message = {
            "type": MessageType.OPERATION_STARTED,
            "operation": operation,
            "timestamp": time.time()
        }
        
        # Send operation started message
        await asyncio.wrap_future(asyncio.run_coroutine_threadsafe(
            client.send_message(start_message),
            client.event_loop
        ))
        
        # Determine operation parameters
        total_updates = random.randint(10, 40)
        step_size = 100.0 / total_updates
        delay_base = random.uniform(0.1, 0.3)
        
        # Create steps
        steps = ["Initializing", "Processing", "Rendering", "Finalizing"]
        current_step = steps[0]
        
        # Send progress updates
        for i in range(total_updates + 1):
            # Check if test is still running
            if self.stop_event.is_set():
                break
                
            # Calculate progress
            progress = min(100.0, i * step_size)
            
            # Update step
            if progress > 75:
                current_step = steps[3]
            elif progress > 50:
                current_step = steps[2]
            elif progress > 25:
                current_step = steps[1]
            
            # Create update data
            update_data = {
                "operation_id": operation_id,
                "progress": progress,
                "current_step": current_step,
                "timestamp": time.time(),
                "details": {
                    "memory_usage": random.randint(50, 500),
                    "current_iteration": int((progress / 100) * 1000)
                }
            }
            
            # Create message
            message = {
                "type": MessageType.PROGRESS_UPDATE,
                "data": update_data,
                "timestamp": time.time()
            }
            
            # Send progress update message
            await asyncio.wrap_future(asyncio.run_coroutine_threadsafe(
                client.send_message(message),
                client.event_loop
            ))
            
            # Random delay between updates
            delay = delay_base * random.uniform(0.8, 1.2)
            await asyncio.sleep(delay)
        
        # Complete operation (small chance of failure)
        if random.random() < 0.05:
            # Send operation failed message
            message = {
                "type": MessageType.OPERATION_FAILED,
                "operation_id": operation_id,
                "timestamp": time.time(),
                "details": {
                    "error_message": "Simulated random failure",
                    "error_code": "SIMULATION_ERROR"
                }
            }
        else:
            # Send operation completed message
            message = {
                "type": MessageType.OPERATION_COMPLETED,
                "operation_id": operation_id,
                "timestamp": time.time(),
                "details": {
                    "results": {
                        "duration": random.uniform(5.0, 20.0),
                        "output_file": f"output_{operation_id[-8:]}.png"
                    }
                }
            }
        
        # Send final message
        await asyncio.wrap_future(asyncio.run_coroutine_threadsafe(
            client.send_message(message),
            client.event_loop
        ))
    
    async def run_client_operations(self, client: WebSocketClient, client_id: str) -> None:
        """
        Run operations for a client.
        
        Args:
            client: WebSocket client
            client_id: Client identifier
        """
        # Wait for connection
        for _ in range(10):  # Wait up to 5 seconds
            if client.is_connected():
                break
            await asyncio.sleep(0.5)
            
        if not client.is_connected():
            logger.warning(f"Client {client_id} failed to connect")
            return
            
        # Run operations
        operations = []
        for i in range(self.config.operations_per_client):
            # Start operation
            operation = asyncio.create_task(
                self.simulate_operation(client, client_id, i)
            )
            operations.append(operation)
            
            # Wait a bit before starting next operation
            await asyncio.sleep(random.uniform(1.0, 3.0))
        
        # Wait for all operations to complete or test to end
        try:
            done, pending = await asyncio.wait(
                operations,
                timeout=self.config.duration,
                return_when=asyncio.ALL_COMPLETED
            )
            
            # Cancel pending operations
            for task in pending:
                task.cancel()
                
        except asyncio.CancelledError:
            # Test was cancelled
            for task in operations:
                task.cancel()
    
    async def inject_chaos(self) -> None:
        """Inject chaos based on test configuration."""
        # Wait for initial setup
        await asyncio.sleep(5)
        
        # Calculate chaos events
        test_duration = self.config.duration
        chaos_interval = self.config.frequency
        num_events = int(test_duration / chaos_interval)
        
        logger.info(f"Will inject {num_events} chaos events over {test_duration}s")
        
        # Inject chaos at regular intervals
        for i in range(num_events):
            # Check if test should stop
            if self.stop_event.is_set():
                break
                
            # Calculate time until next event
            next_event_time = (i + 1) * chaos_interval
            time_to_wait = next_event_time - (time.time() - self.metrics["start_time"])
            
            if time_to_wait > 0:
                await asyncio.sleep(time_to_wait)
                
            # Inject chaos
            await self._inject_specific_chaos()
            
            # Allow system to recover slightly
            await asyncio.sleep(1.0)
    
    async def _inject_specific_chaos(self) -> None:
        """Inject specific chaos based on test type."""
        chaos_type = self.config.chaos_type
        intensity = self.config.intensity
        
        # Log chaos event
        self.log_event(f"chaos_{chaos_type}", {
            "intensity": intensity,
            "elapsed_time": time.time() - self.metrics["start_time"]
        })
        
        if chaos_type == ChaosType.NETWORK_DISCONNECT:
            await self._inject_network_disconnect(intensity)
        elif chaos_type == ChaosType.SERVER_CRASH:
            await self._inject_server_crash(intensity)
        elif chaos_type == ChaosType.HIGH_LOAD:
            await self._inject_high_load(intensity)
        elif chaos_type == ChaosType.DISK_FULL:
            await self._inject_disk_full(intensity)
        elif chaos_type == ChaosType.MEMORY_PRESSURE:
            await self._inject_memory_pressure(intensity)
        elif chaos_type == ChaosType.MALFORMED_DATA:
            await self._inject_malformed_data(intensity)
        elif chaos_type == ChaosType.SLOW_RESPONSE:
            await self._inject_slow_response(intensity)
    
    async def _inject_network_disconnect(self, intensity: float) -> None:
        """
        Simulate network disconnection.
        
        Args:
            intensity: Chaos intensity (0.0 to 1.0)
        """
        logger.info(f"Injecting network disconnect (intensity: {intensity})")
        
        # Determine number of clients to disconnect based on intensity
        num_clients = max(1, int(len(self.clients) * intensity))
        clients_to_disconnect = random.sample(self.clients, num_clients)
        
        for client in clients_to_disconnect:
            # Force disconnect
            if client.websocket and hasattr(client.websocket, "close"):
                await asyncio.wrap_future(asyncio.run_coroutine_threadsafe(
                    client.websocket.close(code=1001, reason="Chaos test disconnect"),
                    client.event_loop
                ))
    
    async def _inject_server_crash(self, intensity: float) -> None:
        """
        Simulate server crash.
        
        Args:
            intensity: Chaos intensity (0.0 to 1.0)
        """
        if not self.server_process:
            logger.warning("Cannot inject server crash: No server process")
            return
            
        logger.info(f"Injecting server crash (intensity: {intensity})")
        
        # Stop the server
        self.stop_server()
        
        # Wait a bit
        crash_duration = 3.0 + (intensity * 7.0)  # 3-10 seconds based on intensity
        await asyncio.sleep(crash_duration)
        
        # Restart the server
        await self.start_server()
    
    async def _inject_high_load(self, intensity: float) -> None:
        """
        Simulate high CPU load.
        
        Args:
            intensity: Chaos intensity (0.0 to 1.0)
        """
        logger.info(f"Injecting high CPU load (intensity: {intensity})")
        
        # Calculate load duration based on intensity
        load_duration = 2.0 + (intensity * 8.0)  # 2-10 seconds based on intensity
        
        # Number of worker processes based on intensity
        num_workers = max(1, int(os.cpu_count() * intensity))
        
        # Create CPU-intensive workload
        def cpu_load():
            end_time = time.time() + load_duration
            while time.time() < end_time:
                # Compute intensive calculation
                for _ in range(10000000):
                    _ = random.random() ** random.random()
        
        # Execute workload in parallel
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(cpu_load) for _ in range(num_workers)]
            
            # Wait for all tasks to complete
            for future in futures:
                future.result()
    
    async def _inject_disk_full(self, intensity: float) -> None:
        """
        Simulate disk full condition.
        
        Args:
            intensity: Chaos intensity (0.0 to 1.0)
        """
        logger.info(f"Injecting disk full condition (intensity: {intensity})")
        
        # Create temporary large file in server data directory
        if self.server_process:
            try:
                # Calculate file size based on intensity (10MB to 100MB)
                file_size_mb = 10 + int(90 * intensity)
                
                # Create data directory if it doesn't exist
                data_dir = os.path.join(project_dir, "data", "tmp")
                os.makedirs(data_dir, exist_ok=True)
                
                # Create large file
                file_path = os.path.join(data_dir, f"chaos_test_large_file_{int(time.time())}.dat")
                
                # Use fallocate if available (faster)
                try:
                    subprocess.run(
                        ["fallocate", "-l", f"{file_size_mb}M", file_path],
                        check=True
                    )
                except (subprocess.SubprocessError, FileNotFoundError):
                    # Fall back to dd
                    with open(file_path, "wb") as f:
                        f.write(b'\0' * (file_size_mb * 1024 * 1024))
                
                logger.info(f"Created large file: {file_path} ({file_size_mb}MB)")
                
                # Keep the file for a while
                await asyncio.sleep(5.0)
                
                # Clean up
                os.unlink(file_path)
                logger.info(f"Removed large file: {file_path}")
                
            except Exception as e:
                logger.error(f"Error creating large file: {e}")
    
    async def _inject_memory_pressure(self, intensity: float) -> None:
        """
        Simulate memory pressure.
        
        Args:
            intensity: Chaos intensity (0.0 to 1.0)
        """
        logger.info(f"Injecting memory pressure (intensity: {intensity})")
        
        # Calculate memory to allocate based on intensity
        memory_mb = 100 + int(400 * intensity)  # 100MB to 500MB
        
        try:
            # Allocate memory
            memory_hog = bytearray(memory_mb * 1024 * 1024)
            
            # Access memory to ensure it's allocated
            for i in range(0, len(memory_hog), 4096):
                memory_hog[i] = 1
                
            logger.info(f"Allocated {memory_mb}MB of memory")
            
            # Hold memory for a while
            await asyncio.sleep(5.0)
            
            # Release memory
            del memory_hog
            
        except Exception as e:
            logger.error(f"Error allocating memory: {e}")
    
    async def _inject_malformed_data(self, intensity: float) -> None:
        """
        Send malformed data to the server.
        
        Args:
            intensity: Chaos intensity (0.0 to 1.0)
        """
        logger.info(f"Injecting malformed data (intensity: {intensity})")
        
        # Select random clients to send malformed data
        num_clients = max(1, int(len(self.clients) * intensity))
        clients = random.sample(self.clients, num_clients)
        
        for client in clients:
            if not client.is_connected():
                continue
                
            try:
                # Generate malformed messages
                malformed_messages = [
                    # Invalid JSON
                    "{",
                    # Missing required fields
                    json.dumps({"type": "ping"}),
                    # Unknown message type
                    json.dumps({"type": "unknown_type", "data": "test"}),
                    # Excessively large message
                    json.dumps({"type": "ping", "data": "X" * 1000000}),
                    # Malformed unicode
                    json.dumps({"type": "ping", "data": "\u0000\u0001\uffff"}),
                    # Invalid operation ID
                    json.dumps({"type": "cancel_operation", "operation_id": ""}),
                ]
                
                # Send malformed messages
                for message in malformed_messages:
                    if hasattr(client, "websocket") and client.websocket:
                        await asyncio.wrap_future(asyncio.run_coroutine_threadsafe(
                            client.websocket.send(message),
                            client.event_loop
                        ))
                        
                        # Brief pause between messages
                        await asyncio.sleep(0.1)
                        
            except Exception as e:
                logger.error(f"Error sending malformed data: {e}")
    
    async def _inject_slow_response(self, intensity: float) -> None:
        """
        Simulate slow server responses by delaying client messages.
        
        Args:
            intensity: Chaos intensity (0.0 to 1.0)
        """
        logger.info(f"Injecting slow response simulation (intensity: {intensity})")
        
        # Calculate delay based on intensity
        delay = 1.0 + (intensity * 9.0)  # 1-10 seconds based on intensity
        
        # Add delay to server process if available
        if self.server_process:
            try:
                # Send SIGSTOP to pause the server process
                self.server_process.send_signal(signal.SIGSTOP)
                logger.info(f"Paused server process for {delay}s")
                
                # Wait for the delay period
                await asyncio.sleep(delay)
                
                # Send SIGCONT to resume the server process
                self.server_process.send_signal(signal.SIGCONT)
                logger.info("Resumed server process")
                
            except Exception as e:
                logger.error(f"Error slowing server response: {e}")
    
    async def run(self) -> Dict[str, Any]:
        """
        Run the chaos test.
        
        Returns:
            Test results
        """
        # Record start time
        self.metrics["start_time"] = time.time()
        
        # Start server if needed
        start_server = True
        for arg in sys.argv:
            if arg == "--use-existing-server":
                start_server = False
                break
        
        server_started = True
        if start_server:
            server_started = await self.start_server()
            if not server_started:
                return {
                    "name": self.config.name,
                    "status": "failed",
                    "error": "Failed to start server"
                }
        
        try:
            # Create clients
            logger.info(f"Creating {self.config.client_count} clients")
            for i in range(self.config.client_count):
                client_id = f"client_{i}"
                client = self.create_client(client_id)
                self.clients.append(client)
                
                # Start client
                client.start()
            
            # Start client operation tasks
            logger.info("Starting client operations")
            client_tasks = []
            for i, client in enumerate(self.clients):
                client_id = f"client_{i}"
                task = asyncio.create_task(self.run_client_operations(client, client_id))
                client_tasks.append(task)
            
            # Start chaos injection task
            chaos_task = asyncio.create_task(self.inject_chaos())
            
            # Wait for test duration
            logger.info(f"Running test for {self.config.duration} seconds")
            await asyncio.sleep(self.config.duration)
            
            # Set stop event to end test
            self.stop_event.set()
            
            # Wait for all tasks to complete
            await chaos_task
            await asyncio.gather(*client_tasks, return_exceptions=True)
            
            # Record end time
            self.metrics["end_time"] = time.time()
            
            # Generate report
            return self.generate_report()
            
        except Exception as e:
            logger.error(f"Error running test: {e}")
            
            # Generate error report
            return {
                "name": self.config.name,
                "status": "failed",
                "error": str(e)
            }
            
        finally:
            # Stop clients
            logger.info("Stopping clients")
            for client in self.clients:
                client.stop()
            
            # Stop server if we started it
            if start_server and server_started:
                logger.info("Stopping server")
                self.stop_server()
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a test report.
        
        Returns:
            Test report
        """
        # Calculate test statistics
        test_duration = self.metrics["end_time"] - self.metrics["start_time"]
        
        # Count completed operations
        completed_ops = sum(1 for op in self.operations.values() 
                          if op.get("status") == "completed")
        failed_ops = sum(1 for op in self.operations.values() 
                        if op.get("status") == "failed")
        
        # Calculate success rate
        if self.operations:
            success_rate = completed_ops / len(self.operations) * 100
        else:
            success_rate = 0
        
        # Aggregate client metrics
        total_connections = sum(client.get("connections", 0) 
                             for client in self.metrics["client_metrics"].values())
        total_reconnections = sum(client.get("reconnections", 0) 
                               for client in self.metrics["client_metrics"].values())
        
        # Create report
        report = {
            "name": self.config.name,
            "description": self.config.description,
            "chaos_type": self.config.chaos_type,
            "status": "passed" if success_rate >= 90 else "failed",
            "start_time": self.metrics["start_time"],
            "end_time": self.metrics["end_time"],
            "duration": test_duration,
            "client_count": self.config.client_count,
            "operations": {
                "total": len(self.operations),
                "completed": completed_ops,
                "failed": failed_ops,
                "success_rate": success_rate
            },
            "connections": {
                "total": total_connections,
                "reconnections": total_reconnections
            },
            "chaos_events": len(self.metrics["chaos_events"]),
            "errors": len(self.metrics["errors"])
        }
        
        # Save detailed metrics to file
        detailed_report = {
            "config": {
                "name": self.config.name,
                "description": self.config.description,
                "chaos_type": self.config.chaos_type,
                "duration": self.config.duration,
                "frequency": self.config.frequency,
                "intensity": self.config.intensity,
                "client_count": self.config.client_count,
                "operations_per_client": self.config.operations_per_client
            },
            "summary": report,
            "metrics": self.metrics
        }
        
        # Write report to file
        report_path = self.report_dir / f"chaos_test_{self.config.chaos_type}_{int(time.time())}.json"
        with open(report_path, "w") as f:
            json.dump(detailed_report, f, indent=2)
            
        logger.info(f"Chaos test {self.config.name} completed")
        logger.info(f"Status: {report['status']}")
        logger.info(f"Operations: {report['operations']['completed']}/{report['operations']['total']} completed ({report['operations']['success_rate']:.1f}%)")
        logger.info(f"Connections: {report['connections']['total']} total, {report['connections']['reconnections']} reconnections")
        logger.info(f"Chaos events: {report['chaos_events']}")
        logger.info(f"Errors: {report['errors']}")
        logger.info(f"Report saved to {report_path}")
        
        return report


def run_single_test(config: ChaosTestConfig) -> Dict[str, Any]:
    """
    Run a single chaos test.
    
    Args:
        config: Test configuration
        
    Returns:
        Test report
    """
    # Create and run test
    test = ChaosTest(config)
    return asyncio.run(test.run())


def run_all_tests(duration: float = 60.0, intensity: float = 0.5) -> None:
    """
    Run all chaos tests.
    
    Args:
        duration: Test duration in seconds
        intensity: Chaos intensity (0.0 to 1.0)
    """
    # Define all test configurations
    test_configs = [
        ChaosTestConfig(
            name="Network Disconnect Test",
            description="Tests resilience against network disconnections",
            chaos_type=ChaosType.NETWORK_DISCONNECT,
            duration=duration,
            frequency=10.0,
            intensity=intensity,
            client_count=5,
            operations_per_client=2
        ),
        ChaosTestConfig(
            name="Server Crash Test",
            description="Tests resilience against server crashes",
            chaos_type=ChaosType.SERVER_CRASH,
            duration=duration,
            frequency=20.0,
            intensity=intensity,
            client_count=3,
            operations_per_client=2
        ),
        ChaosTestConfig(
            name="High Load Test",
            description="Tests resilience under high CPU load",
            chaos_type=ChaosType.HIGH_LOAD,
            duration=duration,
            frequency=15.0,
            intensity=intensity,
            client_count=3,
            operations_per_client=3
        ),
        ChaosTestConfig(
            name="Disk Full Test",
            description="Tests resilience when disk space is limited",
            chaos_type=ChaosType.DISK_FULL,
            duration=duration,
            frequency=15.0,
            intensity=intensity,
            client_count=2,
            operations_per_client=2
        ),
        ChaosTestConfig(
            name="Memory Pressure Test",
            description="Tests resilience under memory pressure",
            chaos_type=ChaosType.MEMORY_PRESSURE,
            duration=duration,
            frequency=15.0,
            intensity=intensity,
            client_count=2,
            operations_per_client=2
        ),
        ChaosTestConfig(
            name="Malformed Data Test",
            description="Tests resilience against malformed data",
            chaos_type=ChaosType.MALFORMED_DATA,
            duration=duration,
            frequency=5.0,
            intensity=intensity,
            client_count=2,
            operations_per_client=2
        ),
        ChaosTestConfig(
            name="Slow Response Test",
            description="Tests resilience against slow server responses",
            chaos_type=ChaosType.SLOW_RESPONSE,
            duration=duration,
            frequency=15.0,
            intensity=intensity,
            client_count=3,
            operations_per_client=2
        )
    ]
    
    # Run tests sequentially
    results = []
    for config in test_configs:
        logger.info(f"Running test: {config.name}")
        result = run_single_test(config)
        results.append(result)
        
        # Wait between tests
        time.sleep(2)
    
    # Print summary
    print("\nCHAOS TEST SUMMARY")
    print("==================")
    
    for result in results:
        status_str = "PASSED" if result.get("status") == "passed" else "FAILED"
        print(f"{result.get('name')}: {status_str}")
        
        operations = result.get("operations", {})
        if operations:
            success_rate = operations.get("success_rate", 0)
            print(f"  Operations: {operations.get('completed', 0)}/{operations.get('total', 0)} completed ({success_rate:.1f}%)")
            
        print()
    
    # Check overall status
    passed = sum(1 for r in results if r.get("status") == "passed")
    total = len(results)
    
    print(f"Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description="Run chaos tests for WebSocket server")
    
    # Test selection
    parser.add_argument("--test", choices=[t.value for t in ChaosType], 
                      help="Specific test to run")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    
    # Test parameters
    parser.add_argument("--duration", type=float, default=60.0, 
                      help="Test duration in seconds")
    parser.add_argument("--frequency", type=float, default=10.0, 
                      help="Chaos frequency in seconds")
    parser.add_argument("--intensity", type=float, default=0.5, 
                      help="Chaos intensity (0.0 to 1.0)")
    parser.add_argument("--client-count", type=int, default=3, 
                      help="Number of clients to create")
    parser.add_argument("--operations", type=int, default=2, 
                      help="Operations per client")
    
    # Server options
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8765, help="Server port")
    parser.add_argument("--server-script", default="run_websocket_server.py", 
                      help="Server script to run")
    parser.add_argument("--use-existing-server", action="store_true", 
                      help="Use existing server instead of starting a new one")
    
    # Output options
    parser.add_argument("--report-dir", help="Directory for test reports")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.all:
        # Run all tests
        run_all_tests(duration=args.duration, intensity=args.intensity)
    elif args.test:
        # Run specific test
        config = ChaosTestConfig(
            name=f"{args.test.replace('_', ' ').title()} Test",
            description=f"Tests resilience against {args.test.replace('_', ' ')}",
            chaos_type=args.test,
            duration=args.duration,
            frequency=args.frequency,
            intensity=args.intensity,
            server_host=args.host,
            server_port=args.port,
            server_script=args.server_script,
            client_count=args.client_count,
            operations_per_client=args.operations,
            report_dir=args.report_dir
        )
        
        result = run_single_test(config)
        
        # Print summary
        status_str = "PASSED" if result.get("status") == "passed" else "FAILED"
        print(f"\nTest result: {status_str}")
        
        operations = result.get("operations", {})
        if operations:
            success_rate = operations.get("success_rate", 0)
            print(f"Operations: {operations.get('completed', 0)}/{operations.get('total', 0)} completed ({success_rate:.1f}%)")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()