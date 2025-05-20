#!/usr/bin/env python3
"""
RFM Architecture Benchmark Runner

This script provides a convenient interface to run performance benchmarks
for the RFM Architecture fractals, generate reports, and track performance
over time.
"""

import os
import sys
import argparse
import logging
import time
from datetime import datetime
from pathlib import Path

from rfm.benchmarks.fractal_benchmark import FractalBenchmark


def setup_logging():
    """Configure logging for the benchmark runner."""
    log_dir = Path("./logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"benchmark_run_{timestamp}.log"
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger("benchmark_runner")


def main():
    """Main function for the benchmark runner."""
    parser = argparse.ArgumentParser(
        description="Run performance benchmarks for RFM Architecture fractals"
    )
    
    # Benchmark selection
    parser.add_argument(
        "--fractal-type", 
        choices=["mandelbrot", "julia", "lsystem", "all"],
        default="all", 
        help="Type of fractal to benchmark"
    )
    
    # Benchmark profile
    parser.add_argument(
        "--profile",
        choices=["quick", "standard", "comprehensive"],
        default="standard",
        help="Benchmark profile to use"
    )
    
    # Output options
    parser.add_argument(
        "--output-dir",
        default="./benchmark_results",
        help="Directory to store benchmark results"
    )
    
    # Actions
    parser.add_argument(
        "--set-baseline",
        action="store_true",
        help="Set this run as the new performance baseline"
    )
    
    parser.add_argument(
        "--compare-baseline",
        action="store_true",
        help="Compare results to the current baseline"
    )
    
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate an HTML performance report"
    )
    
    # Advanced options
    parser.add_argument(
        "--threshold",
        type=float,
        default=20.0,
        help="Percentage threshold for regression detection"
    )
    
    parser.add_argument(
        "--repeats",
        type=int,
        default=3,
        help="Number of repetitions for each benchmark"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    logger.info(f"Starting benchmark run with profile: {args.profile}")
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize benchmark suite
    benchmark = FractalBenchmark(output_dir=str(output_dir))
    
    # Configure benchmark parameters based on profile
    if args.profile == "quick":
        # Quick profile - minimal parameters for faster testing
        resolutions = [(512, 512)]
        max_iterations = [100]
        zoom_levels = [1.0]
        c_values = [(-0.7, 0.27)]
        l_iterations = [3]
        l_systems = ["dragon"]
        repeats = 2
    elif args.profile == "comprehensive":
        # Comprehensive profile - extensive parameter testing
        resolutions = [(512, 512), (1024, 1024), (2048, 2048)]
        max_iterations = [100, 500, 1000, 2000]
        zoom_levels = [1.0, 10.0, 100.0, 1000.0]
        c_values = [
            (-0.7, 0.27),
            (-0.8, 0.156),
            (-0.4, 0.6),
            (-0.835, -0.2321),
            (-0.70176, -0.3842)
        ]
        l_iterations = [3, 4, 5, 6]
        l_systems = ["dragon", "tree", "sierpinski", "koch"]
        repeats = 5
    else:  # standard profile
        # Standard profile - balanced parameter testing
        resolutions = [(512, 512), (1024, 1024)]
        max_iterations = [100, 500, 1000]
        zoom_levels = [1.0, 10.0, 100.0]
        c_values = [(-0.7, 0.27), (-0.8, 0.156), (-0.4, 0.6)]
        l_iterations = [3, 4, 5]
        l_systems = ["dragon", "tree", "sierpinski"]
        repeats = args.repeats
    
    # Run benchmarks
    results = {}
    start_time = time.time()
    
    try:
        if args.fractal_type in ["mandelbrot", "all"]:
            logger.info("Running Mandelbrot set benchmarks")
            results["MandelbrotSet"] = benchmark.benchmark_mandelbrot(
                resolutions=resolutions,
                max_iterations=max_iterations,
                zoom_levels=zoom_levels,
                repeats=repeats
            )
            
        if args.fractal_type in ["julia", "all"]:
            logger.info("Running Julia set benchmarks")
            results["JuliaSet"] = benchmark.benchmark_julia(
                resolutions=resolutions,
                max_iterations=max_iterations,
                c_values=c_values,
                repeats=repeats
            )
            
        if args.fractal_type in ["lsystem", "all"]:
            logger.info("Running L-System benchmarks")
            results["LSystem"] = benchmark.benchmark_lsystem(
                resolutions=resolutions,
                iterations=l_iterations,
                systems=l_systems,
                repeats=repeats
            )
            
        # Calculate total benchmarking time
        elapsed_time = time.time() - start_time
        logger.info(f"All benchmarks completed in {elapsed_time:.2f} seconds")
        
        # Save results
        results_file = benchmark.save_results(results)
        logger.info(f"Benchmark results saved to {results_file}")
        
        # Set as baseline if requested
        if args.set_baseline:
            baseline_file = benchmark.set_as_baseline(results)
            logger.info(f"Results set as new baseline in {baseline_file}")
        
        # Compare with baseline if requested
        if args.compare_baseline:
            logger.info(f"Comparing results with baseline (threshold: {args.threshold}%)")
            comparison = benchmark.compare_with_baseline(
                results, 
                threshold_pct=args.threshold
            )
            
            if "error" in comparison:
                logger.error(f"Error comparing with baseline: {comparison['error']}")
            else:
                logger.info(
                    f"Comparison complete: {comparison['matched_with_baseline']} matching benchmarks, "
                    f"{comparison['regressions']['count']} regressions, "
                    f"{comparison['improvements']['count']} improvements"
                )
                
                # Log details of regressions
                if comparison['regressions']['count'] > 0:
                    logger.warning("Performance regressions detected:")
                    for i, regression in enumerate(comparison['regressions']['details'], 1):
                        logger.warning(
                            f"  {i}. {regression['fractal_type']} ({regression['type']}): "
                            f"{regression['duration_diff_pct']:.1f}% slower"
                        )
        
        # Generate report if requested
        if args.report:
            logger.info("Generating performance report")
            report_file = benchmark.generate_performance_report(results)
            logger.info(f"Performance report saved to {report_file}")
            
        logger.info("Benchmark run completed successfully")
        return 0
        
    except Exception as e:
        logger.exception(f"Error during benchmark run: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())