"""
WebSocket client for real-time progress reporting in RFM Architecture UI.

This module provides a WebSocket client that connects to the progress
reporting server to receive real-time updates during long-running operations.
"""

import asyncio
import json
import logging
import threading
import time
import traceback
import websockets
from typing import Dict, Any, List, Optional, Callable, Set, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class OperationStatus(str, Enum):
    """Status of a tracked operation."""
    
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


@dataclass
class OperationInfo:
    """Information about an operation."""
    
    operation_id: str
    operation_type: str
    name: str
    status: OperationStatus
    progress: float
    current_step: Optional[str] = None
    total_steps: Optional[int] = None
    start_time: Optional[float] = None
    last_update_time: Optional[float] = None
    details: Dict[str, Any] = None


class WebSocketClient:
    """
    WebSocket client for receiving progress updates.
    
    This class manages the WebSocket connection to the progress reporting
    server and handles incoming messages.
    """
    
    def __init__(self, url: str = "ws://localhost:8765"):
        """
        Initialize the WebSocket client.
        
        Args:
            url: WebSocket server URL
        """
        self.url = url
        self.websocket = None
        self.connected = False
        self.connecting = False
        self.reconnect_delay = 1.0  # Initial reconnect delay (seconds)
        self.max_reconnect_delay = 30.0  # Maximum reconnect delay (seconds)
        self.operations: Dict[str, OperationInfo] = {}
        self.callbacks: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {
            "progress_update": [],
            "operation_started": [],
            "operation_completed": [],
            "operation_failed": [],
            "operation_canceled": [],
            "operations_list": [],
            "connection_status": []
        }
        self.receive_task = None
        self.ping_task = None
        self.event_loop = None
        self.thread = None
        
        # Create event loop in thread
        self.started = False
    
    def start(self) -> None:
        """Start the WebSocket client in a background thread."""
        if self.started:
            logger.warning("WebSocket client already started")
            return
            
        # Create new event loop for the thread
        self.event_loop = asyncio.new_event_loop()
        
        # Create and start the thread
        self.thread = threading.Thread(
            target=self._run_event_loop,
            name="WebSocketClientThread",
            daemon=True
        )
        self.thread.start()
        self.started = True
        
        logger.info(f"WebSocket client started, connecting to {self.url}")
    
    def stop(self) -> None:
        """Stop the WebSocket client."""
        if not self.started:
            return
            
        # Stop the event loop
        if self.event_loop:
            asyncio.run_coroutine_threadsafe(self._disconnect(), self.event_loop)
            
            # Give it a moment to disconnect gracefully
            time.sleep(0.5)
            
            # Stop the event loop
            try:
                self.event_loop.call_soon_threadsafe(self.event_loop.stop)
            except Exception:
                pass
                
        # Wait for thread to finish
        if self.thread:
            self.thread.join(timeout=1.0)
            
        self.started = False
        self.connected = False
        logger.info("WebSocket client stopped")
    
    def _run_event_loop(self) -> None:
        """Run the event loop in a thread."""
        asyncio.set_event_loop(self.event_loop)
        
        # Create connect task
        asyncio.ensure_future(self._connect_with_retry())
        
        # Run the event loop
        try:
            self.event_loop.run_forever()
        except Exception as e:
            logger.error(f"Error in WebSocket client event loop: {e}")
            logger.debug(traceback.format_exc())
        finally:
            # Clean up
            for task in asyncio.all_tasks(self.event_loop):
                task.cancel()
                
            self.event_loop.run_until_complete(asyncio.sleep(0.1))
            self.event_loop.close()
            logger.debug("WebSocket client event loop stopped")
    
    async def _connect_with_retry(self) -> None:
        """Connect to the WebSocket server with retry."""
        while True:
            if self.connected or self.connecting:
                await asyncio.sleep(0.1)
                continue
                
            try:
                self.connecting = True
                
                # Notify about connection attempt
                await self._notify_connection_status("connecting")
                
                # Connect to the server
                logger.debug(f"Connecting to WebSocket server at {self.url}")
                self.websocket = await websockets.connect(self.url, close_timeout=2.0)
                self.connected = True
                self.reconnect_delay = 1.0  # Reset reconnect delay
                self.connecting = False
                
                # Notify about connection
                await self._notify_connection_status("connected")
                
                logger.info(f"Connected to WebSocket server at {self.url}")
                
                # Start receive task
                self.receive_task = asyncio.ensure_future(self._receive_messages())
                
                # Start ping task
                self.ping_task = asyncio.ensure_future(self._send_pings())
                
                # Wait for disconnect
                await self.receive_task
                
            except Exception as e:
                self.connected = False
                self.connecting = False
                
                # Notify about disconnection
                await self._notify_connection_status("disconnected", {"error": str(e)})
                
                # Wait before reconnecting
                logger.warning(f"Failed to connect to WebSocket server: {e}, retrying in {self.reconnect_delay}s")
                await asyncio.sleep(self.reconnect_delay)
                
                # Increase reconnect delay with exponential backoff
                self.reconnect_delay = min(self.reconnect_delay * 1.5, self.max_reconnect_delay)
    
    async def _disconnect(self) -> None:
        """Disconnect from the WebSocket server."""
        if not self.connected and not self.connecting:
            return
            
        # Cancel tasks
        if self.receive_task:
            self.receive_task.cancel()
            self.receive_task = None
            
        if self.ping_task:
            self.ping_task.cancel()
            self.ping_task = None
            
        # Close websocket
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.debug(f"Error closing WebSocket: {e}")
                
        self.connected = False
        self.connecting = False
        await self._notify_connection_status("disconnected")
        logger.info("Disconnected from WebSocket server")
    
    async def _receive_messages(self) -> None:
        """Receive and handle messages from the WebSocket server."""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from server: {message}")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    logger.debug(traceback.format_exc())
                    
        except asyncio.CancelledError:
            # Task canceled, exit
            pass
        except Exception as e:
            logger.error(f"Error in WebSocket receive loop: {e}")
            logger.debug(traceback.format_exc())
            
        # Mark as disconnected
        self.connected = False
        await self._notify_connection_status("disconnected")
    
    async def _send_pings(self) -> None:
        """Send periodic ping messages to keep the connection alive."""
        try:
            while self.connected:
                await asyncio.sleep(30)  # Send ping every 30 seconds
                
                if not self.connected:
                    break
                    
                try:
                    await self.websocket.send(json.dumps({
                        "type": "ping",
                        "timestamp": time.time()
                    }))
                except Exception as e:
                    logger.debug(f"Error sending ping: {e}")
                    break
                    
        except asyncio.CancelledError:
            # Task canceled, exit
            pass
        except Exception as e:
            logger.error(f"Error in ping task: {e}")
            logger.debug(traceback.format_exc())
            
        # Mark as disconnected
        self.connected = False
    
    async def _handle_message(self, data: Dict[str, Any]) -> None:
        """
        Handle a message from the WebSocket server.
        
        Args:
            data: Message data
        """
        message_type = data.get("type")
        
        if message_type == "progress_update":
            # Handle progress update
            update_data = data.get("data", {})
            operation_id = update_data.get("operation_id")
            
            if operation_id:
                # Update operation info
                if operation_id not in self.operations:
                    # Create new operation info
                    self.operations[operation_id] = OperationInfo(
                        operation_id=operation_id,
                        operation_type=update_data.get("operation_type", "unknown"),
                        name=update_data.get("name", f"Operation {operation_id}"),
                        status=OperationStatus(update_data.get("status", "running")),
                        progress=update_data.get("progress", 0.0),
                        current_step=update_data.get("current_step"),
                        total_steps=update_data.get("total_steps"),
                        start_time=update_data.get("start_time", time.time()),
                        last_update_time=update_data.get("timestamp", time.time()),
                        details=update_data.get("details", {})
                    )
                else:
                    # Update existing operation info
                    op = self.operations[operation_id]
                    op.progress = update_data.get("progress", op.progress)
                    op.status = OperationStatus(update_data.get("status", op.status))
                    
                    if "current_step" in update_data:
                        op.current_step = update_data["current_step"]
                        
                    if "total_steps" in update_data:
                        op.total_steps = update_data["total_steps"]
                        
                    op.last_update_time = update_data.get("timestamp", time.time())
                    
                    if "details" in update_data:
                        if op.details is None:
                            op.details = {}
                        op.details.update(update_data["details"])
                
                # Notify callbacks
                await self._notify_callbacks("progress_update", data)
                
        elif message_type == "operations_list":
            # Handle operations list
            operations = data.get("operations", [])
            
            # Update operations dictionary
            new_operations = {}
            for op_data in operations:
                operation_id = op_data.get("operation_id")
                if operation_id:
                    # Create or update operation info
                    if operation_id in self.operations:
                        op = self.operations[operation_id]
                        op.status = OperationStatus(op_data.get("status", op.status))
                        op.progress = op_data.get("progress", op.progress)
                        op.last_update_time = op_data.get("last_update_time", op.last_update_time)
                        new_operations[operation_id] = op
                    else:
                        new_operations[operation_id] = OperationInfo(
                            operation_id=operation_id,
                            operation_type=op_data.get("operation_type", "unknown"),
                            name=op_data.get("name", f"Operation {operation_id}"),
                            status=OperationStatus(op_data.get("status", "running")),
                            progress=op_data.get("progress", 0.0),
                            start_time=op_data.get("start_time", time.time()),
                            last_update_time=op_data.get("last_update_time", time.time())
                        )
            
            # Replace operations dictionary
            self.operations = new_operations
            
            # Notify callbacks
            await self._notify_callbacks("operations_list", data)
            
        elif message_type == "operation_started":
            # Handle operation started
            operation_data = data.get("operation", {})
            operation_id = operation_data.get("operation_id")
            
            if operation_id:
                # Create operation info
                self.operations[operation_id] = OperationInfo(
                    operation_id=operation_id,
                    operation_type=operation_data.get("operation_type", "unknown"),
                    name=operation_data.get("name", f"Operation {operation_id}"),
                    status=OperationStatus.PENDING,
                    progress=0.0,
                    start_time=time.time(),
                    last_update_time=time.time()
                )
                
                # Notify callbacks
                await self._notify_callbacks("operation_started", data)
                
        elif message_type == "operation_completed":
            # Handle operation completed
            operation_id = data.get("operation_id")
            
            if operation_id and operation_id in self.operations:
                # Update operation info
                op = self.operations[operation_id]
                op.status = OperationStatus.COMPLETED
                op.progress = 100.0
                op.last_update_time = time.time()
                
                if "details" in data:
                    if op.details is None:
                        op.details = {}
                    op.details.update(data["details"])
                
                # Notify callbacks
                await self._notify_callbacks("operation_completed", data)
                
        elif message_type == "operation_failed":
            # Handle operation failed
            operation_id = data.get("operation_id")
            
            if operation_id and operation_id in self.operations:
                # Update operation info
                op = self.operations[operation_id]
                op.status = OperationStatus.FAILED
                op.last_update_time = time.time()
                
                if "details" in data:
                    if op.details is None:
                        op.details = {}
                    op.details.update(data["details"])
                
                # Notify callbacks
                await self._notify_callbacks("operation_failed", data)
                
        elif message_type == "operation_canceled":
            # Handle operation canceled
            operation_id = data.get("operation_id")
            
            if operation_id and operation_id in self.operations:
                # Update operation info
                op = self.operations[operation_id]
                op.status = OperationStatus.CANCELED
                op.last_update_time = time.time()
                
                if "details" in data:
                    if op.details is None:
                        op.details = {}
                    op.details.update(data["details"])
                
                # Notify callbacks
                await self._notify_callbacks("operation_canceled", data)
                
        elif message_type == "pong":
            # Handle pong (ping response)
            logger.debug("Received pong from server")
            
        else:
            # Unknown message type
            logger.warning(f"Unknown message type: {message_type}")
    
    async def _notify_callbacks(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Notify callbacks for an event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in {event_type} callback: {e}")
                    logger.debug(traceback.format_exc())
    
    async def _notify_connection_status(self, status: str, details: Dict[str, Any] = None) -> None:
        """
        Notify callbacks about connection status changes.
        
        Args:
            status: Connection status ("connected", "disconnected", "connecting")
            details: Optional details about the status change
        """
        data = {
            "type": "connection_status",
            "status": status,
            "timestamp": time.time()
        }
        
        if details:
            data["details"] = details
            
        await self._notify_callbacks("connection_status", data)
    
    def add_callback(self, event_type: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Add a callback for an event type.
        
        Args:
            event_type: Type of event to listen for
            callback: Function to call when event occurs
        """
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
        else:
            logger.warning(f"Unknown event type: {event_type}")
    
    def remove_callback(self, event_type: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Remove a callback for an event type.
        
        Args:
            event_type: Type of event
            callback: Callback to remove
        """
        if event_type in self.callbacks and callback in self.callbacks[event_type]:
            self.callbacks[event_type].remove(callback)
    
    def get_operations(self) -> Dict[str, OperationInfo]:
        """
        Get all tracked operations.
        
        Returns:
            Dictionary of operation ID to OperationInfo
        """
        return self.operations.copy()
    
    def get_operation(self, operation_id: str) -> Optional[OperationInfo]:
        """
        Get information about an operation.
        
        Args:
            operation_id: ID of the operation
            
        Returns:
            OperationInfo if found, None otherwise
        """
        return self.operations.get(operation_id)
    
    def is_connected(self) -> bool:
        """
        Check if the client is connected to the server.
        
        Returns:
            True if connected, False otherwise
        """
        return self.connected
    
    def send_message(self, message: Dict[str, Any]) -> None:
        """
        Send a message to the WebSocket server.
        
        Args:
            message: Message to send
        """
        if not self.connected or not self.websocket:
            logger.warning("Cannot send message: not connected")
            return
            
        # Send message in event loop
        asyncio.run_coroutine_threadsafe(
            self.websocket.send(json.dumps(message)),
            self.event_loop
        )
    
    def list_operations(self) -> None:
        """Request a list of operations from the server."""
        self.send_message({
            "type": "list_operations",
            "timestamp": time.time()
        })
    
    def cancel_operation(self, operation_id: str) -> None:
        """
        Request cancellation of an operation.
        
        Args:
            operation_id: ID of the operation to cancel
        """
        self.send_message({
            "type": "cancel_operation",
            "operation_id": operation_id,
            "timestamp": time.time()
        })
    
    def get_operation_details(self, operation_id: str) -> None:
        """
        Request detailed information about an operation.
        
        Args:
            operation_id: ID of the operation
        """
        self.send_message({
            "type": "get_operation_details",
            "operation_id": operation_id,
            "timestamp": time.time()
        })


# Global client instance
_client_instance = None


def get_websocket_client(url: str = "ws://localhost:8765") -> WebSocketClient:
    """
    Get the global WebSocket client instance.
    
    Args:
        url: WebSocket server URL
        
    Returns:
        WebSocketClient instance
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = WebSocketClient(url)
    return _client_instance