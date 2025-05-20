"""
Error types for RFM Architecture UI.

This module defines the custom exception hierarchy used throughout the application.
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Union


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCode(Enum):
    """Error codes for categorizing errors."""
    # General errors
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    INVALID_PARAMETER = "INVALID_PARAMETER"
    OPERATION_TIMEOUT = "OPERATION_TIMEOUT"
    
    # Rendering errors
    RENDER_FAILED = "RENDER_FAILED"
    INVALID_FRACTAL_TYPE = "INVALID_FRACTAL_TYPE"
    COMPUTATION_DIVERGED = "COMPUTATION_DIVERGED"
    MEMORY_EXCEEDED = "MEMORY_EXCEEDED"
    MAX_ITERATIONS_EXCEEDED = "MAX_ITERATIONS_EXCEEDED"
    
    # IO errors
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_PERMISSION_DENIED = "FILE_PERMISSION_DENIED"
    INVALID_FILE_FORMAT = "INVALID_FILE_FORMAT"
    
    # UI errors
    UI_INITIALIZATION_FAILED = "UI_INITIALIZATION_FAILED"
    WIDGET_CREATION_FAILED = "WIDGET_CREATION_FAILED"
    RENDERING_CONTEXT_ERROR = "RENDERING_CONTEXT_ERROR"


class FractalError(Exception):
    """Base class for all fractal-related errors."""
    
    def __init__(
        self, 
        message: str, 
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        details: Optional[Dict[str, Any]] = None,
        remediation: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        """
        Initialize a FractalError.
        
        Args:
            message: Human-readable error message
            error_code: Categorized error code
            severity: Error severity level
            details: Additional contextual details about the error
            remediation: Suggested remediation steps
            original_exception: Original exception if this is a wrapper
        """
        self.message = message
        self.error_code = error_code
        self.severity = severity
        self.details = details or {}
        self.remediation = remediation
        self.original_exception = original_exception
        super().__init__(self.message)
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the error to a dictionary for serialization.
        
        Returns:
            Dictionary representation of the error
        """
        return {
            "message": self.message,
            "error_code": self.error_code.value,
            "severity": self.severity.value,
            "details": self.details,
            "remediation": self.remediation,
            "original_exception": str(self.original_exception) if self.original_exception else None
        }
        
    def __str__(self) -> str:
        """
        String representation of the error.
        
        Returns:
            String representation with code, message and optionally remediation
        """
        result = f"{self.error_code.value}: {self.message}"
        if self.remediation:
            result += f" - {self.remediation}"
        return result


class ParameterError(FractalError):
    """Error related to invalid parameters."""
    
    def __init__(
        self, 
        message: str, 
        param_name: str,
        expected_type: Optional[Union[str, List[str]]] = None,
        expected_range: Optional[List[Any]] = None,
        actual_value: Optional[Any] = None,
        **kwargs
    ):
        """
        Initialize a ParameterError.
        
        Args:
            message: Human-readable error message
            param_name: Name of the parameter that caused the error
            expected_type: Expected type of the parameter
            expected_range: Expected range or allowed values
            actual_value: Actual value that caused the error
            **kwargs: Additional arguments to pass to FractalError
        """
        details = {
            "param_name": param_name,
            "expected_type": expected_type,
            "expected_range": expected_range,
            "actual_value": actual_value
        }
        
        # Build remediation message
        remediation = f"Check the value of parameter '{param_name}'"
        if expected_type:
            remediation += f", expected type: {expected_type}"
        if expected_range:
            remediation += f", expected range: {expected_range}"
            
        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_PARAMETER,
            details=details,
            remediation=remediation,
            **kwargs
        )


class RenderError(FractalError):
    """Error related to fractal rendering."""
    
    def __init__(
        self, 
        message: str, 
        fractal_type: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize a RenderError.
        
        Args:
            message: Human-readable error message
            fractal_type: Type of fractal being rendered
            params: Parameters used for rendering
            **kwargs: Additional arguments to pass to FractalError
        """
        details = {
            "fractal_type": fractal_type,
            "params": params
        }
        remediation = "Try different rendering parameters"
        
        super().__init__(
            message=message,
            error_code=ErrorCode.RENDER_FAILED,
            details=details,
            remediation=remediation,
            **kwargs
        )


class IOError(FractalError):
    """Error related to file operations."""
    
    def __init__(
        self, 
        message: str, 
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize an IOError.
        
        Args:
            message: Human-readable error message
            file_path: Path to the file that caused the error
            operation: Operation that was being performed
            **kwargs: Additional arguments to pass to FractalError
        """
        details = {
            "file_path": file_path,
            "operation": operation
        }
        remediation = f"Check file path and permissions: {file_path}" if file_path else "Check file path and permissions"
        
        # Determine error code based on the message
        if "not found" in message.lower():
            error_code = ErrorCode.FILE_NOT_FOUND
        elif "permission" in message.lower():
            error_code = ErrorCode.FILE_PERMISSION_DENIED
        elif "format" in message.lower():
            error_code = ErrorCode.INVALID_FILE_FORMAT
        else:
            error_code = kwargs.get("error_code", ErrorCode.UNKNOWN_ERROR)
        
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            remediation=remediation,
            **kwargs
        )


class UIError(FractalError):
    """Error related to the user interface."""
    
    def __init__(
        self, 
        message: str, 
        component: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize a UIError.
        
        Args:
            message: Human-readable error message
            component: UI component that caused the error
            **kwargs: Additional arguments to pass to FractalError
        """
        details = {
            "component": component
        }
        remediation = "Try restarting the application"
        
        # Determine error code based on the message
        if "initialization" in message.lower():
            error_code = ErrorCode.UI_INITIALIZATION_FAILED
        elif "widget" in message.lower() or "creation" in message.lower():
            error_code = ErrorCode.WIDGET_CREATION_FAILED
        elif "rendering" in message.lower() or "context" in message.lower():
            error_code = ErrorCode.RENDERING_CONTEXT_ERROR
        else:
            error_code = kwargs.get("error_code", ErrorCode.UNKNOWN_ERROR)
        
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            remediation=remediation,
            **kwargs
        )


# Domain-specific errors
class MandelbrotError(RenderError):
    """Error specific to Mandelbrot set rendering."""
    pass


class JuliaError(RenderError):
    """Error specific to Julia set rendering."""
    pass


class LSystemError(RenderError):
    """Error specific to L-System rendering."""
    pass


class CantorError(RenderError):
    """Error specific to Cantor set rendering."""
    pass