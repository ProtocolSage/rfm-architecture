#!/usr/bin/env python3
"""
Resource Monitor for WebSocket Server and Clients

This script monitors system resources (CPU, memory, sockets) for the
WebSocket server and clients to detect resource leaks and verify cleanup.
"""

import argparse
import json
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger("resource-monitor")


class ResourceMonitor:
    """Monitor system resources for WebSocket server and clients."""

    def __init__(
        self,
        process_name: str = "python",
        port: int = 8765,
        output_dir: Optional[str] = None,
    ):
        """
        Initialize the resource monitor.

        Args:
            process_name: Process name to monitor
            port: WebSocket port to monitor
            output_dir: Directory for output files
        """
        self.process_name = process_name
        self.port = port
        self.output_dir = Path(output_dir or "reports/resources")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Monitoring data
        self.cpu_usage: List[float] = []
        self.memory_usage: List[float] = []  # MB
        self.socket_count: List[int] = []
        self.timestamps: List[float] = []

        # State
        self.running = False
        self.target_pid: Optional[int] = None
        self.start_time = 0.0

    def find_target_process(self) -> Optional[psutil.Process]:
        """
        Find the target process to monitor.

        Returns:
            Process object or None if not found
        """
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                # Check if process name matches
                if self.process_name in proc.info["name"].lower():
                    # Check if it's a WebSocket server by examining command line
                    if proc.info["cmdline"] and any(
                        "websocket" in arg.lower() for arg in proc.info["cmdline"]
                    ):
                        return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None

    def count_open_sockets(self) -> int:
        """
        Count open socket connections on the monitored port.

        Returns:
            Number of open sockets
        """
        try:
            if os.name == "nt":  # Windows
                output = subprocess.check_output(
                    f"netstat -ano | findstr :{self.port}", shell=True
                )
                lines = output.decode().strip().split("\n")
                return len(lines)
            else:  # Linux/Unix
                output = subprocess.check_output(
                    f"lsof -i :{self.port} | wc -l", shell=True
                )
                # Subtract 1 for header line
                count = int(output.decode().strip()) - 1
                return max(0, count)
        except subprocess.CalledProcessError:
            # No connections or command failed
            return 0

    def collect_sample(self, process: psutil.Process) -> Tuple[float, float, int]:
        """
        Collect a single sample of resource usage.

        Args:
            process: Process to monitor

        Returns:
            Tuple of (cpu_percent, memory_mb, socket_count)
        """
        try:
            # CPU usage
            cpu_percent = process.cpu_percent()

            # Memory usage (convert to MB)
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)

            # Socket count
            socket_count = self.count_open_sockets()

            return cpu_percent, memory_mb, socket_count
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Process no longer exists or can't be accessed
            return 0.0, 0.0, 0

    def start_monitoring(self, interval: float = 1.0) -> None:
        """
        Start monitoring resources.

        Args:
            interval: Sampling interval in seconds
        """
        self.running = True
        self.start_time = time.time()

        # Find target process
        process = self.find_target_process()
        if not process:
            logger.error(
                f"Cannot find process matching '{self.process_name}' running a WebSocket server"
            )
            return

        self.target_pid = process.pid
        logger.info(
            f"Monitoring WebSocket server process {self.target_pid} on port {self.port}"
        )

        # Setup signal handler for graceful shutdown
        original_sigint = signal.getsignal(signal.SIGINT)
        original_sigterm = signal.getsignal(signal.SIGTERM)

        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, stopping monitoring")
            self.running = False
            # Restore original handlers
            signal.signal(signal.SIGINT, original_sigint)
            signal.signal(signal.SIGTERM, original_sigterm)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            while self.running:
                # Check if process still exists
                try:
                    if not psutil.pid_exists(self.target_pid):
                        logger.warning("Target process has terminated")
                        break
                    process = psutil.Process(self.target_pid)
                except psutil.NoSuchProcess:
                    logger.warning("Target process no longer exists")
                    break

                # Collect sample
                cpu, memory, sockets = self.collect_sample(process)
                timestamp = time.time() - self.start_time

                # Store data
                self.cpu_usage.append(cpu)
                self.memory_usage.append(memory)
                self.socket_count.append(sockets)
                self.timestamps.append(timestamp)

                # Log periodic updates
                if len(self.timestamps) % 10 == 0:
                    logger.info(
                        f"Current usage - CPU: {cpu:.1f}%, Memory: {memory:.1f}MB, "
                        f"Sockets: {sockets}"
                    )

                # Wait for next sample
                time.sleep(interval)
        finally:
            # Generate report
            self.generate_report()

    def generate_report(self) -> None:
        """Generate report with resource usage statistics and plots."""
        if not self.timestamps:
            logger.warning("No data collected, cannot generate report")
            return

        # Create timestamp for report files
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Convert lists to numpy arrays for analysis
        timestamps = np.array(self.timestamps)
        cpu_usage = np.array(self.cpu_usage)
        memory_usage = np.array(self.memory_usage)
        socket_count = np.array(self.socket_count)
        
        # Calculate statistics
        stats = {
            "timestamp": timestamp_str,
            "duration": timestamps[-1],
            "process_id": self.target_pid,
            "port": self.port,
            "cpu": {
                "min": float(np.min(cpu_usage)),
                "max": float(np.max(cpu_usage)),
                "mean": float(np.mean(cpu_usage)),
                "std": float(np.std(cpu_usage)),
                "final": float(cpu_usage[-1])
            },
            "memory": {
                "min": float(np.min(memory_usage)),
                "max": float(np.max(memory_usage)),
                "mean": float(np.mean(memory_usage)),
                "std": float(np.std(memory_usage)),
                "final": float(memory_usage[-1]),
                "trend": "increasing" if len(memory_usage) > 10 and 
                         np.polyfit(range(len(memory_usage)), memory_usage, 1)[0] > 0.1 
                         else "stable"
            },
            "sockets": {
                "min": int(np.min(socket_count)),
                "max": int(np.max(socket_count)),
                "mean": float(np.mean(socket_count)),
                "final": int(socket_count[-1])
            }
        }
        
        # Generate JSON report
        json_path = self.output_dir / f"resource_report_{timestamp_str}.json"
        with open(json_path, "w") as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Resource report saved to {json_path}")
        
        # Generate plots
        self._generate_plots(timestamp_str)
        
        # Log summary
        logger.info("Resource Monitoring Summary:")
        logger.info(f"Duration: {stats['duration']:.1f} seconds")
        logger.info(f"CPU: {stats['cpu']['mean']:.1f}% (peak: {stats['cpu']['max']:.1f}%)")
        logger.info(f"Memory: {stats['memory']['mean']:.1f}MB (peak: {stats['memory']['max']:.1f}MB)")
        logger.info(f"Sockets: {stats['sockets']['mean']:.1f} (peak: {stats['sockets']['max']})")
        
        if stats['memory']['trend'] == "increasing":
            logger.warning("WARNING: Memory usage shows an increasing trend, possible leak")
        
        if stats['sockets']['final'] > 0:
            logger.warning(f"WARNING: {stats['sockets']['final']} sockets still open at the end")

    def _generate_plots(self, timestamp_str: str) -> None:
        """
        Generate plots of resource usage.
        
        Args:
            timestamp_str: Timestamp string for filenames
        """
        # Create figure with three subplots
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12))
        fig.suptitle(f"Resource Usage - Process {self.target_pid}", fontsize=16)
        
        # CPU usage plot
        ax1.plot(self.timestamps, self.cpu_usage, 'b-')
        ax1.set_title('CPU Usage')
        ax1.set_ylabel('CPU (%)')
        ax1.grid(True)
        
        # Memory usage plot
        ax2.plot(self.timestamps, self.memory_usage, 'r-')
        ax2.set_title('Memory Usage')
        ax2.set_ylabel('Memory (MB)')
        ax2.grid(True)
        
        # Socket count plot
        ax3.plot(self.timestamps, self.socket_count, 'g-')
        ax3.set_title(f'Socket Count (Port {self.port})')
        ax3.set_xlabel('Time (seconds)')
        ax3.set_ylabel('Count')
        ax3.grid(True)
        
        # Save plot
        plot_path = self.output_dir / f"resource_plot_{timestamp_str}.png"
        plt.tight_layout()
        plt.savefig(plot_path)
        plt.close(fig)
        
        logger.info(f"Resource plot saved to {plot_path}")

    def check_resource_cleanup(self, timeout: float = 5.0) -> bool:
        """
        Check that resources are properly cleaned up after server shutdown.
        
        Args:
            timeout: Time to wait for cleanup in seconds
            
        Returns:
            True if resources are properly cleaned up
        """
        logger.info(f"Checking resource cleanup (timeout: {timeout}s)")
        
        # Wait for resources to be released
        end_time = time.time() + timeout
        while time.time() < end_time:
            # Check for sockets
            sockets = self.count_open_sockets()
            if sockets == 0:
                logger.info("All sockets closed successfully")
                return True
                
            # Wait and retry
            time.sleep(0.5)
            
        # Timeout reached
        sockets = self.count_open_sockets()
        if sockets > 0:
            logger.error(f"Resource cleanup failed: {sockets} sockets still open after {timeout}s")
            return False
        
        return True


