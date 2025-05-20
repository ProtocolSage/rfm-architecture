"""Decorators for self-healing error recovery."""
from __future__ import annotations

import functools
import logging
import traceback
import sys
from typing import Dict, Any, Optional, List, Callable, Type, Union, Set, Tuple

# Set up logger
logger = logging.getLogger(__name__)

def healing_strategy(name: Optional[str] = None, description: Optional[str] = None):
    """
    Decorator to mark a class as a healing strategy.
    
    Args:
        name: Optional name for the strategy
        description: Optional description for the strategy
        
    Returns:
        Decorated class
    """
    def decorator(cls):
        # Set name if provided
        if name is not None:
            cls.name = property(lambda self: name)
        
        # Set description if provided
        if description is not None:
            cls.description = property(lambda self: description)
        
        # Register the strategy
        # Import here instead of at module level to avoid circular imports
        from ui.rfm_ui.healing import get_healing_registry
        registry = get_healing_registry()
        registry.register(cls())
        
        return cls
    
    return decorator

def with_healing(error_types: Optional[List[Type[Exception]]] = None):
    """
    Decorator to add self-healing to a function.
    
    Args:
        error_types: Types of errors to handle, or None for all
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Import here to avoid circular imports
            from ui.rfm_ui.healing import get_healing_registry
            
            try:
                # Call the original function
                return func(*args, **kwargs)
            except Exception as e:
                # Get parameters from args or kwargs
                params = {}
                if args and isinstance(args[0], dict):
                    params = args[0]
                if "params" in kwargs:
                    params = kwargs["params"]
                
                # Prepare context
                context = {
                    "params": params,
                    "args": args,
                    "kwargs": kwargs,
                    "function": func.__name__,
                    "module": func.__module__,
                    "traceback": traceback.format_exc()
                }
                
                # Get healer
                registry = get_healing_registry()
                healer = registry.create_healer(error_types)
                
                # Check if we can heal the error
                if healer.can_heal(e, context):
                    # Try to heal
                    result = healer.heal(e, context)
                    
                    if result.success and result.new_params:
                        logger.info(f"Successfully healed error in {func.__name__}: {e}")
                        
                        # Call function with new parameters
                        if "params" in kwargs:
                            kwargs["params"] = result.new_params
                            return func(*args, **kwargs)
                        elif args and isinstance(args[0], dict):
                            new_args = list(args)
                            new_args[0] = result.new_params
                            return func(*new_args, **kwargs)
                        else:
                            # Can't figure out how to call function with new parameters
                            logger.warning(f"Cannot call function with new parameters: {func.__name__}")
                            
                            # Just return the new parameters
                            return result.new_params
                    else:
                        # Healing failed
                        logger.warning(f"Failed to heal error in {func.__name__}: {e}")
                        
                        # Reraise the original exception
                        raise
                else:
                    # Can't heal this error
                    logger.info(f"Cannot heal error in {func.__name__}: {e}")
                    
                    # Reraise the original exception
                    raise
        
        return wrapper
    
    return decorator

def try_healing(context_provider: Callable[[], Dict[str, Any]] = None,
               error_types: Optional[List[Type[Exception]]] = None):
    """
    Context manager for self-healing error recovery.
    
    Args:
        context_provider: Function that returns context information
        error_types: Types of errors to handle, or None for all
        
    Returns:
        Context manager
    """
    # Import here to avoid circular imports
    from ui.rfm_ui.healing import get_healing_registry
    
    class HealingContext:
        def __init__(self):
            self.healer = get_healing_registry().create_healer(error_types)
            self.healing_result = None
        
        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_val is None:
                return False
            
            # Get context
            context = {}
            if context_provider:
                try:
                    context = context_provider()
                except Exception as e:
                    logger.error(f"Error getting context: {e}")
            
            # Add traceback
            context["traceback"] = traceback.format_exc()
            
            # Check if we can heal the error
            if self.healer.can_heal(exc_val, context):
                # Try to heal
                self.healing_result = self.healer.heal(exc_val, context)
                
                if self.healing_result.success:
                    logger.info(f"Successfully healed error: {exc_val}")
                    
                    # Suppress the exception
                    return True
                else:
                    # Healing failed
                    logger.warning(f"Failed to heal error: {exc_val}")
                    
                    # Don't suppress the exception
                    return False
            else:
                # Can't heal this error
                logger.info(f"Cannot heal error: {exc_val}")
                
                # Don't suppress the exception
                return False
    
    return HealingContext()