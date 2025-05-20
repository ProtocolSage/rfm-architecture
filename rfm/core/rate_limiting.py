"""
Rate limiting module for WebSocket server.

This module provides rate limiting capabilities for the WebSocket server
to protect against abuse and ensure fair resource usage.
"""

import logging
import time
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Set, Tuple, Callable
from dataclasses import dataclass, field
from collections import defaultdict

from .logging_config import (
    get_logger, LogLevel, LogCategory
)


# Configure logger
logger = get_logger(__name__)


class RateLimitScope(str, Enum):
    """Rate limit scope."""
    
    GLOBAL = "global"  # Applies to all clients combined
    CLIENT = "client"  # Applies to each client individually
    USER = "user"      # Applies to each user (across multiple clients)
    IP = "ip"          # Applies to each IP address


@dataclass
class RateLimitRule:
    """Rate limit rule configuration."""
    
    name: str
    requests: int           # Maximum requests allowed
    period: int             # Time period in seconds
    scope: RateLimitScope   # Rule scope
    actions: List[str] = field(default_factory=list)  # Optional list of specific actions to limit
    response_code: int = 429  # Response code for rate limit errors
    response_message: str = "Rate limit exceeded"  # Error message
    
    def __post_init__(self):
        """Validate rule configuration."""
        if self.requests <= 0:
            raise ValueError("Requests must be greater than 0")
        if self.period <= 0:
            raise ValueError("Period must be greater than 0")


@dataclass
class RateLimitContext:
    """Context for rate limit checking."""
    
    client_id: str
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    action: Optional[str] = None
    
    def get_key(self, scope: RateLimitScope) -> str:
        """
        Get cache key for the given scope.
        
        Args:
            scope: Rate limit scope
            
        Returns:
            Cache key string
        """
        if scope == RateLimitScope.GLOBAL:
            return "global"
        elif scope == RateLimitScope.CLIENT:
            return f"client:{self.client_id}"
        elif scope == RateLimitScope.USER:
            return f"user:{self.user_id or 'anonymous'}"
        elif scope == RateLimitScope.IP:
            return f"ip:{self.ip_address or 'unknown'}"
        else:
            return f"client:{self.client_id}"


