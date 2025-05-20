# RFM Architecture API Reference

This document provides a detailed reference for the RFM Architecture API.

## Module Structure

The RFM Architecture is organized into the following modules:

- `rfm.config`: Configuration handling
- `rfm.core`: Core functionality, including fractal generation
- `rfm.viz`: Visualization components and effects
- `rfm.cli`: Command-line interface tools

## Configuration Module

### `rfm.config.settings`

#### `Config`

Main configuration dataclass that holds all settings for RFM Architecture.

```python
class Config:
    """Configuration dataclass for RFM visualization."""
    
    # Properties
    layout: Dict[str, Any]
    components: Dict[str, Dict[str, Any]]
    connections: List[Dict[str, Any]]
    conscious_fields: Dict[str, Dict[str, Any]]
    fractals: Dict[str, Any]
    alternative_fractals: Dict[str, Dict[str, Any]]
    morphogen: Dict[str, Any]
    kin_graph: Dict[str, Any]
    phi_metric: Dict[str, Any]
    processing_scales: Dict[str, Dict[str, Any]]
    animation: Dict[str, Dict[str, Any]]
    styling: Dict[str, Any]
    
    # Methods
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Config:
        """Create a Config from a dictionary."""
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert Config to a dictionary."""
        
    def validate(self) -> Tuple[bool, Optional[str]]:
        """Validate the configuration."""
```

#### `ConfigLoader`

Utility class for loading and merging configuration files.

```python
class ConfigLoader:
    """Configuration loader for RFM visualization."""
    
    @classmethod
    def from_file(cls, path: Optional[Union[str, Path]] = None, validate: bool = True) -> Config:
        """Load configuration from a file."""
        
    @classmethod
    def from_files(cls, base_path: Union[str, Path], override_path: Union[str, Path], 
                  validate: bool = True) -> Config:
        """Load configuration from multiple files, merging them."""
        
    @staticmethod
    def _load_yaml(path: Union[str, Path]) -> Dict[str, Any]:
        """Load a YAML file."""
        
    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
```

### `rfm.config.validator`

#### `ValidationResult`

Class that represents the result of a configuration validation.

```python
class ValidationResult:
    """The result of a configuration validation."""
    
    # Properties
    is_valid: bool
    errors: List[ValidationError]
    
    # Methods
    def __bool__(self) -> bool:
        """Return whether the validation was successful."""
        
    def add_error(self, path: str, message: str, 
                 expected: Optional[Any] = None, received: Optional[Any] = None) -> None:
        """Add a validation error."""
        
    def combine(self, other: ValidationResult) -> ValidationResult:
        """Combine with another validation result."""
        
    def summary(self) -> str:
        """Return a summary of the validation result."""
```

#### `ValidationError`

Class that represents a single validation error.

```python
class ValidationError:
    """A single validation error."""
    
    # Properties
    path: str
    message: str
    expected: Optional[Any]
    received: Optional[Any]
    
    # Methods
    def __str__(self) -> str:
        """Return a string representation of the error."""
```

#### `ConfigValidator`

Validator for RFM Architecture configuration.

```python
class ConfigValidator:
    """Validator for RFM Architecture configuration."""
    
    @classmethod
    def validate(cls, config: Config) -> ValidationResult:
        """Validate the entire configuration."""
        
    @staticmethod
    def validate_layout(config: Config) -> ValidationResult:
        """Validate layout configuration."""
        
    @staticmethod
    def validate_components(config: Config) -> ValidationResult:
        """Validate component configurations."""
        
    @staticmethod
    def validate_connections(config: Config) -> ValidationResult:
        """Validate connection configurations."""
        
    @staticmethod
    def validate_fractals(config: Config) -> ValidationResult:
        """Validate fractal configuration."""
        
    @staticmethod
    def validate_alternative_fractals(config: Config) -> ValidationResult:
        """Validate alternative fractal configurations."""
        
    @staticmethod
    def validate_animation(config: Config) -> ValidationResult:
        """Validate animation configuration."""
        
    @staticmethod
    def validate_styling(config: Config) -> ValidationResult:
        """Validate styling configuration."""
```

## Core Module

### `rfm.core.fractal`

#### `FractalBase`

Base class for all fractal types.

```python
class FractalBase:
    """Base class for fractal generators."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration."""
        
    def generate(self, width: int, height: int) -> np.ndarray:
        """Generate fractal data."""
        
    def plot(self, ax: plt.Axes, x: float, y: float, width: float, height: float):
        """Plot the fractal on the given axes."""
```

#### `MandelbrotSet`

Mandelbrot set fractal generator.

```python
class MandelbrotSet(FractalBase):
    """Mandelbrot set fractal generator."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Mandelbrot set with the given configuration."""
        
    def generate(self, width: int, height: int) -> np.ndarray:
        """Generate Mandelbrot set data."""
        
    def _mandelbrot(self, h: int, w: int, max_iter: int) -> np.ndarray:
        """Compute the Mandelbrot set."""
```

#### `JuliaSet`

