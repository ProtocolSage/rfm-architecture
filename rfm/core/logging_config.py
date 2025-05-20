"""
Logging configuration for RFM Architecture.

This module provides a comprehensive logging configuration for the RFM
Architecture, with support for structured logging, performance tracking,
and integration with monitoring systems.
"""

import os
import sys
import time
import json
import logging
import logging.config
import logging.handlers
import threading
import traceback
import uuid
import socket
from typing import Dict, Any, Optional, Union, List, Tuple
from pathlib import Path
from datetime import datetime
from enum import Enum


class LogLevel(str, Enum):
    """Log levels for the application."""
    
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(str, Enum):
    """Log categories for structured logging."""
    
    CONNECTION = "connection"     # WebSocket connection events
    OPERATION = "operation"       # Operation lifecycle events
    PERFORMANCE = "performance"   # Performance metrics
    SECURITY = "security"         # Security-related events
    SYSTEM = "system"             # System-level events
    UI = "ui"                     # User interface events
    USER = "user"                 # User-initiated actions


class StructuredLogRecord(logging.LogRecord):
    """Enhanced LogRecord with structured data capabilities."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the log record with structured data support."""
        super().__init__(*args, **kwargs)
        self.correlation_id = getattr(threading.current_thread(), "correlation_id", None)
        self.category = None
        self.context = {}
        self.event_id = str(uuid.uuid4())
        self.operation_id = None
        self.component = None
        self.host = socket.gethostname()
        self.timing = {}


class StructuredLogger(logging.Logger):
    """Enhanced logger with support for structured logging."""
    
    def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None, sinfo=None):
        """Create a structured log record."""
        if extra is None:
            extra = {}
            
        # Create record with StructuredLogRecord
        record = StructuredLogRecord(name, level, fn, lno, msg, args, exc_info, func, sinfo)
        
        # Add extra fields
        for key, value in extra.items():
            setattr(record, key, value)
            
        return record
    
    def structured_log(self, 
                    level: Union[int, str], 
                    msg: str, 
                    category: LogCategory, 
                    correlation_id: Optional[str] = None,
                    operation_id: Optional[str] = None,
                    component: Optional[str] = None,
                    context: Optional[Dict[str, Any]] = None,
                    timing: Optional[Dict[str, float]] = None,
                    **kwargs) -> None:
        """
        Log a structured message.
        
        Args:
            level: Log level
            msg: Log message
            category: Log category
            correlation_id: Optional correlation ID for request tracing
            operation_id: Optional operation ID for associating with progress tracking
            component: Optional component name
            context: Optional context data
            timing: Optional timing information
            **kwargs: Additional log fields
        """
        # Get numeric level if string
        if isinstance(level, str):
            level = logging.getLevelName(level)
            
        # Set correlation ID on current thread if provided
        if correlation_id:
            threading.current_thread().correlation_id = correlation_id
            
        # Create extra fields
        extra = {
            "category": category,
            "operation_id": operation_id,
            "component": component,
            "context": context or {},
            "timing": timing or {}
        }
        
        # Add additional fields
        for key, value in kwargs.items():
            extra[key] = value
            
        # Log the message
        self.log(level, msg, extra=extra)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def __init__(self, **kwargs):
        """Initialize the JSON formatter."""
        super().__init__()
        self.additional_fields = kwargs
    
    def format(self, record):
        """Format the record as JSON."""
        # Create base structure
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            # Use getMessage() to retrieve the formatted log message
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
            "function": record.funcName,
            "process": record.process,
            "thread": record.thread,
            "host": getattr(record, "host", socket.gethostname())
        }
        
        # Add structured fields
        for field in ["category", "correlation_id", "context", "event_id", 
                     "operation_id", "component", "timing"]:
            if hasattr(record, field) and getattr(record, field) is not None:
                log_data[field] = getattr(record, field)
                
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": str(record.exc_info[0].__name__),
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
            
        # Add additional fields
        for key, value in self.additional_fields.items():
            if key not in log_data:
                log_data[key] = value
        
        # Convert to JSON
        return json.dumps(log_data)


class RotatingFileHandlerWithCompression(logging.handlers.RotatingFileHandler):
    """Rotating file handler with compression support."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the handler with compression support."""
        self.compress_backend = kwargs.pop("compress_backend", "gzip")
        super().__init__(*args, **kwargs)
    
    def doRollover(self):
        """Compress log file after rollover."""
        # Perform normal rollover
        super().doRollover()
        
        # Compress the rolled-over file
        if self.compress_backend:
            try:
                backup_file = f"{self.baseFilename}.1"
                if os.path.exists(backup_file):
                    if self.compress_backend == "gzip":
                        import gzip
                        with open(backup_file, "rb") as f_in:
                            with gzip.open(f"{backup_file}.gz", "wb") as f_out:
                                f_out.writelines(f_in)
                        os.remove(backup_file)
            except Exception as e:
                sys.stderr.write(f"Error compressing log file: {e}\n")


