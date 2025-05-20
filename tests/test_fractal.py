"""Tests for fractal generation."""
import pytest
import numpy as np
import matplotlib.pyplot as plt

from rfm.core.fractal import LSystem, MandelbrotSet, CantorDust, create_fractal


def test_lsystem_init():
    """Test L-system initialization."""
    config = {
        "axiom": "F",
        "rules": {"F": "F+F-F-F+F"},
        "angle": 90,
        "depth": 2
    }
    lsystem = LSystem(config)
    
    assert lsystem.axiom == "F"
    assert lsystem.rules == {"F": "F+F-F-F+F"}
    assert lsystem.angle == 90
    assert lsystem.depth == 2


def test_lsystem_generate():
    """Test L-system string generation."""
    config = {
        "axiom": "F",
        "rules": {"F": "F+F"},
        "angle": 90,
        "depth": 2
    }
    lsystem = LSystem(config)
    
    result = lsystem.generate()
    assert result == "F+F+F+F"


def test_mandelbrot_init():
    """Test Mandelbrot set initialization."""
    config = {
        "center": [-0.5, 0],
        "zoom": 1.5,
        "max_iter": 100
    }
    mandelbrot = MandelbrotSet(config)
    
    assert mandelbrot.center == [-0.5, 0]
    assert mandelbrot.zoom == 1.5
    assert mandelbrot.max_iter == 100


def test_mandelbrot_compute():
    """Test Mandelbrot set computation."""
    config = {
        "center": [0, 0],
        "zoom": 2,
        "max_iter": 10
    }
    mandelbrot = MandelbrotSet(config)
    
    iterations = mandelbrot.compute(10, 10)
    assert iterations.shape == (10, 10)
    assert np.max(iterations) <= 10


def test_cantor_dust_init():
    """Test Cantor dust initialization."""
    config = {
        "depth": 3,
        "gap_ratio": 0.3
    }
    cantor = CantorDust(config)
    
    assert cantor.depth == 3
    assert cantor.gap_ratio == 0.3


def test_cantor_dust_generate():
    """Test Cantor dust generation."""
    config = {
        "depth": 1,
        "gap_ratio": 0.3
    }
    cantor = CantorDust(config)
    
    rectangles = cantor.generate(0, 100, 0, 100, 1)
    assert len(rectangles) == 8


def test_create_fractal():
    """Test fractal factory function."""
    # L-system
    config_ls = {
        "type": "l_system",
        "depth": 2,
        "parameters": {
            "axiom": "F"
        }
    }
    fractal_ls = create_fractal(config_ls)
    assert isinstance(fractal_ls, LSystem)
    
    # Mandelbrot
    config_mb = {
        "type": "mandelbrot",
        "depth": 2,
        "parameters": {
            "center": [-0.5, 0]
        }
    }
    fractal_mb = create_fractal(config_mb)
    assert isinstance(fractal_mb, MandelbrotSet)
    
    # Cantor dust
    config_cd = {
        "type": "cantor",
        "depth": 2,
        "parameters": {
            "gap_ratio": 0.3
        }
    }
    fractal_cd = create_fractal(config_cd)
    assert isinstance(fractal_cd, CantorDust)
    
    # Unknown type
    with pytest.raises(ValueError):
        create_fractal({"type": "unknown"})