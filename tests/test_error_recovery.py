#!/usr/bin/env python3
"""
Integration tests for error handling and recovery mechanisms.

This test suite verifies the error handling and recovery mechanisms work correctly,
including self-healing strategies, error boundaries, and graceful degradation.
"""
import os
import sys
import unittest
import threading
import asyncio
import time
import json
import numpy as np
import tempfile
import logging
from typing import Dict, Any, List, Optional, Tuple
from unittest.mock import MagicMock, patch

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import components to test
from rfm.core.fractal import create_fractal, JuliaSet, MandelbrotSet
from rfm.core.progress import ProgressReporter, get_progress_manager
from ui.rfm_ui.engine.core import FractalEngine
from ui.rfm_ui.healing.strategies import (
    ParameterBoundsStrategy, NumericOverflowStrategy, 
    MemoryOverflowStrategy, InvalidColorStrategy,
    IterationLimitStrategy, ZoomDepthStrategy
)
from ui.rfm_ui.healing.recovery import RecoveryAction, RecoveryActionType
from ui.rfm_ui.errors.handler import ErrorHandler
from ui.rfm_ui.errors.types import ErrorSeverity, ErrorCategory
from ui.rfm_ui.errors.registry import ErrorRegistry
from ui.rfm_ui.healing.registry import HealingRegistry


