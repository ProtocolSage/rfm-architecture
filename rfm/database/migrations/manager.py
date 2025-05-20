"""
Database migration manager for RFM-Architecture.

This module provides functionality to manage database schema migrations.
It uses Alembic under the hood with a simplified interface.
"""
import os
import logging
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic import command

from rfm.database.connection import get_connection_string

logger = logging.getLogger(__name__)

# Determine the migrations directory path
MIGRATIONS_DIR = Path(__file__).parent
ALEMBIC_DIR = MIGRATIONS_DIR / "alembic"
ALEMBIC_INI = MIGRATIONS_DIR / "alembic.ini"


def init_migrations():
    """Initialize the migrations directory with Alembic if it doesn't exist."""
    if not ALEMBIC_DIR.exists():
        logger.info("Initializing migrations directory")
        
        # Create alembic.ini
        alembic_ini_content = f"""
[alembic]
script_location = {ALEMBIC_DIR}
prepend_sys_path = .
version_path_separator = os

sqlalchemy.url = {get_connection_string()}

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
        """
        
        with open(ALEMBIC_INI, "w") as f:
            f.write(alembic_ini_content.strip())
        
        # Initialize alembic
        alembic_cfg = Config(ALEMBIC_INI)
        command.init(alembic_cfg, ALEMBIC_DIR)
        
        logger.info("Migrations directory initialized")
        
        # Update env.py to include metadata
        env_py_path = ALEMBIC_DIR / "env.py"
        if env_py_path.exists():
            with open(env_py_path, "r") as f:
                env_py_content = f.read()
            
            # Add import for Base metadata
            if "from rfm.database.schema import Base" not in env_py_content:
                env_py_content = env_py_content.replace(
                    "from alembic import context",
                    "from alembic import context\nfrom rfm.database.schema import Base"
                )
            
            # Update target_metadata
            env_py_content = env_py_content.replace(
                "target_metadata = None",
                "target_metadata = Base.metadata"
            )
            
            with open(env_py_path, "w") as f:
                f.write(env_py_content)
            
            logger.info("Updated env.py with metadata")


def create_migration(message):
    """
    Create a new migration.
    
    Args:
        message: Migration message
    """
    init_migrations()
    
    logger.info(f"Creating new migration: {message}")
    
    alembic_cfg = Config(ALEMBIC_INI)
    command.revision(alembic_cfg, message=message, autogenerate=True)
    
    logger.info("Migration created")


def upgrade(target="head"):
    """
    Upgrade the database to a newer version.
    
    Args:
        target: Target version (default: 'head' - the latest version)
    """
    init_migrations()
    
    logger.info(f"Upgrading database to {target}")
    
    alembic_cfg = Config(ALEMBIC_INI)
    command.upgrade(alembic_cfg, target)
    
    logger.info("Database upgraded")


def downgrade(target):
    """
    Downgrade the database to an older version.
    
    Args:
        target: Target version or offset (e.g., '-1' for one version back)
    """
    init_migrations()
    
    logger.info(f"Downgrading database to {target}")
    
    alembic_cfg = Config(ALEMBIC_INI)
    command.downgrade(alembic_cfg, target)
    
    logger.info("Database downgraded")


def get_current_revision():
    """
    Get current database revision.
    
    Returns:
        Current revision or None if no revision info found
    """
    init_migrations()
    
    engine = create_engine(get_connection_string())
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version")).fetchone()
            return result[0] if result else None
    except Exception as e:
        logger.error(f"Failed to get current revision: {e}")
        return None


def show_migrations():
    """
    Show migration history.
    
    Returns:
        List of migration dictionaries with 'revision' and 'description'
    """
    init_migrations()
    
    alembic_cfg = Config(ALEMBIC_INI)
    
    # This is a bit hacky but it works to get migration history
    versions_dir = ALEMBIC_DIR / "versions"
    if not versions_dir.exists():
        return []
    
    migrations = []
    for file_path in versions_dir.glob("*.py"):
        if file_path.is_file():
            # Extract revision and message from filename
            try:
                revision = file_path.stem.split("_")[0]
                
                # Extract revision message from file content
                description = None
                with open(file_path, "r") as f:
                    for line in f:
                        if "revision = " in line and "down_revision" not in line:
                            revision = line.split("'")[1]
                        if "Revises: " in line:
                            down_revision = line.split(" ")[-1].strip()
                        if line.startswith(""""""""):
                            description = line.strip('"""').strip()
                            break
                
                migrations.append({
                    "revision": revision,
                    "description": description,
                    "file": file_path.name
                })
            except Exception as e:
                logger.error(f"Failed to parse migration file {file_path}: {e}")
    
    # Sort migrations by revision
    migrations.sort(key=lambda x: x["revision"])
    
    return migrations