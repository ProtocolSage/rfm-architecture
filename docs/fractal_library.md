# Fractal Library

RFM Architecture supports multiple fractal types for use in visualization. This document describes the available fractal types and their configuration options.

## Available Fractal Types

- **L-System**: Lindenmeyer systems for generating self-similar curves
- **Mandelbrot Set**: The classic Mandelbrot set fractal
- **Julia Set**: Julia set fractals with configurable complex parameter
- **Cantor Dust**: Cantor dust/Cantor set fractal

## L-System

L-Systems (Lindenmayer Systems) are a type of formal grammar used to model the development of plant-like structures. In RFM Architecture, they are used to generate self-similar curves.

### Configuration

```yaml
fractals:
  type: "l_system"
  depth: 4  # Recursion depth
  parameters:
    axiom: "F"  # Initial string
    rules:  # Production rules
      F: "F+F-F-F+F"  # Koch curve
    angle: 90  # Turning angle in degrees
    color: "#b086ff"  # Line color
    alpha: 0.1  # Line opacity
    width: 0.5  # Line width
```

### Popular L-System Examples

#### Koch Curve

```yaml
parameters:
  axiom: "F"
  rules:
    F: "F+F-F-F+F"
  angle: 90
```

#### Dragon Curve

```yaml
parameters:
  axiom: "FX"
  rules:
    X: "X+YF+"
    Y: "-FX-Y"
  angle: 90
```

#### Sierpinski Triangle

```yaml
parameters:
  axiom: "F-G-G"
  rules:
    F: "F-G+F+G-F"
    G: "GG"
  angle: 120
```

## Mandelbrot Set

The Mandelbrot set is a set of complex numbers for which the function f(z) = z² + c does not diverge when iterated from z = 0.

### Configuration

```yaml
fractals:
  type: "mandelbrot"
  parameters:
    center: [-0.5, 0]  # Center point [real, imaginary]
    zoom: 1.5  # Zoom level
    max_iter: 100  # Maximum iterations
    cmap: "viridis"  # Matplotlib colormap
```

## Julia Set

Julia sets are fractals obtained from complex function iteration, similar to the Mandelbrot set, but with a fixed complex parameter c.

### Configuration

```yaml
fractals:
  type: "julia"
  parameters:
    c_real: -0.7  # Real part of c parameter
    c_imag: 0.27  # Imaginary part of c parameter
    center: [0, 0]  # Center point [real, imaginary]
    zoom: 1.5  # Zoom level
    max_iter: 100  # Maximum iterations
    cmap: "viridis"  # Matplotlib colormap
```

### Popular Julia Set Examples

#### Douady Rabbit

```yaml
parameters:
  c_real: -0.123
  c_imag: 0.745
```

#### Dendrite

```yaml
parameters:
  c_real: 0.0
  c_imag: 1.0
```

#### Siegel Disk

```yaml
parameters:
  c_real: -0.391
  c_imag: -0.587
```

## Cantor Dust

Cantor Dust is a multi-dimensional version of the Cantor set, created by repeatedly removing the middle portion of line segments.

### Configuration

```yaml
fractals:
  type: "cantor"
  depth: 5  # Recursion depth
  parameters:
    gap_ratio: 0.3  # Size of the gap relative to the segment
```

## Using Alternative Fractals

RFM Architecture also supports defining multiple fractal configurations in the config file and switching between them:

```yaml
# Main fractal configuration
fractals:
  type: "julia"
  parameters:
    c_real: -0.7
    c_imag: 0.27
    center: [0, 0]
    zoom: 1.5

# Alternative fractals for easy switching
alternative_fractals:
  julia_douady_rabbit:
    type: "julia"
    parameters:
      c_real: -0.123
      c_imag: 0.745
      center: [0, 0]
      zoom: 1.2
  
  mandelbrot_zoom:
    type: "mandelbrot"
    parameters:
      center: [-0.75, 0.1]
      zoom: 4.5
      max_iter: 200
```

To use an alternative fractal, specify it when running the visualizer:

```bash
poetry run rfm-viz --fractal julia_douady_rabbit
```