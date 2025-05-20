"""Built-in healing strategies for common errors."""
from __future__ import annotations

import re
import sys
import math
import numpy as np
from typing import Dict, Any, Optional, List, Type, Union, Set, Tuple

from .recovery import HealingStrategy, RecoveryAction, RecoveryActionType

class ParameterBoundsStrategy(HealingStrategy):
    """Strategy for handling parameter out-of-bounds errors."""
    
    @property
    def name(self) -> str:
        """Get the strategy name."""
        return "parameter_bounds"
    
    @property
    def description(self) -> str:
        """Get the strategy description."""
        return "Fixes parameters that are outside their valid bounds"
    
    @property
    def handled_errors(self) -> List[Type[Exception]]:
        """Get the types of errors this strategy can handle."""
        return [ValueError, TypeError, OverflowError]
    
    def can_handle(self, error: Exception, context: Dict[str, Any]) -> bool:
        """
        Determine if this strategy can handle the error.
        
        Args:
            error: Error to handle
            context: Context information
            
        Returns:
            True if the strategy can handle the error
        """
        # Check error type
        if not isinstance(error, tuple(self.handled_errors)):
            return False
        
        # Check error message for bounds-related keywords
        error_msg = str(error).lower()
        bounds_keywords = ["range", "bound", "limit", "max", "min", "valid", "invalid"]
        
        if any(keyword in error_msg for keyword in bounds_keywords):
            return True
        
        # Check traceback for common parameter validation functions
        if "traceback" in context:
            traceback = context["traceback"].lower()
            validation_funcs = ["validate_params", "check_bounds", "validate", "check_range"]
            
            if any(func in traceback for func in validation_funcs):
                return True
        
        return False
    
    def diagnose(self, error: Exception, context: Dict[str, Any]) -> str:
        """
        Diagnose the error.
        
        Args:
            error: Error to diagnose
            context: Context information
            
        Returns:
            Human-readable diagnosis of the error
        """
        error_msg = str(error)
        
        # Try to extract parameter name and bounds
        param_name = None
        min_value = None
        max_value = None
        
        # Pattern matching for common error message formats
        patterns = [
            r"([\w_]+) must be between ([0-9.-]+) and ([0-9.-]+)",
            r"([\w_]+) is outside the valid range \[([0-9.-]+), ([0-9.-]+)\]",
            r"invalid value for ([\w_]+): ([0-9.-]+) < value < ([0-9.-]+) required"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_msg)
            if match:
                param_name = match.group(1)
                min_value = float(match.group(2))
                max_value = float(match.group(3))
                break
        
        if param_name and min_value is not None and max_value is not None:
            return f"Parameter '{param_name}' is outside the valid range [{min_value}, {max_value}]"
        
        return "One or more parameters are outside their valid bounds"
    
    def suggest_actions(self, error: Exception, context: Dict[str, Any]) -> List[RecoveryAction]:
        """
        Suggest recovery actions for the error.
        
        Args:
            error: Error to recover from
            context: Context information
            
        Returns:
            List of suggested recovery actions
        """
        error_msg = str(error)
        params = context.get("params", {})
        actions = []
        
        # Extract parameter name and bounds from error message
        patterns = [
            r"([\w_]+) must be between ([0-9.-]+) and ([0-9.-]+)",
            r"([\w_]+) is outside the valid range \[([0-9.-]+), ([0-9.-]+)\]",
            r"invalid value for ([\w_]+): ([0-9.-]+) < value < ([0-9.-]+) required"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_msg)
            if match:
                param_name = match.group(1)
                min_value = float(match.group(2))
                max_value = float(match.group(3))
                
                # Check if parameter exists in context
                if param_name in params:
                    current_value = params[param_name]
                    
                    # Parameter is too small
                    if current_value < min_value:
                        actions.append(RecoveryAction(
                            action_type=RecoveryActionType.PARAMETER_ADJUST,
                            description=f"Set {param_name} to minimum value {min_value}",
                            changes={param_name: min_value},
                            confidence=0.9
                        ))
                    
                    # Parameter is too large
                    elif current_value > max_value:
                        actions.append(RecoveryAction(
                            action_type=RecoveryActionType.PARAMETER_ADJUST,
                            description=f"Set {param_name} to maximum value {max_value}",
                            changes={param_name: max_value},
                            confidence=0.9
                        ))
                
                break
        
        # If no specific parameter was identified, try some common parameters
        if not actions:
            # Check max_iter
            if "max_iter" in params and isinstance(params["max_iter"], (int, float)):
                max_iter = params["max_iter"]
                
                if max_iter < 10:
                    actions.append(RecoveryAction(
                        action_type=RecoveryActionType.PARAMETER_ADJUST,
                        description="Increase max_iter to 100 (minimum recommended value)",
                        changes={"max_iter": 100},
                        confidence=0.6
                    ))
                elif max_iter > 10000:
                    actions.append(RecoveryAction(
                        action_type=RecoveryActionType.PARAMETER_ADJUST,
                        description="Decrease max_iter to 1000 (maximum recommended value)",
                        changes={"max_iter": 1000},
                        confidence=0.6
                    ))
            
            # Check zoom
            if "zoom" in params and isinstance(params["zoom"], (int, float)):
                zoom = params["zoom"]
                
                if zoom < 0.1:
                    actions.append(RecoveryAction(
                        action_type=RecoveryActionType.PARAMETER_ADJUST,
                        description="Increase zoom to 0.1 (minimum recommended value)",
                        changes={"zoom": 0.1},
                        confidence=0.6
                    ))
                elif zoom > 1e10:
                    actions.append(RecoveryAction(
                        action_type=RecoveryActionType.PARAMETER_ADJUST,
                        description="Decrease zoom to 1e6 (maximum recommended value)",
                        changes={"zoom": 1e6},
                        confidence=0.6
                    ))
        
        return actions

