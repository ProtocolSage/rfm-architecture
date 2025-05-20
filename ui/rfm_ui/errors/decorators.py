"""
Error handling decorators and context managers.

This module provides decorators and context managers for error handling,
making it easy to create error boundaries around functions and code blocks.
"""

import functools
import contextlib
from typing import Callable, Any, Dict, Optional, List, Type, Tuple, TypeVar, cast

from .types import FractalError, ParameterError

# Import error handler
from . import get_error_handler

# Type variable for function return type
T = TypeVar('T')


def error_boundary(func: Optional[Callable[..., T]] = None, *, 
                  reraise: bool = False, 
                  error_callback: Optional[Callable[[Exception], None]] = None) -> Any:
    """
    Decorator to create an error boundary around a function.
    
    Args:
        func: Function to decorate
        reraise: Whether to reraise the error after handling
        error_callback: Optional callback to call with the error
        
    Returns:
        Decorated function
        
    Example:
        @error_boundary
        def my_function():
            # Function that might raise an exception
            
        @error_boundary(reraise=True)
        def another_function():
            # Errors will be handled but also reraised
    """
    def decorator(f: Callable[..., T]) -> Callable[..., Optional[T]]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Optional[T]:
            try:
                return f(*args, **kwargs)
            except Exception as e:
                # Handle the error
                error_handler = get_error_handler()
                handled = error_handler.handle_error(e)
                
                # Call the error callback if provided
                if error_callback:
                    try:
                        error_callback(e)
                    except Exception as callback_error:
                        error_handler.handle_error(callback_error)
                
                # Reraise if requested
                if reraise:
                    raise
                    
                # Return None to indicate error
                return None
        return wrapper
        
    if func is None:
        return decorator
    return decorator(func)


@contextlib.contextmanager
def error_context(context_name: str, 
                 context_data: Optional[Dict[str, Any]] = None, 
                 reraise: bool = False):
    """
    Context manager to create an error boundary.
    
    Args:
        context_name: Name of the context for error reporting
        context_data: Additional data to include in error reports
        reraise: Whether to reraise the error after handling
        
    Example:
        with error_context("render_fractal", {"params": params}):
            # Code that might raise an exception
    """
    try:
        yield
    except Exception as e:
        # Convert to FractalError if needed and add context
        if isinstance(e, FractalError):
            # Add context to existing FractalError
            if context_data:
                e.details.update(context_data)
            e.details["error_context"] = context_name
        
        # Handle the error
        error_handler = get_error_handler()
        handled = error_handler.handle_error(e)
        
        # Reraise if requested
        if reraise:
            raise


def validate_params(params: Dict[str, Any], 
                   schema: Dict[str, Dict[str, Any]]) -> None:
    """
    Validate parameters against a schema.
    
    Args:
        params: Parameters to validate
        schema: Validation schema
        
    Raises:
        ParameterError: If validation fails
        
    Example schema:
        {
            "width": {
                "type": int,
                "required": True,
                "range": [1, 1000]
            }
        }
    """
    for name, constraints in schema.items():
        # Check if required parameter is missing
        if constraints.get("required", False) and name not in params:
            raise ParameterError(
                message=f"Missing required parameter: {name}",
                param_name=name,
                expected_type=constraints.get("type", None),
                expected_range=constraints.get("range", None)
            )
            
        # Skip validation if parameter is not provided
        if name not in params:
            continue
            
        value = params[name]
        
        # Type validation
        if "type" in constraints:
            expected_type = constraints["type"]
            
            # Check if type is a list of allowed types
            if isinstance(expected_type, list) or isinstance(expected_type, tuple):
                if not any(isinstance(value, t) for t in expected_type):
                    type_names = [t.__name__ for t in expected_type]
                    raise ParameterError(
                        message=f"Invalid type for parameter {name}",
                        param_name=name,
                        expected_type=type_names,
                        actual_value=value
                    )
            else:
                # Single type check
                if not isinstance(value, expected_type):
                    raise ParameterError(
                        message=f"Invalid type for parameter {name}",
                        param_name=name,
                        expected_type=expected_type.__name__,
                        actual_value=value
                    )
                    
        # Range validation
        if "range" in constraints and value is not None:
            expected_range = constraints["range"]
            
            # Check if value is in range
            if len(expected_range) == 2:
                min_val, max_val = expected_range
                
                # Handle None in range (means no limit)
                if min_val is not None and value < min_val:
                    raise ParameterError(
                        message=f"Value for parameter {name} is below minimum",
                        param_name=name,
                        expected_range=expected_range,
                        actual_value=value
                    )
                    
                if max_val is not None and value > max_val:
                    raise ParameterError(
                        message=f"Value for parameter {name} is above maximum",
                        param_name=name,
                        expected_range=expected_range,
                        actual_value=value
                    )
            else:
                # Enum-like validation
                if value not in expected_range:
                    raise ParameterError(
                        message=f"Invalid value for parameter {name}",
                        param_name=name,
                        expected_range=expected_range,
                        actual_value=value
                    )
                    
        # Custom validation
        if "validate" in constraints and callable(constraints["validate"]):
            validator = constraints["validate"]
            try:
                valid = validator(value)
                if not valid:
                    raise ParameterError(
                        message=f"Validation failed for parameter {name}",
                        param_name=name,
                        actual_value=value
                    )
            except Exception as e:
                raise ParameterError(
                    message=f"Validation error for parameter {name}: {str(e)}",
                    param_name=name,
                    actual_value=value,
                    original_exception=e
                )