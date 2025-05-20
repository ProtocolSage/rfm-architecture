"""
Enhanced WebSocket client for real-time progress reporting in RFM Architecture UI.

This module provides a resilient WebSocket client that connects to the progress
reporting server to receive real-time updates during long-running operations.
Features include automatic reconnection, state preservation, and comprehensive
monitoring.
"""

import asyncio
import json
import logging
import threading
import time
import traceback
import websockets
import uuid
import random
from typing import Dict, Any, List, Optional, Callable, Set, Union, Tuple, Deque
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import socket

from rfm.core.logging_config import (
    get_logger, configure_logging, LogLevel, LogCategory, log_timing, TimingContext
)


# Configure logger
logger = get_logger(__name__)


class ConnectionState(str, Enum):
    """WebSocket connection states."""
    
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


class OperationStatus(str, Enum):
    """Status of a tracked operation."""
    
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class MessageType(str, Enum):
    """Types of WebSocket messages."""
    
    # Client messages
    PING = "ping"
    LIST_OPERATIONS = "list_operations"
    CANCEL_OPERATION = "cancel_operation"
    GET_OPERATION_DETAILS = "get_operation_details"
    
    # Server messages
    PONG = "pong"
    OPERATION_STARTED = "operation_started"
    PROGRESS_UPDATE = "progress_update"
    OPERATION_COMPLETED = "operation_completed"
    OPERATION_FAILED = "operation_failed"
    OPERATION_CANCELED = "operation_canceled"
    OPERATIONS_LIST = "operations_list"
    
    # System messages
    CONNECTION_STATUS = "connection_status"
    SERVER_STATUS = "server_status"
    ERROR = "error"


@dataclass
class MessageStats:
    """Statistics for WebSocket messages."""
    
    received_count: int = 0
    sent_count: int = 0
    received_bytes: int = 0
    sent_bytes: int = 0
    errors: int = 0
    last_received_time: Optional[float] = None
    last_sent_time: Optional[float] = None
    message_types: Dict[str, int] = field(default_factory=dict)
    
    def record_received(self, message: Union[str, Dict], message_type: Optional[str] = None) -> None:
        """
        Record a received message.
        
        Args:
            message: Received message
            message_type: Optional message type
        """
        self.received_count += 1
        self.last_received_time = time.time()
        
        # Calculate size
        if isinstance(message, str):
            self.received_bytes += len(message.encode('utf-8'))
        elif isinstance(message, dict):
            self.received_bytes += len(json.dumps(message).encode('utf-8'))
        
        # Record message type
        if message_type:
            if message_type not in self.message_types:
                self.message_types[message_type] = 0
                
            self.message_types[message_type] += 1
    
    def record_sent(self, message: Union[str, Dict], message_type: Optional[str] = None) -> None:
        """
        Record a sent message.
        
        Args:
            message: Sent message
            message_type: Optional message type
        """
        self.sent_count += 1
        self.last_sent_time = time.time()
        
        # Calculate size
        if isinstance(message, str):
            self.sent_bytes += len(message.encode('utf-8'))
        elif isinstance(message, dict):
            self.sent_bytes += len(json.dumps(message).encode('utf-8'))
        
        # Record message type
        if message_type:
            if message_type not in self.message_types:
                self.message_types[message_type] = 0
                
            self.message_types[message_type] += 1
    
    def record_error(self) -> None:
        """Record a message error."""
        self.errors += 1


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
    end_time: Optional[float] = None
    duration: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)
    is_cancellable: bool = True
    
    @property
    def completion_percentage(self) -> float:
        """Get completion percentage."""
        return round(self.progress, 1)
    
    @property
    def elapsed_time(self) -> Optional[float]:
        """Get elapsed time in seconds."""
        if self.start_time:
            if self.end_time:
                return self.end_time - self.start_time
            return time.time() - self.start_time
        return None
    
    @property
    def estimated_completion_time(self) -> Optional[float]:
        """
        Estimate completion time based on progress rate.
        
        Returns:
            Estimated time to completion in seconds, or None if not estimable
        """
        if self.status not in (OperationStatus.PENDING, OperationStatus.RUNNING, OperationStatus.PAUSED):
            return 0
            
        if self.progress <= 0 or self.start_time is None:
            return None
            
        elapsed = time.time() - self.start_time
        progress_per_second = self.progress / (100 * elapsed) if elapsed > 0 else 0
        
        if progress_per_second <= 0:
            return None
            
        remaining_progress = 1.0 - (self.progress / 100)
        estimated_seconds = remaining_progress / progress_per_second
        
        return max(0, estimated_seconds)
    
    @property
    def is_active(self) -> bool:
        """Check if operation is active."""
        return self.status in (OperationStatus.PENDING, OperationStatus.RUNNING, OperationStatus.PAUSED)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OperationInfo':
        """
        Create from dictionary data.
        
        Args:
            data: Operation data
            
        Returns:
            OperationInfo instance
        """
        return cls(
            operation_id=data.get("operation_id", ""),
            operation_type=data.get("operation_type", "unknown"),
            name=data.get("name", "Unknown Operation"),
            status=OperationStatus(data.get("status", "running")),
            progress=data.get("progress", 0),
            current_step=data.get("current_step"),
            total_steps=data.get("total_steps"),
            start_time=data.get("start_time"),
            last_update_time=data.get("last_update_time") or data.get("timestamp"),
            end_time=data.get("end_time"),
            duration=data.get("duration"),
            details=data.get("details", {})
        )


@dataclass
class ReconnectionConfig:
    """Configuration for WebSocket reconnection."""
    
    initial_delay: float = 1.0  # Initial delay in seconds
    max_delay: float = 60.0     # Maximum delay in seconds
    multiplier: float = 1.5     # Multiplier for exponential backoff
    jitter: float = 0.2         # Jitter factor for randomization (0.0 to 1.0)
    max_attempts: int = 0       # Maximum reconnection attempts (0 = infinite)
    
    def get_delay(self, attempt: int) -> float:
        """
        Calculate reconnection delay with exponential backoff and jitter.
        
        Args:
            attempt: Reconnection attempt number (1-based)
            
        Returns:
            Delay in seconds
        """
        # Calculate base delay with exponential backoff
        delay = min(self.initial_delay * (self.multiplier ** (attempt - 1)), self.max_delay)
        
        # Add jitter
        if self.jitter > 0:
            jitter_amount = delay * self.jitter
            delay = delay + random.uniform(-jitter_amount, jitter_amount)
            
        return max(0.1, delay)  # Ensure minimum delay


