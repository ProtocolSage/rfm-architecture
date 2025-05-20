"""
Constants for the System Configuration module.

This module defines constants used throughout the System Configuration module.
"""
from typing import Dict, Any, List

# Configuration sections information
CONFIG_SECTIONS = [
    {
        "name": "layout",
        "label": "Layout",
        "description": "Grid and layout settings",
        "icon": "grid-3x3",  # Material Design icon name
        "color": [46, 204, 113],  # Green
    },
    {
        "name": "components",
        "label": "Components",
        "description": "Component definitions",
        "icon": "widgets",
        "color": [52, 152, 219],  # Blue
    },
    {
        "name": "connections",
        "label": "Connections",
        "description": "Connection definitions",
        "icon": "share",
        "color": [155, 89, 182],  # Purple
    },
    {
        "name": "conscious_fields",
        "label": "Conscious Fields",
        "description": "Conscious field settings",
        "icon": "psychology",
        "color": [241, 196, 15],  # Yellow
    },
    {
        "name": "fractals",
        "label": "Fractals",
        "description": "Fractal visualization settings",
        "icon": "auto-awesome",
        "color": [230, 126, 34],  # Orange
    },
    {
        "name": "morphogen",
        "label": "Morphogen",
        "description": "Morphogenetic pattern settings",
        "icon": "biotech",
        "color": [231, 76, 60],  # Red
    },
    {
        "name": "kin_graph",
        "label": "KIN Graph",
        "description": "Knowledge Integration Network settings",
        "icon": "account-tree",
        "color": [142, 68, 173],  # Deep Purple
    },
    {
        "name": "phi_metric",
        "label": "Phi Metric",
        "description": "Phi metric settings",
        "icon": "calculate",
        "color": [41, 128, 185],  # Light Blue
    },
    {
        "name": "processing_scales",
        "label": "Processing Scales",
        "description": "Processing scale settings",
        "icon": "layers",
        "color": [243, 156, 18],  # Orange Yellow
    },
    {
        "name": "animation",
        "label": "Animation",
        "description": "Animation settings",
        "icon": "animation",
        "color": [26, 188, 156],  # Turquoise
    },
    {
        "name": "styling",
        "label": "Styling",
        "description": "Global styling settings",
        "icon": "palette",
        "color": [192, 57, 43],  # Dark Red
    }
]

# Field descriptions based on common keys
FIELD_DESCRIPTIONS = {
    "width": "Width dimension",
    "height": "Height dimension",
    "position": "Position coordinates [x, y]",
    "size": "Size dimensions [width, height]",
    "color": "Color (hex format, e.g. #FF0000)",
    "label": "Display label",
    "description": "Descriptive text",
    "zorder": "Z-ordering for rendering (higher values appear on top)",
    "source": "Source component ID",
    "target": "Target component ID",
    "curve": "Curve factor for connections",
    "bidirectional": "Whether connection is bidirectional",
    "type": "Type identifier",
    "depth": "Recursion or nesting depth",
    "origin": "Origin coordinates [x, y]",
    "golden_ratio": "Golden ratio value for layout",
    "angle": "Angle in degrees",
    "alpha": "Opacity/alpha value (0-1)",
    "enabled": "Whether feature is enabled",
    "duration": "Duration in milliseconds",
    "fps": "Frames per second",
    "axiom": "Initial axiom for L-systems",
    "rules": "Production rules for L-systems",
    "center": "Center coordinates [x, y]",
    "zoom": "Zoom level",
    "max_iter": "Maximum iterations",
    "cmap": "Colormap name",
    "c_real": "Real part of complex parameter",
    "c_imag": "Imaginary part of complex parameter",
    "gap_ratio": "Gap ratio (0-1)",
    "pulse_count": "Number of pulses",
    "easing": "Easing function specification",
    "glow": "Whether glow effect is enabled",
    "background": "Background color",
    "border": "Border color",
    "blur": "Blur radius",
    "opacity": "Opacity value (0-1)"
}

# Required fields for each section
REQUIRED_FIELDS = {
    "layout": {"width", "height"},
    "components": {"position", "size"},
    "connections": {"source", "target"},
    "fractals": {"type", "parameters"}
}

# Premium theme colors
THEME = {
    "primary": [46, 134, 193],  # Medium Blue
    "secondary": [155, 89, 182],  # Purple
    "success": [46, 204, 113],  # Green
    "error": [231, 76, 60],  # Red
    "warning": [241, 196, 15],  # Yellow
    "info": [52, 152, 219],  # Light Blue
    "background": [22, 22, 24],  # Nearly Black
    "card": [32, 32, 36],  # Dark Gray
    "text": [240, 240, 240],  # Nearly White
    "text_secondary": [180, 180, 180],  # Light Gray
    "border": [60, 60, 70],  # Medium Gray
    "highlight": [46, 134, 193, 50],  # Semi-transparent Blue
}

# Font sizes
FONT_SIZES = {
    "header": 24,
    "title": 18,
    "subtitle": 16,
    "body": 14,
    "small": 12,
    "tiny": 10,
}

# Spacing values
SPACING = {
    "xs": 2,
    "sm": 4,
    "md": 8,
    "lg": 16,
    "xl": 24,
}

# UI Animation settings
ANIMATIONS = {
    "fade_in_ms": 200,
    "slide_ms": 300,
    "expand_ms": 250,
}

# Premium UI style - rounded corners, shadows, etc.
STYLE = {
    "corner_radius": 5,
    "shadow_offset": [3, 3],
    "shadow_size": 5,
    "button_padding": [8, 4],
    "input_padding": [6, 4],
    "border_width": 1,
}

# Field type mappings
FIELD_TYPES = {
    "str": "string",
    "int": "int",
    "float": "float",
    "bool": "bool",
    "list": "array",
    "dict": "object",
    "Dict": "object",
    "List": "array",
    "Any": "any",
    "Optional": "optional"
}