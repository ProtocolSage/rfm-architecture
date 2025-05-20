"""Tests for configuration handling."""
import pytest
import os
from pathlib import Path
import tempfile
import yaml

from rfm.config.settings import Config, ConfigLoader
from rfm.config.validator import ConfigValidator, ValidationResult, ValidationError


def test_config_from_dict():
    """Test creating a Config from a dictionary."""
    data = {
        "layout": {"grid": {"width": 100}},
        "components": {"cif": {"center": [50, 50]}}
    }
    config = Config.from_dict(data)
    
    assert config.layout == {"grid": {"width": 100}}
    assert config.components == {"cif": {"center": [50, 50]}}


def test_config_to_dict():
    """Test converting a Config to a dictionary."""
    config = Config(
        layout={"grid": {"width": 100}},
        components={"cif": {"center": [50, 50]}}
    )
    data = config.to_dict()
    
    assert data["layout"] == {"grid": {"width": 100}}
    assert data["components"] == {"cif": {"center": [50, 50]}}


def test_config_loader_deep_merge():
    """Test deep merging of dictionaries."""
    base = {
        "a": 1,
        "b": {"c": 2, "d": 3},
        "e": {"f": 4}
    }
    override = {
        "b": {"c": 5},
        "e": 6
    }
    
    merged = ConfigLoader._deep_merge(base, override)
    
    assert merged["a"] == 1
    assert merged["b"]["c"] == 5
    assert merged["b"]["d"] == 3
    assert merged["e"] == 6


def test_config_loader_from_file():
    """Test loading configuration from a file."""
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump({
            "layout": {"grid": {"width": 100, "height": 100}},
            "components": {"cif": {"position": [50, 50], "size": [20, 20]}},
            "fractals": {"type": "mandelbrot", "parameters": {"center": [0, 0], "zoom": 1.5}}
        }, f)
    
    try:
        # Load the configuration with validation
        config = ConfigLoader.from_file(f.name, validate=True)
        
        assert config.layout == {"grid": {"width": 100, "height": 100}}
        assert config.components == {"cif": {"position": [50, 50], "size": [20, 20]}}
    finally:
        # Clean up
        os.unlink(f.name)


def test_config_loader_from_file_invalid():
    """Test loading an invalid configuration from a file."""
    # Create a temporary config file with invalid data
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump({
            "layout": {"grid": {"width": -100}},  # Invalid width
            "components": {"cif": {"position": [50], "size": [20, 20]}}  # Invalid position
        }, f)
    
    try:
        # Attempt to load with validation
        with pytest.raises(ValueError):
            ConfigLoader.from_file(f.name, validate=True)
        
        # Load without validation should succeed
        config = ConfigLoader.from_file(f.name, validate=False)
        assert config.layout["grid"]["width"] == -100  # Invalid but loaded
    finally:
        # Clean up
        os.unlink(f.name)


def test_config_loader_from_files():
    """Test loading and merging configurations from multiple files."""
    # Create temporary config files
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as base_file:
        yaml.dump({
            "layout": {"grid": {"width": 100, "height": 100}},
            "components": {"cif": {"position": [50, 50], "size": [20, 20]}},
            "fractals": {"type": "mandelbrot", "parameters": {"center": [0, 0], "zoom": 1.5}}
        }, base_file)
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as override_file:
        yaml.dump({
            "layout": {"grid": {"height": 120}},
            "components": {"cif": {"size": [25, 25]}}
        }, override_file)
    
    try:
        # Load and merge the configurations
        config = ConfigLoader.from_files(base_file.name, override_file.name)
        
        assert config.layout == {"grid": {"width": 100, "height": 120}}
        assert config.components == {"cif": {"position": [50, 50], "size": [25, 25]}}
    finally:
        # Clean up
        os.unlink(base_file.name)
        os.unlink(override_file.name)


def test_validation_result():
    """Test ValidationResult functionality."""
    # Test success case
    result = ValidationResult(is_valid=True)
    assert result.is_valid
    assert len(result.errors) == 0
    assert bool(result) is True
    
    # Test adding an error
    result.add_error("test.path", "Error message", expected="expected", received="received")
    assert not result.is_valid
    assert len(result.errors) == 1
    assert bool(result) is False
    
    # Test error representation
    error = result.errors[0]
    assert str(error) == "test.path: Error message (expected: expected, received: received)"
    
    # Test combining results
    other_result = ValidationResult(is_valid=True)
    combined = result.combine(other_result)
    assert not combined.is_valid  # One had an error
    assert len(combined.errors) == 1
    
    # Test summary
    assert "1 errors" in result.summary()
    
    # Test success summary
    success_result = ValidationResult(is_valid=True)
    assert "valid" in success_result.summary()


