"""
Performance monitoring module for RFM Architecture UI.

This module provides tools for monitoring and visualizing application performance.
"""

from .tracker import PerformanceTracker, PerformanceRecord
from .visualizer import PerformanceVisualizer

# Singleton performance tracker
_performance_tracker = None


def setup_performance_monitoring(log_dir: str = "./performance_logs") -> PerformanceTracker:
    """
    Setup performance monitoring system and return the tracker.
    
    Args:
        log_dir: Directory to store performance logs
        
    Returns:
        Initialized performance tracker
    """
    global _performance_tracker
    
    # Create performance tracker if it doesn't exist
    if _performance_tracker is None:
        _performance_tracker = PerformanceTracker(log_dir=log_dir)
        
    return _performance_tracker


def get_performance_tracker() -> PerformanceTracker:
    """
    Get the global performance tracker instance.
    
    Returns:
        Global performance tracker instance
    """
    if _performance_tracker is None:
        return setup_performance_monitoring()
    return _performance_tracker