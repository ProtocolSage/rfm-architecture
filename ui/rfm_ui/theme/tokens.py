"""
Premium theme tokens for RFM Architecture UI.

This module defines the theme tokens (colors, typography, spacing, etc.) used
throughout the application to create a cohesive, premium visual identity.
"""

from typing import Dict, Any, List, Tuple

# Color palette
class Colors:
    """Premium color palette for RFM Architecture UI."""
    
    # Base colors
    DARK_GRAPHITE = (26, 26, 26, 255)  # #1A1A1A
    CARBON = (38, 38, 38, 255)         # #262626
    STONE = (64, 64, 64, 255)          # #404040
    LIGHT_STONE = (96, 96, 96, 255)    # #606060
    
    # Accent colors
    TEAL_ACCENT = (63, 245, 212, 255)  # #3FF5D4
    AMBER_ACCENT = (255, 210, 124, 255)  # #FFD27C
    
    # Teal variations
    TEAL_DARK = (38, 191, 166, 255)    # #26BFA6
    TEAL_LIGHT = (121, 255, 234, 255)  # #79FFEA
    
    # Amber variations
    AMBER_DARK = (230, 175, 77, 255)   # #E6AF4D
    AMBER_LIGHT = (255, 225, 166, 255)  # #FFE1A6
    
    # Utility colors
    WHITE = (255, 255, 255, 255)       # #FFFFFF
    BLACK = (0, 0, 0, 255)             # #000000
    TRANSPARENT = (0, 0, 0, 0)         # Transparent
    
    # Semantic colors
    SUCCESS = (64, 230, 176, 255)      # #40E6B0
    WARNING = (255, 181, 71, 255)      # #FFB547
    ERROR = (255, 95, 107, 255)        # #FF5F6B
    INFO = (79, 193, 255, 255)         # #4FC1FF
    
    # Glow colors (with reduced alpha)
    TEAL_GLOW = (63, 245, 212, 51)     # #3FF5D4 with 20% opacity
    AMBER_GLOW = (255, 210, 124, 51)   # #FFD27C with 20% opacity
    
    # UI component colors
    BACKGROUND = DARK_GRAPHITE
    WINDOW_BG = CARBON
    PANEL_BG = STONE
    CONTROL_BG = STONE
    CONTROL_ACTIVE = LIGHT_STONE
    CONTROL_HOVER = (74, 74, 74, 255)  # #4A4A4A
    
    TEXT_PRIMARY = (230, 230, 230, 255)  # #E6E6E6
    TEXT_SECONDARY = (180, 180, 180, 255)  # #B4B4B4
    TEXT_DISABLED = (128, 128, 128, 255)  # #808080
    
    # Convert (R,G,B,A) to normalized (0-1) values required by DearPyGui
    @staticmethod
    def normalize(color: Tuple[int, int, int, int]) -> Tuple[float, float, float, float]:
        """
        Convert 8-bit color values to normalized 0-1 values.
        
        Args:
            color: Tuple of (R,G,B,A) values in 0-255 range
            
        Returns:
            Tuple of normalized (R,G,B,A) values in 0-1 range
        """
        return (
            color[0] / 255.0,
            color[1] / 255.0,
            color[2] / 255.0,
            color[3] / 255.0
        )
    
    @staticmethod
    def to_hex(color: Tuple[int, int, int, int]) -> str:
        """
        Convert color tuple to hex string.
        
        Args:
            color: Tuple of (R,G,B,A) values in 0-255 range
            
        Returns:
            Hex color string (e.g., "#1A1A1A")
        """
        return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
    
    @staticmethod
    def from_hex(hex_color: str) -> Tuple[int, int, int, int]:
        """
        Convert hex color to tuple.
        
        Args:
            hex_color: Hex color string (e.g., "#1A1A1A")
            
        Returns:
            Tuple of (R,G,B,A) values in 0-255 range
        """
        if hex_color.startswith("#"):
            hex_color = hex_color[1:]
            
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return (r, g, b, 255)
        elif len(hex_color) == 8:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            a = int(hex_color[6:8], 16)
            return (r, g, b, a)
        else:
            raise ValueError(f"Invalid hex color: {hex_color}")


