#!/usr/bin/env python
"""
WebSocket Performance Benchmark.

This script benchmarks the performance of the WebSocket-based progress reporting
system, measuring message throughput, latency, and resource usage under various
loads.
"""

import os
import sys
import time
import asyncio
import threading
import logging
import argparse
import json
import uuid
import statistics
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import psutil
import matplotlib.pyplot as plt
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("websocket_benchmark.log")
    ]
)
logger = logging.getLogger("websocket_benchmark")

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

# Import components to test
try:
    from rfm.core.websocket_server import start_websocket_server
    from rfm.core.progress import ProgressReporter, get_progress_manager
    from ui.rfm_ui.websocket_client import get_websocket_client, WebSocketClient
except ImportError:
    logger.error("Failed to import required modules. Make sure you're running this script from the project root.")
    sys.exit(1)


@dataclass
class BenchmarkResult:
    """Benchmark result data."""
    
    operation_count: int
    message_count: int
    duration_seconds: float
    messages_per_second: float
    avg_latency_ms: float
    max_latency_ms: float
    min_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    cpu_percent: float
    memory_mb: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation_count": self.operation_count,
            "message_count": self.message_count,
            "duration_seconds": self.duration_seconds,
            "messages_per_second": self.messages_per_second,
            "avg_latency_ms": self.avg_latency_ms,
            "max_latency_ms": self.max_latency_ms,
            "min_latency_ms": self.min_latency_ms,
            "p95_latency_ms": self.p95_latency_ms,
            "p99_latency_ms": self.p99_latency_ms,
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb
        }


