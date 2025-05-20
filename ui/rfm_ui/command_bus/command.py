"""Command class for the command bus pattern."""
from __future__ import annotations

import time
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, TypeVar, Generic, Union, Type

# Set up logger
logger = logging.getLogger(__name__)

class CommandStatus(Enum):
    """Possible statuses for a command."""
    PENDING = "pending"
    EXECUTING = "executing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REVERTED = "reverted"

@dataclass
class CommandResult:
    """Result of a command execution."""
    status: CommandStatus
    data: Dict[str, Any] = None
    error: Optional[Exception] = None
    execution_time: float = 0.0
    
    @property
    def success(self) -> bool:
        """Check if the command succeeded."""
        return self.status == CommandStatus.SUCCEEDED
    
    @property
    def has_error(self) -> bool:
        """Check if the command has an error."""
        return self.error is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert command result to a dictionary."""
        result = {
            "status": self.status.value,
            "execution_time": self.execution_time
        }
        
        if self.data:
            result["data"] = self.data
        
        if self.error:
            result["error"] = {
                "type": type(self.error).__name__,
                "message": str(self.error)
            }
        
        return result
    
    @classmethod
    def success(cls, data: Dict[str, Any] = None, execution_time: float = 0.0) -> CommandResult:
        """Create a success result."""
        return cls(CommandStatus.SUCCEEDED, data, None, execution_time)
    
    @classmethod
    def failure(cls, error: Exception, data: Dict[str, Any] = None, execution_time: float = 0.0) -> CommandResult:
        """Create a failure result."""
        return cls(CommandStatus.FAILED, data, error, execution_time)

class Command(ABC):
    """Base class for all commands."""
    
    def __init__(self, **kwargs):
        """Initialize the command with parameters."""
        self.params = kwargs
        self.id = None  # Will be set by command bus
        self.created_at = time.time()
        self.executed_at = None
        self.reverted_at = None
        self.result = None
    
    @abstractmethod
    def execute(self) -> CommandResult:
        """Execute the command."""
        pass
    
    @abstractmethod
    def revert(self) -> CommandResult:
        """Revert the command."""
        pass
    
    @property
    def name(self) -> str:
        """Get the command name."""
        return self.__class__.__name__
    
    @property
    def is_executed(self) -> bool:
        """Check if the command has been executed."""
        return self.executed_at is not None
    
    @property
    def is_reverted(self) -> bool:
        """Check if the command has been reverted."""
        return self.reverted_at is not None
    
    @property
    def can_revert(self) -> bool:
        """Check if the command can be reverted."""
        return self.is_executed and not self.is_reverted and self.result and self.result.success
    
    def mark_executed(self):
        """Mark the command as executed."""
        self.executed_at = time.time()
    
    def mark_reverted(self):
        """Mark the command as reverted."""
        self.reverted_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert command to a dictionary."""
        result = {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at
        }
        
        if self.params:
            result["params"] = self.params
        
        if self.executed_at:
            result["executed_at"] = self.executed_at
        
        if self.reverted_at:
            result["reverted_at"] = self.reverted_at
        
        if self.result:
            result["result"] = self.result.to_dict()
        
        return result

class ParameterCommand(Command):
    """Base class for commands that modify parameters."""
    
    def __init__(self, param_name: str, new_value: Any, old_value: Any = None, **kwargs):
        """Initialize the parameter command."""
        super().__init__(**kwargs)
        self.param_name = param_name
        self.new_value = new_value
        self.old_value = old_value
        
    @abstractmethod
    def apply_value(self, value: Any) -> CommandResult:
        """Apply a value to the parameter."""
        pass
    
    def execute(self) -> CommandResult:
        """Execute the command by applying the new value."""
        start_time = time.time()
        try:
            result = self.apply_value(self.new_value)
            execution_time = time.time() - start_time
            return CommandResult.success(result, execution_time)
        except Exception as e:
            logger.error(f"Error executing command {self.name}: {e}")
            execution_time = time.time() - start_time
            return CommandResult.failure(e, None, execution_time)
    
    def revert(self) -> CommandResult:
        """Revert the command by applying the old value."""
        if self.old_value is None:
            logger.warning(f"Cannot revert command {self.name}: old value is None")
            return CommandResult.failure(ValueError("Old value is None"))
        
        start_time = time.time()
        try:
            result = self.apply_value(self.old_value)
            execution_time = time.time() - start_time
            return CommandResult.success(result, execution_time)
        except Exception as e:
            logger.error(f"Error reverting command {self.name}: {e}")
            execution_time = time.time() - start_time
            return CommandResult.failure(e, None, execution_time)

class BatchCommand(Command):
    """Command that executes multiple commands as a single unit."""
    
    def __init__(self, commands: List[Command], **kwargs):
        """Initialize the batch command."""
        super().__init__(**kwargs)
        self.commands = commands
        self.results = []
    
    def execute(self) -> CommandResult:
        """Execute all commands in the batch."""
        start_time = time.time()
        self.results = []
        
        try:
            for command in self.commands:
                result = command.execute()
                self.results.append(result)
                
                if not result.success:
                    # Revert already executed commands
                    for i in range(len(self.results) - 1):
                        if self.results[i].success:
                            self.commands[i].revert()
                    
                    execution_time = time.time() - start_time
                    return CommandResult.failure(
                        Exception(f"Batch command failed at {command.name}: {result.error}"),
                        {"results": [r.to_dict() for r in self.results]},
                        execution_time
                    )
            
            execution_time = time.time() - start_time
            return CommandResult.success(
                {"results": [r.to_dict() for r in self.results]},
                execution_time
            )
        except Exception as e:
            logger.error(f"Error executing batch command: {e}")
            execution_time = time.time() - start_time
            return CommandResult.failure(e, None, execution_time)
    
    def revert(self) -> CommandResult:
        """Revert all commands in the batch in reverse order."""
        start_time = time.time()
        revert_results = []
        
        try:
            # Revert in reverse order
            for command in reversed(self.commands):
                if command.can_revert:
                    result = command.revert()
                    revert_results.append(result)
                    
                    if not result.success:
                        execution_time = time.time() - start_time
                        return CommandResult.failure(
                            Exception(f"Batch revert failed at {command.name}: {result.error}"),
                            {"results": [r.to_dict() for r in revert_results]},
                            execution_time
                        )
            
            execution_time = time.time() - start_time
            return CommandResult.success(
                {"results": [r.to_dict() for r in revert_results]},
                execution_time
            )
        except Exception as e:
            logger.error(f"Error reverting batch command: {e}")
            execution_time = time.time() - start_time
            return CommandResult.failure(e, None, execution_time)