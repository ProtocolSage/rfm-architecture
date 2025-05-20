"""Configuration handling for RFM visualization."""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Union, Tuple

import yaml

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Configuration dataclass for RFM visualization."""
    
    # Layout settings
    layout: Dict[str, Any] = field(default_factory=dict)
    
    # Component definitions
    components: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Connection definitions
    connections: List[Dict[str, Any]] = field(default_factory=list)
    
    # Conscious fields settings
    conscious_fields: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Fractal settings
    fractals: Dict[str, Any] = field(default_factory=dict)
    
    # Alternative fractal presets
    alternative_fractals: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Morphogen settings
    morphogen: Dict[str, Any] = field(default_factory=dict)
    
    # KIN graph settings
    kin_graph: Dict[str, Any] = field(default_factory=dict)
    
    # Phi metric settings
    phi_metric: Dict[str, Any] = field(default_factory=dict)
    
    # Processing scales settings
    processing_scales: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Animation settings
    animation: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Styling settings
    styling: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Config:
        """Create a Config from a dictionary.
        
        Args:
            data: Dictionary with configuration data
        
        Returns:
            Config object
        """
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Config to a dictionary.
        
        Returns:
            Dictionary representation of Config
        """
        return asdict(self)
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """Validate the configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
            is_valid: True if the configuration is valid, False otherwise
            error_message: Error message if the configuration is invalid, None otherwise
        """
        # Import here to avoid circular imports
        from .validator import ConfigValidator
        
        result = ConfigValidator.validate(self)
        
        if result.is_valid:
            return True, None
        
        return False, result.summary()


class ConfigLoader:
    """Configuration loader for RFM visualization."""
    
    @staticmethod
    def _load_yaml(path: Union[str, Path]) -> Dict[str, Any]:
        """Load a YAML file.
        
        Args:
            path: Path to YAML file
        
        Returns:
            Dictionary with YAML contents
        
        Raises:
            FileNotFoundError: If the file does not exist
            yaml.YAMLError: If the file cannot be parsed
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        if not data:
            logger.warning(f"Empty config file: {path}")
            return {}
        
        return data
    
    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries.
        
        Args:
            base: Base dictionary
            override: Dictionary to merge on top of base
        
        Returns:
            Merged dictionary
        """
        result = base.copy()
        
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = ConfigLoader._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    @classmethod
    def from_file(cls, path: Optional[Union[str, Path]] = None, validate: bool = True) -> Config:
        """Load configuration from a file.
        
        Args:
            path: Path to configuration file (defaults to "config.yaml")
            validate: Whether to validate the configuration after loading
        
        Returns:
            Config object
        
        Raises:
            FileNotFoundError: If the file does not exist
            yaml.YAMLError: If the file cannot be parsed
            ValueError: If the configuration is invalid and validate is True
        """
        # Use default if no path is provided
        if path is None:
            path = "config.yaml"
        
        # Load the configuration
        try:
            data = cls._load_yaml(path)
            logger.info(f"Loaded configuration from {path}")
        except FileNotFoundError:
            logger.warning(f"Config file not found: {path}")
            data = {}
        
        # Create the Config object
        config = Config.from_dict(data)
        
        logger.debug(f"Created Config object with {len(config.components)} components")
        
        # Validate the configuration if requested
        if validate:
            is_valid, error_message = config.validate()
            if not is_valid:
                logger.error(f"Invalid configuration: {error_message}")
                raise ValueError(f"Invalid configuration: {error_message}")
        
        return config
    
    @classmethod
    def from_files(cls, base_path: Union[str, Path], override_path: Union[str, Path], 
                  validate: bool = True) -> Config:
        """Load configuration from multiple files, merging them.
        
        Args:
            base_path: Path to base configuration file
            override_path: Path to override configuration file
            validate: Whether to validate the configuration after loading
        
        Returns:
            Config object
        
        Raises:
            FileNotFoundError: If the base file does not exist
            yaml.YAMLError: If a file cannot be parsed
            ValueError: If the configuration is invalid and validate is True
        """
        # Load the base configuration
        base_data = cls._load_yaml(base_path)
        logger.info(f"Loaded base configuration from {base_path}")
        
        # Load the override configuration
        try:
            override_data = cls._load_yaml(override_path)
            logger.info(f"Loaded override configuration from {override_path}")
        except FileNotFoundError:
            logger.warning(f"Override config file not found: {override_path}")
            override_data = {}
        
        # Merge the configurations
        merged_data = cls._deep_merge(base_data, override_data)
        
        # Create the Config object
        config = Config.from_dict(merged_data)
        
        logger.debug(f"Created Config object with {len(config.components)} components")
        
        # Validate the configuration if requested
        if validate:
            is_valid, error_message = config.validate()
            if not is_valid:
                logger.error(f"Invalid configuration: {error_message}")
                raise ValueError(f"Invalid configuration: {error_message}")
        
        return config