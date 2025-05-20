"""
Standalone application for the System Configuration Manager.

This module provides a standalone application entry point for the System Configuration Manager.
"""
from __future__ import annotations

import os
import sys
import logging
import argparse
from typing import Dict, Any, Optional, List, Tuple
import traceback
from datetime import datetime

import dearpygui.dearpygui as dpg

from .manager import SystemConfigManager
from .theme import get_theme
from .constants import THEME

logger = logging.getLogger(__name__)


def configure_logging(
    log_level: str = "info",
    log_file: Optional[str] = None,
    console: bool = True,
) -> None:
    """
    Configure logging.
    
    Args:
        log_level: Logging level
        log_file: Optional log file path
        console: Whether to log to console
    """
    # Set up logging
    log_level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }
    
    level = log_level_map.get(log_level.lower(), logging.INFO)
    
    # Configure logging
    handlers = []
    
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        handlers.append(console_handler)
    
    if log_file:
        try:
            # Ensure log directory exists
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
                
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            handlers.append(file_handler)
        except Exception as e:
            print(f"Error setting up log file: {e}")
    
    # Configure logging
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )


def check_dependencies() -> Tuple[bool, List[str]]:
    """
    Check if all dependencies are installed.
    
    Returns:
        Tuple of (success, missing dependencies)
    """
    missing = []
    
    # Check Python version
    if sys.version_info < (3, 7):
        missing.append(f"Python 3.7+ (found {sys.version})")
    
    # Check required packages
    required_packages = [
        "dearpygui",
        "pyyaml",
    ]
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    return len(missing) == 0, missing


def run_standalone_app() -> int:
    """
    Run the system configuration manager as a standalone application.
    
    Returns:
        Exit code
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="RFM Architecture System Configuration Manager"
    )
    parser.add_argument(
        "--config",
        help="Path to configuration file",
        default=None,
    )
    parser.add_argument(
        "--schema",
        help="Path to configuration schema file",
        default=None,
    )
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error", "critical"],
        default="info",
        help="Logging level",
    )
    parser.add_argument(
        "--log-file",
        help="Path to log file",
        default=None,
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1280,
        help="Window width",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=800,
        help="Window height",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="RFM Architecture System Configuration Manager v1.0",
    )
    
    args = parser.parse_args()
    
    # Configure logging
    log_file = args.log_file
    if log_file is None:
        # Use default log file if not specified
        log_dir = os.path.join(os.path.expanduser("~"), ".rfm", "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"config_manager_{timestamp}.log")
    
    configure_logging(
        log_level=args.log_level,
        log_file=log_file,
        console=True,
    )
    
    logger.info(f"Starting RFM Architecture System Configuration Manager")
    
    try:
        # Check dependencies
        dependencies_ok, missing = check_dependencies()
        if not dependencies_ok:
            logger.error(f"Missing dependencies: {', '.join(missing)}")
            print(f"Error: Missing dependencies: {', '.join(missing)}")
            return 1
        
        # Initialize DearPyGui
        dpg.create_context()
        
        # Create viewport
        dpg.create_viewport(
            title="RFM Architecture System Configuration Manager",
            width=args.width,
            height=args.height,
        )
        
        # Set up fonts
        with dpg.font_registry():
            default_font = dpg.add_font("fonts/Roboto-Regular.ttf", 16)
        
        # Create theme
        theme = get_theme()
        theme.setup()
        
        # Add a window for the application
        with dpg.window(
            label="System Config Manager",
            tag="main_window",
            no_close=True,
        ):
            # Create the system configuration manager
            config_manager = SystemConfigManager(dpg.last_item())
        
        # Set up the viewport
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("main_window", True)
        
        # Set default font
        if default_font:
            dpg.bind_font(default_font)
        
        # Start the main loop
        dpg.start_dearpygui()
        dpg.destroy_context()
        
        logger.info(f"RFM Architecture System Configuration Manager exited")
        
        return 0
    
    except Exception as e:
        traceback_str = traceback.format_exc()
        logger.critical(f"Unhandled exception: {e}\n{traceback_str}")
        print(f"Error: {e}")
        
        # Ensure DPG context is destroyed
        if dpg.is_viewport_alive():
            dpg.stop_dearpygui()
        
        if dpg.does_context_exist():
            dpg.destroy_context()
        
        return 1


if __name__ == "__main__":
    sys.exit(run_standalone_app())