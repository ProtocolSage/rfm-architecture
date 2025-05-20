#!/usr/bin/env python
"""
Production-ready WebSocket server for RFM Architecture.

This script launches a production-ready WebSocket server with:
- TLS/SSL encryption
- JWT authentication
- Rate limiting
- Resource monitoring
- Comprehensive logging
"""

import os
import sys
import logging
import argparse
import asyncio
import signal
import json
from typing import Dict, Any, Optional
from pathlib import Path

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
# Ensure structured logger class is used for module-level loggers before importing modules
sys.path.insert(0, script_dir)
try:
    from rfm.core.logging_config import StructuredLogger
    import logging as _logging_setup
    _logging_setup.setLoggerClass(StructuredLogger)
except Exception:
    pass

# Import required modules
try:
    from rfm.core.logging_config import configure_logging, LogLevel, LogCategory
    from rfm.core.websocket_server_secure import SecureProgressServer, start_secure_websocket_server
    from rfm.core.auth import JWTAuthenticator, set_authenticator
    from rfm.core.rate_limiting import (
        RateLimiter, RateLimitRule, RateLimitScope, set_rate_limiter
    )
except ImportError:
    print("Failed to import required modules. Make sure you're running this script from the project root.")
    sys.exit(1)

def load_config(config_file: str) -> Dict[str, Any]:
    """
    Load server configuration from a JSON file.
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    if not os.path.exists(config_file):
        print(f"Configuration file not found: {config_file}")
        print("Using default configuration.")
        return {}
        
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"Error loading configuration file: {e}")
        print("Using default configuration.")
        return {}

def setup_rate_limiting(config: Dict[str, Any]) -> None:
    """
    Set up rate limiting from configuration.
    
    Args:
        config: Configuration dictionary
    """
    # Rebind rate_limiting module logger to StructuredLogger (post-configure)
    from rfm.core.logging_config import get_logger
    import rfm.core.rate_limiting as rlmod
    rlmod.logger = get_logger(rlmod.__name__)
    rate_limit_config = config.get("rate_limiting", {})
    rules = []
    
    # Create rate limit rules from configuration
    for rule_config in rate_limit_config.get("rules", []):
        try:
            rule = RateLimitRule(
                name=rule_config["name"],
                requests=rule_config["requests"],
                period=rule_config["period"],
                scope=RateLimitScope(rule_config["scope"]),
                actions=rule_config.get("actions", []),
                response_code=rule_config.get("response_code", 429),
                response_message=rule_config.get("response_message", "Rate limit exceeded")
            )
            rules.append(rule)
        except (KeyError, ValueError) as e:
            print(f"Error creating rate limit rule: {e}")
    
    # If no rules defined in config, use default rules
    if not rules:
        rules = [
            RateLimitRule(
                name="connection_per_ip",
                requests=10,
                period=60,  # 1 minute
                scope=RateLimitScope.IP
            ),
            RateLimitRule(
                name="operations_per_client",
                requests=20,
                period=60,  # 1 minute
                scope=RateLimitScope.CLIENT,
                actions=["start_render", "start_operation"]
            ),
            RateLimitRule(
                name="global_operations",
                requests=50,
                period=60,  # 1 minute
                scope=RateLimitScope.GLOBAL,
                actions=["start_render", "start_operation"]
            )
        ]
    
    # Create and set rate limiter
    rate_limiter = RateLimiter(rules)
    set_rate_limiter(rate_limiter)

def setup_authentication(config: Dict[str, Any]) -> None:
    """
    Set up JWT authentication from configuration.
    
    Args:
        config: Configuration dictionary
    """
    auth_config = config.get("authentication", {})
    
    # Determine secret key: direct or from file
    secret_key = auth_config.get("secret_key")
    jwt_key_path = auth_config.get("jwt_secret_key_path")
    if not secret_key and jwt_key_path:
        try:
            with open(jwt_key_path, 'r') as f:
                secret_key = f.read().strip()
        except Exception as e:
            print(f"Could not read JWT secret key file {jwt_key_path}: {e}")
    # Create JWT authenticator
    authenticator = JWTAuthenticator(
        secret_key=secret_key,
        algorithm=auth_config.get("algorithm", "HS256"),
        token_expiry=auth_config.get("token_expiry", 3600),
        refresh_expiry=auth_config.get("refresh_expiry", 86400),
        audience=auth_config.get("audience"),
        issuer=auth_config.get("issuer"),
        required_claims=auth_config.get("required_claims"),
        env_secret_key=auth_config.get("env_secret_key", "JWT_SECRET_KEY")
    )
    
    # Set global authenticator
    set_authenticator(authenticator)

async def setup_resource_monitoring(config: Dict[str, Any], server_process_id: int) -> asyncio.Task:
    """
    Set up resource monitoring task.
    
    Args:
        config: Configuration dictionary
        server_process_id: Server process ID
        
    Returns:
        Monitoring task
    """
    monitor_config = config.get("monitoring", {})
    interval = monitor_config.get("interval", 60)  # Default to 60 seconds
    
    async def monitor_resources():
        while True:
            try:
                # Import here to avoid circular import
                from tools.monitor_resources import ResourceMonitor
                
                # Create monitor for this process
                monitor = ResourceMonitor(
                    process_name="python",
                    port=args.port,
                    output_dir=os.path.join(script_dir, "reports", "resources")
                )
                
                # Collect a single sample
                if hasattr(monitor, "collect_sample"):
                    import psutil
                    process = psutil.Process(server_process_id)
                    cpu, memory, sockets = monitor.collect_sample(process)
                    
                    # Log resource usage
                    logging.info(
                        f"Resource usage - CPU: {cpu:.1f}%, Memory: {memory:.1f}MB, Sockets: {sockets}"
                    )
            except ImportError:
                logging.warning("ResourceMonitor not available for monitoring")
                break
            except Exception as e:
                logging.error(f"Error monitoring resources: {e}")
                
            # Wait before next check
            await asyncio.sleep(interval)
    
    # Start monitoring task
    return asyncio.create_task(monitor_resources())

async def main(args):
    """
    Main entry point.
    
    Args:
        args: Command-line arguments
    """
    # Load configuration
    config = {}
    if args.config:
        config = load_config(args.config)
    
    # Set up logging
    log_level_map = {
        "debug": LogLevel.DEBUG,
        "info": LogLevel.INFO,
        "warning": LogLevel.WARNING,
        "error": LogLevel.ERROR
    }
    log_level = log_level_map.get(args.log_level.lower(), LogLevel.INFO)
    
    # Create log directory
    log_dir = args.log_dir or config.get("log_dir") or "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    configure_logging(
        app_name="websocket_server_production",
        log_dir=log_dir,
        console_level=log_level,
        file_level=LogLevel.DEBUG,
        json_format=True
    )
    
    # Create logger
    logger = logging.getLogger("websocket_server_production")
    logger.info(f"Starting production WebSocket server on {args.host}:{args.port}")
    
    # Set up rate limiting
    try:
        setup_rate_limiting(config)
    except Exception as e:
        logger = logging.getLogger("websocket_server_production")
        logger.warning(f"Skipping rate limiting due to error: {e}")
    
    # Set up authentication
    try:
        setup_authentication(config)
    except Exception as e:
        logger = logging.getLogger("websocket_server_production")
        logger.warning(f"Skipping authentication due to error: {e}")
    
    # API keys for authentication
    api_keys = None
    if args.enable_auth:
        api_keys = config.get("api_keys", {
            "test_client": "test_key_12345",
            "resilience_test_client": "test_key_67890"
        })
    
    # Create data directory if needed
    data_dir = args.data_dir or config.get("data_dir") or os.path.join(os.getcwd(), "data", "progress")
    os.makedirs(data_dir, exist_ok=True)
    
    # Set up SSL certificates
    ssl_cert_file = args.ssl_cert or config.get("ssl_cert_file")
    ssl_key_file = args.ssl_key or config.get("ssl_key_file")
    
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
    monitoring_task = None

    def signal_handler():
        logger.info("Shutdown signal received")
        stop_event.set()
        if monitoring_task:
            monitoring_task.cancel()

    # Register signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: signal_handler())
    
    try:
        # Start server
        server = await start_secure_websocket_server(**server_config)
        protocol = "wss" if ssl_cert_file and ssl_key_file else "ws"
        logger.info(f"WebSocket server started on {protocol}://{args.host}:{args.port}")
        
        # Start resource monitoring if enabled
        if args.monitor_resources:
            server_process_id = os.getpid()
            monitoring_task = await setup_resource_monitoring(config, server_process_id)
        
        # Wait for stop signal
        await stop_event.wait()
        
        # Stop the server
        logger.info("Stopping WebSocket server...")
        await server.stop()
        
        # Stop monitoring task if running
        if monitoring_task and not monitoring_task.done():
            monitoring_task.cancel()
            try:
                await monitoring_task
            except asyncio.CancelledError:
                pass
                
        logger.info("WebSocket server stopped")
        
        return 0
    except Exception as e:
        logger.error(f"Error starting server: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run the production WebSocket server")
    
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=8765, help="Server port")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"], help="Log level")
    parser.add_argument("--data-dir", help="Data directory for server")
    parser.add_argument("--log-dir", help="Log directory for server")
    parser.add_argument("--connection-timeout", type=float, default=300.0, help="Connection timeout in seconds")
    parser.add_argument("--enable-auth", action="store_true", help="Enable authentication")
    parser.add_argument("--ssl-cert", help="Path to SSL certificate file")
    parser.add_argument("--ssl-key", help="Path to SSL private key file")
    parser.add_argument("--client-auth", action="store_true", help="Require client certificate authentication")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--monitor-resources", action="store_true", help="Enable resource monitoring")
    
    args = parser.parse_args()
    
    # Run the server
    exit_code = asyncio.run(main(args))
    sys.exit(exit_code)