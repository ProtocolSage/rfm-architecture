"""Command-line interface for RFM visualization."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)


def parse_args():
    """Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        prog="rfm-viz",
        description="Generate a visualization of the Recursive Fractal Mind architecture."
    )
    
    parser.add_argument(
        "--config", 
        default="config.yaml", 
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--format", 
        choices=["svg", "png", "pdf"], 
        default="svg", 
        help="Output format"
    )
    
    parser.add_argument(
        "--dpi", 
        type=int, 
        default=300, 
        help="DPI for raster formats"
    )
    
    parser.add_argument(
        "--output", 
        default="rfm_architecture", 
        help="Output filename (without extension)"
    )
    
    parser.add_argument(
        "--show", 
        action="store_true", 
        help="Show the visualization in a window"
    )
    
    parser.add_argument(
        "--animate", 
        action="store_true", 
        help="Enable animation"
    )
    
    parser.add_argument(
        "--log-level", 
        choices=["debug", "info", "warning", "error", "critical"], 
        default="info", 
        help="Logging level"
    )
    
    parser.add_argument(
        "--dark-mode",
        action="store_true",
        help="Use dark mode (dark background)"
    )
    
    args = parser.parse_args()
    
    return args