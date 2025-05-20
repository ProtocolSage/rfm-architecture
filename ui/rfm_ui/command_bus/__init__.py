"""
Command-Bus pattern implementation for RFM Architecture UI.

This package provides a robust command bus implementation
for undo/redo functionality and command history.
"""

from .command import Command, CommandResult
from .command_bus import CommandBus
from .command_history import CommandHistory
from .decorators import command, register_command
from .registry import CommandRegistry

# Create singleton instances
command_registry = CommandRegistry()
command_bus = CommandBus()
command_history = CommandHistory()

# Make the bus aware of history
command_bus.set_history(command_history)

# Link the components
command_registry.link(command_bus)

# Export singletons
def get_command_bus():
    """Get the global command bus instance."""
    return command_bus

def get_command_history():
    """Get the global command history instance."""
    return command_history

def get_command_registry():
    """Get the global command registry instance."""
    return command_registry