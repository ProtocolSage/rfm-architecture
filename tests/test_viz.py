"""Tests for visualization components."""
import pytest
import matplotlib.pyplot as plt
import numpy as np

from rfm.viz.components import Component, NestedConsciousFields, PhiMetric, ProcessingScales
from rfm.viz.layout import GoldenRatioLayout


@pytest.fixture
def mock_figure():
    """Create a figure and axes for testing."""
    fig, ax = plt.subplots()
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    return fig, ax


def test_component_init():
    """Test Component initialization."""
    component = Component("test", {
        "center": [50, 50],
        "size": [20, 15],
        "color": "#ff0000"
    })
    
    assert component.name == "test"
    assert component.center == [50, 50]
    assert component.size == [20, 15]
    assert component.color == "#ff0000"


def test_component_draw(mock_figure):
    """Test Component drawing."""
    _, ax = mock_figure
    
    component = Component("test", {
        "center": [50, 50],
        "size": [20, 15],
        "color": "#ff0000",
        "label": "Test"
    })
    
    component.draw(ax)
    
    # Check that an ellipse was added
    assert len(ax.patches) == 1
    
    # Check that a text was added
    assert len(ax.texts) == 1


def test_component_connect_to(mock_figure):
    """Test Component connection."""
    _, ax = mock_figure
    
    component1 = Component("source", {
        "center": [30, 50],
        "size": [20, 15],
        "color": "#ff0000"
    })
    
    component2 = Component("target", {
        "center": [70, 50],
        "size": [20, 15],
        "color": "#00ff00"
    })
    
    connection_config = {
        "curve": 0.1,
        "width": 2,
        "color": "#0000ff",
        "bidirectional": True
    }
    
    component1.connect_to(component2, ax, connection_config)
    
    # Check that an arrow was added
    assert len(ax.patches) == 1


def test_nested_conscious_fields(mock_figure):
    """Test NestedConsciousFields drawing."""
    _, ax = mock_figure
    
    fields_config = {
        "primary": {
            "size": [30, 30],
            "alpha": 0.8,
            "color": "#ff0000"
        },
        "reflective": {
            "size": [40, 40],
            "alpha": 0.6,
            "color": "#00ff00"
        }
    }
    
    cif = Component("cif", {
        "center": [50, 50],
        "size": [20, 15],
        "color": "#0000ff"
    })
    
    fields = NestedConsciousFields(fields_config)
    fields.draw(ax, cif)
    
    # Check that two ellipses were added
    assert len(ax.patches) == 2


def test_phi_metric(mock_figure):
    """Test PhiMetric drawing."""
    _, ax = mock_figure
    
    phi_config = {
        "display": True,
        "position": [60, 55],
        "formula": True,
        "font_size": 10,
        "color": "#ff00ff",
        "value": 0.85
    }
    
    cif = Component("cif", {
        "center": [50, 50],
        "size": [20, 15],
        "color": "#0000ff"
    })
    
    phi = PhiMetric(phi_config)
    phi.draw(ax, cif)
    
    # Check that a text was added
    assert len(ax.texts) == 1


def test_processing_scales(mock_figure):
    """Test ProcessingScales drawing."""
    _, ax = mock_figure
    
    scales_config = {
        "micro": {
            "radius": 15,
            "dash_pattern": [1, 1],
            "color": "#ff0000"
        },
        "cognitive": {
            "radius": 25,
            "dash_pattern": [2, 1],
            "color": "#00ff00"
        }
    }
    
    cif = Component("cif", {
        "center": [50, 50],
        "size": [20, 15],
        "color": "#0000ff"
    })
    
    scales = ProcessingScales(scales_config)
    scales.draw(ax, cif)
    
    # Check that two ellipses were added
    assert len(ax.patches) == 2


def test_golden_ratio_layout(mock_figure):
    """Test GoldenRatioLayout initialization."""
    _, ax = mock_figure
    
    layout_config = {
        "grid": {
            "width": 100,
            "height": 100,
            "origin": [50, 50],
            "golden_ratio": 1.618
        }
    }
    
    layout = GoldenRatioLayout(ax, layout_config)
    
    assert layout.grid_width == 100
    assert layout.grid_height == 100
    assert layout.origin == [50, 50]
    assert layout.golden_ratio == 1.618


def test_golden_section():
    """Test golden section calculation."""
    _, ax = plt.subplots()
    
    layout = GoldenRatioLayout(ax, {})
    
    larger, smaller = layout.golden_section(100)
    
    # Check that the ratio is approximately the golden ratio
    assert abs(larger / smaller - layout.GOLDEN_RATIO) < 0.0001
    assert abs(larger + smaller - 100) < 0.0001