"""
Testing utilities to support integration tests.

This module provides mock implementations and helpers to allow tests to run
without dependent services like databases.
"""

import os
import sys
import asyncio
import threading
import logging
import numpy as np
import tempfile
from typing import Dict, Any, List, Callable, Tuple, Optional
from unittest.mock import patch, MagicMock

# Configure logging for tests
logging.basicConfig(level=logging.INFO, 
                   format="%(name)s - %(levelname)s - %(message)s")

logger = logging.getLogger("test_utils")

# Define some type constants for testing
class RecoveryActionType:
    PARAMETER_ADJUST = "parameter_adjust"
    RESET = "reset"
    RESOURCE_REDUCTION = "resource_reduction"
    REDUCE_COMPLEXITY = "reduce_complexity"

class RecoveryAction:
    def __init__(self, action_type, description, changes, confidence):
        self.action_type = action_type
        self.description = description
        self.changes = changes
        self.confidence = confidence

class MockRecoveryStrategy:
    """Mock implementation of a recovery strategy for testing."""
    
    def __init__(self, name="mock_strategy", description="Mock strategy for testing", handled_errors=None):
        self.name_value = name
        self.description_value = description
        self.handled_errors_value = handled_errors or [ValueError, OverflowError]
    
    @property
    def name(self):
        return self.name_value
    
    @property
    def description(self):
        return self.description_value
    
    @property
    def handled_errors(self):
        return self.handled_errors_value
    
    def can_handle(self, error, context):
        """Check if this strategy can handle the given error."""
        # For testing, always return True
        return True
    
    def diagnose(self, error, context):
        """Diagnose the error and return a description."""
        if isinstance(error, ValueError) and "zoom" in str(error):
            return "Parameter 'zoom' is outside the valid range"
        elif isinstance(error, OverflowError):
            return "Numerical overflow detected in parameters"
        else:
            return "Unknown error detected"
    
    def suggest_actions(self, error, context):
        """Suggest recovery actions for the error."""
        if isinstance(error, ValueError) and "zoom" in str(error):
            return [
                RecoveryAction(
                    action_type=RecoveryActionType.PARAMETER_ADJUST,
                    description="Adjust zoom to valid range",
                    changes={"zoom": 1.0},
                    confidence=0.9
                )
            ]
        elif isinstance(error, OverflowError):
            return [
                RecoveryAction(
                    action_type=RecoveryActionType.PARAMETER_ADJUST,
                    description="Adjust center coordinates to valid range",
                    changes={"center_x": 0.0, "center_y": 0.0, "zoom": 1.0},
                    confidence=0.8
                )
            ]
        else:
            return [
                RecoveryAction(
                    action_type=RecoveryActionType.PARAMETER_ADJUST,
                    description="Reset parameters to defaults",
                    changes={"zoom": 1.0, "center_x": 0.0, "center_y": 0.0, "max_iter": 100},
                    confidence=0.5
                )
            ]

