#!/usr/bin/env python3
"""
Run integration tests for the RFM Architecture.

This script runs all integration tests for the RFM Architecture to verify
that components work correctly together.
"""
import os
import sys
import unittest
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("integration_tests")

def discover_and_run_tests(test_pattern=None, verbose=False):
    """
    Discover and run tests matching the given pattern.
    
    Args:
        test_pattern: Pattern to match test files (default: "test_*integration*.py")
        verbose: Whether to run tests in verbose mode
    
    Returns:
        Test result object
    """
    # Set default pattern if not provided
    if test_pattern is None:
        test_pattern = "test_*integration*.py"
    
    # Get the tests directory
    tests_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    
    # Discover tests
    loader = unittest.TestLoader()
    suite = loader.discover(tests_dir, pattern=test_pattern)
    
    # Run tests
    verbosity = 2 if verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity)
    return runner.run(suite)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run integration tests for the RFM Architecture")
    parser.add_argument("--pattern", type=str, default=None,
                      help="Pattern to match test files (default: 'test_*integration*.py')")
    parser.add_argument("--verbose", "-v", action="store_true",
                      help="Run tests in verbose mode")
    parser.add_argument("--sys-tests", action="store_true",
                      help="Run system integration tests only")
    parser.add_argument("--all", action="store_true",
                      help="Run all tests including non-integration tests")
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
    # Set test pattern based on arguments
    pattern = None
    if args.sys_tests:
        pattern = "test_system_integration.py"
    elif args.all:
        pattern = "test_*.py"
    else:
        pattern = args.pattern
    
    # Run tests
    logger.info(f"Running tests matching pattern: {pattern}")
    result = discover_and_run_tests(pattern, args.verbose)
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Tests run: {result.testsRun}")
    print(f"Errors: {len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Skipped: {len(result.skipped)}")
    
    # Exit with appropriate code
    if result.wasSuccessful():
        print("\nAll tests passed!")
        return 0
    else:
        print("\nSome tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())