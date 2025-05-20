#!/usr/bin/env python
"""
Configuration validation script for RFM Architecture.

Usage:
    python validate_config.py [config_file]

If no config_file is provided, it defaults to 'config.yaml'.
"""
import sys
import logging
from pathlib import Path
from typing import List, Optional

from rfm.config.settings import ConfigLoader


def validate_config(config_path: str) -> bool:
    """Validate a configuration file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        True if the configuration is valid, False otherwise
    """
    try:
        # Attempt to load and validate the configuration
        ConfigLoader.from_file(config_path, validate=True)
        print(f"✅ Configuration '{config_path}' is valid.")
        return True
    except ValueError as e:
        # Print validation errors
        print(f"❌ Configuration '{config_path}' is invalid:")
        print(f"{e}")
        return False
    except Exception as e:
        # Print other errors
        print(f"❌ Error validating configuration '{config_path}':")
        print(f"{e}")
        return False


def main(args: Optional[List[str]] = None) -> int:
    """Run the validation script.
    
    Args:
        args: Command-line arguments
        
    Returns:
        0 if successful, 1 otherwise
    """
    if args is None:
        args = sys.argv[1:]
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Parse arguments
    config_path = args[0] if args else "config.yaml"
    
    # Validate the configuration
    if validate_config(config_path):
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())