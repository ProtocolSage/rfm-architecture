#!/usr/bin/env python3
"""
Comprehensive Resilience Testing Script for RFM Architecture

This script runs all resilience tests and integrates with CI/CD pipelines.
It can be used both in CI environments and by developers locally.
"""

import argparse
import logging
import os
import subprocess
import sys
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger("resilience-tests")


class ResilienceTestRunner:
    """Main class for running resilience tests."""

    def __init__(self, args: argparse.Namespace):
        """Initialize the test runner with command line arguments."""
        self.args = args
        self.test_results: Dict[str, Dict] = {}
        self.websocket_server_process: Optional[subprocess.Popen] = None
        self.start_time = datetime.now()
        
        # Set up directories
        self.project_root = Path(__file__).parents[2].resolve()
        self.output_dir = self.project_root / "test-results" / "resilience"
        self.logs_dir = self.output_dir / "logs"
        
        # Test definitions
        self.tests = [
            {
                "name": "connection_resilience",
                "description": "Tests resilience of connections under various network conditions",
                "module": "tests.resilience.test_connection_resilience",
                "timeout": args.connection_timeout,
            },
            {
                "name": "operation_resilience",
                "description": "Tests resilience of operations under error conditions",
                "module": "tests.resilience.test_operation_resilience",
                "timeout": args.operation_timeout,
            },
            {
                "name": "load_resilience",
                "description": "Tests resilience under various load conditions",
                "module": "tests.resilience.test_load_resilience",
                "timeout": args.load_timeout,
            },
        ]

    def setup_environment(self) -> bool:
        """Set up the test environment."""
        logger.info("Setting up test environment...")
        
        try:
            # Create necessary directories
            os.makedirs(self.output_dir, exist_ok=True)
            os.makedirs(self.logs_dir, exist_ok=True)
            
            # Check for dependencies
            self._check_dependencies()
            
            # Set up any required environment variables
            os.environ["RFM_TEST_MODE"] = "resilience"
            os.environ["RFM_LOG_LEVEL"] = self.args.log_level
            
            if self.args.env_file and os.path.exists(self.args.env_file):
                self._load_env_file(self.args.env_file)
                
            return True
        except Exception as e:
            logger.error(f"Failed to set up environment: {str(e)}")
            return False

    def _load_env_file(self, env_file: str) -> None:
        """Load environment variables from a file."""
        logger.info(f"Loading environment variables from {env_file}")
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        except Exception as e:
            logger.warning(f"Error loading environment file: {str(e)}")

    def _check_dependencies(self) -> None:
        """Check if all required dependencies are installed."""
        try:
            import pytest
            import websockets
            import asyncio
            
            # Add other required dependencies here
            
            logger.info("All dependencies are installed.")
        except ImportError as e:
            logger.error(f"Missing dependency: {str(e)}")
            if not self.args.ignore_dependency_errors:
                raise

    def start_websocket_server(self) -> bool:
        """Start the WebSocket server for testing."""
        logger.info("Starting WebSocket server...")
        
        try:
            server_script = self.project_root / "rfm" / "core" / "network.py"
            
            # If server script doesn't exist, try alternative locations
            if not server_script.exists():
                alternatives = [
                    self.project_root / "rfm" / "server.py",
                    self.project_root / "server" / "websocket.py"
                ]
                
                for alt in alternatives:
                    if alt.exists():
                        server_script = alt
                        break
                else:
                    raise FileNotFoundError("Could not find WebSocket server script")
            
            cmd = [
                sys.executable,
                str(server_script),
                "--port", str(self.args.port),
                "--log-level", self.args.log_level
            ]
            
            if self.args.debug:
                cmd.append("--debug")
            
            # Start server as a subprocess
            self.websocket_server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            
            # Wait for server to start
            logger.info(f"Waiting {self.args.server_startup_time}s for server to start...")
            time.sleep(self.args.server_startup_time)
            
            if self.websocket_server_process.poll() is not None:
                # Server failed to start
                stdout, stderr = self.websocket_server_process.communicate()
                logger.error(f"Server failed to start: {stderr}")
                return False
                
            logger.info(f"WebSocket server started on port {self.args.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {str(e)}")
            return False

    def run_tests(self) -> bool:
        """Run all resilience tests."""
        logger.info("Running resilience tests...")
        
        all_passed = True
        
        for test in self.tests:
            if self.args.skip and test["name"] in self.args.skip:
                logger.info(f"Skipping test: {test['name']}")
                continue
                
            if self.args.only and test["name"] not in self.args.only:
                logger.info(f"Skipping test: {test['name']} (not in --only list)")
                continue
            
            logger.info(f"Running test: {test['name']} - {test['description']}")
            
            try:
                # Build pytest command
                cmd = [
                    "pytest",
                    "-xvs",
                    test["module"],
                    f"--port={self.args.port}",
                ]
                
                if self.args.junit_xml:
                    junit_file = self.output_dir / f"{test['name']}_junit.xml"
                    cmd.append(f"--junitxml={junit_file}")
                
                # Set timeout
                cmd.append(f"--timeout={test['timeout']}")
                
                # Add any additional pytest arguments
                if self.args.pytest_args:
                    cmd.extend(self.args.pytest_args)
                
                # Run the test
                start_time = time.time()
                process = subprocess.run(
                    cmd,
                    universal_newlines=True,
                    capture_output=True,
                    check=False,
                )
                end_time = time.time()
                
                # Store results
                self.test_results[test["name"]] = {
                    "description": test["description"],
                    "command": " ".join(cmd),
                    "passed": process.returncode == 0,
                    "returncode": process.returncode,
                    "stdout": process.stdout,
                    "stderr": process.stderr,
                    "duration": end_time - start_time,
                }
                
                # Save logs
                log_file = self.logs_dir / f"{test['name']}.log"
                with open(log_file, "w") as f:
                    f.write(f"STDOUT:\n{process.stdout}\n\n")
                    f.write(f"STDERR:\n{process.stderr}\n\n")
                
                if process.returncode != 0:
                    logger.error(f"Test failed: {test['name']}")
                    if self.args.verbose:
                        logger.error(f"Error details: {process.stderr}")
                    all_passed = False
                else:
                    logger.info(f"Test passed: {test['name']}")
                
            except Exception as e:
                logger.error(f"Error running test {test['name']}: {str(e)}")
                self.test_results[test["name"]] = {
                    "description": test["description"],
                    "passed": False,
                    "error": str(e),
                }
                all_passed = False
                
            # Add a pause between tests if specified
            if self.args.test_pause > 0:
                logger.info(f"Pausing for {self.args.test_pause}s before next test...")
                time.sleep(self.args.test_pause)
        
        return all_passed

    def stop_websocket_server(self) -> None:
        """Stop the WebSocket server."""
        if self.websocket_server_process:
            logger.info("Stopping WebSocket server...")
            try:
                self.websocket_server_process.terminate()
                self.websocket_server_process.wait(timeout=5)
                logger.info("WebSocket server stopped")
            except subprocess.TimeoutExpired:
                logger.warning("WebSocket server did not terminate gracefully, forcing...")
                self.websocket_server_process.kill()
            except Exception as e:
                logger.error(f"Error stopping WebSocket server: {str(e)}")

    def generate_report(self) -> None:
        """Generate a consolidated report of test results."""
        logger.info("Generating consolidated report...")
        
        end_time = datetime.now()
        report_data = {
            "summary": {
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration": (end_time - self.start_time).total_seconds(),
                "total_tests": len(self.test_results),
                "passed_tests": sum(1 for result in self.test_results.values() if result.get("passed", False)),
                "failed_tests": sum(1 for result in self.test_results.values() if not result.get("passed", False)),
            },
            "tests": self.test_results,
            "environment": {
                "python_version": sys.version,
                "platform": sys.platform,
                "arguments": vars(self.args),
            }
        }
        
        # Save JSON report
        json_report_path = self.output_dir / "resilience_report.json"
        with open(json_report_path, "w") as f:
            json.dump(report_data, f, indent=2)
        
        # Generate HTML report
        html_report_path = self.output_dir / "resilience_report.html"
        self._generate_html_report(report_data, html_report_path)
        
        logger.info(f"Reports generated at: {self.output_dir}")
        logger.info(f"JSON Report: {json_report_path}")
        logger.info(f"HTML Report: {html_report_path}")
        
        # Print summary
        passed = report_data["summary"]["passed_tests"]
        total = report_data["summary"]["total_tests"]
        logger.info(f"SUMMARY: {passed}/{total} tests passed")
        
        for test_name, result in self.test_results.items():
            status = "PASSED" if result.get("passed", False) else "FAILED"
            logger.info(f"  {test_name}: {status}")

    def _generate_html_report(self, report_data: Dict, output_path: Path) -> None:
        """Generate an HTML report from the test results."""
        try:
            html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Resilience Tests Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2, h3 {{ color: #333; }}
        .summary {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .test {{ margin-bottom: 20px; padding: 15px; border-radius: 5px; }}
        .passed {{ background-color: #e6ffe6; border-left: 5px solid #33cc33; }}
        .failed {{ background-color: #ffe6e6; border-left: 5px solid #ff3333; }}
        pre {{ background-color: #f8f8f8; padding: 10px; border-radius: 3px; overflow-x: auto; }}
        .stats {{ display: flex; gap: 20px; }}
        .stat-item {{ flex: 1; padding: 10px; background-color: #eee; border-radius: 5px; text-align: center; }}
        .stat-value {{ font-size: 24px; font-weight: bold; margin: 5px 0; }}
        .pass-value {{ color: #33cc33; }}
        .fail-value {{ color: #ff3333; }}
        .duration-value {{ color: #3366ff; }}
    </style>
</head>
<body>
    <h1>Resilience Tests Report</h1>
    
    <div class="summary">
        <h2>Summary</h2>
        <div class="stats">
            <div class="stat-item">
                <h3>Passed</h3>
                <div class="stat-value pass-value">{report_data["summary"]["passed_tests"]}</div>
            </div>
            <div class="stat-item">
                <h3>Failed</h3>
                <div class="stat-value fail-value">{report_data["summary"]["failed_tests"]}</div>
            </div>
            <div class="stat-item">
                <h3>Total</h3>
                <div class="stat-value">{report_data["summary"]["total_tests"]}</div>
            </div>
            <div class="stat-item">
                <h3>Duration</h3>
                <div class="stat-value duration-value">{report_data["summary"]["duration"]:.2f}s</div>
            </div>
        </div>
        <p>Start Time: {report_data["summary"]["start_time"]}</p>
        <p>End Time: {report_data["summary"]["end_time"]}</p>
    </div>
    
    <h2>Test Results</h2>
    """
            
            # Add each test result
            for test_name, result in report_data["tests"].items():
                status = "passed" if result.get("passed", False) else "failed"
                
                html += f"""
    <div class="test {status}">
        <h3>{test_name}</h3>
        <p><strong>Description:</strong> {result.get("description", "")}</p>
        <p><strong>Status:</strong> {status.upper()}</p>
                """
                
                if "duration" in result:
                    html += f"""<p><strong>Duration:</strong> {result["duration"]:.2f}s</p>"""
                
                if "command" in result:
                    html += f"""
        <h4>Command</h4>
        <pre>{result["command"]}</pre>
                    """
                
                if "error" in result:
                    html += f"""
        <h4>Error</h4>
        <pre>{result["error"]}</pre>
                    """
                
                if "stderr" in result and result["stderr"].strip():
                    html += f"""
        <h4>Error Output</h4>
        <pre>{result["stderr"]}</pre>
                    """
                
                html += """
    </div>
                """
            
            # Add environment info
            html += f"""
    <h2>Environment</h2>
    <pre>{json.dumps(report_data["environment"], indent=2)}</pre>
    
</body>
</html>
            """
            
            with open(output_path, "w") as f:
                f.write(html)
                
        except Exception as e:
            logger.error(f"Error generating HTML report: {str(e)}")

    def run(self) -> int:
        """Run the full test suite."""
        try:
            # Setup
            if not self.setup_environment():
                return 1
            
            # Start server if required
            if not self.args.skip_server:
                if not self.start_websocket_server():
                    return 1
            
            # Run tests
            all_passed = self.run_tests()
            
            # Generate report
            self.generate_report()
            
            # Return appropriate exit code
            return 0 if all_passed else 1
            
        except KeyboardInterrupt:
            logger.info("Test execution interrupted by user")
            return 130
        except Exception as e:
            logger.error(f"Error running tests: {str(e)}")
            return 1
        finally:
            # Always stop the server if we started it
            if not self.args.skip_server and self.websocket_server_process:
                self.stop_websocket_server()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run RFM Architecture resilience tests",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    
    # Server configuration
    server_group = parser.add_argument_group("Server Configuration")
    server_group.add_argument("--port", type=int, default=8765,
                             help="Port for WebSocket server")
    server_group.add_argument("--skip-server", action="store_true",
                             help="Skip starting the WebSocket server (use if it's already running)")
    server_group.add_argument("--server-startup-time", type=int, default=3,
                             help="Time to wait for server to start (seconds)")
    
    # Test selection
    test_group = parser.add_argument_group("Test Selection")
    test_group.add_argument("--skip", type=str, nargs="+",
                           help="Tests to skip (e.g., --skip connection_resilience)")
    test_group.add_argument("--only", type=str, nargs="+",
                           help="Only run these tests (e.g., --only load_resilience)")
    
    # Timeouts
    timeout_group = parser.add_argument_group("Timeouts")
    timeout_group.add_argument("--connection-timeout", type=int, default=300,
                              help="Timeout for connection resilience tests (seconds)")
    timeout_group.add_argument("--operation-timeout", type=int, default=300,
                              help="Timeout for operation resilience tests (seconds)")
    timeout_group.add_argument("--load-timeout", type=int, default=600,
                              help="Timeout for load resilience tests (seconds)")
    timeout_group.add_argument("--test-pause", type=int, default=1,
                              help="Pause between tests (seconds)")
    
    # Reporting
    reporting_group = parser.add_argument_group("Reporting")
    reporting_group.add_argument("--junit-xml", action="store_true",
                                help="Generate JUnit XML reports")
    
    # Environment
    env_group = parser.add_argument_group("Environment")
    env_group.add_argument("--env-file", type=str,
                          help="Path to environment file (.env)")
    env_group.add_argument("--ignore-dependency-errors", action="store_true",
                          help="Ignore dependency errors and continue")
    
    # Logging
    logging_group = parser.add_argument_group("Logging")
    logging_group.add_argument("--log-level", type=str, default="INFO",
                              choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                              help="Logging level")
    logging_group.add_argument("--verbose", "-v", action="store_true",
                              help="Verbose output")
    logging_group.add_argument("--debug", action="store_true",
                              help="Debug mode")
    
    # Advanced
    advanced_group = parser.add_argument_group("Advanced")
    advanced_group.add_argument("--pytest-args", type=str, nargs="+",
                               help="Additional arguments to pass to pytest")
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    # Configure logging based on args
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(getattr(logging, args.log_level))
    
    # Run tests
    runner = ResilienceTestRunner(args)
    exit_code = runner.run()
    
    # Exit with appropriate code
    sys.exit(exit_code)