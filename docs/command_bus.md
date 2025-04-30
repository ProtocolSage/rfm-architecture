# Command-Bus Pattern for RFM Architecture

## Overview

The Command-Bus pattern implemented in the RFM Architecture provides:

1. Centralized command execution
2. Command history tracking
3. Undo/redo functionality
4. Command batching
5. Command execution monitoring

This pattern enhances the user experience and provides a foundation for complex operations like animation sequencing.

## Architecture

The Command-Bus implementation consists of several key components:

### Command

The `Command` class is the base class for all commands:

```python
class Command(ABC):
    @abstractmethod
    def execute(self) -> CommandResult:
        """Execute the command."""
        pass
    
    @abstractmethod
    def revert(self) -> CommandResult:
        """Revert the command."""
        pass
```

Each command encapsulates:
- Parameters needed for execution
- Execution logic
- Reversion logic (for undo)
- Metadata (ID, timestamps, etc.)

### CommandBus

The `CommandBus` manages command execution and history:

```python
class CommandBus:
    def execute(self, command: Command) -> CommandResult:
        """Execute a command."""
        pass
    
    def undo(self) -> Optional[CommandResult]:
        """Undo the last command."""
        pass
    
    def redo(self) -> Optional[CommandResult]:
        """Redo the last undone command."""
        pass
```

It provides:
- Command execution with error handling
- Command history management
- Undo/redo functionality
- Command subscription for observers

### CommandHistory

The `CommandHistory` class tracks executed commands:

```python
class CommandHistory:
    def add(self, command: Command):
        """Add a command to the history."""
        pass
    
    def get_last_executed(self) -> Optional[Command]:
        """Get the most recently executed command."""
        pass
    
    def get_last_reverted(self) -> Optional[Command]:
        """Get the most recently reverted command."""
        pass
```

It maintains:
- The list of executed commands
- Tracking of reverted commands
- Command usage statistics

### CommandRegistry

The `CommandRegistry` provides a central registry for command classes:

```python
class CommandRegistry:
    def register(self, command_class: Type[Command], name: Optional[str] = None):
        """Register a command class."""
        pass
    
    def create(self, name: str, **kwargs) -> Optional[Command]:
        """Create a command instance by name."""
        pass
    
    def execute(self, name: str, **kwargs):
        """Create and execute a command by name."""
        pass
```

It enables:
- Command registration by name
- Command instantiation by name
- Command lookup by error type

## Command Types

The framework includes several built-in command types:

### ParameterCommand

A base class for commands that modify parameters:

```python
class ParameterCommand(Command):
    def __init__(self, param_name: str, new_value: Any, old_value: Any = None, **kwargs):
        """Initialize the parameter command."""
        pass
    
    @abstractmethod
    def apply_value(self, value: Any) -> CommandResult:
        """Apply a value to the parameter."""
        pass
```

### BatchCommand

A command that executes multiple commands as a single unit:

```python
class BatchCommand(Command):
    def __init__(self, commands: List[Command], **kwargs):
        """Initialize the batch command."""
        pass
```

This enables:
- Grouping related commands
- Atomic execution (all succeed or all fail)
- Single undo for multiple changes

## Usage Examples

### Basic Command Execution

```python
# Create and execute a command
from ui.rfm_ui.command_bus import get_command_bus
from my_commands import SetZoomCommand

# Create command
command = SetZoomCommand(new_value=2.0, old_value=1.0)

# Execute command
result = get_command_bus().execute(command)

# Check result
if result.success:
    print("Command executed successfully")
else:
    print(f"Command failed: {result.error}")
```

### Using the Command Registry

```python
# Execute a command by name
from ui.rfm_ui.command_bus import get_command_registry

# Execute command
result = get_command_registry().execute("set_zoom", new_value=2.0, old_value=1.0)
```

### Undo and Redo

```python
# Undo and redo commands
from ui.rfm_ui.command_bus import get_command_bus

# Undo last command
result = get_command_bus().undo()
if result and result.success:
    print("Command undone successfully")

# Redo last undone command
result = get_command_bus().redo()
if result and result.success:
    print("Command redone successfully")
```

### Batch Commands

```python
# Execute multiple commands as a single unit
from ui.rfm_ui.command_bus import get_command_bus
from ui.rfm_ui.command_bus.command import BatchCommand
from my_commands import SetZoomCommand, SetCenterCommand

# Create commands
zoom_command = SetZoomCommand(new_value=2.0, old_value=1.0)
center_command = SetCenterCommand(new_value=(-0.5, 0.0), old_value=(0.0, 0.0))

# Create batch command
batch = BatchCommand([zoom_command, center_command])

# Execute batch
result = get_command_bus().execute(batch)
```

### Command Decorators

```python
# Register a command class
from ui.rfm_ui.command_bus.decorators import command
from ui.rfm_ui.command_bus.command import Command, CommandResult

@command(name="set_zoom")
class SetZoomCommand(Command):
    def __init__(self, new_value, old_value=None, **kwargs):
        super().__init__(**kwargs)
        self.new_value = new_value
        self.old_value = old_value
    
    def execute(self) -> CommandResult:
        # Execute logic
        pass
    
    def revert(self) -> CommandResult:
        # Revert logic
        pass
```

## Benefits of the Command-Bus Pattern

1. **Encapsulation**: Each command encapsulates a single operation with its parameters
2. **History**: Tracks all operations for undo/redo and logging
3. **Testability**: Commands can be tested in isolation
4. **Extensibility**: New commands can be added without modifying existing code
5. **Centralization**: All operations go through a single bus, enabling global monitoring
6. **Atomicity**: Batch commands ensure all-or-nothing execution

## Integration with UI

The Command-Bus pattern integrates with the UI through:

1. **UI Events**: UI events trigger command creation and execution
2. **Command Results**: UI components update based on command results
3. **Undo/Redo Buttons**: Connect directly to the command bus
4. **Command History Display**: Shows past operations

This integration provides a robust foundation for the entire application, enabling more complex features like animation sequencing and parameter presets.

## Future Enhancements

Planned enhancements to the Command-Bus system include:

1. **Command Pipelines**: Chaining commands with conditional execution
2. **Command Scheduling**: Delayed and recurring command execution
3. **Remote Command Execution**: Distributed command execution
4. **Command Authorization**: Access control for commands
5. **Command Replay**: Replay sequences of commands for demonstrations