"""
Error handler for RFM Architecture UI.

This module provides centralized error handling and logging capabilities.
"""

import logging
import traceback
import sys
import threading
import json
import os
from typing import Dict, Any, Callable, List, Optional, Set, Tuple
from datetime import datetime
import time

from .types import FractalError, ErrorCode, ErrorSeverity


class ErrorHandler:
    """
    Centralized error handling for the fractal application.
    
    This class provides a centralized way to handle errors throughout the application,
    including logging, displaying errors to the user, and recording error statistics.
    """
    
    def __init__(self, log_dir: str = "./error_logs"):
        """
        Initialize the error handler.
        
        Args:
            log_dir: Directory to store error logs
        """
        self.log_dir = log_dir
        self.handlers: Dict[ErrorCode, List[Callable[[FractalError], None]]] = {}
        self.default_handlers: List[Callable[[FractalError], None]] = []
        self.error_log: List[FractalError] = []
        self.lock = threading.RLock()
        self.error_counts: Dict[ErrorCode, int] = {code: 0 for code in ErrorCode}
        self.last_error_time: Dict[ErrorCode, float] = {}
        
        # Configure logging
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        self.logger = logging.getLogger("fractal_error_handler")
        self.logger.setLevel(logging.DEBUG)
        
        # File handler
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_handler = logging.FileHandler(
            os.path.join(log_dir, f"error_log_{timestamp}.log")
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def register_handler(self, 
                         handler: Callable[[FractalError], None], 
                         error_codes: Optional[List[ErrorCode]] = None):
        """
        Register a handler for specific error codes or as a default handler.
        
        Args:
            handler: Function to call when the specified error occurs
            error_codes: List of error codes to handle, or None for all errors
        """
        with self.lock:
            if error_codes:
                for code in error_codes:
                    if code not in self.handlers:
                        self.handlers[code] = []
                    self.handlers[code].append(handler)
            else:
                self.default_handlers.append(handler)
                
    def handle_error(self, error: Exception) -> bool:
        """
        Handle an exception by converting it to a FractalError if needed,
        logging it, and calling appropriate handlers.
        
        Args:
            error: The exception to handle
            
        Returns:
            True if the error was handled by at least one handler, False otherwise
        """
        # Convert to FractalError if it's not already
        if not isinstance(error, FractalError):
            error = self._convert_to_fractal_error(error)
            
        # Log the error
        self._log_error(error)
        
        # Update error statistics
        with self.lock:
            self.error_counts[error.error_code] += 1
            self.last_error_time[error.error_code] = time.time()
            
            # Store in in-memory log
            self.error_log.append(error)
            if len(self.error_log) > 100:  # Keep only the most recent 100 errors
                self.error_log.pop(0)
        
        # Call specific handlers
        handlers_called = False
        with self.lock:
            if error.error_code in self.handlers:
                for handler in self.handlers[error.error_code]:
                    try:
                        handler(error)
                        handlers_called = True
                    except Exception as e:
                        self.logger.error(f"Error in error handler: {e}")
            
            # Call default handlers if no specific handlers or as fallback
            if not handlers_called or not self.handlers.get(error.error_code):
                for handler in self.default_handlers:
                    try:
                        handler(error)
                        handlers_called = True
                    except Exception as e:
                        self.logger.error(f"Error in default error handler: {e}")
                        
        return handlers_called
                
    def _convert_to_fractal_error(self, error: Exception) -> FractalError:
        """
        Convert a standard exception to a FractalError.
        
        Args:
            error: The exception to convert
            
        Returns:
            Converted FractalError
        """
        from .types import ParameterError, IOError, UIError
        
        # Extract info from the exception
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_str = ''.join(traceback.format_tb(exc_traceback))
        
        # Determine error type based on the exception
        if isinstance(error, ValueError):
            return ParameterError(
                message=str(error),
                param_name="unknown",  # We don't know which parameter
                actual_value=None,  # We don't know the value
                severity=ErrorSeverity.ERROR,
                original_exception=error,
                details={"traceback": tb_str}
            )
        elif isinstance(error, (FileNotFoundError, PermissionError)):
            return IOError(
                message=str(error),
                severity=ErrorSeverity.ERROR,
                original_exception=error,
                details={"traceback": tb_str}
            )
        else:
            # Generic error
            return FractalError(
                message=str(error),
                error_code=ErrorCode.UNKNOWN_ERROR,
                severity=ErrorSeverity.ERROR,
                original_exception=error,
                details={"traceback": tb_str},
                remediation="Please report this error with the details from the log file"
            )
    
    def _log_error(self, error: FractalError):
        """
        Log the error to file and console.
        
        Args:
            error: The error to log
        """
        # Determine log level
        if error.severity == ErrorSeverity.INFO:
            log_level = logging.INFO
        elif error.severity == ErrorSeverity.WARNING:
            log_level = logging.WARNING
        elif error.severity == ErrorSeverity.CRITICAL:
            log_level = logging.CRITICAL
        else:
            log_level = logging.ERROR
            
        # Create log message
        log_message = f"{error.error_code.value}: {error.message}"
        if error.details:
            # Exclude traceback from main log message to avoid clutter
            details_for_log = {k: v for k, v in error.details.items() if k != "traceback"}
            if details_for_log:
                log_message += f" - Details: {json.dumps(details_for_log)}"
                
        if error.original_exception:
            log_message += f" - Original exception: {error.original_exception}"
            
        # Log the message
        self.logger.log(log_level, log_message)
        
        # If there's a traceback, log it separately at DEBUG level
        if error.details and "traceback" in error.details:
            self.logger.debug(f"Traceback for {error.error_code.value}: {error.details['traceback']}")
        
    def get_recent_errors(self, limit: Optional[int] = 10) -> List[FractalError]:
        """
        Get the most recent errors.
        
        Args:
            limit: Maximum number of errors to return
            
        Returns:
            List of recent errors
        """
        with self.lock:
            if limit is None or limit >= len(self.error_log):
                return self.error_log.copy()
            return self.error_log[-limit:]
    
    def get_error_stats(self) -> Dict[str, Any]:
        """
        Get statistics about errors that have occurred.
        
        Returns:
            Dictionary with error statistics
        """
        with self.lock:
            stats = {
                "total_errors": sum(self.error_counts.values()),
                "error_counts": {code.value: count for code, count in self.error_counts.items()},
                "most_common_errors": sorted(
                    [(code, count) for code, count in self.error_counts.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:5],
                "recent_errors": [e.to_dict() for e in self.get_recent_errors(5)]
            }
            return stats
            
    def clear_error_log(self):
        """Clear the in-memory error log."""
        with self.lock:
            self.error_log.clear()
            
    def export_error_log(self, filepath: str) -> bool:
        """
        Export the error log to a JSON file.
        
        Args:
            filepath: Path to save the export
            
        Returns:
            True if export was successful, False otherwise
        """
        try:
            with self.lock:
                log_data = {
                    "timestamp": datetime.now().isoformat(),
                    "error_counts": {code.value: count for code, count in self.error_counts.items()},
                    "errors": [e.to_dict() for e in self.error_log]
                }
                
            with open(filepath, 'w') as f:
                json.dump(log_data, f, indent=2)
                
            return True
        except Exception as e:
            self.logger.error(f"Error exporting error log: {e}")
            return False