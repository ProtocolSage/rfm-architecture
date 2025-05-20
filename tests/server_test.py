#!/usr/bin/env python
"""
WebSocket server for testing.

Run this script in a separate terminal to start the WebSocket server.
"""

import asyncio
import websockets
import json
import time
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("websocket_server")


# Simple WebSocket server
async def websocket_server(websocket, path):
    """Handle WebSocket connections."""
    logger.info(f"Client connected: {websocket.remote_address}")
    
    try:
        async for message in websocket:
            logger.info(f"Received message: {message}")
            
            try:
                data = json.loads(message)
                message_type = data.get("type")
                
                if message_type == "ping":
                    # Respond with pong
                    response = {
                        "type": "pong",
                        "timestamp": time.time()
                    }
                    await websocket.send(json.dumps(response))
                    
                elif message_type == "test_operation":
                    # Simulate progress updates
                    operation_id = data.get("operation_id", "unknown")
                    
                    # Send operation started
                    await websocket.send(json.dumps({
                        "type": "operation_started",
                        "operation": {
                            "operation_id": operation_id,
                            "operation_type": "test",
                            "name": "Test Operation"
                        }
                    }))
                    
                    # Send progress updates
                    for progress in [0, 25, 50, 75, 100]:
                        await websocket.send(json.dumps({
                            "type": "progress_update",
                            "data": {
                                "operation_id": operation_id,
                                "operation_type": "test",
                                "progress": progress,
                                "status": "running",
                                "current_step": f"Step {progress//25 + 1}" if progress < 100 else "Completed",
                                "timestamp": time.time()
                            }
                        }))
                        
                        # Delay between updates
                        await asyncio.sleep(0.5)
                    
                    # Send operation completed
                    await websocket.send(json.dumps({
                        "type": "operation_completed",
                        "operation_id": operation_id,
                        "details": {"completion_time": time.time()}
                    }))
                    
                elif message_type == "cancel_operation":
                    # Simulate operation cancellation
                    operation_id = data.get("operation_id")
                    
                    # Send operation canceled
                    await websocket.send(json.dumps({
                        "type": "operation_canceled",
                        "operation_id": operation_id,
                        "details": {"cancellation_time": time.time()}
                    }))
                    
                else:
                    # Echo unknown messages back
                    await websocket.send(message)
                    
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {message}")
                # Echo back as text
                await websocket.send(message)
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client disconnected: {websocket.remote_address}")


async def main():
    """Main function."""
    # Start server
    logger.info("Starting WebSocket server on localhost:8765")
    async with websockets.serve(websocket_server, "localhost", 8765):
        # Keep server running
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    asyncio.run(main())