#!/usr/bin/env python
"""
Resilience test runner script.

This script runs the WebSocket resilience tests that verify the robustness
of the WebSocket-based progress reporting system under adverse conditions.
"""

import os
import sys
import logging
import argparse
import asyncio
import json
import time
import signal
from typing import Dict, Any, Optional, List
import subprocess
import importlib.util
from pathlib import Path

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

# Import resilience test module
try:
    from tests.resilience_test import (
        ResilienceTest, ConnectionResilienceTest, 
        OperationResilienceTest, LoadResilienceTest
    )
except ImportError:
    print("Failed to import resilience_test module. Make sure you're running this script from the project root.")
    sys.exit(1)

def setup_logging(log_level: str = "info") -> logging.Logger:
    """
    Set up logging for the resilience test runner.
    
    Args:
        log_level: Log level
        
    Returns:
        Logger instance
    """
    # Map string log level to logging constants
    log_level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR
    }
    level = log_level_map.get(log_level.lower(), logging.INFO)
    
    # Create log directory
    log_dir = os.path.join(parent_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    log_file = os.path.join(log_dir, f"resilience_test_{time.strftime('%Y%m%d_%H%M%S')}.log")
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )
    
    return logging.getLogger("resilience_test_runner")

async def start_server(host: str, port: int, enable_auth: bool) -> subprocess.Popen:
    """
    Start the WebSocket server in a separate process.
    
    Args:
        host: Server host
        port: Server port
        enable_auth: Enable authentication
        
    Returns:
        Server process
    """
    # Build command
    cmd = [
        sys.executable,
        os.path.join(parent_dir, "run_websocket_server.py"),
        f"--host={host}",
        f"--port={port}",
        "--log-level=debug"
    ]
    
    if enable_auth:
        cmd.append("--enable-auth")
    
    # Start server process
    server_process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    
    # Wait for server to start
    await asyncio.sleep(2)
    
    return server_process

def stop_server(server_process: subprocess.Popen) -> None:
    """
    Stop the WebSocket server process.
    
    Args:
        server_process: Server process
    """
    if server_process:
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()

async def run_tests(args) -> int:
    """
    Run the resilience tests.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Set up logging
    logger = setup_logging(args.log_level)
    logger.info("Starting resilience tests")
    
    # Start server if requested
    server_process = None
    if args.start_server:
        logger.info(f"Starting WebSocket server on {args.host}:{args.port}")
        server_process = await start_server(args.host, args.port, args.enable_auth)
    
    try:
        # Create report directory
        report_dir = os.path.join(parent_dir, "reports")
        os.makedirs(report_dir, exist_ok=True)
        
        # Configure authentication if needed
        authentication = None
        if args.enable_auth:
            authentication = {
                "client_id": "resilience_test_client",
                "token": "test_key_67890"
            }
        
        # Common test parameters
        test_params = {
            "server_host": args.host,
            "server_port": args.port,
            "authentication": authentication,
            "duration": args.duration,
            "concurrency": args.concurrency,
            "report_dir": report_dir
        }
        
        # Run selected tests
        results = []
        
        if "connection" in args.tests:
            logger.info("Running connection resilience test")
            connection_test = ConnectionResilienceTest(
                **test_params,
                name="connection_resilience",
                description="Tests client reconnection capabilities during server restarts",
                restart_count=args.restart_count,
                restart_interval=args.restart_interval
            )
            results.append(await connection_test.run())
        
        if "operation" in args.tests:
            logger.info("Running operation resilience test")
            operation_test = OperationResilienceTest(
                **test_params,
                name="operation_resilience",
                description="Tests operation state preservation during connection disruptions",
                operation_count=args.operation_count
            )
            results.append(await operation_test.run())
        
        if "load" in args.tests:
            logger.info("Running load resilience test")
            load_test = LoadResilienceTest(
                **test_params,
                name="load_resilience",
                description="Tests system behavior under high load",
                client_count=args.client_count,
                operations_per_client=args.operations_per_client
            )
            results.append(await load_test.run())
        
        # Generate summary report
        summary = {
            "timestamp": time.time(),
            "config": vars(args),
            "tests": len(results),
            "passed": sum(1 for r in results if r.get("status") == "passed"),
            "failed": sum(1 for r in results if r.get("status") == "failed"),
            "results": results
        }
        
        # Save summary report
        summary_file = os.path.join(
            report_dir, 
            f"resilience_test_summary_{time.strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)
            
        # Print summary
        logger.info(f"Tests completed: {summary['tests']} total, {summary['passed']} passed, {summary['failed']} failed")
        logger.info(f"Report saved to {summary_file}")
        
        # Return success if all tests passed
        return 0 if summary["failed"] == 0 else 1
        
    except Exception as e:
        logger.error(f"Error running resilience tests: {e}", exc_info=True)
        return 1
    finally:
        # Stop server if we started it
        if server_process:
            logger.info("Stopping WebSocket server")
            stop_server(server_process)

def main():
    """Main entry point."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run WebSocket resilience tests")
    
    # Server options
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8765, help="Server port")
    parser.add_argument("--start-server", action="store_true", help="Start server for testing")
    parser.add_argument("--enable-auth", action="store_true", help="Enable authentication")
    
    # Test selection and options
    parser.add_argument("--tests", nargs="+", default=["connection", "operation", "load"],
                      choices=["connection", "operation", "load", "all"],
                      help="Tests to run")
    parser.add_argument("--duration", type=float, default=60.0, help="Test duration in seconds")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"], 
                      help="Log level")
    
    # Connection test options
    parser.add_argument("--restart-count", type=int, default=3, help="Number of server restarts")
    parser.add_argument("--restart-interval", type=float, default=10.0, help="Interval between restarts")
    
    # Operation test options
    parser.add_argument("--operation-count", type=int, default=5, help="Number of operations to test")
    
    # Load test options
    parser.add_argument("--client-count", type=int, default=10, help="Number of clients for load testing")
    parser.add_argument("--operations-per-client", type=int, default=3, 
                      help="Operations per client for load testing")
    parser.add_argument("--concurrency", type=int, default=5, 
                      help="Maximum concurrent operations")
    
    args = parser.parse_args()
    
    # Transform 'all' to all test types
    if "all" in args.tests:
        args.tests = ["connection", "operation", "load"]
    
    # Run tests
    exit_code = asyncio.run(run_tests(args))
    sys.exit(exit_code)

if __name__ == "__main__":
    main()