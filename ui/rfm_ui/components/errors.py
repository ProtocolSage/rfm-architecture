"""
Errors module forwarder.

This module forwards imports from the top-level errors module to allow
components to import from '..errors' instead of 'rfm_ui.errors'.
"""

from rfm_ui.errors import (
    FractalError, ErrorCode, ErrorSeverity,
    ParameterError, RenderError, IOError, UIError,
    MandelbrotError, JuliaError, LSystemError, CantorError,
    error_boundary, error_context, validate_params,
    get_error_handler, setup_error_handling
)

# Export all symbols from errors module
__all__ = [
    'FractalError', 'ErrorCode', 'ErrorSeverity',
    'ParameterError', 'RenderError', 'IOError', 'UIError',
    'MandelbrotError', 'JuliaError', 'LSystemError', 'CantorError',
    'error_boundary', 'error_context', 'validate_params',
    'get_error_handler', 'setup_error_handling'
]

# Define a decorators module to allow imports from ..errors.decorators
class DecoratorsModule:
    """Module-like object to provide decorators."""

    @staticmethod
    def error_boundary(*args, **kwargs):
        """Forward to error_boundary decorator."""
        return error_boundary(*args, **kwargs)

    @staticmethod
    def error_context(*args, **kwargs):
        """Forward to error_context context manager."""
        return error_context(*args, **kwargs)

    @staticmethod
    def validate_params(*args, **kwargs):
        """Forward to validate_params function."""
        return validate_params(*args, **kwargs)

# Create a decorators module instance
decorators = DecoratorsModule()