Julia set fractal generator.

```python
class JuliaSet(FractalBase):
    """Julia set fractal generator."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Julia set with the given configuration."""
        
    def generate(self, width: int, height: int) -> np.ndarray:
        """Generate Julia set data."""
        
    def _julia(self, h: int, w: int, max_iter: int, c_real: float, c_imag: float) -> np.ndarray:
        """Compute the Julia set."""
```

#### `LSystem`

L-System fractal generator.

```python
class LSystem(FractalBase):
    """L-System fractal generator."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the L-System with the given configuration."""
        
    def generate_string(self, iterations: int) -> str:
        """Generate the L-System string after the given number of iterations."""
        
    def plot(self, ax: plt.Axes, x: float, y: float, width: float, height: float):
        """Plot the L-System on the given axes."""
        
    def _turtle_interpretation(self, lstr: str, ax: plt.Axes, 
                              x: float, y: float, width: float, height: float):
        """Interpret the L-System string using turtle graphics."""
```

#### `CantorDust`

Cantor dust fractal generator.

```python
class CantorDust(FractalBase):
    """Cantor dust fractal generator."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Cantor dust with the given configuration."""
        
    def plot(self, ax: plt.Axes, x: float, y: float, width: float, height: float):
        """Plot the Cantor dust on the given axes."""
        
    def _plot_cantor(self, ax: plt.Axes, x: float, y: float, width: float, 
                    height: float, depth: int):
        """Recursively plot the Cantor dust."""
```

#### `create_fractal`

Factory function to create a fractal of the specified type.

```python
def create_fractal(config: Dict[str, Any]) -> FractalBase:
    """Create a fractal of the specified type."""
```

### `rfm.core.morphogen`

#### `MorphogenBase`

Base class for morphogenic pattern generators.

```python
class MorphogenBase:
    """Base class for morphogenic pattern generators."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration."""
        
    def generate(self, width: int, height: int) -> np.ndarray:
        """Generate morphogenic pattern data."""
        
    def plot(self, ax: plt.Axes, x: float, y: float, width: float, height: float):
        """Plot the pattern on the given axes."""
```

#### `VoronoiMorphogen`

Voronoi-based morphogenic pattern generator.

```python
class VoronoiMorphogen(MorphogenBase):
    """Voronoi-based morphogenic pattern generator."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Voronoi generator with the given configuration."""
        
    def generate(self, width: int, height: int) -> np.ndarray:
        """Generate Voronoi pattern data."""
        
    def plot(self, ax: plt.Axes, x: float, y: float, width: float, height: float):
        """Plot the Voronoi pattern on the given axes."""
```

#### `GradientMorphogen`

Gradient-based morphogenic pattern generator.

```python
class GradientMorphogen(MorphogenBase):
    """Gradient-based morphogenic pattern generator."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the gradient generator with the given configuration."""
        
    def generate(self, width: int, height: int) -> np.ndarray:
        """Generate gradient pattern data."""
        
    def plot(self, ax: plt.Axes, x: float, y: float, width: float, height: float):
        """Plot the gradient pattern on the given axes."""
```

### `rfm.core.network`

#### `NetworkGenerator`

Generator for network structures.

```python
class NetworkGenerator:
    """Generator for network structures."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration."""
        
    def generate_network(self) -> Tuple[np.ndarray, np.ndarray]:
        """Generate a network structure."""
        
    def plot(self, ax: plt.Axes, x: float, y: float, width: float, height: float):
        """Plot the network on the given axes."""
```

## Visualization Module

### `rfm.viz.layout`

#### `ArchitectureLayout`

Main class for laying out and rendering the architecture.

```python
class ArchitectureLayout:
    """Layout engine for RFM Architecture visualization."""
    
    def __init__(self, config: Config):
        """Initialize with configuration."""
        
    def render(self, ax: plt.Axes):
        """Render the architecture on the given axes."""
        
    def render_components(self, ax: plt.Axes):
        """Render the components on the given axes."""
        
    def render_connections(self, ax: plt.Axes):
        """Render the connections on the given axes."""
        
    def render_conscious_fields(self, ax: plt.Axes):
        """Render the conscious fields on the given axes."""
        
    def render_fractals(self, ax: plt.Axes):
        """Render the fractals on the given axes."""
        
    def render_morphogen(self, ax: plt.Axes):
        """Render the morphogenic pattern on the given axes."""
        
    def render_kin_graph(self, ax: plt.Axes):
        """Render the KIN graph on the given axes."""
        
    def render_phi_metric(self, ax: plt.Axes):
        """Render the phi metric on the given axes."""
        
    def render_processing_scales(self, ax: plt.Axes):
        """Render the processing scales on the given axes."""
```

### `rfm.viz.components`

#### `ComponentRenderer`

Renderer for architecture components.

```python
class ComponentRenderer:
    """Renderer for architecture components."""
    
    def __init__(self, config: Dict[str, Any], styling: Dict[str, Any]):
        """Initialize with configuration and styling."""
        
    def render(self, ax: plt.Axes, component_id: str, component: Dict[str, Any], 
              center: Tuple[float, float] = None):
        """Render a component on the given axes."""
```