def configure_logging(
    app_name: str,
    log_dir: Optional[str] = None,
    console_level: LogLevel = LogLevel.INFO,
    file_level: LogLevel = LogLevel.DEBUG,
    json_format: bool = True,
    max_bytes: int = 10485760,  # 10 MB
    backup_count: int = 5,
    compress_logs: bool = True,
    correlation_id: Optional[str] = None
) -> None:
    """
    Configure application logging.
    
    Args:
        app_name: Application name for log files
        log_dir: Directory for log files (default: ./logs)
        console_level: Log level for console output
        file_level: Log level for file output
        json_format: Whether to use JSON format for file logs
        max_bytes: Maximum log file size in bytes
        backup_count: Number of backup log files to keep
        compress_logs: Whether to compress rotated log files
        correlation_id: Optional correlation ID to set on current thread
    """
    # Convert LogLevel enums to valid types for handlers
    from .logging_config import LogLevel  # ensure reference to LogLevel in this scope
    if isinstance(console_level, LogLevel):
        console_level = console_level.value
    if isinstance(file_level, LogLevel):
        file_level = file_level.value
    # Register custom logger class
    logging.setLoggerClass(StructuredLogger)
    
    # Set correlation ID on current thread if provided
    if correlation_id:
        threading.current_thread().correlation_id = correlation_id
    
    # Create log directory
    if log_dir is None:
        log_dir = os.path.join(os.getcwd(), "logs")
        
    os.makedirs(log_dir, exist_ok=True)
    
    # Create formatters
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create JSON formatter for file logging if requested
    if json_format:
        file_formatter = JSONFormatter(application=app_name)
    else:
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s - "
            "[%(category)s] [%(correlation_id)s] [%(operation_id)s] [%(component)s]"
        )
    
    # Create handlers
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)
    
    # Create log file name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(log_dir, f"{app_name}_{timestamp}.log")
    
    # Create file handler
    file_handler = RotatingFileHandlerWithCompression(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        compress_backend="gzip" if compress_logs else None
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(file_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Allow all levels, handlers will filter
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    # Add new handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Log configuration
    logger = logging.getLogger(__name__)
    logger.structured_log(
        LogLevel.INFO,
        f"Logging configured for {app_name}",
        LogCategory.SYSTEM,
        correlation_id=correlation_id,
        component="logging_config",
        context={
            "console_level": console_level,
            "file_level": file_level,
            "json_format": json_format,
            "log_dir": log_dir,
            "log_file": log_file
        }
    )


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger.
    
    Args:
        name: Logger name
        
    Returns:
        StructuredLogger instance
    """
    return logging.getLogger(name)


# Structured logging context manager for timing operations
class TimingContext:
    """Context manager for timing operations with structured logging."""
    
    def __init__(self, 
                logger: StructuredLogger, 
                operation: str, 
                level: LogLevel = LogLevel.DEBUG,
                category: LogCategory = LogCategory.PERFORMANCE,
                correlation_id: Optional[str] = None,
                operation_id: Optional[str] = None,
                component: Optional[str] = None,
                context: Optional[Dict[str, Any]] = None):
        """
        Initialize the timing context.
        
        Args:
            logger: Logger to use
            operation: Operation name
            level: Log level
            category: Log category
            correlation_id: Optional correlation ID
            operation_id: Optional operation ID
            component: Optional component name
            context: Optional context data
        """
        self.logger = logger
        self.operation = operation
        self.level = level
        self.category = category
        self.correlation_id = correlation_id
        self.operation_id = operation_id
        self.component = component
        self.context = context or {}
        self.start_time = None
        self.end_time = None
        
    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        
        # Log start of operation
        self.logger.structured_log(
            self.level,
            f"Starting operation: {self.operation}",
            self.category,
            correlation_id=self.correlation_id,
            operation_id=self.operation_id,
            component=self.component,
            context=self.context,
            timing={"start_time": self.start_time}
        )
        
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timing and log results."""
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        
        # Create timing information
        timing = {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": duration
        }
        
        # Update context
        context = self.context.copy()
        context["duration_ms"] = duration * 1000
        
        if exc_type is not None:
            # Log error
            self.logger.structured_log(
                LogLevel.ERROR,
                f"Operation failed: {self.operation}",
                self.category,
                correlation_id=self.correlation_id,
                operation_id=self.operation_id,
                component=self.component,
                context=context,
                timing=timing,
                error=str(exc_val),
                error_type=exc_type.__name__,
                success=False
            )
        else:
            # Log success
            self.logger.structured_log(
                self.level,
                f"Completed operation: {self.operation} in {duration*1000:.2f}ms",
                self.category,
                correlation_id=self.correlation_id,
                operation_id=self.operation_id,
                component=self.component,
                context=context,
                timing=timing,
                success=True
            )
            
        # Don't suppress exceptions
        return False


# Function decorator for timing
def log_timing(operation: str,
             level: LogLevel = LogLevel.DEBUG,
             category: LogCategory = LogCategory.PERFORMANCE,
             component: Optional[str] = None):
    """
    Decorator for timing function execution with structured logging.
    
    Args:
        operation: Operation name
        level: Log level
        category: Log category
        component: Optional component name
        
    Returns:
        Function decorator
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get logger from module name
            logger = get_logger(func.__module__)
            
            # Get correlation ID and operation ID from kwargs if present
            correlation_id = kwargs.pop("correlation_id", None)
            operation_id = kwargs.pop("operation_id", None)
            
            # Create context
            context = {
                "function": func.__name__,
                "module": func.__module__
            }
            
            # Add timing context
            with TimingContext(
                logger,
                operation,
                level,
                category,
                correlation_id,
                operation_id,
                component,
                context
            ):
                return func(*args, **kwargs)
                
        return wrapper
    
    return decorator