def test_validation_error():
    """Test ValidationError functionality."""
    # Basic error
    error = ValidationError("test.path", "Error message")
    assert str(error) == "test.path: Error message"
    
    # Error with expected and received
    error = ValidationError("test.path", "Error message", expected="expected", received="received")
    assert str(error) == "test.path: Error message (expected: expected, received: received)"


def test_validator_types():
    """Test type validation."""
    # Valid case
    result = ConfigValidator._validate_type("test.path", 100, int)
    assert result.is_valid
    
    # Invalid case
    result = ConfigValidator._validate_type("test.path", "string", int)
    assert not result.is_valid
    assert "Invalid type" in str(result.errors[0])
    
    # Valid multi-type case
    result = ConfigValidator._validate_type("test.path", 100, (int, float))
    assert result.is_valid


def test_validator_required_keys():
    """Test required keys validation."""
    # Valid case
    result = ConfigValidator._validate_required_keys(
        "test", {"a": 1, "b": 2, "c": 3}, {"a", "b"}
    )
    assert result.is_valid
    
    # Invalid case
    result = ConfigValidator._validate_required_keys(
        "test", {"a": 1}, {"a", "b", "c"}
    )
    assert not result.is_valid
    assert "Missing required keys" in str(result.errors[0])


def test_validator_enum():
    """Test enum validation."""
    # Valid case
    result = ConfigValidator._validate_enum("test.path", "a", {"a", "b", "c"})
    assert result.is_valid
    
    # Invalid case
    result = ConfigValidator._validate_enum("test.path", "d", {"a", "b", "c"})
    assert not result.is_valid
    assert "Invalid value" in str(result.errors[0])


def test_validator_range():
    """Test range validation."""
    # Valid case
    result = ConfigValidator._validate_range("test.path", 5, min_value=0, max_value=10)
    assert result.is_valid
    
    # Invalid min case
    result = ConfigValidator._validate_range("test.path", -1, min_value=0)
    assert not result.is_valid
    assert "less than minimum" in str(result.errors[0])
    
    # Invalid max case
    result = ConfigValidator._validate_range("test.path", 11, max_value=10)
    assert not result.is_valid
    assert "greater than maximum" in str(result.errors[0])


def test_validator_array():
    """Test array validation."""
    # Valid case
    result = ConfigValidator._validate_array(
        "test.path", [1, 2, 3], expected_length=3, item_type=int
    )
    assert result.is_valid
    
    # Invalid length case
    result = ConfigValidator._validate_array(
        "test.path", [1, 2], expected_length=3
    )
    assert not result.is_valid
    assert "Invalid array length" in str(result.errors[0])
    
    # Invalid min length case
    result = ConfigValidator._validate_array(
        "test.path", [1], min_length=2
    )
    assert not result.is_valid
    assert "too short" in str(result.errors[0])
    
    # Invalid max length case
    result = ConfigValidator._validate_array(
        "test.path", [1, 2, 3], max_length=2
    )
    assert not result.is_valid
    assert "too long" in str(result.errors[0])
    
    # Invalid item type case
    result = ConfigValidator._validate_array(
        "test.path", [1, "2", 3], item_type=int
    )
    assert not result.is_valid
    assert "Invalid type" in str(result.errors[0])


def test_config_validate():
    """Test the Config.validate method."""
    # Valid configuration
    config = Config(
        layout={"grid": {"width": 100, "height": 100}},
        components={"cif": {"position": [50, 50], "size": [20, 20]}},
        connections=[{"source": "cif", "target": "cif"}],
        fractals={"type": "mandelbrot", "parameters": {"center": [0, 0], "zoom": 1.5}}
    )
    is_valid, error_message = config.validate()
    assert is_valid
    assert error_message is None
    
    # Invalid configuration
    config = Config(
        layout={"grid": {"width": -100}},
        components={"cif": {"position": [50], "size": [20, 20]}}
    )
    is_valid, error_message = config.validate()
    assert not is_valid
    assert error_message is not None
    assert "errors" in error_message