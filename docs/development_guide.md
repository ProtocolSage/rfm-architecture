# RFM Architecture Development Guide

This guide provides information for developers who want to extend or modify the RFM Architecture visualization system.

## Development Environment Setup

### Setting Up the Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/username/RFM-Architecture.git
   cd RFM-Architecture
   ```

2. Install development dependencies:
   ```bash
   poetry install --no-root --with dev
   ```

3. Set up pre-commit hooks:
   ```bash
   poetry run pre-commit install
   ```

### Running Tests

Run the test suite with pytest:

```bash
poetry run pytest
```

Run tests with coverage:

```bash
poetry run pytest --cov=rfm
```

### Code Style

This project follows PEP 8 style guidelines. Code formatting is enforced using Black and isort:

```bash
# Format code
poetry run black rfm tests

# Sort imports
poetry run isort rfm tests
```

## Project Structure

```
RFM-Architecture/
├── config.yaml              # Default configuration
├── docs/                    # Documentation
├── pyproject.toml           # Project metadata and dependencies
├── rfm/                     # Main package
│   ├── __init__.py          # Package initialization
│   ├── cli.py               # Command-line interface
│   ├── config/              # Configuration handling
│   │   ├── __init__.py
│   │   ├── settings.py      # Configuration dataclasses
│   │   └── validator.py     # Configuration validation
│   ├── core/                # Core functionality
│   │   ├── __init__.py
│   │   ├── fractal.py       # Fractal generators
│   │   ├── morphogen.py     # Morphogenic pattern generators
│   │   └── network.py       # Network structure generators
│   ├── main.py              # Main application entry point
│   └── viz/                 # Visualization
│       ├── __init__.py
│       ├── animation.py     # Basic animation functions
│       ├── animation_engine.py  # Advanced animation engine
│       ├── components.py    # Component renderers
│       ├── effects.py       # Visual effects
│       └── layout.py        # Layout engine
├── run_animation.py         # Animation script
├── run_viz.py               # Visualization script
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── test_cli.py          # CLI tests
│   ├── test_config.py       # Configuration tests
│   ├── test_fractal.py      # Fractal generator tests
│   └── test_viz.py          # Visualization tests
└── validate_config.py       # Configuration validation script
```

## Extension Points

The RFM Architecture system is designed to be extensible. Here are the main extension points:

### Adding a New Fractal Type

To add a new fractal type:

1. Create a new class in `rfm/core/fractal.py` that inherits from `FractalBase`:

   ```python
   class NewFractal(FractalBase):
       def __init__(self, config: Dict[str, Any]):
           super().__init__(config)
           # Initialize your fractal parameters
           
       def generate(self, width: int, height: int) -> np.ndarray:
           # Implement fractal generation logic
           return data
           
       def plot(self, ax: plt.Axes, x: float, y: float, width: float, height: float):
           # Implement fractal plotting logic
           # This method is called to render the fractal on the given axes
   ```

2. Register your fractal in the `create_fractal` factory function:

   ```python
   def create_fractal(config: Dict[str, Any]) -> FractalBase:
       fractal_type = config.get("type", "l_system")
       
       if fractal_type == "new_fractal":
           return NewFractal(config.get("parameters", {}))
       elif fractal_type == "l_system":
           # existing code...
   ```

3. Update the configuration schema to include your new fractal type:
   - Edit `rfm/config/validator.py` to validate the new fractal type and its parameters
   - Update `docs/config_schema.md` with documentation for the new fractal type

4. Add tests for your new fractal type in `tests/test_fractal.py`.

### Adding a New Animation Effect

To add a new animation effect:

1. Create a new class in `rfm/viz/animation_engine.py` that inherits from `AnimationSequence`:

   ```python
   class NewEffect(AnimationSequence):
       def __init__(self, **kwargs):
           super().__init__(**kwargs)
           # Initialize your effect parameters
           
       def render_frame(self, time: float, layout: ArchitectureLayout, ax: plt.Axes):
           # Implement frame rendering logic
           # This method is called to render a frame at the specified time
   ```

2. Use your new effect in animations:

   ```python
   from rfm.viz.animation_engine import AnimationTimeline, NewEffect
   
   timeline = AnimationTimeline(fps=60, duration=5000)
   timeline.add_sequence(
       NewEffect(
           # Your effect parameters
           start_time=1000,
           duration=2000
       )
   )
   ```

3. Add tests for your new animation effect in `tests/test_viz.py`.

### Adding a New Visual Component

To add a new visual component for the architecture:

1. Extend the `ComponentRenderer` class in `rfm/viz/components.py` to handle your new component type.

2. Update the `ArchitectureLayout` class in `rfm/viz/layout.py` to include your new component type.

3. Add configuration schema updates and tests as needed.

### Extending the Configuration System

To add new configuration options:

1. Update the `Config` dataclass in `rfm/config/settings.py`.

2. Add validation logic for the new configuration options in `rfm/config/validator.py`.

3. Update the configuration schema documentation in `docs/config_schema.md`.

## Contributing Guidelines

### Commit Message Guidelines

Follow these guidelines for commit messages:

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests after the first line

Example:
```
Add Julia set fractal generator

