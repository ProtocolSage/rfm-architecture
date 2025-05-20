"""
Performance tracking for RFM Architecture UI.

This module provides tools for tracking application performance metrics.
"""

import time
import collections
import threading
import json
import os
import logging
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional, Deque, Union, Set
from datetime import datetime
from functools import wraps
import numpy as np
import psutil


@dataclass
class PerformanceRecord:
    """Single performance measurement record."""
    
    timestamp: float
    operation: str
    params: Dict[str, Any]
    duration_ms: float
    memory_before_mb: float
    memory_after_mb: float
    thread_id: int
    gpu_memory_mb: Optional[float] = None
    cpu_percent: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


class PerformanceTracker:
    """Centralized performance tracking for fractal rendering operations."""
    
    def __init__(self, 
                max_history: int = 1000, 
                auto_save: bool = True, 
                log_dir: str = "./performance_logs",
                auto_save_interval: int = 100):
        """
        Initialize the performance tracker.
        
        Args:
            max_history: Maximum number of records to keep in memory
            auto_save: Whether to automatically save records periodically
            log_dir: Directory to store performance logs
            auto_save_interval: Save after this many new records
        """
        self._history: Deque[PerformanceRecord] = collections.deque(maxlen=max_history)
        self._lock = threading.RLock()
        self._auto_save = auto_save
        self._auto_save_interval = auto_save_interval
        self._save_path = log_dir
        self._baseline_data: Dict[str, Dict[str, float]] = {}
        self._logger = logging.getLogger("rfm_performance")
        
        # Operation statistics tracking
        self._operation_min_times: Dict[str, float] = {}
        self._operation_max_times: Dict[str, float] = {}
        self._operation_total_times: Dict[str, float] = {}
        self._operation_call_counts: Dict[str, int] = {}
        
        # Ensure save directory exists
        if auto_save and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Load baseline if available
        self._load_baseline()
    
    def start_operation(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start tracking an operation's performance.
        
        Args:
            operation: Name of the operation being tracked
            params: Parameters related to the operation
            
        Returns:
            Context dictionary to pass to end_operation
        """
        # Get current process
        process = psutil.Process(os.getpid())
        
        # Capture current resource usage
        cpu_percent = process.cpu_percent(interval=0.1)  # Short interval for quick sampling
        memory_before = process.memory_info().rss / (1024 * 1024)  # MB
        
        # Get GPU memory usage if possible
        gpu_memory = None
        try:
            # Optionally implement GPU memory tracking here
            # This would typically use pynvml for NVIDIA GPUs
            pass
        except Exception:
            # Not critical, just log and continue without GPU metrics
            pass
            
        return {
            "operation": operation,
            "params": params,
            "start_time": time.time(),
            "memory_before": memory_before,
            "thread_id": threading.get_ident(),
            "cpu_percent": cpu_percent,
            "gpu_memory": gpu_memory
        }
    
    def end_operation(self, context: Dict[str, Any]) -> PerformanceRecord:
        """
        End tracking an operation and record its performance.
        
        Args:
            context: Context dictionary from start_operation
            
        Returns:
            Performance record with timing information
        """
        end_time = time.time()
        duration_ms = (end_time - context["start_time"]) * 1000
        
        # Get current process
        process = psutil.Process(os.getpid())
        
        # Capture resource usage
        memory_after = process.memory_info().rss / (1024 * 1024)  # MB
        operation = context["operation"]
        
        # Create the record
        record = PerformanceRecord(
            timestamp=end_time,
            operation=operation,
            params=context["params"],
            duration_ms=duration_ms,
            memory_before_mb=context["memory_before"],
            memory_after_mb=memory_after,
            thread_id=context["thread_id"],
            cpu_percent=context.get("cpu_percent"),
            gpu_memory_mb=context.get("gpu_memory")
        )
        
        with self._lock:
            # Update operation statistics
            if operation not in self._operation_call_counts:
                self._operation_call_counts[operation] = 0
                self._operation_total_times[operation] = 0.0
                self._operation_min_times[operation] = float('inf')
                self._operation_max_times[operation] = 0.0
                
            self._operation_call_counts[operation] += 1
            self._operation_total_times[operation] += duration_ms
            self._operation_min_times[operation] = min(self._operation_min_times[operation], duration_ms)
            self._operation_max_times[operation] = max(self._operation_max_times[operation], duration_ms)
            
            # Add to history
            self._history.append(record)
            
            # Auto-save if enabled
            if self._auto_save and len(self._history) % self._auto_save_interval == 0:
                self._save_history()
                
        # Log if operation is unusually slow (more than 2x average)
        avg_time = self._operation_total_times[operation] / self._operation_call_counts[operation]
        if duration_ms > avg_time * 2 and self._operation_call_counts[operation] > 5:
            self._logger.warning(
                f"Slow operation: {operation} took {duration_ms:.2f}ms "
                f"(avg: {avg_time:.2f}ms, max: {self._operation_max_times[operation]:.2f}ms)"
            )
                
        return record
    
    def track(self, operation: str, params: Optional[Dict[str, Any]] = None):
        """
        Decorator to track function performance.
        
        Args:
            operation: Name of the operation being tracked
            params: Static parameters to record with each call
            
        Returns:
            Decorator function
            
        Example:
            @performance_tracker.track("render_fractal")
            def render_fractal(params):
                # Function implementation
        """
        params = params or {}
        
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Combine static params with any dynamic params we can extract
                call_params = params.copy()
                
                # Try to extract parameters from the first argument if it's a dict
                if args and isinstance(args[0], dict):
                    call_params.update(args[0])
                
                # Start tracking
                context = self.start_operation(operation, call_params)
                try:
                    # Call the function
                    result = func(*args, **kwargs)
                    return result
                finally:
                    # End tracking
                    self.end_operation(context)
            
            return wrapper
        
        return decorator
    
    def get_history(self) -> List[PerformanceRecord]:
        """
        Get a copy of the performance history.
        
        Returns:
            List of performance records
        """
        with self._lock:
            return list(self._history)
    
    def get_operation_stats(self, operation: str) -> Dict[str, float]:
        """
        Get statistics for a specific operation.
        
        Args:
            operation: Name of the operation
            
        Returns:
            Dictionary with operation statistics
        """
        with self._lock:
            if operation not in self._operation_call_counts or self._operation_call_counts[operation] == 0:
                return {}
                
            # Calculate statistics for this operation
            call_count = self._operation_call_counts[operation]
            total_time = self._operation_total_times[operation]
            min_time = self._operation_min_times[operation]
            max_time = self._operation_max_times[operation]
            avg_time = total_time / call_count
                
            # Get recent records for this operation
            records = [r for r in self._history if r.operation == operation]
            
            # Calculate percentiles and memory usage if we have data
            if records:
                durations = [r.duration_ms for r in records]
                memory_usage = [(r.memory_after_mb - r.memory_before_mb) for r in records]
                
                stats = {
                    "count": call_count,
                    "total_duration_ms": total_time,
                    "avg_duration_ms": avg_time,
                    "min_duration_ms": min_time,
                    "max_duration_ms": max_time,
                    "p95_duration_ms": float(np.percentile(durations, 95) if durations else 0),
                    "p99_duration_ms": float(np.percentile(durations, 99) if durations else 0),
                    "avg_memory_usage_mb": float(np.mean(memory_usage) if memory_usage else 0),
                    "max_memory_usage_mb": float(np.max(memory_usage) if memory_usage else 0)
                }
            else:
                stats = {
                    "count": call_count,
                    "total_duration_ms": total_time,
                    "avg_duration_ms": avg_time,
                    "min_duration_ms": min_time,
                    "max_duration_ms": max_time
                }
                
            return stats
    
    def get_all_operation_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Get statistics for all operations.
        
        Returns:
            Dictionary mapping operation names to their statistics
        """
        with self._lock:
            stats = {}
            for op in self._operation_call_counts.keys():
                op_stats = self.get_operation_stats(op)
                if op_stats:  # Only include operations with data
                    stats[op] = op_stats
            return stats
    
    def get_hotspots(self, threshold_ms: float = 100) -> List[PerformanceRecord]:
        """
        Get operations that took longer than threshold.
        
        Args:
            threshold_ms: Threshold in milliseconds
            
        Returns:
            List of performance records for operations exceeding the threshold
        """
        with self._lock:
            return [r for r in self._history if r.duration_ms > threshold_ms]
    
    def detect_performance_regressions(self, threshold_pct: float = 20) -> List[Dict[str, Any]]:
        """
        Detect performance regressions compared to baseline.
        
        Args:
            threshold_pct: Percentage threshold for regression detection
            
        Returns:
            List of detected regressions
        """
        if not self._baseline_data:
            return []
            
        regressions = []
        
        # Group current data by operation
        current_stats = self.get_all_operation_stats()
        
        # Compare with baseline
        for op, baseline in self._baseline_data.items():
            if op not in current_stats:
                continue
                
            current = current_stats[op]
            
            # Check duration regression
            if current["avg_duration_ms"] > baseline["avg_duration_ms"] * (1 + threshold_pct/100):
                regressions.append({
                    "operation": op,
                    "metric": "duration",
                    "baseline_value": baseline["avg_duration_ms"],
                    "current_value": current["avg_duration_ms"],
                    "regression_pct": (current["avg_duration_ms"] - baseline["avg_duration_ms"]) / 
                                      baseline["avg_duration_ms"] * 100
                })
                
            # Check memory regression if available
            if "avg_memory_usage_mb" in current and "avg_memory_usage_mb" in baseline:
                if current["avg_memory_usage_mb"] > baseline["avg_memory_usage_mb"] * (1 + threshold_pct/100):
                    regressions.append({
                        "operation": op,
                        "metric": "memory",
                        "baseline_value": baseline["avg_memory_usage_mb"],
                        "current_value": current["avg_memory_usage_mb"],
                        "regression_pct": (current["avg_memory_usage_mb"] - baseline["avg_memory_usage_mb"]) / 
                                          baseline["avg_memory_usage_mb"] * 100
                    })
                
        return regressions
    
    def set_current_as_baseline(self) -> bool:
        """
        Set the current performance data as the baseline.
        
        Returns:
            True if baseline was set successfully, False otherwise
        """
        try:
            baseline = self.get_all_operation_stats()
            
            if not baseline:
                self._logger.warning("No performance data to set as baseline")
                return False
                
            self._baseline_data = baseline
            
            # Save baseline to file
            baseline_path = os.path.join(self._save_path, "baseline.json")
            with open(baseline_path, "w") as f:
                json.dump(baseline, f, indent=2)
                
            self._logger.info(f"Performance baseline set with {len(baseline)} operations")
            return True
        except Exception as e:
            self._logger.error(f"Error setting performance baseline: {e}")
            return False
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive performance report.
        
        Returns:
            Dictionary with performance report data
        """
        operations = set(r.operation for r in self._history)
        
        # Get overall stats
        total_records = len(self._history)
        total_operations = len(operations)
        
        # Get operation stats
        operation_stats = {}
        for op in operations:
            stats = self.get_operation_stats(op)
            if stats:
                operation_stats[op] = stats
            
        # Find slowest operations
        slowest_ops = sorted(
            [(op, stats["avg_duration_ms"]) for op, stats in operation_stats.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Find operations with highest memory usage
        memory_ops = sorted(
            [(op, stats.get("avg_memory_usage_mb", 0)) for op, stats in operation_stats.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Get regression data
        regressions = self.detect_performance_regressions()
        
        # Build report
        report = {
            "timestamp": time.time(),
            "total_records": total_records,
            "total_operations": total_operations,
            "operation_stats": operation_stats,
            "slowest_operations": slowest_ops,
            "highest_memory_usage": memory_ops,
            "regressions": regressions
        }
        
        return report
    
    def _save_history(self) -> bool:
        """
        Save performance history to file.
        
        Returns:
            True if save was successful, False otherwise
        """
        try:
            timestamp = int(time.time())
            filename = f"perf_log_{timestamp}.json"
            filepath = os.path.join(self._save_path, filename)
            
            with open(filepath, "w") as f:
                json.dump([r.to_dict() for r in self._history], f, indent=2)
                
            self._logger.debug(f"Saved performance history to {filepath}")
            return True
        except Exception as e:
            self._logger.error(f"Error saving performance history: {e}")
            return False
            
    def _load_baseline(self) -> bool:
        """
        Load baseline data if available.
        
        Returns:
            True if baseline was loaded successfully, False otherwise
        """
        baseline_path = os.path.join(self._save_path, "baseline.json")
        if not os.path.exists(baseline_path):
            return False
            
        try:
            with open(baseline_path, "r") as f:
                self._baseline_data = json.load(f)
                
            self._logger.info(f"Loaded performance baseline with {len(self._baseline_data)} operations")
            return True
        except Exception as e:
            self._logger.error(f"Error loading baseline data: {e}")
            return False