#!/usr/bin/env python
"""
WebSocket client for testing.

Run this script to test the WebSocket client against the server.
"""

import asyncio
import websockets
import json
import time
import logging
import sys
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("websocket_client")


# Simple WebSocket client
class WebSocketClient:
    """Simple WebSocket client."""
    
    def __init__(self, url: str = "ws://localhost:8765"):
        """Initialize the WebSocket client."""
        self.url = url
        self.websocket = None
        self.connected = False
        self.received_messages = []
        
    async def connect(self):
        """Connect to the WebSocket server."""
        self.websocket = await websockets.connect(self.url)
        self.connected = True
        logger.info(f"Connected to {self.url}")
        
    async def disconnect(self):
        """Disconnect from the WebSocket server."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            self.connected = False
            logger.info("Disconnected from server")
            
    async def send_message(self, message: Dict[str, Any]):
        """Send a message to the server."""
        if not self.connected or not self.websocket:
            logger.warning("Cannot send message: not connected")
            return
            
        await self.websocket.send(json.dumps(message))
        logger.info(f"Sent message: {message}")
        
    async def send_text(self, text: str):
        """Send a text message to the server."""
        if not self.connected or not self.websocket:
            logger.warning("Cannot send message: not connected")
            return
            
        await self.websocket.send(text)
        logger.info(f"Sent text: {text}")
        
    async def receive_messages(self, timeout: float = 10.0):
        """Receive messages from the server."""
        if not self.connected or not self.websocket:
            logger.warning("Cannot receive messages: not connected")
            return
            
        try:
            # Set timeout for receiving messages
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    # Set per-message timeout
                    message = await asyncio.wait_for(self.websocket.recv(), 1.0)
                    
                    try:
                        # Try to parse as JSON
                        data = json.loads(message)
                        logger.info(f"Received message: {data}")
                        self.received_messages.append(data)
                    except json.JSONDecodeError:
                        # Handle as text
                        logger.info(f"Received text: {message}")
                        self.received_messages.append(message)
                        
                except asyncio.TimeoutError:
                    # Check if timeout expired
                    if time.time() - start_time >= timeout:
                        break
                    
                    # Continue waiting
                    continue
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Connection closed while receiving messages")
            self.connected = False
            self.websocket = None


async def run_client_test():
    """Run the WebSocket client test."""
    # Create client
    client = WebSocketClient("ws://localhost:8765")
    
    try:
        # Connect to server
        await client.connect()
        
        # Send ping message
        await client.send_message({
            "type": "ping",
            "timestamp": time.time()
        })
        
        # Wait for pong response
        await client.receive_messages(timeout=2.0)
        
        # Send test operation
        operation_id = f"test_{int(time.time())}"
        await client.send_message({
            "type": "test_operation",
            "operation_id": operation_id,
            "timestamp": time.time()
        })
        
        # Receive operation messages
        await client.receive_messages(timeout=5.0)
        
        # Send cancel operation
        await client.send_message({
            "type": "cancel_operation",
            "operation_id": operation_id,
            "timestamp": time.time()
        })
        
        # Receive cancellation message
        await client.receive_messages(timeout=2.0)
        
        # Analyze received messages
        message_types = [msg.get("type") if isinstance(msg, dict) else None 
                        for msg in client.received_messages]
        
        logger.info(f"Received message types: {message_types}")
        
        # Check for expected message types
        expected_types = ["pong", "operation_started", "progress_update", "operation_completed", "operation_canceled"]
        missing_types = [t for t in expected_types if t not in message_types]
        
        if missing_types:
            logger.warning(f"Missing expected message types: {missing_types}")
        else:
            logger.info("All expected message types were received!")
            
        return len(missing_types) == 0
        
    finally:
        # Disconnect
        await client.disconnect()


def main():
    """Main entry point."""
    try:
        # Run client test
        success = asyncio.run(run_client_test())
        
        if success:
            logger.info("WebSocket test completed successfully!")
            return 0
        else:
            logger.error("WebSocket test failed!")
            return 1
            
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Error running test: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())