- Implement JuliaSet class with vectorized computation
- Add configuration validation for Julia parameters
- Add tests for Julia set generation
- Update documentation with Julia set examples

Fixes #123
```

### Pull Request Process

1. Fork the repository and create your branch from `main`.
2. Update the documentation to reflect any changes.
3. Write tests for your changes.
4. Ensure all tests pass and the code follows style guidelines.
5. Submit a pull request with a clear description of the changes.

### Versioning

This project follows [Semantic Versioning](https://semver.org/).

- MAJOR version for incompatible API changes
- MINOR version for new functionality in a backwards compatible manner
- PATCH version for backwards compatible bug fixes

## Performance Considerations

### Fractal Generation Performance

Fractal generation can be computationally intensive. Here are some tips for optimizing performance:

1. Use vectorized operations with NumPy for mathematical computations
2. Cache intermediate results when possible
3. Consider using Numba for JIT compilation of performance-critical functions

Example of using Numba:

```python
import numba

@numba.jit(nopython=True, parallel=True)
def compute_fractal(h, w, max_iter, c_real, c_imag):
    # Your optimized fractal computation code
    return result
```

### Visualization Performance

For visualization performance:

1. Use the `cmap` parameter to render fractals using colormaps instead of RGB arrays
2. Avoid rendering extremely high-resolution fractals during interactive use
3. Consider using a dedicated rendering thread for animations

### Animation Performance

Animation performance tips:

1. Reduce the number of frames per second for complex animations
2. Use smaller output dimensions for animated GIFs
3. Use the HTML output format for interactive web viewing of complex animations

## Debugging

### Debugging Visualization Issues

For visualization issues:

1. Enable matplotlib debugging:
   ```python
   import matplotlib
   matplotlib.set_loglevel("debug")
   ```

2. Use the `--debug` command-line option:
   ```bash
   poetry run rfm-viz --debug
   ```

3. Export intermediate rendering steps:
   ```python
   layout.render_debug_info(ax, output_dir="debug")
   ```

### Debugging Animation Issues

For animation issues:

1. Render individual frames:
   ```python
   timeline.render_debug_frames(output_dir="debug_frames")
   ```

2. Use a lower frame rate for testing:
   ```python
   timeline = AnimationTimeline(fps=10)  # Use 10 FPS for debugging
   ```

3. Enable verbose logging:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

## Further Resources

- [Matplotlib Documentation](https://matplotlib.org/stable/contents.html)
- [NumPy Documentation](https://numpy.org/doc/stable/)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Python Packaging User Guide](https://packaging.python.org/en/latest/)