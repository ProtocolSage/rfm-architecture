#!/usr/bin/env python
"""
Test script for the real-time progress reporting system.

This script runs the WebSocket server and simulates various operations to
demonstrate and test the progress reporting system.
"""

import os
import sys
import time
import asyncio
import threading
import random
import logging
import argparse
import uuid
import signal
from typing import Dict, Any, List, Optional, Set
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("progress_test.log")
    ]
)
logger = logging.getLogger("progress_test")

# Import components
try:
    from rfm.core.websocket_server import start_websocket_server
    from rfm.core.progress import ProgressReporter, get_progress_manager
except ImportError:
    logger.error("Failed to import required modules. Make sure you're running this script from the project root.")
    sys.exit(1)


async def run_server(host: str, port: int) -> None:
    """
    Run the WebSocket server.
    
    Args:
        host: Server hostname
        port: Server port
    """
    # Create data directory
    data_dir = Path("./data/progress")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up signal handlers for graceful shutdown
    stop_event = asyncio.Event()
    
    def signal_handler():
        logger.info("Shutdown signal received")
        stop_event.set()
    
    # Register signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        # Start WebSocket server
        server = await start_websocket_server(host, port)
        logger.info(f"WebSocket server started on {host}:{port}")
        
        # Wait for stop signal
        await stop_event.wait()
        
        # Stop server
        logger.info("Stopping WebSocket server...")
        await server.stop()
        logger.info("WebSocket server stopped")
        
    except Exception as e:
        logger.error(f"Error running WebSocket server: {e}", exc_info=True)


async def simulate_operation(name: str, duration: float, success_rate: float = 0.8) -> None:
    """
    Simulate an operation with progress reporting.
    
    Args:
        name: Operation name
        duration: Duration in seconds
        success_rate: Probability of success (0.0 to 1.0)
    """
    # Create progress reporter
    reporter = ProgressReporter(f"test_operation", name)
    
    # Get progress manager
    progress_manager = get_progress_manager()
    
    # Register operation
    await progress_manager.add_operation(reporter)
    
    try:
        # Calculate steps
        step_count = max(int(duration / 0.2), 5)  # At least 5 steps
        step_duration = duration / step_count
        
        # Start operation
        logger.info(f"Starting operation: {name}")
        reporter.report_progress(0, "Initializing...")
        
        # Simulate steps
        for step in range(1, step_count + 1):
            # Check for cancellation
            if reporter.should_cancel():
                logger.info(f"Operation canceled: {name}")
                reporter.report_canceled()
                return
                
            # Calculate progress percentage
            progress = step / step_count * 100
            
            # Simulate step execution
            await asyncio.sleep(step_duration)
            
            # Report progress
            reporter.report_progress(
                progress,
                f"Step {step}/{step_count}",
                current_step_progress=100,
                details={
                    "step": step,
                    "total_steps": step_count,
                    "timestamp": time.time()
                }
            )
            
        # Determine outcome
        if random.random() < success_rate:
            # Success
            logger.info(f"Operation completed: {name}")
            reporter.report_completed(details={"duration": duration})
        else:
            # Failure
            logger.info(f"Operation failed: {name}")
            error_message = random.choice([
                "Simulation error: Out of memory",
                "Simulation error: Timeout",
                "Simulation error: Invalid parameter",
                "Simulation error: Connection lost",
                "Simulation error: Unexpected condition"
            ])
            reporter.report_failed(error_message)
            
    except Exception as e:
        logger.error(f"Error in operation {name}: {e}")
        reporter.report_failed(str(e))


