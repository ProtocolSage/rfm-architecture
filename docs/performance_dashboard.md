# Performance Dashboard

## Overview

The Performance Dashboard is a real-time monitoring and visualization system for the RFM Architecture. It enables developers and users to observe, analyze, and optimize the performance of fractal rendering operations across different components of the system.

## Architecture

The dashboard is built using Streamlit for the frontend visualization and integrates with a comprehensive performance tracking backend:

### Performance Tracker

Core component for capturing performance metrics:

```python
class PerformanceTracker:
    def __init__(self):
        self.metrics = {}
        self.history = defaultdict(list)
        self.baselines = {}
    
    def start_timer(self, metric_name: str):
        """Start timing a specific operation."""
        pass
    
    def end_timer(self, metric_name: str) -> float:
        """End timing for an operation and return elapsed time."""
        pass
    
    def track_metric(self, metric_name: str, value: float):
        """Record a specific metric value."""
        pass
    
    def get_metric(self, metric_name: str) -> Optional[float]:
        """Get the current value for a metric."""
        pass
    
    def get_history(self, metric_name: str) -> List[Tuple[datetime, float]]:
        """Get historical values for a metric."""
        pass
    
    def detect_regressions(self, threshold: float = 0.2) -> List[RegressionReport]:
        """Detect performance regressions compared to baselines."""
        pass
```

### Instrumentation Decorators

Utility decorators for easy performance tracking:

```python
def track_performance(metric_name=None):
    """Decorator to track function execution time."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            name = metric_name or f"{func.__module__}.{func.__name__}"
            tracker = get_performance_tracker()
            tracker.start_timer(name)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                tracker.end_timer(name)
        return wrapper
    return decorator
```

### Performance API

REST API endpoints for accessing performance data:

```python
@app.route('/api/performance/metrics')
def get_metrics():
    """Get current performance metrics."""
    tracker = get_performance_tracker()
    return jsonify({
        'metrics': tracker.metrics,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/performance/history/<metric_name>')
def get_metric_history(metric_name):
    """Get historical data for a specific metric."""
    tracker = get_performance_tracker()
    history = tracker.get_history(metric_name)
    return jsonify({
        'metric': metric_name,
        'history': [{'timestamp': ts.isoformat(), 'value': val} for ts, val in history]
    })
```

## Dashboard Components

The dashboard consists of several visualizations and analysis tools:

### 1. Real-time Metrics Panel

Displays current performance metrics with color-coded status indicators:

- Render Time (ms)
- FPS
- Memory Usage (MB)
- GPU Utilization (%)
- Computation Complexity

### 2. Timeline Visualization

Interactive time-series visualization of key metrics:

- Selectable metrics for comparison
- Zoom and pan capabilities
- Anomaly highlighting
- Comparison with baseline performance

### 3. Bottleneck Analyzer

Identifies performance bottlenecks through:

- Function-level timing analysis
- Component timing breakdown
- Call frequency analysis
- Execution path visualization

### 4. Resource Utilization

Visualizes system resource usage:

- CPU usage by core
- Memory allocation and garbage collection
- GPU memory and computation usage
- I/O operations and wait times

### 5. Optimization Suggestions

AI-assisted performance optimization suggestions:

- Parameter adjustments for optimal performance
- Algorithm efficiency recommendations
- Parallelization opportunities
- Memory usage optimization

## Usage Examples

### Viewing the Dashboard

```python
# Launch the dashboard in default browser
from ui.rfm_ui.performance.dashboard import launch_dashboard

# Launch with specific configuration
launch_dashboard(
    update_interval=1.0,  # Update frequency in seconds
    metrics_to_show=["render_time", "memory_usage", "fps"],
    show_bottleneck_analysis=True
)
```

### Instrumenting Code

```python
# Track performance of specific functions
from ui.rfm_ui.performance.decorators import track_performance

@track_performance()
def compute_fractal(params):
    # Computation code
    pass

# Track with custom metric name
@track_performance("mandelbrot.generation")
def generate_mandelbrot(width, height, max_iterations):
    # Generation code
    pass

# Manual performance tracking
from ui.rfm_ui.performance import get_performance_tracker

def complex_operation():
    tracker = get_performance_tracker()
    
    # Track overall operation
    tracker.start_timer("complex_operation")
    
    # Track sub-operations
    tracker.start_timer("preparation")
    # Preparation code
    tracker.end_timer("preparation")
    
    tracker.start_timer("computation")
    # Computation code
    tracker.end_timer("computation")
    
    tracker.start_timer("finalization")
    # Finalization code
    tracker.end_timer("finalization")
    
    # End overall timing
    total_time = tracker.end_timer("complex_operation")
    return total_time
```

### Accessing the API

```python
# Python client for the Performance API
import requests

def get_current_metrics():
    response = requests.get('http://localhost:8501/api/performance/metrics')
    return response.json()

def get_metric_history(metric_name):
    response = requests.get(f'http://localhost:8501/api/performance/history/{metric_name}')
    return response.json()
```

## Integration with UI

The dashboard integrates with the main UI in several ways:

1. **Embedded View**: A simplified version can be embedded directly in the main application
2. **FPS Overlay**: Real-time FPS counter in the main rendering window
3. **Status Indicators**: Performance health indicators in the application status bar
4. **Alerts**: Proactive notifications when performance degrades
5. **Suggestions**: In-context optimization suggestions based on current usage patterns

## Benefits of Performance Dashboard

1. **Visibility**: Real-time insights into system performance
2. **Diagnosis**: Quick identification of performance bottlenecks
3. **Optimization**: Data-driven approach to performance tuning
4. **Regression Detection**: Early warning of performance degradation
5. **User Experience**: Better understanding of performance impacts of parameter changes

## Future Enhancements

Planned enhancements to the Performance Dashboard include:

1. **Predictive Models**: ML-based performance prediction based on parameter settings
2. **Automated Optimization**: Smart parameter tuning for optimal performance
3. **Comparative Benchmarking**: Benchmarking against different hardware configurations
4. **Custom Alerts**: User-defined performance thresholds and notifications
5. **Extended Telemetry**: Network performance and API latency metrics