class RateLimiter:
    """
    Rate limiter for WebSocket connections and actions.
    
    Provides configurable rate limiting with:
    - Multiple scopes (global, client, user, IP)
    - Time-window based tracking
    - Action-specific limits
    """
    
    def __init__(self, rules: Optional[List[RateLimitRule]] = None):
        """
        Initialize the rate limiter.
        
        Args:
            rules: List of rate limit rules
        """
        self.rules = rules or []
        
        # Request tracking
        # Structure: {rule_name: {scope_key: [(timestamp, count)]}}
        self.request_log: Dict[str, Dict[str, List[Tuple[float, int]]]] = defaultdict(lambda: defaultdict(list))
        
        logger.structured_log(
            LogLevel.INFO,
            "Rate limiter initialized",
            LogCategory.SECURITY,
            component="rate_limiter",
            context={"rule_count": len(self.rules)}
        )
        
        # Log rules
        for rule in self.rules:
            logger.structured_log(
                LogLevel.DEBUG,
                f"Rate limit rule: {rule.name}",
                LogCategory.SECURITY,
                component="rate_limiter",
                context={
                    "rule": rule.name,
                    "requests": rule.requests,
                    "period": rule.period,
                    "scope": rule.scope
                }
            )
    
    def add_rule(self, rule: RateLimitRule) -> None:
        """
        Add a rate limit rule.
        
        Args:
            rule: Rate limit rule
        """
        self.rules.append(rule)
        
        logger.structured_log(
            LogLevel.INFO,
            f"Added rate limit rule: {rule.name}",
            LogCategory.SECURITY,
            component="rate_limiter",
            context={
                "rule": rule.name,
                "requests": rule.requests,
                "period": rule.period,
                "scope": rule.scope
            }
        )
    
    def check_rate_limit(self, context: RateLimitContext) -> Tuple[bool, Optional[RateLimitRule]]:
        """
        Check if a request is within rate limits.
        
        Args:
            context: Rate limit context
            
        Returns:
            Tuple of (is_allowed, rule_exceeded). If is_allowed is False, rule_exceeded
            contains the rule that was exceeded.
        """
        now = time.time()
        
        # Check against each rule
        for rule in self.rules:
            # Skip rules for specific actions if they don't match
            if rule.actions and context.action not in rule.actions:
                continue
                
            # Get cache key for this rule and scope
            scope_key = context.get_key(rule.scope)
            
            # Get request log for this rule and scope
            request_log = self.request_log[rule.name][scope_key]
            
            # Clean up old entries
            cutoff_time = now - rule.period
            while request_log and request_log[0][0] < cutoff_time:
                request_log.pop(0)
                
            # Count requests in current period
            total_requests = sum(count for _, count in request_log)
            
            # Check if rate limit exceeded
            if total_requests >= rule.requests:
                logger.structured_log(
                    LogLevel.WARNING,
                    f"Rate limit exceeded: {rule.name}",
                    LogCategory.SECURITY,
                    component="rate_limiter",
                    context={
                        "rule": rule.name,
                        "requests": total_requests,
                        "limit": rule.requests,
                        "scope": rule.scope,
                        "scope_key": scope_key,
                        "client_id": context.client_id,
                        "user_id": context.user_id,
                        "ip_address": context.ip_address,
                        "action": context.action
                    }
                )
                return False, rule
                
        # Request is allowed, record it
        self._record_request(context)
        return True, None
    
    def _record_request(self, context: RateLimitContext) -> None:
        """
        Record a request for rate limiting.
        
        Args:
            context: Rate limit context
        """
        now = time.time()
        
        # Record request for each applicable rule
        for rule in self.rules:
            # Skip rules for specific actions if they don't match
            if rule.actions and context.action not in rule.actions:
                continue
                
            # Get cache key for this rule and scope
            scope_key = context.get_key(rule.scope)
            
            # Get request log for this rule and scope
            request_log = self.request_log[rule.name][scope_key]
            
            # If the last entry is from the same second, increment its count
            if request_log and int(request_log[-1][0]) == int(now):
                request_log[-1] = (request_log[-1][0], request_log[-1][1] + 1)
            else:
                # Otherwise, add a new entry
                request_log.append((now, 1))
    
    def get_remaining_requests(self, context: RateLimitContext) -> Dict[str, int]:
        """
        Get the number of remaining requests for each rule.
        
        Args:
            context: Rate limit context
            
        Returns:
            Dictionary of rule name to remaining requests count
        """
        now = time.time()
        result = {}
        
        # Check each rule
        for rule in self.rules:
            # Skip rules for specific actions if they don't match
            if rule.actions and context.action not in rule.actions:
                continue
                
            # Get cache key for this rule and scope
            scope_key = context.get_key(rule.scope)
            
            # Get request log for this rule and scope
            request_log = self.request_log[rule.name][scope_key]
            
            # Clean up old entries
            cutoff_time = now - rule.period
            cleaned_log = [entry for entry in request_log if entry[0] >= cutoff_time]
            self.request_log[rule.name][scope_key] = cleaned_log
            
            # Count requests in current period
            total_requests = sum(count for _, count in cleaned_log)
            
            # Calculate remaining requests
            remaining = max(0, rule.requests - total_requests)
            result[rule.name] = remaining
            
        return result


# Default global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """
    Get or create the global rate limiter instance.
    
    Returns:
        RateLimiter instance
    """
    global _rate_limiter
    
    if _rate_limiter is None:
        # Create default rate limiter with some common rules
        rules = [
            RateLimitRule(
                name="connection_per_ip",
                requests=5,
                period=60,  # 1 minute
                scope=RateLimitScope.IP
            ),
            RateLimitRule(
                name="operations_per_client",
                requests=10,
                period=60,  # 1 minute
                scope=RateLimitScope.CLIENT,
                actions=["start_render", "start_operation"]
            ),
            RateLimitRule(
                name="global_operations",
                requests=30,
                period=60,  # 1 minute
                scope=RateLimitScope.GLOBAL,
                actions=["start_render", "start_operation"]
            )
        ]
        _rate_limiter = RateLimiter(rules)
        
    return _rate_limiter


def set_rate_limiter(rate_limiter: RateLimiter) -> None:
    """
    Set the global rate limiter instance.
    
    Args:
        rate_limiter: RateLimiter instance
    """
    global _rate_limiter
    _rate_limiter = rate_limiter


# Utility functions
def check_rate_limit(context: RateLimitContext) -> Tuple[bool, Optional[RateLimitRule]]:
    """
    Check if a request is within rate limits using the global rate limiter.
    
    Args:
        context: Rate limit context
        
    Returns:
        Tuple of (is_allowed, rule_exceeded)
    """
    return get_rate_limiter().check_rate_limit(context)


def get_remaining_requests(context: RateLimitContext) -> Dict[str, int]:
    """
    Get the number of remaining requests for each rule using the global rate limiter.
    
    Args:
        context: Rate limit context
        
    Returns:
        Dictionary of rule name to remaining requests count
    """
    return get_rate_limiter().get_remaining_requests(context)