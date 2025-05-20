#!/usr/bin/env python
"""
Database initialization script for RFM-Architecture.

This script initializes the PostgreSQL database for the RFM project.
"""
import argparse
import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from rfm.database.connection import init_db, close_db_connections
from rfm.database.migrations.manager import upgrade

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="RFM Database Initialization")
    
    parser.add_argument(
        "--host", help="Database host", default=os.environ.get("RFM_DB_HOST", "localhost")
    )
    parser.add_argument(
        "--port", help="Database port", default=os.environ.get("RFM_DB_PORT", "5432")
    )
    parser.add_argument(
        "--name", help="Database name", default=os.environ.get("RFM_DB_NAME", "rfm")
    )
    parser.add_argument(
        "--user", help="Database user", default=os.environ.get("RFM_DB_USER", "postgres")
    )
    parser.add_argument(
        "--password", help="Database password", default=os.environ.get("RFM_DB_PASS", "postgres")
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Set environment variables for database connection
    os.environ["RFM_DB_HOST"] = args.host
    os.environ["RFM_DB_PORT"] = args.port
    os.environ["RFM_DB_NAME"] = args.name
    os.environ["RFM_DB_USER"] = args.user
    os.environ["RFM_DB_PASS"] = args.password
    
    logger.info(f"Initializing database {args.name} on {args.host}:{args.port}")
    
    try:
        # Initialize database connection and create tables
        if init_db():
            logger.info("Database connection established")
            
            # Run migrations
            upgrade()
            logger.info("Database schema initialized")
            
            return 0
        else:
            logger.error("Failed to initialize database")
            return 1
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return 1
    finally:
        close_db_connections()


if __name__ == "__main__":
    sys.exit(main())