class NumericOverflowStrategy(HealingStrategy):
    """Strategy for handling numeric overflow errors."""
    
    @property
    def name(self) -> str:
        """Get the strategy name."""
        return "numeric_overflow"
    
    @property
    def description(self) -> str:
        """Get the strategy description."""
        return "Fixes numeric overflow errors in computation"
    
    @property
    def handled_errors(self) -> List[Type[Exception]]:
        """Get the types of errors this strategy can handle."""
        return [OverflowError, FloatingPointError, ValueError]
    
    def can_handle(self, error: Exception, context: Dict[str, Any]) -> bool:
        """
        Determine if this strategy can handle the error.
        
        Args:
            error: Error to handle
            context: Context information
            
        Returns:
            True if the strategy can handle the error
        """
        # Check error type
        if not isinstance(error, tuple(self.handled_errors)):
            return False
        
        # Check error message for overflow-related keywords
        error_msg = str(error).lower()
        overflow_keywords = ["overflow", "too large", "infinite", "nan", "inf", "out of range"]
        
        return any(keyword in error_msg for keyword in overflow_keywords)
    
    def diagnose(self, error: Exception, context: Dict[str, Any]) -> str:
        """
        Diagnose the error.
        
        Args:
            error: Error to diagnose
            context: Context information
            
        Returns:
            Human-readable diagnosis of the error
        """
        error_msg = str(error).lower()
        
        if "inf" in error_msg or "infinite" in error_msg:
            return "Calculation resulted in an infinite value"
        elif "nan" in error_msg:
            return "Calculation resulted in an invalid value (NaN)"
        elif "overflow" in error_msg:
            return "Numeric overflow during calculation"
        
        return "Numeric calculation error due to extreme parameter values"
    
    def suggest_actions(self, error: Exception, context: Dict[str, Any]) -> List[RecoveryAction]:
        """
        Suggest recovery actions for the error.
        
        Args:
            error: Error to recover from
            context: Context information
            
        Returns:
            List of suggested recovery actions
        """
        params = context.get("params", {})
        actions = []
        
        # Check zoom parameter
        if "zoom" in params and isinstance(params["zoom"], (int, float)):
            zoom = params["zoom"]
            
            if zoom > 1e6:
                actions.append(RecoveryAction(
                    action_type=RecoveryActionType.PARAMETER_ADJUST,
                    description="Decrease zoom to avoid numeric overflow",
                    changes={"zoom": 1e6},
                    confidence=0.8
                ))
        
        # Check center coordinates
        if "center_x" in params and "center_y" in params:
            center_x = params["center_x"]
            center_y = params["center_y"]
            
            # Check if coordinates are extreme
            if abs(center_x) > 1e10 or abs(center_y) > 1e10:
                actions.append(RecoveryAction(
                    action_type=RecoveryActionType.PARAMETER_ADJUST,
                    description="Reset center coordinates to avoid numeric overflow",
                    changes={"center_x": -0.5, "center_y": 0.0},
                    confidence=0.7
                ))
        
        # Check max_iter
        if "max_iter" in params and isinstance(params["max_iter"], (int, float)):
            max_iter = params["max_iter"]
            
            if max_iter > 1000:
                actions.append(RecoveryAction(
                    action_type=RecoveryActionType.PARAMETER_ADJUST,
                    description="Decrease max_iter to reduce computation intensity",
                    changes={"max_iter": 1000},
                    confidence=0.6
                ))
        
        # Generic action if no specific parameter adjustments were found
        if not actions:
            actions.append(RecoveryAction(
                action_type=RecoveryActionType.PARAMETER_ADJUST,
                description="Reset parameters to safe defaults",
                changes={
                    "zoom": 1.0,
                    "center_x": -0.5,
                    "center_y": 0.0,
                    "max_iter": 100
                },
                confidence=0.5
            ))
        
        return actions

