# RFM Architecture Documentation

Welcome to the RFM Architecture documentation. This documentation provides comprehensive information about the Recursive Fractal Mind Architecture visualization system.

## Contents

### User Documentation
- [User Guide](user_guide.md): Getting started and basic usage instructions
- [Architecture Overview](architecture.md): Overview of the RFM cognitive architecture
- [Configuration Schema](config_schema.md): Detailed description of the configuration file format
- [Fractal Library](fractal_library.md): Documentation of fractal types supported by RFM Architecture
- [Animation System](animation_system.md): Documentation of the animation capabilities

### Developer Documentation
- [API Reference](api_reference.md): Detailed API documentation for all modules
- [Development Guide](development_guide.md): Guide for extending and modifying the system

## Quick Start

1. Install the package:
   ```bash
   poetry install --no-root
   ```

2. Run the visualizer:
   ```bash
   poetry run rfm-viz --output diagram.svg --format svg --dpi 300
   ```

3. Alternatively, run an animation:
   ```bash
   poetry run python animate_rfm.py
   ```

4. Validate your configuration:
   ```bash
   python validate_config.py config.yaml
   ```

## Configuration

The RFM Architecture system is configured using YAML files. The default configuration file is `config.yaml` in the project root directory.

Example configuration:

```yaml
layout:
  grid:
    width: 100
    height: 100

components:
  cif:
    position: [50, 50]
    size: [28, 28]
    color: "#42d7f5"
    label: "Consciousness Integration Field"

fractals:
  type: "julia"
  parameters:
    c_real: -0.7
    c_imag: 0.27
    center: [0, 0]
    zoom: 1.5
```

For a complete reference of the configuration format, see the [Configuration Schema](config_schema.md).