def setup_test_environment():
    """
    Set up the test environment with mocks and patches.
    
    Returns:
        Tuple of patchers and event loop
    """
    patchers = []
    mocks = {}
    
    # Create mock functions for GPU operations
    def mock_mandelbrot(params, progress_reporter=None):
        """Mock implementation of mandelbrot that accepts progress_reporter."""
        width = params.get("width", 400)
        height = params.get("height", 300)
        result = np.zeros((height, width), dtype=np.int32)
        
        # Simulate progress reporting
        if progress_reporter:
            if hasattr(progress_reporter, 'update'):
                progress_reporter.update(25)
                progress_reporter.update(50)
                progress_reporter.update(75)
                progress_reporter.update(100)
            elif hasattr(progress_reporter, 'report_progress'):
                progress_reporter.report_progress(25)
                progress_reporter.report_progress(50)
                progress_reporter.report_progress(75)
                progress_reporter.report_progress(100)
        
        return result
        
    def mock_julia(params, progress_reporter=None):
        """Mock implementation of julia that accepts progress_reporter."""
        width = params.get("width", 400)
        height = params.get("height", 300)
        result = np.zeros((height, width), dtype=np.int32)
        
        # Simulate progress reporting
        if progress_reporter:
            if hasattr(progress_reporter, 'update'):
                progress_reporter.update(25)
                progress_reporter.update(50)
                progress_reporter.update(75)
                progress_reporter.update(100)
            elif hasattr(progress_reporter, 'report_progress'):
                progress_reporter.report_progress(25)
                progress_reporter.report_progress(50)
                progress_reporter.report_progress(75)
                progress_reporter.report_progress(100)
        
        return result
    
    # Mock the GPU import rather than the functions
    try:
        # Create a mock GPU module with functions
        mock_gpu_module = MagicMock()
        mock_gpu_module.mandelbrot = mock_mandelbrot
        mock_gpu_module.julia = mock_julia
        
        # Patch the GPU module import
        gpu_patcher = patch.dict('sys.modules', {'rfm.gpu_backend': mock_gpu_module})
        patchers.append(gpu_patcher)
        gpu_patcher.start()
        mocks['gpu_backend'] = mock_gpu_module
        
        logger.info("Mocked rfm.gpu_backend successfully")
    except Exception as e:
        logger.warning(f"Failed to mock GPU backend: {e}")
    
    # Mock database connection - only if the module exists
    try:
        import importlib.util
        if importlib.util.find_spec("rfm.database.connection"):
            db_patcher = patch("rfm.database.connection.get_database_engine", return_value=get_mock_db_engine())
            patchers.append(db_patcher)
            mocks["db_engine"] = db_patcher.start()
        else:
            logger.warning("rfm.database.connection module not found, skipping patch")
    except (ImportError, AttributeError) as e:
        logger.warning(f"Could not patch database connection: {e}")
    
    # Handle the AsyncIO event loop
    try:
        # Store the current event loop policy
        old_policy = asyncio.get_event_loop_policy()
        # Create a new event loop for tests
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Return in results
        mocks["event_loop"] = loop
        mocks["old_event_loop_policy"] = old_policy
    except Exception as e:
        logger.warning(f"Could not set up asyncio event loop: {e}")
    
    return patchers, mocks

def teardown_test_environment(patchers):
    """
    Clean up the test environment.
    
    Args:
        patchers: List of patchers to stop
    """
    # Stop all patchers
    for patcher in patchers:
        try:
            patcher.stop()
        except Exception as e:
            logger.warning(f"Error stopping patcher {patcher}: {e}")
    
    # Clean up event loop
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            pending = asyncio.all_tasks(loop)
            for task in pending:
                if not task.done():
                    task.cancel()
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        
        # Close the event loop
        loop.close()
    except Exception as e:
        logger.warning(f"Error cleaning up event loop: {e}")

def get_mock_db_engine():
    """
    Create a mock database engine for testing.
    
    Returns:
        Mock SQLAlchemy engine
    """
    mock_engine = MagicMock()
    mock_engine.connect.return_value = MagicMock()
    mock_engine.dialect.name = "sqlite"
    
    # Mock session creation
    mock_session = MagicMock()
    mock_engine.session = mock_session
    
    return mock_engine

def mock_progress_reporter():
    """
    Create a mock progress reporter for testing.
    
    Returns:
        Mock progress reporter
    """
    mock_reporter = MagicMock()
    mock_reporter.update.return_value = None
    mock_reporter.report_progress.return_value = None
    mock_reporter.report_completed.return_value = None
    mock_reporter.report_failed.return_value = None
    mock_reporter.report_canceled.return_value = None
    mock_reporter.should_cancel.return_value = False
    return mock_reporter

