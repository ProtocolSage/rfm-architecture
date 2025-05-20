"""
Authentication module for WebSocket server.

This module provides JWT-based authentication for the WebSocket server.
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List, Set, Union

# Use PyJWT for JWT handling
try:
    import jwt
except ImportError:
    raise ImportError("PyJWT is required for JWT authentication. Install with: pip install PyJWT")

from .logging_config import (
    get_logger, LogLevel, LogCategory
)


# Configure logger
logger = get_logger(__name__)


class AuthError(Exception):
    """Authentication error."""
    pass


class TokenExpiredError(AuthError):
    """JWT token has expired."""
    pass


class InvalidTokenError(AuthError):
    """JWT token is invalid."""
    pass


class MissingClaimError(AuthError):
    """Required JWT claim is missing."""
    pass


class JWTAuthenticator:
    """JWT-based authenticator for WebSocket connections."""
    
    def __init__(self, 
                secret_key: Optional[str] = None,
                algorithm: str = "HS256",
                token_expiry: int = 3600,  # 1 hour
                refresh_expiry: int = 86400,  # 24 hours
                audience: Optional[str] = None,
                issuer: Optional[str] = None,
                required_claims: Optional[List[str]] = None,
                env_secret_key: str = "JWT_SECRET_KEY"):
        """
        Initialize the JWT authenticator.
        
        Args:
            secret_key: Secret key for JWT signing
            algorithm: JWT algorithm to use
            token_expiry: Access token expiry time in seconds
            refresh_expiry: Refresh token expiry time in seconds
            audience: Expected audience claim
            issuer: Expected issuer claim
            required_claims: List of required claims
            env_secret_key: Environment variable name for secret key
        """
        # Get secret key from environment or parameter
        self.secret_key = secret_key or os.environ.get(env_secret_key)
        if not self.secret_key:
            raise ValueError(
                f"JWT secret key must be provided either as a parameter or in environment variable {env_secret_key}"
            )
            
        self.algorithm = algorithm
        self.token_expiry = token_expiry
        self.refresh_expiry = refresh_expiry
        self.audience = audience
        self.issuer = issuer
        self.required_claims = required_claims or ["sub", "exp"]
        
        logger.structured_log(
            LogLevel.INFO,
            "JWT authenticator initialized",
            LogCategory.SECURITY,
            component="jwt_auth",
            context={
                "algorithm": algorithm,
                "token_expiry": token_expiry,
                "audience": audience,
                "issuer": issuer
            }
        )
    
    def generate_token(self, 
                      user_id: str, 
                      additional_claims: Optional[Dict[str, Any]] = None, 
                      token_type: str = "access") -> str:
        """
        Generate a JWT token.
        
        Args:
            user_id: User identifier
            additional_claims: Additional JWT claims
            token_type: Token type (access or refresh)
            
        Returns:
            JWT token string
        """
        expiry = self.refresh_expiry if token_type == "refresh" else self.token_expiry
        now = int(time.time())
        
        # Base claims
        claims = {
            "sub": user_id,
            "iat": now,
            "exp": now + expiry,
            "type": token_type
        }
        
        # Add audience if provided
        if self.audience:
            claims["aud"] = self.audience
            
        # Add issuer if provided
        if self.issuer:
            claims["iss"] = self.issuer
            
        # Add additional claims
        if additional_claims:
            claims.update(additional_claims)
            
        # Generate token
        token = jwt.encode(claims, self.secret_key, algorithm=self.algorithm)
        
        logger.structured_log(
            LogLevel.DEBUG,
            f"Generated {token_type} token",
            LogCategory.SECURITY,
            component="jwt_auth",
            context={
                "user_id": user_id,
                "expiry": now + expiry
            }
        )
        
        return token
    
    def verify_token(self, token: str, verify_exp: bool = True) -> Dict[str, Any]:
        """
        Verify a JWT token.
        
        Args:
            token: JWT token string
            verify_exp: Whether to verify token expiration
            
        Returns:
            JWT claims dictionary
            
        Raises:
            TokenExpiredError: If token has expired
            InvalidTokenError: If token is invalid
            MissingClaimError: If required claim is missing
        """
        try:
            # Decode and verify token
            options = {"verify_exp": verify_exp}
            claims = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                options=options,
                audience=self.audience,
                issuer=self.issuer
            )
            
            # Check required claims
            for claim in self.required_claims:
                if claim not in claims:
                    logger.structured_log(
                        LogLevel.WARNING,
                        f"Missing required claim: {claim}",
                        LogCategory.SECURITY,
                        component="jwt_auth",
                        context={"token": token[:10] + "..."}
                    )
                    raise MissingClaimError(f"Missing required claim: {claim}")
                    
            logger.structured_log(
                LogLevel.DEBUG,
                "Token verified successfully",
                LogCategory.SECURITY,
                component="jwt_auth",
                context={
                    "user_id": claims.get("sub"),
                    "token_type": claims.get("type", "access")
                }
            )
                
            return claims
            
        except jwt.ExpiredSignatureError:
            logger.structured_log(
                LogLevel.WARNING,
                "Token has expired",
                LogCategory.SECURITY,
                component="jwt_auth",
                context={"token": token[:10] + "..."}
            )
            raise TokenExpiredError("Token has expired")
            
        except jwt.InvalidTokenError as e:
            logger.structured_log(
                LogLevel.WARNING,
                f"Invalid token: {str(e)}",
                LogCategory.SECURITY,
                component="jwt_auth",
                context={"token": token[:10] + "..."}
            )
            raise InvalidTokenError(f"Invalid token: {str(e)}")
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """
        Refresh an access token using a refresh token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New access token
            
        Raises:
            TokenExpiredError: If refresh token has expired
            InvalidTokenError: If refresh token is invalid
            AuthError: If refresh token is not a refresh token
        """
        # Verify refresh token
        claims = self.verify_token(refresh_token)
        
        # Check token type
        if claims.get("type") != "refresh":
            logger.structured_log(
                LogLevel.WARNING,
                "Not a refresh token",
                LogCategory.SECURITY,
                component="jwt_auth",
                context={"token": refresh_token[:10] + "..."}
            )
            raise AuthError("Not a refresh token")
            
        # Generate new access token
        user_id = claims["sub"]
        additional_claims = {k: v for k, v in claims.items() 
                            if k not in ["sub", "iat", "exp", "type"]}
        
        return self.generate_token(user_id, additional_claims)


# Default global authenticator instance
_authenticator: Optional[JWTAuthenticator] = None


def get_authenticator() -> JWTAuthenticator:
    """
    Get or create the global authenticator instance.
    
    Returns:
        JWTAuthenticator instance
    """
    global _authenticator
    
    if _authenticator is None:
        _authenticator = JWTAuthenticator()
        
    return _authenticator


def set_authenticator(authenticator: JWTAuthenticator) -> None:
    """
    Set the global authenticator instance.
    
    Args:
        authenticator: JWTAuthenticator instance
    """
    global _authenticator
    _authenticator = authenticator


# Utility functions
def generate_token(user_id: str, 
                  additional_claims: Optional[Dict[str, Any]] = None, 
                  token_type: str = "access") -> str:
    """
    Generate a JWT token using the global authenticator.
    
    Args:
        user_id: User identifier
        additional_claims: Additional JWT claims
        token_type: Token type (access or refresh)
        
    Returns:
        JWT token string
    """
    return get_authenticator().generate_token(user_id, additional_claims, token_type)


def verify_token(token: str, verify_exp: bool = True) -> Dict[str, Any]:
    """
    Verify a JWT token using the global authenticator.
    
    Args:
        token: JWT token string
        verify_exp: Whether to verify token expiration
        
    Returns:
        JWT claims dictionary
    """
    return get_authenticator().verify_token(token, verify_exp)


def refresh_access_token(refresh_token: str) -> str:
    """
    Refresh an access token using the global authenticator.
    
    Args:
        refresh_token: Refresh token
        
    Returns:
        New access token
    """
    return get_authenticator().refresh_access_token(refresh_token)