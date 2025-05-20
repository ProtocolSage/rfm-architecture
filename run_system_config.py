#!/usr/bin/env python3
"""
Run the RFM Architecture System Configuration Manager as a standalone application.

This script serves as an entry point to launch the System Configuration Manager,
providing command-line options for customization and configuration.

Usage:
    python run_system_config.py [options]

Options:
    --config PATH        Path to configuration file to open on startup
    --schema PATH        Path to configuration schema file for validation
    --log-level LEVEL    Set logging level (debug, info, warning, error, critical)
    --log-file PATH      Path to log file (default: ~/.rfm/logs/config_manager_TIMESTAMP.log)
    --width WIDTH        Set window width (default: 1280)
    --height HEIGHT      Set window height (default: 800)
    --version            Show version information and exit
    --help               Show help message and exit
"""
import os
import sys
import platform
import logging
import traceback
import argparse
from datetime import datetime
from typing import Optional, List, Tuple

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def validate_python_version() -> bool:
    """
    Validate the Python version.
    
    Returns:
        True if Python version is sufficient, False otherwise
    """
    min_version = (3, 7)
    current_version = sys.version_info[:2]
    
    if current_version < min_version:
        print(f"Error: Python {min_version[0]}.{min_version[1]}+ is required. "
              f"Current version is {current_version[0]}.{current_version[1]}.")
        return False
    
    return True


def check_dependencies() -> Tuple[bool, List[str]]:
    """
    Check if all dependencies are installed.
    
    Returns:
        Tuple of (success, missing dependencies)
    """
    missing = []
    
    # Check required packages
    required_packages = [
        "dearpygui",
        "pyyaml",
        "numpy",
    ]
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    return len(missing) == 0, missing


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
    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }
    
    level = level_map.get(log_level.lower(), logging.INFO)
    
    # Configure logging
    handlers = []
    
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        
        # Color formatting for console output
        if platform.system() != "Windows" or "ANSICON" in os.environ:
            # Define color codes
            colors = {
                logging.DEBUG: '\033[36m',      # Cyan
                logging.INFO: '\033[0m',        # Default
                logging.WARNING: '\033[33m',    # Yellow
                logging.ERROR: '\033[31m',      # Red
                logging.CRITICAL: '\033[1;31m', # Bold Red
            }
            reset = '\033[0m'
            
            class ColorFormatter(logging.Formatter):
                def format(self, record):
                    levelname = record.levelname
                    color = colors.get(record.levelno, '\033[0m')
                    record.levelname = f"{color}{levelname}{reset}"
                    return super().format(record)
            
            formatter = ColorFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
        
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
            if console:
                print(f"Error setting up log file: {e}")
    
    # Configure logging
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="RFM Architecture System Configuration Manager",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    
    parser.add_argument(
        "--config",
        metavar="PATH",
        help="Path to configuration file to open on startup",
    )
    
    parser.add_argument(
        "--schema",
        metavar="PATH",
        help="Path to configuration schema file for validation",
    )
    
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error", "critical"],
        default="info",
        help="Set logging level",
    )
    
    parser.add_argument(
        "--log-file",
        metavar="PATH",
        help="Path to log file (default: ~/.rfm/logs/config_manager_TIMESTAMP.log)",
    )
    
    parser.add_argument(
        "--width",
        type=int,
        default=1280,
        help="Set window width",
    )
    
    parser.add_argument(
        "--height",
        type=int,
        default=800,
        help="Set window height",
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="RFM Architecture System Configuration Manager v1.0",
    )
    
    return parser.parse_args()


def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code
    """
    # Validate Python version
    if not validate_python_version():
        return 1
    
    # Parse arguments
    args = parse_arguments()
    
    # Set up default log file if not specified
    log_file = args.log_file
    if log_file is None:
        # Use default log file if not specified
        log_dir = os.path.join(os.path.expanduser("~"), ".rfm", "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"config_manager_{timestamp}.log")
    
    # Configure logging
    configure_logging(
        log_level=args.log_level,
        log_file=log_file,
        console=True,
    )
    
    logger = logging.getLogger("rfm_config")
    logger.info(f"Starting RFM Architecture System Configuration Manager")
    logger.info(f"Python version: {platform.python_version()}")
    logger.info(f"Platform: {platform.platform()}")
    
    try:
        # Check dependencies
        dependencies_ok, missing = check_dependencies()
        if not dependencies_ok:
            missing_str = ", ".join(missing)
            logger.error(f"Missing dependencies: {missing_str}")
            print(f"Error: Missing dependencies: {missing_str}")
            print(f"Please install missing dependencies with:")
            print(f"pip install {' '.join(missing)}")
            return 1
        
        # Import the system configuration manager
        # This import is delayed to allow checking Python version and dependencies first
        from ui.rfm_ui.components.system_config import run_system_config_manager
        
        # Pass arguments to the run function via sys.argv
        # This is a bit of a hack, but it works
        sys.argv = [
            sys.argv[0],
            f"--config={args.config}" if args.config else "",
            f"--schema={args.schema}" if args.schema else "",
            f"--log-level={args.log_level}",
            f"--log-file={log_file}",
            f"--width={args.width}",
            f"--height={args.height}",
        ]
        # Remove empty arguments
        sys.argv = [arg for arg in sys.argv if arg]
        
        # Run the system configuration manager
        run_system_config_manager()
        
        logger.info("RFM Architecture System Configuration Manager exited normally")
        return 0
    
    except ModuleNotFoundError as e:
        logger.critical(f"Module not found: {e}")
        print(f"Error: Module not found: {e}")
        print("Please check that the RFM Architecture project is properly installed.")
        return 1
    
    except ImportError as e:
        logger.critical(f"Import error: {e}")
        print(f"Error: Import error: {e}")
        print("Please check that the RFM Architecture project is properly installed.")
        return 1
    
    except Exception as e:
        # Log the full traceback
        logger.critical(f"Unhandled exception: {e}\n{traceback.format_exc()}")
        
        # Print a user-friendly error message
        print(f"Error: {e}")
        print(f"See log file for details: {log_file}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(130)  # 128 + SIGINT(2) = 130, standard exit code for Ctrl+C
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)