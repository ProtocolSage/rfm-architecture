# RFM Architecture Configuration Schema

This document describes the configuration schema for the RFM Architecture visualization.

## Top-Level Sections

| Section | Type | Description | Required |
|---------|------|-------------|----------|
| `layout` | Object | Grid and layout settings | Yes |
| `components` | Object | Component definitions | Yes |
| `connections` | Array | Connection definitions | Yes |
| `conscious_fields` | Object | Conscious field settings | No |
| `fractals` | Object | Fractal visualization settings | Yes |
| `morphogen` | Object | Morphogenetic pattern settings | No |
| `kin_graph` | Object | Knowledge Integration Network settings | No |
| `phi_metric` | Object | Phi metric settings | No |
| `processing_scales` | Object | Processing scale settings | No |
| `animation` | Object | Animation settings | No |
| `styling` | Object | Global styling settings | No |

## Layout Settings

```yaml
layout:
  grid:
    width: 100        # Width of the grid (int/float) - Required
    height: 100       # Height of the grid (int/float) - Required
    origin: [50, 50]  # Origin coordinates [x, y] - Optional
    golden_ratio: 1.618  # Golden ratio for layout - Optional
```

## Component Settings

Each component must have a unique key and define at least a position and size:

```yaml
components:
  component_name:      # Unique component identifier
    position: [x, y]   # Position coordinates [x, y] - Required
    size: [width, height]  # Size dimensions [width, height] - Required
    color: "#hex"      # Component color (string) - Optional
    label: "Label"     # Component label (string) - Optional
    description: "Description"  # Component description (string) - Optional
    zorder: 10         # Z-order for rendering (int) - Optional
```

## Connection Settings

Each connection must define a source and target component:

```yaml
connections:
  - source: "source_component"    # Source component ID - Required
    target: "target_component"    # Target component ID - Required
    curve: 0.1                    # Curve factor (float) - Optional
    width: 2                      # Line width (int/float) - Optional
    color: "#hex"                 # Line color (string) - Optional
    bidirectional: true           # Whether connection is bidirectional (bool) - Optional
```

## Fractal Settings

Fractal settings depend on the selected fractal type:

```yaml
fractals:
  type: "l_system"     # Fractal type (l_system, mandelbrot, julia, cantor) - Required
  depth: 4             # Recursion depth (int) - Optional
  parameters:          # Type-specific parameters - Required
    # L-system specific
    axiom: "F"
    rules:
      F: "F+F-F-F+F"
    angle: 90
    # Mandelbrot/Julia specific
    center: [-0.5, 0]
    zoom: 1.5
    max_iter: 100
    cmap: "viridis"
    # Julia specific
    c_real: -0.7
    c_imag: 0.27
    # Cantor specific
    gap_ratio: 0.3
```

### L-System Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `axiom` | String | Initial axiom | Yes |
| `rules` | Object | Production rules mapping | Yes |
| `angle` | Number | Turning angle in degrees | Yes |
| `color` | String | Line color (hex) | No |
| `alpha` | Number | Line opacity (0-1) | No |
| `width` | Number | Line width | No |

### Mandelbrot/Julia Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `center` | Array | Center coordinates [x, y] | Yes |
| `zoom` | Number | Zoom level (>0) | Yes |
| `max_iter` | Integer | Maximum iterations (>0) | Yes |
| `cmap` | String | Matplotlib colormap name | No |

### Julia-Specific Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `c_real` | Number | Real part of c parameter | Yes |
| `c_imag` | Number | Imaginary part of c parameter | Yes |

### Cantor Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `gap_ratio` | Number | Gap ratio (0-1) | Yes |

## Animation Settings

```yaml
animation:
  broadcast:
    enabled: true        # Enable broadcast animation (bool) - Optional
    duration: 400        # Animation duration in ms (int) - Optional
    fps: 60              # Frames per second (int) - Optional
    pulse_count: 3       # Number of pulses (int) - Optional
    easing: "cubic-bezier(0.25, 0.1, 0.25, 1.0)"  # Easing function (string) - Optional
    color: "#hex"        # Pulse color (string) - Optional
    glow: true           # Enable glow effect (bool) - Optional
```

## Styling Settings

```yaml
styling:
  background: "#hex"    # Background color (string) - Optional
  border: "#hex"        # Border color (string) - Optional
  fonts:
    ui: "Font Name"     # UI font family (string) - Optional
    code: "Font Name"   # Code font family (string) - Optional
    sizes:              # Font sizes - Optional
      title: 18         # Title font size (int) - Optional
      subtitle: 12      # Subtitle font size (int) - Optional
      component: 11     # Component font size (int) - Optional
      description: 8    # Description font size (int) - Optional
  effects:
    shadow:             # Shadow effect settings - Optional
      blur: 8           # Shadow blur radius (int) - Optional
      opacity: 0.25     # Shadow opacity (float 0-1) - Optional
    glow:               # Glow effect settings - Optional
      color: "#hex"     # Glow color (string) - Optional
      blur: 10          # Glow blur radius (int) - Optional
      opacity: 0.4      # Glow opacity (float 0-1) - Optional
```