class TestErrorRecovery(unittest.TestCase):
    """Test the error handling and recovery mechanisms."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test environment."""
        # Initialize fractal engine
        cls.engine = FractalEngine(enable_progress_reporting=False)
        
        # Initialize error registry
        cls.error_registry = ErrorRegistry()
        
        # Initialize healing registry
        cls.healing_registry = HealingRegistry()
        
        # Register healing strategies
        cls.healing_registry.register_strategy(ParameterBoundsStrategy())
        cls.healing_registry.register_strategy(NumericOverflowStrategy())
        cls.healing_registry.register_strategy(MemoryOverflowStrategy())
        cls.healing_registry.register_strategy(InvalidColorStrategy())
        cls.healing_registry.register_strategy(IterationLimitStrategy())
        cls.healing_registry.register_strategy(ZoomDepthStrategy())
        
        # Initialize error handler
        cls.error_handler = ErrorHandler(
            error_registry=cls.error_registry,
            healing_registry=cls.healing_registry
        )
    
    def test_parameter_bounds_healing(self):
        """Test that the parameter bounds healing strategy works correctly."""
        # Create invalid parameters
        invalid_params = {
            "type": "julia",
            "width": 400,
            "height": 300,
            "c_real": -0.7,
            "c_imag": 0.27,
            "center_x": 0.0,
            "center_y": 0.0,
            "zoom": -5.0,  # Invalid: must be positive
            "max_iter": 100,
            "colormap": "viridis",
            "high_quality": False
        }
        
        # Create test error
        test_error = ValueError("zoom must be between 0.1 and 1e10")
        
        # Create error context
        context = {
            "params": invalid_params,
            "operation": "fractal_render",
            "fractal_type": "julia"
        }
        
        # Process the error
        result = self.__class__.error_handler.process_error(test_error, context)
        
        # Verify error was processed
        self.assertIsNotNone(result)
        self.assertTrue(result.diagnosed)
        self.assertTrue(result.handled)
        self.assertGreater(len(result.recovery_actions), 0)
        
        # Verify diagnosis
        self.assertIn("zoom", result.diagnosis)
        self.assertIn("outside the valid range", result.diagnosis)
        
        # Find zoom parameter adjustment
        zoom_action = None
        for action in result.recovery_actions:
            if "zoom" in action.changes:
                zoom_action = action
                break
        
        self.assertIsNotNone(zoom_action)
        self.assertEqual(zoom_action.action_type, RecoveryActionType.PARAMETER_ADJUST)
        
        # Apply the zoom correction
        healed_params = invalid_params.copy()
        healed_params["zoom"] = zoom_action.changes["zoom"]
        
        # Try rendering with the healed parameters
        try:
            result = self.__class__.engine.render(healed_params)
            self.assertIsInstance(result, np.ndarray)
            self.assertEqual(result.shape, (300, 400, 4))
        except Exception as e:
            self.fail(f"Rendering with healed parameters failed: {e}")
    
    def test_numeric_overflow_healing(self):
        """Test that the numeric overflow healing strategy works correctly."""
        # Create invalid parameters
        invalid_params = {
            "type": "julia",
            "width": 400,
            "height": 300,
            "c_real": -0.7,
            "c_imag": 0.27,
            "center_x": 1e15,  # Extreme value
            "center_y": 2e15,  # Extreme value
            "zoom": 1e12,  # Extreme value
            "max_iter": 100,
            "colormap": "viridis",
            "high_quality": False
        }
        
        # Create test error
        test_error = OverflowError("Numerical result too large")
        
        # Create error context
        context = {
            "params": invalid_params,
            "operation": "fractal_render",
            "fractal_type": "julia"
        }
        
        # Process the error
        result = self.__class__.error_handler.process_error(test_error, context)
        
        # Verify error was processed
        self.assertIsNotNone(result)
        self.assertTrue(result.diagnosed)
        self.assertTrue(result.handled)
        self.assertGreater(len(result.recovery_actions), 0)
        
        # Apply all recovery actions
        healed_params = invalid_params.copy()
        best_action = result.recovery_actions[0]  # Get first (best) action
        
        for key, value in best_action.changes.items():
            healed_params[key] = value
        
        # Verify parameters were adjusted
        self.assertLess(healed_params["zoom"], invalid_params["zoom"])
        
        # Only check center coordinates if they were adjusted
        if "center_x" in best_action.changes:
            self.assertLess(abs(healed_params["center_x"]), abs(invalid_params["center_x"]))
        if "center_y" in best_action.changes:
            self.assertLess(abs(healed_params["center_y"]), abs(invalid_params["center_y"]))
    
    def test_memory_overflow_healing(self):
        """Test that the memory overflow healing strategy works correctly."""
        # Create invalid parameters
        invalid_params = {
            "type": "mandelbrot",
            "width": 10000,  # Very high resolution
            "height": 8000,  # Very high resolution
            "center_x": -0.5,
            "center_y": 0.0,
            "zoom": 1.0,
            "max_iter": 1000,
            "colormap": "viridis",
            "high_quality": True
        }
        
        # Create test error
        test_error = MemoryError("Cannot allocate memory for array")
        
        # Create error context
        context = {
            "params": invalid_params,
            "operation": "fractal_render",
            "fractal_type": "mandelbrot"
        }
        
        # Process the error
        result = self.__class__.error_handler.process_error(test_error, context)
        
        # Verify error was processed
        self.assertIsNotNone(result)
        self.assertTrue(result.diagnosed)
        self.assertTrue(result.handled)
        self.assertGreater(len(result.recovery_actions), 0)
        
        # Verify diagnosis
        self.assertIn("memory", result.diagnosis.lower())
        
        # Apply all recovery actions
        healed_params = invalid_params.copy()
        best_action = result.recovery_actions[0]  # Get first (best) action
        
        for key, value in best_action.changes.items():
            healed_params[key] = value
        
        # Verify resolution was reduced
        self.assertLess(healed_params["width"] * healed_params["height"], 
                       invalid_params["width"] * invalid_params["height"])
        
        # Verify high quality was disabled
        if "high_quality" in best_action.changes:
            self.assertFalse(healed_params["high_quality"])
    
    def test_invalid_colormap_healing(self):
        """Test that the invalid color specification healing strategy works correctly."""
        # Create invalid parameters
        invalid_params = {
            "type": "julia",
            "width": 400,
            "height": 300,
            "c_real": -0.7,
            "c_imag": 0.27,
            "center_x": 0.0,
            "center_y": 0.0,
            "zoom": 1.5,
            "max_iter": 100,
            "colormap": "nonexistent_colormap",  # Invalid colormap
            "high_quality": False
        }
        
        # Create test error
        test_error = ValueError("Unknown colormap: nonexistent_colormap")
        
        # Create error context
        context = {
            "params": invalid_params,
            "operation": "fractal_render",
            "fractal_type": "julia"
        }
        
        # Process the error
        result = self.__class__.error_handler.process_error(test_error, context)
        
        # Verify error was processed
        self.assertIsNotNone(result)
        self.assertTrue(result.diagnosed)
        self.assertTrue(result.handled)
        self.assertGreater(len(result.recovery_actions), 0)
        
        # Verify diagnosis
        self.assertIn("colormap", result.diagnosis.lower())
        
        # Find colormap adjustment
        colormap_action = None
        for action in result.recovery_actions:
            if "colormap" in action.changes:
                colormap_action = action
                break
        
        self.assertIsNotNone(colormap_action)
        self.assertEqual(colormap_action.action_type, RecoveryActionType.PARAMETER_ADJUST)
        
        # Apply the colormap correction
        healed_params = invalid_params.copy()
        healed_params["colormap"] = colormap_action.changes["colormap"]
        
        # Try rendering with the healed parameters
        try:
            result = self.__class__.engine.render(healed_params)
            self.assertIsInstance(result, np.ndarray)
            self.assertEqual(result.shape, (300, 400, 4))
        except Exception as e:
            self.fail(f"Rendering with healed parameters failed: {e}")
    
    def test_iteration_limit_healing(self):
        """Test that the iteration limit healing strategy works correctly."""
        # Create invalid parameters
        invalid_params = {
            "type": "mandelbrot",
            "width": 400,
            "height": 300,
            "center_x": -0.5,
            "center_y": 0.0,
            "zoom": 1.0,
            "max_iter": 100000,  # Extreme value
            "colormap": "viridis",
            "high_quality": False
        }
        
        # Create test error
        test_error = RuntimeError("Maximum iteration limit exceeded")
        
        # Create error context
        context = {
            "params": invalid_params,
            "operation": "fractal_render",
            "fractal_type": "mandelbrot"
        }
        
        # Process the error
        result = self.__class__.error_handler.process_error(test_error, context)
        
        # Verify error was processed
        self.assertIsNotNone(result)
        self.assertTrue(result.diagnosed)
        self.assertTrue(result.handled)
        self.assertGreater(len(result.recovery_actions), 0)
        
        # Verify diagnosis
        self.assertIn("iteration", result.diagnosis.lower())
        
        # Find max_iter adjustment
        max_iter_action = None
        for action in result.recovery_actions:
            if "max_iter" in action.changes:
                max_iter_action = action
                break
        
        self.assertIsNotNone(max_iter_action)
        self.assertEqual(max_iter_action.action_type, RecoveryActionType.PARAMETER_ADJUST)
        
        # Apply the max_iter correction
        healed_params = invalid_params.copy()
        healed_params["max_iter"] = max_iter_action.changes["max_iter"]
        
        # Verify max_iter was reduced
        self.assertLess(healed_params["max_iter"], invalid_params["max_iter"])
    
    def test_zoom_depth_healing(self):
        """Test that the zoom depth healing strategy works correctly."""
        # Create invalid parameters
        invalid_params = {
            "type": "mandelbrot",
            "width": 400,
            "height": 300,
            "center_x": -0.5,
            "center_y": 0.0,
            "zoom": 1e15,  # Extreme zoom value
            "max_iter": 100,
            "colormap": "viridis",
            "high_quality": False
        }
        
        # Create test error
        test_error = ArithmeticError("Floating point precision error due to extreme zoom")
        
        # Create error context
        context = {
            "params": invalid_params,
            "operation": "fractal_render",
            "fractal_type": "mandelbrot"
        }
        
        # Process the error
        result = self.__class__.error_handler.process_error(test_error, context)
        
        # Verify error was processed
        self.assertIsNotNone(result)
        self.assertTrue(result.diagnosed)
        self.assertTrue(result.handled)
        self.assertGreater(len(result.recovery_actions), 0)
        
        # Verify diagnosis
        self.assertIn("zoom", result.diagnosis.lower())
        
        # Find zoom adjustment
        zoom_action = None
        for action in result.recovery_actions:
            if "zoom" in action.changes:
                zoom_action = action
                break
        
        self.assertIsNotNone(zoom_action)
        self.assertEqual(zoom_action.action_type, RecoveryActionType.PARAMETER_ADJUST)
        
        # Apply the zoom correction
        healed_params = invalid_params.copy()
        healed_params["zoom"] = zoom_action.changes["zoom"]
        
        # Verify zoom was reduced
        self.assertLess(healed_params["zoom"], invalid_params["zoom"])
    
    def test_multiple_errors_healing(self):
        """Test handling multiple errors with appropriate healing strategies."""
        # Create parameters with multiple issues
        invalid_params = {
            "type": "julia",
            "width": 8000,  # Very high resolution
            "height": 6000,  # Very high resolution
            "c_real": -0.7,
            "c_imag": 0.27,
            "center_x": 0.0,
            "center_y": 0.0,
            "zoom": -2.0,  # Invalid: must be positive
            "max_iter": 20000,  # Extreme value
            "colormap": "nonexistent_colormap",  # Invalid colormap
            "high_quality": True
        }
        
        # Test different errors with the same context
        errors = [
            ValueError("zoom must be between 0.1 and 1e10"),
            ValueError("Unknown colormap: nonexistent_colormap"),
            RuntimeError("Maximum iteration limit exceeded"),
            MemoryError("Cannot allocate memory for array")
        ]
        
        # Create error context
        context = {
            "params": invalid_params,
            "operation": "fractal_render",
            "fractal_type": "julia"
        }
        
        # Track all suggested parameter changes
        all_changes = {}
        
        for error in errors:
            # Process each error
            result = self.__class__.error_handler.process_error(error, context)
            
            # Verify error was processed
            self.assertIsNotNone(result)
            self.assertTrue(result.diagnosed)
            self.assertTrue(result.handled)
            self.assertGreater(len(result.recovery_actions), 0)
            
            # Collect changes from best action
            best_action = result.recovery_actions[0]
            for key, value in best_action.changes.items():
                all_changes[key] = value
        
        # Apply all changes to create a fully healed parameter set
        healed_params = invalid_params.copy()
        for key, value in all_changes.items():
            healed_params[key] = value
        
        # Verify key parameters were fixed
        if "zoom" in all_changes:
            self.assertGreaterEqual(healed_params["zoom"], 0.1)
        
        if "colormap" in all_changes:
            self.assertNotEqual(healed_params["colormap"], "nonexistent_colormap")
        
        if "max_iter" in all_changes:
            self.assertLess(healed_params["max_iter"], 20000)
        
        if "width" in all_changes and "height" in all_changes:
            self.assertLess(healed_params["width"] * healed_params["height"], 
                           invalid_params["width"] * invalid_params["height"])
    
    def test_error_registry_integration(self):
        """Test that the error registry correctly tracks and categorizes errors."""
        # Create a test error
        test_error = ValueError("zoom must be between 0.1 and 1e10")
        
        # Register the error
        error_id = self.__class__.error_registry.register_error(
            test_error,
            error_category=ErrorCategory.PARAMETER_VALIDATION,
            severity=ErrorSeverity.WARNING,
            additional_info={
                "parameter": "zoom",
                "min_value": 0.1,
                "max_value": 1e10
            }
        )
        
        # Verify error was registered
        self.assertIsNotNone(error_id)
        
        # Retrieve the error
        error_info = self.__class__.error_registry.get_error(error_id)
        self.assertIsNotNone(error_info)
        
        # Verify error information
        self.assertEqual(error_info["category"], ErrorCategory.PARAMETER_VALIDATION)
        self.assertEqual(error_info["severity"], ErrorSeverity.WARNING)
        self.assertIn("parameter", error_info["additional_info"])
        self.assertEqual(error_info["additional_info"]["parameter"], "zoom")
        
        # Test error searching
        parameter_errors = self.__class__.error_registry.search_errors(
            category=ErrorCategory.PARAMETER_VALIDATION
        )
        self.assertGreaterEqual(len(parameter_errors), 1)
        
        # Test error statistics
        stats = self.__class__.error_registry.get_error_statistics()
        self.assertIn(ErrorCategory.PARAMETER_VALIDATION, stats["by_category"])
        self.assertIn(ErrorSeverity.WARNING, stats["by_severity"])
    
    def test_complex_error_scenarios(self):
        """Test handling of complex error scenarios with multiple strategies."""
        # Create a mock rendering function that simulates different errors
        def mock_render(params):
            errors = []
            
            # Check for parameter bounds errors
            if params.get("zoom", 1.0) <= 0:
                errors.append(ValueError("zoom must be positive"))
            
            # Check for extremely high zoom
            if params.get("zoom", 1.0) > 1e10:
                errors.append(ArithmeticError("Precision error due to extreme zoom"))
            
            # Check for valid colormap
            if params.get("colormap") == "nonexistent_colormap":
                errors.append(ValueError("Unknown colormap: nonexistent_colormap"))
            
            # Check for memory issues with high resolution
            width = params.get("width", 800)
            height = params.get("height", 600)
            if width * height > 10_000_000:  # 10 megapixels
                errors.append(MemoryError("Cannot allocate memory for large image"))
            
            # Return the first error found, or a successful result
            if errors:
                raise errors[0]
            
            # Return a mock image if no errors
            return np.zeros((height, width, 4))
        
        # Create different test scenarios
        scenarios = [
            {
                "name": "Negative zoom scenario",
                "params": {
                    "type": "mandelbrot",
                    "width": 800,
                    "height": 600,
                    "zoom": -1.0,
                    "colormap": "viridis"
                },
                "expected_error_type": ValueError
            },
            {
                "name": "Extreme zoom scenario",
                "params": {
                    "type": "julia",
                    "width": 800,
                    "height": 600,
                    "zoom": 1e12,
                    "colormap": "viridis"
                },
                "expected_error_type": ArithmeticError
            },
            {
                "name": "Invalid colormap scenario",
                "params": {
                    "type": "mandelbrot",
                    "width": 800,
                    "height": 600,
                    "zoom": 1.0,
                    "colormap": "nonexistent_colormap"
                },
                "expected_error_type": ValueError
            },
            {
                "name": "Memory overflow scenario",
                "params": {
                    "type": "julia",
                    "width": 5000,
                    "height": 4000,
                    "zoom": 1.0,
                    "colormap": "viridis"
                },
                "expected_error_type": MemoryError
            }
        ]
        
        # Test each scenario
        for scenario in scenarios:
            with self.subTest(scenario=scenario["name"]):
                # Try rendering with invalid parameters
                try:
                    mock_render(scenario["params"])
                    self.fail(f"Expected {scenario['expected_error_type'].__name__} was not raised")
                except Exception as e:
                    # Verify the expected error was raised
                    self.assertIsInstance(e, scenario["expected_error_type"])
                    
                    # Get healing strategy
                    result = self.__class__.error_handler.process_error(
                        e, {"params": scenario["params"]}
                    )
                    
                    # Verify error was handled
                    self.assertIsNotNone(result)
                    self.assertTrue(result.handled)
                    self.assertGreater(len(result.recovery_actions), 0)
                    
                    # Apply the first suggested recovery action
                    healed_params = scenario["params"].copy()
                    for key, value in result.recovery_actions[0].changes.items():
                        healed_params[key] = value
                    
                    try:
                        # Try rendering again with healed parameters
                        mock_render(healed_params)
                        # If we get here, the healing was successful
                    except Exception as e2:
                        self.fail(f"Healing failed: {e2}")
    
    def test_error_boundary_functionality(self):
        """Test that error boundaries contain and report errors correctly."""
        
        # Create an error boundary class for testing
        class TestErrorBoundary:
            def __init__(self, error_handler):
                self.error_handler = error_handler
                self.last_error = None
                self.last_result = None
            
            def execute(self, function, *args, **kwargs):
                """Execute a function within an error boundary."""
                try:
                    result = function(*args, **kwargs)
                    self.last_error = None
                    self.last_result = result
                    return {"success": True, "result": result}
                except Exception as e:
                    self.last_error = e
                    
                    # Process the error
                    context = {"args": args, "kwargs": kwargs}
                    result = self.error_handler.process_error(e, context)
                    self.last_result = result
                    
                    return {
                        "success": False, 
                        "error": e,
                        "diagnosis": result.diagnosis if result else "Unknown error",
                        "recovery_actions": result.recovery_actions if result else []
                    }
        
        # Create a test boundary
        boundary = TestErrorBoundary(self.__class__.error_handler)
        
        # Define test functions
        def divide(a, b):
            return a / b
        
        def render_fractal(params):
            # Simplified validation logic
            if params.get("zoom", 1.0) <= 0:
                raise ValueError("zoom must be positive")
            if params.get("colormap") == "nonexistent_colormap":
                raise ValueError("Unknown colormap: nonexistent_colormap")
            return np.zeros((params.get("height", 100), params.get("width", 100), 4))
        
        # Test successful execution
        result = boundary.execute(divide, 10, 2)
        self.assertTrue(result["success"])
        self.assertEqual(result["result"], 5)
        
        # Test division by zero
        result = boundary.execute(divide, 10, 0)
        self.assertFalse(result["success"])
        self.assertIsInstance(result["error"], ZeroDivisionError)
        
        # Test fractal rendering with valid parameters
        valid_params = {
            "type": "mandelbrot",
            "width": 100,
            "height": 100,
            "zoom": 1.0,
            "colormap": "viridis"
        }
        result = boundary.execute(render_fractal, valid_params)
        self.assertTrue(result["success"])
        
        # Test fractal rendering with invalid zoom
        invalid_params = valid_params.copy()
        invalid_params["zoom"] = -1.0
        result = boundary.execute(render_fractal, invalid_params)
        self.assertFalse(result["success"])
        self.assertIsInstance(result["error"], ValueError)
        self.assertIn("zoom", result["diagnosis"].lower())
        self.assertGreater(len(result["recovery_actions"]), 0)
        
        # Test fractal rendering with invalid colormap
        invalid_params = valid_params.copy()
        invalid_params["colormap"] = "nonexistent_colormap"
        result = boundary.execute(render_fractal, invalid_params)
        self.assertFalse(result["success"])
        self.assertIsInstance(result["error"], ValueError)
        self.assertIn("colormap", result["diagnosis"].lower())
        self.assertGreater(len(result["recovery_actions"]), 0)


if __name__ == "__main__":
    unittest.main()