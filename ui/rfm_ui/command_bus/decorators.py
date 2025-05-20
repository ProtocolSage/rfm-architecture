"""Decorators for the command bus pattern."""
from __future__ import annotations

import functools
import inspect
import logging
from typing import Dict, Any, Optional, List, Callable, Type, Union

from .command import Command, CommandResult

# Set up logger
logger = logging.getLogger(__name__)

def command(name: Optional[str] = None):
    """
    Decorator to mark a class as a command.
    
    Args:
        name: Optional name for the command
        
    Returns:
        Decorated class
    """
    def decorator(cls):
        # Import here to avoid circular imports
        from ui.rfm_ui.command_bus import get_command_registry
        
        # Register the command
        registry = get_command_registry()
        registry.register(cls, name)
        
        return cls
    
    return decorator

def register_command(cls: Type[Command], name: Optional[str] = None):
    """
    Register a command class.
    
    Args:
        cls: Command class to register
        name: Optional name for the command
    """
    # Import here to avoid circular imports
    from ui.rfm_ui.command_bus import get_command_registry
    
    # Register the command
    registry = get_command_registry()
    registry.register(cls, name)

def create_command_from_function(func: Callable, base_command_class: Type[Command] = Command):
    """
    Create a command class from a function.
    
    Args:
        func: Function to create a command from
        base_command_class: Base command class to inherit from
        
    Returns:
        Command class
    """
    # Create command class
    class FunctionCommand(base_command_class):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.func = func
            self.result_value = None
        
        def execute(self) -> CommandResult:
            try:
                self.result_value = self.func(**self.params)
                return CommandResult.success({"result": self.result_value})
            except Exception as e:
                logger.error(f"Error executing function command: {e}")
                return CommandResult.failure(e)
        
        def revert(self) -> CommandResult:
            # By default, function commands are not revertible
            logger.warning(f"Function command {self.name} is not revertible")
            return CommandResult.failure(
                NotImplementedError("Function command is not revertible")
            )
    
    # Set name and docstring
    FunctionCommand.__name__ = f"{func.__name__}Command"
    FunctionCommand.__doc__ = func.__doc__
    
    return FunctionCommand

def as_command(name: Optional[str] = None, revertible: bool = False):
    """
    Decorator to convert a function to a command.
    
    Args:
        name: Optional name for the command
        revertible: Whether the command is revertible
        
    Returns:
        Decorated function
    """
    def decorator(func):
        # Import here to avoid circular imports
        from ui.rfm_ui.command_bus import get_command_registry, get_command_bus
        
        # Create command class
        command_class = create_command_from_function(func)
        
        # Make revertible if requested
        if revertible:
            reverse_name = f"reverse_{func.__name__}"
            
            # Check if reverse function exists in the same module
            module = inspect.getmodule(func)
            reverse_func = getattr(module, reverse_name, None)
            
            if reverse_func is not None:
                # Override revert method
                def revert(self) -> CommandResult:
                    try:
                        result = reverse_func(**self.params)
                        return CommandResult.success({"result": result})
                    except Exception as e:
                        logger.error(f"Error reverting function command: {e}")
                        return CommandResult.failure(e)
                
                command_class.revert = revert
            else:
                logger.warning(f"No reverse function {reverse_name} found for {func.__name__}")
        
        # Register the command
        registry = get_command_registry()
        cmd_name = name or func.__name__
        registry.register(command_class, cmd_name)
        
        # Create wrapper that executes the command
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Convert args to kwargs
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            all_kwargs = bound_args.arguments
            
            # Execute command via registry
            registry = get_command_registry()
            result = registry.execute(cmd_name, **all_kwargs)
            
            # Return command result
            if result is not None and result.success and "result" in result.data:
                return result.data["result"]
            else:
                return result
        
        return wrapper
    
    return decorator