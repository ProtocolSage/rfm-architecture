"""
WebSocket server for real-time progress reporting in RFM Architecture.

This module provides a WebSocket server that clients can connect to for
receiving real-time progress updates during long-running operations.
"""

import asyncio
import json
import logging
import time
import traceback
from typing import Dict, Any, Set, Optional, Callable, List, Union
from dataclasses import asdict

import websockets
from websockets.server import WebSocketServerProtocol, serve
from websockets.exceptions import ConnectionClosed

from .progress import get_progress_manager, ProgressData, OperationStatus

logger = logging.getLogger(__name__)


class ProgressWebSocketServer:
    """
    WebSocket server for broadcasting progress updates.
    
    This class manages WebSocket connections and broadcasts progress
    updates to connected clients.
    """
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        """
        Initialize the WebSocket server.
        
        Args:
            host: Hostname to bind to
            port: Port to listen on
        """
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self.server = None
        self.running = False
        self.progress_manager = get_progress_manager()
    
    async def start(self) -> None:
        """Start the WebSocket server."""
        if self.running:
            logger.warning("WebSocket server already running")
            return
            
        # Add progress callback
        self.progress_manager.add_callback(self._on_progress_update)
        
        # Start server
        try:
            self.server = await serve(
                self._handle_client,
                self.host,
                self.port
            )
            self.running = True
            logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the WebSocket server."""
        if not self.running:
            return
            
        # Remove progress callback
        self.progress_manager.remove_callback(self._on_progress_update)
        
        # Close all connections
        close_tasks = []
        for client in self.clients:
            try:
                close_tasks.append(client.close())
            except Exception:
                pass
                
        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)
            
        # Stop server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            
        self.running = False
        self.clients.clear()
        logger.info("WebSocket server stopped")
    
    async def _handle_client(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """
        Handle a client connection.
        
        Args:
            websocket: WebSocket connection
            path: Request path
        """
        # Add client to set
        self.clients.add(websocket)
        client_id = id(websocket)
        logger.debug(f"Client connected: {client_id} from {websocket.remote_address}")
        
        try:
            # Send list of current operations
            operations = await self.progress_manager.list_operations()
            if operations:
                await websocket.send(json.dumps({
                    "type": "operations_list",
                    "operations": operations
                }))
            
            # Handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(websocket, data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from client {client_id}: {message}")
                except Exception as e:
                    logger.error(f"Error handling message from client {client_id}: {e}")
                    logger.debug(traceback.format_exc())
        except ConnectionClosed:
            logger.debug(f"Client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
            logger.debug(traceback.format_exc())
        finally:
            # Remove client from set
            self.clients.discard(websocket)
    
    async def _handle_message(self, websocket: WebSocketServerProtocol, data: Dict[str, Any]) -> None:
        """
        Handle a message from a client.
        
        Args:
            websocket: WebSocket connection
            data: Message data
        """
        message_type = data.get("type")
        
        if message_type == "ping":
            # Handle ping message
            await websocket.send(json.dumps({
                "type": "pong",
                "timestamp": time.time()
            }))
            
        elif message_type == "list_operations":
            # Handle list operations request
            operations = await self.progress_manager.list_operations()
            await websocket.send(json.dumps({
                "type": "operations_list",
                "operations": operations
            }))
            
        elif message_type == "cancel_operation":
            # Handle cancel operation request
            operation_id = data.get("operation_id")
            if not operation_id:
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": "Missing operation_id"
                }))
                return
                
            success = await self.progress_manager.cancel_operation(operation_id)
            await websocket.send(json.dumps({
                "type": "cancel_result",
                "operation_id": operation_id,
                "success": success
            }))
            
        elif message_type == "get_operation_details":
            # Handle get operation details request
            operation_id = data.get("operation_id")
            if not operation_id:
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": "Missing operation_id"
                }))
                return
                
            operation = await self.progress_manager.get_operation(operation_id)
            if not operation:
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": f"Operation not found: {operation_id}"
                }))
                return
                
            # Create response with operation details
            await websocket.send(json.dumps({
                "type": "operation_details",
                "operation_id": operation_id,
                "details": {
                    "operation_type": operation.operation_type,
                    "name": operation.name,
                    "status": operation.status.value,
                    "progress": operation.progress,
                    "current_step": operation.current_step,
                    "total_steps": operation.total_steps,
                    "current_step_progress": operation.current_step_progress,
                    "start_time": operation.start_time,
                    "last_update_time": operation.last_update_time,
                    "details": operation.details
                }
            }))
            
        else:
            # Unknown message type
            await websocket.send(json.dumps({
                "type": "error",
                "error": f"Unknown message type: {message_type}"
            }))
    
    def _on_progress_update(self, progress_data: ProgressData) -> None:
        """
        Handle a progress update.
        
        Args:
            progress_data: Progress update data
        """
        # Broadcast message to all clients
        message = {
            "type": "progress_update",
            "timestamp": time.time(),
            "data": progress_data.to_dict()
        }
        
        # Convert to JSON once for all clients
        message_json = json.dumps(message)
        
        # Broadcast to all clients
        for client in list(self.clients):
            try:
                # Use ensure_future to avoid blocking
                asyncio.ensure_future(client.send(message_json))
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
    
    def is_running(self) -> bool:
        """
        Check if the server is running.
        
        Returns:
            True if the server is running, False otherwise
        """
        return self.running
    
    def get_address(self) -> str:
        """
        Get the server address.
        
        Returns:
            WebSocket server address as a string
        """
        return f"ws://{self.host}:{self.port}"


# Global server instance
_server_instance = None


def get_websocket_server(host: str = "localhost", port: int = 8765) -> ProgressWebSocketServer:
    """
    Get the global WebSocket server instance.
    
    Args:
        host: Hostname to bind to
        port: Port to listen on
        
    Returns:
        ProgressWebSocketServer instance
    """
    global _server_instance
    if _server_instance is None:
        _server_instance = ProgressWebSocketServer(host, port)
    return _server_instance


async def start_websocket_server(host: str = "localhost", port: int = 8765) -> ProgressWebSocketServer:
    """
    Start the WebSocket server.
    
    Args:
        host: Hostname to bind to
        port: Port to listen on
        
    Returns:
        Running ProgressWebSocketServer instance
    """
    server = get_websocket_server(host, port)
    if not server.is_running():
        await server.start()
    return server