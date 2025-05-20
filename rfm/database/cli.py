"""
Command-line interface for database operations.

This module provides CLI commands for database management.
"""
import argparse
import logging
import sys
from pathlib import Path

from rfm.database.connection import init_db, close_db_connections
from rfm.database.migrations.manager import (
    create_migration, upgrade, downgrade, get_current_revision, show_migrations
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="RFM Database Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # init command
    init_parser = subparsers.add_parser("init", help="Initialize the database")
    
    # migration commands
    migration_parser = subparsers.add_parser("migration", help="Migration operations")
    migration_subparsers = migration_parser.add_subparsers(
        dest="migration_command", help="Migration command"
    )
    
    # create migration
    create_parser = migration_subparsers.add_parser("create", help="Create a new migration")
    create_parser.add_argument("message", help="Migration message")
    
    # upgrade
    upgrade_parser = migration_subparsers.add_parser("upgrade", help="Upgrade the database")
    upgrade_parser.add_argument(
        "--target", default="head", help="Target version (default: head)"
    )
    
    # downgrade
    downgrade_parser = migration_subparsers.add_parser("downgrade", help="Downgrade the database")
    downgrade_parser.add_argument("target", help="Target version or offset (e.g., -1)")
    
    # show
    show_parser = migration_subparsers.add_parser("show", help="Show migration history")
    
    return parser.parse_args()


def main():
    """Main CLI entry point."""
    args = parse_args()
    
    if args.command == "init":
        # Initialize the database
        success = init_db()
        if success:
            logger.info("Database initialized successfully")
        else:
            logger.error("Failed to initialize database")
            return 1
    
    elif args.command == "migration":
        if args.migration_command == "create":
            # Create a new migration
            create_migration(args.message)
        
        elif args.migration_command == "upgrade":
            # Upgrade the database
            upgrade(args.target)
        
        elif args.migration_command == "downgrade":
            # Downgrade the database
            downgrade(args.target)
        
        elif args.migration_command == "show":
            # Show migration history
            current = get_current_revision()
            migrations = show_migrations()
            
            if not migrations:
                logger.info("No migrations found")
                return 0
            
            logger.info(f"Current database revision: {current}")
            logger.info("Migration history:")
            
            for migration in migrations:
                marker = "* " if migration["revision"] == current else "  "
                logger.info(f"{marker}{migration['revision']} - {migration['description']}")
        
        else:
            logger.error(f"Unknown migration command: {args.migration_command}")
            return 1
    
    else:
        logger.error(f"Unknown command: {args.command}")
        return 1
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    finally:
        close_db_connections()