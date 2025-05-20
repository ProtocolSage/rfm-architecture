"""
Integration module for connecting the database with other RFM components.

This module provides integration classes and functions to connect
the database with other components of the RFM system.
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable, Coroutine, Set, Union

from rfm.core.progress import ProgressData, ProgressReporter, get_progress_manager
from rfm.database.service import ProgressService, PerformanceService

logger = logging.getLogger(__name__)


class DatabaseProgressListener:
    """
    Listens for progress updates and stores them in the database.
    
    This class connects the in-memory progress tracking system with
    the persistent database storage for progress records.
    """
    
    def __init__(self):
        """Initialize the database progress listener."""
        self.progress_service = ProgressService()
        self.record_map: Dict[str, int] = {}  # Maps operation_id to database record_id
        
    def start(self):
        """Start listening for progress updates."""
        progress_manager = get_progress_manager()
        progress_manager.add_callback(self.handle_progress_update)
        logger.info("Database progress listener started")
        
    def stop(self):
        """Stop listening for progress updates."""
        progress_manager = get_progress_manager()
        progress_manager.remove_callback(self.handle_progress_update)
        logger.info("Database progress listener stopped")
        
    def handle_progress_update(self, progress_data: ProgressData):
        """
        Handle a progress update by storing it in the database.
        
        Args:
            progress_data: Progress update data
        """
        try:
            operation_id = progress_data.operation_id
            
            # If this is a new operation, create a database record
            if operation_id not in self.record_map:
                record = self.progress_service.create_progress_record(
                    operation_type=getattr(progress_data, "operation_type", "unknown"),
                    total_steps=progress_data.total_steps,
                    operation_data={
                        "operation_id": operation_id,
                        "start_time": datetime.fromtimestamp(progress_data.timestamp).isoformat()
                    }
                )
                self.record_map[operation_id] = record["id"]
                logger.debug(f"Created database record {record['id']} for operation {operation_id}")
                
            # Update the existing record
            record_id = self.record_map[operation_id]
            
            # Map progress status to database status
            status_map = {
                "pending": "pending",
                "running": "in_progress",
                "paused": "in_progress",
                "completed": "completed",
                "failed": "failed",
                "canceled": "failed"
            }
            
            status = status_map.get(progress_data.status, "in_progress")
            
            if status == "completed":
                self.progress_service.complete_progress(
                    record_id,
                    message=progress_data.current_step
                )
            elif status == "failed":
                error_details = (
                    progress_data.details.get("error_message", "Unknown error")
                    if progress_data.details
                    else "Unknown error"
                )
                self.progress_service.fail_progress(record_id, error_details)
            else:
                # Regular progress update
                self.progress_service.update_progress(
                    record_id,
                    progress_percent=progress_data.progress,
                    current_step=progress_data.current_step
                )
                
        except Exception as e:
            logger.error(f"Error updating progress in database: {e}")


class DatabasePerformanceTracker:
    """
    Tracks performance metrics and stores them in the database.
    
    This class provides methods for recording performance metrics
    in the database for later analysis.
    """
    
    def __init__(self):
        """Initialize the database performance tracker."""
        self.performance_service = PerformanceService()
        
    def record_render_time(self, 
                         value_ms: float, 
                         context: Optional[Dict[str, Any]] = None,
                         user_id: Optional[int] = None) -> None:
        """
        Record a render time metric.
        
        Args:
            value_ms: Render time in milliseconds
            context: Optional context information
            user_id: Optional user ID
        """
        try:
            self.performance_service.record_metric(
                metric_type="render_time",
                value=value_ms,
                unit="ms",
                context=context,
                user_id=user_id
            )
        except Exception as e:
            logger.error(f"Error recording render time metric: {e}")
            
    def record_memory_usage(self, 
                          value_mb: float, 
                          context: Optional[Dict[str, Any]] = None,
                          user_id: Optional[int] = None) -> None:
        """
        Record a memory usage metric.
        
        Args:
            value_mb: Memory usage in megabytes
            context: Optional context information
            user_id: Optional user ID
        """
        try:
            self.performance_service.record_metric(
                metric_type="memory_usage",
                value=value_mb,
                unit="MB",
                context=context,
                user_id=user_id
            )
        except Exception as e:
            logger.error(f"Error recording memory usage metric: {e}")
            
    def record_fps(self, 
                 value: float, 
                 context: Optional[Dict[str, Any]] = None,
                 user_id: Optional[int] = None) -> None:
        """
        Record an FPS metric.
        
        Args:
            value: Frames per second
            context: Optional context information
            user_id: Optional user ID
        """
        try:
            self.performance_service.record_metric(
                metric_type="fps",
                value=value,
                unit="fps",
                context=context,
                user_id=user_id
            )
        except Exception as e:
            logger.error(f"Error recording FPS metric: {e}")
            
    def get_average_render_time(self, days: int = 1) -> float:
        """
        Get average render time for the past N days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Average render time in milliseconds
        """
        try:
            return self.performance_service.get_average("render_time", days)
        except Exception as e:
            logger.error(f"Error getting average render time: {e}")
            return 0.0
            
    def get_average_memory_usage(self, days: int = 1) -> float:
        """
        Get average memory usage for the past N days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Average memory usage in megabytes
        """
        try:
            return self.performance_service.get_average("memory_usage", days)
        except Exception as e:
            logger.error(f"Error getting average memory usage: {e}")
            return 0.0
            
    def get_average_fps(self, days: int = 1) -> float:
        """
        Get average FPS for the past N days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Average FPS
        """
        try:
            return self.performance_service.get_average("fps", days)
        except Exception as e:
            logger.error(f"Error getting average FPS: {e}")
            return 0.0


# Initialize and start the database progress listener
def init_database_integrations():
    """Initialize and start the database integrations."""
    try:
        # Initialize progress listener
        progress_listener = DatabaseProgressListener()
        progress_listener.start()
        
        # Initialize performance tracker
        performance_tracker = DatabasePerformanceTracker()
        
        logger.info("Database integrations initialized")
        
        return progress_listener, performance_tracker
    except Exception as e:
        logger.error(f"Failed to initialize database integrations: {e}")
        return None, None