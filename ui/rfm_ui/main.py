"""
Main entry point for RFM Architecture UI.

This module provides the main entry point for the RFM Architecture
visualization UI.
"""

import os
import sys
import argparse
from typing import List, Optional

from rfm.core.logging_config import configure_logging, LogLevel
from rfm_ui.ui import RFMApp


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="RFM Architecture Visualization UI"
    )
    
    parser.add_argument(
        "--config", "-c",
        help="Path to configuration file",
        default=None
    )
    
    parser.add_argument(
        "--log-dir", "-l",
        help="Directory for log files",
        default="logs"
    )
    
    parser.add_argument(
        "--debug",
        help="Enable debug logging",
        action="store_true"
    )
    
    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Parse arguments
    args = parse_args(args)

    configure_logging(
        app_name="rfm_ui",
        log_dir=args.log_dir,
        console_level=LogLevel.DEBUG if args.debug else LogLevel.INFO,
    )

    # Create and run application
    app = RFMApp(
        config_file=args.config,
        log_dir=args.log_dir
    )
    
    if not app.initialize():
        return 1
        
    return app.run()


if __name__ == "__main__":
    sys.exit(main())