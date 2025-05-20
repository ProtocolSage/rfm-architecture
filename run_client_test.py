#!/usr/bin/env python
"""
WebSocket client test script for resilience testing.

This script tests the enhanced WebSocket client's resilience features
by connecting to a server and performing operations that test connection
recovery, state preservation, and other resilience aspects.
"""

import os
import sys
import logging
import argparse
import asyncio
import json
import time
import signal
import uuid
from typing import Dict, Any, Optional, List
import random

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# Set up structured logger class BEFORE importing modules
try:
    from rfm.core.logging_config import StructuredLogger
    import logging as _logging_setup
    _logging_setup.setLoggerClass(StructuredLogger)
except Exception as e:
    print(f"Warning: Couldn't set StructuredLogger as default logger class: {e}")
    print("Will fall back to standard logging")

# Import required modules
try:
    from rfm.core.logging_config import configure_logging, LogLevel, LogCategory
    from ui.rfm_ui.websocket_client_enhanced import (
        WebSocketClient, ReconnectionConfig, ConnectionState, MessageType, OperationStatus
    )
except ImportError:
    print("Failed to import required modules. Make sure you're running this script from the project root.")
    sys.exit(1)

class ClientTest:
    """
    Test harness for the enhanced WebSocket client.
    
    Tests the client's resilience capabilities including:
    - Automatic reconnection
    - Operation state preservation
    - Message delivery guarantees
    """
    
    def __init__(self, 
                server_url: str = "ws://localhost:8765",
                authentication: Optional[Dict[str, str]] = None,
                test_duration: float = 60.0,
                log_level: str = "info",
                debug_mode: bool = False):
        """
        Initialize the client test harness.
        
        Args:
            server_url: WebSocket server URL
            authentication: Optional authentication parameters
            test_duration: Test duration in seconds
            log_level: Log level
            debug_mode: Enable debug mode
        """
        self.server_url = server_url
        self.authentication = authentication
        self.test_duration = test_duration
        self.debug_mode = debug_mode
        
        # Set up logging
        log_level_map = {
            "debug": LogLevel.DEBUG,
            "info": LogLevel.INFO,
            "warning": LogLevel.WARNING,
            "error": LogLevel.ERROR
        }
        self.log_level = log_level_map.get(log_level.lower(), LogLevel.INFO)
        
        # Create log directory
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure logging
        configure_logging(
            app_name="client_test",
            log_dir=log_dir,
            console_level=self.log_level,
            file_level=LogLevel.DEBUG,
            json_format=True
        )
        
        # Create logger
        self.logger = logging.getLogger("client_test")
        
        # Test metrics
        self.metrics = {
            "reconnections": 0,
            "operations_started": 0,
            "operations_completed": 0,
            "operations_failed": 0,
            "operations_canceled": 0,
            "progress_updates": 0,
            "connection_state_changes": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "errors": 0,
            "test_start_time": 0,
            "test_end_time": 0,
            "events": []
        }
        
        # Test state
        self.client = None
        self.stop_event = asyncio.Event()
        self.active_operations = {}
        
        # Callbacks
        self.callbacks = {}
    
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
        
        self.metrics["events"].append(event)
        
        # Log to console
        self.logger.info(f"Event: {event_type} - {json.dumps(details)}")
    
    def initialize_client(self) -> WebSocketClient:
        """
        Initialize the WebSocket client with resilience configuration.
        
        Returns:
            Configured WebSocketClient instance
        """
        # Configure reconnection with exponential backoff
        reconnection_config = ReconnectionConfig(
            initial_delay=1.0,
            max_delay=20.0,
            multiplier=1.5,
            jitter=0.2,
            max_attempts=0  # Infinite retries
        )
        
        # Create client
        client = WebSocketClient(
            url=self.server_url,
            reconnection_config=reconnection_config,
            authentication=self.authentication,
            log_level=self.log_level,
            debug_mode=self.debug_mode
        )
        
        # Register callbacks
        client.add_callback(MessageType.CONNECTION_STATUS, self.on_connection_status)
        client.add_callback(MessageType.OPERATION_STARTED, self.on_operation_started)
        client.add_callback(MessageType.PROGRESS_UPDATE, self.on_progress_update)
        client.add_callback(MessageType.OPERATION_COMPLETED, self.on_operation_completed)
        client.add_callback(MessageType.OPERATION_FAILED, self.on_operation_failed)
        client.add_callback(MessageType.OPERATION_CANCELED, self.on_operation_canceled)
        client.add_callback(MessageType.ERROR, self.on_error)
        
        return client
    
    def on_connection_status(self, data: Dict[str, Any]) -> None:
        """
        Handle connection status changes.
        
        Args:
            data: Connection status data
        """
        status = data.get("status")
        details = data.get("details", {})
        
        self.metrics["connection_state_changes"] += 1
        
        if status == ConnectionState.CONNECTED:
            self.log_event("connection_established", {
                "connection_id": self.client.client_id
            })
            
        elif status == ConnectionState.RECONNECTING:
            self.metrics["reconnections"] += 1
            self.log_event("connection_reconnecting", {
                "connection_id": self.client.client_id,
                "reconnect_attempt": self.client.reconnect_attempt
            })
            
        elif status == ConnectionState.DISCONNECTED:
            self.log_event("connection_lost", {
                "connection_id": self.client.client_id
            })
            
        elif status == ConnectionState.ERROR:
            self.log_event("connection_error", {
                "connection_id": self.client.client_id,
                "error": details.get("error")
            })
    
    def on_operation_started(self, data: Dict[str, Any]) -> None:
        """
        Handle operation started events.
        
        Args:
            data: Operation data
        """
        operation = data.get("operation", {})
        operation_id = operation.get("operation_id")
        
        if operation_id:
            self.metrics["operations_started"] += 1
            self.active_operations[operation_id] = operation
            
            self.log_event("operation_started", {
                "operation_id": operation_id,
                "operation_type": operation.get("operation_type"),
                "operation_name": operation.get("name")
            })
    
    def on_progress_update(self, data: Dict[str, Any]) -> None:
        """
        Handle progress update events.
        
        Args:
            data: Progress data
        """
        update_data = data.get("data", {})
        operation_id = update_data.get("operation_id")
        
        if operation_id:
            self.metrics["progress_updates"] += 1
            
            # Log significant progress only (0%, 25%, 50%, 75%, 100%)
            progress = update_data.get("progress", 0)
            if progress % 25 == 0:
                self.log_event("operation_progress", {
                    "operation_id": operation_id,
                    "progress": progress,
                    "current_step": update_data.get("current_step")
                })
    
    def on_operation_completed(self, data: Dict[str, Any]) -> None:
        """
        Handle operation completed events.
        
        Args:
            data: Operation data
        """
        operation_id = data.get("operation_id")
        
        if operation_id:
            self.metrics["operations_completed"] += 1
            
            if operation_id in self.active_operations:
                del self.active_operations[operation_id]
                
            self.log_event("operation_completed", {
                "operation_id": operation_id
            })
    
    def on_operation_failed(self, data: Dict[str, Any]) -> None:
        """
        Handle operation failed events.
        
        Args:
            data: Operation data
        """
        operation_id = data.get("operation_id")
        
        if operation_id:
            self.metrics["operations_failed"] += 1
            
            if operation_id in self.active_operations:
                del self.active_operations[operation_id]
                
            self.log_event("operation_failed", {
                "operation_id": operation_id,
                "error": data.get("details", {}).get("error_message")
            })
    
    def on_operation_canceled(self, data: Dict[str, Any]) -> None:
        """
        Handle operation canceled events.
        
        Args:
            data: Operation data
        """
        operation_id = data.get("operation_id")
        
        if operation_id:
            self.metrics["operations_canceled"] += 1
            
            if operation_id in self.active_operations:
                del self.active_operations[operation_id]
                
            self.log_event("operation_canceled", {
                "operation_id": operation_id
            })
    
    def on_error(self, data: Dict[str, Any]) -> None:
        """
        Handle error events.
        
        Args:
            data: Error data
        """
        self.metrics["errors"] += 1
        
        self.log_event("client_error", {
            "error_code": data.get("error_code"),
            "error_message": data.get("error_message")
        })
    
    async def simulate_operation(self) -> str:
        """
        Simulate a long-running operation with progress updates.
        
        Returns:
            Operation ID
        """
        # Generate operation ID
        operation_id = str(uuid.uuid4())
        
        # Create operation details
        operation_types = ["fractal_render", "animation_export", "parameter_optimization", "morphing"]
        operation_type = random.choice(operation_types)
        operation_name = f"{operation_type.replace('_', ' ').title()} {operation_id[:6]}"
        
        # Start operation
        await self.send_operation_started(operation_id, operation_type, operation_name)
        
        # Start progress updates task
        asyncio.create_task(self.simulate_progress_updates(operation_id))
        
        return operation_id
    
    async def send_operation_started(self, 
                                  operation_id: str, 
                                  operation_type: str, 
                                  name: str) -> None:
        """
        Send operation started message.
        
        Args:
            operation_id: Operation ID
            operation_type: Type of operation
            name: Operation name
        """
        if not self.client:
            return
            
        # Create operation data
        operation = {
            "operation_id": operation_id,
            "operation_type": operation_type,
            "name": name,
            "status": "pending",
            "progress": 0,
            "start_time": time.time(),
            "details": {
                "parameters": {
                    "resolution": random.choice([512, 1024, 2048, 4096]),
                    "iterations": random.choice([100, 500, 1000, 5000]),
                    "precision": random.choice(["single", "double"])
                }
            }
        }
        
        # Create message
        message = {
            "type": MessageType.OPERATION_STARTED,
            "operation": operation,
            "timestamp": time.time()
        }
        
        # Record send attempt
        self.metrics["messages_sent"] += 1
        
        # Send through event loop
        if self.client.event_loop and self.client.event_loop.is_running():
            await asyncio.wrap_future(asyncio.run_coroutine_threadsafe(
                self.client.send_message(message),
                self.client.event_loop
            ))
    
    async def simulate_progress_updates(self, operation_id: str) -> None:
        """
        Simulate progress updates for an operation.
        
        Args:
            operation_id: Operation ID
        """
        # Determine operation parameters
        total_updates = random.randint(10, 50)
        step_size = 100.0 / total_updates
        delay_base = random.uniform(0.1, 0.5)
        
        # Create steps
        steps = ["Initializing", "Processing", "Rendering", "Finalizing"]
        current_step = steps[0]
        
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
            
            # Send progress update
            await self.send_progress_update(operation_id, progress, current_step)
            
            # Random delay between updates
            delay = delay_base * random.uniform(0.8, 1.2)
            await asyncio.sleep(delay)
        
        # Complete operation (small chance of failure)
        if random.random() < 0.05:
            await self.send_operation_failed(operation_id, "Simulated random failure")
        elif random.random() < 0.03:
            await self.send_operation_canceled(operation_id)
        else:
            await self.send_operation_completed(operation_id)
    
    async def send_progress_update(self, 
                                operation_id: str, 
                                progress: float, 
                                current_step: str) -> None:
        """
        Send progress update message.
        
        Args:
            operation_id: Operation ID
            progress: Progress percentage (0-100)
            current_step: Current step description
        """
        if not self.client:
            return
            
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
        
        # Record send attempt
        self.metrics["messages_sent"] += 1
        
        # Send through event loop
        if self.client.event_loop and self.client.event_loop.is_running():
            await asyncio.wrap_future(asyncio.run_coroutine_threadsafe(
                self.client.send_message(message),
                self.client.event_loop
            ))
    
    async def send_operation_completed(self, operation_id: str) -> None:
        """
        Send operation completed message.
        
        Args:
            operation_id: Operation ID
        """
        if not self.client:
            return
            
        # Create message
        message = {
            "type": MessageType.OPERATION_COMPLETED,
            "operation_id": operation_id,
            "timestamp": time.time(),
            "details": {
                "results": {
                    "duration": random.uniform(5.0, 60.0),
                    "output_file": f"output_{operation_id[:8]}.png"
                }
            }
        }
        
        # Record send attempt
        self.metrics["messages_sent"] += 1
        
        # Send through event loop
        if self.client.event_loop and self.client.event_loop.is_running():
            await asyncio.wrap_future(asyncio.run_coroutine_threadsafe(
                self.client.send_message(message),
                self.client.event_loop
            ))
    
    async def send_operation_failed(self, 
                                 operation_id: str, 
                                 error_message: str) -> None:
        """
        Send operation failed message.
        
        Args:
            operation_id: Operation ID
            error_message: Error message
        """
        if not self.client:
            return
            
        # Create message
        message = {
            "type": MessageType.OPERATION_FAILED,
            "operation_id": operation_id,
            "timestamp": time.time(),
            "details": {
                "error_message": error_message,
                "error_code": "SIMULATION_ERROR"
            }
        }
        
        # Record send attempt
        self.metrics["messages_sent"] += 1
        
        # Send through event loop
        if self.client.event_loop and self.client.event_loop.is_running():
            await asyncio.wrap_future(asyncio.run_coroutine_threadsafe(
                self.client.send_message(message),
                self.client.event_loop
            ))
    
    async def send_operation_canceled(self, operation_id: str) -> None:
        """
        Send operation canceled message.
        
        Args:
            operation_id: Operation ID
        """
        if not self.client:
            return
            
        # Create message
        message = {
            "type": MessageType.OPERATION_CANCELED,
            "operation_id": operation_id,
            "timestamp": time.time(),
            "details": {
                "reason": "User canceled operation"
            }
        }
        
        # Record send attempt
        self.metrics["messages_sent"] += 1
        
        # Send through event loop
        if self.client.event_loop and self.client.event_loop.is_running():
            await asyncio.wrap_future(asyncio.run_coroutine_threadsafe(
                self.client.send_message(message),
                self.client.event_loop
            ))
    
    async def run_test(self) -> Dict[str, Any]:
        """
        Run the client test.
        
        Returns:
            Test metrics
        """
        # Initialize metrics
        self.metrics["test_start_time"] = time.time()
        
        # Log test start
        self.logger.info(f"Starting client test (duration: {self.test_duration}s)")
        self.log_event("test_started", {
            "server_url": self.server_url,
            "test_duration": self.test_duration
        })
        
        # Create and start client
        self.client = self.initialize_client()
        self.client.start()
        
        # Set up signal handlers for graceful shutdown
        loop = asyncio.get_running_loop()
        
        def signal_handler():
            self.logger.info("Shutdown signal received")
            self.stop_event.set()
        
        # Register signal handlers
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)
        
        try:
            # Wait for initial connection
            for _ in range(10):  # Wait up to 5 seconds
                if self.client.is_connected():
                    break
                await asyncio.sleep(0.5)
            
            # Start operation generator task
            operation_gen_task = asyncio.create_task(self.generate_operations())
            
            # Wait for test duration or stop signal
            try:
                await asyncio.wait_for(self.stop_event.wait(), self.test_duration)
            except asyncio.TimeoutError:
                # Test duration reached
                self.logger.info("Test duration reached")
                
            # Set stop event
            self.stop_event.set()
            
            # Wait for operation generator to finish
            await operation_gen_task
            
            # Log test completion
            self.logger.info("Client test completed")
            
        finally:
            # Stop client
            if self.client:
                self.client.stop()
                
                # Update metrics with client stats
                message_stats = self.client.get_message_stats()
                self.metrics["messages_received"] = message_stats.received_count
                self.metrics["messages_sent"] = message_stats.sent_count
            
            # Record test end time
            self.metrics["test_end_time"] = time.time()
            
            # Calculate test duration
            test_duration = self.metrics["test_end_time"] - self.metrics["test_start_time"]
            
            # Log test summary
            self.log_event("test_completed", {
                "actual_duration": test_duration,
                "reconnections": self.metrics["reconnections"],
                "operations_started": self.metrics["operations_started"],
                "operations_completed": self.metrics["operations_completed"],
                "operations_failed": self.metrics["operations_failed"],
                "operations_canceled": self.metrics["operations_canceled"],
                "progress_updates": self.metrics["progress_updates"],
                "messages_sent": self.metrics["messages_sent"],
                "messages_received": self.metrics["messages_received"]
            })
            
            # Generate report
            report = {
                "test_id": str(uuid.uuid4()),
                "test_type": "client_resilience",
                "server_url": self.server_url,
                "planned_duration": self.test_duration,
                "actual_duration": test_duration,
                "timestamp": time.time(),
                "metrics": {
                    k: v for k, v in self.metrics.items() if k != "events"
                },
                "events": self.metrics["events"]
            }
            
            # Save report to file
            report_dir = "reports"
            os.makedirs(report_dir, exist_ok=True)
            
            report_file = os.path.join(
                report_dir, 
                f"client_test_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2)
                
            self.logger.info(f"Test report saved to {report_file}")
            
            return report
    
    async def generate_operations(self) -> None:
        """Generate operations periodically until stopped."""
        # Wait for initial connection
        while not self.client.is_connected() and not self.stop_event.is_set():
            await asyncio.sleep(0.5)
        
        # Stop if requested
        if self.stop_event.is_set():
            return
            
        # Start operations with random delays
        while not self.stop_event.is_set():
            # Start a new operation
            await self.simulate_operation()
            
            # Wait before starting next operation
            delay = random.uniform(2.0, 10.0)
            try:
                await asyncio.wait_for(self.stop_event.wait(), delay)
            except asyncio.TimeoutError:
                # Delay elapsed, continue
                pass

async def main(args):
    """
    Main entry point.
    
    Args:
        args: Command-line arguments
    """
    # Configure authentication if requested
    authentication = None
    if args.enable_auth:
        authentication = {
            "client_id": "resilience_test_client",
            "token": "test_key_67890"
        }
    
    # Create client test
    # Use secure WebSocket if SSL is enabled
    protocol = "wss" if args.ssl else "ws"

    # Create connection URL with SSL verification parameters
    url = f"{protocol}://{args.host}:{args.port}"
    if args.ssl and args.ssl_verify is False:
        url += "?ssl_verify=0"
        print(f"Warning: SSL certificate verification disabled for {url}")

    client_test = ClientTest(
        server_url=url,
        authentication=authentication,
        test_duration=args.duration,
        log_level=args.log_level,
        debug_mode=args.debug
    )
    
    # Run test
    try:
        report = await client_test.run_test()
        
        # Print summary
        print("\nTest Results:")
        print(f"Test Duration: {report['actual_duration']:.2f}s")
        print(f"Reconnections: {report['metrics']['reconnections']}")
        print(f"Operations Started: {report['metrics']['operations_started']}")
        print(f"Operations Completed: {report['metrics']['operations_completed']}")
        print(f"Operations Failed: {report['metrics']['operations_failed']}")
        print(f"Operations Canceled: {report['metrics']['operations_canceled']}")
        print(f"Progress Updates: {report['metrics']['progress_updates']}")
        print(f"Messages Sent: {report['metrics']['messages_sent']}")
        print(f"Messages Received: {report['metrics']['messages_received']}")
        print(f"Errors: {report['metrics']['errors']}")
        print(f"Report saved to: {report.get('report_file', 'reports directory')}")
        
        return 0
    except Exception as e:
        logging.error(f"Error running client test: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Test WebSocket client resilience")
    
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8765, help="Server port")
    parser.add_argument("--duration", type=float, default=60.0, help="Test duration in seconds")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"], help="Log level")
    parser.add_argument("--enable-auth", action="store_true", help="Enable authentication")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--ssl", action="store_true", help="Use secure WebSocket (wss://)")
    parser.add_argument("--ssl-verify", dest="ssl_verify", action="store_true", help="Verify SSL certificate")
    parser.add_argument("--no-ssl-verify", dest="ssl_verify", action="store_false", help="Skip SSL certificate verification")
    parser.set_defaults(ssl_verify=True)
    
    args = parser.parse_args()
    
    # Run the client test
    exit_code = asyncio.run(main(args))
    sys.exit(exit_code)