class MemoryOverflowStrategy(HealingStrategy):
    """Strategy for handling memory overflow errors."""
    
    @property
    def name(self) -> str:
        """Get the strategy name."""
        return "memory_overflow"
    
    @property
    def description(self) -> str:
        """Get the strategy description."""
        return "Fixes memory overflow errors by reducing resource usage"
    
    @property
    def handled_errors(self) -> List[Type[Exception]]:
        """Get the types of errors this strategy can handle."""
        return [MemoryError, ValueError]
    
    def can_handle(self, error: Exception, context: Dict[str, Any]) -> bool:
        """
        Determine if this strategy can handle the error.
        
        Args:
            error: Error to handle
            context: Context information
            
        Returns:
            True if the strategy can handle the error
        """
        # Check error type
        if isinstance(error, MemoryError):
            return True
        
        # Check error message for memory-related keywords
        if isinstance(error, ValueError):
            error_msg = str(error).lower()
            memory_keywords = ["memory", "allocation", "buffer", "size", "too large", "out of memory"]
            
            return any(keyword in error_msg for keyword in memory_keywords)
        
        return False
    
    def diagnose(self, error: Exception, context: Dict[str, Any]) -> str:
        """
        Diagnose the error.
        
        Args:
            error: Error to diagnose
            context: Context information
            
        Returns:
            Human-readable diagnosis of the error
        """
        if isinstance(error, MemoryError):
            return "Out of memory error during calculation"
        
        error_msg = str(error).lower()
        
        if "allocation" in error_msg:
            return "Memory allocation failed due to insufficient resources"
        elif "size" in error_msg and ("large" in error_msg or "big" in error_msg):
            return "Requested array size is too large for available memory"
        
        return "Memory-related error due to excessive resource usage"
    
    def suggest_actions(self, error: Exception, context: Dict[str, Any]) -> List[RecoveryAction]:
        """
        Suggest recovery actions for the error.
        
        Args:
            error: Error to recover from
            context: Context information
            
        Returns:
            List of suggested recovery actions
        """
        params = context.get("params", {})
        actions = []
        
        # Check resolution
        if "width" in params and "height" in params:
            width = params["width"]
            height = params["height"]
            
            # Calculate pixel count
            pixel_count = width * height
            
            if pixel_count > 1_000_000:  # More than 1 megapixel
                # Reduce resolution while maintaining aspect ratio
                scale_factor = math.sqrt(1_000_000 / pixel_count)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                
                actions.append(RecoveryAction(
                    action_type=RecoveryActionType.RESOURCE_REDUCTION,
                    description=f"Reduce resolution from {width}×{height} to {new_width}×{new_height}",
                    changes={"width": new_width, "height": new_height},
                    confidence=0.9
                ))
        
        # Check max_iter (can impact memory usage in some algorithms)
        if "max_iter" in params and isinstance(params["max_iter"], (int, float)):
            max_iter = params["max_iter"]
            
            if max_iter > 500:
                actions.append(RecoveryAction(
                    action_type=RecoveryActionType.RESOURCE_REDUCTION,
                    description="Decrease max_iter to reduce memory usage",
                    changes={"max_iter": 500},
                    confidence=0.7
                ))
        
        # Check if high quality mode is enabled
        if "high_quality" in params and params["high_quality"]:
            actions.append(RecoveryAction(
                action_type=RecoveryActionType.RESOURCE_REDUCTION,
                description="Disable high quality mode to reduce memory usage",
                changes={"high_quality": False},
                confidence=0.8
            ))
        
        # Generic action if no specific parameter adjustments were found
        if not actions:
            actions.append(RecoveryAction(
                action_type=RecoveryActionType.RESOURCE_REDUCTION,
                description="Reduce resource usage with conservative settings",
                changes={
                    "width": 800,
                    "height": 600,
                    "max_iter": 100,
                    "high_quality": False
                },
                confidence=0.6
            ))
        
        return actions

