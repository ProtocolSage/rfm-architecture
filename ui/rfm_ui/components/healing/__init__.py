"""
Healing module forwarder.

This is a simple module to forward imports from the top-level healing module,
allowing components to import from '..healing' instead of 'rfm_ui.healing'.
"""

# Import from top-level module
from rfm_ui.healing import decorators

# Export the sub-modules
__all__ = ['decorators']