# Typography
class Typography:
    """Typography settings for RFM Architecture UI."""
    
    # Font families
    FONT_PRIMARY = "Inter"
    FONT_SECONDARY = "JetBrains Mono"
    
    # Font sizes
    FONT_SIZE_SMALL = 14
    FONT_SIZE_BASE = 16
    FONT_SIZE_MEDIUM = 18
    FONT_SIZE_LARGE = 20
    FONT_SIZE_XL = 24
    FONT_SIZE_XXL = 32
    
    # Font weights
    FONT_WEIGHT_REGULAR = 400
    FONT_WEIGHT_MEDIUM = 500
    FONT_WEIGHT_SEMIBOLD = 600
    
    # Line heights
    LINE_HEIGHT_TIGHT = 1.2
    LINE_HEIGHT_BASE = 1.45
    LINE_HEIGHT_RELAXED = 1.65
    
    # Letter spacing
    LETTER_SPACING_TIGHT = -0.5
    LETTER_SPACING_BASE = 0
    LETTER_SPACING_WIDE = 1.0


# Spacing and sizing
class Spacing:
    """Spacing and sizing tokens for RFM Architecture UI."""
    
    # Base spacing units
    UNIT = 8  # Base unit (8px)
    
    # Spacing scale
    XXS = UNIT / 2  # 4px
    XS = UNIT  # 8px
    SM = UNIT * 2  # 16px
    MD = UNIT * 3  # 24px
    LG = UNIT * 4  # 32px
    XL = UNIT * 6  # 48px
    XXL = UNIT * 8  # 64px
    
    # Component-specific spacing
    CARD_PADDING = MD
    BUTTON_PADDING_X = MD
    BUTTON_PADDING_Y = XS
    INPUT_PADDING_X = SM
    INPUT_PADDING_Y = XS
    GUTTER = MD  # 24px minimum for grid gutters
    
    # Border radius
    RADIUS_SM = 4
    RADIUS_MD = 8
    RADIUS_LG = 16
    RADIUS_PILL = 999  # For pill-shaped elements


# Shadow and elevation
class Elevation:
    """Shadow and elevation tokens for RFM Architecture UI."""
    
    # Soft shadows (two-layer approach per specs)
    SHADOW_SMALL = [
        (1, 3, 0, 0.03),  # First layer: 1px blur, 3% opacity
        (2, 8, 0, 0.08)   # Second layer: 8px blur, 8% opacity
    ]
    
    SHADOW_MEDIUM = [
        (1, 3, 0, 0.05),  # First layer: 1px blur, 5% opacity
        (4, 12, 0, 0.12)  # Second layer: 12px blur, 12% opacity
    ]
    
    SHADOW_LARGE = [
        (1, 3, 0, 0.07),  # First layer: 1px blur, 7% opacity
        (8, 16, 0, 0.16)  # Second layer: 16px blur, 16% opacity
    ]
    
    # Glow effects
    GLOW_SMALL = (8, 0, 0.15)  # 8px blur, 0px spread, 15% opacity
    GLOW_MEDIUM = (12, 0, 0.2)  # 12px blur, 0px spread, 20% opacity
    GLOW_LARGE = (16, 0, 0.25)  # 16px blur, 0px spread, 25% opacity


# Motion and animation
class Motion:
    """Motion and animation tokens for RFM Architecture UI."""
    
    # Durations
    DURATION_FAST = 100  # ms
    DURATION_BASE = 200  # ms
    DURATION_SLOW = 300  # ms
    
    # Easing curves
    EASE_DEFAULT = (0.22, 1, 0.36, 1)  # cubic-bezier(0.22, 1, 0.36, 1)
    EASE_IN_OUT = (0.4, 0, 0.2, 1)     # cubic-bezier(0.4, 0, 0.2, 1)
    EASE_OUT = (0, 0, 0.2, 1)          # cubic-bezier(0, 0, 0.2, 1)
    EASE_IN = (0.4, 0, 1, 1)           # cubic-bezier(0.4, 0, 1, 1)
    
    # Common animations
    HOVER_TRANSITION = {
        'duration': DURATION_BASE,
        'easing': EASE_DEFAULT
    }
    
    PANEL_TRANSITION = {
        'duration': DURATION_SLOW,
        'easing': EASE_IN_OUT
    }