class InvalidColorStrategy(HealingStrategy):
    """Strategy for handling invalid color specifications."""
    
    @property
    def name(self) -> str:
        """Get the strategy name."""
        return "invalid_color"
    
    @property
    def description(self) -> str:
        """Get the strategy description."""
        return "Fixes invalid color specifications in parameters"
    
    @property
    def handled_errors(self) -> List[Type[Exception]]:
        """Get the types of errors this strategy can handle."""
        return [ValueError, TypeError]
    
    def can_handle(self, error: Exception, context: Dict[str, Any]) -> bool:
        """
        Determine if this strategy can handle the error.
        
        Args:
            error: Error to handle
            context: Context information
            
        Returns:
            True if the strategy can handle the error
        """
        # Check error type
        if not isinstance(error, tuple(self.handled_errors)):
            return False
        
        # Check error message for color-related keywords
        error_msg = str(error).lower()
        color_keywords = ["color", "rgb", "rgba", "hex", "invalid color", "colormap", "cmap"]
        
        return any(keyword in error_msg for keyword in color_keywords)
    
    def diagnose(self, error: Exception, context: Dict[str, Any]) -> str:
        """
        Diagnose the error.
        
        Args:
            error: Error to diagnose
            context: Context information
            
        Returns:
            Human-readable diagnosis of the error
        """
        error_msg = str(error).lower()
        
        if "hex" in error_msg:
            return "Invalid hex color code"
        elif "rgb" in error_msg:
            return "Invalid RGB color values"
        elif "colormap" in error_msg or "cmap" in error_msg:
            return "Invalid colormap name"
        
        return "Invalid color specification"
    
    def suggest_actions(self, error: Exception, context: Dict[str, Any]) -> List[RecoveryAction]:
        """
        Suggest recovery actions for the error.
        
        Args:
            error: Error to recover from
            context: Context information
            
        Returns:
            List of suggested recovery actions
        """
        params = context.get("params", {})
        actions = []
        
        # Check colormap parameter
        if "colormap" in params or "cmap" in params:
            cmap_param = "colormap" if "colormap" in params else "cmap"
            
            actions.append(RecoveryAction(
                action_type=RecoveryActionType.PARAMETER_ADJUST,
                description=f"Set {cmap_param} to default 'viridis'",
                changes={cmap_param: "viridis"},
                confidence=0.9
            ))
        
        # Check color parameter (typically hex code)
        if "color" in params:
            color = params["color"]
            
            # Check if it's a string but not a valid hex color
            if isinstance(color, str) and not (color.startswith("#") and len(color) in (4, 7, 9)):
                actions.append(RecoveryAction(
                    action_type=RecoveryActionType.PARAMETER_ADJUST,
                    description="Set color to default value '#2c3e50'",
                    changes={"color": "#2c3e50"},
                    confidence=0.9
                ))
        
        # Check alpha parameter
        if "alpha" in params:
            alpha = params["alpha"]
            
            # Check if alpha is outside valid range [0, 1]
            if not isinstance(alpha, (int, float)) or alpha < 0 or alpha > 1:
                actions.append(RecoveryAction(
                    action_type=RecoveryActionType.PARAMETER_ADJUST,
                    description="Set alpha to default value 0.8",
                    changes={"alpha": 0.8},
                    confidence=0.9
                ))
        
        return actions

