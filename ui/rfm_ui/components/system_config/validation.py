"""
Configuration validation for RFM Architecture.

This module provides validation utilities for RFM Architecture configuration files.
It integrates with the core configuration validator to provide enhanced
validation capabilities with user-friendly error reporting.
"""
from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, Tuple, Union, Set
from dataclasses import dataclass

# Import core validation utilities
from rfm.config.settings import Config
from rfm.config.validator import ConfigValidator, ValidationResult, ValidationError

logger = logging.getLogger(__name__)


@dataclass
class FieldValidationError:
    """Represents a validation error specific to a configuration field."""
    
    path: str
    message: str
    expected: Optional[Any] = None
    received: Optional[Any] = None
    field_id: Optional[str] = None
    
    @classmethod
    def from_validation_error(cls, error: ValidationError, field_id: Optional[str] = None) -> 'FieldValidationError':
        """
        Create a FieldValidationError from a ValidationError.
        
        Args:
            error: The validation error
            field_id: Optional UI field ID
            
        Returns:
            FieldValidationError
        """
        return cls(
            path=error.path,
            message=error.message,
            expected=error.expected,
            received=error.received,
            field_id=field_id
        )
    
    def to_user_message(self) -> str:
        """
        Get a user-friendly error message.
        
        Returns:
            User-friendly error message
        """
        base_message = f"{self.path}: {self.message}"
        
        if self.expected is not None and self.received is not None:
            base_message += f" (expected: {self.expected}, received: {self.received})"
            
        return base_message


@dataclass
class ValidationResults:
    """Results of configuration validation with field-specific information."""
    
    is_valid: bool
    errors: List[FieldValidationError]
    error_fields: Set[str]
    
    @classmethod
    def from_validation_result(cls, result: ValidationResult, field_mapping: Dict[str, str] = None) -> 'ValidationResults':
        """
        Create ValidationResults from a ValidationResult.
        
        Args:
            result: The validation result
            field_mapping: Optional mapping from config paths to field IDs
            
        Returns:
            ValidationResults
        """
        field_mapping = field_mapping or {}
        errors = []
        error_fields = set()
        
        for error in result.errors:
            field_id = field_mapping.get(error.path)
            field_error = FieldValidationError.from_validation_error(error, field_id)
            errors.append(field_error)
            
            if field_id:
                error_fields.add(field_id)
                
        return cls(
            is_valid=result.is_valid,
            errors=errors,
            error_fields=error_fields
        )
    
    def get_summary(self) -> str:
        """
        Get a summary of the validation results.
        
        Returns:
            Validation summary
        """
        if self.is_valid:
            return "Configuration is valid."
        
        return f"Configuration has {len(self.errors)} errors:\n" + "\n".join(
            f"- {error.to_user_message()}" for error in self.errors
        )


def validate_config(config: Union[Config, Dict[str, Any]], field_mapping: Dict[str, str] = None) -> ValidationResults:
    """
    Validate a configuration.
    
    Args:
        config: Configuration to validate (Config object or dict)
        field_mapping: Optional mapping from config paths to field IDs
        
    Returns:
        ValidationResults with field-specific information
    """
    logger.debug("Validating configuration")
    
    # Convert dict to Config if needed
    if isinstance(config, dict):
        config = Config.from_dict(config)
    
    # Perform validation using core validator
    result = ConfigValidator.validate(config)
    
    # Convert to field-specific results
    field_results = ValidationResults.from_validation_result(result, field_mapping)
    
    if field_results.is_valid:
        logger.info("Configuration validation successful")
    else:
        logger.warning(f"Configuration validation failed with {len(field_results.errors)} errors")
        
    return field_results


def get_field_type(value: Any) -> str:
    """
    Determine the field type based on the value.
    
    Args:
        value: The value to check
        
    Returns:
        Field type string
    """
    if isinstance(value, str):
        # Check if this looks like a color
        if value.startswith("#") and (len(value) == 7 or len(value) == 9):
            return "color"
        return "string"
    elif isinstance(value, int):
        return "int"
    elif isinstance(value, float):
        return "float"
    elif isinstance(value, bool):
        return "bool"
    elif isinstance(value, list):
        return "array"
    elif isinstance(value, dict):
        return "object"
    else:
        # Default to string for unknown types
        return "string"


def get_field_constraints(key: str, field_type: str) -> Dict[str, Any]:
    """
    Get constraints for a field based on its key and type.
    
    Args:
        key: Field key
        field_type: Field type
        
    Returns:
        Dictionary of constraints
    """
    constraints = {}
    
    # Define constraints based on field name and type
    if field_type == "int" or field_type == "float":
        if key in ["width", "height", "size", "zoom", "depth"]:
            constraints["min"] = 1
        elif key in ["opacity", "alpha"]:
            constraints["min"] = 0.0
            constraints["max"] = 1.0
        elif key in ["angle", "rotation"]:
            constraints["min"] = 0
            constraints["max"] = 360
    
    return constraints