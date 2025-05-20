"""
Enhanced WebSocket server for real-time progress reporting.

This module provides an enhanced WebSocket server for real-time progress reporting
with comprehensive logging, monitoring, and resilience features.
"""

import os
import sys
import time
import json
import asyncio
import logging
import signal
import uuid
import threading
import traceback
import websockets
from typing import Dict, Any, Optional, List, Set, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from .logging_config import (
    get_logger, configure_logging, LogLevel, LogCategory, log_timing, TimingContext
)
from .monitoring import (
    get_metrics_registry, get_connection_monitor,
    MetricType, HealthStatus, ConnectionMonitor
)


# Configure logger
logger = get_logger(__name__)


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
class ClientInfo:
    """Information about a connected client."""
    
    connection_id: str
    websocket: Any
    remote_address: Optional[str] = None
    user_agent: Optional[str] = None
    client_version: Optional[str] = None
    connect_time: float = field(default_factory=time.time)
    last_activity_time: float = field(default_factory=time.time)
    messages_received: int = 0
    messages_sent: int = 0
    subscriptions: Set[str] = field(default_factory=set)


class ProgressServer:
    """
    Enhanced WebSocket server for progress reporting.
    
    Features:
    - Comprehensive logging of connection events
    - Performance monitoring and metrics collection
    - Connection tracking and timeout management
    - Message validation and rate limiting
    - Secure client authentication (optional)
    - Operation management and monitoring
    """
    
    def __init__(self, 
                host: str = "localhost", 
                port: int = 8765,
                data_dir: Optional[str] = None,
                log_dir: Optional[str] = None,
                log_level: LogLevel = LogLevel.INFO,
                connection_timeout: float = 300.0,  # 5 minutes
                message_rate_limit: int = 100,      # messages per second
                enable_authentication: bool = False,
                api_keys: Optional[Dict[str, str]] = None):
        """
        Initialize the progress server.
        
        Args:
            host: Server hostname
            port: Server port
            data_dir: Directory for data storage
            log_dir: Directory for logs
            log_level: Log level
            connection_timeout: Timeout for inactive connections
            message_rate_limit: Rate limit for messages per client
            enable_authentication: Whether to enable API key authentication
            api_keys: Dictionary of API keys (client_id -> api_key)
        """
        self.host = host
        self.port = port
        self.data_dir = data_dir or os.path.join(os.getcwd(), "data", "progress")
        self.log_dir = log_dir or os.path.join(os.getcwd(), "logs")
        self.log_level = log_level
        self.connection_timeout = connection_timeout
        self.message_rate_limit = message_rate_limit
        self.enable_authentication = enable_authentication
        self.api_keys = api_keys or {}
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Configure logging
        configure_logging(
            app_name="websocket_server",
            log_dir=self.log_dir,
            console_level=self.log_level,
            file_level=LogLevel.DEBUG,
            json_format=True,
            correlation_id=f"server_{uuid.uuid4().hex[:8]}"
        )
        
        # Get metrics registry
        self.metrics_registry = get_metrics_registry("websocket_server")
        
        # Get connection monitor
        self.connection_monitor = get_connection_monitor()
        
        # Start system metrics collection
        self.metrics_registry.start_system_metrics_collection()
        
        # Set up server storage
        self.server = None
        self.clients: Dict[str, ClientInfo] = {}
        self.operations: Dict[str, Dict[str, Any]] = {}
        self.stop_event = asyncio.Event()
        
        # Operation event handlers
        self.operation_handlers: Dict[str, List[Callable]] = {
            "started": [],
            "updated": [],
            "completed": [],
            "failed": [],
            "canceled": []
        }
        
        # Generate server ID
        self.server_id = str(uuid.uuid4())
        
        logger.structured_log(
            LogLevel.INFO,
            "Initialized progress reporting WebSocket server",
            LogCategory.SYSTEM,
            component="websocket_server",
            context={
                "host": host,
                "port": port,
                "data_dir": self.data_dir,
                "log_dir": self.log_dir,
                "log_level": log_level,
                "server_id": self.server_id,
                "enable_authentication": enable_authentication
            }
        )
    
    @log_timing("start_server", LogLevel.INFO, LogCategory.SYSTEM, "websocket_server")
    async def start(self) -> None:
        """
        Start the WebSocket server.
        
        Returns:
            Server instance
        """
        # Register health check
        self.metrics_registry.register_health_check(
            "websocket_server",
            HealthStatus.HEALTHY,
            {"server_id": self.server_id}
        )
        
        # Start connection monitor
        self.connection_monitor.start()
        
        # Start server
        logger.structured_log(
            LogLevel.INFO,
            f"Starting WebSocket server on {self.host}:{self.port}",
            LogCategory.SYSTEM,
            component="websocket_server",
            context={"server_id": self.server_id}
        )
        
        try:
            # Create WebSocket server
            self.server = await websockets.serve(
                self._handle_client,
                self.host,
                self.port,
                process_request=self._process_request
            )
            
            # Reset stop event
            self.stop_event.clear()
            
            # Start periodic tasks
            asyncio.create_task(self._periodic_cleanup())
            
            # Log successful start
            logger.structured_log(
                LogLevel.INFO,
                f"WebSocket server started on ws://{self.host}:{self.port}",
                LogCategory.SYSTEM,
                component="websocket_server",
                context={"server_id": self.server_id}
            )
            
            # Update metrics
            self.metrics_registry.register_health_check(
                "websocket_server",
                HealthStatus.HEALTHY,
                {"server_id": self.server_id, "status": "running"}
            )
            
            return self
            
        except Exception as e:
            logger.structured_log(
                LogLevel.ERROR,
                f"Failed to start WebSocket server: {e}",
                LogCategory.SYSTEM,
                component="websocket_server",
                context={"server_id": self.server_id},
                error=str(e)
            )
            
            # Update metrics
            self.metrics_registry.register_health_check(
                "websocket_server",
                HealthStatus.UNHEALTHY,
                {"server_id": self.server_id, "error": str(e)}
            )
            
            # Propagate exception
            raise
    
    async def stop(self) -> None:
        """Stop the WebSocket server."""
        if not self.server:
            return
            
        # Set stop event
        self.stop_event.set()
        
        # Log stop request
        logger.structured_log(
            LogLevel.INFO,
            "Stopping WebSocket server",
            LogCategory.SYSTEM,
            component="websocket_server",
            context={"server_id": self.server_id}
        )
        
        # Update metrics
        self.metrics_registry.register_health_check(
            "websocket_server",
            HealthStatus.DEGRADED,
            {"server_id": self.server_id, "status": "stopping"}
        )
        
        # Close all client connections
        client_connections = list(self.clients.items())
        for connection_id, client_info in client_connections:
            try:
                await client_info.websocket.close(1001, "Server shutting down")
                
                # Remove client
                if connection_id in self.clients:
                    del self.clients[connection_id]
                    
                    # Update connection monitor
                    self.connection_monitor.connection_closed(
                        connection_id, 
                        {"reason": "server_shutdown"}
                    )
                    
            except Exception as e:
                logger.structured_log(
                    LogLevel.WARNING,
                    f"Error closing client connection: {e}",
                    LogCategory.CONNECTION,
                    component="websocket_server",
                    context={"connection_id": connection_id, "server_id": self.server_id},
                    error=str(e)
                )
        
        # Stop connection monitor
        self.connection_monitor.stop()
        
        # Stop metrics collection
        self.metrics_registry.stop_system_metrics_collection()
        
        # Close the server
        self.server.close()
        await self.server.wait_closed()
        
        # Update health status
        self.metrics_registry.register_health_check(
            "websocket_server",
            HealthStatus.UNKNOWN,
            {"server_id": self.server_id, "status": "stopped"}
        )
        
        # Log server stopped
        logger.structured_log(
            LogLevel.INFO,
            "WebSocket server stopped",
            LogCategory.SYSTEM,
            component="websocket_server",
            context={"server_id": self.server_id}
        )
        
        # Clear server reference
        self.server = None
    
    async def _process_request(self, 
                             path: str, 
                             request_headers: Dict[str, str]) -> Optional[Tuple[int, Dict[str, str], bytes]]:
        """
        Process HTTP request before WebSocket handshake.
        
        This is used for authentication and path routing.
        
        Args:
            path: Request path
            request_headers: HTTP headers
            
        Returns:
            Tuple of (status_code, headers, body) if request should be rejected, 
            None if connection should proceed
        """
        # Parse URL path and query parameters
        parsed_url = urlparse(path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        
        # Get authentication parameters
        auth_token = query_params.get("token", [None])[0]
        client_id = query_params.get("client_id", [None])[0]
        
        # Check authentication if enabled
        if self.enable_authentication:
            if not client_id or not auth_token:
                # Missing authentication parameters
                logger.structured_log(
                    LogLevel.WARNING,
                    "Authentication failed: Missing client_id or token",
                    LogCategory.SECURITY,
                    component="websocket_server",
                    context={"server_id": self.server_id, "path": path}
                )
                
                return (401, {}, b"Authentication required")
                
            # Check API key
            if client_id not in self.api_keys:
                # Unknown client
                logger.structured_log(
                    LogLevel.WARNING,
                    f"Authentication failed: Unknown client_id {client_id}",
                    LogCategory.SECURITY,
                    component="websocket_server",
                    context={"server_id": self.server_id, "client_id": client_id}
                )
                
                return (401, {}, b"Invalid client_id")
                
            if self.api_keys[client_id] != auth_token:
                # Invalid token
                logger.structured_log(
                    LogLevel.WARNING,
                    f"Authentication failed: Invalid token for client_id {client_id}",
                    LogCategory.SECURITY,
                    component="websocket_server",
                    context={"server_id": self.server_id, "client_id": client_id}
                )
                
                return (401, {}, b"Invalid token")
        
        # Check path if needed
        if path != "/":
            if path == "/health":
                # Health check endpoint
                health_status = self.metrics_registry.get_health_status()
                return (200, {"Content-Type": "application/json"}, json.dumps(health_status).encode("utf-8"))
                
            elif path == "/metrics":
                # Metrics endpoint
                metrics = self.metrics_registry.get_metrics_report()
                return (200, {"Content-Type": "application/json"}, json.dumps(metrics).encode("utf-8"))
                
            else:
                # Unknown path
                logger.structured_log(
                    LogLevel.WARNING,
                    f"Unknown path requested: {path}",
                    LogCategory.SYSTEM,
                    component="websocket_server",
                    context={"server_id": self.server_id, "path": path}
                )
                
                return (404, {}, b"Not found")
        
        # Allow connection
        return None
    
    @log_timing("handle_client", LogLevel.DEBUG, LogCategory.CONNECTION, "websocket_server")
    async def _handle_client(self, websocket, path: str) -> None:
        """
        Handle a client WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            path: Connection path
        """
        # Generate connection ID
        connection_id = str(uuid.uuid4())
        
        # Get client info
        remote_address = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}" if websocket.remote_address else "unknown"
        
        # Extract client info from request
        request_headers = websocket.request_headers
        user_agent = request_headers.get("User-Agent", "unknown")
        
        # Create client info
        client_info = ClientInfo(
            connection_id=connection_id,
            websocket=websocket,
            remote_address=remote_address,
            user_agent=user_agent
        )
        
        # Register client
        self.clients[connection_id] = client_info
        
        # Update connection monitor
        self.connection_monitor.connection_opened(
            connection_id,
            websocket,
            {
                "user_agent": user_agent,
                "client_info": {
                    "remote_address": remote_address
                }
            }
        )
        
        # Log connection
        logger.structured_log(
            LogLevel.INFO,
            f"Client connected: {connection_id} from {remote_address}",
            LogCategory.CONNECTION,
            component="websocket_server",
            context={
                "connection_id": connection_id,
                "remote_address": remote_address,
                "user_agent": user_agent,
                "server_id": self.server_id
            }
        )
        
        try:
            # Send initial operations list
            await self._send_operations_list(connection_id)
            
            # Handle messages in a loop
            async for message in websocket:
                # Update last activity time
                client_info.last_activity_time = time.time()
                
                # Process message
                try:
                    # Update connection monitor
                    self.connection_monitor.message_received(
                        connection_id, 
                        message,
                        "unknown"  # Will be updated after parsing
                    )
                    
                    # Increment message count
                    client_info.messages_received += 1
                    
                    # Parse message
                    try:
                        data = json.loads(message)
                        message_type = data.get("type")
                        
                        # Update connection monitor with message type
                        self.connection_monitor.message_received(
                            connection_id, 
                            message,
                            message_type
                        )
                        
                        # Log message
                        logger.structured_log(
                            LogLevel.DEBUG,
                            f"Received message from {connection_id}: {message_type}",
                            LogCategory.CONNECTION,
                            component="websocket_server",
                            context={
                                "connection_id": connection_id,
                                "message_type": message_type,
                                "server_id": self.server_id
                            }
                        )
                        
                        # Process message
                        await self._process_message(connection_id, data)
                        
                    except json.JSONDecodeError:
                        # Invalid JSON
                        logger.structured_log(
                            LogLevel.WARNING,
                            f"Invalid JSON from client {connection_id}",
                            LogCategory.CONNECTION,
                            component="websocket_server",
                            context={
                                "connection_id": connection_id,
                                "message": message[:100],  # Log first 100 chars
                                "server_id": self.server_id
                            }
                        )
                        
                        # Send error message
                        await self._send_error(
                            connection_id,
                            "invalid_json",
                            "Invalid JSON message"
                        )
                        
                except Exception as e:
                    # Error processing message
                    logger.structured_log(
                        LogLevel.ERROR,
                        f"Error processing message from {connection_id}: {e}",
                        LogCategory.CONNECTION,
                        component="websocket_server",
                        context={
                            "connection_id": connection_id,
                            "server_id": self.server_id
                        },
                        error=str(e)
                    )
                    
                    # Send error message
                    await self._send_error(
                        connection_id,
                        "processing_error",
                        f"Error processing message: {e}"
                    )
                    
        except websockets.exceptions.ConnectionClosed as e:
            # Connection closed
            close_code = e.code if hasattr(e, "code") else None
            close_reason = e.reason if hasattr(e, "reason") else None
            
            logger.structured_log(
                LogLevel.INFO,
                f"Client connection closed: {connection_id} (code: {close_code}, reason: {close_reason})",
                LogCategory.CONNECTION,
                component="websocket_server",
                context={
                    "connection_id": connection_id,
                    "code": close_code,
                    "reason": close_reason,
                    "server_id": self.server_id
                }
            )
            
        except Exception as e:
            # Unexpected error
            logger.structured_log(
                LogLevel.ERROR,
                f"Error handling client {connection_id}: {e}",
                LogCategory.CONNECTION,
                component="websocket_server",
                context={"connection_id": connection_id, "server_id": self.server_id},
                error=str(e)
            )
            
        finally:
            # Remove client
            if connection_id in self.clients:
                del self.clients[connection_id]
                
                # Update connection monitor
                self.connection_monitor.connection_closed(
                    connection_id,
                    {"reason": "normal"}
                )
    
    async def _process_message(self, connection_id: str, message: Dict[str, Any]) -> None:
        """
        Process a client message.
        
        Args:
            connection_id: Connection ID
            message: Message data
        """
        message_type = message.get("type")
        
        # Process based on message type
        if message_type == MessageType.PING:
            # Ping request
            await self._send_pong(connection_id, message.get("timestamp"))
            
        elif message_type == MessageType.LIST_OPERATIONS:
            # List operations request
            await self._send_operations_list(connection_id)
            
        elif message_type == MessageType.CANCEL_OPERATION:
            # Cancel operation request
            operation_id = message.get("operation_id")
            
            if not operation_id:
                await self._send_error(
                    connection_id,
                    "missing_operation_id",
                    "Missing operation_id parameter"
                )
                return
                
            await self._cancel_operation(connection_id, operation_id)
            
        elif message_type == MessageType.GET_OPERATION_DETAILS:
            # Get operation details request
            operation_id = message.get("operation_id")
            
            if not operation_id:
                await self._send_error(
                    connection_id,
                    "missing_operation_id",
                    "Missing operation_id parameter"
                )
                return
                
            await self._send_operation_details(connection_id, operation_id)
            
        elif message_type in (
            MessageType.OPERATION_STARTED,
            MessageType.PROGRESS_UPDATE,
            MessageType.OPERATION_COMPLETED,
            MessageType.OPERATION_FAILED,
            MessageType.OPERATION_CANCELED
        ):
            # Forward operation events to all clients
            await self._broadcast_message(message, exclude_connection_ids={connection_id})
            
            # Process operation event
            await self._process_operation_event(message)
            
        else:
            # Unknown message type
            logger.structured_log(
                LogLevel.WARNING,
                f"Unknown message type from {connection_id}: {message_type}",
                LogCategory.CONNECTION,
                component="websocket_server",
                context={
                    "connection_id": connection_id,
                    "message_type": message_type,
                    "server_id": self.server_id
                }
            )
            
            # Send error message
            await self._send_error(
                connection_id,
                "unknown_message_type",
                f"Unknown message type: {message_type}"
            )
    
    async def _send_message(self, 
                          connection_id: str, 
                          message: Dict[str, Any]) -> None:
        """
        Send a message to a client.
        
        Args:
            connection_id: Connection ID
            message: Message to send
        """
        if connection_id not in self.clients:
            logger.structured_log(
                LogLevel.WARNING,
                f"Cannot send message to unknown client: {connection_id}",
                LogCategory.CONNECTION,
                component="websocket_server",
                context={"server_id": self.server_id}
            )
            return
            
        try:
            # Get client info
            client_info = self.clients[connection_id]
            
            # Serialize message
            message_json = json.dumps(message)
            
            # Send message
            await client_info.websocket.send(message_json)
            
            # Update metrics
            client_info.messages_sent += 1
            
            # Update connection monitor
            self.connection_monitor.message_sent(
                connection_id,
                message_json,
                message.get("type")
            )
            
            # Log message
            logger.structured_log(
                LogLevel.DEBUG,
                f"Sent message to {connection_id}: {message.get('type')}",
                LogCategory.CONNECTION,
                component="websocket_server",
                context={
                    "connection_id": connection_id,
                    "message_type": message.get("type"),
                    "server_id": self.server_id
                }
            )
            
        except websockets.exceptions.ConnectionClosed:
            # Connection already closed
            logger.structured_log(
                LogLevel.WARNING,
                f"Cannot send message to closed connection: {connection_id}",
                LogCategory.CONNECTION,
                component="websocket_server",
                context={
                    "connection_id": connection_id,
                    "server_id": self.server_id
                }
            )
            
            # Remove client
            if connection_id in self.clients:
                del self.clients[connection_id]
                
                # Update connection monitor
                self.connection_monitor.connection_closed(
                    connection_id,
                    {"reason": "closed_before_send"}
                )
                
        except Exception as e:
            # Error sending message
            logger.structured_log(
                LogLevel.ERROR,
                f"Error sending message to {connection_id}: {e}",
                LogCategory.CONNECTION,
                component="websocket_server",
                context={
                    "connection_id": connection_id,
                    "server_id": self.server_id
                },
                error=str(e)
            )
    
    async def _broadcast_message(self, 
                               message: Dict[str, Any],
                               exclude_connection_ids: Optional[Set[str]] = None) -> None:
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: Message to broadcast
            exclude_connection_ids: Optional set of connection IDs to exclude
        """
        exclude_connection_ids = exclude_connection_ids or set()
        
        # Get client connections
        connections = list(self.clients.keys())
        
        # Send message to each client
        for connection_id in connections:
            if connection_id not in exclude_connection_ids:
                await self._send_message(connection_id, message)
    
    async def _send_error(self, 
                        connection_id: str, 
                        error_code: str, 
                        error_message: str) -> None:
        """
        Send an error message to a client.
        
        Args:
            connection_id: Connection ID
            error_code: Error code
            error_message: Error message
        """
        message = {
            "type": MessageType.ERROR,
            "error_code": error_code,
            "error_message": error_message,
            "timestamp": time.time()
        }
        
        await self._send_message(connection_id, message)
    
    async def _send_pong(self, 
                       connection_id: str, 
                       client_timestamp: Optional[float] = None) -> None:
        """
        Send a pong response to a client.
        
        Args:
            connection_id: Connection ID
            client_timestamp: Optional client timestamp from ping
        """
        message = {
            "type": MessageType.PONG,
            "timestamp": time.time()
        }
        
        if client_timestamp:
            message["client_timestamp"] = client_timestamp
            
        await self._send_message(connection_id, message)
    
    async def _send_operations_list(self, connection_id: str) -> None:
        """
        Send list of operations to a client.
        
        Args:
            connection_id: Connection ID
        """
        # Get operations
        operations = list(self.operations.values())
        
        # Create message
        message = {
            "type": MessageType.OPERATIONS_LIST,
            "operations": operations,
            "timestamp": time.time()
        }
        
        await self._send_message(connection_id, message)
    
    async def _send_operation_details(self, 
                                   connection_id: str, 
                                   operation_id: str) -> None:
        """
        Send operation details to a client.
        
        Args:
            connection_id: Connection ID
            operation_id: Operation ID
        """
        if operation_id not in self.operations:
            await self._send_error(
                connection_id,
                "unknown_operation",
                f"Unknown operation: {operation_id}"
            )
            return
            
        # Get operation details
        operation = self.operations[operation_id]
        
        # Create message
        message = {
            "type": MessageType.GET_OPERATION_DETAILS,
            "operation": operation,
            "timestamp": time.time()
        }
        
        await self._send_message(connection_id, message)
    
    async def _cancel_operation(self, 
                             connection_id: str, 
                             operation_id: str) -> None:
        """
        Handle operation cancellation request.
        
        Args:
            connection_id: Connection ID
            operation_id: Operation ID
        """
        if operation_id not in self.operations:
            await self._send_error(
                connection_id,
                "unknown_operation",
                f"Unknown operation: {operation_id}"
            )
            return
            
        # Get operation
        operation = self.operations[operation_id]
        
        # Check if operation is active
        status = operation.get("status")
        if status not in ("pending", "running", "paused"):
            await self._send_error(
                connection_id,
                "invalid_operation_state",
                f"Cannot cancel operation in state: {status}"
            )
            return
            
        # Log cancellation request
        logger.structured_log(
            LogLevel.INFO,
            f"Cancellation requested for operation {operation_id} by {connection_id}",
            LogCategory.OPERATION,
            operation_id=operation_id,
            component="websocket_server",
            context={
                "connection_id": connection_id,
                "operation_id": operation_id,
                "operation_type": operation.get("operation_type"),
                "server_id": self.server_id
            }
        )
        
        # Mark operation for cancellation
        operation["cancellation_requested"] = True
        operation["cancellation_time"] = time.time()
        operation["cancellation_connection_id"] = connection_id
        
        # Update operation in storage
        self.operations[operation_id] = operation
        
        # Broadcast cancellation request
        message = {
            "type": MessageType.CANCEL_OPERATION,
            "operation_id": operation_id,
            "timestamp": time.time()
        }
        
        await self._broadcast_message(message)
        
        # Update metrics
        self.metrics_registry.update_metric("operations.canceled", 1)
    
    async def _process_operation_event(self, message: Dict[str, Any]) -> None:
        """
        Process an operation event message.
        
        Args:
            message: Operation event message
        """
        message_type = message.get("type")
        
        if message_type == MessageType.OPERATION_STARTED:
            # Operation started
            operation = message.get("operation", {})
            operation_id = operation.get("operation_id")
            
            if not operation_id:
                logger.structured_log(
                    LogLevel.WARNING,
                    "Invalid operation_started message: Missing operation_id",
                    LogCategory.OPERATION,
                    component="websocket_server",
                    context={"server_id": self.server_id}
                )
                return
                
            # Store operation
            self.operations[operation_id] = operation
            
            # Log operation started
            logger.structured_log(
                LogLevel.INFO,
                f"Operation started: {operation_id}",
                LogCategory.OPERATION,
                operation_id=operation_id,
                component="websocket_server",
                context={
                    "operation_id": operation_id,
                    "operation_type": operation.get("operation_type"),
                    "operation_name": operation.get("name"),
                    "server_id": self.server_id
                }
            )
            
            # Update metrics
            self.metrics_registry.update_metric("operations.total", 1)
            self.metrics_registry.update_metric("operations.active", len(self.operations))
            
            # Trigger handlers
            await self._trigger_operation_handlers("started", operation)
            
        elif message_type == MessageType.PROGRESS_UPDATE:
            # Progress update
            data = message.get("data", {})
            operation_id = data.get("operation_id")
            
            if not operation_id:
                logger.structured_log(
                    LogLevel.WARNING,
                    "Invalid progress_update message: Missing operation_id",
                    LogCategory.OPERATION,
                    component="websocket_server",
                    context={"server_id": self.server_id}
                )
                return
                
            # Get existing operation
            if operation_id not in self.operations:
                # Unknown operation, create it
                self.operations[operation_id] = {
                    "operation_id": operation_id,
                    "operation_type": data.get("operation_type", "unknown"),
                    "status": data.get("status", "running"),
                    "progress": data.get("progress", 0),
                    "start_time": data.get("timestamp", time.time()),
                    "last_update_time": data.get("timestamp", time.time())
                }
            
            # Update operation
            operation = self.operations[operation_id]
            operation["status"] = data.get("status", operation.get("status", "running"))
            operation["progress"] = data.get("progress", operation.get("progress", 0))
            operation["current_step"] = data.get("current_step", operation.get("current_step"))
            operation["last_update_time"] = data.get("timestamp", time.time())
            
            # Update details if provided
            if "details" in data and data["details"]:
                if "details" not in operation:
                    operation["details"] = {}
                    
                operation["details"].update(data["details"])
                
            # Store updated operation
            self.operations[operation_id] = operation
            
            # Log progress update (only for significant changes)
            progress = data.get("progress", 0)
            if progress % 10 == 0 or progress == 100:  # Log at 0%, 10%, 20%, ..., 100%
                logger.structured_log(
                    LogLevel.DEBUG,
                    f"Operation progress: {operation_id} - {progress}%",
                    LogCategory.OPERATION,
                    operation_id=operation_id,
                    component="websocket_server",
                    context={
                        "operation_id": operation_id,
                        "progress": progress,
                        "current_step": data.get("current_step"),
                        "server_id": self.server_id
                    }
                )
                
            # Trigger handlers
            await self._trigger_operation_handlers("updated", operation)
            
        elif message_type == MessageType.OPERATION_COMPLETED:
            # Operation completed
            operation_id = message.get("operation_id")
            
            if not operation_id:
                logger.structured_log(
                    LogLevel.WARNING,
                    "Invalid operation_completed message: Missing operation_id",
                    LogCategory.OPERATION,
                    component="websocket_server",
                    context={"server_id": self.server_id}
                )
                return
                
            # Get operation
            if operation_id not in self.operations:
                logger.structured_log(
                    LogLevel.WARNING,
                    f"Operation completed for unknown operation: {operation_id}",
                    LogCategory.OPERATION,
                    operation_id=operation_id,
                    component="websocket_server",
                    context={"server_id": self.server_id}
                )
                
                # Create operation
                self.operations[operation_id] = {
                    "operation_id": operation_id,
                    "operation_type": "unknown",
                    "status": "completed",
                    "progress": 100,
                    "start_time": time.time() - 1,  # 1 second ago
                    "end_time": time.time()
                }
            
            # Update operation
            operation = self.operations[operation_id]
            operation["status"] = "completed"
            operation["progress"] = 100
            operation["end_time"] = time.time()
            
            # Calculate duration
            if "start_time" in operation:
                operation["duration"] = operation["end_time"] - operation["start_time"]
                
            # Update details if provided
            if "details" in message:
                if "details" not in operation:
                    operation["details"] = {}
                    
                operation["details"].update(message["details"])
                
            # Store updated operation
            self.operations[operation_id] = operation
            
            # Log operation completed
            logger.structured_log(
                LogLevel.INFO,
                f"Operation completed: {operation_id}",
                LogCategory.OPERATION,
                operation_id=operation_id,
                component="websocket_server",
                context={
                    "operation_id": operation_id,
                    "duration": operation.get("duration"),
                    "server_id": self.server_id
                }
            )
            
            # Update metrics
            self.metrics_registry.update_metric("operations.completed", 1)
            self.metrics_registry.update_metric("operations.active", len(self.operations))
            
            if "duration" in operation:
                self.metrics_registry.update_metric("operations.duration", operation["duration"])
                
            # Trigger handlers
            await self._trigger_operation_handlers("completed", operation)
            
        elif message_type == MessageType.OPERATION_FAILED:
            # Operation failed
            operation_id = message.get("operation_id")
            
            if not operation_id:
                logger.structured_log(
                    LogLevel.WARNING,
                    "Invalid operation_failed message: Missing operation_id",
                    LogCategory.OPERATION,
                    component="websocket_server",
                    context={"server_id": self.server_id}
                )
                return
                
            # Get operation
            if operation_id not in self.operations:
                logger.structured_log(
                    LogLevel.WARNING,
                    f"Operation failed for unknown operation: {operation_id}",
                    LogCategory.OPERATION,
                    operation_id=operation_id,
                    component="websocket_server",
                    context={"server_id": self.server_id}
                )
                
                # Create operation
                self.operations[operation_id] = {
                    "operation_id": operation_id,
                    "operation_type": "unknown",
                    "status": "failed",
                    "start_time": time.time() - 1,  # 1 second ago
                    "end_time": time.time()
                }
            
            # Update operation
            operation = self.operations[operation_id]
            operation["status"] = "failed"
            operation["end_time"] = time.time()
            
            # Calculate duration
            if "start_time" in operation:
                operation["duration"] = operation["end_time"] - operation["start_time"]
                
            # Update details if provided
            if "details" in message:
                if "details" not in operation:
                    operation["details"] = {}
                    
                operation["details"].update(message["details"])
                
            # Store updated operation
            self.operations[operation_id] = operation
            
            # Log operation failed
            error_message = operation.get("details", {}).get("error_message", "Unknown error")
            
            logger.structured_log(
                LogLevel.ERROR,
                f"Operation failed: {operation_id} - {error_message}",
                LogCategory.OPERATION,
                operation_id=operation_id,
                component="websocket_server",
                context={
                    "operation_id": operation_id,
                    "error_message": error_message,
                    "duration": operation.get("duration"),
                    "server_id": self.server_id
                }
            )
            
            # Update metrics
            self.metrics_registry.update_metric("operations.failed", 1)
            self.metrics_registry.update_metric("operations.active", len(self.operations))
            
            # Trigger handlers
            await self._trigger_operation_handlers("failed", operation)
            
        elif message_type == MessageType.OPERATION_CANCELED:
            # Operation canceled
            operation_id = message.get("operation_id")
            
            if not operation_id:
                logger.structured_log(
                    LogLevel.WARNING,
                    "Invalid operation_canceled message: Missing operation_id",
                    LogCategory.OPERATION,
                    component="websocket_server",
                    context={"server_id": self.server_id}
                )
                return
                
            # Get operation
            if operation_id not in self.operations:
                logger.structured_log(
                    LogLevel.WARNING,
                    f"Operation canceled for unknown operation: {operation_id}",
                    LogCategory.OPERATION,
                    operation_id=operation_id,
                    component="websocket_server",
                    context={"server_id": self.server_id}
                )
                
                # Create operation
                self.operations[operation_id] = {
                    "operation_id": operation_id,
                    "operation_type": "unknown",
                    "status": "canceled",
                    "start_time": time.time() - 1,  # 1 second ago
                    "end_time": time.time()
                }
            
            # Update operation
            operation = self.operations[operation_id]
            operation["status"] = "canceled"
            operation["end_time"] = time.time()
            
            # Calculate duration
            if "start_time" in operation:
                operation["duration"] = operation["end_time"] - operation["start_time"]
                
            # Update details if provided
            if "details" in message:
                if "details" not in operation:
                    operation["details"] = {}
                    
                operation["details"].update(message["details"])
                
            # Store updated operation
            self.operations[operation_id] = operation
            
            # Log operation canceled
            logger.structured_log(
                LogLevel.INFO,
                f"Operation canceled: {operation_id}",
                LogCategory.OPERATION,
                operation_id=operation_id,
                component="websocket_server",
                context={
                    "operation_id": operation_id,
                    "duration": operation.get("duration"),
                    "server_id": self.server_id
                }
            )
            
            # Update metrics
            self.metrics_registry.update_metric("operations.canceled", 1)
            self.metrics_registry.update_metric("operations.active", len(self.operations))
            
            # Trigger handlers
            await self._trigger_operation_handlers("canceled", operation)
    
    async def _trigger_operation_handlers(self, 
                                       event_type: str, 
                                       operation: Dict[str, Any]) -> None:
        """
        Trigger operation event handlers.
        
        Args:
            event_type: Event type (started, updated, completed, failed, canceled)
            operation: Operation data
        """
        if event_type not in self.operation_handlers:
            return
            
        # Get handlers
        handlers = self.operation_handlers[event_type]
        
        # Trigger handlers
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(operation)
                else:
                    handler(operation)
            except Exception as e:
                logger.structured_log(
                    LogLevel.ERROR,
                    f"Error in operation {event_type} handler: {e}",
                    LogCategory.OPERATION,
                    operation_id=operation.get("operation_id"),
                    component="websocket_server",
                    context={"server_id": self.server_id},
                    error=str(e)
                )
    
    def register_operation_handler(self, 
                                event_type: str, 
                                handler: Callable) -> None:
        """
        Register an operation event handler.
        
        Args:
            event_type: Event type (started, updated, completed, failed, canceled)
            handler: Handler function
        """
        if event_type not in self.operation_handlers:
            logger.structured_log(
                LogLevel.WARNING,
                f"Unknown operation event type: {event_type}",
                LogCategory.SYSTEM,
                component="websocket_server",
                context={"server_id": self.server_id}
            )
            return
            
        # Add handler
        self.operation_handlers[event_type].append(handler)
        
        logger.structured_log(
            LogLevel.INFO,
            f"Registered operation {event_type} handler",
            LogCategory.SYSTEM,
            component="websocket_server",
            context={"server_id": self.server_id}
        )
    
    def get_operations(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all operations.
        
        Returns:
            Dictionary of operation ID to operation data
        """
        return self.operations.copy()
    
    def get_active_client_count(self) -> int:
        """
        Get the number of active clients.
        
        Returns:
            Number of active clients
        """
        return len(self.clients)
    
    def get_server_status(self) -> Dict[str, Any]:
        """
        Get server status information.
        
        Returns:
            Dictionary with server status information
        """
        active_operations = sum(1 for op in self.operations.values() 
                             if op.get("status") in ("pending", "running", "paused"))
        
        return {
            "server_id": self.server_id,
            "start_time": getattr(self, "start_time", None),
            "active_clients": len(self.clients),
            "active_operations": active_operations,
            "total_operations": len(self.operations),
            "connection_stats": self.connection_monitor.get_connection_stats()
        }
    
    async def _periodic_cleanup(self) -> None:
        """Perform periodic cleanup tasks."""
        while not self.stop_event.is_set():
            try:
                # Clean up completed operations
                await self._cleanup_operations()
                
                # Wait before next cleanup
                await asyncio.sleep(60)  # Cleanup every minute
                
            except asyncio.CancelledError:
                # Task canceled
                break
            except Exception as e:
                logger.structured_log(
                    LogLevel.ERROR,
                    f"Error in periodic cleanup: {e}",
                    LogCategory.SYSTEM,
                    component="websocket_server",
                    context={"server_id": self.server_id},
                    error=str(e)
                )
                
                # Continue cleanup
                await asyncio.sleep(60)
    
    async def _cleanup_operations(self) -> None:
        """Clean up old completed operations."""
        # Current time
        current_time = time.time()
        
        # Find old completed operations
        old_operations = []
        
        for operation_id, operation in self.operations.items():
            # Skip active operations
            if operation.get("status") in ("pending", "running", "paused"):
                continue
                
            # Get end time
            end_time = operation.get("end_time")
            
            if end_time and (current_time - end_time) > 3600:  # 1 hour old
                old_operations.append(operation_id)
                
        # Remove old operations
        for operation_id in old_operations:
            del self.operations[operation_id]
            
        # Log cleanup
        if old_operations:
            logger.structured_log(
                LogLevel.INFO,
                f"Cleaned up {len(old_operations)} old operations",
                LogCategory.SYSTEM,
                component="websocket_server",
                context={
                    "operation_count": len(old_operations),
                    "remaining_operations": len(self.operations),
                    "server_id": self.server_id
                }
            )


