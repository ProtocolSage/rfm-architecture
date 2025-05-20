"""Core self-healing error recovery components."""
from __future__ import annotations

import logging
import inspect
import traceback
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Callable, Type, Union, Set, Tuple

# Set up logger
logger = logging.getLogger(__name__)

class RecoveryActionType(Enum):
    """Types of recovery actions."""
    PARAMETER_ADJUST = "parameter_adjust"
    ALGORITHM_SWITCH = "algorithm_switch"
    RESOURCE_REDUCTION = "resource_reduction"
    CONFIGURATION_FIX = "configuration_fix"
    RESTART = "restart"
    USER_ACTION = "user_action"
    OTHER = "other"

@dataclass
class RecoveryAction:
    """
    Action to recover from an error.
    
    Attributes:
        action_type: Type of recovery action
        description: Human-readable description of the action
        changes: Dictionary of parameter changes
        confidence: Confidence in the recovery action (0-1)
        code: Optional code to execute for recovery
    """
    action_type: RecoveryActionType
    description: str
    changes: Dict[str, Any]
    confidence: float = 0.5
    code: Optional[str] = None
    
    def apply(self, current_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply the recovery action to the current parameters.
        
        Args:
            current_params: Current parameters
            
        Returns:
            Updated parameters
        """
        # Create a copy of the current parameters
        new_params = current_params.copy()
        
        # Apply changes
        for param, value in self.changes.items():
            # Handle nested parameters with dot notation
            if "." in param:
                parts = param.split(".")
                target = new_params
                for part in parts[:-1]:
                    if part not in target:
                        target[part] = {}
                    target = target[part]
                target[parts[-1]] = value
            else:
                new_params[param] = value
        
        return new_params

@dataclass
class RecoveryResult:
    """
    Result of an error recovery attempt.
    
    Attributes:
        success: Whether the recovery was successful
        action: Recovery action that was applied
        original_error: Original error that was recovered from
        new_params: New parameters after recovery
        user_message: Message to display to the user
    """
    success: bool
    action: Optional[RecoveryAction] = None
    original_error: Optional[Exception] = None
    new_params: Optional[Dict[str, Any]] = None
    user_message: Optional[str] = None

class HealingStrategy(ABC):
    """
    Base class for error healing strategies.
    
    A healing strategy is responsible for:
    1. Determining if it can handle a specific error
    2. Diagnosing the error and its cause
    3. Providing recovery actions to fix the error
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the strategy name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Get the strategy description."""
        pass
    
    @property
    @abstractmethod
    def handled_errors(self) -> List[Type[Exception]]:
        """Get the types of errors this strategy can handle."""
        pass
    
    @abstractmethod
    def can_handle(self, error: Exception, context: Dict[str, Any]) -> bool:
        """
        Determine if this strategy can handle the error.
        
        Args:
            error: Error to handle
            context: Context information
            
        Returns:
            True if the strategy can handle the error
        """
        pass
    
    @abstractmethod
    def diagnose(self, error: Exception, context: Dict[str, Any]) -> str:
        """
        Diagnose the error.
        
        Args:
            error: Error to diagnose
            context: Context information
            
        Returns:
            Human-readable diagnosis of the error
        """
        pass
    
    @abstractmethod
    def suggest_actions(self, error: Exception, context: Dict[str, Any]) -> List[RecoveryAction]:
        """
        Suggest recovery actions for the error.
        
        Args:
            error: Error to recover from
            context: Context information
            
        Returns:
            List of suggested recovery actions
        """
        pass
    
    def get_best_action(self, error: Exception, context: Dict[str, Any]) -> Optional[RecoveryAction]:
        """
        Get the best recovery action for the error.
        
        Args:
            error: Error to recover from
            context: Context information
            
        Returns:
            Best recovery action, or None if no action is available
        """
        actions = self.suggest_actions(error, context)
        if not actions:
            return None
        
        # Return the action with the highest confidence
        return max(actions, key=lambda a: a.confidence)

class ErrorHealer:
    """
    Error healer that orchestrates multiple healing strategies.
    
    The error healer is responsible for:
    1. Finding the right strategy for an error
    2. Applying recovery actions
    3. Monitoring the success of recovery attempts
    4. Learning from successful recoveries
    """
    
    def __init__(self, strategies: List[HealingStrategy] = None):
        """
        Initialize the error healer.
        
        Args:
            strategies: List of healing strategies to use
        """
        self.strategies = strategies or []
        self.recovery_history = []
        
    def add_strategy(self, strategy: HealingStrategy):
        """
        Add a healing strategy.
        
        Args:
            strategy: Strategy to add
        """
        self.strategies.append(strategy)
        logger.debug(f"Added healing strategy: {strategy.name}")
    
    def can_heal(self, error: Exception, context: Dict[str, Any]) -> bool:
        """
        Determine if the error can be healed.
        
        Args:
            error: Error to heal
            context: Context information
            
        Returns:
            True if the error can be healed
        """
        # Find strategies that can handle the error
        applicable_strategies = [
            s for s in self.strategies
            if s.can_handle(error, context)
        ]
        
        return len(applicable_strategies) > 0
    
    def get_applicable_strategies(self, error: Exception, context: Dict[str, Any]) -> List[HealingStrategy]:
        """
        Get strategies that can handle the error.
        
        Args:
            error: Error to heal
            context: Context information
            
        Returns:
            List of applicable strategies
        """
        return [
            s for s in self.strategies
            if s.can_handle(error, context)
        ]
    
    def heal(self, error: Exception, context: Dict[str, Any]) -> RecoveryResult:
        """
        Attempt to heal an error.
        
        Args:
            error: Error to heal
            context: Context information
            
        Returns:
            Recovery result
        """
        # Find applicable strategies
        applicable_strategies = self.get_applicable_strategies(error, context)
        if not applicable_strategies:
            logger.warning(f"No healing strategies available for error: {error}")
            return RecoveryResult(
                success=False,
                original_error=error,
                user_message="No automatic recovery available for this error."
            )
        
        # Diagnose the error with all applicable strategies
        diagnoses = [
            (s.name, s.diagnose(error, context))
            for s in applicable_strategies
        ]
        
        # Get best action from each strategy
        actions = []
        for strategy in applicable_strategies:
            action = strategy.get_best_action(error, context)
            if action:
                actions.append((strategy.name, action))
        
        if not actions:
            logger.warning(f"No recovery actions available for error: {error}")
            return RecoveryResult(
                success=False,
                original_error=error,
                user_message="Diagnosis: " + "; ".join(f"{name}: {diag}" for name, diag in diagnoses)
            )
        
        # Get the action with the highest confidence
        strategy_name, best_action = max(actions, key=lambda a: a[1].confidence)
        
        # Apply the action
        try:
            current_params = context.get("params", {})
            new_params = best_action.apply(current_params)
            
            # Create user message
            user_message = (
                f"Error detected: {type(error).__name__}: {str(error)}\n\n"
                f"Diagnosis: {'; '.join(f'{name}: {diag}' for name, diag in diagnoses)}\n\n"
                f"Recovery action: {best_action.description}\n\n"
                f"Parameters adjusted automatically."
            )
            
            # Record the successful recovery
            self.recovery_history.append({
                "error": type(error).__name__,
                "message": str(error),
                "strategy": strategy_name,
                "action": best_action.description,
                "original_params": current_params,
                "new_params": new_params,
                "success": True
            })
            
            return RecoveryResult(
                success=True,
                action=best_action,
                original_error=error,
                new_params=new_params,
                user_message=user_message
            )
        except Exception as e:
            logger.error(f"Error applying recovery action: {e}")
            
            # Record the failed recovery
            self.recovery_history.append({
                "error": type(error).__name__,
                "message": str(error),
                "strategy": strategy_name,
                "action": best_action.description,
                "recovery_error": str(e),
                "success": False
            })
            
            return RecoveryResult(
                success=False,
                action=best_action,
                original_error=error,
                user_message=f"Error recovery failed: {e}"
            )
    
    def get_recovery_statistics(self) -> Dict[str, Any]:
        """
        Get statistics on recovery attempts.
        
        Returns:
            Dictionary with recovery statistics
        """
        total_attempts = len(self.recovery_history)
        if total_attempts == 0:
            return {
                "total_attempts": 0,
                "success_rate": 0,
                "strategy_usage": {},
                "error_types": {}
            }
        
        successful_attempts = sum(1 for r in self.recovery_history if r.get("success", False))
        
        # Count strategy usage
        strategy_usage = {}
        for r in self.recovery_history:
            strategy = r.get("strategy", "unknown")
            strategy_usage[strategy] = strategy_usage.get(strategy, 0) + 1
        
        # Count error types
        error_types = {}
        for r in self.recovery_history:
            error_type = r.get("error", "unknown")
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "success_rate": successful_attempts / total_attempts,
            "strategy_usage": strategy_usage,
            "error_types": error_types
        }