#### `ConnectionRenderer`

Renderer for connections between components.

```python
class ConnectionRenderer:
    """Renderer for connections between components."""
    
    def __init__(self, config: Dict[str, Any], component_positions: Dict[str, Tuple[float, float]], 
                styling: Dict[str, Any]):
        """Initialize with configuration, component positions, and styling."""
        
    def render(self, ax: plt.Axes, connection: Dict[str, Any]):
        """Render a connection on the given axes."""
```

### `rfm.viz.effects`

#### `GlassMorphism`

Glass morphism effect for components.

```python
class GlassMorphism:
    """Glass morphism effect for components."""
    
    @staticmethod
    def apply(ax: plt.Axes, x: float, y: float, width: float, height: float, 
             color: str, alpha: float = 0.5, blur: float = 5):
        """Apply glass morphism effect to the specified region."""
```

#### `GlowEffect`

Glow effect for components and connections.

```python
class GlowEffect:
    """Glow effect for components and connections."""
    
    @staticmethod
    def apply(ax: plt.Axes, x: float, y: float, width: float, height: float, 
             color: str, blur: float = 10, opacity: float = 0.4):
        """Apply glow effect to the specified region."""
```

### `rfm.viz.animation`

#### `AnimationRenderer`

Renderer for static animation frames.

```python
class AnimationRenderer:
    """Renderer for animation frames."""
    
    def __init__(self, config: Config):
        """Initialize with configuration."""
        
    def render_frame(self, time: float, ax: plt.Axes):
        """Render a frame at the specified time."""
        
    def render_broadcast(self, time: float, ax: plt.Axes, source: str, targets: List[str], 
                        start_time: float, duration: float, color: str):
        """Render a broadcast animation frame."""
```

### `rfm.viz.animation_engine`

#### `AnimationTimeline`

Container for animation sequences.

```python
class AnimationTimeline:
    """Container for animation sequences."""
    
    def __init__(self, fps: int = 60, duration: int = 5000):
        """Initialize with FPS and duration."""
        
    def add_sequence(self, sequence: AnimationSequence, start_time: int = 0, 
                    duration: int = None):
        """Add an animation sequence to the timeline."""
        
    def render(self, output_path: str, format: str = "gif", 
              width: int = 800, height: int = 800, dpi: int = 100):
        """Render the animation to a file."""
        
    def render_frame(self, time: float, layout: ArchitectureLayout, ax: plt.Axes):
        """Render a frame at the specified time."""
```

#### `AnimationSequence`

Base class for animation sequences.

```python
class AnimationSequence:
    """Base class for animation sequences."""
    
    def __init__(self, start_time: int = 0, duration: int = 1000):
        """Initialize with start time and duration."""
        
    def render_frame(self, time: float, layout: ArchitectureLayout, ax: plt.Axes):
        """Render a frame at the specified time."""
```

#### `BroadcastSequence`

Animation sequence for broadcasting information.

```python
class BroadcastSequence(AnimationSequence):
    """Animation sequence for broadcasting information."""
    
    def __init__(self, source: str, targets: List[str], start_time: int = 0, 
                duration: int = 1000, color: str = "#00c2c7", pulse_count: int = 3, 
                easing: str = "ease-out"):
        """Initialize broadcast sequence."""
        
    def render_frame(self, time: float, layout: ArchitectureLayout, ax: plt.Axes):
        """Render a broadcast frame at the specified time."""
```

#### `ParticleFlowSystem`

Animation sequence for particle flow effects.

```python
class ParticleFlowSystem(AnimationSequence):
    """Animation sequence for particle flow effects."""
    
    def __init__(self, source: str, target: str, particle_count: int = 50, 
                start_time: int = 0, duration: int = 2000, color: str = "#4287f5", 
                size_range: Tuple[float, float] = (1, 3), 
                trail_length: int = 5, jitter: float = 0.2):
        """Initialize particle flow system."""
        
    def render_frame(self, time: float, layout: ArchitectureLayout, ax: plt.Axes):
        """Render a particle flow frame at the specified time."""
```

## CLI Module

### `rfm.cli`

#### `VisualizerCLI`

Command-line interface for the visualizer.

```python
class VisualizerCLI:
    """Command-line interface for the visualizer."""
    
    @staticmethod
    def parse_args(args: List[str] = None) -> argparse.Namespace:
        """Parse command-line arguments."""
        
    @staticmethod
    def run(args: argparse.Namespace):
        """Run the visualizer with the specified arguments."""
```

#### `AnimationCLI`

Command-line interface for the animation system.

```python
class AnimationCLI:
    """Command-line interface for the animation system."""
    
    @staticmethod
    def parse_args(args: List[str] = None) -> argparse.Namespace:
        """Parse command-line arguments."""
        
    @staticmethod
    def run(args: argparse.Namespace):
        """Run the animation system with the specified arguments."""
```