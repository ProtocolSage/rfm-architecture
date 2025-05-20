"""
Progress reporting system for RFM Architecture.

This module provides a progress tracking and reporting system for long-running operations
in the RFM Architecture. It enables real-time progress updates during complex computations.
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Coroutine, Set, Union

logger = logging.getLogger(__name__)


class OperationStatus(str, Enum):
    """Status of a tracked operation."""
    
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


@dataclass
class ProgressData:
    """Data for a progress update."""
    
    operation_id: str
    timestamp: float
    progress: float  # 0.0 to 100.0
    status: OperationStatus
    current_step: Optional[str] = None
    total_steps: Optional[int] = None
    current_step_progress: Optional[float] = None
    estimated_time_remaining_ms: Optional[int] = None
    memory_usage_mb: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        
        # Convert enum to string
        data["status"] = self.status.value if isinstance(self.status, Enum) else self.status
        
        return data


class ProgressReporter:
    """
    Reports progress updates for long-running operations.
    
    This class provides methods for reporting progress during operations,
    which can be consumed by progress listeners like the WebSocket server.
    """
    
    def __init__(self, operation_type: str, name: str = None):
        """
        Initialize a progress reporter.
        
        Args:
            operation_type: Type of operation (e.g., "fractal_render", "animation")
            name: Optional name for the operation
        """
        self.operation_id = str(uuid.uuid4())
        self.operation_type = operation_type
        self.name = name or f"{operation_type}_{self.operation_id[:8]}"
        self.start_time = time.time()
        self.last_update_time = self.start_time
        self.status = OperationStatus.PENDING
        self.progress = 0.0
        self.current_step = None
        self.total_steps = None
        self.current_step_progress = None
        self.details = {}
        self.callbacks: List[Callable[[ProgressData], None]] = []
        self.finished = False
        
        # Report initial status
        self.report_status(OperationStatus.PENDING)
        
        logger.debug(f"Created progress reporter for operation {self.name} ({self.operation_id})")
    
    def add_callback(self, callback: Callable[[ProgressData], None]) -> None:
        """
        Add a callback for progress updates.
        
        Args:
            callback: Function to call with progress updates
        """
        self.callbacks.append(callback)
    
    def report_progress(self, 
                      progress: float, 
                      current_step: Optional[str] = None,
                      total_steps: Optional[int] = None,
                      current_step_progress: Optional[float] = None,
                      estimated_time_remaining_ms: Optional[int] = None,
                      memory_usage_mb: Optional[float] = None,
                      details: Optional[Dict[str, Any]] = None) -> None:
        """
        Report progress for the operation.
        
        Args:
            progress: Overall progress percentage (0-100)
            current_step: Current processing step description
            total_steps: Total number of steps
            current_step_progress: Progress within current step (0-100)
            estimated_time_remaining_ms: Estimated time remaining in milliseconds
            memory_usage_mb: Current memory usage in MB
            details: Additional operation-specific details
        """
        if self.finished:
            return
            
        # Update state
        self.progress = max(0.0, min(100.0, progress))
        self.last_update_time = time.time()
        
        if current_step is not None:
            self.current_step = current_step
            
        if total_steps is not None:
            self.total_steps = total_steps
            
        if current_step_progress is not None:
            self.current_step_progress = current_step_progress
            
        if details is not None:
            self.details.update(details)
        
        # Set status to running if not completed/failed/canceled
        if self.status == OperationStatus.PENDING:
            self.status = OperationStatus.RUNNING
        
        # Create progress data
        progress_data = ProgressData(
            operation_id=self.operation_id,
            timestamp=self.last_update_time,
            progress=self.progress,
            status=self.status,
            current_step=self.current_step,
            total_steps=self.total_steps,
            current_step_progress=self.current_step_progress,
            estimated_time_remaining_ms=estimated_time_remaining_ms,
            memory_usage_mb=memory_usage_mb,
            details=self.details.copy()
        )
        
        # Call callbacks
        for callback in self.callbacks:
            try:
                callback(progress_data)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")
        
        # Auto-complete if reached 100%
        if self.progress >= 100.0 and self.status == OperationStatus.RUNNING:
            self.report_completed()
    
    def report_status(self, status: OperationStatus, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Report a status change for the operation.
        
        Args:
            status: New operation status
            details: Additional details about the status change
        """
        # Update state
        self.status = status
        self.last_update_time = time.time()
        
        if details is not None:
            self.details.update(details)
            
        # Create progress data
        progress_data = ProgressData(
            operation_id=self.operation_id,
            timestamp=self.last_update_time,
            progress=self.progress,
            status=self.status,
            current_step=self.current_step,
            total_steps=self.total_steps,
            current_step_progress=self.current_step_progress,
            details=self.details.copy()
        )
        
        # Call callbacks
        for callback in self.callbacks:
            try:
                callback(progress_data)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")
        
        # Mark as finished if terminal state
        if status in (OperationStatus.COMPLETED, OperationStatus.FAILED, OperationStatus.CANCELED):
            self.finished = True
    
    def report_completed(self, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Report that the operation has completed successfully.
        
        Args:
            details: Additional details about completion
        """
        # Set progress to 100% on completion
        self.progress = 100.0
        
        # Add completion details
        completion_details = {
            "duration_ms": int((time.time() - self.start_time) * 1000)
        }
        
        if details is not None:
            completion_details.update(details)
            
        self.report_status(OperationStatus.COMPLETED, completion_details)
    
    def report_failed(self, error_message: str, error_code: Optional[str] = None, 
                    details: Optional[Dict[str, Any]] = None) -> None:
        """
        Report that the operation has failed.
        
        Args:
            error_message: Error message
            error_code: Optional error code
            details: Additional details about the failure
        """
        # Add failure details
        failure_details = {
            "error_message": error_message,
            "duration_ms": int((time.time() - self.start_time) * 1000)
        }
        
        if error_code is not None:
            failure_details["error_code"] = error_code
            
        if details is not None:
            failure_details.update(details)
            
        self.report_status(OperationStatus.FAILED, failure_details)
    
    def report_canceled(self, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Report that the operation has been canceled.
        
        Args:
            details: Additional details about cancellation
        """
        # Add cancellation details
        cancellation_details = {
            "duration_ms": int((time.time() - self.start_time) * 1000)
        }
        
        if details is not None:
            cancellation_details.update(details)
            
        self.report_status(OperationStatus.CANCELED, cancellation_details)
    
    def should_cancel(self) -> bool:
        """
        Check if the operation has been marked for cancellation.
        
        Returns:
            True if the operation should be canceled, False otherwise
        """
        return self.status == OperationStatus.CANCELED
    
    def is_finished(self) -> bool:
        """
        Check if the operation has finished (completed, failed, or canceled).
        
        Returns:
            True if the operation has finished, False otherwise
        """
        return self.finished
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is not None:
            # Report failure on exception
            self.report_failed(
                error_message=str(exc_val),
                details={"exception_type": exc_type.__name__}
            )
        elif not self.finished:
            # Report completion if not already finished
            self.report_completed()


class ProgressManager:
    """
    Manages progress reporting for multiple operations.
    
    This class tracks and manages progress reporters for multiple concurrent
    operations, and provides methods for querying operation status and progress.
    """
    
    def __init__(self):
        """Initialize the progress manager."""
        self.operations: Dict[str, ProgressReporter] = {}
        self.callbacks: List[Callable[[ProgressData], None]] = []
        self.lock = asyncio.Lock()
    
    async def add_operation(self, operation: ProgressReporter) -> None:
        """
        Add an operation to track.
        
        Args:
            operation: ProgressReporter for the operation
        """
        async with self.lock:
            self.operations[operation.operation_id] = operation
            
            # Add global callback to the operation
            operation.add_callback(self._progress_callback)
    
    async def remove_operation(self, operation_id: str) -> None:
        """
        Remove an operation from tracking.
        
        Args:
            operation_id: ID of the operation to remove
        """
        async with self.lock:
            if operation_id in self.operations:
                del self.operations[operation_id]
    
    async def get_operation(self, operation_id: str) -> Optional[ProgressReporter]:
        """
        Get an operation by ID.
        
        Args:
            operation_id: ID of the operation
            
        Returns:
            ProgressReporter for the operation, or None if not found
        """
        async with self.lock:
            return self.operations.get(operation_id)
    
    async def list_operations(self) -> List[Dict[str, Any]]:
        """
        List all tracked operations.
        
        Returns:
            List of operation details
        """
        async with self.lock:
            return [
                {
                    "operation_id": op.operation_id,
                    "operation_type": op.operation_type,
                    "name": op.name,
                    "status": op.status.value,
                    "progress": op.progress,
                    "start_time": op.start_time,
                    "last_update_time": op.last_update_time
                }
                for op in self.operations.values()
            ]
    
    async def cancel_operation(self, operation_id: str) -> bool:
        """
        Request cancellation of an operation.
        
        Args:
            operation_id: ID of the operation to cancel
            
        Returns:
            True if the operation was found and cancellation was requested,
            False otherwise
        """
        async with self.lock:
            operation = self.operations.get(operation_id)
            if operation is None:
                return False
                
            # Only cancel if not already in a terminal state
            if operation.status not in (OperationStatus.COMPLETED, OperationStatus.FAILED, OperationStatus.CANCELED):
                operation.report_status(OperationStatus.CANCELED)
                return True
                
            return False
    
    def add_callback(self, callback: Callable[[ProgressData], None]) -> None:
        """
        Add a global callback for all progress updates.
        
        Args:
            callback: Function to call with progress updates
        """
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[ProgressData], None]) -> None:
        """
        Remove a global callback.
        
        Args:
            callback: Callback to remove
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def _progress_callback(self, progress_data: ProgressData) -> None:
        """
        Internal callback for progress updates from operations.
        
        Args:
            progress_data: Progress update data
        """
        # Call global callbacks
        for callback in self.callbacks:
            try:
                callback(progress_data)
            except Exception as e:
                logger.error(f"Error in global progress callback: {e}")
        
        # Clean up completed operations (after a delay)
        if progress_data.status in (OperationStatus.COMPLETED, OperationStatus.FAILED, OperationStatus.CANCELED):
            operation_id = progress_data.operation_id
            
            async def _cleanup_later():
                # Wait before cleanup to allow final status to be queried
                await asyncio.sleep(300)  # 5 minutes
                await self.remove_operation(operation_id)
                
            asyncio.create_task(_cleanup_later())


# Global progress manager instance
_progress_manager = None


def get_progress_manager() -> ProgressManager:
    """
    Get the global progress manager instance.
    
    Returns:
        ProgressManager instance
    """
    global _progress_manager
    if _progress_manager is None:
        _progress_manager = ProgressManager()
    return _progress_manager


# Decorator for progress tracking
def track_progress(operation_type: str, name: Optional[str] = None):
    """
    Decorator for tracking progress of a function.
    
    Args:
        operation_type: Type of operation
        name: Optional operation name
        
    Returns:
        Decorated function
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Create progress reporter
            reporter = ProgressReporter(operation_type, name)
            
            # Add to progress manager
            progress_manager = get_progress_manager()
            await progress_manager.add_operation(reporter)
            
            # Add reporter to kwargs if the function accepts it
            from inspect import signature
            sig = signature(func)
            if "progress_reporter" in sig.parameters:
                kwargs["progress_reporter"] = reporter
            
            try:
                # Call the function
                return await func(*args, **kwargs)
            except Exception as e:
                # Report failure
                reporter.report_failed(str(e))
                raise
            finally:
                # Ensure completion is reported
                if not reporter.is_finished():
                    reporter.report_completed()
        
        return wrapper
    
    return decorator