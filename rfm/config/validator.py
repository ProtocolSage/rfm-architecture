"""Configuration validation for RFM Architecture."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union, Tuple, Set

from .settings import Config

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """A single validation error."""
    path: str
    message: str
    expected: Optional[Any] = None
    received: Optional[Any] = None

    def __str__(self) -> str:
        """Return a string representation of the error."""
        result = f"{self.path}: {self.message}"
        if self.expected is not None and self.received is not None:
            result += f" (expected: {self.expected}, received: {self.received})"
        return result


@dataclass
class ValidationResult:
    """The result of a configuration validation."""
    is_valid: bool
    errors: List[ValidationError] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.errors is None:
            self.errors = []
    
    def __bool__(self) -> bool:
        """Return whether the validation was successful."""
        return self.is_valid
    
    def add_error(self, path: str, message: str, 
                 expected: Optional[Any] = None, received: Optional[Any] = None) -> None:
        """Add a validation error."""
        self.errors.append(ValidationError(path, message, expected, received))
        self.is_valid = False
    
    def combine(self, other: ValidationResult) -> ValidationResult:
        """Combine with another validation result."""
        combined = ValidationResult(
            is_valid=self.is_valid and other.is_valid,
            errors=self.errors + other.errors
        )
        return combined
    
    def summary(self) -> str:
        """Return a summary of the validation result."""
        if self.is_valid:
            return "Configuration is valid."
        
        return f"Configuration has {len(self.errors)} errors:\n" + "\n".join(
            f"- {error}" for error in self.errors
        )


class ConfigValidator:
    """Validator for RFM Architecture configuration."""
    
    @staticmethod
    def _validate_type(path: str, value: Any, expected_type: Any) -> ValidationResult:
        """Validate that a value has the expected type.
        
        Args:
            path: The path to the value in the configuration
            value: The value to validate
            expected_type: The expected type or types
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True)
        
        if not isinstance(value, expected_type):
            result.add_error(
                path=path,
                message=f"Invalid type",
                expected=expected_type.__name__ if hasattr(expected_type, "__name__") else str(expected_type),
                received=type(value).__name__
            )
        
        return result
    
    @staticmethod
    def _validate_required_keys(path: str, data: Dict[str, Any], 
                              required_keys: Set[str]) -> ValidationResult:
        """Validate that a dictionary contains all required keys.
        
        Args:
            path: The path to the dictionary in the configuration
            data: The dictionary to validate
            required_keys: Set of required keys
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True)
        
        missing_keys = required_keys - set(data.keys())
        if missing_keys:
            result.add_error(
                path=path,
                message=f"Missing required keys: {', '.join(missing_keys)}",
                expected=list(required_keys),
                received=list(data.keys())
            )
        
        return result
    
    @staticmethod
    def _validate_enum(path: str, value: Any, allowed_values: Set[Any]) -> ValidationResult:
        """Validate that a value is one of the allowed values.
        
        Args:
            path: The path to the value in the configuration
            value: The value to validate
            allowed_values: Set of allowed values
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True)
        
        if value not in allowed_values:
            result.add_error(
                path=path,
                message=f"Invalid value",
                expected=list(allowed_values),
                received=value
            )
        
        return result
    
    @staticmethod
    def _validate_range(path: str, value: Union[int, float], 
                       min_value: Optional[Union[int, float]] = None,
                       max_value: Optional[Union[int, float]] = None) -> ValidationResult:
        """Validate that a numeric value is within the specified range.
        
        Args:
            path: The path to the value in the configuration
            value: The value to validate
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True)
        
        if min_value is not None and value < min_value:
            result.add_error(
                path=path,
                message=f"Value is less than minimum allowed",
                expected=f">= {min_value}",
                received=value
            )
        
        if max_value is not None and value > max_value:
            result.add_error(
                path=path,
                message=f"Value is greater than maximum allowed",
                expected=f"<= {max_value}",
                received=value
            )
        
        return result
    
    @staticmethod
    def _validate_array(path: str, value: List[Any], 
                       expected_length: Optional[int] = None,
                       min_length: Optional[int] = None,
                       max_length: Optional[int] = None,
                       item_type: Optional[Any] = None) -> ValidationResult:
        """Validate an array value.
        
        Args:
            path: The path to the value in the configuration
            value: The value to validate
            expected_length: Expected length of the array
            min_length: Minimum allowed length
            max_length: Maximum allowed length
            item_type: Expected type of array items
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True)
        
        if expected_length is not None and len(value) != expected_length:
            result.add_error(
                path=path,
                message=f"Invalid array length",
                expected=expected_length,
                received=len(value)
            )
        
        if min_length is not None and len(value) < min_length:
            result.add_error(
                path=path,
                message=f"Array is too short",
                expected=f">= {min_length} elements",
                received=f"{len(value)} elements"
            )
        
        if max_length is not None and len(value) > max_length:
            result.add_error(
                path=path,
                message=f"Array is too long",
                expected=f"<= {max_length} elements",
                received=f"{len(value)} elements"
            )
        
        if item_type is not None:
            for i, item in enumerate(value):
                item_result = ConfigValidator._validate_type(f"{path}[{i}]", item, item_type)
                result = result.combine(item_result)
        
        return result
    
    @staticmethod
    def validate_layout(config: Config) -> ValidationResult:
        """Validate layout configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True)
        
        path = "layout"
        if not config.layout:
            result.add_error(path, "Layout configuration is missing")
            return result
            
        # Validate layout.grid
        grid_path = f"{path}.grid"
        grid = config.layout.get("grid")
        if grid is None:
            result.add_error(grid_path, "Grid configuration is missing")
        else:
            grid_result = ConfigValidator._validate_type(grid_path, grid, dict)
            result = result.combine(grid_result)
            
            if grid_result.is_valid:
                # Validate required grid properties
                required_grid_keys = {"width", "height"}
                keys_result = ConfigValidator._validate_required_keys(
                    grid_path, grid, required_grid_keys
                )
                result = result.combine(keys_result)
                
                # Validate individual properties
                if "width" in grid:
                    width_result = ConfigValidator._validate_type(f"{grid_path}.width", grid["width"], (int, float))
                    result = result.combine(width_result)
                    if width_result.is_valid:
                        range_result = ConfigValidator._validate_range(f"{grid_path}.width", grid["width"], min_value=1)
                        result = result.combine(range_result)
                
                if "height" in grid:
                    height_result = ConfigValidator._validate_type(f"{grid_path}.height", grid["height"], (int, float))
                    result = result.combine(height_result)
                    if height_result.is_valid:
                        range_result = ConfigValidator._validate_range(f"{grid_path}.height", grid["height"], min_value=1)
                        result = result.combine(range_result)
        
        return result
    
    @staticmethod
    def validate_components(config: Config) -> ValidationResult:
        """Validate component configurations.
        
        Args:
            config: Configuration to validate
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True)
        
        path = "components"
        if not config.components:
            result.add_error(path, "Component configuration is missing")
            return result
        
        # Check for at least one component
        if len(config.components) == 0:
            result.add_error(path, "At least one component must be defined")
        
        # Validate each component
        for name, component in config.components.items():
            component_path = f"{path}.{name}"
            
            # Validate component type
            component_result = ConfigValidator._validate_type(component_path, component, dict)
            result = result.combine(component_result)
            
            if component_result.is_valid:
                # Validate required component properties
                required_keys = {"position", "size"}
                keys_result = ConfigValidator._validate_required_keys(
                    component_path, component, required_keys
                )
                result = result.combine(keys_result)
                
                # Validate position
                if "position" in component:
                    position_path = f"{component_path}.position"
                    position = component["position"]
                    
                    position_result = ConfigValidator._validate_type(position_path, position, list)
                    result = result.combine(position_result)
                    
                    if position_result.is_valid:
                        array_result = ConfigValidator._validate_array(
                            position_path, position, 
                            expected_length=2, 
                            item_type=(int, float)
                        )
                        result = result.combine(array_result)
                
                # Validate size
                if "size" in component:
                    size_path = f"{component_path}.size"
                    size = component["size"]
                    
                    size_result = ConfigValidator._validate_type(size_path, size, list)
                    result = result.combine(size_result)
                    
                    if size_result.is_valid:
                        array_result = ConfigValidator._validate_array(
                            size_path, size, 
                            expected_length=2, 
                            item_type=(int, float)
                        )
                        result = result.combine(array_result)
                        
                        # Validate size values
                        if array_result.is_valid:
                            for i, dimension in enumerate(size):
                                dim_result = ConfigValidator._validate_range(
                                    f"{size_path}[{i}]", dimension, min_value=1
                                )
                                result = result.combine(dim_result)
        
        return result
    
    @staticmethod
    def validate_connections(config: Config) -> ValidationResult:
        """Validate connection configurations.
        
        Args:
            config: Configuration to validate
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True)
        
        path = "connections"
        
        if not hasattr(config, "connections") or config.connections is None:
            result.add_error(path, "Connections configuration is missing")
            return result
        
        # Validate connections type
        connections_result = ConfigValidator._validate_type(path, config.connections, list)
        result = result.combine(connections_result)
        
        if not connections_result.is_valid:
            return result
            
        # Validate each connection
        for i, connection in enumerate(config.connections):
            connection_path = f"{path}[{i}]"
            
            # Validate connection type
            connection_result = ConfigValidator._validate_type(connection_path, connection, dict)
            result = result.combine(connection_result)
            
            if connection_result.is_valid:
                # Validate required connection properties
                required_keys = {"source", "target"}
                keys_result = ConfigValidator._validate_required_keys(
                    connection_path, connection, required_keys
                )
                result = result.combine(keys_result)
                
                # Validate source and target
                for key in ["source", "target"]:
                    if key in connection:
                        key_path = f"{connection_path}.{key}"
                        key_value = connection[key]
                        
                        # Check that source and target are strings
                        key_result = ConfigValidator._validate_type(key_path, key_value, str)
                        result = result.combine(key_result)
                        
                        # Check that source and target exist in components
                        if key_result.is_valid and key_value not in config.components:
                            result.add_error(
                                key_path,
                                f"Referenced component does not exist",
                                expected="A valid component name",
                                received=key_value
                            )
                
                # Validate bidirectional flag if present
                if "bidirectional" in connection:
                    bidirectional_path = f"{connection_path}.bidirectional"
                    bidirectional_result = ConfigValidator._validate_type(
                        bidirectional_path, connection["bidirectional"], bool
                    )
                    result = result.combine(bidirectional_result)
        
        return result
    
    @staticmethod
    def validate_fractals(config: Config) -> ValidationResult:
        """Validate fractal configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True)
        
        path = "fractals"
        if not config.fractals:
            result.add_error(path, "Fractal configuration is missing")
            return result
        
        # Validate fractals type
        fractals_result = ConfigValidator._validate_type(path, config.fractals, dict)
        result = result.combine(fractals_result)
        
        if not fractals_result.is_valid:
            return result
        
        # Validate fractal type
        if "type" in config.fractals:
            type_path = f"{path}.type"
            fractal_type = config.fractals["type"]
            
            # Check type is a string
            type_result = ConfigValidator._validate_type(type_path, fractal_type, str)
            result = result.combine(type_result)
            
            # Check type is one of the allowed values
            if type_result.is_valid:
                allowed_types = {"l_system", "mandelbrot", "julia", "cantor"}
                enum_result = ConfigValidator._validate_enum(
                    type_path, fractal_type, allowed_types
                )
                result = result.combine(enum_result)
                
                # Validate parameters based on fractal type
                if enum_result.is_valid and "parameters" in config.fractals:
                    params_path = f"{path}.parameters"
                    params = config.fractals["parameters"]
                    
                    params_result = ConfigValidator._validate_type(params_path, params, dict)
                    result = result.combine(params_result)
                    
                    if params_result.is_valid:
                        # Validate type-specific parameters
                        if fractal_type == "l_system":
                            required_keys = {"axiom", "rules", "angle"}
                            keys_result = ConfigValidator._validate_required_keys(
                                params_path, params, required_keys
                            )
                            result = result.combine(keys_result)
                            
                            # Validate axiom
                            if "axiom" in params:
                                axiom_path = f"{params_path}.axiom"
                                axiom_result = ConfigValidator._validate_type(
                                    axiom_path, params["axiom"], str
                                )
                                result = result.combine(axiom_result)
                            
                            # Validate rules
                            if "rules" in params:
                                rules_path = f"{params_path}.rules"
                                rules_result = ConfigValidator._validate_type(
                                    rules_path, params["rules"], dict
                                )
                                result = result.combine(rules_result)
                            
                            # Validate angle
                            if "angle" in params:
                                angle_path = f"{params_path}.angle"
                                angle_result = ConfigValidator._validate_type(
                                    angle_path, params["angle"], (int, float)
                                )
                                result = result.combine(angle_result)
                        
                        elif fractal_type in {"mandelbrot", "julia"}:
                            # Common parameters for Mandelbrot and Julia sets
                            if "max_iter" in params:
                                max_iter_path = f"{params_path}.max_iter"
                                max_iter_result = ConfigValidator._validate_type(
                                    max_iter_path, params["max_iter"], int
                                )
                                result = result.combine(max_iter_result)
                                
                                if max_iter_result.is_valid:
                                    range_result = ConfigValidator._validate_range(
                                        max_iter_path, params["max_iter"], min_value=1
                                    )
                                    result = result.combine(range_result)
                            
                            # Validate center
                            if "center" in params:
                                center_path = f"{params_path}.center"
                                center = params["center"]
                                
                                center_result = ConfigValidator._validate_type(center_path, center, list)
                                result = result.combine(center_result)
                                
                                if center_result.is_valid:
                                    array_result = ConfigValidator._validate_array(
                                        center_path, center, 
                                        expected_length=2, 
                                        item_type=(int, float)
                                    )
                                    result = result.combine(array_result)
                            
                            # Validate zoom
                            if "zoom" in params:
                                zoom_path = f"{params_path}.zoom"
                                zoom_result = ConfigValidator._validate_type(
                                    zoom_path, params["zoom"], (int, float)
                                )
                                result = result.combine(zoom_result)
                                
                                if zoom_result.is_valid:
                                    range_result = ConfigValidator._validate_range(
                                        zoom_path, params["zoom"], min_value=0.1
                                    )
                                    result = result.combine(range_result)
                            
                            # Julia-specific parameters
                            if fractal_type == "julia":
                                # Validate c_real
                                if "c_real" in params:
                                    c_real_path = f"{params_path}.c_real"
                                    c_real_result = ConfigValidator._validate_type(
                                        c_real_path, params["c_real"], (int, float)
                                    )
                                    result = result.combine(c_real_result)
                                
                                # Validate c_imag
                                if "c_imag" in params:
                                    c_imag_path = f"{params_path}.c_imag"
                                    c_imag_result = ConfigValidator._validate_type(
                                        c_imag_path, params["c_imag"], (int, float)
                                    )
                                    result = result.combine(c_imag_result)
                        
                        elif fractal_type == "cantor":
                            # Validate gap_ratio
                            if "gap_ratio" in params:
                                gap_ratio_path = f"{params_path}.gap_ratio"
                                gap_ratio_result = ConfigValidator._validate_type(
                                    gap_ratio_path, params["gap_ratio"], (int, float)
                                )
                                result = result.combine(gap_ratio_result)
                                
                                if gap_ratio_result.is_valid:
                                    range_result = ConfigValidator._validate_range(
                                        gap_ratio_path, params["gap_ratio"], 
                                        min_value=0, max_value=1
                                    )
                                    result = result.combine(range_result)
        
        return result
    
    @staticmethod
    def validate_animation(config: Config) -> ValidationResult:
        """Validate animation configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True)
        
        path = "animation"
        if not config.animation:
            # Animation is optional, so no error
            return result
        
        # Validate animation type
        animation_result = ConfigValidator._validate_type(path, config.animation, dict)
        result = result.combine(animation_result)
        
        if not animation_result.is_valid:
            return result
        
        # Validate broadcast section if present
        if "broadcast" in config.animation:
            broadcast_path = f"{path}.broadcast"
            broadcast = config.animation["broadcast"]
            
            broadcast_result = ConfigValidator._validate_type(broadcast_path, broadcast, dict)
            result = result.combine(broadcast_result)
            
            if broadcast_result.is_valid:
                # Validate enabled flag
                if "enabled" in broadcast:
                    enabled_path = f"{broadcast_path}.enabled"
                    enabled_result = ConfigValidator._validate_type(
                        enabled_path, broadcast["enabled"], bool
                    )
                    result = result.combine(enabled_result)
                
                # Validate duration
                if "duration" in broadcast:
                    duration_path = f"{broadcast_path}.duration"
                    duration_result = ConfigValidator._validate_type(
                        duration_path, broadcast["duration"], (int, float)
                    )
                    result = result.combine(duration_result)
                    
                    if duration_result.is_valid:
                        range_result = ConfigValidator._validate_range(
                            duration_path, broadcast["duration"], min_value=1
                        )
                        result = result.combine(range_result)
                
                # Validate fps
                if "fps" in broadcast:
                    fps_path = f"{broadcast_path}.fps"
                    fps_result = ConfigValidator._validate_type(
                        fps_path, broadcast["fps"], (int, float)
                    )
                    result = result.combine(fps_result)
                    
                    if fps_result.is_valid:
                        range_result = ConfigValidator._validate_range(
                            fps_path, broadcast["fps"], min_value=1, max_value=120
                        )
                        result = result.combine(range_result)
        
        return result
    
    @staticmethod
    def validate_styling(config: Config) -> ValidationResult:
        """Validate styling configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True)
        
        path = "styling"
        if not config.styling:
            # Styling is optional, so no error
            return result
        
        # Validate styling type
        styling_result = ConfigValidator._validate_type(path, config.styling, dict)
        result = result.combine(styling_result)
        
        if not styling_result.is_valid:
            return result
        
        # Validate background color if present
        if "background" in config.styling:
            bg_path = f"{path}.background"
            bg_result = ConfigValidator._validate_type(
                bg_path, config.styling["background"], str
            )
            result = result.combine(bg_result)
        
        # Validate fonts if present
        if "fonts" in config.styling:
            fonts_path = f"{path}.fonts"
            fonts = config.styling["fonts"]
            
            fonts_result = ConfigValidator._validate_type(fonts_path, fonts, dict)
            result = result.combine(fonts_result)
            
            if fonts_result.is_valid:
                # Validate font sizes if present
                if "sizes" in fonts:
                    sizes_path = f"{fonts_path}.sizes"
                    sizes = fonts["sizes"]
                    
                    sizes_result = ConfigValidator._validate_type(sizes_path, sizes, dict)
                    result = result.combine(sizes_result)
                    
                    if sizes_result.is_valid:
                        # Validate each size
                        for name, size in sizes.items():
                            size_path = f"{sizes_path}.{name}"
                            
                            size_result = ConfigValidator._validate_type(size_path, size, (int, float))
                            result = result.combine(size_result)
                            
                            if size_result.is_valid:
                                range_result = ConfigValidator._validate_range(
                                    size_path, size, min_value=1
                                )
                                result = result.combine(range_result)
        
        # Validate effects if present
        if "effects" in config.styling:
            effects_path = f"{path}.effects"
            effects = config.styling["effects"]
            
            effects_result = ConfigValidator._validate_type(effects_path, effects, dict)
            result = result.combine(effects_result)
            
            if effects_result.is_valid:
                # Validate shadow if present
                if "shadow" in effects:
                    shadow_path = f"{effects_path}.shadow"
                    shadow = effects["shadow"]
                    
                    shadow_result = ConfigValidator._validate_type(shadow_path, shadow, dict)
                    result = result.combine(shadow_result)
                    
                    if shadow_result.is_valid:
                        # Validate blur
                        if "blur" in shadow:
                            blur_path = f"{shadow_path}.blur"
                            blur_result = ConfigValidator._validate_type(
                                blur_path, shadow["blur"], (int, float)
                            )
                            result = result.combine(blur_result)
                            
                            if blur_result.is_valid:
                                range_result = ConfigValidator._validate_range(
                                    blur_path, shadow["blur"], min_value=0
                                )
                                result = result.combine(range_result)
                        
                        # Validate opacity
                        if "opacity" in shadow:
                            opacity_path = f"{shadow_path}.opacity"
                            opacity_result = ConfigValidator._validate_type(
                                opacity_path, shadow["opacity"], (int, float)
                            )
                            result = result.combine(opacity_result)
                            
                            if opacity_result.is_valid:
                                range_result = ConfigValidator._validate_range(
                                    opacity_path, shadow["opacity"], min_value=0, max_value=1
                                )
                                result = result.combine(range_result)
        
        return result
    
    @staticmethod
    def validate_alternative_fractals(config: Config) -> ValidationResult:
        """Validate alternative fractal configurations.
        
        Args:
            config: Configuration to validate
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True)
        
        path = "alternative_fractals"
        if not config.alternative_fractals:
            # Alternative fractals are optional
            return result
        
        # Validate alternative_fractals type
        alt_fractals_result = ConfigValidator._validate_type(path, config.alternative_fractals, dict)
        result = result.combine(alt_fractals_result)
        
        if not alt_fractals_result.is_valid:
            return result
        
        # Validate each alternative fractal
        for name, fractal_config in config.alternative_fractals.items():
            fractal_path = f"{path}.{name}"
            
            # Validate fractal config type
            config_result = ConfigValidator._validate_type(fractal_path, fractal_config, dict)
            result = result.combine(config_result)
            
            if not config_result.is_valid:
                continue
            
            # Validate fractal type
            if "type" in fractal_config:
                type_path = f"{fractal_path}.type"
                fractal_type = fractal_config["type"]
                
                # Check type is a string
                type_result = ConfigValidator._validate_type(type_path, fractal_type, str)
                result = result.combine(type_result)
                
                # Check type is one of the allowed values
                if type_result.is_valid:
                    allowed_types = {"l_system", "mandelbrot", "julia", "cantor"}
                    enum_result = ConfigValidator._validate_enum(
                        type_path, fractal_type, allowed_types
                    )
                    result = result.combine(enum_result)
            else:
                result.add_error(
                    f"{fractal_path}",
                    "Missing required field: type",
                    expected="A fractal type (l_system, mandelbrot, julia, cantor)"
                )
            
            # Validate parameters
            if "parameters" in fractal_config:
                params_path = f"{fractal_path}.parameters"
                params = fractal_config["parameters"]
                
                params_result = ConfigValidator._validate_type(params_path, params, dict)
                result = result.combine(params_result)
            else:
                result.add_error(
                    f"{fractal_path}",
                    "Missing required field: parameters",
                    expected="A parameters object"
                )
        
        return result
        
    @classmethod
    def validate(cls, config: Config) -> ValidationResult:
        """Validate the entire configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True)
        
        # Validate each section
        layout_result = cls.validate_layout(config)
        result = result.combine(layout_result)
        
        components_result = cls.validate_components(config)
        result = result.combine(components_result)
        
        connections_result = cls.validate_connections(config)
        result = result.combine(connections_result)
        
        fractals_result = cls.validate_fractals(config)
        result = result.combine(fractals_result)
        
        alt_fractals_result = cls.validate_alternative_fractals(config)
        result = result.combine(alt_fractals_result)
        
        animation_result = cls.validate_animation(config)
        result = result.combine(animation_result)
        
        styling_result = cls.validate_styling(config)
        result = result.combine(styling_result)
        
        return result