class WebSocketClient:
    """
    Resilient WebSocket client for receiving progress updates.
    
    Features:
    - Automatic reconnection with exponential backoff
    - Connection state management
    - Message delivery guarantees
    - Operation state preservation across reconnections
    - Comprehensive logging and monitoring
    - Rate limiting and debouncing for high-frequency updates
    """
    
    def __init__(self, 
                url: str = "ws://localhost:8765",
                reconnection_config: Optional[ReconnectionConfig] = None,
                authentication: Optional[Dict[str, str]] = None,
                log_level: LogLevel = LogLevel.INFO,
                debug_mode: bool = False):
        """
        Initialize the WebSocket client.
        
        Args:
            url: WebSocket server URL
            reconnection_config: Optional reconnection configuration
            authentication: Optional authentication parameters (client_id and api_key)
            log_level: Log level for client logs
            debug_mode: Enable debug mode with additional logging
        """
        # Configuration
        self.base_url = url
        self.reconnection_config = reconnection_config or ReconnectionConfig()
        self.authentication = authentication or {}
        self.log_level = log_level
        self.debug_mode = debug_mode
        
        # Create client ID if not provided
        if "client_id" not in self.authentication:
            self.authentication["client_id"] = f"client_{uuid.uuid4().hex[:8]}"
            
        # Build authenticated URL
        self.url = self._build_authenticated_url()
        
        # State
        self.websocket = None
        self.state = ConnectionState.DISCONNECTED
        self.connected = False
        self.connecting = False
        self.reconnect_attempt = 0
        self.last_reconnect_time = 0
        self.connection_error = None
        
        # Message tracking
        self.message_stats = MessageStats()
        self.pending_messages: Deque[Dict[str, Any]] = deque(maxlen=1000)
        self.message_processing_lock = asyncio.Lock()
        
        # Operation tracking
        self.operations: Dict[str, OperationInfo] = {}
        self.operations_to_resurrect: Dict[str, Dict[str, Any]] = {}
        
        # Callbacks
        self.callbacks: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {
            MessageType.PROGRESS_UPDATE: [],
            MessageType.OPERATION_STARTED: [],
            MessageType.OPERATION_COMPLETED: [],
            MessageType.OPERATION_FAILED: [],
            MessageType.OPERATION_CANCELED: [],
            MessageType.OPERATIONS_LIST: [],
            MessageType.CONNECTION_STATUS: [],
            MessageType.ERROR: []
        }
        
        # Async components
        self.receive_task = None
        self.ping_task = None
        self.message_processor_task = None
        self.resurrection_task = None
        self.event_loop = None
        self.thread = None
        
        # State management
        self.started = False
        self._stop_event = asyncio.Event()
        
        # Generate client ID
        self.client_id = str(uuid.uuid4())
        
        logger.structured_log(
            LogLevel.INFO,
            "Initialized WebSocket client",
            LogCategory.CONNECTION,
            component="websocket_client",
            context={
                "url": self.url,
                "client_id": self.client_id,
                "debug_mode": debug_mode
            }
        )
    
    def _build_authenticated_url(self) -> str:
        """
        Build the authenticated WebSocket URL.
        
        Returns:
            Authenticated URL with query parameters
        """
        url = self.base_url
        
        # Add authentication parameters
        if self.authentication:
            # Check if URL already has query parameters
            if "?" in url:
                url += "&"
            else:
                url += "?"
                
            # Add authentication parameters
            for key, value in self.authentication.items():
                url += f"{key}={value}&"
                
            # Remove trailing &
            url = url.rstrip("&")
            
        return url
    
    def start(self) -> None:
        """Start the WebSocket client in a background thread."""
        if self.started:
            logger.structured_log(
                LogLevel.WARNING,
                "WebSocket client already started",
                LogCategory.CONNECTION,
                component="websocket_client",
                context={"client_id": self.client_id}
            )
            return
            
        # Reset stop event
        self._stop_event = asyncio.Event()
        
        # Create new event loop for the thread
        self.event_loop = asyncio.new_event_loop()
        
        # Create and start the thread
        self.thread = threading.Thread(
            target=self._run_event_loop,
            name=f"WebSocketClientThread-{self.client_id[:8]}",
            daemon=True
        )
        self.thread.start()
        self.started = True
        
        # Use standard logging if structured_log isn't available
        if hasattr(logger, 'structured_log'):
            logger.structured_log(
                LogLevel.INFO,
                f"WebSocket client started, connecting to {self.url}",
                LogCategory.CONNECTION,
                component="websocket_client",
                context={"client_id": self.client_id}
            )
        else:
            logger.info(f"WebSocket client started, connecting to {self.url} [client_id={self.client_id}]")
    
    def stop(self) -> None:
        """Stop the WebSocket client."""
        if not self.started:
            return
            
        # Set stop event
        if self.event_loop and self.event_loop.is_running():
            self.event_loop.call_soon_threadsafe(self._stop_event.set)
            
        # Run disconnect in event loop
        if self.event_loop and self.event_loop.is_running():
            asyncio.run_coroutine_threadsafe(self._disconnect(), self.event_loop)
            
        # Give it a moment to disconnect gracefully
        time.sleep(0.5)
        
        # Stop the event loop if still running
        if self.event_loop and self.event_loop.is_running():
            try:
                self.event_loop.call_soon_threadsafe(self.event_loop.stop)
            except Exception as e:
                logger.structured_log(
                    LogLevel.ERROR,
                    f"Error stopping event loop: {e}",
                    LogCategory.CONNECTION,
                    component="websocket_client",
                    context={"client_id": self.client_id},
                    error=str(e)
                )
                
        # Wait for thread to finish
        if self.thread:
            self.thread.join(timeout=1.0)
            
        # Reset state
        self.started = False
        self.connected = False
        self.connecting = False
        self.state = ConnectionState.DISCONNECTED
        
        logger.structured_log(
            LogLevel.INFO,
            "WebSocket client stopped",
            LogCategory.CONNECTION,
            component="websocket_client",
            context={"client_id": self.client_id}
        )
    
    def _run_event_loop(self) -> None:
        """Run the event loop in a thread."""
        asyncio.set_event_loop(self.event_loop)
        
        # Create connect task
        asyncio.ensure_future(self._connect_with_retry())
        
        # Create message processor task
        asyncio.ensure_future(self._process_pending_messages())
        
        # Run the event loop
        try:
            self.event_loop.run_forever()
        except Exception as e:
            logger.structured_log(
                LogLevel.ERROR,
                f"Error in WebSocket client event loop: {e}",
                LogCategory.CONNECTION,
                component="websocket_client",
                context={"client_id": self.client_id},
                error=str(e)
            )
            
            # Log traceback in debug mode
            if self.debug_mode:
                logger.structured_log(
                    LogLevel.DEBUG,
                    traceback.format_exc(),
                    LogCategory.CONNECTION,
                    component="websocket_client",
                    context={"client_id": self.client_id}
                )
                
        finally:
            # Clean up
            for task in asyncio.all_tasks(self.event_loop):
                task.cancel()
                
            self.event_loop.run_until_complete(asyncio.sleep(0.1))
            self.event_loop.close()
            
            logger.structured_log(
                LogLevel.DEBUG,
                "WebSocket client event loop stopped",
                LogCategory.CONNECTION,
                component="websocket_client",
                context={"client_id": self.client_id}
            )
    
    async def _connect_with_retry(self) -> None:
        """Connect to the WebSocket server with retry."""
        while not self._stop_event.is_set():
            if self.connected or self.connecting:
                await asyncio.sleep(0.1)
                continue
                
            try:
                self.connecting = True
                self.state = ConnectionState.CONNECTING
                
                # Notify about connection attempt
                await self._notify_connection_status(ConnectionState.CONNECTING)
                
                # Calculate reconnection delay if this is a retry
                if self.reconnect_attempt > 0:
                    delay = self.reconnection_config.get_delay(self.reconnect_attempt)
                    
                    logger.structured_log(
                        LogLevel.INFO,
                        f"Reconnection attempt {self.reconnect_attempt}, waiting {delay:.1f}s",
                        LogCategory.CONNECTION,
                        component="websocket_client",
                        context={
                            "client_id": self.client_id,
                            "reconnect_attempt": self.reconnect_attempt,
                            "delay": delay
                        }
                    )
                    
                    # Wait before reconnecting
                    await asyncio.sleep(delay)
                    
                    # Check if we should stop
                    if self._stop_event.is_set():
                        break
                    
                # Connect to the server
                logger.structured_log(
                    LogLevel.DEBUG,
                    f"Connecting to WebSocket server at {self.url}",
                    LogCategory.CONNECTION,
                    component="websocket_client",
                    context={"client_id": self.client_id}
                )
                
                # Set connection timeout
                try:
                    self.websocket = await asyncio.wait_for(
                        websockets.connect(self.url, close_timeout=2.0),
                        timeout=10.0  # 10 second connection timeout
                    )
                    self.connected = True
                    self.connecting = False
                    self.state = ConnectionState.CONNECTED
                    self.reconnect_attempt = 0  # Reset reconnect attempt on success
                    self.connection_error = None
                    
                    # Notify about connection
                    await self._notify_connection_status(ConnectionState.CONNECTED)
                    
                    logger.structured_log(
                        LogLevel.INFO,
                        f"Connected to WebSocket server at {self.url}",
                        LogCategory.CONNECTION,
                        component="websocket_client",
                        context={"client_id": self.client_id}
                    )
                    
                    # Start receive task
                    self.receive_task = asyncio.create_task(self._receive_messages())
                    
                    # Start ping task
                    self.ping_task = asyncio.create_task(self._send_pings())
                    
                    # Start resurrection task if needed
                    if self.operations_to_resurrect:
                        self.resurrection_task = asyncio.create_task(self._resurrect_operations())
                    
                    # Wait for disconnect
                    await self.receive_task
                    
                except asyncio.TimeoutError:
                    # Connection timeout
                    self.connecting = False
                    self.connection_error = "Connection timeout"
                    
                    logger.structured_log(
                        LogLevel.WARNING,
                        "Connection timeout",
                        LogCategory.CONNECTION,
                        component="websocket_client",
                        context={"client_id": self.client_id}
                    )
                    
                    # Update reconnection attempt
                    self.reconnect_attempt += 1
                
            except websockets.exceptions.InvalidStatusCode as e:
                # Server rejected the connection
                self.connected = False
                self.connecting = False
                self.state = ConnectionState.ERROR
                self.connection_error = f"Server rejected connection: {e.status_code}"
                
                # Notify about connection error
                await self._notify_connection_status(
                    ConnectionState.ERROR,
                    {"error": self.connection_error, "status_code": e.status_code}
                )
                
                logger.structured_log(
                    LogLevel.ERROR,
                    f"Server rejected connection: {e.status_code}",
                    LogCategory.CONNECTION,
                    component="websocket_client",
                    context={"client_id": self.client_id, "status_code": e.status_code},
                    error=str(e)
                )
                
                # Update reconnection attempt
                self.reconnect_attempt += 1
                
                # Check max attempts
                if self.reconnection_config.max_attempts > 0 and self.reconnect_attempt > self.reconnection_config.max_attempts:
                    logger.structured_log(
                        LogLevel.ERROR,
                        f"Maximum reconnection attempts reached ({self.reconnection_config.max_attempts})",
                        LogCategory.CONNECTION,
                        component="websocket_client",
                        context={"client_id": self.client_id}
                    )
                    
                    break
                
            except Exception as e:
                # Connection error
                self.connected = False
                self.connecting = False
                self.state = ConnectionState.ERROR
                self.connection_error = str(e)
                
                # Notify about connection error
                await self._notify_connection_status(ConnectionState.ERROR, {"error": str(e)})
                
                # Handle specific connection errors
                if isinstance(e, (websockets.exceptions.InvalidURI, ValueError)):
                    # Invalid URL - don't retry
                    logger.structured_log(
                        LogLevel.ERROR,
                        f"Invalid WebSocket URL: {self.url}",
                        LogCategory.CONNECTION,
                        component="websocket_client",
                        context={"client_id": self.client_id},
                        error=str(e)
                    )
                    
                    break
                    
                elif isinstance(e, (ConnectionRefusedError, socket.gaierror)):
                    # Server unreachable - retry with backoff
                    logger.structured_log(
                        LogLevel.WARNING,
                        f"Server unreachable: {e}",
                        LogCategory.CONNECTION,
                        component="websocket_client",
                        context={"client_id": self.client_id},
                        error=str(e)
                    )
                    
                else:
                    # Other connection error
                    logger.structured_log(
                        LogLevel.ERROR,
                        f"Connection error: {e}",
                        LogCategory.CONNECTION,
                        component="websocket_client",
                        context={"client_id": self.client_id},
                        error=str(e)
                    )
                    
                    # Log traceback in debug mode
                    if self.debug_mode:
                        logger.structured_log(
                            LogLevel.DEBUG,
                            traceback.format_exc(),
                            LogCategory.CONNECTION,
                            component="websocket_client",
                            context={"client_id": self.client_id}
                        )
                
                # Update reconnection attempt
                self.reconnect_attempt += 1
                
                # Check max attempts
                if self.reconnection_config.max_attempts > 0 and self.reconnect_attempt > self.reconnection_config.max_attempts:
                    logger.structured_log(
                        LogLevel.ERROR,
                        f"Maximum reconnection attempts reached ({self.reconnection_config.max_attempts})",
                        LogCategory.CONNECTION,
                        component="websocket_client",
                        context={"client_id": self.client_id}
                    )
                    
                    break
    
    async def _disconnect(self) -> None:
        """Disconnect from the WebSocket server."""
        if not self.connected and not self.connecting:
            return
            
        # Save active operations for resurrection
        self._save_operations_for_resurrection()
            
        # Cancel tasks
        if self.receive_task:
            self.receive_task.cancel()
            self.receive_task = None
            
        if self.ping_task:
            self.ping_task.cancel()
            self.ping_task = None
            
        if self.resurrection_task:
            self.resurrection_task.cancel()
            self.resurrection_task = None
            
        # Close websocket
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.structured_log(
                    LogLevel.DEBUG,
                    f"Error closing WebSocket: {e}",
                    LogCategory.CONNECTION,
                    component="websocket_client",
                    context={"client_id": self.client_id},
                    error=str(e)
                )
                
            self.websocket = None
            
        # Update state
        self.connected = False
        self.connecting = False
        self.state = ConnectionState.DISCONNECTED
        
        # Notify about disconnection
        await self._notify_connection_status(ConnectionState.DISCONNECTED)
        
        logger.structured_log(
            LogLevel.INFO,
            "Disconnected from WebSocket server",
            LogCategory.CONNECTION,
            component="websocket_client",
            context={"client_id": self.client_id}
        )
    
    async def _receive_messages(self) -> None:
        """Receive and handle messages from the WebSocket server."""
        if not self.connected or not self.websocket:
            return
            
        try:
            async for message in self.websocket:
                try:
                    # Parse message
                    try:
                        data = json.loads(message)
                        
                        # Update message stats
                        self.message_stats.record_received(message, data.get("type"))
                        
                        # Handle message
                        await self._handle_message(data)
                        
                    except json.JSONDecodeError:
                        # Invalid JSON
                        logger.structured_log(
                            LogLevel.WARNING,
                            f"Invalid JSON from server: {message}",
                            LogCategory.CONNECTION,
                            component="websocket_client",
                            context={"client_id": self.client_id}
                        )
                        
                        # Update message stats
                        self.message_stats.record_error()
                        
                except Exception as e:
                    # Error handling message
                    logger.structured_log(
                        LogLevel.ERROR,
                        f"Error handling message: {e}",
                        LogCategory.CONNECTION,
                        component="websocket_client",
                        context={"client_id": self.client_id},
                        error=str(e)
                    )
                    
                    # Log traceback in debug mode
                    if self.debug_mode:
                        logger.structured_log(
                            LogLevel.DEBUG,
                            traceback.format_exc(),
                            LogCategory.CONNECTION,
                            component="websocket_client",
                            context={"client_id": self.client_id}
                        )
                        
                    # Update message stats
                    self.message_stats.record_error()
                    
        except asyncio.CancelledError:
            # Task canceled, exit
            pass
        except websockets.exceptions.ConnectionClosed as e:
            # Connection closed
            logger.structured_log(
                LogLevel.WARNING,
                f"WebSocket connection closed: {e}",
                LogCategory.CONNECTION,
                component="websocket_client",
                context={"client_id": self.client_id, "code": e.code, "reason": e.reason},
                error=str(e)
            )
            
        except Exception as e:
            # Unexpected error
            logger.structured_log(
                LogLevel.ERROR,
                f"Error in WebSocket receive loop: {e}",
                LogCategory.CONNECTION,
                component="websocket_client",
                context={"client_id": self.client_id},
                error=str(e)
            )
            
            # Log traceback in debug mode
            if self.debug_mode:
                logger.structured_log(
                    LogLevel.DEBUG,
                    traceback.format_exc(),
                    LogCategory.CONNECTION,
                    component="websocket_client",
                    context={"client_id": self.client_id}
                )
            
        finally:
            # Mark as disconnected
            self.connected = False
            self.state = ConnectionState.DISCONNECTED
            
            # Notify about disconnection
            await self._notify_connection_status(ConnectionState.DISCONNECTED)
    
    async def _send_pings(self) -> None:
        """Send periodic ping messages to keep the connection alive."""
        if not self.connected or not self.websocket:
            return
            
        try:
            while self.connected:
                # Wait before sending ping
                await asyncio.sleep(30)  # Send ping every 30 seconds
                
                # Check if still connected
                if not self.connected:
                    break
                    
                # Send ping
                try:
                    await self.send_message({
                        "type": MessageType.PING,
                        "timestamp": time.time()
                    })
                    
                    logger.structured_log(
                        LogLevel.DEBUG,
                        "Sent ping message",
                        LogCategory.CONNECTION,
                        component="websocket_client",
                        context={"client_id": self.client_id}
                    )
                    
                except Exception as e:
                    logger.structured_log(
                        LogLevel.WARNING,
                        f"Error sending ping: {e}",
                        LogCategory.CONNECTION,
                        component="websocket_client",
                        context={"client_id": self.client_id},
                        error=str(e)
                    )
                    
                    break
                    
        except asyncio.CancelledError:
            # Task canceled, exit
            pass
        except Exception as e:
            # Unexpected error
            logger.structured_log(
                LogLevel.ERROR,
                f"Error in ping task: {e}",
                LogCategory.CONNECTION,
                component="websocket_client",
                context={"client_id": self.client_id},
                error=str(e)
            )
            
            # Log traceback in debug mode
            if self.debug_mode:
                logger.structured_log(
                    LogLevel.DEBUG,
                    traceback.format_exc(),
                    LogCategory.CONNECTION,
                    component="websocket_client",
                    context={"client_id": self.client_id}
                )
                
        finally:
            # Mark as disconnected if ping fails
            self.connected = False
    
    async def _handle_message(self, data: Dict[str, Any]) -> None:
        """
        Handle a message from the WebSocket server.
        
        Args:
            data: Message data
        """
        message_type = data.get("type")
        
        if not message_type:
            logger.structured_log(
                LogLevel.WARNING,
                "Received message without type",
                LogCategory.CONNECTION,
                component="websocket_client",
                context={"client_id": self.client_id, "message": data}
            )
            return
            
        # Handle system messages
        if message_type == MessageType.PONG:
            # Pong response
            client_timestamp = data.get("client_timestamp")
            server_timestamp = data.get("timestamp")
            
            if client_timestamp and server_timestamp:
                # Calculate round-trip time
                rtt = (time.time() - client_timestamp) * 1000  # ms
                
                logger.structured_log(
                    LogLevel.DEBUG,
                    f"Received pong (RTT: {rtt:.2f} ms)",
                    LogCategory.CONNECTION,
                    component="websocket_client",
                    context={"client_id": self.client_id, "rtt_ms": rtt}
                )
            else:
                logger.structured_log(
                    LogLevel.DEBUG,
                    "Received pong from server",
                    LogCategory.CONNECTION,
                    component="websocket_client",
                    context={"client_id": self.client_id}
                )
        
        elif message_type == MessageType.ERROR:
            # Error message
            error_code = data.get("error_code", "unknown")
            error_message = data.get("error_message", "Unknown error")
            
            logger.structured_log(
                LogLevel.WARNING,
                f"Received error from server: {error_code} - {error_message}",
                LogCategory.CONNECTION,
                component="websocket_client",
                context={
                    "client_id": self.client_id,
                    "error_code": error_code,
                    "error_message": error_message
                }
            )
            
            # Notify error callbacks
            await self._notify_callbacks(MessageType.ERROR, data)
            
        # Handle operation messages
        elif message_type == MessageType.PROGRESS_UPDATE:
            # Handle progress update
            await self._handle_progress_update(data)
            
        elif message_type == MessageType.OPERATION_STARTED:
            # Handle operation started
            await self._handle_operation_started(data)
            
        elif message_type == MessageType.OPERATION_COMPLETED:
            # Handle operation completed
            await self._handle_operation_completed(data)
            
        elif message_type == MessageType.OPERATION_FAILED:
            # Handle operation failed
            await self._handle_operation_failed(data)
            
        elif message_type == MessageType.OPERATION_CANCELED:
            # Handle operation canceled
            await self._handle_operation_canceled(data)
            
        elif message_type == MessageType.OPERATIONS_LIST:
            # Handle operations list
            await self._handle_operations_list(data)
            
        else:
            # Unknown message type
            logger.structured_log(
                LogLevel.WARNING,
                f"Unknown message type: {message_type}",
                LogCategory.CONNECTION,
                component="websocket_client",
                context={"client_id": self.client_id, "message_type": message_type}
            )
    
    async def _handle_progress_update(self, data: Dict[str, Any]) -> None:
        """
        Handle progress update message.
        
        Args:
            data: Message data
        """
        update_data = data.get("data", {})
        operation_id = update_data.get("operation_id")
        
        if not operation_id:
            logger.structured_log(
                LogLevel.WARNING,
                "Received progress update without operation_id",
                LogCategory.OPERATION,
                component="websocket_client",
                context={"client_id": self.client_id}
            )
            return
            
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
                
        # Log significant progress updates
        progress = update_data.get("progress", 0)
        if progress % 25 == 0 or progress == 100:  # Log at 0%, 25%, 50%, 75%, 100%
            logger.structured_log(
                LogLevel.DEBUG,
                f"Operation progress: {operation_id} - {progress}%",
                LogCategory.OPERATION,
                operation_id=operation_id,
                component="websocket_client",
                context={
                    "client_id": self.client_id,
                    "operation_id": operation_id,
                    "progress": progress,
                    "current_step": update_data.get("current_step")
                }
            )
                
        # Notify callbacks
        await self._notify_callbacks(MessageType.PROGRESS_UPDATE, data)
    
    async def _handle_operation_started(self, data: Dict[str, Any]) -> None:
        """
        Handle operation started message.
        
        Args:
            data: Message data
        """
        operation_data = data.get("operation", {})
        operation_id = operation_data.get("operation_id")
        
        if not operation_id:
            logger.structured_log(
                LogLevel.WARNING,
                "Received operation started without operation_id",
                LogCategory.OPERATION,
                component="websocket_client",
                context={"client_id": self.client_id}
            )
            return
            
        # Create operation info
        self.operations[operation_id] = OperationInfo(
            operation_id=operation_id,
            operation_type=operation_data.get("operation_type", "unknown"),
            name=operation_data.get("name", f"Operation {operation_id}"),
            status=OperationStatus.PENDING,
            progress=0.0,
            start_time=time.time(),
            last_update_time=time.time(),
            details=operation_data.get("details", {})
        )
        
        # Log operation started
        logger.structured_log(
            LogLevel.INFO,
            f"Operation started: {operation_id} - {operation_data.get('name', 'Unknown')}",
            LogCategory.OPERATION,
            operation_id=operation_id,
            component="websocket_client",
            context={
                "client_id": self.client_id,
                "operation_id": operation_id,
                "operation_type": operation_data.get("operation_type"),
                "operation_name": operation_data.get("name")
            }
        )
        
        # Remove from resurrection list if present
        if operation_id in self.operations_to_resurrect:
            del self.operations_to_resurrect[operation_id]
            
        # Notify callbacks
        await self._notify_callbacks(MessageType.OPERATION_STARTED, data)
    
    async def _handle_operation_completed(self, data: Dict[str, Any]) -> None:
        """
        Handle operation completed message.
        
        Args:
            data: Message data
        """
        operation_id = data.get("operation_id")
        
        if not operation_id:
            logger.structured_log(
                LogLevel.WARNING,
                "Received operation completed without operation_id",
                LogCategory.OPERATION,
                component="websocket_client",
                context={"client_id": self.client_id}
            )
            return
            
        # Check if operation exists
        if operation_id not in self.operations:
            logger.structured_log(
                LogLevel.WARNING,
                f"Operation completed for unknown operation: {operation_id}",
                LogCategory.OPERATION,
                component="websocket_client",
                context={"client_id": self.client_id, "operation_id": operation_id}
            )
            
            # Create placeholder operation
            self.operations[operation_id] = OperationInfo(
                operation_id=operation_id,
                operation_type="unknown",
                name=f"Operation {operation_id}",
                status=OperationStatus.COMPLETED,
                progress=100.0,
                start_time=time.time() - 1,  # 1 second ago
                last_update_time=time.time(),
                end_time=time.time(),
                details={}
            )
            
        # Update operation info
        op = self.operations[operation_id]
        op.status = OperationStatus.COMPLETED
        op.progress = 100.0
        op.last_update_time = time.time()
        op.end_time = time.time()
        
        # Calculate duration
        if op.start_time:
            op.duration = op.end_time - op.start_time
            
        # Update details
        if "details" in data:
            if not op.details:
                op.details = {}
            op.details.update(data["details"])
            
        # Log operation completed
        logger.structured_log(
            LogLevel.INFO,
            f"Operation completed: {operation_id}",
            LogCategory.OPERATION,
            operation_id=operation_id,
            component="websocket_client",
            context={
                "client_id": self.client_id,
                "operation_id": operation_id,
                "duration": op.duration
            }
        )
        
        # Remove from resurrection list if present
        if operation_id in self.operations_to_resurrect:
            del self.operations_to_resurrect[operation_id]
            
        # Notify callbacks
        await self._notify_callbacks(MessageType.OPERATION_COMPLETED, data)
    
    async def _handle_operation_failed(self, data: Dict[str, Any]) -> None:
        """
        Handle operation failed message.
        
        Args:
            data: Message data
        """
        operation_id = data.get("operation_id")
        
        if not operation_id:
            logger.structured_log(
                LogLevel.WARNING,
                "Received operation failed without operation_id",
                LogCategory.OPERATION,
                component="websocket_client",
                context={"client_id": self.client_id}
            )
            return
            
        # Check if operation exists
        if operation_id not in self.operations:
            logger.structured_log(
                LogLevel.WARNING,
                f"Operation failed for unknown operation: {operation_id}",
                LogCategory.OPERATION,
                component="websocket_client",
                context={"client_id": self.client_id, "operation_id": operation_id}
            )
            
            # Create placeholder operation
            self.operations[operation_id] = OperationInfo(
                operation_id=operation_id,
                operation_type="unknown",
                name=f"Operation {operation_id}",
                status=OperationStatus.FAILED,
                progress=0.0,
                start_time=time.time() - 1,  # 1 second ago
                last_update_time=time.time(),
                end_time=time.time(),
                details={}
            )
            
        # Update operation info
        op = self.operations[operation_id]
        op.status = OperationStatus.FAILED
        op.last_update_time = time.time()
        op.end_time = time.time()
        
        # Calculate duration
        if op.start_time:
            op.duration = op.end_time - op.start_time
            
        # Update details
        if "details" in data:
            if not op.details:
                op.details = {}
            op.details.update(data["details"])
            
        # Get error message
        error_message = op.details.get("error_message", "Unknown error")
            
        # Log operation failed
        logger.structured_log(
            LogLevel.ERROR,
            f"Operation failed: {operation_id} - {error_message}",
            LogCategory.OPERATION,
            operation_id=operation_id,
            component="websocket_client",
            context={
                "client_id": self.client_id,
                "operation_id": operation_id,
                "error_message": error_message,
                "duration": op.duration
            }
        )
        
        # Remove from resurrection list if present
        if operation_id in self.operations_to_resurrect:
            del self.operations_to_resurrect[operation_id]
            
        # Notify callbacks
        await self._notify_callbacks(MessageType.OPERATION_FAILED, data)
    
    async def _handle_operation_canceled(self, data: Dict[str, Any]) -> None:
        """
        Handle operation canceled message.
        
        Args:
            data: Message data
        """
        operation_id = data.get("operation_id")
        
        if not operation_id:
            logger.structured_log(
                LogLevel.WARNING,
                "Received operation canceled without operation_id",
                LogCategory.OPERATION,
                component="websocket_client",
                context={"client_id": self.client_id}
            )
            return
            
        # Check if operation exists
        if operation_id not in self.operations:
            logger.structured_log(
                LogLevel.WARNING,
                f"Operation canceled for unknown operation: {operation_id}",
                LogCategory.OPERATION,
                component="websocket_client",
                context={"client_id": self.client_id, "operation_id": operation_id}
            )
            
            # Create placeholder operation
            self.operations[operation_id] = OperationInfo(
                operation_id=operation_id,
                operation_type="unknown",
                name=f"Operation {operation_id}",
                status=OperationStatus.CANCELED,
                progress=0.0,
                start_time=time.time() - 1,  # 1 second ago
                last_update_time=time.time(),
                end_time=time.time(),
                details={}
            )
            
        # Update operation info
        op = self.operations[operation_id]
        op.status = OperationStatus.CANCELED
        op.last_update_time = time.time()
        op.end_time = time.time()
        
        # Calculate duration
        if op.start_time:
            op.duration = op.end_time - op.start_time
            
        # Update details
        if "details" in data:
            if not op.details:
                op.details = {}
            op.details.update(data["details"])
            
        # Log operation canceled
        logger.structured_log(
            LogLevel.INFO,
            f"Operation canceled: {operation_id}",
            LogCategory.OPERATION,
            operation_id=operation_id,
            component="websocket_client",
            context={
                "client_id": self.client_id,
                "operation_id": operation_id,
                "duration": op.duration
            }
        )
        
        # Remove from resurrection list if present
        if operation_id in self.operations_to_resurrect:
            del self.operations_to_resurrect[operation_id]
            
        # Notify callbacks
        await self._notify_callbacks(MessageType.OPERATION_CANCELED, data)
    
    async def _handle_operations_list(self, data: Dict[str, Any]) -> None:
        """
        Handle operations list message.
        
        Args:
            data: Message data
        """
        operations_data = data.get("operations", [])
        
        # Process each operation
        for op_data in operations_data:
            operation_id = op_data.get("operation_id")
            
            if not operation_id:
                continue
                
            # Check if operation exists
            if operation_id in self.operations:
                # Update existing operation
                op = self.operations[operation_id]
                op.status = OperationStatus(op_data.get("status", op.status))
                op.progress = op_data.get("progress", op.progress)
                
                if "last_update_time" in op_data:
                    op.last_update_time = op_data["last_update_time"]
                    
                if "end_time" in op_data:
                    op.end_time = op_data["end_time"]
                    
                if "duration" in op_data:
                    op.duration = op_data["duration"]
                    
                # Update details
                if "details" in op_data:
                    if not op.details:
                        op.details = {}
                    op.details.update(op_data["details"])
                    
            else:
                # Create new operation
                self.operations[operation_id] = OperationInfo.from_dict(op_data)
                
                # Log new operation
                logger.structured_log(
                    LogLevel.DEBUG,
                    f"New operation from list: {operation_id}",
                    LogCategory.OPERATION,
                    operation_id=operation_id,
                    component="websocket_client",
                    context={
                        "client_id": self.client_id,
                        "operation_id": operation_id,
                        "operation_type": op_data.get("operation_type"),
                        "operation_name": op_data.get("name")
                    }
                )
                
        # Log operations list
        logger.structured_log(
            LogLevel.DEBUG,
            f"Received operations list: {len(operations_data)} operations",
            LogCategory.OPERATION,
            component="websocket_client",
            context={
                "client_id": self.client_id,
                "operation_count": len(operations_data)
            }
        )
        
        # Notify callbacks
        await self._notify_callbacks(MessageType.OPERATIONS_LIST, data)
    
    async def _notify_connection_status(self, 
                                     status: ConnectionState, 
                                     details: Optional[Dict[str, Any]] = None) -> None:
        """
        Notify callbacks about connection status changes.
        
        Args:
            status: Connection status
            details: Optional details about the status change
        """
        # Create message
        data = {
            "type": MessageType.CONNECTION_STATUS,
            "status": status,
            "timestamp": time.time()
        }
        
        if details:
            data["details"] = details
            
        # Notify callbacks
        await self._notify_callbacks(MessageType.CONNECTION_STATUS, data)
    
    async def _notify_callbacks(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Notify callbacks for an event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        if event_type not in self.callbacks:
            return
            
        # Get callbacks
        callbacks = self.callbacks[event_type].copy()
        
        # Notify callbacks
        for callback in callbacks:
            try:
                # Call callback
                callback(data)
            except Exception as e:
                logger.structured_log(
                    LogLevel.ERROR,
                    f"Error in {event_type} callback: {e}",
                    LogCategory.CONNECTION,
                    component="websocket_client",
                    context={"client_id": self.client_id, "event_type": event_type},
                    error=str(e)
                )
                
                # Log traceback in debug mode
                if self.debug_mode:
                    logger.structured_log(
                        LogLevel.DEBUG,
                        traceback.format_exc(),
                        LogCategory.CONNECTION,
                        component="websocket_client",
                        context={"client_id": self.client_id}
                    )
    
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """
        Send a message to the WebSocket server.
        
        Args:
            message: Message to send
            
        Returns:
            True if message was sent or queued, False if failed
        """
        if not self.connected and not self.connecting:
            # Queue message if not connected
            if len(self.pending_messages) < self.pending_messages.maxlen:
                self.pending_messages.append(message)
                
                logger.structured_log(
                    LogLevel.DEBUG,
                    f"Queued message while disconnected: {message.get('type')}",
                    LogCategory.CONNECTION,
                    component="websocket_client",
                    context={
                        "client_id": self.client_id,
                        "message_type": message.get("type"),
                        "queue_size": len(self.pending_messages)
                    }
                )
                
                return True
            else:
                logger.structured_log(
                    LogLevel.WARNING,
                    "Message queue full, dropping message",
                    LogCategory.CONNECTION,
                    component="websocket_client",
                    context={
                        "client_id": self.client_id,
                        "message_type": message.get("type")
                    }
                )
                
                return False
                
        if not self.websocket:
            logger.structured_log(
                LogLevel.WARNING,
                "Cannot send message: no websocket",
                LogCategory.CONNECTION,
                component="websocket_client",
                context={
                    "client_id": self.client_id,
                    "message_type": message.get("type")
                }
            )
            
            return False
            
        try:
            # Serialize message
            message_json = json.dumps(message)
            
            # Send message
            await self.websocket.send(message_json)
            
            # Update message stats
            self.message_stats.record_sent(message, message.get("type"))
            
            # Log message (debug only)
            logger.structured_log(
                LogLevel.DEBUG,
                f"Sent message: {message.get('type')}",
                LogCategory.CONNECTION,
                component="websocket_client",
                context={
                    "client_id": self.client_id,
                    "message_type": message.get("type")
                }
            )
            
            return True
            
        except websockets.exceptions.ConnectionClosed:
            # Connection closed
            logger.structured_log(
                LogLevel.WARNING,
                "Cannot send message: connection closed",
                LogCategory.CONNECTION,
                component="websocket_client",
                context={
                    "client_id": self.client_id,
                    "message_type": message.get("type")
                }
            )
            
            # Queue message
            if len(self.pending_messages) < self.pending_messages.maxlen:
                self.pending_messages.append(message)
                
                logger.structured_log(
                    LogLevel.DEBUG,
                    f"Queued message after connection closed: {message.get('type')}",
                    LogCategory.CONNECTION,
                    component="websocket_client",
                    context={
                        "client_id": self.client_id,
                        "message_type": message.get("type"),
                        "queue_size": len(self.pending_messages)
                    }
                )
                
                return True
                
            return False
            
        except Exception as e:
            # Error sending message
            logger.structured_log(
                LogLevel.ERROR,
                f"Error sending message: {e}",
                LogCategory.CONNECTION,
                component="websocket_client",
                context={
                    "client_id": self.client_id,
                    "message_type": message.get("type")
                },
                error=str(e)
            )
            
            # Update message stats
            self.message_stats.record_error()
            
            return False
    
    async def _process_pending_messages(self) -> None:
        """Process pending messages."""
        while not self._stop_event.is_set():
            try:
                # Wait for connection
                if not self.connected:
                    await asyncio.sleep(0.5)
                    continue
                    
                # Wait for lock
                async with self.message_processing_lock:
                    # Process pending messages
                    while self.pending_messages:
                        # Get message
                        message = self.pending_messages.popleft()
                        
                        # Send message
                        await self.send_message(message)
                        
                        # Pause briefly to avoid flooding
                        await asyncio.sleep(0.05)
                
                # Wait before next check
                await asyncio.sleep(0.5)
                
            except asyncio.CancelledError:
                # Task canceled
                break
            except Exception as e:
                # Error processing messages
                logger.structured_log(
                    LogLevel.ERROR,
                    f"Error processing pending messages: {e}",
                    LogCategory.CONNECTION,
                    component="websocket_client",
                    context={"client_id": self.client_id},
                    error=str(e)
                )
                
                # Pause before retry
                await asyncio.sleep(1.0)
    
    def _save_operations_for_resurrection(self) -> None:
        """Save active operations for resurrection after reconnection."""
        # Find active operations
        active_operations = {
            op_id: op for op_id, op in self.operations.items()
            if op.status in (OperationStatus.PENDING, OperationStatus.RUNNING, OperationStatus.PAUSED)
        }
        
        # Save for resurrection
        self.operations_to_resurrect.update({
            op_id: {
                "operation_id": op.operation_id,
                "operation_type": op.operation_type,
                "name": op.name,
                "status": op.status,
                "progress": op.progress,
                "current_step": op.current_step,
                "total_steps": op.total_steps,
                "start_time": op.start_time,
                "last_update_time": op.last_update_time,
                "details": op.details
            } for op_id, op in active_operations.items()
        })
        
        # Log resurrection info
        if self.operations_to_resurrect:
            logger.structured_log(
                LogLevel.INFO,
                f"Saved {len(self.operations_to_resurrect)} operations for resurrection",
                LogCategory.OPERATION,
                component="websocket_client",
                context={
                    "client_id": self.client_id,
                    "operation_count": len(self.operations_to_resurrect)
                }
            )
    
    async def _resurrect_operations(self) -> None:
        """Resurrect operations after reconnection."""
        if not self.operations_to_resurrect:
            return
            
        # Wait for connection
        for _ in range(10):  # Wait up to 5 seconds
            if self.connected:
                break
            await asyncio.sleep(0.5)
            
        if not self.connected:
            logger.structured_log(
                LogLevel.WARNING,
                "Cannot resurrect operations: not connected",
                LogCategory.OPERATION,
                component="websocket_client",
                context={"client_id": self.client_id}
            )
            return
            
        # Log resurrection start
        logger.structured_log(
            LogLevel.INFO,
            f"Resurrecting {len(self.operations_to_resurrect)} operations",
            LogCategory.OPERATION,
            component="websocket_client",
            context={
                "client_id": self.client_id,
                "operation_count": len(self.operations_to_resurrect)
            }
        )
        
        # Copy operations to resurrect
        operations_to_resurrect = self.operations_to_resurrect.copy()
        
        # Resurrect operations
        for op_id, op_data in operations_to_resurrect.items():
            # Skip if operation already exists or has been processed
            if op_id not in self.operations_to_resurrect:
                continue
                
            # Create operation message
            message = {
                "type": MessageType.OPERATION_STARTED,
                "operation": op_data,
                "timestamp": time.time()
            }
            
            # Send message
            await self.send_message(message)
            
            # Remove from resurrection list
            del self.operations_to_resurrect[op_id]
            
            # Pause briefly to avoid flooding
            await asyncio.sleep(0.1)
    
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
            logger.structured_log(
                LogLevel.WARNING,
                f"Unknown event type: {event_type}",
                LogCategory.CONNECTION,
                component="websocket_client",
                context={"client_id": self.client_id}
            )
    
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
    
    def get_active_operations(self) -> Dict[str, OperationInfo]:
        """
        Get active operations.
        
        Returns:
            Dictionary of operation ID to OperationInfo for active operations
        """
        return {
            op_id: op for op_id, op in self.operations.items()
            if op.status in (OperationStatus.PENDING, OperationStatus.RUNNING, OperationStatus.PAUSED)
        }
    
    def is_connected(self) -> bool:
        """
        Check if the client is connected to the server.
        
        Returns:
            True if connected, False otherwise
        """
        return self.connected
    
    def get_connection_state(self) -> ConnectionState:
        """
        Get the current connection state.
        
        Returns:
            Connection state
        """
        return self.state
    
    def get_message_stats(self) -> MessageStats:
        """
        Get message statistics.
        
        Returns:
            Message statistics
        """
        return self.message_stats
    
    def list_operations(self) -> None:
        """Request a list of operations from the server."""
        if self.event_loop and self.event_loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.send_message({
                    "type": MessageType.LIST_OPERATIONS,
                    "timestamp": time.time()
                }),
                self.event_loop
            )
        else:
            logger.structured_log(
                LogLevel.WARNING,
                "Cannot list operations: event loop not running",
                LogCategory.CONNECTION,
                component="websocket_client",
                context={"client_id": self.client_id}
            )
    
    def cancel_operation(self, operation_id: str) -> None:
        """
        Request cancellation of an operation.
        
        Args:
            operation_id: ID of the operation to cancel
        """
        if self.event_loop and self.event_loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.send_message({
                    "type": MessageType.CANCEL_OPERATION,
                    "operation_id": operation_id,
                    "timestamp": time.time()
                }),
                self.event_loop
            )
            
            # Log cancellation request
            logger.structured_log(
                LogLevel.INFO,
                f"Requesting cancellation of operation {operation_id}",
                LogCategory.OPERATION,
                operation_id=operation_id,
                component="websocket_client",
                context={
                    "client_id": self.client_id,
                    "operation_id": operation_id
                }
            )
        else:
            logger.structured_log(
                LogLevel.WARNING,
                "Cannot cancel operation: event loop not running",
                LogCategory.CONNECTION,
                component="websocket_client",
                context={"client_id": self.client_id, "operation_id": operation_id}
            )
    
    def get_operation_details(self, operation_id: str) -> None:
        """
        Request detailed information about an operation.
        
        Args:
            operation_id: ID of the operation
        """
        if self.event_loop and self.event_loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.send_message({
                    "type": MessageType.GET_OPERATION_DETAILS,
                    "operation_id": operation_id,
                    "timestamp": time.time()
                }),
                self.event_loop
            )
        else:
            logger.structured_log(
                LogLevel.WARNING,
                "Cannot get operation details: event loop not running",
                LogCategory.CONNECTION,
                component="websocket_client",
                context={"client_id": self.client_id, "operation_id": operation_id}
            )


# Global client instance
_client_instance = None


def get_websocket_client(url: str = "ws://localhost:8765", 
                        reconnection_config: Optional[ReconnectionConfig] = None,
                        authentication: Optional[Dict[str, str]] = None,
                        debug_mode: bool = False) -> WebSocketClient:
    """
    Get the global WebSocket client instance.
    
    Args:
        url: WebSocket server URL
        reconnection_config: Optional reconnection configuration
        authentication: Optional authentication parameters
        debug_mode: Enable debug mode
        
    Returns:
        WebSocketClient instance
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = WebSocketClient(
            url=url,
            reconnection_config=reconnection_config,
            authentication=authentication,
            debug_mode=debug_mode
        )
    return _client_instance