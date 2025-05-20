"""Command history management for the command bus."""
from __future__ import annotations

import time
import json
import logging
import threading
import os
from typing import Dict, Any, Optional, List, Set, Union
from collections import deque

from .command import Command

# Set up logger
logger = logging.getLogger(__name__)

class CommandHistory:
    """
    Command history manager for tracking executed commands.
    
    This class provides:
    1. A record of executed commands
    2. Undo/redo tracking
    3. Persistence of command history
    4. Statistics on command usage
    """
    
    def __init__(self, max_size: int = 100):
        """
        Initialize the command history.
        
        Args:
            max_size: Maximum number of commands to keep in history
        """
        self.max_size = max_size
        self.commands = deque(maxlen=max_size)
        self.executed_set = set()  # IDs of executed commands
        self.reverted_set = set()  # IDs of reverted commands
        self.lock = threading.RLock()
        
        # Statistics
        self.command_counts = {}  # Command name -> count
    
    def add(self, command: Command):
        """
        Add a command to the history.
        
        Args:
            command: Command to add
        """
        with self.lock:
            # Clear any redoable commands when a new command is added
            self._clear_redoable()
            
            # Add to command list
            self.commands.append(command)
            self.executed_set.add(command.id)
            
            # Update statistics
            name = command.name
            self.command_counts[name] = self.command_counts.get(name, 0) + 1
            
            logger.debug(f"Added command {name} to history")
    
    def mark_reverted(self, command_id: str):
        """
        Mark a command as reverted (undone).
        
        Args:
            command_id: ID of the command to mark as reverted
        """
        with self.lock:
            if command_id in self.executed_set:
                self.reverted_set.add(command_id)
                logger.debug(f"Marked command {command_id} as reverted")
            else:
                logger.warning(f"Cannot mark as reverted: command {command_id} not in executed set")
    
    def mark_redone(self, command_id: str):
        """
        Mark a command as redone (redo operation).
        
        Args:
            command_id: ID of the command to mark as redone
        """
        with self.lock:
            if command_id in self.reverted_set:
                self.reverted_set.remove(command_id)
                logger.debug(f"Marked command {command_id} as redone")
            else:
                logger.warning(f"Cannot mark as redone: command {command_id} not in reverted set")
    
    def get_last_executed(self) -> Optional[Command]:
        """
        Get the most recently executed command that hasn't been reverted.
        
        Returns:
            The last executed command, or None if no executed commands
        """
        with self.lock:
            # Check from the end of the list
            for i in range(len(self.commands) - 1, -1, -1):
                cmd = self.commands[i]
                if cmd.id in self.executed_set and cmd.id not in self.reverted_set:
                    return cmd
            return None
    
    def get_last_reverted(self) -> Optional[Command]:
        """
        Get the most recently reverted command.
        
        Returns:
            The last reverted command, or None if no reverted commands
        """
        with self.lock:
            # Check from the end of the list
            for i in range(len(self.commands) - 1, -1, -1):
                cmd = self.commands[i]
                if cmd.id in self.reverted_set:
                    return cmd
            return None
    
    def _clear_redoable(self):
        """Clear any redoable commands (commands after the current position)."""
        with self.lock:
            # Find the last executed command
            last_executed = self.get_last_executed()
            if not last_executed:
                return
            
            # Find its position
            try:
                position = self._find_command_position(last_executed.id)
            except ValueError:
                return
            
            # Remove commands after this position
            if position < len(self.commands) - 1:
                # Get IDs of commands to remove
                to_remove = [cmd.id for cmd in list(self.commands)[position + 1:]]
                
                # Remove from sets
                for cmd_id in to_remove:
                    if cmd_id in self.executed_set:
                        self.executed_set.remove(cmd_id)
                    if cmd_id in self.reverted_set:
                        self.reverted_set.remove(cmd_id)
                
                # Adjust the command list (deque)
                new_commands = list(self.commands)[:position + 1]
                self.commands = deque(new_commands, maxlen=self.max_size)
    
    def _find_command_position(self, command_id: str) -> int:
        """
        Find the position of a command in the history.
        
        Args:
            command_id: ID of the command to find
            
        Returns:
            Position of the command
            
        Raises:
            ValueError: If the command is not in the history
        """
        for i, cmd in enumerate(self.commands):
            if cmd.id == command_id:
                return i
        raise ValueError(f"Command {command_id} not found in history")
    
    def get_all(self) -> List[Command]:
        """
        Get all commands in the history.
        
        Returns:
            List of all commands
        """
        with self.lock:
            return list(self.commands)
    
    def get_executed(self) -> List[Command]:
        """
        Get all executed commands that haven't been reverted.
        
        Returns:
            List of executed commands
        """
        with self.lock:
            return [cmd for cmd in self.commands 
                  if cmd.id in self.executed_set and cmd.id not in self.reverted_set]
    
    def get_reverted(self) -> List[Command]:
        """
        Get all reverted commands.
        
        Returns:
            List of reverted commands
        """
        with self.lock:
            return [cmd for cmd in self.commands if cmd.id in self.reverted_set]
    
    def can_undo(self) -> bool:
        """
        Check if there are commands that can be undone.
        
        Returns:
            True if there are commands that can be undone
        """
        return self.get_last_executed() is not None
    
    def can_redo(self) -> bool:
        """
        Check if there are commands that can be redone.
        
        Returns:
            True if there are commands that can be redone
        """
        return self.get_last_reverted() is not None
    
    def clear(self):
        """Clear the command history."""
        with self.lock:
            self.commands.clear()
            self.executed_set.clear()
            self.reverted_set.clear()
            logger.debug("Command history cleared")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics on command usage.
        
        Returns:
            Dictionary with command usage statistics
        """
        with self.lock:
            stats = {
                "total_commands": len(self.commands),
                "executed_commands": len(self.executed_set),
                "reverted_commands": len(self.reverted_set),
                "command_counts": self.command_counts.copy()
            }
            
            # Sort command counts by usage
            sorted_counts = sorted(
                self.command_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )
            stats["top_commands"] = sorted_counts[:10]
            
            return stats
    
    def get_summary(self) -> List[Dict[str, Any]]:
        """
        Get a summary of the command history.
        
        Returns:
            List of command summary dictionaries
        """
        with self.lock:
            summary = []
            for cmd in self.commands:
                status = "reverted" if cmd.id in self.reverted_set else "executed"
                summary.append({
                    "id": cmd.id,
                    "name": cmd.name,
                    "status": status,
                    "created_at": cmd.created_at,
                    "executed_at": cmd.executed_at,
                    "reverted_at": cmd.reverted_at,
                    "params": cmd.params
                })
            return summary
    
    def save_to_file(self, filename: str):
        """
        Save the command history to a file.
        
        Args:
            filename: Name of the file to save to
        """
        with self.lock:
            try:
                summary = self.get_summary()
                with open(filename, "w") as f:
                    json.dump(summary, f, indent=2)
                logger.info(f"Command history saved to {filename}")
            except Exception as e:
                logger.error(f"Error saving command history: {e}")
    
    def load_from_file(self, filename: str):
        """
        Load the command history from a file.
        
        Args:
            filename: Name of the file to load from
            
        Note:
            This is mainly for informational purposes, as the actual
            command objects cannot be reconstructed from the summary.
        """
        try:
            with open(filename, "r") as f:
                summary = json.load(f)
            
            logger.info(f"Command history loaded from {filename}: {len(summary)} commands")
            return summary
        except Exception as e:
            logger.error(f"Error loading command history: {e}")
            return []