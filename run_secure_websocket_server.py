#!/usr/bin/env python
"""
Secure WebSocket server launcher script for resilience testing.

This script starts a SecureProgressServer instance with TLS/SSL support.
It configures the server with appropriate settings and starts it in standalone mode.
"""

import os
import sys
import logging
import argparse
import asyncio
import signal
from typing import Dict, Any, Optional
from pathlib import Path

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# Import required modules
try:
    from rfm.core.logging_config import configure_logging, LogLevel, LogCategory
    from rfm.core.websocket_server_secure import SecureProgressServer, start_secure_websocket_server
except ImportError:
    print("Failed to import required modules. Make sure you're running this script from the project root.")
    sys.exit(1)

async def main(args):
    """
    Main entry point.
    
    Args:
        args: Command-line arguments
    """
    # Set up logging
    log_level_map = {
        "debug": LogLevel.DEBUG,
        "info": LogLevel.INFO,
        "warning": LogLevel.WARNING,
        "error": LogLevel.ERROR
    }
    log_level = log_level_map.get(args.log_level.lower(), LogLevel.INFO)
    
    # Create log directory
    log_dir = args.log_dir or "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    configure_logging(
        app_name="websocket_server_secure",
        log_dir=log_dir,
        console_level=log_level,
        file_level=LogLevel.DEBUG,
        json_format=True
    )
    
    # Create logger
    logger = logging.getLogger("websocket_server_secure")
    logger.info(f"Starting secure WebSocket server on {args.host}:{args.port}")
    
    # API keys for authentication
    api_keys = None
    if args.enable_auth:
        api_keys = {
            "test_client": "test_key_12345",
            "resilience_test_client": "test_key_67890"
        }
    
    # Create data directory if needed
    data_dir = args.data_dir or os.path.join(os.getcwd(), "data", "progress")
    os.makedirs(data_dir, exist_ok=True)
    
    # Verify SSL certificates
    ssl_cert_file = args.ssl_cert
    ssl_key_file = args.ssl_key
    
    if not ssl_cert_file or not ssl_key_file:
        # Try default locations
        tools_ssl_dir = os.path.join(script_dir, "tools", "ssl", "certs")
        
        if not ssl_cert_file and os.path.exists(os.path.join(tools_ssl_dir, "server.crt")):
            ssl_cert_file = os.path.join(tools_ssl_dir, "server.crt")
            
        if not ssl_key_file and os.path.exists(os.path.join(tools_ssl_dir, "server.key")):
            ssl_key_file = os.path.join(tools_ssl_dir, "server.key")
    
    if not ssl_cert_file or not ssl_key_file:
        logger.warning("SSL certificate or key file not provided. Generating self-signed certificates...")
        # Run the certificate generator
        ssl_dir = os.path.join(script_dir, "tools", "ssl")
        gen_script = os.path.join(ssl_dir, "generate_certs.sh")
        
        if os.path.exists(gen_script):
            logger.info("Running certificate generator...")
            os.chmod(gen_script, 0o755)  # Make executable
            exit_code = os.system(gen_script)
            
            if exit_code == 0:
                ssl_cert_file = os.path.join(ssl_dir, "certs", "server.crt")
                ssl_key_file = os.path.join(ssl_dir, "certs", "server.key")
                logger.info(f"Generated certificates: {ssl_cert_file}, {ssl_key_file}")
            else:
                logger.error(f"Certificate generation failed with exit code {exit_code}")
        else:
            logger.error(f"Certificate generator script not found: {gen_script}")
            logger.warning("Running without TLS/SSL")
            ssl_cert_file = None
            ssl_key_file = None
    
    # Define server config
    server_config = {
        "host": args.host,
        "port": args.port,
        "data_dir": data_dir,
        "log_dir": log_dir,
        "log_level": log_level,
        "connection_timeout": args.connection_timeout,
        "enable_authentication": args.enable_auth,
        "api_keys": api_keys,
        "ssl_cert_file": ssl_cert_file,
        "ssl_key_file": ssl_key_file,
        "client_auth": args.client_auth
    }
    
    # Set up signal handlers for graceful shutdown
    stop_event = asyncio.Event()

    def signal_handler():
        logger.info("Shutdown signal received")
        stop_event.set()

    # Register signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: signal_handler())
    
    try:
        # Start server
        server = await start_secure_websocket_server(**server_config)
        protocol = "wss" if ssl_cert_file and ssl_key_file else "ws"
        logger.info(f"WebSocket server started on {protocol}://{args.host}:{args.port}")
        
        # Wait for stop signal
        await stop_event.wait()
        
        # Stop the server
        logger.info("Stopping WebSocket server...")
        await server.stop()
        logger.info("WebSocket server stopped")
        
        return 0
    except Exception as e:
        logger.error(f"Error starting server: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run the secure WebSocket progress reporting server")
    
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8765, help="Server port")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"], help="Log level")
    parser.add_argument("--data-dir", help="Data directory for server")
    parser.add_argument("--log-dir", help="Log directory for server")
    parser.add_argument("--connection-timeout", type=float, default=300.0, help="Connection timeout in seconds")
    parser.add_argument("--enable-auth", action="store_true", help="Enable authentication")
    parser.add_argument("--ssl-cert", help="Path to SSL certificate file")
    parser.add_argument("--ssl-key", help="Path to SSL private key file")
    parser.add_argument("--client-auth", action="store_true", help="Require client certificate authentication")
    
    args = parser.parse_args()
    
    # Run the server
    exit_code = asyncio.run(main(args))
    sys.exit(exit_code)