class IterationLimitStrategy(HealingStrategy):
    """Strategy for handling iteration limit-related errors."""
    
    @property
    def name(self) -> str:
        """Get the strategy name."""
        return "iteration_limit"
    
    @property
    def description(self) -> str:
        """Get the strategy description."""
        return "Adjusts iteration limits to balance performance and quality"
    
    @property
    def handled_errors(self) -> List[Type[Exception]]:
        """Get the types of errors this strategy can handle."""
        return [RuntimeError, ValueError, TimeoutError]
    
    def can_handle(self, error: Exception, context: Dict[str, Any]) -> bool:
        """
        Determine if this strategy can handle the error.
        
        Args:
            error: Error to handle
            context: Context information
            
        Returns:
            True if the strategy can handle the error
        """
        # Check error type
        if not isinstance(error, tuple(self.handled_errors)):
            return False
        
        # Check error message for iteration-related keywords
        error_msg = str(error).lower()
        iteration_keywords = ["iteration", "max_iter", "maximum iterations", "timeout", "took too long"]
        
        return any(keyword in error_msg for keyword in iteration_keywords)
    
    def diagnose(self, error: Exception, context: Dict[str, Any]) -> str:
        """
        Diagnose the error.
        
        Args:
            error: Error to diagnose
            context: Context information
            
        Returns:
            Human-readable diagnosis of the error
        """
        error_msg = str(error).lower()
        
        if "timeout" in error_msg or "took too long" in error_msg:
            return "Computation timed out due to excessive iterations"
        elif "maximum iterations" in error_msg or "max_iter" in error_msg:
            return "Maximum iteration limit reached"
        
        return "Iteration-related error in fractal computation"
    
    def suggest_actions(self, error: Exception, context: Dict[str, Any]) -> List[RecoveryAction]:
        """
        Suggest recovery actions for the error.
        
        Args:
            error: Error to recover from
            context: Context information
            
        Returns:
            List of suggested recovery actions
        """
        params = context.get("params", {})
        actions = []
        
        # Check max_iter parameter
        if "max_iter" in params and isinstance(params["max_iter"], (int, float)):
            max_iter = params["max_iter"]
            
            if max_iter > 1000:
                actions.append(RecoveryAction(
                    action_type=RecoveryActionType.PARAMETER_ADJUST,
                    description="Reduce maximum iterations to 1000",
                    changes={"max_iter": 1000},
                    confidence=0.9
                ))
            elif max_iter < 100:
                actions.append(RecoveryAction(
                    action_type=RecoveryActionType.PARAMETER_ADJUST,
                    description="Increase maximum iterations to 100",
                    changes={"max_iter": 100},
                    confidence=0.8
                ))
        else:
            actions.append(RecoveryAction(
                action_type=RecoveryActionType.PARAMETER_ADJUST,
                description="Set maximum iterations to a reasonable default (100)",
                changes={"max_iter": 100},
                confidence=0.7
            ))
        
        # Check if high quality mode is enabled (may affect iterations)
        if "high_quality" in params and params["high_quality"]:
            actions.append(RecoveryAction(
                action_type=RecoveryActionType.PARAMETER_ADJUST,
                description="Disable high quality mode to reduce computation time",
                changes={"high_quality": False},
                confidence=0.6
            ))
        
        return actions

