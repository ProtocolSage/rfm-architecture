"""
System Configuration Module for RFM Architecture.

This module provides a comprehensive UI for viewing and editing all aspects of
the RFM Architecture system configuration. It integrates with the configuration
schema and validator to provide a user-friendly interface for managing complex
configuration settings.
"""
from typing import Optional, Dict, Any

# Export public interface
from .manager import SystemConfigManager
from .editor import SystemConfigEditor
from .comparison import ConfigComparisonTool
from .io import ConfigFileManager
from .validation import validate_config


__all__ = [
    'SystemConfigManager',
    'SystemConfigEditor',
    'ConfigComparisonTool',
    'ConfigFileManager',
    'validate_config',
]


def run_system_config_manager() -> None:
    """Run the system configuration manager as a standalone application."""
    from .app import run_standalone_app
    run_standalone_app()