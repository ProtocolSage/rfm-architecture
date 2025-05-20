"""Command bus implementation for RFM Architecture UI."""
from __future__ import annotations

import uuid
import time
import logging
import threading
import asyncio
from typing import Dict, Any, Optional, List, Callable, Union, Type, Set

from .command import Command, CommandResult, CommandStatus

# Set up logger
logger = logging.getLogger(__name__)

class CommandBus:
    """
    Command bus for executing and routing commands.
    
    The command bus is responsible for:
    1. Executing commands
    2. Tracking command history
    3. Providing undo/redo functionality
    4. Notifying subscribers of command execution
    """
    
    def __init__(self):
        """Initialize the command bus."""
        self.history = None
        self.subscribers = set()
        self.executing = False
        self.lock = threading.RLock()
        self._async_lock = asyncio.Lock()
    
    def set_history(self, history):
        """Set the command history."""
        self.history = history
    
    def subscribe(self, callback: Callable[[Command, CommandResult], None]):
        """
        Subscribe to command execution events.
        
        Args:
            callback: Function to call when a command is executed
        """
        self.subscribers.add(callback)
    
    def unsubscribe(self, callback: Callable[[Command, CommandResult], None]):
        """
        Unsubscribe from command execution events.
        
        Args:
            callback: Function to unsubscribe
        """
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    def execute(self, command: Command) -> CommandResult:
        """
        Execute a command.
        
        Args:
            command: Command to execute
            
        Returns:
            Result of the command execution
        """
        with self.lock:
            # Generate ID if not present
            if command.id is None:
                command.id = str(uuid.uuid4())
            
            # Check if we're already executing
            if self.executing:
                logger.warning(f"Command {command.name} skipped, bus is already executing")
                return CommandResult(
                    status=CommandStatus.FAILED,
                    error=RuntimeError("Command bus is already executing")
                )
            
            self.executing = True
            
            try:
                # Execute the command
                command.mark_executed()
                result = command.execute()
                command.result = result
                
                # Add to history if successful
                if result.success and self.history:
                    self.history.add(command)
                
                # Notify subscribers
                self._notify_subscribers(command, result)
                
                return result
            except Exception as e:
                logger.error(f"Error executing command {command.name}: {e}")
                result = CommandResult.failure(e)
                command.result = result
                return result
            finally:
                self.executing = False
    
    async def execute_async(self, command: Command) -> CommandResult:
        """
        Execute a command asynchronously.
        
        Args:
            command: Command to execute
            
        Returns:
            Result of the command execution
        """
        async with self._async_lock:
            # Generate ID if not present
            if command.id is None:
                command.id = str(uuid.uuid4())
            
            # Execute the command in a thread pool
            return await asyncio.to_thread(self.execute, command)
    
    def undo(self) -> Optional[CommandResult]:
        """
        Undo the last command.
        
        Returns:
            Result of the undo operation, or None if no commands to undo
        """
        if not self.history:
            logger.warning("Cannot undo: no history available")
            return None
        
        with self.lock:
            if self.executing:
                logger.warning("Cannot undo: bus is already executing")
                return CommandResult(
                    status=CommandStatus.FAILED,
                    error=RuntimeError("Command bus is already executing")
                )
            
            self.executing = True
            
            try:
                # Get the last command
                command = self.history.get_last_executed()
                if not command:
                    logger.warning("No commands to undo")
                    return None
                
                # Check if command can be reverted
                if not command.can_revert:
                    logger.warning(f"Command {command.name} cannot be reverted")
                    return CommandResult(
                        status=CommandStatus.FAILED,
                        error=RuntimeError(f"Command {command.name} cannot be reverted")
                    )
                
                # Revert the command
                command.mark_reverted()
                result = command.revert()
                
                # Update history
                if result.success and self.history:
                    self.history.mark_reverted(command.id)
                
                # Notify subscribers
                self._notify_subscribers(command, result, is_undo=True)
                
                return result
            except Exception as e:
                logger.error(f"Error reverting command: {e}")
                return CommandResult.failure(e)
            finally:
                self.executing = False
    
    def redo(self) -> Optional[CommandResult]:
        """
        Redo the last undone command.
        
        Returns:
            Result of the redo operation, or None if no commands to redo
        """
        if not self.history:
            logger.warning("Cannot redo: no history available")
            return None
        
        with self.lock:
            if self.executing:
                logger.warning("Cannot redo: bus is already executing")
                return CommandResult(
                    status=CommandStatus.FAILED,
                    error=RuntimeError("Command bus is already executing")
                )
            
            self.executing = True
            
            try:
                # Get the last reverted command
                command = self.history.get_last_reverted()
                if not command:
                    logger.warning("No commands to redo")
                    return None
                
                # Re-execute the command
                command.reverted_at = None
                result = command.execute()
                command.mark_executed()
                
                # Update history
                if result.success and self.history:
                    self.history.mark_redone(command.id)
                
                # Notify subscribers
                self._notify_subscribers(command, result, is_redo=True)
                
                return result
            except Exception as e:
                logger.error(f"Error redoing command: {e}")
                return CommandResult.failure(e)
            finally:
                self.executing = False
    
    def _notify_subscribers(self, command: Command, result: CommandResult, 
                          is_undo: bool = False, is_redo: bool = False):
        """
        Notify subscribers of a command execution.
        
        Args:
            command: Command that was executed
            result: Result of the command execution
            is_undo: Whether this is an undo operation
            is_redo: Whether this is a redo operation
        """
        for subscriber in self.subscribers:
            try:
                subscriber(command, result, is_undo, is_redo)
            except Exception as e:
                logger.error(f"Error in command subscriber: {e}")
                
    def can_undo(self) -> bool:
        """Check if there are commands that can be undone."""
        if not self.history:
            return False
        return self.history.can_undo()
    
    def can_redo(self) -> bool:
        """Check if there are commands that can be redone."""
        if not self.history:
            return False
        return self.history.can_redo()
    
    def get_history_summary(self) -> List[Dict[str, Any]]:
        """Get a summary of the command history."""
        if not self.history:
            return []
        return self.history.get_summary()
    
    def clear_history(self):
        """Clear the command history."""
        if self.history:
            self.history.clear()