# RFM Architecture UI

An interactive visualization tool for the Recursive Fractal Mind Architecture.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## Features

- Interactive fractal exploration with real-time rendering
- Support for multiple fractal types (Mandelbrot, Julia, L-System, Cantor Dust)
- High-quality rendering with customizable parameters
- Real-time performance monitoring and optimization
- Robust error handling with user-friendly messages
- Parameter presets for quick exploration
- Export to various image formats

## Installation

### Prerequisites

- Python 3.8 or higher
- Poetry (for dependency management)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/RFM-Architecture.git
   cd RFM-Architecture/ui
   ```

2. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

3. Activate the virtual environment:
   ```bash
   poetry shell
   ```

## Usage

### Running the UI

```bash
# Using Poetry
poetry run python -m rfm_ui.main

# Or if already in Poetry shell
python -m rfm_ui.main
```

On Windows, you can also use the provided batch file:
```
run_rfm_ui.bat
```

### Command-Line Options

```
usage: main.py [-h] [--config CONFIG] [--log-dir LOG_DIR] [--debug]

RFM Architecture Visualization UI

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG, -c CONFIG
                        Path to configuration file
  --log-dir LOG_DIR, -l LOG_DIR
                        Directory for log files
  --debug               Enable debug logging
```

## Fractal Types

### Mandelbrot Set

The Mandelbrot set is a set of complex numbers for which the function f(z) = z² + c does not diverge when iterated from z = 0.

Parameters:
- Center (X, Y): Center point in the complex plane
- Zoom: Zoom level
- Max Iterations: Maximum number of iterations

### Julia Set

Julia sets are closely related to the Mandelbrot set. They are obtained by fixing the parameter c and iterating the function f(z) = z² + c.

Parameters:
- Complex Parameter (Real, Imaginary): The fixed c value
- Center (X, Y): Center point in the complex plane
- Zoom: Zoom level
- Max Iterations: Maximum number of iterations

### L-System

L-Systems (Lindenmayer systems) are formal grammars used to model plant growth and other fractal patterns.

Parameters:
- Axiom: Initial string
- Rules: Production rules
- Angle: Angle for turtle interpretation
- Iterations: Number of iterations
- Line Width: Width of lines
- Color: Line color

### Cantor Dust

Cantor dust is a multi-dimensional version of the Cantor set, created by repeatedly removing the middle portion of line segments.

Parameters:
- Gap Ratio: Size of the gap relative to the segment
- Iterations: Number of iterations
- Color: Dust color

## Performance Monitoring

The application includes a built-in performance monitoring system that tracks:
- Rendering times
- Memory usage
- FPS (Frames Per Second)
- Performance hotspots

Press F5 or select "Performance Monitor" from the View menu to access these features.

## Error Handling

The application includes comprehensive error handling with:
- User-friendly error messages
- Detailed error information for debugging
- Automatic recovery from most errors
- Error logging for diagnostics

## Development

### Project Structure

```
ui/
├── rfm_ui/                 # Main package
│   ├── __init__.py         # Package initialization
│   ├── main.py             # Entry point
│   ├── config/             # Configuration handling
│   ├── engine/             # Fractal rendering engine
│   ├── errors/             # Error handling
│   ├── performance/        # Performance monitoring
│   └── ui/                 # User interface components
├── tests/                  # Test suite
├── pyproject.toml          # Project metadata and dependencies
└── README.md               # This file
```

### Testing

```bash
# Run tests
poetry run pytest
```

### Building a Standalone Executable

```bash
# Install pyinstaller
poetry add --dev pyinstaller

# Build executable
poetry run pyinstaller --onefile --windowed --name rfm_ui rfm_ui/main.py
```

The executable will be created in the `dist` directory.

## License

This project is licensed under the MIT License - see the LICENSE file for details.