async def simulate_fractal_render(name: str, resolution: int, iterations: int) -> None:
    """
    Simulate a fractal rendering operation.
    
    Args:
        name: Operation name
        resolution: Image resolution
        iterations: Number of fractal iterations
    """
    # Create progress reporter
    reporter = ProgressReporter("fractal_render", name)
    
    # Get progress manager
    progress_manager = get_progress_manager()
    
    # Register operation
    await progress_manager.add_operation(reporter)
    
    try:
        # Calculate base duration based on parameters
        duration = (resolution / 100) * (iterations / 50) * 0.5  # seconds
        
        # Start operation
        logger.info(f"Starting fractal render: {name} ({resolution}x{resolution}, {iterations} iterations)")
        reporter.report_progress(0, "Initializing renderer...")
        
        # Simulate initialization
        await asyncio.sleep(0.5)
        
        # Simulate pixel calculation (rows of the image)
        row_count = resolution
        pixels_per_row = resolution
        total_pixels = resolution * resolution
        
        for row in range(row_count):
            # Check for cancellation
            if reporter.should_cancel():
                logger.info(f"Fractal render canceled: {name}")
                reporter.report_canceled()
                return
                
            # Calculate progress
            progress = (row / row_count) * 100
            pixels_done = row * pixels_per_row
            
            # Simulate row calculation
            row_duration = duration / row_count
            await asyncio.sleep(row_duration)
            
            # Report progress
            reporter.report_progress(
                progress,
                f"Calculating pixels ({pixels_done}/{total_pixels})",
                details={
                    "rows_completed": row,
                    "total_rows": row_count,
                    "pixels_calculated": pixels_done,
                    "total_pixels": total_pixels,
                    "resolution": resolution,
                    "iterations": iterations,
                    "timestamp": time.time()
                }
            )
            
        # Simulate post-processing
        reporter.report_progress(
            95,
            "Post-processing image...",
            details={"stage": "post-processing"}
        )
        
        await asyncio.sleep(0.5)
        
        # Complete operation
        logger.info(f"Fractal render completed: {name}")
        reporter.report_progress(
            100,
            "Render complete",
            details={"stage": "completed"}
        )
        
        reporter.report_completed(
            details={
                "duration": duration + 1.0,
                "resolution": resolution,
                "iterations": iterations,
                "pixels": total_pixels
            }
        )
            
    except Exception as e:
        logger.error(f"Error in fractal render {name}: {e}")
        reporter.report_failed(str(e))


async def simulate_operation_group(count: int, cancel_probability: float = 0.1) -> None:
    """
    Simulate a group of concurrent operations.
    
    Args:
        count: Number of operations to simulate
        cancel_probability: Probability of canceling an operation
    """
    # Create tasks
    tasks = []
    
    # Create operations
    for i in range(count):
        # Randomly choose operation type
        op_type = random.choice(["simple", "fractal"])
        
        if op_type == "simple":
            # Simple operation
            duration = random.uniform(3.0, 15.0)
            success_rate = random.uniform(0.7, 0.95)
            
            task = asyncio.create_task(
                simulate_operation(
                    f"Operation {i+1}",
                    duration,
                    success_rate
                )
            )
            
        else:
            # Fractal render
            resolution = random.choice([128, 256, 512, 1024])
            iterations = random.choice([50, 100, 200, 500])
            
            task = asyncio.create_task(
                simulate_fractal_render(
                    f"Fractal Render {i+1}",
                    resolution,
                    iterations
                )
            )
        
        tasks.append(task)
        
        # Stagger operation starts
        await asyncio.sleep(random.uniform(0.2, 2.0))
    
    # Wait for all operations to complete
    await asyncio.gather(*tasks)


async def run_simulation(args) -> None:
    """
    Run the simulation.
    
    Args:
        args: Command-line arguments
    """
    # Start server in a separate task
    server_task = asyncio.create_task(run_server(args.host, args.port))
    
    try:
        # Wait for server to start
        await asyncio.sleep(1)
        
        logger.info(f"Starting simulation with {args.operations} operations")
        
        # Run the specified number of simulation rounds
        for round_num in range(1, args.rounds + 1):
            logger.info(f"Starting simulation round {round_num}/{args.rounds}")
            
            # Simulate a group of operations
            await simulate_operation_group(args.operations, args.cancel_prob)
            
            # Wait between rounds
            if round_num < args.rounds:
                logger.info(f"Waiting {args.interval} seconds before next round")
                await asyncio.sleep(args.interval)
                
        logger.info("Simulation completed")
        
        # Wait for user to press Ctrl+C
        if args.wait:
            logger.info("Server is still running. Press Ctrl+C to exit.")
            try:
                # Wait indefinitely
                await asyncio.Future()
            except asyncio.CancelledError:
                pass
                
    except asyncio.CancelledError:
        logger.info("Simulation interrupted")
    finally:
        # Cancel server task
        server_task.cancel()
        
        try:
            await server_task
        except asyncio.CancelledError:
            pass


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test the real-time progress reporting system")
    
    parser.add_argument("--host", default="localhost", help="WebSocket server host")
    parser.add_argument("--port", type=int, default=8765, help="WebSocket server port")
    parser.add_argument("--operations", type=int, default=5, help="Number of concurrent operations per round")
    parser.add_argument("--rounds", type=int, default=1, help="Number of simulation rounds")
    parser.add_argument("--interval", type=int, default=5, help="Interval between rounds in seconds")
    parser.add_argument("--cancel-prob", type=float, default=0.1, help="Probability of canceling an operation")
    parser.add_argument("--wait", action="store_true", help="Keep server running after simulation")
    
    args = parser.parse_args()
    
    try:
        # Run simulation
        asyncio.run(run_simulation(args))
        return 0
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Error running test: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())