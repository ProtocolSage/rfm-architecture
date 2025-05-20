"""
Configuration file I/O operations for RFM Architecture.

This module provides utilities for loading and saving RFM Architecture
configuration files with robust error handling.
"""
from __future__ import annotations

import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Tuple
from dataclasses import dataclass

# Import core configuration utilities
from rfm.config.settings import Config, ConfigLoader

logger = logging.getLogger(__name__)


@dataclass
class LoadResult:
    """Result of loading a configuration file."""
    
    success: bool
    config: Optional[Config]
    error_message: Optional[str] = None
    file_path: Optional[str] = None
    
    @property
    def has_error(self) -> bool:
        """Check if the load operation encountered an error."""
        return not self.success or self.error_message is not None


@dataclass
class SaveResult:
    """Result of saving a configuration file."""
    
    success: bool
    file_path: Optional[str] = None
    error_message: Optional[str] = None
    
    @property
    def has_error(self) -> bool:
        """Check if the save operation encountered an error."""
        return not self.success or self.error_message is not None


class ConfigFileManager:
    """
    Manager for configuration file operations.
    
    This class provides utilities for loading and saving configuration files
    with robust error handling.
    """
    
    DEFAULT_CONFIG_PATHS = [
        "config.yaml",
        str(Path.home() / ".rfm" / "config.yaml"),
    ]
    
    @classmethod
    def load_config(cls, file_path: Optional[str] = None, validate: bool = True) -> LoadResult:
        """
        Load a configuration file.
        
        Args:
            file_path: Path to the configuration file, or None to use default paths
            validate: Whether to validate the configuration after loading
            
        Returns:
            LoadResult containing the loaded configuration or error details
        """
        # Try to find a configuration file
        paths_to_try = [file_path] if file_path else cls.DEFAULT_CONFIG_PATHS
        
        # Remove None values
        paths_to_try = [p for p in paths_to_try if p]
        
        for path in paths_to_try:
            try:
                logger.info(f"Loading configuration from {path}")
                
                # Try to load the configuration using the core loader
                config = ConfigLoader.from_file(path, validate=validate)
                
                logger.info(f"Successfully loaded configuration from {path}")
                
                return LoadResult(
                    success=True,
                    config=config,
                    file_path=path
                )
            
            except FileNotFoundError:
                logger.warning(f"Configuration file not found: {path}")
                continue
                
            except yaml.YAMLError as e:
                logger.error(f"Error parsing YAML in {path}: {e}")
                return LoadResult(
                    success=False,
                    config=None,
                    error_message=f"Error parsing YAML: {e}",
                    file_path=path
                )
                
            except ValueError as e:
                logger.error(f"Invalid configuration in {path}: {e}")
                return LoadResult(
                    success=False,
                    config=None,
                    error_message=f"Invalid configuration: {e}",
                    file_path=path
                )
                
            except Exception as e:
                logger.error(f"Unexpected error loading {path}: {e}", exc_info=True)
                return LoadResult(
                    success=False,
                    config=None,
                    error_message=f"Unexpected error: {e}",
                    file_path=path
                )
        
        # If we get here, no configuration file was found
        logger.warning("No configuration file found")
        
        # Create an empty configuration
        return LoadResult(
            success=True,
            config=Config(),
            error_message="No configuration file found, created new empty configuration",
            file_path=None
        )
    
    @classmethod
    def save_config(cls, config: Config, file_path: str, create_parent_dirs: bool = True) -> SaveResult:
        """
        Save a configuration to a file.
        
        Args:
            config: Configuration to save
            file_path: Path to save the configuration to
            create_parent_dirs: Whether to create parent directories if they don't exist
            
        Returns:
            SaveResult indicating success or failure
        """
        try:
            logger.info(f"Saving configuration to {file_path}")
            
            # Ensure the parent directory exists
            parent_dir = os.path.dirname(file_path)
            if parent_dir and not os.path.exists(parent_dir):
                if create_parent_dirs:
                    logger.info(f"Creating parent directory: {parent_dir}")
                    os.makedirs(parent_dir, exist_ok=True)
                else:
                    logger.error(f"Parent directory doesn't exist: {parent_dir}")
                    return SaveResult(
                        success=False,
                        error_message=f"Parent directory doesn't exist: {parent_dir}",
                        file_path=file_path
                    )
            
            # Convert config to dict and save
            config_dict = config.to_dict()
            
            # Save based on file extension
            if file_path.endswith((".yml", ".yaml")):
                with open(file_path, "w") as f:
                    yaml.dump(config_dict, f, default_flow_style=False)
            elif file_path.endswith(".json"):
                with open(file_path, "w") as f:
                    json.dump(config_dict, f, indent=2)
            else:
                # Default to YAML
                with open(file_path, "w") as f:
                    yaml.dump(config_dict, f, default_flow_style=False)
            
            logger.info(f"Successfully saved configuration to {file_path}")
            
            return SaveResult(
                success=True,
                file_path=file_path
            )
            
        except IOError as e:
            logger.error(f"I/O error saving configuration to {file_path}: {e}")
            return SaveResult(
                success=False,
                error_message=f"I/O error: {e}",
                file_path=file_path
            )
            
        except Exception as e:
            logger.error(f"Unexpected error saving configuration to {file_path}: {e}", exc_info=True)
            return SaveResult(
                success=False,
                error_message=f"Unexpected error: {e}",
                file_path=file_path
            )
    
    @classmethod
    def get_default_paths(cls) -> List[str]:
        """
        Get the default configuration file paths.
        
        Returns:
            List of default configuration file paths
        """
        return cls.DEFAULT_CONFIG_PATHS.copy()
    
    @classmethod
    def get_first_existing_path(cls) -> Optional[str]:
        """
        Get the first existing configuration file path.
        
        Returns:
            Path to the first existing configuration file, or None if none exist
        """
        for path in cls.DEFAULT_CONFIG_PATHS:
            if os.path.exists(path):
                return path
        return None