class BenchmarkServer:
    """Benchmark WebSocket server."""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        """Initialize the benchmark server."""
        self.host = host
        self.port = port
        self.server = None
        self.thread = None
        self.running = False
        
    def start(self):
        """Start the WebSocket server in a separate thread."""
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()
        
        # Wait for server to start
        time.sleep(1)
        logger.info(f"WebSocket server started on {self.host}:{self.port}")
        
    def _run_server(self):
        """Run the WebSocket server."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the server
        async def run_server_async():
            try:
                # Create data directory
                data_dir = Path("./data/progress")
                data_dir.mkdir(parents=True, exist_ok=True)
                
                # Start server
                self.server = await start_websocket_server(self.host, self.port)
                self.running = True
                
                # Keep server running
                while self.running:
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Error running WebSocket server: {e}")
                
            finally:
                if self.server:
                    await self.server.stop()
                    
        # Start the server
        loop.run_until_complete(run_server_async())
        
    def stop(self):
        """Stop the WebSocket server."""
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=5.0)
            

class BenchmarkClient:
    """Benchmark WebSocket client."""
    
    def __init__(self, 
                url: str = "ws://localhost:8765",
                operation_count: int = 10,
                updates_per_operation: int = 20,
                update_interval_ms: int = 50):
        """
        Initialize the benchmark client.
        
        Args:
            url: WebSocket server URL
            operation_count: Number of concurrent operations to simulate
            updates_per_operation: Number of progress updates per operation
            update_interval_ms: Interval between updates in milliseconds
        """
        self.url = url
        self.operation_count = operation_count
        self.updates_per_operation = updates_per_operation
        self.update_interval_ms = update_interval_ms
        
        self.client = get_websocket_client(url)
        self.latencies: List[float] = []
        self.message_count = 0
        self.received_messages: List[Dict[str, Any]] = []
        self.start_time = 0
        self.end_time = 0
        self.cpu_usage: List[float] = []
        self.memory_usage: List[float] = []
        
        # Register message handlers
        self.client.add_callback("progress_update", self._on_message)
        self.client.add_callback("operation_started", self._on_message)
        self.client.add_callback("operation_completed", self._on_message)
        self.client.add_callback("operation_failed", self._on_message)
        
    def _on_message(self, message):
        """Handle received messages."""
        # Record message receipt time
        receive_time = time.time()
        
        # Get send timestamp if available
        send_time = None
        if isinstance(message, dict):
            if "timestamp" in message:
                send_time = message.get("timestamp")
            elif "data" in message and isinstance(message["data"], dict):
                send_time = message["data"].get("timestamp")
                
        # Calculate latency if send time is available
        if send_time:
            latency_ms = (receive_time - send_time) * 1000
            self.latencies.append(latency_ms)
            
        # Count message
        self.message_count += 1
        self.received_messages.append(message)
        
    async def run_benchmark(self) -> BenchmarkResult:
        """
        Run the benchmark.
        
        Returns:
            BenchmarkResult with performance metrics
        """
        # Start client
        self.client.start()
        
        # Wait for connection
        await asyncio.sleep(1)
        
        if not self.client.is_connected():
            raise ConnectionError("Failed to connect to WebSocket server")
            
        # Reset metrics
        self.latencies = []
        self.message_count = 0
        self.received_messages = []
        self.cpu_usage = []
        self.memory_usage = []
        
        # Start CPU and memory monitoring
        monitor_thread = threading.Thread(target=self._monitor_resources, daemon=True)
        monitor_thread.start()
        
        # Start timing
        self.start_time = time.time()
        
        # Create progress manager
        progress_manager = get_progress_manager()
        
        # Create operations
        operations = []
        for i in range(self.operation_count):
            reporter = ProgressReporter(
                f"benchmark_op_{i}", 
                f"Benchmark Operation {i}"
            )
            operations.append(reporter)
            
        # Register operations with progress manager
        tasks = []
        for reporter in operations:
            task = asyncio.create_task(progress_manager.add_operation(reporter))
            tasks.append(task)
            
        # Wait for operations to be registered
        await asyncio.gather(*tasks)
        await asyncio.sleep(0.5)  # Allow registration to propagate
        
        # Send progress updates
        tasks = []
        for reporter in operations:
            task = asyncio.create_task(
                self._send_updates(
                    reporter, 
                    self.updates_per_operation, 
                    self.update_interval_ms
                )
            )
            tasks.append(task)
            
        # Wait for all operations to complete
        await asyncio.gather(*tasks)
        
        # Mark operations as completed
        for reporter in operations:
            reporter.report_completed()
            
        # Wait for completion messages to propagate
        await asyncio.sleep(1)
        
        # End timing
        self.end_time = time.time()
        
        # Stop resource monitoring
        self._stop_resource_monitoring = True
        monitor_thread.join(timeout=1.0)
        
        # Disconnect client
        self.client.stop()
        
        # Calculate metrics
        duration = self.end_time - self.start_time
        messages_per_second = self.message_count / duration if duration > 0 else 0
        
        # Calculate latency statistics
        if self.latencies:
            avg_latency = statistics.mean(self.latencies)
            max_latency = max(self.latencies)
            min_latency = min(self.latencies)
            latencies_sorted = sorted(self.latencies)
            p95_latency = latencies_sorted[int(len(latencies_sorted) * 0.95)]
            p99_latency = latencies_sorted[int(len(latencies_sorted) * 0.99)]
        else:
            avg_latency = max_latency = min_latency = p95_latency = p99_latency = 0
            
        # Calculate resource usage
        cpu_percent = statistics.mean(self.cpu_usage) if self.cpu_usage else 0
        memory_mb = statistics.mean(self.memory_usage) if self.memory_usage else 0
        
        # Return benchmark result
        return BenchmarkResult(
            operation_count=self.operation_count,
            message_count=self.message_count,
            duration_seconds=duration,
            messages_per_second=messages_per_second,
            avg_latency_ms=avg_latency,
            max_latency_ms=max_latency,
            min_latency_ms=min_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            cpu_percent=cpu_percent,
            memory_mb=memory_mb
        )
        
    async def _send_updates(self, 
                         reporter: ProgressReporter, 
                         count: int, 
                         interval_ms: int):
        """
        Send progress updates for an operation.
        
        Args:
            reporter: Progress reporter
            count: Number of updates to send
            interval_ms: Interval between updates in milliseconds
        """
        interval_sec = interval_ms / 1000
        
        for i in range(count):
            # Calculate progress
            progress = (i + 1) / count * 100
            
            # Send update
            reporter.report_progress(
                progress, 
                f"Step {i + 1}/{count}", 
                details={
                    "timestamp": time.time(),
                    "benchmark": True
                }
            )
            
            # Wait for next update
            await asyncio.sleep(interval_sec)
            
    def _monitor_resources(self):
        """Monitor CPU and memory usage."""
        process = psutil.Process()
        self._stop_resource_monitoring = False
        
        while not getattr(self, "_stop_resource_monitoring", False):
            # Record CPU and memory usage
            self.cpu_usage.append(process.cpu_percent())
            memory_info = process.memory_info()
            self.memory_usage.append(memory_info.rss / (1024 * 1024))  # MB
            
            # Wait before next measurement
            time.sleep(0.5)


async def run_benchmark(args):
    """
    Run the WebSocket benchmark.
    
    Args:
        args: Command-line arguments
    """
    logger.info("Starting WebSocket benchmark")
    
    # Start server if requested
    server = None
    if args.start_server:
        logger.info("Starting benchmark server")
        server = BenchmarkServer(args.host, args.port)
        server.start()
        
    try:
        results = []
        
        # Run benchmarks with different operation counts
        for op_count in args.operations:
            logger.info(f"Running benchmark with {op_count} operations")
            
            # Create client with specified parameters
            client = BenchmarkClient(
                url=f"ws://{args.host}:{args.port}",
                operation_count=op_count,
                updates_per_operation=args.updates,
                update_interval_ms=args.interval
            )
            
            # Run benchmark
            result = await client.run_benchmark()
            results.append(result)
            
            # Log result
            logger.info(f"Benchmark result: {op_count} operations, "
                     f"{result.messages_per_second:.2f} msgs/sec, "
                     f"{result.avg_latency_ms:.2f} ms avg latency")
            
        # Generate report
        if args.report:
            generate_report(results, args.report)
            
    finally:
        # Stop server if started
        if server:
            logger.info("Stopping benchmark server")
            server.stop()
            
    logger.info("Benchmark completed")


def generate_report(results: List[BenchmarkResult], filename: str):
    """
    Generate a benchmark report.
    
    Args:
        results: List of benchmark results
        filename: Output filename
    """
    # Create report directory if needed
    report_dir = os.path.dirname(filename)
    if report_dir and not os.path.exists(report_dir):
        os.makedirs(report_dir)
        
    # Save raw results as JSON
    with open(f"{filename}.json", "w") as f:
        json.dump([result.to_dict() for result in results], f, indent=2)
        
    # Generate plots
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 15))
    
    # Extract data for plotting
    op_counts = [result.operation_count for result in results]
    throughputs = [result.messages_per_second for result in results]
    latencies = [result.avg_latency_ms for result in results]
    p95_latencies = [result.p95_latency_ms for result in results]
    p99_latencies = [result.p99_latency_ms for result in results]
    cpu_usages = [result.cpu_percent for result in results]
    memory_usages = [result.memory_mb for result in results]
    
    # Plot 1: Throughput vs. Operation Count
    ax1.plot(op_counts, throughputs, 'o-', linewidth=2)
    ax1.set_xlabel('Number of Operations')
    ax1.set_ylabel('Messages per Second')
    ax1.set_title('Throughput vs. Operation Count')
    ax1.grid(True)
    
    # Plot 2: Latency vs. Operation Count
    ax2.plot(op_counts, latencies, 'o-', label='Avg Latency', linewidth=2)
    ax2.plot(op_counts, p95_latencies, 's--', label='P95 Latency', linewidth=2)
    ax2.plot(op_counts, p99_latencies, '^--', label='P99 Latency', linewidth=2)
    ax2.set_xlabel('Number of Operations')
    ax2.set_ylabel('Latency (ms)')
    ax2.set_title('Latency vs. Operation Count')
    ax2.legend()
    ax2.grid(True)
    
    # Plot 3: Resource Usage vs. Operation Count
    ax3_cpu = ax3
    ax3_mem = ax3.twinx()
    
    ax3_cpu.plot(op_counts, cpu_usages, 'o-', color='blue', label='CPU Usage', linewidth=2)
    ax3_mem.plot(op_counts, memory_usages, 's--', color='red', label='Memory Usage', linewidth=2)
    
    ax3_cpu.set_xlabel('Number of Operations')
    ax3_cpu.set_ylabel('CPU Usage (%)', color='blue')
    ax3_mem.set_ylabel('Memory Usage (MB)', color='red')
    ax3_cpu.set_title('Resource Usage vs. Operation Count')
    
    # Add legends
    lines_cpu, labels_cpu = ax3_cpu.get_legend_handles_labels()
    lines_mem, labels_mem = ax3_mem.get_legend_handles_labels()
    ax3.legend(lines_cpu + lines_mem, labels_cpu + labels_mem, loc='upper left')
    
    ax3_cpu.grid(True)
    
    # Adjust layout and save plot
    plt.tight_layout()
    plt.savefig(f"{filename}.png", dpi=300)
    
    # Generate HTML report
    with open(f"{filename}.html", "w") as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>WebSocket Benchmark Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
        }}
        h1, h2 {{
            color: #333;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 20px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: right;
        }}
        th {{
            background-color: #f2f2f2;
            text-align: center;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        .timestamp {{
            color: #666;
            font-style: italic;
            margin-bottom: 20px;
        }}
        .summary {{
            margin-bottom: 30px;
        }}
        .graph {{
            margin-top: 30px;
            text-align: center;
        }}
        .graph img {{
            max-width: 100%;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <h1>WebSocket Benchmark Report</h1>
    <div class="timestamp">Generated on {time.strftime("%Y-%m-%d %H:%M:%S")}</div>
    
    <div class="summary">
        <h2>Summary</h2>
        <p>This benchmark tested the WebSocket-based progress reporting system with various numbers of concurrent operations.</p>
        <p>Update interval: {args.interval} ms, Updates per operation: {args.updates}</p>
    </div>
    
    <h2>Results</h2>
    <table>
        <tr>
            <th>Operations</th>
            <th>Messages</th>
            <th>Duration (s)</th>
            <th>Throughput (msgs/sec)</th>
            <th>Avg Latency (ms)</th>
            <th>P95 Latency (ms)</th>
            <th>P99 Latency (ms)</th>
            <th>CPU Usage (%)</th>
            <th>Memory (MB)</th>
        </tr>
""")
        
        for result in results:
            f.write(f"""        <tr>
            <td>{result.operation_count}</td>
            <td>{result.message_count}</td>
            <td>{result.duration_seconds:.2f}</td>
            <td>{result.messages_per_second:.2f}</td>
            <td>{result.avg_latency_ms:.2f}</td>
            <td>{result.p95_latency_ms:.2f}</td>
            <td>{result.p99_latency_ms:.2f}</td>
            <td>{result.cpu_percent:.1f}</td>
            <td>{result.memory_mb:.1f}</td>
        </tr>
""")
            
        f.write(f"""    </table>
    
    <div class="graph">
        <h2>Graphs</h2>
        <img src="{os.path.basename(filename)}.png" alt="Benchmark Graphs" />
    </div>
    
    <h2>Analysis</h2>
    <p>
        The benchmark shows that the WebSocket progress reporting system can handle 
        {max(throughputs):.0f} messages per second at peak throughput.
    </p>
    <p>
        Average latency ranges from {min(latencies):.2f} ms to {max(latencies):.2f} ms 
        depending on the number of concurrent operations.
    </p>
    <p>
        Resource usage scales with the number of operations, with CPU usage ranging 
        from {min(cpu_usages):.1f}% to {max(cpu_usages):.1f}% and memory usage 
        from {min(memory_usages):.1f} MB to {max(memory_usages):.1f} MB.
    </p>
    
    <h2>Recommendations</h2>
    <p>
        Based on these results, the system should be configured to handle no more than 
        {op_counts[throughputs.index(max(throughputs))]} concurrent operations for optimal performance.
    </p>
    <p>
        For production use, consider implementing message batching and rate limiting to 
        maintain good performance under heavy load.
    </p>
</body>
</html>
""")
        
    logger.info(f"Report generated: {filename}.html")


def main():
    """Main entry point for the benchmark script."""
    parser = argparse.ArgumentParser(description="WebSocket Progress Reporting Benchmark")
    
    parser.add_argument("--host", default="localhost", help="WebSocket server host")
    parser.add_argument("--port", type=int, default=8765, help="WebSocket server port")
    parser.add_argument("--start-server", action="store_true", help="Start WebSocket server")
    parser.add_argument("--operations", type=int, nargs="+", default=[1, 5, 10, 20, 50], 
                      help="Number of concurrent operations to test")
    parser.add_argument("--updates", type=int, default=20, 
                      help="Number of progress updates per operation")
    parser.add_argument("--interval", type=int, default=50, 
                      help="Interval between updates in milliseconds")
    parser.add_argument("--report", type=str, default="reports/websocket_benchmark", 
                      help="Output report filename")
    
    args = parser.parse_args()
    
    try:
        # Run benchmark
        asyncio.run(run_benchmark(args))
        return 0
    except KeyboardInterrupt:
        logger.info("Benchmark interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Error running benchmark: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())