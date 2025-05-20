"""
Error code registry for RFM Architecture UI.

This module provides a comprehensive registry of error codes, descriptions,
remediation strategies, and severity classifications for all anticipated errors.
"""

from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

from .types import ErrorCode, ErrorSeverity


@dataclass
class ErrorDefinition:
    """Detailed definition of an error type."""
    
    code: ErrorCode
    name: str
    description: str
    severity: ErrorSeverity
    remediation_steps: List[str]
    likely_causes: List[str]
    example_message: str
    category: str
    impact: str


class ErrorRegistry:
    """
    Central registry of all error types in the application.
    
    This registry provides detailed information about each error code,
    including descriptions, remediation steps, and categorization.
    """
    
    def __init__(self):
        """Initialize the error registry with all known error definitions."""
        self._registry: Dict[ErrorCode, ErrorDefinition] = {}
        self._initialize_registry()
        
    def _initialize_registry(self):
        """Populate the registry with all error definitions."""
        # General errors
        self._add_error(
            ErrorDefinition(
                code=ErrorCode.UNKNOWN_ERROR,
                name="Unknown Error",
                description="An unexpected error occurred that doesn't match any known error type.",
                severity=ErrorSeverity.ERROR,
                remediation_steps=[
                    "Check the application logs for more details",
                    "Restart the application",
                    "If the issue persists, report it with the error details from the log"
                ],
                likely_causes=[
                    "Bug in the application code",
                    "Unexpected input or state",
                    "System resource constraints"
                ],
                example_message="An unexpected error occurred: {error_message}",
                category="General",
                impact="May prevent the application from functioning correctly"
            )
        )
        
        self._add_error(
            ErrorDefinition(
                code=ErrorCode.INVALID_PARAMETER,
                name="Invalid Parameter",
                description="A parameter provided to a function or operation has an invalid value.",
                severity=ErrorSeverity.ERROR,
                remediation_steps=[
                    "Check the parameter value and ensure it matches the expected type and range",
                    "Refer to the parameter documentation for valid values",
                    "Try restoring default parameters"
                ],
                likely_causes=[
                    "User entered an invalid value",
                    "Parameter validation constraints too strict",
                    "Parameter type mismatch"
                ],
                example_message="Invalid value for parameter '{param_name}': {actual_value}",
                category="Input Validation",
                impact="Operation cannot proceed with invalid parameters"
            )
        )
        
        self._add_error(
            ErrorDefinition(
                code=ErrorCode.OPERATION_TIMEOUT,
                name="Operation Timeout",
                description="An operation took too long to complete and was timed out.",
                severity=ErrorSeverity.WARNING,
                remediation_steps=[
                    "Reduce the complexity of the operation (e.g., lower max iterations)",
                    "Try again with a smaller rendering area",
                    "Close other applications to free system resources"
                ],
                likely_causes=[
                    "Operation parameters cause excessive computation",
                    "System under heavy load",
                    "Inefficient algorithm implementation"
                ],
                example_message="Operation '{operation}' timed out after {timeout_ms}ms",
                category="Performance",
                impact="Operation was terminated before completion"
            )
        )
        
        # Rendering errors
        self._add_error(
            ErrorDefinition(
                code=ErrorCode.RENDER_FAILED,
                name="Render Failed",
                description="Failed to render the fractal with the given parameters.",
                severity=ErrorSeverity.ERROR,
                remediation_steps=[
                    "Check rendering parameters for extreme values",
                    "Try a different fractal type or configuration",
                    "Restart the application with default settings"
                ],
                likely_causes=[
                    "Parameters causing numerical instability",
                    "Resource constraints (memory, GPU)",
                    "Bug in the rendering algorithm"
                ],
                example_message="Failed to render fractal of type '{fractal_type}': {error_message}",
                category="Rendering",
                impact="Cannot generate the requested visualization"
            )
        )
        
        self._add_error(
            ErrorDefinition(
                code=ErrorCode.INVALID_FRACTAL_TYPE,
                name="Invalid Fractal Type",
                description="The specified fractal type does not exist or is not supported.",
                severity=ErrorSeverity.ERROR,
                remediation_steps=[
                    "Select a valid fractal type from the available options",
                    "Check the fractal registry for available types",
                    "Verify that custom fractal plugins are correctly installed"
                ],
                likely_causes=[
                    "Typo in fractal type name",
                    "Missing or incorrectly installed fractal plugin",
                    "Attempting to use a fractal type that requires unavailable resources"
                ],
                example_message="Invalid or unsupported fractal type: '{fractal_type}'",
                category="Configuration",
                impact="Cannot initialize the requested fractal type"
            )
        )
        
        self._add_error(
            ErrorDefinition(
                code=ErrorCode.COMPUTATION_DIVERGED,
                name="Computation Diverged",
                description="The fractal computation diverged or resulted in invalid values.",
                severity=ErrorSeverity.WARNING,
                remediation_steps=[
                    "Adjust the parameters to more stable values",
                    "Decrease the maximum iteration count",
                    "Try a different area of the fractal space"
                ],
                likely_causes=[
                    "Parameters leading to numerical instability",
                    "Trying to render an area with chaotic behavior",
                    "Floating-point precision limitations"
                ],
                example_message="Computation diverged at coordinates ({x}, {y}) with parameters: {params}",
                category="Mathematical",
                impact="Resulting image may contain artifacts or be incomplete"
            )
        )
        
        self._add_error(
            ErrorDefinition(
                code=ErrorCode.MEMORY_EXCEEDED,
                name="Memory Exceeded",
                description="The operation exceeded available memory limits.",
                severity=ErrorSeverity.ERROR,
                remediation_steps=[
                    "Reduce the rendering resolution",
                    "Lower algorithmic complexity settings",
                    "Close other applications to free system memory",
                    "Try enabling disk-based computation if available"
                ],
                likely_causes=[
                    "Rendering at too high resolution",
                    "Algorithm settings causing excessive memory usage",
                    "System low on available memory"
                ],
                example_message="Memory limit exceeded: Required {required_mb}MB, available {available_mb}MB",
                category="Resource",
                impact="Unable to complete the operation due to memory constraints"
            )
        )
        
        self._add_error(
            ErrorDefinition(
                code=ErrorCode.MAX_ITERATIONS_EXCEEDED,
                name="Maximum Iterations Exceeded",
                description="The computation reached the maximum allowed iteration count.",
                severity=ErrorSeverity.WARNING,
                remediation_steps=[
                    "Increase the maximum iterations setting",
                    "Adjust fractal parameters for faster convergence",
                    "Change the region of interest to one with better convergence"
                ],
                likely_causes=[
                    "Maximum iterations set too low for the complexity of the region",
                    "Rendering a highly detailed area of the fractal",
                    "Parameters causing slow convergence"
                ],
                example_message="Maximum iterations ({max_iter}) exceeded at {percentage}% of pixels",
                category="Performance",
                impact="Results may lack detail in areas requiring more iterations"
            )
        )
        
        # IO errors
        self._add_error(
            ErrorDefinition(
                code=ErrorCode.FILE_NOT_FOUND,
                name="File Not Found",
                description="The specified file could not be found.",
                severity=ErrorSeverity.ERROR,
                remediation_steps=[
                    "Check that the file exists at the specified path",
                    "Verify file permissions",
                    "Try selecting a different file or restoring from backup"
                ],
                likely_causes=[
                    "File was moved, deleted, or never existed",
                    "Incorrect file path",
                    "File access permissions issue"
                ],
                example_message="File not found: '{file_path}'",
                category="File I/O",
                impact="Cannot access the required file"
            )
        )
        
        self._add_error(
            ErrorDefinition(
                code=ErrorCode.FILE_PERMISSION_DENIED,
                name="File Permission Denied",
                description="Permission denied when attempting to access a file.",
                severity=ErrorSeverity.ERROR,
                remediation_steps=[
                    "Check that the application has appropriate permissions for the file",
                    "Run the application with elevated privileges if necessary",
                    "Verify file ownership and access rights"
                ],
                likely_causes=[
                    "File is locked by another process",
                    "Insufficient user permissions",
                    "File is read-only"
                ],
                example_message="Permission denied for file: '{file_path}'",
                category="File I/O",
                impact="Cannot read from or write to the required file"
            )
        )
        
        self._add_error(
            ErrorDefinition(
                code=ErrorCode.INVALID_FILE_FORMAT,
                name="Invalid File Format",
                description="The file is not in the expected format or is corrupted.",
                severity=ErrorSeverity.ERROR,
                remediation_steps=[
                    "Check that the file is in the correct format",
                    "Try opening and resaving the file in the correct format",
                    "Verify that the file has not been corrupted",
                    "Try loading a different file"
                ],
                likely_causes=[
                    "File was created with a different version of the application",
                    "File was manually modified and corrupted",
                    "File was not completely written before being read"
                ],
                example_message="Invalid file format for '{file_path}': {details}",
                category="File I/O",
                impact="Cannot parse or use the file contents"
            )
        )
        
        # UI errors
        self._add_error(
            ErrorDefinition(
                code=ErrorCode.UI_INITIALIZATION_FAILED,
                name="UI Initialization Failed",
                description="Failed to initialize the user interface.",
                severity=ErrorSeverity.CRITICAL,
                remediation_steps=[
                    "Restart the application",
                    "Check system compatibility with the UI framework",
                    "Verify graphics drivers are up to date",
                    "Try running the application with default settings"
                ],
                likely_causes=[
                    "Graphics driver issues",
                    "Missing UI dependencies",
                    "Incompatible system configuration"
                ],
                example_message="Failed to initialize UI: {error_message}",
                category="UI",
                impact="Application cannot start or display UI elements"
            )
        )
        
        self._add_error(
            ErrorDefinition(
                code=ErrorCode.WIDGET_CREATION_FAILED,
                name="Widget Creation Failed",
                description="Failed to create a UI widget.",
                severity=ErrorSeverity.ERROR,
                remediation_steps=[
                    "Check widget parameters",
                    "Try reducing the number of widgets",
                    "Restart the application"
                ],
                likely_causes=[
                    "Invalid widget parameters",
                    "Resource constraints",
                    "UI framework limitation"
                ],
                example_message="Failed to create widget '{widget_name}': {error_message}",
                category="UI",
                impact="Specific UI component will be missing or non-functional"
            )
        )
        
        self._add_error(
            ErrorDefinition(
                code=ErrorCode.RENDERING_CONTEXT_ERROR,
                name="Rendering Context Error",
                description="Error with the GPU or rendering context.",
                severity=ErrorSeverity.ERROR,
                remediation_steps=[
                    "Update graphics drivers",
                    "Reduce rendering quality settings",
                    "Try switching to CPU rendering mode",
                    "Close other GPU-intensive applications"
                ],
                likely_causes=[
                    "Outdated or incompatible graphics drivers",
                    "GPU resource exhaustion",
                    "Hardware limitations"
                ],
                example_message="Rendering context error: {error_message}",
                category="Graphics",
                impact="Cannot initialize or use the rendering system"
            )
        )
        
        # Add domain-specific errors for common fractal types
        
        # Mandelbrot errors
        self._add_error(
            ErrorDefinition(
                code=ErrorCode.MANDELBROT_PRECISION_ERROR,
                name="Mandelbrot Precision Error",
                description="The Mandelbrot computation requires higher numerical precision than available.",
                severity=ErrorSeverity.WARNING,
                remediation_steps=[
                    "Reduce zoom level",
                    "Enable high-precision mode if available",
                    "Explore a different region of the fractal"
                ],
                likely_causes=[
                    "Zoomed in too far for standard floating-point precision",
                    "Using coordinates with very small differences",
                    "Perturbation theory limitations"
                ],
                example_message="Mandelbrot computation requires higher precision at zoom level {zoom_level}",
                category="Mathematical",
                impact="Image may show banding artifacts or inaccurate details"
            )
        )
        
        # Julia errors
        self._add_error(
            ErrorDefinition(
                code=ErrorCode.JULIA_PARAMETER_INSTABILITY,
                name="Julia Parameter Instability",
                description="The selected Julia set parameters produce unstable or degenerate results.",
                severity=ErrorSeverity.WARNING,
                remediation_steps=[
                    "Adjust the Julia parameter (c value)",
                    "Stay within the main cardioid region for more stable results",
                    "Try preset parameters known to produce interesting results"
                ],
                likely_causes=[
                    "Parameters outside the range that produces interesting Julia sets",
                    "Using extreme parameter values",
                    "Parameters too close to a critical point"
                ],
                example_message="Julia parameters unstable: c = ({real}, {imag})",
                category="Mathematical",
                impact="Resulting image may be empty, solid, or have poor detail"
            )
        )
        
        # L-System errors
        self._add_error(
            ErrorDefinition(
                code=ErrorCode.LSYSTEM_RECURSION_LIMIT,
                name="L-System Recursion Limit",
                description="The L-System reached the maximum recursion depth.",
                severity=ErrorSeverity.WARNING,
                remediation_steps=[
                    "Reduce the number of iterations",
                    "Simplify the L-System rules",
                    "Increase recursion limit in settings if system resources allow"
                ],
                likely_causes=[
                    "Too many iterations for the complexity of the L-System",
                    "Production rules causing exponential growth",
                    "System recursion limitations"
                ],
                example_message="L-System reached recursion limit at depth {depth}",
                category="Algorithmic",
                impact="L-System will not be fully expanded to requested depth"
            )
        )
        
        # Cantor set errors
        self._add_error(
            ErrorDefinition(
                code=ErrorCode.CANTOR_RESOLUTION_LIMIT,
                name="Cantor Resolution Limit",
                description="The Cantor set computation reached the minimum displayable resolution.",
                severity=ErrorSeverity.INFO,
                remediation_steps=[
                    "Reduce the number of iterations",
                    "Increase the display size or resolution",
                    "Zoom in to a specific region"
                ],
                likely_causes=[
                    "Too many iterations for the available display resolution",
                    "Attempting to render features smaller than a pixel"
                ],
                example_message="Cantor set features smaller than pixel resolution at iteration {iteration}",
                category="Display",
                impact="Some details of the Cantor set will not be visible"
            )
        )
        
        # Performance errors
        self._add_error(
            ErrorDefinition(
                code=ErrorCode.PERFORMANCE_REGRESSION,
                name="Performance Regression",
                description="A significant performance regression was detected compared to baseline.",
                severity=ErrorSeverity.WARNING,
                remediation_steps=[
                    "Check for system resource contention",
                    "Close other applications",
                    "Consider reverting to a previous version if using new code",
                    "Revert recent parameter changes"
                ],
                likely_causes=[
                    "Code changes reducing performance",
                    "Increased algorithmic complexity",
                    "System under heavier load than during baseline"
                ],
                example_message="Performance regression detected: {operation} is {percentage}% slower than baseline",
                category="Performance",
                impact="Operations will take longer than expected"
            )
        )
        
        self._add_error(
            ErrorDefinition(
                code=ErrorCode.RESOURCE_EXHAUSTION,
                name="Resource Exhaustion",
                description="System resources (CPU, memory, GPU) are critically low.",
                severity=ErrorSeverity.CRITICAL,
                remediation_steps=[
                    "Save your work immediately",
                    "Close other applications",
                    "Reduce rendering quality settings",
                    "Restart the application or system"
                ],
                likely_causes=[
                    "Multiple high-resource operations running simultaneously",
                    "Memory leak",
                    "System overheating causing throttling"
                ],
                example_message="Resource exhaustion: {resource_type} at {percentage}% capacity",
                category="Resource",
                impact="Application may become unresponsive or crash"
            )
        )
        
    def _add_error(self, definition: ErrorDefinition):
        """Add an error definition to the registry."""
        self._registry[definition.code] = definition
    
    def get_definition(self, code: ErrorCode) -> Optional[ErrorDefinition]:
        """
        Get the definition for an error code.
        
        Args:
            code: The error code to look up
            
        Returns:
            ErrorDefinition if found, None otherwise
        """
        return self._registry.get(code)
    
    def get_all_definitions(self) -> Dict[ErrorCode, ErrorDefinition]:
        """
        Get all error definitions.
        
        Returns:
            Dictionary mapping error codes to their definitions
        """
        return self._registry.copy()
    
    def get_category_errors(self, category: str) -> List[ErrorDefinition]:
        """
        Get all errors in a specific category.
        
        Args:
            category: Category to filter by
            
        Returns:
            List of error definitions in the specified category
        """
        return [d for d in self._registry.values() if d.category == category]
    
    def get_severity_errors(self, severity: ErrorSeverity) -> List[ErrorDefinition]:
        """
        Get all errors with a specific severity.
        
        Args:
            severity: Severity to filter by
            
        Returns:
            List of error definitions with the specified severity
        """
        return [d for d in self._registry.values() if d.severity == severity]
    
    def get_remediation_steps(self, code: ErrorCode) -> List[str]:
        """
        Get remediation steps for an error code.
        
        Args:
            code: The error code
            
        Returns:
            List of remediation steps, or empty list if code not found
        """
        definition = self.get_definition(code)
        return definition.remediation_steps if definition else []
    
    def generate_markdown_documentation(self) -> str:
        """
        Generate Markdown documentation of all error codes.
        
        Returns:
            Markdown formatted documentation string
        """
        markdown = "# Error Code Reference\n\n"
        
        # Group errors by category
        categories = {}
        for definition in self._registry.values():
            if definition.category not in categories:
                categories[definition.category] = []
            categories[definition.category].append(definition)
        
        # Generate markdown for each category
        for category, definitions in sorted(categories.items()):
            markdown += f"## {category} Errors\n\n"
            
            for definition in sorted(definitions, key=lambda d: d.name):
                markdown += f"### {definition.code.value}: {definition.name}\n\n"
                markdown += f"**Severity:** {definition.severity.value}\n\n"
                markdown += f"**Description:** {definition.description}\n\n"
                
                markdown += "**Likely Causes:**\n"
                for cause in definition.likely_causes:
                    markdown += f"- {cause}\n"
                markdown += "\n"
                
                markdown += "**Remediation Steps:**\n"
                for step in definition.remediation_steps:
                    markdown += f"- {step}\n"
                markdown += "\n"
                
                markdown += f"**Impact:** {definition.impact}\n\n"
                markdown += f"**Example Message:** `{definition.example_message}`\n\n"
            
        return markdown


# Extend the ErrorCode enum with additional codes
# Using monkey patching to add new error codes without modifying the original enum
ErrorCode.MANDELBROT_PRECISION_ERROR = ErrorCode("MANDELBROT_PRECISION_ERROR")
ErrorCode.JULIA_PARAMETER_INSTABILITY = ErrorCode("JULIA_PARAMETER_INSTABILITY")
ErrorCode.LSYSTEM_RECURSION_LIMIT = ErrorCode("LSYSTEM_RECURSION_LIMIT")
ErrorCode.CANTOR_RESOLUTION_LIMIT = ErrorCode("CANTOR_RESOLUTION_LIMIT")
ErrorCode.PERFORMANCE_REGRESSION = ErrorCode("PERFORMANCE_REGRESSION")
ErrorCode.RESOURCE_EXHAUSTION = ErrorCode("RESOURCE_EXHAUSTION")


# Singleton instance
_registry_instance = None


def get_error_registry() -> ErrorRegistry:
    """
    Get the singleton instance of the error registry.
    
    Returns:
        ErrorRegistry instance
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ErrorRegistry()
    return _registry_instance