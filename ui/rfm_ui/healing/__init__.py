"""
Self-Healing Error Recovery system for RFM Architecture UI.

This package provides error recovery mechanisms that can:
1. Detect and diagnose common errors
2. Suggest fixes for problematic parameters
3. Automatically apply fixes when possible
4. Provide user-friendly remediation steps
"""

# First, import basic components that don't have dependencies
from .recovery import HealingStrategy, ErrorHealer, RecoveryAction, RecoveryResult, RecoveryActionType

# Create and expose registry functionality first
from .registry import HealingRegistry

# Create singleton registry
healing_registry = HealingRegistry()

# Export functions to access the registry
def get_healing_registry():
    """Get the global healing registry."""
    return healing_registry

def register_strategy(strategy):
    """
    Register a healing strategy.
    
    Args:
        strategy: Strategy to register
    """
    healing_registry.register(strategy)
    return strategy

# Now import strategies
from .strategies import (
    ParameterBoundsStrategy,
    NumericOverflowStrategy,
    MemoryOverflowStrategy,
    InvalidColorStrategy,
    IterationLimitStrategy,
    ZoomDepthStrategy
)

# Finally, import decorator that depends on the registry
from .decorators import healing_strategy, with_healing, try_healing

# Register built-in strategies at the end
register_strategy(ParameterBoundsStrategy())
register_strategy(NumericOverflowStrategy())
register_strategy(MemoryOverflowStrategy())
register_strategy(InvalidColorStrategy())
register_strategy(IterationLimitStrategy())
register_strategy(ZoomDepthStrategy())