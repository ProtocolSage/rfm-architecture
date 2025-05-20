"""
Error handling module for RFM Architecture UI.

This module provides a comprehensive error handling system with custom exception types,
error boundaries, and UI components for displaying errors to users.
"""

from .types import (
    FractalError, ErrorCode, ErrorSeverity,
    ParameterError, RenderError, IOError, UIError,
    MandelbrotError, JuliaError, LSystemError, CantorError
)
from .handler import ErrorHandler

# Singleton error handler
_error_handler = None


def setup_error_handling(log_dir: str = "./error_logs") -> ErrorHandler:
    """
    Setup error handling system and return the error handler.

    Args:
        log_dir: Directory to store error logs

    Returns:
        Initialized error handler
    """
    global _error_handler

    # Create error handler if it doesn't exist
    if _error_handler is None:
        _error_handler = ErrorHandler(log_dir=log_dir)

    return _error_handler


def get_error_handler() -> ErrorHandler:
    """
    Get the global error handler instance.

    Returns:
        Global error handler instance
    """
    if _error_handler is None:
        return setup_error_handling()
    return _error_handler

# Import decorators after defining get_error_handler to avoid circular imports
from .decorators import error_boundary, error_context, validate_params