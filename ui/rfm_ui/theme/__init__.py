"""
Theme module for RFM Architecture UI.

This module provides theme definitions and components for creating a premium,
cohesive user interface.
"""

from .tokens import Colors, Typography, Spacing, Elevation, Motion, get_theme_tokens
from .premium_theme import PremiumTheme

# Create singleton instance of PremiumTheme
_theme_instance = None

def get_theme(dark_mode: bool = True):
    """
    Get the singleton theme instance.
    
    Args:
        dark_mode: Whether to use dark mode (True) or light mode (False)
        
    Returns:
        PremiumTheme instance
    """
    global _theme_instance
    if _theme_instance is None:
        _theme_instance = PremiumTheme(dark_mode=dark_mode)
    return _theme_instance

__all__ = [
    'Colors', 
    'Typography', 
    'Spacing', 
    'Elevation', 
    'Motion', 
    'get_theme_tokens',
    'PremiumTheme',
    'get_theme'
]