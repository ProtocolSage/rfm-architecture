"""Encode/decode presets for copy-to-clipboard links."""
from __future__ import annotations

import base64
import json
import urllib.parse
import logging
import datetime
from typing import Dict, Any, Optional, Union

# Set up logger
logger = logging.getLogger("rfm_ui.share")

# URL prefix for RFM preset links
PREFIX = "rfm://preset?data="

def encode_preset(params: Dict[str, Any]) -> str:
    """
    Encode fractal parameters into a shareable link.
    
    Args:
        params: Dictionary of fractal parameters
        
    Returns:
        Encoded URL string that can be shared
    """
    try:
        # Add metadata to parameters
        metadata = {
            "version": "1.0",
            "created": datetime.datetime.now().isoformat(),
            "type": "preset"
        }
        
        # Combine parameters and metadata
        data = {
            "meta": metadata,
            "params": params
        }
        
        # Serialize to JSON
        raw = json.dumps(data, separators=(',', ':'))
        
        # Base64 encode
        b64 = base64.urlsafe_b64encode(raw.encode()).decode()
        
        # Create URL with prefix
        result = PREFIX + urllib.parse.quote_plus(b64)
        
        logger.debug(f"Encoded preset: {len(result)} characters")
        return result
    except Exception as e:
        logger.error(f"Error encoding preset: {str(e)}")
        raise ValueError(f"Failed to encode preset: {str(e)}")

def decode_preset(link: str) -> Dict[str, Any]:
    """
    Decode a preset link into fractal parameters.
    
    Args:
        link: Encoded preset link
        
    Returns:
        Dictionary of fractal parameters
        
    Raises:
        ValueError: If the link is invalid or cannot be decoded
    """
    try:
        # Validate prefix
        if not link.startswith(PREFIX):
            raise ValueError("Invalid preset link format")
        
        # Extract encoded data
        b64 = urllib.parse.unquote_plus(link[len(PREFIX):])
        
        # Base64 decode
        raw = base64.urlsafe_b64decode(b64)
        
        # Parse JSON
        data = json.loads(raw)
        
        # Extract parameters
        if "params" not in data:
            raise ValueError("Invalid preset data: missing parameters")
        
        logger.debug(f"Decoded preset: {data.get('meta', {}).get('type', 'unknown')}")
        return data["params"]
    except Exception as e:
        logger.error(f"Error decoding preset: {str(e)}")
        raise ValueError(f"Failed to decode preset: {str(e)}")

def validate_preset(params: Dict[str, Any]) -> bool:
    """
    Validate that parameters contain essential fractal settings.
    
    Args:
        params: Dictionary of fractal parameters
        
    Returns:
        True if parameters are valid, False otherwise
    """
    # Check for required parameters
    if "type" not in params:
        logger.warning("Missing required parameter: type")
        return False
    
    # Validate based on fractal type
    fractal_type = params.get("type", "").lower()
    
    if fractal_type == "mandelbrot":
        required = ["center_x", "center_y", "zoom", "max_iter"]
    elif fractal_type == "julia":
        required = ["c_real", "c_imag", "center_x", "center_y", "zoom", "max_iter"]
    elif fractal_type == "l_system":
        required = ["axiom", "rules", "angle", "iterations"]
    elif fractal_type == "cantor dust":
        required = ["gap_ratio", "iterations"]
    else:
        logger.warning(f"Unknown fractal type: {fractal_type}")
        return False
    
    # Check for required parameters
    for param in required:
        if param not in params:
            logger.warning(f"Missing required parameter for {fractal_type}: {param}")
            return False
    
    return True