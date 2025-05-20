"""
Performance benchmark suite for fractal rendering algorithms.

This module provides standardized benchmarks for measuring the performance
of different fractal rendering algorithms under various parameter configurations.
Results are used to establish baseline performance profiles and detect regressions.
"""

import time
import json
import os
import sys
import numpy as np
import argparse
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from datetime import datetime
import multiprocessing
import psutil
import matplotlib.pyplot as plt
from pathlib import Path

# Add parent directory to path so we can import from the rfm package
sys.path.append(str(Path(__file__).parent.parent.parent))

from rfm.core.fractal import (
    MandelbrotSet,
    JuliaSet,
    LSystem,
    CantorDust,
    SierpinskiTriangle,
    IFSFractal
)


@dataclass
class BenchmarkResult:
    """Results of a single benchmark run."""
    
    fractal_type: str
    parameters: Dict[str, Any]
    resolution: Tuple[int, int]
    duration_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    iterations_per_pixel: float
    timestamp: str
    system_info: Dict[str, Any]


class FractalBenchmark:
    """
    Benchmark suite for fractal rendering algorithms.
    
    This class provides methods to benchmark different fractal types
    across various parameters and resolutions, and to compare results
    against established baselines.
    """
    
    def __init__(self, output_dir: str = "./benchmark_results"):
        """
        Initialize the benchmark suite.
        
        Args:
            output_dir: Directory to store benchmark results
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        self.logger = logging.getLogger("fractal_benchmark")
        self.logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler(
            self.output_dir / f"benchmark_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
        # Get system info once
        self.system_info = self._get_system_info()
        
    def _get_system_info(self) -> Dict[str, Any]:
        """
        Collect system information for benchmark context.
        
        Returns:
            Dictionary with system information
        """
        cpu_info = {}
        try:
            import cpuinfo
            cpu_info = cpuinfo.get_cpu_info()
        except ImportError:
            cpu_info = {
                "brand_raw": "Unknown (cpuinfo module not installed)",
                "count": psutil.cpu_count(logical=True),
                "physical_count": psutil.cpu_count(logical=False)
            }
        
        # Try to get GPU info if available
        gpu_info = "Unknown"
        try:
            # For NVIDIA GPUs using pynvml
            import pynvml
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            if device_count > 0:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                gpu_info = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                pynvml.nvmlShutdown()
        except (ImportError, Exception):
            # Just continue without GPU info if not available
            pass
            
        memory = psutil.virtual_memory()
        
        return {
            "cpu": {
                "brand": cpu_info.get("brand_raw", "Unknown"),
                "cores_logical": cpu_info.get("count", psutil.cpu_count(logical=True)),
                "cores_physical": cpu_info.get("physical_count", psutil.cpu_count(logical=False))
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2)
            },
            "gpu": gpu_info,
            "platform": sys.platform,
            "python_version": sys.version,
            "timestamp": datetime.now().isoformat()
        }
    
    def benchmark_mandelbrot(self, 
                           resolutions: List[Tuple[int, int]] = [(512, 512), (1024, 1024)],
                           max_iterations: List[int] = [100, 500, 1000],
                           zoom_levels: List[float] = [1.0, 10.0, 100.0],
                           repeats: int = 3) -> List[BenchmarkResult]:
        """
        Benchmark Mandelbrot set rendering with different parameters.
        
        Args:
            resolutions: List of resolutions to test
            max_iterations: List of max iteration counts to test
            zoom_levels: List of zoom levels to test
            repeats: Number of times to repeat each benchmark for statistical accuracy
            
        Returns:
            List of benchmark results
        """
        results = []
        
        for resolution in resolutions:
            for max_iter in max_iterations:
                for zoom in zoom_levels:
                    # Benchmark parameters for this run
                    params = {
                        "max_iterations": max_iter,
                        "zoom": zoom,
                        "center_x": -0.5,
                        "center_y": 0.0
                    }
                    
                    self.logger.info(f"Benchmarking Mandelbrot set: {resolution}, max_iter={max_iter}, zoom={zoom}")
                    
                    # Create fractal instance
                    fractal = MandelbrotSet(
                        max_iterations=max_iter,
                        escape_radius=2.0
                    )
                    
                    # Set view parameters
                    x_min, x_max = -2.0 / zoom, 1.0 / zoom
                    y_min, y_max = -1.5 / zoom, 1.5 / zoom
                    
                    # Center the view
                    width = x_max - x_min
                    height = y_max - y_min
                    x_min = params["center_x"] - width / 2
                    x_max = params["center_x"] + width / 2
                    y_min = params["center_y"] - height / 2
                    y_max = params["center_y"] + height / 2
                    
                    # Repeat benchmark multiple times
                    durations = []
                    memory_usages = []
                    cpu_usages = []
                    iterations_counts = []
                    
                    for i in range(repeats):
                        # Get process for resource monitoring
                        process = psutil.Process(os.getpid())
                        
                        # Record initial memory
                        initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
                        
                        # Start CPU usage monitoring
                        process.cpu_percent()  # First call initializes monitoring
                        
                        # Measure rendering time
                        start_time = time.time()
                        
                        # Render the fractal
                        image_data, iterations = fractal.render(
                            width=resolution[0],
                            height=resolution[1],
                            x_min=x_min,
                            x_max=x_max,
                            y_min=y_min,
                            y_max=y_max
                        )
                        
                        # Calculate elapsed time
                        elapsed = (time.time() - start_time) * 1000  # ms
                        
                        # Record final memory and CPU usage
                        final_memory = process.memory_info().rss / (1024 * 1024)  # MB
                        cpu_percent = process.cpu_percent()
                        
                        # Calculate average iterations per pixel
                        avg_iterations = np.mean(iterations)
                        
                        # Store measurements
                        durations.append(elapsed)
                        memory_usages.append(final_memory - initial_memory)
                        cpu_usages.append(cpu_percent)
                        iterations_counts.append(avg_iterations)
                        
                        self.logger.debug(f"  Run {i+1}/{repeats}: {elapsed:.2f}ms, "
                                         f"{final_memory - initial_memory:.2f}MB, "
                                         f"{cpu_percent:.1f}% CPU, "
                                         f"{avg_iterations:.1f} avg iterations")
                    
                    # Calculate averages across runs
                    avg_duration = sum(durations) / len(durations)
                    avg_memory = sum(memory_usages) / len(memory_usages)
                    avg_cpu = sum(cpu_usages) / len(cpu_usages)
                    avg_iterations_per_pixel = sum(iterations_counts) / len(iterations_counts)
                    
                    # Create result
                    result = BenchmarkResult(
                        fractal_type="MandelbrotSet",
                        parameters=params,
                        resolution=resolution,
                        duration_ms=avg_duration,
                        memory_usage_mb=avg_memory,
                        cpu_usage_percent=avg_cpu,
                        iterations_per_pixel=avg_iterations_per_pixel,
                        timestamp=datetime.now().isoformat(),
                        system_info=self.system_info
                    )
                    
                    results.append(result)
                    
                    self.logger.info(f"  Result: avg={avg_duration:.2f}ms, "
                                    f"memory={avg_memory:.2f}MB, "
                                    f"CPU={avg_cpu:.1f}%, "
                                    f"avg_iter={avg_iterations_per_pixel:.1f}")
        
        return results
    
    def benchmark_julia(self, 
                      resolutions: List[Tuple[int, int]] = [(512, 512), (1024, 1024)],
                      max_iterations: List[int] = [100, 500, 1000],
                      c_values: List[Tuple[float, float]] = [
                          (-0.7, 0.27),  # Classic Julia set
                          (-0.8, 0.156),
                          (-0.4, 0.6)
                      ],
                      repeats: int = 3) -> List[BenchmarkResult]:
        """
        Benchmark Julia set rendering with different parameters.
        
        Args:
            resolutions: List of resolutions to test
            max_iterations: List of max iteration counts to test
            c_values: List of c values (complex parameter) to test
            repeats: Number of times to repeat each benchmark for statistical accuracy
            
        Returns:
            List of benchmark results
        """
        results = []
        
        for resolution in resolutions:
            for max_iter in max_iterations:
                for c_value in c_values:
                    # Benchmark parameters for this run
                    params = {
                        "max_iterations": max_iter,
                        "c_real": c_value[0],
                        "c_imag": c_value[1]
                    }
                    
                    self.logger.info(f"Benchmarking Julia set: {resolution}, max_iter={max_iter}, "
                                    f"c=({c_value[0]}, {c_value[1]}i)")
                    
                    # Create fractal instance
                    fractal = JuliaSet(
                        max_iterations=max_iter,
                        c_real=c_value[0],
                        c_imag=c_value[1],
                        escape_radius=2.0
                    )
                    
                    # Set view parameters (standard Julia view)
                    x_min, x_max = -2.0, 2.0
                    y_min, y_max = -2.0, 2.0
                    
                    # Repeat benchmark multiple times
                    durations = []
                    memory_usages = []
                    cpu_usages = []
                    iterations_counts = []
                    
                    for i in range(repeats):
                        # Get process for resource monitoring
                        process = psutil.Process(os.getpid())
                        
                        # Record initial memory
                        initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
                        
                        # Start CPU usage monitoring
                        process.cpu_percent()  # First call initializes monitoring
                        
                        # Measure rendering time
                        start_time = time.time()
                        
                        # Render the fractal
                        image_data, iterations = fractal.render(
                            width=resolution[0],
                            height=resolution[1],
                            x_min=x_min,
                            x_max=x_max,
                            y_min=y_min,
                            y_max=y_max
                        )
                        
                        # Calculate elapsed time
                        elapsed = (time.time() - start_time) * 1000  # ms
                        
                        # Record final memory and CPU usage
                        final_memory = process.memory_info().rss / (1024 * 1024)  # MB
                        cpu_percent = process.cpu_percent()
                        
                        # Calculate average iterations per pixel
                        avg_iterations = np.mean(iterations)
                        
                        # Store measurements
                        durations.append(elapsed)
                        memory_usages.append(final_memory - initial_memory)
                        cpu_usages.append(cpu_percent)
                        iterations_counts.append(avg_iterations)
                        
                        self.logger.debug(f"  Run {i+1}/{repeats}: {elapsed:.2f}ms, "
                                         f"{final_memory - initial_memory:.2f}MB, "
                                         f"{cpu_percent:.1f}% CPU, "
                                         f"{avg_iterations:.1f} avg iterations")
                    
                    # Calculate averages across runs
                    avg_duration = sum(durations) / len(durations)
                    avg_memory = sum(memory_usages) / len(memory_usages)
                    avg_cpu = sum(cpu_usages) / len(cpu_usages)
                    avg_iterations_per_pixel = sum(iterations_counts) / len(iterations_counts)
                    
                    # Create result
                    result = BenchmarkResult(
                        fractal_type="JuliaSet",
                        parameters=params,
                        resolution=resolution,
                        duration_ms=avg_duration,
                        memory_usage_mb=avg_memory,
                        cpu_usage_percent=avg_cpu,
                        iterations_per_pixel=avg_iterations_per_pixel,
                        timestamp=datetime.now().isoformat(),
                        system_info=self.system_info
                    )
                    
                    results.append(result)
                    
                    self.logger.info(f"  Result: avg={avg_duration:.2f}ms, "
                                    f"memory={avg_memory:.2f}MB, "
                                    f"CPU={avg_cpu:.1f}%, "
                                    f"avg_iter={avg_iterations_per_pixel:.1f}")
        
        return results
    
    def benchmark_lsystem(self,
                        resolutions: List[Tuple[int, int]] = [(512, 512), (1024, 1024)],
                        iterations: List[int] = [3, 4, 5],
                        systems: List[str] = ["dragon", "tree", "sierpinski"],
                        repeats: int = 3) -> List[BenchmarkResult]:
        """
        Benchmark L-System rendering with different parameters.
        
        Args:
            resolutions: List of resolutions to test
            iterations: List of iteration counts to test
            systems: List of L-System types to test
            repeats: Number of times to repeat each benchmark for statistical accuracy
            
        Returns:
            List of benchmark results
        """
        results = []
        
        # L-System definitions
        lsystem_configs = {
            "dragon": {
                "axiom": "FX",
                "rules": {"X": "X+YF+", "Y": "-FX-Y"},
                "angle": 90
            },
            "tree": {
                "axiom": "F",
                "rules": {"F": "FF+[+F-F-F]-[-F+F+F]"},
                "angle": 25
            },
            "sierpinski": {
                "axiom": "A",
                "rules": {"A": "B-A-B", "B": "A+B+A"},
                "angle": 60
            }
        }
        
        for resolution in resolutions:
            for iter_count in iterations:
                for system_name in systems:
                    # Get L-System configuration
                    config = lsystem_configs[system_name]
                    
                    # Benchmark parameters for this run
                    params = {
                        "iterations": iter_count,
                        "system": system_name,
                        "axiom": config["axiom"],
                        "angle": config["angle"]
                    }
                    
                    self.logger.info(f"Benchmarking L-System: {resolution}, {system_name}, iterations={iter_count}")
                    
                    # Create fractal instance
                    fractal = LSystem(
                        axiom=config["axiom"],
                        rules=config["rules"],
                        angle=config["angle"]
                    )
                    
                    # Repeat benchmark multiple times
                    durations = []
                    memory_usages = []
                    cpu_usages = []
                    
                    for i in range(repeats):
                        # Get process for resource monitoring
                        process = psutil.Process(os.getpid())
                        
                        # Record initial memory
                        initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
                        
                        # Start CPU usage monitoring
                        process.cpu_percent()  # First call initializes monitoring
                        
                        # Measure rendering time
                        start_time = time.time()
                        
                        # Render the fractal
                        image_data = fractal.render(
                            width=resolution[0],
                            height=resolution[1],
                            iterations=iter_count
                        )
                        
                        # Calculate elapsed time
                        elapsed = (time.time() - start_time) * 1000  # ms
                        
                        # Record final memory and CPU usage
                        final_memory = process.memory_info().rss / (1024 * 1024)  # MB
                        cpu_percent = process.cpu_percent()
                        
                        # Store measurements
                        durations.append(elapsed)
                        memory_usages.append(final_memory - initial_memory)
                        cpu_usages.append(cpu_percent)
                        
                        self.logger.debug(f"  Run {i+1}/{repeats}: {elapsed:.2f}ms, "
                                        f"{final_memory - initial_memory:.2f}MB, "
                                        f"{cpu_percent:.1f}% CPU")
                    
                    # Calculate averages across runs
                    avg_duration = sum(durations) / len(durations)
                    avg_memory = sum(memory_usages) / len(memory_usages)
                    avg_cpu = sum(cpu_usages) / len(cpu_usages)
                    
                    # Create result
                    result = BenchmarkResult(
                        fractal_type="LSystem",
                        parameters=params,
                        resolution=resolution,
                        duration_ms=avg_duration,
                        memory_usage_mb=avg_memory,
                        cpu_usage_percent=avg_cpu,
                        iterations_per_pixel=0.0,  # Not applicable for L-Systems
                        timestamp=datetime.now().isoformat(),
                        system_info=self.system_info
                    )
                    
                    results.append(result)
                    
                    self.logger.info(f"  Result: avg={avg_duration:.2f}ms, "
                                    f"memory={avg_memory:.2f}MB, "
                                    f"CPU={avg_cpu:.1f}%")
        
        return results
    
    def benchmark_all(self) -> Dict[str, List[BenchmarkResult]]:
        """
        Run benchmarks for all fractal types.
        
        Returns:
            Dictionary mapping fractal types to lists of benchmark results
        """
        results = {}
        
        # Benchmark Mandelbrot set
        self.logger.info("Starting Mandelbrot set benchmarks")
        mandelbrot_results = self.benchmark_mandelbrot()
        results["MandelbrotSet"] = mandelbrot_results
        
        # Benchmark Julia set
        self.logger.info("Starting Julia set benchmarks")
        julia_results = self.benchmark_julia()
        results["JuliaSet"] = julia_results
        
        # Benchmark L-System
        self.logger.info("Starting L-System benchmarks")
        lsystem_results = self.benchmark_lsystem()
        results["LSystem"] = lsystem_results
        
        return results
    
    def save_results(self, results: Union[List[BenchmarkResult], Dict[str, List[BenchmarkResult]]]) -> str:
        """
        Save benchmark results to a JSON file.
        
        Args:
            results: Benchmark results to save
            
        Returns:
            Path to the saved results file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_results_{timestamp}.json"
        filepath = self.output_dir / filename
        
        # Convert results to serializable format
        if isinstance(results, dict):
            # Dictionary of results by fractal type
            serialized = {
                fractal_type: [asdict(r) for r in result_list]
                for fractal_type, result_list in results.items()
            }
        else:
            # List of results
            serialized = [asdict(r) for r in results]
        
        # Add metadata
        data = {
            "timestamp": datetime.now().isoformat(),
            "system_info": self.system_info,
            "results": serialized
        }
        
        # Save to file
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
            
        self.logger.info(f"Benchmark results saved to {filepath}")
        return str(filepath)
    
    def compare_with_baseline(self, 
                             current_results: Union[List[BenchmarkResult], Dict[str, List[BenchmarkResult]]],
                             baseline_file: Optional[str] = None,
                             threshold_pct: float = 20) -> Dict[str, Any]:
        """
        Compare current benchmark results with a baseline.
        
        Args:
            current_results: Current benchmark results
            baseline_file: Path to baseline results file, or None to use the most recent
            threshold_pct: Percentage threshold for regression detection
            
        Returns:
            Dictionary with comparison results
        """
        # Find baseline file if not specified
        if baseline_file is None:
            baseline_files = list(self.output_dir.glob("baseline_*.json"))
            if not baseline_files:
                self.logger.warning("No baseline file found for comparison")
                return {"error": "No baseline file found"}
            
            # Use the most recent baseline
            baseline_file = str(sorted(baseline_files, key=lambda f: f.stat().st_mtime, reverse=True)[0])
            
        # Load baseline data
        try:
            with open(baseline_file, "r") as f:
                baseline_data = json.load(f)
                
            # Convert baseline results to dictionary by (fractal_type, params_tuple, resolution_tuple)
            baseline_lookup = {}
            
            # Handle different baseline formats
            baseline_results = baseline_data.get("results", {})
            if isinstance(baseline_results, dict):
                # Dictionary of results by fractal type
                for fractal_type, results in baseline_results.items():
                    for result in results:
                        params_tuple = self._params_to_tuple(result["parameters"])
                        resolution_tuple = tuple(result["resolution"])
                        key = (fractal_type, params_tuple, resolution_tuple)
                        baseline_lookup[key] = result
            else:
                # List of results
                for result in baseline_results:
                    fractal_type = result["fractal_type"]
                    params_tuple = self._params_to_tuple(result["parameters"])
                    resolution_tuple = tuple(result["resolution"])
                    key = (fractal_type, params_tuple, resolution_tuple)
                    baseline_lookup[key] = result
                    
            # Compare current results with baseline
            comparisons = []
            regressions = []
            improvements = []
            
            # Process current results
            if isinstance(current_results, dict):
                # Dictionary of results by fractal type
                all_results = []
                for fractal_type, results in current_results.items():
                    all_results.extend(results)
            else:
                # List of results
                all_results = current_results
                
            # Compare each result with baseline
            for result in all_results:
                fractal_type = result.fractal_type
                params_tuple = self._params_to_tuple(result.parameters)
                resolution_tuple = result.resolution
                key = (fractal_type, params_tuple, resolution_tuple)
                
                if key in baseline_lookup:
                    baseline = baseline_lookup[key]
                    
                    # Calculate differences
                    duration_diff_pct = ((result.duration_ms - baseline["duration_ms"]) / 
                                       baseline["duration_ms"] * 100)
                    memory_diff_pct = ((result.memory_usage_mb - baseline["memory_usage_mb"]) / 
                                      baseline["memory_usage_mb"] * 100 if baseline["memory_usage_mb"] else 0)
                    
                    comparison = {
                        "fractal_type": fractal_type,
                        "parameters": result.parameters,
                        "resolution": resolution_tuple,
                        "current_duration_ms": result.duration_ms,
                        "baseline_duration_ms": baseline["duration_ms"],
                        "duration_diff_pct": duration_diff_pct,
                        "current_memory_mb": result.memory_usage_mb,
                        "baseline_memory_mb": baseline["memory_usage_mb"],
                        "memory_diff_pct": memory_diff_pct
                    }
                    
                    comparisons.append(comparison)
                    
                    # Check for regressions
                    if duration_diff_pct > threshold_pct:
                        regressions.append({
                            **comparison,
                            "type": "performance",
                            "regression_severity": "high" if duration_diff_pct > threshold_pct * 2 else "medium"
                        })
                    
                    if memory_diff_pct > threshold_pct:
                        regressions.append({
                            **comparison,
                            "type": "memory",
                            "regression_severity": "high" if memory_diff_pct > threshold_pct * 2 else "medium"
                        })
                        
                    # Check for improvements
                    if duration_diff_pct < -threshold_pct:
                        improvements.append({
                            **comparison,
                            "type": "performance",
                            "improvement_magnitude": "high" if duration_diff_pct < -threshold_pct * 2 else "medium"
                        })
                        
                    if memory_diff_pct < -threshold_pct:
                        improvements.append({
                            **comparison,
                            "type": "memory",
                            "improvement_magnitude": "high" if memory_diff_pct < -threshold_pct * 2 else "medium"
                        })
                        
            # Generate comparison report
            report = {
                "timestamp": datetime.now().isoformat(),
                "baseline_file": baseline_file,
                "total_benchmarks": len(all_results),
                "matched_with_baseline": len(comparisons),
                "regressions": {
                    "count": len(regressions),
                    "details": regressions
                },
                "improvements": {
                    "count": len(improvements),
                    "details": improvements
                },
                "all_comparisons": comparisons
            }
            
            return report
        except Exception as e:
            self.logger.error(f"Error comparing with baseline: {e}")
            return {"error": f"Error comparing with baseline: {str(e)}"}
    
    def _params_to_tuple(self, params: Dict[str, Any]) -> Tuple:
        """
        Convert parameters dictionary to a hashable tuple.
        
        Args:
            params: Parameters dictionary
            
        Returns:
            Tuple representation of parameters
        """
        return tuple(sorted((k, str(v)) for k, v in params.items()))
    
    def set_as_baseline(self, results: Union[List[BenchmarkResult], Dict[str, List[BenchmarkResult]]]) -> str:
        """
        Save benchmark results as the new baseline.
        
        Args:
            results: Benchmark results to use as baseline
            
        Returns:
            Path to the saved baseline file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"baseline_{timestamp}.json"
        filepath = self.output_dir / filename
        
        # Convert results to serializable format
        if isinstance(results, dict):
            # Dictionary of results by fractal type
            serialized = {
                fractal_type: [asdict(r) for r in result_list]
                for fractal_type, result_list in results.items()
            }
        else:
            # List of results
            serialized = [asdict(r) for r in results]
        
        # Add metadata
        data = {
            "timestamp": datetime.now().isoformat(),
            "system_info": self.system_info,
            "results": serialized
        }
        
        # Save to file
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
            
        self.logger.info(f"Baseline set and saved to {filepath}")
        return str(filepath)
    
    def generate_performance_report(self, 
                                 results: Union[List[BenchmarkResult], Dict[str, List[BenchmarkResult]]],
                                 output_file: Optional[str] = None) -> str:
        """
        Generate a detailed performance report with visualizations.
        
        Args:
            results: Benchmark results to include in the report
            output_file: Path to save the report, or None for default
            
        Returns:
            Path to the saved report file
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = str(self.output_dir / f"performance_report_{timestamp}.html")
            
        # Process results into a flat list
        if isinstance(results, dict):
            # Dictionary of results by fractal type
            all_results = []
            for fractal_type, result_list in results.items():
                all_results.extend(result_list)
        else:
            # List of results
            all_results = results
            
        # Group results by fractal type
        grouped_results = {}
        for result in all_results:
            if result.fractal_type not in grouped_results:
                grouped_results[result.fractal_type] = []
            grouped_results[result.fractal_type].append(result)
            
        # Generate HTML report
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html lang='en'>")
        html.append("<head>")
        html.append("  <meta charset='UTF-8'>")
        html.append("  <meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        html.append("  <title>Fractal Performance Report</title>")
        html.append("  <style>")
        html.append("    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #333; }")
        html.append("    h1, h2, h3 { color: #0066cc; }")
        html.append("    table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }")
        html.append("    th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }")
        html.append("    th { background-color: #f2f2f2; }")
        html.append("    tr:hover { background-color: #f5f5f5; }")
        html.append("    .chart { width: 100%; height: 400px; margin-bottom: 30px; }")
        html.append("    .summary { background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin-bottom: 20px; }")
        html.append("    .system-info { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }")
        html.append("    .metric { font-weight: bold; }")
        html.append("  </style>")
        html.append("  <script src='https://cdn.jsdelivr.net/npm/chart.js'></script>")
        html.append("</head>")
        html.append("<body>")
        
        # Header and system information
        html.append("  <h1>Fractal Rendering Performance Report</h1>")
        html.append(f"  <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
        
        html.append("  <h2>System Information</h2>")
        html.append("  <div class='system-info'>")
        html.append(f"    <div><span class='metric'>CPU:</span> {self.system_info['cpu']['brand']}</div>")
        html.append(f"    <div><span class='metric'>Cores:</span> {self.system_info['cpu']['cores_logical']} logical, {self.system_info['cpu']['cores_physical']} physical</div>")
        html.append(f"    <div><span class='metric'>Memory:</span> {self.system_info['memory']['total_gb']} GB total</div>")
        html.append(f"    <div><span class='metric'>GPU:</span> {self.system_info['gpu']}</div>")
        html.append(f"    <div><span class='metric'>Platform:</span> {self.system_info['platform']}</div>")
        html.append(f"    <div><span class='metric'>Python:</span> {self.system_info['python_version'].split()[0]}</div>")
        html.append("  </div>")
        
        # Summary of results
        html.append("  <h2>Summary</h2>")
        html.append("  <div class='summary'>")
        html.append(f"    <p><span class='metric'>Total benchmarks:</span> {len(all_results)}</p>")
        html.append(f"    <p><span class='metric'>Fractal types tested:</span> {', '.join(grouped_results.keys())}</p>")
        
        # Calculate average render times by fractal type
        avg_times = {}
        for fractal_type, results in grouped_results.items():
            avg_times[fractal_type] = sum(r.duration_ms for r in results) / len(results)
            
        html.append("    <p><span class='metric'>Average render times:</span></p>")
        html.append("    <ul>")
        for fractal_type, avg_time in avg_times.items():
            html.append(f"      <li>{fractal_type}: {avg_time:.2f} ms</li>")
        html.append("    </ul>")
        html.append("  </div>")
        
        # Performance charts
        html.append("  <h2>Performance by Fractal Type</h2>")
        
        # Create a chart for each fractal type
        chart_id = 0
        for fractal_type, results in grouped_results.items():
            chart_id += 1
            canvas_id = f"chart{chart_id}"
            html.append(f"  <h3>{fractal_type}</h3>")
            html.append(f"  <div class='chart'><canvas id='{canvas_id}'></canvas></div>")
            
            # Prepare chart data
            labels = []
            durations = []
            memory_usages = []
            
            for result in results:
                # Create label based on parameters and resolution
                param_str = ", ".join(f"{k}={v}" for k, v in result.parameters.items())
                resolution_str = f"{result.resolution[0]}x{result.resolution[1]}"
                label = f"{resolution_str}, {param_str}"
                
                labels.append(label)
                durations.append(result.duration_ms)
                memory_usages.append(result.memory_usage_mb)
            
            # Add chart JavaScript
            html.append("  <script>")
            html.append(f"    const ctx{chart_id} = document.getElementById('{canvas_id}').getContext('2d');")
            html.append(f"    new Chart(ctx{chart_id}, {{")
            html.append("      type: 'bar',")
            html.append("      data: {")
            html.append(f"        labels: {str(labels).replace('\'', '\\\'')},")
            html.append("        datasets: [{")
            html.append("          label: 'Render Time (ms)',")
            html.append("          backgroundColor: 'rgba(54, 162, 235, 0.5)',")
            html.append("          borderColor: 'rgba(54, 162, 235, 1)',")
            html.append("          borderWidth: 1,")
            html.append(f"          data: {str(durations)}")
            html.append("        }, {")
            html.append("          label: 'Memory Usage (MB)',")
            html.append("          backgroundColor: 'rgba(255, 99, 132, 0.5)',")
            html.append("          borderColor: 'rgba(255, 99, 132, 1)',")
            html.append("          borderWidth: 1,")
            html.append(f"          data: {str(memory_usages)}")
            html.append("        }]")
            html.append("      },")
            html.append("      options: {")
            html.append("        responsive: true,")
            html.append("        scales: {")
            html.append("          y: {")
            html.append("            beginAtZero: true")
            html.append("          }")
            html.append("        },")
            html.append("        plugins: {")
            html.append("          legend: {")
            html.append("            position: 'top',")
            html.append("          },")
            html.append("          title: {")
            html.append("            display: true,")
            html.append(f"            text: '{fractal_type} Performance'")
            html.append("          }")
            html.append("        }")
            html.append("      }")
            html.append("    });")
            html.append("  </script>")
            
            # Detailed results table
            html.append("  <h3>Detailed Results</h3>")
            html.append("  <table>")
            html.append("    <tr>")
            html.append("      <th>Resolution</th>")
            html.append("      <th>Parameters</th>")
            html.append("      <th>Render Time (ms)</th>")
            html.append("      <th>Memory Usage (MB)</th>")
            html.append("      <th>CPU Usage (%)</th>")
            if fractal_type in ["MandelbrotSet", "JuliaSet"]:
                html.append("      <th>Avg. Iterations</th>")
            html.append("    </tr>")
            
            for result in results:
                param_str = ", ".join(f"{k}={v}" for k, v in result.parameters.items())
                resolution_str = f"{result.resolution[0]}x{result.resolution[1]}"
                
                html.append("    <tr>")
                html.append(f"      <td>{resolution_str}</td>")
                html.append(f"      <td>{param_str}</td>")
                html.append(f"      <td>{result.duration_ms:.2f}</td>")
                html.append(f"      <td>{result.memory_usage_mb:.2f}</td>")
                html.append(f"      <td>{result.cpu_usage_percent:.1f}</td>")
                if fractal_type in ["MandelbrotSet", "JuliaSet"]:
                    html.append(f"      <td>{result.iterations_per_pixel:.1f}</td>")
                html.append("    </tr>")
                
            html.append("  </table>")
        
        # End of HTML
        html.append("</body>")
        html.append("</html>")
        
        # Write report to file
        with open(output_file, "w") as f:
            f.write("\n".join(html))
            
        self.logger.info(f"Performance report saved to {output_file}")
        return output_file


def main():
    """Main function to run benchmarks from command line."""
    parser = argparse.ArgumentParser(description="Benchmark fractal rendering algorithms")
    parser.add_argument("--output-dir", default="./benchmark_results", 
                        help="Directory to store benchmark results")
    parser.add_argument("--fractal-type", choices=["mandelbrot", "julia", "lsystem", "all"],
                        default="all", help="Fractal type to benchmark")
    parser.add_argument("--set-baseline", action="store_true",
                        help="Set benchmark results as the new baseline")
    parser.add_argument("--compare-baseline", action="store_true",
                        help="Compare results with existing baseline")
    parser.add_argument("--generate-report", action="store_true",
                        help="Generate a detailed HTML performance report")
    parser.add_argument("--threshold", type=float, default=20,
                        help="Percentage threshold for regression detection")
    parser.add_argument("--quick", action="store_true",
                        help="Run a quicker version of benchmarks with fewer parameters")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create benchmark instance
    benchmark = FractalBenchmark(output_dir=args.output_dir)
    
    # Run benchmarks
    results = {}
    
    if args.quick:
        # Quick benchmarks with minimal parameters
        if args.fractal_type in ["mandelbrot", "all"]:
            results["MandelbrotSet"] = benchmark.benchmark_mandelbrot(
                resolutions=[(512, 512)],
                max_iterations=[100],
                zoom_levels=[1.0],
                repeats=2
            )
            
        if args.fractal_type in ["julia", "all"]:
            results["JuliaSet"] = benchmark.benchmark_julia(
                resolutions=[(512, 512)],
                max_iterations=[100],
                c_values=[(-0.7, 0.27)],
                repeats=2
            )
            
        if args.fractal_type in ["lsystem", "all"]:
            results["LSystem"] = benchmark.benchmark_lsystem(
                resolutions=[(512, 512)],
                iterations=[3],
                systems=["dragon"],
                repeats=2
            )
    else:
        # Full benchmarks
        if args.fractal_type == "mandelbrot":
            results["MandelbrotSet"] = benchmark.benchmark_mandelbrot()
        elif args.fractal_type == "julia":
            results["JuliaSet"] = benchmark.benchmark_julia()
        elif args.fractal_type == "lsystem":
            results["LSystem"] = benchmark.benchmark_lsystem()
        else:  # "all"
            results = benchmark.benchmark_all()
    
    # Save results
    results_file = benchmark.save_results(results)
    print(f"Benchmark results saved to {results_file}")
    
    # Set as baseline if requested
    if args.set_baseline:
        baseline_file = benchmark.set_as_baseline(results)
        print(f"Results set as new baseline in {baseline_file}")
    
    # Compare with baseline if requested
    if args.compare_baseline:
        comparison = benchmark.compare_with_baseline(results, threshold_pct=args.threshold)
        if "error" in comparison:
            print(f"Error comparing with baseline: {comparison['error']}")
        else:
            print(f"Compared with baseline: {comparison['matched_with_baseline']} matching benchmarks")
            print(f"Found {comparison['regressions']['count']} regressions and {comparison['improvements']['count']} improvements")
            
            # Print details of regressions
            if comparison['regressions']['count'] > 0:
                print("\nRegressions:")
                for i, regression in enumerate(comparison['regressions']['details'], 1):
                    print(f"  {i}. {regression['fractal_type']} ({regression['type']}): "
                          f"{regression['duration_diff_pct']:.1f}% slower")
    
    # Generate report if requested
    if args.generate_report:
        report_file = benchmark.generate_performance_report(results)
        print(f"Performance report saved to {report_file}")
    

if __name__ == "__main__":
    main()