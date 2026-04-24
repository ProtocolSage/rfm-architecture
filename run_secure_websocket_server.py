#!/usr/bin/env python
"""Secure WebSocket server launcher.

Runs a SecureProgressServer with TLS/SSL. Production-grade add-ons — JSON
config loading, JWT authentication, rate limiting, and resource monitoring —
are opt-in via ``--config`` / ``--monitor-resources``. When those flags are
absent, the behaviour matches a plain secure launcher.
"""

import os
import sys
import json
import logging
import argparse
import asyncio
import signal
from typing import Dict, Any, Optional
from pathlib import Path

script_dir = os.path.dirname(os.path.abspath(__file__))

# Import required modules (importing rfm registers StructuredLogger as the
# default logger class; see rfm/__init__.py).
try:
    from rfm.core.logging_config import configure_logging, LogLevel, LogCategory
    from rfm.core.websocket_server_secure import (
        SecureProgressServer, start_secure_websocket_server,
    )
    from rfm.core.auth import JWTAuthenticator, set_authenticator
    from rfm.core.rate_limiting import (
        RateLimiter, RateLimitRule, RateLimitScope, set_rate_limiter,
    )
except ImportError:
    print("Failed to import required modules. Make sure you're running this script from the project root.")
    sys.exit(1)


def load_config(config_file: str) -> Dict[str, Any]:
    """Load server configuration from a JSON file; return {} on any failure."""
    if not os.path.exists(config_file):
        print(f"Configuration file not found: {config_file}; using defaults.")
        return {}
    try:
        with open(config_file, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading configuration file: {e}; using defaults.")
        return {}


def setup_rate_limiting(config: Dict[str, Any]) -> None:
    """Install a RateLimiter from ``config['rate_limiting']`` (or sensible defaults)."""
    rate_limit_config = config.get("rate_limiting", {})
    rules = []
    for rule_config in rate_limit_config.get("rules", []):
        try:
            rules.append(RateLimitRule(
                name=rule_config["name"],
                requests=rule_config["requests"],
                period=rule_config["period"],
                scope=RateLimitScope(rule_config["scope"]),
                actions=rule_config.get("actions", []),
                response_code=rule_config.get("response_code", 429),
                response_message=rule_config.get("response_message", "Rate limit exceeded"),
            ))
        except (KeyError, ValueError) as e:
            print(f"Error creating rate limit rule: {e}")

    if not rules:
        rules = [
            RateLimitRule(name="connection_per_ip", requests=10, period=60, scope=RateLimitScope.IP),
            RateLimitRule(
                name="operations_per_client", requests=20, period=60,
                scope=RateLimitScope.CLIENT, actions=["start_render", "start_operation"],
            ),
            RateLimitRule(
                name="global_operations", requests=50, period=60,
                scope=RateLimitScope.GLOBAL, actions=["start_render", "start_operation"],
            ),
        ]

    set_rate_limiter(RateLimiter(rules))


def setup_authentication(config: Dict[str, Any]) -> None:
    """Install a JWTAuthenticator from ``config['authentication']``."""
    auth_config = config.get("authentication", {})
    secret_key = auth_config.get("secret_key")
    jwt_key_path = auth_config.get("jwt_secret_key_path")
    if not secret_key and jwt_key_path:
        try:
            with open(jwt_key_path, "r") as f:
                secret_key = f.read().strip()
        except Exception as e:
            print(f"Could not read JWT secret key file {jwt_key_path}: {e}")

    set_authenticator(JWTAuthenticator(
        secret_key=secret_key,
        algorithm=auth_config.get("algorithm", "HS256"),
        token_expiry=auth_config.get("token_expiry", 3600),
        refresh_expiry=auth_config.get("refresh_expiry", 86400),
        audience=auth_config.get("audience"),
        issuer=auth_config.get("issuer"),
        required_claims=auth_config.get("required_claims"),
        env_secret_key=auth_config.get("env_secret_key", "JWT_SECRET_KEY"),
    ))


async def setup_resource_monitoring(
    config: Dict[str, Any],
    server_process_id: int,
    server_port: int,
    logger: logging.Logger,
) -> asyncio.Task:
    """Start a background task that periodically samples CPU/mem/sockets."""
    monitor_config = config.get("monitoring", {})
    interval = monitor_config.get("interval", 60)

    async def monitor_resources():
        while True:
            try:
                from tools.monitor_resources import ResourceMonitor
                monitor = ResourceMonitor(
                    process_name="python",
                    port=server_port,
                    output_dir=os.path.join(script_dir, "reports", "resources"),
                )
                if hasattr(monitor, "collect_sample"):
                    import psutil
                    process = psutil.Process(server_process_id)
                    cpu, memory, sockets = monitor.collect_sample(process)
                    logger.info(
                        f"Resource usage - CPU: {cpu:.1f}%, Memory: {memory:.1f}MB, Sockets: {sockets}"
                    )
            except ImportError:
                logger.warning("ResourceMonitor not available for monitoring")
                break
            except Exception as e:
                logger.error(f"Error monitoring resources: {e}")
            await asyncio.sleep(interval)

    return asyncio.create_task(monitor_resources())


def _resolve_ssl_paths(args, config: Dict[str, Any], logger: logging.Logger):
    """Pick SSL cert+key from args, config, or tools/ssl/certs defaults.

    If nothing resolves, attempt ``tools/ssl/generate_certs.sh`` and re-check.
    Falls back to plain ``ws://`` (returns ``(None, None)``) on failure.
    """
    ssl_cert_file = args.ssl_cert or config.get("ssl_cert_file")
    ssl_key_file = args.ssl_key or config.get("ssl_key_file")

    if not ssl_cert_file or not ssl_key_file:
        tools_ssl_dir = os.path.join(script_dir, "tools", "ssl", "certs")
        if not ssl_cert_file and os.path.exists(os.path.join(tools_ssl_dir, "server.crt")):
            ssl_cert_file = os.path.join(tools_ssl_dir, "server.crt")
        if not ssl_key_file and os.path.exists(os.path.join(tools_ssl_dir, "server.key")):
            ssl_key_file = os.path.join(tools_ssl_dir, "server.key")

    if not ssl_cert_file or not ssl_key_file:
        logger.warning("SSL cert/key not provided; attempting to generate self-signed certs...")
        ssl_dir = os.path.join(script_dir, "tools", "ssl")
        gen_script = os.path.join(ssl_dir, "generate_certs.sh")
        if os.path.exists(gen_script):
            os.chmod(gen_script, 0o755)
            exit_code = os.system(gen_script)
            if exit_code == 0:
                ssl_cert_file = os.path.join(ssl_dir, "certs", "server.crt")
                ssl_key_file = os.path.join(ssl_dir, "certs", "server.key")
                logger.info(f"Generated certificates: {ssl_cert_file}, {ssl_key_file}")
            else:
                logger.error(f"Certificate generation failed with exit code {exit_code}")
                ssl_cert_file = ssl_key_file = None
        else:
            logger.error(f"Certificate generator script not found: {gen_script}")
            logger.warning("Running without TLS/SSL")
            ssl_cert_file = ssl_key_file = None

    return ssl_cert_file, ssl_key_file


async def main(args):
    config: Dict[str, Any] = load_config(args.config) if args.config else {}

    log_level_map = {
        "debug": LogLevel.DEBUG,
        "info": LogLevel.INFO,
        "warning": LogLevel.WARNING,
        "error": LogLevel.ERROR,
    }
    log_level = log_level_map.get(args.log_level.lower(), LogLevel.INFO)
    log_dir = args.log_dir or config.get("log_dir") or "logs"
    os.makedirs(log_dir, exist_ok=True)

    app_name = "websocket_server_production" if args.config else "websocket_server_secure"
    configure_logging(
        app_name=app_name,
        log_dir=log_dir,
        console_level=log_level,
        file_level=LogLevel.DEBUG,
        json_format=True,
    )
    logger = logging.getLogger(app_name)
    logger.info(f"Starting secure WebSocket server on {args.host}:{args.port}")

    # Optional production-grade add-ons. Activated when a config file is
    # supplied (authentication + rate limiting) or --enable-auth is set.
    if args.config:
        try:
            setup_rate_limiting(config)
        except Exception as e:
            logger.warning(f"Skipping rate limiting due to error: {e}")
        try:
            setup_authentication(config)
        except Exception as e:
            logger.warning(f"Skipping authentication due to error: {e}")

    api_keys = None
    if args.enable_auth:
        api_keys = config.get("api_keys") or {
            "test_client": "test_key_12345",
            "resilience_test_client": "test_key_67890",
        }

    data_dir = args.data_dir or config.get("data_dir") or os.path.join(os.getcwd(), "data", "progress")
    os.makedirs(data_dir, exist_ok=True)

    ssl_cert_file, ssl_key_file = _resolve_ssl_paths(args, config, logger)

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
        "client_auth": args.client_auth,
    }

    stop_event = asyncio.Event()
    monitoring_task: Optional[asyncio.Task] = None

    def signal_handler():
        logger.info("Shutdown signal received")
        stop_event.set()
        if monitoring_task and not monitoring_task.done():
            monitoring_task.cancel()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: signal_handler())

    try:
        server = await start_secure_websocket_server(**server_config)
        protocol = "wss" if ssl_cert_file and ssl_key_file else "ws"
        logger.info(f"WebSocket server started on {protocol}://{args.host}:{args.port}")

        if args.monitor_resources:
            monitoring_task = await setup_resource_monitoring(
                config, os.getpid(), args.port, logger,
            )

        await stop_event.wait()

        logger.info("Stopping WebSocket server...")
        await server.stop()

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
    parser = argparse.ArgumentParser(description="Run the secure WebSocket progress reporting server")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8765, help="Server port")
    parser.add_argument(
        "--log-level", default="info",
        choices=["debug", "info", "warning", "error"], help="Log level",
    )
    parser.add_argument("--data-dir", help="Data directory for server")
    parser.add_argument("--log-dir", help="Log directory for server")
    parser.add_argument("--connection-timeout", type=float, default=300.0, help="Connection timeout in seconds")
    parser.add_argument("--enable-auth", action="store_true", help="Enable authentication")
    parser.add_argument("--ssl-cert", help="Path to SSL certificate file")
    parser.add_argument("--ssl-key", help="Path to SSL private key file")
    parser.add_argument("--client-auth", action="store_true", help="Require client certificate authentication")
    parser.add_argument(
        "--config",
        help="Optional JSON config file enabling production add-ons (rate limiting, JWT auth).",
    )
    parser.add_argument(
        "--monitor-resources", action="store_true",
        help="Periodically sample CPU/memory/sockets of the server process.",
    )
    args = parser.parse_args()

    exit_code = asyncio.run(main(args))
    sys.exit(exit_code)
