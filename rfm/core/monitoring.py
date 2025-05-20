"""
Monitoring system for RFM Architecture.

This module provides performance monitoring, health checks, and metrics collection
for the RFM Architecture components, with a focus on the WebSocket-based
progress reporting system.
"""

import os
import time
import threading
import asyncio
import json
import psutil
import logging
from typing import Dict, Any, List, Optional, Set, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import socket
import uuid

from .logging_config import get_logger, log_timing, LogCategory, LogLevel, TimingContext


# Get logger
logger = get_logger(__name__)


class MetricType(str, Enum):
    """Types of metrics that can be collected."""
    
    COUNTER = "counter"       # Increasing count (e.g., message count)
    GAUGE = "gauge"           # Value that can go up or down (e.g., connection count)
    HISTOGRAM = "histogram"   # Distribution of values (e.g., message size)
    TIMER = "timer"           # Duration measurements (e.g., message processing time)


@dataclass
class MetricValue:
    """Value for a metric with timestamp."""
    
    value: Union[int, float]
    timestamp: float = field(default_factory=time.time)


@dataclass
class Metric:
    """Metric definition and current value."""
    
    name: str
    type: MetricType
    description: str
    unit: str
    value: Any = None
    values: List[MetricValue] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)
    max_history: int = 100  # Maximum number of historical values to keep
    
    def __post_init__(self):
        """Initialize metric based on type."""
        if self.type == MetricType.COUNTER:
            self.value = 0
        elif self.type == MetricType.HISTOGRAM:
            self.values = []
            
    def update(self, value: Union[int, float]) -> None:
        """
        Update the metric value.
        
        Args:
            value: New value for the metric
        """
        if self.type == MetricType.COUNTER:
            self.value += value
        elif self.type == MetricType.GAUGE:
            self.value = value
        
        # Add to history
        self.values.append(MetricValue(value))
        
        # Trim history if needed
        if len(self.values) > self.max_history:
            self.values = self.values[-self.max_history:]
            
    def get_current_value(self) -> Union[int, float, None]:
        """
        Get the current value of the metric.
        
        Returns:
            Current metric value
        """
        if self.type in (MetricType.COUNTER, MetricType.GAUGE):
            return self.value
        elif self.type == MetricType.HISTOGRAM and self.values:
            # Return average of recent values
            return sum(v.value for v in self.values[-10:]) / min(10, len(self.values))
        elif self.type == MetricType.TIMER and self.values:
            # Return average of recent values
            return sum(v.value for v in self.values[-10:]) / min(10, len(self.values))
        return None
    
    def get_history(self) -> List[Tuple[float, Union[int, float]]]:
        """
        Get historical values with timestamps.
        
        Returns:
            List of (timestamp, value) tuples
        """
        return [(v.timestamp, v.value) for v in self.values]
        
    def get_percentile(self, percentile: float) -> Optional[float]:
        """
        Get a percentile value from the metric history.
        
        Args:
            percentile: Percentile to calculate (0.0 to 1.0)
            
        Returns:
            Percentile value, or None if no values
        """
        if not self.values:
            return None
            
        # Sort values
        sorted_values = sorted(v.value for v in self.values)
        
        # Calculate percentile index
        index = int(percentile * len(sorted_values))
        
        # Handle edge cases
        if index >= len(sorted_values):
            return sorted_values[-1]
        if index < 0:
            return sorted_values[0]
            
        return sorted_values[index]
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert metric to dictionary.
        
        Returns:
            Dictionary representation of the metric
        """
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "unit": self.unit,
            "value": self.get_current_value(),
            "tags": self.tags,
            "percentiles": {
                "p50": self.get_percentile(0.5),
                "p90": self.get_percentile(0.9),
                "p95": self.get_percentile(0.95),
                "p99": self.get_percentile(0.99)
            } if self.type in (MetricType.HISTOGRAM, MetricType.TIMER) else None
        }


class HealthStatus(str, Enum):
    """Health status for components."""
    
    HEALTHY = "healthy"           # Component is functioning normally
    DEGRADED = "degraded"         # Component is functioning with reduced capabilities
    UNHEALTHY = "unhealthy"       # Component is not functioning correctly
    UNKNOWN = "unknown"           # Component health status is unknown


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    
    component: str
    status: HealthStatus
    details: Optional[Dict[str, Any]] = None
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert health check result to dictionary.
        
        Returns:
            Dictionary representation of the health check result
        """
        return {
            "component": self.component,
            "status": self.status,
            "details": self.details,
            "timestamp": self.timestamp
        }