class ZoomDepthStrategy(HealingStrategy):
    """Strategy for handling zoom depth-related errors."""
    
    @property
    def name(self) -> str:
        """Get the strategy name."""
        return "zoom_depth"
    
    @property
    def description(self) -> str:
        """Get the strategy description."""
        return "Adjusts zoom and center parameters to avoid precision issues"
    
    @property
    def handled_errors(self) -> List[Type[Exception]]:
        """Get the types of errors this strategy can handle."""
        return [ValueError, RuntimeError, ArithmeticError]
    
    def can_handle(self, error: Exception, context: Dict[str, Any]) -> bool:
        """
        Determine if this strategy can handle the error.
        
        Args:
            error: Error to handle
            context: Context information
            
        Returns:
            True if the strategy can handle the error
        """
        # Check error type
        if not isinstance(error, tuple(self.handled_errors)):
            return False
        
        # Check error message for zoom-related keywords
        error_msg = str(error).lower()
        zoom_keywords = ["zoom", "precision", "depth", "floating point", "underflow", "overflow"]
        
        if any(keyword in error_msg for keyword in zoom_keywords):
            return True
        
        # Check context for extreme zoom values
        params = context.get("params", {})
        if "zoom" in params and isinstance(params["zoom"], (int, float)):
            zoom = params["zoom"]
            
            # Extreme zoom values can cause precision issues
            if zoom > 1e10 or zoom < 1e-10:
                return True
        
        return False
    
    def diagnose(self, error: Exception, context: Dict[str, Any]) -> str:
        """
        Diagnose the error.
        
        Args:
            error: Error to diagnose
            context: Context information
            
        Returns:
            Human-readable diagnosis of the error
        """
        params = context.get("params", {})
        
        if "zoom" in params and isinstance(params["zoom"], (int, float)):
            zoom = params["zoom"]
            
            if zoom > 1e10:
                return "Zoom level too high for floating-point precision"
            elif zoom < 1e-10:
                return "Zoom level too low for meaningful calculation"
        
        return "Precision error due to extreme zoom or center values"
    
    def suggest_actions(self, error: Exception, context: Dict[str, Any]) -> List[RecoveryAction]:
        """
        Suggest recovery actions for the error.
        
        Args:
            error: Error to recover from
            context: Context information
            
        Returns:
            List of suggested recovery actions
        """
        params = context.get("params", {})
        actions = []
        
        # Check zoom parameter
        if "zoom" in params and isinstance(params["zoom"], (int, float)):
            zoom = params["zoom"]
            
            if zoom > 1e10:
                actions.append(RecoveryAction(
                    action_type=RecoveryActionType.PARAMETER_ADJUST,
                    description="Reduce zoom to a safe level (1e6)",
                    changes={"zoom": 1e6},
                    confidence=0.9
                ))
            elif zoom < 1e-10:
                actions.append(RecoveryAction(
                    action_type=RecoveryActionType.PARAMETER_ADJUST,
                    description="Increase zoom to a safe level (0.1)",
                    changes={"zoom": 0.1},
                    confidence=0.9
                ))
        
        # Check center coordinates for extreme values
        if "center_x" in params and "center_y" in params:
            center_x = params["center_x"]
            center_y = params["center_y"]
            
            if abs(center_x) > 1e10 or abs(center_y) > 1e10:
                actions.append(RecoveryAction(
                    action_type=RecoveryActionType.PARAMETER_ADJUST,
                    description="Reset center to a safe position",
                    changes={"center_x": -0.5, "center_y": 0.0},
                    confidence=0.8
                ))
        
        # Check if max_iter is adequate for the zoom level
        if "zoom" in params and "max_iter" in params:
            zoom = params["zoom"]
            max_iter = params["max_iter"]
            
            # For deep zooms, we need more iterations
            if zoom > 1e6 and max_iter < 500:
                actions.append(RecoveryAction(
                    action_type=RecoveryActionType.PARAMETER_ADJUST,
                    description="Increase max_iter to match deep zoom level",
                    changes={"max_iter": 500},
                    confidence=0.7
                ))
        
        # Generic action for zoom-related issues
        if not actions:
            actions.append(RecoveryAction(
                action_type=RecoveryActionType.PARAMETER_ADJUST,
                description="Reset to safe zoom and center values",
                changes={
                    "zoom": 1.0,
                    "center_x": -0.5,
                    "center_y": 0.0,
                    "max_iter": 100
                },
                confidence=0.6
            ))
        
        return actions