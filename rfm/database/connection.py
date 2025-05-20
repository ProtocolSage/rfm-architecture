"""
Database connection management for RFM-Architecture.

This module provides connection handling, session management,
and initialization functions for the PostgreSQL database.
"""
import os
import logging
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError

from rfm.database.schema import Base

# Configure logging
logger = logging.getLogger(__name__)

# Default connection values that can be overridden with environment variables
DEFAULT_DB_USER = "postgres"
DEFAULT_DB_PASS = "postgres"
DEFAULT_DB_HOST = "localhost"
DEFAULT_DB_PORT = "5432"
DEFAULT_DB_NAME = "rfm"

# SQLAlchemy engine and session
engine = None
SessionFactory = None


def get_connection_string():
    """
    Build database connection string from environment variables or defaults.
    
    Returns:
        str: SQLAlchemy connection string
    """
    db_user = os.environ.get("RFM_DB_USER", DEFAULT_DB_USER)
    db_pass = os.environ.get("RFM_DB_PASS", DEFAULT_DB_PASS)
    db_host = os.environ.get("RFM_DB_HOST", DEFAULT_DB_HOST)
    db_port = os.environ.get("RFM_DB_PORT", DEFAULT_DB_PORT)
    db_name = os.environ.get("RFM_DB_NAME", DEFAULT_DB_NAME)
    
    return f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"


def init_db(connection_string=None):
    """
    Initialize the database connection and create tables if they don't exist.
    
    Args:
        connection_string (str, optional): Override the default connection string. 
                                         Defaults to None.
    
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    global engine, SessionFactory
    
    if connection_string is None:
        connection_string = get_connection_string()
    
    try:
        # Create SQLAlchemy engine with connection pool
        engine = create_engine(
            connection_string,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,  # Recycle connections every 30 minutes
            echo=os.environ.get("RFM_SQL_ECHO", "").lower() == "true"
        )
        
        # Create session factory
        SessionFactory = scoped_session(sessionmaker(bind=engine))
        
        # Create all tables if they don't exist
        Base.metadata.create_all(engine)
        
        logger.info("Database initialized successfully")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Failed to initialize database: {e}")
        return False


@contextmanager
def db_session():
    """
    Context manager for database sessions.
    Automatically handles commit/rollback and session cleanup.
    
    Yields:
        SQLAlchemy Session: Database session for making queries
    
    Example:
        ```
        with db_session() as session:
            user = session.query(User).filter_by(id=1).first()
        ```
    """
    if SessionFactory is None:
        init_db()
        
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def close_db_connections():
    """Close database connections when shutting down the application."""
    if engine is not None:
        engine.dispose()
        logger.info("Database connections closed")


# Initialize database if this module is imported directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()