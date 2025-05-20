"""
Secure WebSocket server for real-time progress reporting.

This module provides a secure version of the WebSocket server with TLS/SSL support
for encrypted connections.
"""

import asyncio
import json
import logging
import os
import signal
import ssl
import sys
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Union, Callable, Tuple

import websockets

from .logging_config import (
    get_logger, configure_logging, LogLevel, LogCategory, log_timing, TimingContext
)
from .monitoring import (
    get_metrics_registry, get_connection_monitor,
    MetricType, HealthStatus, ConnectionMonitor
)
from .websocket_server_enhanced import (
    ProgressServer as BaseProgressServer,
    MessageType, ClientInfo
)


# Configure logger
logger = get_logger(__name__)


class SecureProgressServer(BaseProgressServer):
    """
    Secure WebSocket server for progress reporting with TLS/SSL support.
    
    This extends the enhanced WebSocket server with:
    - TLS/SSL encryption
    - Certificate management
    - Additional security measures
    """
    
    def __init__(self, 
                host: str = "localhost", 
                port: int = 8765,
                data_dir: Optional[str] = None,
                log_dir: Optional[str] = None,
                log_level: LogLevel = LogLevel.INFO,
                connection_timeout: float = 300.0,
                message_rate_limit: int = 100,
                enable_authentication: bool = False,
                api_keys: Optional[Dict[str, str]] = None,
                ssl_cert_file: Optional[str] = None,
                ssl_key_file: Optional[str] = None,
                client_auth: bool = False):
        """
        Initialize the secure progress server.
        
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
            ssl_cert_file: Path to SSL certificate file
            ssl_key_file: Path to SSL private key file
            client_auth: Whether to require client certificate authentication
        """
        # Initialize base server
        super().__init__(
            host=host,
            port=port,
            data_dir=data_dir,
            log_dir=log_dir,
            log_level=log_level,
            connection_timeout=connection_timeout,
            message_rate_limit=message_rate_limit,
            enable_authentication=enable_authentication,
            api_keys=api_keys
        )
        
        # SSL configuration
        self.ssl_cert_file = ssl_cert_file
        self.ssl_key_file = ssl_key_file
        self.client_auth = client_auth
        self.ssl_context = None
        
        # Create SSL context if certificates provided
        if ssl_cert_file and ssl_key_file:
            self._create_ssl_context()
            
        logger.structured_log(
            LogLevel.INFO,
            "Initialized secure progress reporting WebSocket server",
            LogCategory.SYSTEM,
            component="websocket_server_secure",
            context={
                "host": host,
                "port": port,
                "ssl_enabled": bool(self.ssl_context),
                "client_auth": client_auth,
                "server_id": self.server_id
            }
        )
        
    def _create_ssl_context(self) -> None:
        """Create SSL context for secure WebSocket connections."""
        try:
            # Validate certificate files
            if not os.path.exists(self.ssl_cert_file):
                raise FileNotFoundError(f"SSL certificate file not found: {self.ssl_cert_file}")
                
            if not os.path.exists(self.ssl_key_file):
                raise FileNotFoundError(f"SSL key file not found: {self.ssl_key_file}")
                
            # Create SSL context
            self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            
            # Load certificate and key
            self.ssl_context.load_cert_chain(
                self.ssl_cert_file,
                self.ssl_key_file
            )
            
            # Configure security settings
            self.ssl_context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1  # Disable old TLS versions
            self.ssl_context.set_ciphers('ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384')
            
            # Set to verify client certificate if client_auth is True
            if self.client_auth:
                self.ssl_context.verify_mode = ssl.CERT_REQUIRED
                self.ssl_context.load_verify_locations(cafile=self.ssl_cert_file)
                
            logger.structured_log(
                LogLevel.INFO,
                "SSL context created successfully",
                LogCategory.SECURITY,
                component="websocket_server_secure",
                context={
                    "cert_file": self.ssl_cert_file,
                    "client_auth": self.client_auth,
                    "server_id": self.server_id
                }
            )
            
        except Exception as e:
            logger.structured_log(
                LogLevel.ERROR,
                f"Failed to create SSL context: {e}",
                LogCategory.SECURITY,
                component="websocket_server_secure",
                context={"server_id": self.server_id},
                error=str(e)
            )
            self.ssl_context = None
            
    @log_timing("start_secure_server", LogLevel.INFO, LogCategory.SYSTEM, "websocket_server_secure")
    async def start(self) -> None:
        """
        Start the secure WebSocket server.
        
        Returns:
            Server instance
        """
        # Register health check
        self.metrics_registry.register_health_check(
            "websocket_server_secure",
            HealthStatus.HEALTHY,
            {"server_id": self.server_id}
        )
        
        # Start connection monitor
        self.connection_monitor.start()
        
        # Start server
        logger.structured_log(
            LogLevel.INFO,
            f"Starting secure WebSocket server on {'wss' if self.ssl_context else 'ws'}://{self.host}:{self.port}",
            LogCategory.SYSTEM,
            component="websocket_server_secure",
            context={"server_id": self.server_id}
        )
        
        try:
            # Create WebSocket server with SSL context if available
            self.server = await websockets.serve(
                self._handle_client,
                self.host,
                self.port,
                process_request=self._process_request,
                ssl=self.ssl_context
            )
            
            # Reset stop event
            self.stop_event.clear()
            
            # Start periodic tasks
            asyncio.create_task(self._periodic_cleanup())
            
            # Log successful start
            protocol = "wss" if self.ssl_context else "ws"
            logger.structured_log(
                LogLevel.INFO,
                f"Secure WebSocket server started on {protocol}://{self.host}:{self.port}",
                LogCategory.SYSTEM,
                component="websocket_server_secure",
                context={"server_id": self.server_id}
            )
            
            # Update metrics
            self.metrics_registry.register_health_check(
                "websocket_server_secure",
                HealthStatus.HEALTHY,
                {"server_id": self.server_id, "status": "running"}
            )
            
            return self
            
        except Exception as e:
            logger.structured_log(
                LogLevel.ERROR,
                f"Failed to start secure WebSocket server: {e}",
                LogCategory.SYSTEM,
                component="websocket_server_secure",
                context={"server_id": self.server_id},
                error=str(e)
            )
            
            # Update metrics
            self.metrics_registry.register_health_check(
                "websocket_server_secure",
                HealthStatus.UNHEALTHY,
                {"server_id": self.server_id, "error": str(e)}
            )
            
            # Propagate exception
            raise