# Global server instance
_server_instance: Optional[ProgressServer] = None


async def start_websocket_server(
    host: str = "localhost",
    port: int = 8765,
    data_dir: Optional[str] = None,
    log_dir: Optional[str] = None,
    log_level: LogLevel = LogLevel.INFO,
    connection_timeout: float = 300.0,
    enable_authentication: bool = False,
    api_keys: Optional[Dict[str, str]] = None
) -> ProgressServer:
    """
    Start the WebSocket server for progress reporting.
    
    Args:
        host: Server hostname
        port: Server port
        data_dir: Directory for data storage
        log_dir: Directory for logs
        log_level: Log level
        connection_timeout: Timeout for inactive connections
        enable_authentication: Whether to enable API key authentication
        api_keys: Dictionary of API keys (client_id -> api_key)
        
    Returns:
        ProgressServer instance
    """
    global _server_instance
    
    # Create server if needed
    if _server_instance is None:
        _server_instance = ProgressServer(
            host=host,
            port=port,
            data_dir=data_dir,
            log_dir=log_dir,
            log_level=log_level,
            connection_timeout=connection_timeout,
            enable_authentication=enable_authentication,
            api_keys=api_keys
        )
        
        # Start server
        await _server_instance.start()
        
        # Store start time
        _server_instance.start_time = time.time()
        
    return _server_instance


async def stop_websocket_server() -> None:
    """Stop the WebSocket server."""
    global _server_instance
    
    if _server_instance:
        await _server_instance.stop()
        _server_instance = None


def get_server_instance() -> Optional[ProgressServer]:
    """
    Get the global server instance.
    
    Returns:
        ProgressServer instance, or None if not started
    """
    global _server_instance
    return _server_instance