#!/usr/bin/env python3
"""
Simple WebSocket server for testing.

This script starts a basic WebSocket server for testing client connections.
"""

import asyncio
import websockets
import json
import logging
import argparse
import time
import uuid
import signal

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('simple_websocket_server')

# Active connections
connections = {}
operations = {}

async def handle_client(websocket, path):
    """Handle a client connection."""
    # Generate connection ID
    connection_id = str(uuid.uuid4())
    connections[connection_id] = websocket
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            'type': 'connection_status',
            'status': 'connected',
            'connection_id': connection_id,
            'timestamp': time.time()
        }))
        
        logger.info(f"Client connected: {connection_id}")
        
        # Handle messages
        async for message in websocket:
            try:
                # Parse message
                data = json.loads(message)
                message_type = data.get('type')
                
                logger.info(f"Received message from {connection_id}: {message_type}")
                
                # Handle different message types
                if message_type == 'ping':
                    # Respond with pong
                    await websocket.send(json.dumps({
                        'type': 'pong',
                        'timestamp': time.time(),
                        'client_timestamp': data.get('timestamp')
                    }))
                    
                elif message_type == 'list_operations':
                    # Send list of operations
                    await websocket.send(json.dumps({
                        'type': 'operations_list',
                        'operations': list(operations.values()),
                        'timestamp': time.time()
                    }))
                    
                elif message_type in ('operation_started', 'progress_update', 
                                    'operation_completed', 'operation_failed', 
                                    'operation_canceled'):
                    # Forward to all other clients
                    await broadcast_message(data, exclude=connection_id)
                    
                    # Save operation state
                    process_operation_event(data)
                    
                else:
                    # Unknown message type
                    logger.warning(f"Unknown message type: {message_type}")
                    
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from client {connection_id}")
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client disconnected: {connection_id}")
        
    finally:
        # Remove connection
        if connection_id in connections:
            del connections[connection_id]

async def broadcast_message(message, exclude=None):
    """
    Broadcast a message to all connected clients.
    
    Args:
        message: Message to broadcast
        exclude: Optional connection ID to exclude
    """
    # Get copy of connections
    connection_ids = list(connections.keys())
    
    # Send to each client (except excluded one)
    for conn_id in connection_ids:
        if conn_id != exclude:
            try:
                await connections[conn_id].send(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending to {conn_id}: {e}")

def process_operation_event(message):
    """
    Process an operation event message.
    
    Args:
        message: Operation event message
    """
    message_type = message.get('type')
    
    if message_type == 'operation_started':
        # Operation started
        operation = message.get('operation', {})
        operation_id = operation.get('operation_id')
        
        if operation_id:
            operations[operation_id] = operation
            logger.info(f"Operation started: {operation_id}")
            
    elif message_type == 'progress_update':
        # Progress update
        data = message.get('data', {})
        operation_id = data.get('operation_id')
        
        if operation_id and operation_id in operations:
            # Update operation
            operations[operation_id]['progress'] = data.get('progress', 0)
            operations[operation_id]['current_step'] = data.get('current_step')
            operations[operation_id]['last_update_time'] = time.time()
            
            # Log significant progress
            progress = data.get('progress', 0)
            if progress % 25 == 0:
                logger.info(f"Operation progress: {operation_id} - {progress}%")
                
    elif message_type == 'operation_completed':
        # Operation completed
        operation_id = message.get('operation_id')
        
        if operation_id and operation_id in operations:
            operations[operation_id]['status'] = 'completed'
            operations[operation_id]['progress'] = 100
            operations[operation_id]['end_time'] = time.time()
            logger.info(f"Operation completed: {operation_id}")
            
    elif message_type == 'operation_failed':
        # Operation failed
        operation_id = message.get('operation_id')
        
        if operation_id and operation_id in operations:
            operations[operation_id]['status'] = 'failed'
            operations[operation_id]['end_time'] = time.time()
            logger.info(f"Operation failed: {operation_id}")
            
    elif message_type == 'operation_canceled':
        # Operation canceled
        operation_id = message.get('operation_id')
        
        if operation_id and operation_id in operations:
            operations[operation_id]['status'] = 'canceled'
            operations[operation_id]['end_time'] = time.time()
            logger.info(f"Operation canceled: {operation_id}")

async def main(args):
    """
    Main entry point.
    
    Args:
        args: Command-line arguments
    """
    # Set up signal handlers for graceful shutdown
    stop_event = asyncio.Event()
    server = None
    
    def signal_handler():
        logger.info("Shutdown signal received")
        stop_event.set()
        
    # Register signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        # Start server
        server = await websockets.serve(
            handle_client, 
            args.host, 
            args.port,
            ping_interval=20,
            ping_timeout=10
        )
        
        logger.info(f"WebSocket server started on ws://{args.host}:{args.port}")
        
        # Wait for stop signal
        await stop_event.wait()
        
        return 0
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        return 1
    finally:
        # Close server if it was created
        if server:
            server.close()
            await server.wait_closed()
            logger.info("WebSocket server stopped")

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run a simple WebSocket server")
    
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=8767, help="Server port")
    
    args = parser.parse_args()
    
    # Run the server
    exit_code = asyncio.run(main(args))
    exit(exit_code)