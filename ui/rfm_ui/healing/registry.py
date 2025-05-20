"""Registry for self-healing strategies."""
from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List, Type, Set

from .recovery import HealingStrategy, ErrorHealer

# Set up logger
logger = logging.getLogger(__name__)

class HealingRegistry:
    """
    Registry for healing strategies.
    
    This registry:
    1. Keeps track of available healing strategies
    2. Creates error healers with appropriate strategies
    3. Provides lookup of strategies by name or error type
    """
    
    def __init__(self):
        """Initialize the healing registry."""
        self.strategies = {}  # name -> strategy
        self.error_map = {}   # error type -> list of strategy names
    
    def register(self, strategy: HealingStrategy):
        """
        Register a healing strategy.
        
        Args:
            strategy: Strategy to register
        """
        name = strategy.name
        
        # Check if strategy is already registered
        if name in self.strategies:
            logger.warning(f"Strategy {name} already registered, overwriting")
        
        # Register strategy
        self.strategies[name] = strategy
        
        # Update error map
        for error_type in strategy.handled_errors:
            if error_type not in self.error_map:
                self.error_map[error_type] = set()
            self.error_map[error_type].add(name)
            
        logger.debug(f"Registered healing strategy {name}")
    
    def unregister(self, name: str):
        """
        Unregister a healing strategy.
        
        Args:
            name: Name of the strategy to unregister
        """
        if name not in self.strategies:
            logger.warning(f"Cannot unregister: strategy {name} not found")
            return
        
        # Get strategy
        strategy = self.strategies[name]
        
        # Remove from error map
        for error_type in strategy.handled_errors:
            if error_type in self.error_map and name in self.error_map[error_type]:
                self.error_map[error_type].remove(name)
                if not self.error_map[error_type]:
                    del self.error_map[error_type]
        
        # Remove from strategies
        del self.strategies[name]
        
        logger.debug(f"Unregistered healing strategy {name}")
    
    def get(self, name: str) -> Optional[HealingStrategy]:
        """
        Get a healing strategy by name.
        
        Args:
            name: Name of the strategy to get
            
        Returns:
            Strategy instance, or None if not found
        """
        return self.strategies.get(name)
    
    def get_for_error(self, error_type: Type[Exception]) -> List[HealingStrategy]:
        """
        Get healing strategies that can handle an error type.
        
        Args:
            error_type: Type of error to get strategies for
            
        Returns:
            List of strategy instances
        """
        strategy_names = set()
        
        # Check each error type in the hierarchy
        for et in error_type.__mro__:
            if et in self.error_map:
                strategy_names.update(self.error_map[et])
        
        # Get strategies
        return [self.strategies[name] for name in strategy_names if name in self.strategies]
    
    def create_healer(self, error_types: Optional[List[Type[Exception]]] = None) -> ErrorHealer:
        """
        Create an error healer with strategies for specific error types.
        
        Args:
            error_types: Types of errors to handle, or None for all
            
        Returns:
            Error healer instance
        """
        if error_types is None:
            # Use all strategies
            strategies = list(self.strategies.values())
        else:
            # Get strategies for specified error types
            strategy_names = set()
            for et in error_types:
                if et in self.error_map:
                    strategy_names.update(self.error_map[et])
            
            strategies = [self.strategies[name] for name in strategy_names if name in self.strategies]
        
        return ErrorHealer(strategies)
    
    def create_healer_for_all(self) -> ErrorHealer:
        """
        Create an error healer with all registered strategies.
        
        Returns:
            Error healer instance
        """
        return ErrorHealer(list(self.strategies.values()))
    
    def get_strategy_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all registered strategies.
        
        Returns:
            List of strategy information dictionaries
        """
        return [
            {
                "name": strategy.name,
                "description": strategy.description,
                "handled_errors": [et.__name__ for et in strategy.handled_errors]
            }
            for strategy in self.strategies.values()
        ]