# Breakpoints
class Breakpoints:
    """Responsive breakpoints for RFM Architecture UI."""
    
    XS = 480
    SM = 768
    MD = 1024
    LG = 1280
    XL = 1440
    XXL = 1920


# Theme tokens as a complete dictionary
def get_theme_tokens() -> Dict[str, Any]:
    """
    Get all theme tokens as a dictionary.
    
    Returns:
        Dictionary of all theme tokens
    """
    return {
        'colors': {
            'background': Colors.BACKGROUND,
            'windowBg': Colors.WINDOW_BG,
            'panelBg': Colors.PANEL_BG,
            'controlBg': Colors.CONTROL_BG,
            'controlActive': Colors.CONTROL_ACTIVE,
            'controlHover': Colors.CONTROL_HOVER,
            'textPrimary': Colors.TEXT_PRIMARY,
            'textSecondary': Colors.TEXT_SECONDARY,
            'textDisabled': Colors.TEXT_DISABLED,
            'tealAccent': Colors.TEAL_ACCENT,
            'amberAccent': Colors.AMBER_ACCENT,
            'tealGlow': Colors.TEAL_GLOW,
            'amberGlow': Colors.AMBER_GLOW,
            'success': Colors.SUCCESS,
            'warning': Colors.WARNING,
            'error': Colors.ERROR,
            'info': Colors.INFO
        },
        'typography': {
            'fontPrimary': Typography.FONT_PRIMARY,
            'fontSecondary': Typography.FONT_SECONDARY,
            'fontSizeSmall': Typography.FONT_SIZE_SMALL,
            'fontSizeBase': Typography.FONT_SIZE_BASE,
            'fontSizeMedium': Typography.FONT_SIZE_MEDIUM,
            'fontSizeLarge': Typography.FONT_SIZE_LARGE,
            'fontSizeXl': Typography.FONT_SIZE_XL,
            'fontSizeXxl': Typography.FONT_SIZE_XXL,
            'fontWeightRegular': Typography.FONT_WEIGHT_REGULAR,
            'fontWeightMedium': Typography.FONT_WEIGHT_MEDIUM,
            'fontWeightSemibold': Typography.FONT_WEIGHT_SEMIBOLD,
            'lineHeightBase': Typography.LINE_HEIGHT_BASE
        },
        'spacing': {
            'unit': Spacing.UNIT,
            'xxs': Spacing.XXS,
            'xs': Spacing.XS,
            'sm': Spacing.SM,
            'md': Spacing.MD,
            'lg': Spacing.LG,
            'xl': Spacing.XL,
            'xxl': Spacing.XXL,
            'gutter': Spacing.GUTTER,
            'cardPadding': Spacing.CARD_PADDING,
            'buttonPaddingX': Spacing.BUTTON_PADDING_X,
            'buttonPaddingY': Spacing.BUTTON_PADDING_Y,
            'radiusSm': Spacing.RADIUS_SM,
            'radiusMd': Spacing.RADIUS_MD,
            'radiusLg': Spacing.RADIUS_LG
        },
        'elevation': {
            'shadowSmall': Elevation.SHADOW_SMALL,
            'shadowMedium': Elevation.SHADOW_MEDIUM,
            'shadowLarge': Elevation.SHADOW_LARGE,
            'glowSmall': Elevation.GLOW_SMALL,
            'glowMedium': Elevation.GLOW_MEDIUM,
            'glowLarge': Elevation.GLOW_LARGE
        },
        'motion': {
            'durationFast': Motion.DURATION_FAST,
            'durationBase': Motion.DURATION_BASE,
            'durationSlow': Motion.DURATION_SLOW,
            'easeDefault': Motion.EASE_DEFAULT,
            'easeInOut': Motion.EASE_IN_OUT,
            'hoverTransition': Motion.HOVER_TRANSITION,
            'panelTransition': Motion.PANEL_TRANSITION
        },
        'breakpoints': {
            'xs': Breakpoints.XS,
            'sm': Breakpoints.SM,
            'md': Breakpoints.MD,
            'lg': Breakpoints.LG,
            'xl': Breakpoints.XL,
            'xxl': Breakpoints.XXL
        }
    }