def main():
    parser = argparse.ArgumentParser(description="Monitor WebSocket server resources")
    parser.add_argument("--process", default="python", help="Process name to monitor")
    parser.add_argument("--port", type=int, default=8765, help="WebSocket port to monitor")
    parser.add_argument("--interval", type=float, default=1.0, help="Sampling interval (seconds)")
    parser.add_argument("--output-dir", help="Output directory for reports and plots")
    parser.add_argument("--no-plots", action="store_true", help="Disable plot generation")
    parser.add_argument("--verify-cleanup", action="store_true", 
                       help="Verify resources are cleaned up after monitoring")
    
    args = parser.parse_args()
    
    # Create monitor
    monitor = ResourceMonitor(
        process_name=args.process,
        port=args.port,
        output_dir=args.output_dir
    )
    
    # Start monitoring
    try:
        logger.info(f"Starting resource monitoring (interval: {args.interval}s)")
        monitor.start_monitoring(interval=args.interval)
    except KeyboardInterrupt:
        logger.info("Monitoring interrupted by user")
    
    # Verify cleanup if requested
    if args.verify_cleanup:
        if monitor.check_resource_cleanup():
            logger.info("Resource cleanup verification: PASSED")
            return 0
        else:
            logger.error("Resource cleanup verification: FAILED")
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())