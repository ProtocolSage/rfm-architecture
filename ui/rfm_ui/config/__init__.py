"""
Configuration module for RFM Architecture UI.

This module provides configuration handling for the RFM Architecture
visualization UI.
"""

from pathlib import Path
import yaml
from typing import Dict, Any, Optional


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    if config_path is None:
        # Try default locations
        default_paths = [
            "config.yaml",
            Path.home() / ".rfm" / "config.yaml",
            Path(__file__).parent / "default_config.yaml"
        ]
        
        for path in default_paths:
            try:
                with open(path, "r") as f:
                    return yaml.safe_load(f)
            except (FileNotFoundError, IOError):
                continue
                
        # No config found, return empty dict
        return {}
    else:
        # Load specified config
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except (FileNotFoundError, IOError) as e:
            raise ValueError(f"Failed to load config from {config_path}: {e}")
            
    return {}