# RFM Architecture User Guide

This guide provides detailed instructions for using the RFM Architecture visualization system.

## Installation

### Prerequisites

Before installing, ensure you have:

- Python 3.8 or higher
- Poetry (for dependency management)
- Matplotlib 3.5.0 or higher
- NumPy 1.20.0 or higher

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/username/RFM-Architecture.git
   cd RFM-Architecture
   ```

2. Install dependencies using Poetry:
   ```bash
   poetry install --no-root
   ```

3. Verify installation:
   ```bash
   poetry run python -c "import rfm; print(rfm.__version__)"
   ```

## Basic Usage

### Generating a Visualization

To generate a basic visualization:

```bash
poetry run rfm-viz --output diagram.png
```

This will create a visualization using the default configuration in `config.yaml`.

### Command Line Options

The visualization tool supports several command-line options:

```bash
poetry run rfm-viz --help
```

Common options include:

- `--output FILENAME`: Output filename
- `--format FORMAT`: Output format (png, svg, pdf)
- `--config CONFIG`: Path to configuration file
- `--dpi DPI`: Resolution for raster formats
- `--fractal FRACTAL`: Use an alternative fractal type from config
- `--theme THEME`: Visual theme (default, dark, light, neon)
- `--width WIDTH`: Output width in pixels
- `--height HEIGHT`: Output height in pixels

### Customizing the Visualization

To customize the visualization, you can either:

1. Edit the `config.yaml` file
2. Create a custom configuration file
3. Use command-line options to override specific settings

Example with custom configuration:

```bash
poetry run rfm-viz --config custom_config.yaml --output custom_diagram.svg --format svg
```

## Animation

### Creating Animations

To create an animation:

```bash
poetry run python animate_rfm.py --output animation.gif
```

For Windows users, a batch file is provided:

```bash
run_animation.bat
```

### Animation Options

Animation customization options:

```bash
python animate_rfm.py --help
```

Key options include:

- `--output FILENAME`: Output filename
- `--format FORMAT`: Output format (gif, mp4, webm, html)
- `--duration SECONDS`: Animation duration in seconds
- `--fps FPS`: Frames per second
- `--config CONFIG`: Path to configuration file
- `--width WIDTH`: Output width in pixels
- `--height HEIGHT`: Output height in pixels

## Configuration Validation

To validate your configuration file:

```bash
# On Linux/macOS
python validate_config.py [config_file]

# On Windows
validate_config.bat [config_file]
```

This will check that your configuration is valid according to the expected schema.

## Working with Fractals

### Switching Fractal Types

The system supports multiple fractal types:

```bash
# Use a Mandelbrot set
poetry run rfm-viz --fractal-type mandelbrot

# Use an L-System
poetry run rfm-viz --fractal-type l_system

# Use a Julia set
poetry run rfm-viz --fractal-type julia

# Use a Cantor dust
poetry run rfm-viz --fractal-type cantor
```

### Using Predefined Fractal Presets

You can use predefined fractal presets from the configuration:

```bash
poetry run rfm-viz --fractal julia_douady_rabbit
```

### Customizing Fractal Parameters

For detailed fractal customization, edit the parameters in the configuration file:

```yaml
fractals:
  type: "julia"
  parameters:
    c_real: -0.7
    c_imag: 0.27
    center: [0, 0]
    zoom: 1.5
    max_iter: 100
    cmap: "viridis"
```

## Using the API

### Basic API Usage

You can use the RFM Architecture as a library in your own Python code:

```python
from rfm.config.settings import ConfigLoader
from rfm.viz.layout import ArchitectureLayout
import matplotlib.pyplot as plt

# Load configuration
config = ConfigLoader.from_file("config.yaml")

# Create layout
layout = ArchitectureLayout(config)

# Create figure
fig, ax = plt.subplots(figsize=(10, 10))

# Render architecture
layout.render(ax)

# Show or save the result
plt.savefig("my_diagram.png", dpi=300)
```

### Animation API

For programmatic animation creation:

```python
from rfm.config.settings import ConfigLoader
from rfm.viz.animation_engine import AnimationTimeline, BroadcastSequence, create_animation

# Load configuration
config = ConfigLoader.from_file("config.yaml")

# Create animation
timeline = create_animation(config)

# Add custom sequences
timeline.add_sequence(
    BroadcastSequence(
        source="cif",
        targets=["perception", "knowledge"],
        start_time=1000,
        duration=2000,
        color="#00c2c7"
    )
)

# Render the animation
timeline.render("custom_animation.gif", format="gif")
```

## Troubleshooting

### Common Issues

#### Missing Dependencies

If you encounter errors about missing dependencies:

```bash
poetry install --no-root
```

#### Display Issues

If you're having issues with display (particularly on WSL):

1. Ensure you have a proper X server setup
2. Use the `--no-display` option to save directly to file without showing
3. Try using a different backend: `export MPLBACKEND=Agg`

#### Configuration Errors

If your configuration is invalid:

1. Run the validation script:
   ```bash
   python validate_config.py config.yaml
   ```
2. Check the error messages and fix the identified issues
3. Consult the configuration schema documentation

#### Animation Issues

If animations are not rendering correctly:

1. Check that you have FFmpeg installed for video formats
2. Try reducing the FPS or resolution
3. Use GIF format which has better compatibility

## Advanced Features

### Integration with Other Tools

You can integrate RFM Architecture with other visualization tools:

```python
# Export to JSON for web visualization
from rfm.export import export_json
export_json(config, "architecture.json")

# Generate code for D3.js visualization
from rfm.export import export_d3
export_d3(config, "architecture.js")
```

### Custom Fractal Creation

You can define custom fractals by extending the fractal base classes:

```python
from rfm.core.fractal import FractalBase
import numpy as np

class CustomFractal(FractalBase):
    def __init__(self, config):
        super().__init__(config)
        # Custom initialization
        
    def generate(self, width, height):
        # Custom fractal generation logic
        data = np.zeros((height, width))
        # Your algorithm here
        return data
```

### Custom Animation Effects

For custom animation effects:

```python
from rfm.viz.animation_engine import AnimationSequence

class CustomEffect(AnimationSequence):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Custom initialization
        
    def render_frame(self, time, layout, ax):
        # Custom frame rendering logic
        pass
```

## Resources

- [Configuration Schema](config_schema.md)
- [Fractal Library](fractal_library.md)
- [Animation System](animation_system.md)
- [Architecture Overview](architecture.md)
- [API Reference](api_reference.md)