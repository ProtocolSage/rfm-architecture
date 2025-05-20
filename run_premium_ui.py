#!/usr/bin/env python3
"""
Run the RFM Architecture with the premium UI.

This script launches the RFM Architecture Visualizer with the enhanced
premium UI components and styling.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Ensure we can import from the RFM Architecture package
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
# Also add ui directory to path explicitly for rfm_ui imports
ui_path = os.path.join(project_root, 'ui')
sys.path.append(ui_path)

from ui.rfm_ui.ui.app_premium import PremiumRFMApp


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="RFM Architecture Visualizer with Premium UI"
    )
    
    parser.add_argument(
        "--config", 
        type=str, 
        default="config.yaml",
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--log-dir", 
        type=str, 
        default="logs",
        help="Directory for logs"
    )
    
    parser.add_argument(
        "--load", 
        type=str, 
        default=None,
        help="Load preset from encoded share link"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the application."""
    # Parse command line arguments
    args = parse_args()
    
    try:
        # Check if preset link is provided
        preset_params = None
        if args.load:
            try:
                # Try to decode preset link
                from ui.rfm_ui.utils.share import decode_preset, validate_preset
                preset_params = decode_preset(args.load)
                
                # Validate preset parameters
                if not validate_preset(preset_params):
                    print("Invalid preset parameters in share link", file=sys.stderr)
                    preset_params = None
                    
            except ImportError as e:
                print(f"Failed to import share module: {e}", file=sys.stderr)
            except ValueError as e:
                print(f"Failed to decode share link: {e}", file=sys.stderr)
        
        # Create and initialize the app
        app = PremiumRFMApp(
            config_file=args.config,
            log_dir=args.log_dir,
            initial_params=preset_params
        )
        
        # Initialize the app
        if not app.initialize():
            print("Failed to initialize application", file=sys.stderr)
            return 1
            
        # Run the app
        return app.run()
    except Exception as e:
        print(f"Error running application: {e}", file=sys.stderr)
        logging.error(f"Error running application: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())