# Global server instance
_secure_server_instance: Optional[SecureProgressServer] = None


async def start_secure_websocket_server(
    host: str = "localhost",
    port: int = 8765,
    data_dir: Optional[str] = None,
    log_dir: Optional[str] = None,
    log_level: LogLevel = LogLevel.INFO,
    connection_timeout: float = 300.0,
    enable_authentication: bool = False,
    api_keys: Optional[Dict[str, str]] = None,
    ssl_cert_file: Optional[str] = None,
    ssl_key_file: Optional[str] = None,
    client_auth: bool = False
) -> SecureProgressServer:
    """
    Start a secure WebSocket server for progress reporting.
    
    Args:
        host: Server hostname
        port: Server port
        data_dir: Directory for data storage
        log_dir: Directory for logs
        log_level: Log level
        connection_timeout: Timeout for inactive connections
        enable_authentication: Whether to enable API key authentication
        api_keys: Dictionary of API keys (client_id -> api_key)
        ssl_cert_file: Path to SSL certificate file
        ssl_key_file: Path to SSL private key file
        client_auth: Whether to require client certificate authentication
        
    Returns:
        SecureProgressServer instance
    """
    global _secure_server_instance
    
    # Create server if needed
    if _secure_server_instance is None:
        _secure_server_instance = SecureProgressServer(
            host=host,
            port=port,
            data_dir=data_dir,
            log_dir=log_dir,
            log_level=log_level,
            connection_timeout=connection_timeout,
            enable_authentication=enable_authentication,
            api_keys=api_keys,
            ssl_cert_file=ssl_cert_file,
            ssl_key_file=ssl_key_file,
            client_auth=client_auth
        )
        
        # Start server
        await _secure_server_instance.start()
        
        # Store start time
        _secure_server_instance.start_time = time.time()
        
    return _secure_server_instance


async def stop_secure_websocket_server() -> None:
    """Stop the secure WebSocket server."""
    global _secure_server_instance
    
    if _secure_server_instance:
        await _secure_server_instance.stop()
        _secure_server_instance = None


def get_secure_server_instance() -> Optional[SecureProgressServer]:
    """
    Get the global secure server instance.
    
    Returns:
        SecureProgressServer instance, or None if not started
    """
    global _secure_server_instance
    return _secure_server_instance