# RFM Architecture Error Code Reference

The RFM Architecture implements a comprehensive error handling system that provides detailed error information, remediation steps, and error tracking. This document provides a reference for all error codes used throughout the application.

## Error Code System Design

The error handling system is designed with the following goals:

- **Comprehensive Coverage**: Captures all anticipated error conditions with unique codes
- **Detailed Context**: Provides rich context for troubleshooting (parameters, state, etc.)
- **User-Friendly Messages**: Presents clear error messages with remediation steps
- **Centralized Handling**: Routes all errors through a central handler for consistent processing
- **Performance Analysis**: Tracks error frequency and patterns for identifying systemic issues
- **Graceful Degradation**: Prevents application crashes by containing errors within boundaries

## Error Severity Levels

Errors are categorized into severity levels to help prioritize responses:

| Severity | Description |
|----------|-------------|
| INFO | Informational message that doesn't indicate a problem |
| WARNING | Potential issue that doesn't prevent operation but may affect quality |
| ERROR | Significant issue that prevents a specific operation from completing |
| CRITICAL | Severe issue that threatens application stability or data integrity |

## Error Categories

Errors are grouped into the following categories:

| Category | Description |
|----------|-------------|
| General | Generic errors that don't fit specific categories |
| Input Validation | Errors related to parameter validation |
| Performance | Errors related to timing, resources, and computation limits |
| Rendering | Errors specific to the rendering process |
| Configuration | Errors in application or fractal configuration |
| Mathematical | Errors related to mathematical operations and algorithms |
| Resource | Errors related to system resource constraints |
| File I/O | Errors related to file operations |
| UI | Errors in user interface components |
| Graphics | Errors related to graphics hardware or APIs |
| Algorithmic | Errors related to specific algorithms |
| Display | Errors related to display limitations |

## Core Error Codes

### General Errors

| Code | Name | Description | Severity |
|------|------|-------------|----------|
| UNKNOWN_ERROR | Unknown Error | An unexpected error occurred that doesn't match any known error type | ERROR |
| INVALID_PARAMETER | Invalid Parameter | A parameter provided to a function or operation has an invalid value | ERROR |
| OPERATION_TIMEOUT | Operation Timeout | An operation took too long to complete and was timed out | WARNING |

### Rendering Errors

| Code | Name | Description | Severity |
|------|------|-------------|----------|
| RENDER_FAILED | Render Failed | Failed to render the fractal with the given parameters | ERROR |
| INVALID_FRACTAL_TYPE | Invalid Fractal Type | The specified fractal type does not exist or is not supported | ERROR |
| COMPUTATION_DIVERGED | Computation Diverged | The fractal computation diverged or resulted in invalid values | WARNING |
| MEMORY_EXCEEDED | Memory Exceeded | The operation exceeded available memory limits | ERROR |
| MAX_ITERATIONS_EXCEEDED | Maximum Iterations Exceeded | The computation reached the maximum allowed iteration count | WARNING |

### File I/O Errors

| Code | Name | Description | Severity |
|------|------|-------------|----------|
| FILE_NOT_FOUND | File Not Found | The specified file could not be found | ERROR |
| FILE_PERMISSION_DENIED | File Permission Denied | Permission denied when attempting to access a file | ERROR |
| INVALID_FILE_FORMAT | Invalid File Format | The file is not in the expected format or is corrupted | ERROR |

### UI Errors

| Code | Name | Description | Severity |
|------|------|-------------|----------|
| UI_INITIALIZATION_FAILED | UI Initialization Failed | Failed to initialize the user interface | CRITICAL |
| WIDGET_CREATION_FAILED | Widget Creation Failed | Failed to create a UI widget | ERROR |
| RENDERING_CONTEXT_ERROR | Rendering Context Error | Error with the GPU or rendering context | ERROR |

## Fractal-Specific Error Codes

### Mandelbrot Set Errors

| Code | Name | Description | Severity |
|------|------|-------------|----------|
| MANDELBROT_PRECISION_ERROR | Mandelbrot Precision Error | The Mandelbrot computation requires higher numerical precision than available | WARNING |

### Julia Set Errors

| Code | Name | Description | Severity |
|------|------|-------------|----------|
| JULIA_PARAMETER_INSTABILITY | Julia Parameter Instability | The selected Julia set parameters produce unstable or degenerate results | WARNING |

### L-System Errors

| Code | Name | Description | Severity |
|------|------|-------------|----------|
| LSYSTEM_RECURSION_LIMIT | L-System Recursion Limit | The L-System reached the maximum recursion depth | WARNING |

### Cantor Set Errors

| Code | Name | Description | Severity |
|------|------|-------------|----------|
| CANTOR_RESOLUTION_LIMIT | Cantor Resolution Limit | The Cantor set computation reached the minimum displayable resolution | INFO |

## Performance Errors

| Code | Name | Description | Severity |
|------|------|-------------|----------|
| PERFORMANCE_REGRESSION | Performance Regression | A significant performance regression was detected compared to baseline | WARNING |
| RESOURCE_EXHAUSTION | Resource Exhaustion | System resources (CPU, memory, GPU) are critically low | CRITICAL |

## Using the Error System

### Error Boundaries

The error system provides decorators and context managers to create error boundaries around code:

```python
from rfm_ui.errors.decorators import error_boundary, error_context

# Function decorator approach
@error_boundary
def render_fractal(params):
    # Function code that might raise exceptions
    pass

# Context manager approach
with error_context("render_operation", {"params": params}):
    # Code that might raise exceptions
    pass
```

### Parameter Validation

Use the validation utility to check parameters against a schema:

```python
from rfm_ui.errors.decorators import validate_params

# Define a validation schema
schema = {
    "width": {
        "type": int,
        "required": True,
        "range": [1, 10000]
    },
    "max_iterations": {
        "type": int,
        "required": True,
        "range": [10, 5000]
    }
}

# Validate parameters
validate_params(params, schema)
```

### Error Handler

The central error handler can be accessed through the singleton instance:

```python
from rfm_ui.errors import get_error_handler

# Get error statistics
stats = get_error_handler().get_error_stats()

# Get recent errors
recent_errors = get_error_handler().get_recent_errors(limit=5)

# Export error log
get_error_handler().export_error_log("error_export.json")
```

## Extending the Error System

To add new error types, extend the appropriate error class:

```python
from rfm_ui.errors.types import RenderError, ErrorCode

class CustomRenderError(RenderError):
    """Custom rendering error for specific use cases."""
    
    def __init__(self, message, custom_param, **kwargs):
        details = {"custom_param": custom_param}
        super().__init__(
            message=message,
            error_code=ErrorCode.RENDER_FAILED,
            details=details,
            **kwargs
        )
```

To add new error codes, register them in the error registry:

```python
from rfm_ui.errors.types import ErrorCode
from rfm_ui.errors.registry import get_error_registry, ErrorDefinition, ErrorSeverity

# Define a new error code
ErrorCode.CUSTOM_ERROR = ErrorCode("CUSTOM_ERROR")

# Register the error definition
get_error_registry()._add_error(
    ErrorDefinition(
        code=ErrorCode.CUSTOM_ERROR,
        name="Custom Error",
        description="Description of the custom error",
        severity=ErrorSeverity.ERROR,
        remediation_steps=["Step 1", "Step 2"],
        likely_causes=["Cause 1", "Cause 2"],
        example_message="Custom error occurred: {details}",
        category="Custom",
        impact="Impact description"
    )
)
```