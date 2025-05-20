"""Command registry for the command bus pattern."""
from __future__ import annotations

import inspect
import logging
from typing import Dict, Any, Optional, List, Callable, Type, Union, Set

from .command import Command

# Set up logger
logger = logging.getLogger(__name__)

class CommandRegistry:
    """
    Registry for command classes.
    
    This registry maps command names to command classes,
    allowing the system to create commands by name.
    """
    
    def __init__(self):
        """Initialize the command registry."""
        self.commands = {}  # name -> command class
        self.command_bus = None
    
    def register(self, command_class: Type[Command], name: Optional[str] = None):
        """
        Register a command class.
        
        Args:
            command_class: Command class to register
            name: Optional name to register the command under
        """
        # Get command name
        if name is None:
            name = command_class.__name__
        
        # Check if command is already registered
        if name in self.commands:
            logger.warning(f"Command {name} already registered, overwriting")
        
        # Register command
        self.commands[name] = command_class
        logger.debug(f"Registered command {name}")
    
    def unregister(self, name: str):
        """
        Unregister a command.
        
        Args:
            name: Name of the command to unregister
        """
        if name in self.commands:
            del self.commands[name]
            logger.debug(f"Unregistered command {name}")
        else:
            logger.warning(f"Cannot unregister: command {name} not found")
    
    def get(self, name: str) -> Optional[Type[Command]]:
        """
        Get a command class by name.
        
        Args:
            name: Name of the command to get
            
        Returns:
            Command class, or None if not found
        """
        return self.commands.get(name)
    
    def create(self, name: str, **kwargs) -> Optional[Command]:
        """
        Create a command instance by name.
        
        Args:
            name: Name of the command to create
            **kwargs: Arguments to pass to the command constructor
            
        Returns:
            Command instance, or None if not found
        """
        command_class = self.get(name)
        if command_class is None:
            logger.warning(f"Cannot create: command {name} not found")
            return None
        
        try:
            return command_class(**kwargs)
        except Exception as e:
            logger.error(f"Error creating command {name}: {e}")
            return None
    
    def execute(self, name: str, **kwargs):
        """
        Create and execute a command by name.
        
        Args:
            name: Name of the command to execute
            **kwargs: Arguments to pass to the command constructor
            
        Returns:
            Result of command execution, or None if command creation failed
        """
        if self.command_bus is None:
            logger.error("Cannot execute: command bus not set")
            return None
        
        command = self.create(name, **kwargs)
        if command is None:
            return None
        
        return self.command_bus.execute(command)
    
    def link(self, command_bus):
        """
        Link the registry to a command bus.
        
        Args:
            command_bus: Command bus to link to
        """
        self.command_bus = command_bus
        logger.debug("Linked command registry to command bus")
    
    def get_available_commands(self) -> List[str]:
        """
        Get list of available command names.
        
        Returns:
            List of registered command names
        """
        return list(self.commands.keys())
    
    def get_command_info(self, name: str) -> Dict[str, Any]:
        """
        Get information about a command.
        
        Args:
            name: Name of the command to get info for
            
        Returns:
            Dictionary with command information
        """
        command_class = self.get(name)
        if command_class is None:
            return {}
        
        # Get command docstring
        docstring = inspect.getdoc(command_class) or ""
        
        # Get parameter info
        signature = inspect.signature(command_class.__init__)
        params = {}
        
        for param_name, param in signature.parameters.items():
            if param_name in ("self", "args", "kwargs"):
                continue
                
            param_info = {
                "name": param_name,
                "required": param.default is inspect.Parameter.empty,
                "default": None if param.default is inspect.Parameter.empty else param.default
            }
            
            # Try to get parameter type
            if param.annotation is not inspect.Parameter.empty:
                param_info["type"] = str(param.annotation)
            
            params[param_name] = param_info
        
        return {
            "name": name,
            "docstring": docstring,
            "parameters": params
        }