class MetricsRegistry:
    """Registry for metrics collection and reporting."""
    
    def __init__(self, application_name: str):
        """
        Initialize the metrics registry.
        
        Args:
            application_name: Name of the application
        """
        self.application_name = application_name
        self.metrics: Dict[str, Metric] = {}
        self.health_checks: Dict[str, HealthCheckResult] = {}
        self.lock = threading.RLock()
        self.host = socket.gethostname()
        
        # System metrics collector
        self._system_metrics_interval = 10.0  # seconds
        self._stop_system_metrics = False
        self._system_metrics_thread = None
        
        # Register core metrics
        self._register_core_metrics()
        
    def _register_core_metrics(self) -> None:
        """Register core system metrics."""
        # CPU metrics
        self.register_metric(
            "system.cpu.usage",
            MetricType.GAUGE,
            "CPU usage percentage",
            "percent"
        )
        
        # Memory metrics
        self.register_metric(
            "system.memory.usage",
            MetricType.GAUGE,
            "Memory usage",
            "bytes"
        )
        
        self.register_metric(
            "system.memory.available",
            MetricType.GAUGE,
            "Available memory",
            "bytes"
        )
        
        # Disk metrics
        self.register_metric(
            "system.disk.usage",
            MetricType.GAUGE,
            "Disk usage percentage",
            "percent"
        )
        
        # Thread metrics
        self.register_metric(
            "system.threads.count",
            MetricType.GAUGE,
            "Thread count",
            "count"
        )
        
        # Connection metrics
        self.register_metric(
            "websocket.connections.active",
            MetricType.GAUGE,
            "Active WebSocket connections",
            "count"
        )
        
        self.register_metric(
            "websocket.connections.total",
            MetricType.COUNTER,
            "Total WebSocket connections",
            "count"
        )
        
        # Message metrics
        self.register_metric(
            "websocket.messages.received",
            MetricType.COUNTER,
            "WebSocket messages received",
            "count"
        )
        
        self.register_metric(
            "websocket.messages.sent",
            MetricType.COUNTER,
            "WebSocket messages sent",
            "count"
        )
        
        self.register_metric(
            "websocket.messages.size",
            MetricType.HISTOGRAM,
            "WebSocket message size",
            "bytes"
        )
        
        # Latency metrics
        self.register_metric(
            "websocket.latency",
            MetricType.TIMER,
            "WebSocket message latency",
            "seconds"
        )
        
        # Operation metrics
        self.register_metric(
            "operations.active",
            MetricType.GAUGE,
            "Active operations",
            "count"
        )
        
        self.register_metric(
            "operations.total",
            MetricType.COUNTER,
            "Total operations",
            "count"
        )
        
        self.register_metric(
            "operations.completed",
            MetricType.COUNTER,
            "Completed operations",
            "count"
        )
        
        self.register_metric(
            "operations.failed",
            MetricType.COUNTER,
            "Failed operations",
            "count"
        )
        
        self.register_metric(
            "operations.canceled",
            MetricType.COUNTER,
            "Canceled operations",
            "count"
        )
        
        self.register_metric(
            "operations.duration",
            MetricType.TIMER,
            "Operation duration",
            "seconds"
        )
        
    def start_system_metrics_collection(self) -> None:
        """Start collecting system metrics in background thread."""
        if self._system_metrics_thread and self._system_metrics_thread.is_alive():
            logger.structured_log(
                LogLevel.WARNING,
                "System metrics collection already running",
                LogCategory.SYSTEM,
                component="metrics_registry"
            )
            return
            
        # Reset flag
        self._stop_system_metrics = False
        
        # Start collection thread
        self._system_metrics_thread = threading.Thread(
            target=self._collect_system_metrics,
            daemon=True,
            name="SystemMetricsCollector"
        )
        self._system_metrics_thread.start()
        
        logger.structured_log(
            LogLevel.INFO,
            "Started system metrics collection",
            LogCategory.SYSTEM,
            component="metrics_registry",
            context={"interval": self._system_metrics_interval}
        )
        
    def stop_system_metrics_collection(self) -> None:
        """Stop collecting system metrics."""
        if not self._system_metrics_thread or not self._system_metrics_thread.is_alive():
            return
            
        # Set stop flag
        self._stop_system_metrics = True
        
        # Wait for thread to exit
        self._system_metrics_thread.join(timeout=1.0)
        
        logger.structured_log(
            LogLevel.INFO,
            "Stopped system metrics collection",
            LogCategory.SYSTEM,
            component="metrics_registry"
        )
        
    def _collect_system_metrics(self) -> None:
        """Collect system metrics in background thread."""
        try:
            while not self._stop_system_metrics:
                try:
                    # Collect CPU metrics
                    cpu_percent = psutil.cpu_percent(interval=0.1)
                    self.update_metric("system.cpu.usage", cpu_percent)
                    
                    # Collect memory metrics
                    memory = psutil.virtual_memory()
                    self.update_metric("system.memory.usage", memory.used)
                    self.update_metric("system.memory.available", memory.available)
                    
                    # Collect disk metrics
                    disk = psutil.disk_usage('/')
                    self.update_metric("system.disk.usage", disk.percent)
                    
                    # Collect thread metrics
                    thread_count = threading.active_count()
                    self.update_metric("system.threads.count", thread_count)
                    
                except Exception as e:
                    logger.structured_log(
                        LogLevel.ERROR,
                        f"Error collecting system metrics: {e}",
                        LogCategory.SYSTEM,
                        component="metrics_registry",
                        error=str(e)
                    )
                
                # Sleep until next collection
                time.sleep(self._system_metrics_interval)
                
        except Exception as e:
            logger.structured_log(
                LogLevel.ERROR,
                f"System metrics collection thread error: {e}",
                LogCategory.SYSTEM,
                component="metrics_registry",
                error=str(e)
            )
        
    def register_metric(self, 
                      name: str, 
                      type: MetricType, 
                      description: str, 
                      unit: str,
                      tags: Optional[Dict[str, str]] = None) -> Metric:
        """
        Register a new metric.
        
        Args:
            name: Metric name
            type: Metric type
            description: Metric description
            unit: Metric unit
            tags: Optional tags for the metric
            
        Returns:
            Registered metric
        """
        with self.lock:
            if name in self.metrics:
                return self.metrics[name]
                
            metric = Metric(
                name=name,
                type=type,
                description=description,
                unit=unit,
                tags=tags or {}
            )
            
            # Add standard tags
            metric.tags.update({
                "application": self.application_name,
                "host": self.host
            })
            
            self.metrics[name] = metric
            
            return metric
        
    def update_metric(self, name: str, value: Union[int, float]) -> None:
        """
        Update a metric value.
        
        Args:
            name: Metric name
            value: New value
            
        Raises:
            ValueError: If metric does not exist
        """
        with self.lock:
            if name not in self.metrics:
                raise ValueError(f"Metric '{name}' not registered")
                
            metric = self.metrics[name]
            metric.update(value)
        
    def get_metric(self, name: str) -> Optional[Metric]:
        """
        Get a metric by name.
        
        Args:
            name: Metric name
            
        Returns:
            Metric if found, None otherwise
        """
        with self.lock:
            return self.metrics.get(name)
        
    def get_metrics(self) -> Dict[str, Metric]:
        """
        Get all registered metrics.
        
        Returns:
            Dictionary of metric name to metric
        """
        with self.lock:
            return self.metrics.copy()
        
    def get_metrics_report(self) -> Dict[str, Any]:
        """
        Get a report of all metrics.
        
        Returns:
            Dictionary with metric data
        """
        with self.lock:
            return {
                "timestamp": time.time(),
                "application": self.application_name,
                "host": self.host,
                "metrics": {name: metric.to_dict() for name, metric in self.metrics.items()}
            }
        
    def register_health_check(self, 
                           component: str, 
                           status: HealthStatus, 
                           details: Optional[Dict[str, Any]] = None) -> None:
        """
        Register a health check result.
        
        Args:
            component: Component name
            status: Health status
            details: Optional details about the health status
        """
        with self.lock:
            self.health_checks[component] = HealthCheckResult(
                component=component,
                status=status,
                details=details
            )
        
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get the overall health status.
        
        Returns:
            Dictionary with health status information
        """
        with self.lock:
            # Get latest health checks
            health_checks = list(self.health_checks.values())
            
            # Determine overall status
            if not health_checks:
                overall_status = HealthStatus.UNKNOWN
            elif any(check.status == HealthStatus.UNHEALTHY for check in health_checks):
                overall_status = HealthStatus.UNHEALTHY
            elif any(check.status == HealthStatus.DEGRADED for check in health_checks):
                overall_status = HealthStatus.DEGRADED
            else:
                overall_status = HealthStatus.HEALTHY
                
            return {
                "status": overall_status,
                "timestamp": time.time(),
                "application": self.application_name,
                "host": self.host,
                "components": [check.to_dict() for check in health_checks]
            }


# Singleton instance
_metrics_registry: Optional[MetricsRegistry] = None


def get_metrics_registry(application_name: str = "rfm_architecture") -> MetricsRegistry:
    """
    Get the global metrics registry.
    
    Args:
        application_name: Application name for metrics
        
    Returns:
        MetricsRegistry instance
    """
    global _metrics_registry
    if _metrics_registry is None:
        _metrics_registry = MetricsRegistry(application_name)
        
    return _metrics_registry


# Connection monitoring for WebSocket server
class ConnectionMonitor:
    """Monitors WebSocket connections for the server."""
    
    def __init__(self, 
                metrics_registry: Optional[MetricsRegistry] = None,
                connection_timeout: float = 300.0,  # 5 minutes
                check_interval: float = 60.0):      # 1 minute
        """
        Initialize the connection monitor.
        
        Args:
            metrics_registry: Optional metrics registry
            connection_timeout: Timeout for inactive connections (seconds)
            check_interval: Interval for checking connections (seconds)
        """
        self.metrics_registry = metrics_registry or get_metrics_registry()
        self.connection_timeout = connection_timeout
        self.check_interval = check_interval
        
        self.active_connections: Dict[str, Dict[str, Any]] = {}
        self.connection_history: deque = deque(maxlen=1000)  # Last 1000 connections
        
        self.lock = threading.RLock()
        self._stop_monitor = False
        self._monitor_task = None
        
        # Generate monitor ID
        self.monitor_id = str(uuid.uuid4())
        
        logger.structured_log(
            LogLevel.INFO,
            "Initialized connection monitor",
            LogCategory.CONNECTION,
            component="connection_monitor",
            context={
                "connection_timeout": connection_timeout,
                "check_interval": check_interval,
                "monitor_id": self.monitor_id
            }
        )
        
    def start(self) -> None:
        """Start connection monitoring."""
        if self._monitor_task:
            logger.structured_log(
                LogLevel.WARNING,
                "Connection monitor already running",
                LogCategory.CONNECTION,
                component="connection_monitor",
                context={"monitor_id": self.monitor_id}
            )
            return
            
        # Reset flag
        self._stop_monitor = False
        
        # Start monitoring task
        self._monitor_task = asyncio.create_task(self._monitor_connections())
        
        logger.structured_log(
            LogLevel.INFO,
            "Started connection monitoring",
            LogCategory.CONNECTION,
            component="connection_monitor",
            context={"monitor_id": self.monitor_id}
        )
        
    def stop(self) -> None:
        """Stop connection monitoring."""
        if not self._monitor_task:
            return
            
        # Set stop flag
        self._stop_monitor = True
        
        # Cancel task
        self._monitor_task.cancel()
        self._monitor_task = None
        
        logger.structured_log(
            LogLevel.INFO,
            "Stopped connection monitoring",
            LogCategory.CONNECTION,
            component="connection_monitor",
            context={"monitor_id": self.monitor_id}
        )
        
    def connection_opened(self, 
                        connection_id: str, 
                        websocket: Any,
                        details: Optional[Dict[str, Any]] = None) -> None:
        """
        Register a new connection.
        
        Args:
            connection_id: Unique connection ID
            websocket: WebSocket connection object
            details: Optional connection details
        """
        with self.lock:
            # Record connection info
            connection_info = {
                "connection_id": connection_id,
                "websocket": websocket,
                "open_time": time.time(),
                "last_activity_time": time.time(),
                "remote_address": getattr(websocket, "remote_address", None),
                "user_agent": details.get("user_agent") if details else None,
                "client_info": details.get("client_info") if details else None,
                "messages_received": 0,
                "messages_sent": 0,
                "bytes_received": 0,
                "bytes_sent": 0
            }
            
            self.active_connections[connection_id] = connection_info
            
            # Update metrics
            self.metrics_registry.update_metric("websocket.connections.active", len(self.active_connections))
            self.metrics_registry.update_metric("websocket.connections.total", 1)
            
            # Add to history
            history_entry = connection_info.copy()
            history_entry.pop("websocket", None)  # Remove WebSocket object from history
            self.connection_history.append(history_entry)
            
            logger.structured_log(
                LogLevel.INFO,
                f"WebSocket connection opened: {connection_id}",
                LogCategory.CONNECTION,
                component="connection_monitor",
                context={
                    "connection_id": connection_id,
                    "remote_address": getattr(websocket, "remote_address", None),
                    "active_connections": len(self.active_connections),
                    "monitor_id": self.monitor_id
                }
            )
        
    def connection_closed(self, 
                        connection_id: str, 
                        details: Optional[Dict[str, Any]] = None) -> None:
        """
        Register a closed connection.
        
        Args:
            connection_id: Connection ID
            details: Optional details about the closure
        """
        with self.lock:
            if connection_id not in self.active_connections:
                logger.structured_log(
                    LogLevel.WARNING,
                    f"Unknown connection closed: {connection_id}",
                    LogCategory.CONNECTION,
                    component="connection_monitor",
                    context={"monitor_id": self.monitor_id}
                )
                return
                
            # Get connection info
            connection_info = self.active_connections[connection_id]
            
            # Calculate duration
            duration = time.time() - connection_info["open_time"]
            
            # Remove from active connections
            del self.active_connections[connection_id]
            
            # Update metrics
            self.metrics_registry.update_metric("websocket.connections.active", len(self.active_connections))
            
            # Update connection history
            for entry in self.connection_history:
                if entry.get("connection_id") == connection_id:
                    entry["close_time"] = time.time()
                    entry["duration"] = duration
                    entry["close_details"] = details
                    break
                    
            logger.structured_log(
                LogLevel.INFO,
                f"WebSocket connection closed: {connection_id}",
                LogCategory.CONNECTION,
                component="connection_monitor",
                context={
                    "connection_id": connection_id,
                    "duration": duration,
                    "messages_received": connection_info["messages_received"],
                    "messages_sent": connection_info["messages_sent"],
                    "bytes_received": connection_info["bytes_received"],
                    "bytes_sent": connection_info["bytes_sent"],
                    "close_details": details,
                    "monitor_id": self.monitor_id
                }
            )
        
    def message_received(self, 
                       connection_id: str, 
                       message: Union[str, bytes],
                       message_type: Optional[str] = None) -> None:
        """
        Register a received message.
        
        Args:
            connection_id: Connection ID
            message: Message content
            message_type: Optional message type
        """
        with self.lock:
            if connection_id not in self.active_connections:
                logger.structured_log(
                    LogLevel.WARNING,
                    f"Message received on unknown connection: {connection_id}",
                    LogCategory.CONNECTION,
                    component="connection_monitor",
                    context={"monitor_id": self.monitor_id}
                )
                return
                
            # Update connection info
            connection_info = self.active_connections[connection_id]
            connection_info["last_activity_time"] = time.time()
            connection_info["messages_received"] += 1
            
            # Calculate message size
            size = len(message) if isinstance(message, (str, bytes)) else 0
            connection_info["bytes_received"] += size
            
            # Update metrics
            self.metrics_registry.update_metric("websocket.messages.received", 1)
            self.metrics_registry.update_metric("websocket.messages.size", size)
            
            # Log high rate or large messages
            if size > 10000:  # Log large messages (>10KB)
                logger.structured_log(
                    LogLevel.DEBUG,
                    f"Large message received on connection {connection_id}",
                    LogCategory.CONNECTION,
                    component="connection_monitor",
                    context={
                        "connection_id": connection_id,
                        "message_size": size,
                        "message_type": message_type,
                        "monitor_id": self.monitor_id
                    }
                )
        
    def message_sent(self, 
                   connection_id: str, 
                   message: Union[str, bytes],
                   message_type: Optional[str] = None) -> None:
        """
        Register a sent message.
        
        Args:
            connection_id: Connection ID
            message: Message content
            message_type: Optional message type
        """
        with self.lock:
            if connection_id not in self.active_connections:
                logger.structured_log(
                    LogLevel.WARNING,
                    f"Message sent on unknown connection: {connection_id}",
                    LogCategory.CONNECTION,
                    component="connection_monitor",
                    context={"monitor_id": self.monitor_id}
                )
                return
                
            # Update connection info
            connection_info = self.active_connections[connection_id]
            connection_info["last_activity_time"] = time.time()
            connection_info["messages_sent"] += 1
            
            # Calculate message size
            size = len(message) if isinstance(message, (str, bytes)) else 0
            connection_info["bytes_sent"] += size
            
            # Update metrics
            self.metrics_registry.update_metric("websocket.messages.sent", 1)
            
            # Log high rate or large messages
            if size > 10000:  # Log large messages (>10KB)
                logger.structured_log(
                    LogLevel.DEBUG,
                    f"Large message sent on connection {connection_id}",
                    LogCategory.CONNECTION,
                    component="connection_monitor",
                    context={
                        "connection_id": connection_id,
                        "message_size": size,
                        "message_type": message_type,
                        "monitor_id": self.monitor_id
                    }
                )
        
    async def _monitor_connections(self) -> None:
        """Monitor connections for timeouts and health."""
        try:
            while not self._stop_monitor:
                try:
                    await self._check_connections()
                    
                    # Log connection statistics
                    with self.lock:
                        connection_count = len(self.active_connections)
                        
                        if connection_count > 0:
                            logger.structured_log(
                                LogLevel.DEBUG,
                                f"Connection monitor status: {connection_count} active connections",
                                LogCategory.CONNECTION,
                                component="connection_monitor",
                                context={
                                    "active_connections": connection_count,
                                    "monitor_id": self.monitor_id
                                }
                            )
                    
                    # Wait for next check
                    await asyncio.sleep(self.check_interval)
                    
                except asyncio.CancelledError:
                    # Task canceled, exit
                    break
                except Exception as e:
                    logger.structured_log(
                        LogLevel.ERROR,
                        f"Error in connection monitor: {e}",
                        LogCategory.CONNECTION,
                        component="connection_monitor",
                        context={"monitor_id": self.monitor_id},
                        error=str(e)
                    )
                    
                    # Continue monitoring
                    await asyncio.sleep(self.check_interval)
                    
        except asyncio.CancelledError:
            # Task canceled
            pass
        
    async def _check_connections(self) -> None:
        """Check connections for timeouts."""
        current_time = time.time()
        timed_out_connections = []
        
        # Find timed out connections
        with self.lock:
            for connection_id, info in self.active_connections.items():
                # Check if connection has timed out
                idle_time = current_time - info["last_activity_time"]
                
                if idle_time > self.connection_timeout:
                    timed_out_connections.append(connection_id)
                    
                    logger.structured_log(
                        LogLevel.WARNING,
                        f"Connection timed out: {connection_id}",
                        LogCategory.CONNECTION,
                        component="connection_monitor",
                        context={
                            "connection_id": connection_id,
                            "idle_time": idle_time,
                            "timeout": self.connection_timeout,
                            "monitor_id": self.monitor_id
                        }
                    )
        
        # Close timed out connections
        for connection_id in timed_out_connections:
            with self.lock:
                if connection_id in self.active_connections:
                    websocket = self.active_connections[connection_id]["websocket"]
                    
                    try:
                        await websocket.close(1001, "Connection timeout")
                    except Exception as e:
                        logger.structured_log(
                            LogLevel.ERROR,
                            f"Error closing timed out connection {connection_id}: {e}",
                            LogCategory.CONNECTION,
                            component="connection_monitor",
                            context={"connection_id": connection_id, "monitor_id": self.monitor_id},
                            error=str(e)
                        )
                        
                    # Remove from active connections
                    self.connection_closed(connection_id, {"reason": "timeout"})
        
    def get_active_connections(self) -> List[Dict[str, Any]]:
        """
        Get a list of active connections.
        
        Returns:
            List of connection information dictionaries
        """
        with self.lock:
            # Create a copy without WebSocket objects
            connections = []
            
            for conn_id, info in self.active_connections.items():
                conn_info = info.copy()
                conn_info.pop("websocket", None)  # Remove WebSocket object
                connections.append(conn_info)
                
            return connections
        
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get connection statistics.
        
        Returns:
            Dictionary with connection statistics
        """
        with self.lock:
            active_count = len(self.active_connections)
            
            # Calculate totals
            messages_received = sum(conn["messages_received"] for conn in self.active_connections.values())
            messages_sent = sum(conn["messages_sent"] for conn in self.active_connections.values())
            bytes_received = sum(conn["bytes_received"] for conn in self.active_connections.values())
            bytes_sent = sum(conn["bytes_sent"] for conn in self.active_connections.values())
            
            return {
                "active_connections": active_count,
                "historical_connections": len(self.connection_history),
                "messages_received": messages_received,
                "messages_sent": messages_sent,
                "bytes_received": bytes_received,
                "bytes_sent": bytes_sent,
                "monitor_id": self.monitor_id
            }


# Singleton instances for connection monitors
_connection_monitors: Dict[str, ConnectionMonitor] = {}


def get_connection_monitor(monitor_id: Optional[str] = None) -> ConnectionMonitor:
    """
    Get a connection monitor instance.
    
    Args:
        monitor_id: Optional monitor ID (for multiple server instances)
        
    Returns:
        ConnectionMonitor instance
    """
    global _connection_monitors
    
    # Use default monitor ID if not provided
    if monitor_id is None:
        monitor_id = "default"
        
    # Create monitor if needed
    if monitor_id not in _connection_monitors:
        _connection_monitors[monitor_id] = ConnectionMonitor()
        
    return _connection_monitors[monitor_id]