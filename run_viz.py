#!/usr/bin/env python
"""Simple script to run the RFM visualization."""

import sys
import os
import argparse
from pathlib import Path

# Add the current directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rfm.main import main

if __name__ == "__main__":
    # Create a simple parser for arguments
    parser = argparse.ArgumentParser(description="Run RFM Visualization")
    parser.add_argument("--output", default="rfm_diagram.svg", help="Output file path")
    parser.add_argument("--format", default="svg", choices=["svg", "png", "pdf"], help="Output format")
    parser.add_argument("--dpi", type=int, default=300, help="DPI for raster formats")
    parser.add_argument("--show", action="store_true", help="Show visualization in a window")
    parser.add_argument("--animate", action="store_true", help="Enable animations")
    parser.add_argument("--dark-mode", action="store_true", help="Enable dark mode")
    
    args = parser.parse_args()
    
    # Set environment variables to match args
    os.environ["RFM_OUTPUT"] = args.output
    os.environ["RFM_FORMAT"] = args.format
    os.environ["RFM_DPI"] = str(args.dpi)
    os.environ["RFM_SHOW"] = "1" if args.show else "0"
    os.environ["RFM_ANIMATE"] = "1" if args.animate else "0"
    os.environ["RFM_DARK_MODE"] = "1" if args.dark_mode else "0"
    
    # Call the main function
    sys.exit(main())