def mock_websocket_server():
    """
    Create a mock WebSocket server for testing.
    
    Returns:
        Mock WebSocket server
    """
    mock_server = MagicMock()
    mock_server.start.return_value = asyncio.Future()
    mock_server.start.return_value.set_result(None)
    mock_server.stop.return_value = asyncio.Future()
    mock_server.stop.return_value.set_result(None)
    mock_server.is_running.return_value = True
    mock_server.get_address.return_value = "ws://localhost:8765"
    return mock_server

def mock_websocket_client():
    """
    Create a mock WebSocket client for testing.
    
    Returns:
        Mock WebSocket client
    """
    mock_client = MagicMock()
    mock_client.start.return_value = True
    mock_client.stop.return_value = True
    mock_client.is_connected.return_value = True
    mock_client.add_callback.return_value = None
    mock_client.remove_callback.return_value = None
    mock_client.send.return_value = asyncio.Future()
    mock_client.send.return_value.set_result(None)
    return mock_client

def load_test_config():
    """
    Load test configuration.
    
    Returns:
        Configuration dictionary for testing
    """
    return {
        "alternative_fractals": {
            "julia_douady_rabbit": {
                "type": "julia",
                "parameters": {
                    "c_real": -0.123,
                    "c_imag": 0.745,
                    "center": [0, 0],
                    "zoom": 1.2,
                    "max_iter": 100,
                    "cmap": "viridis",
                    "alpha": 0.25
                }
            },
            "julia_dragon": {
                "type": "julia",
                "parameters": {
                    "c_real": -0.835,
                    "c_imag": -0.2321,
                    "center": [0, 0],
                    "zoom": 1.3,
                    "max_iter": 180,
                    "cmap": "viridis"
                }
            },
            "julia_dendrite": {
                "type": "julia",
                "parameters": {
                    "c_real": 0.0,
                    "c_imag": 1.0,
                    "center": [0, 0],
                    "zoom": 1.5,
                    "max_iter": 100,
                    "cmap": "viridis",
                    "alpha": 0.25
                }
            },
            "julia_siegel_disk": {
                "type": "julia",
                "parameters": {
                    "c_real": -0.391,
                    "c_imag": -0.587,
                    "center": [0, 0],
                    "zoom": 1.2,
                    "max_iter": 100,
                    "cmap": "viridis",
                    "alpha": 0.25
                }
            },
            "julia_seahorse_valley": {
                "type": "julia",
                "parameters": {
                    "c_real": -0.75,
                    "c_imag": 0.1,
                    "center": [0, 0],
                    "zoom": 1.4,
                    "max_iter": 150,
                    "cmap": "viridis"
                }
            },
            "julia_san_marco": {
                "type": "julia",
                "parameters": {
                    "c_real": -0.75,
                    "c_imag": 0.0,
                    "center": [0, 0],
                    "zoom": 1.1,
                    "max_iter": 120,
                    "cmap": "viridis"
                }
            },
            "julia_galaxies": {
                "type": "julia",
                "parameters": {
                    "c_real": -1.25,
                    "c_imag": 0.0,
                    "center": [0, 0],
                    "zoom": 1.2,
                    "max_iter": 200,
                    "cmap": "viridis"
                }
            },
            "julia_feathers": {
                "type": "julia",
                "parameters": {
                    "c_real": 0.0,
                    "c_imag": -0.8,
                    "center": [0, 0],
                    "zoom": 1.3,
                    "max_iter": 150,
                    "cmap": "viridis"
                }
            },
            "julia_spiral": {
                "type": "julia",
                "parameters": {
                    "c_real": 0.7454054,
                    "c_imag": 0.1130063,
                    "center": [0, 0],
                    "zoom": 1.1,
                    "max_iter": 180,
                    "cmap": "viridis"
                }
            },
            "julia_nebula": {
                "type": "julia",
                "parameters": {
                    "c_real": -0.624,
                    "c_imag": 0.435,
                    "center": [0, 0],
                    "zoom": 1.25,
                    "max_iter": 200,
                    "cmap": "viridis"
                }
            }
        }
    }