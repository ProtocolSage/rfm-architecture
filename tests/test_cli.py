"""Tests for command-line interface."""
import pytest
import sys
from unittest.mock import patch

from rfm.cli import parse_args


def test_parse_args_defaults():
    """Test parsing of default arguments."""
    with patch('sys.argv', ['rfm-viz']):
        args = parse_args()
        
        assert args.config == "config.yaml"
        assert args.format == "svg"
        assert args.dpi == 300
        assert args.output == "rfm_architecture"
        assert not args.show
        assert not args.animate
        assert args.log_level == "info"
        assert not args.dark_mode


def test_parse_args_custom():
    """Test parsing of custom arguments."""
    with patch('sys.argv', [
        'rfm-viz',
        '--config', 'custom.yaml',
        '--format', 'png',
        '--dpi', '600',
        '--output', 'custom_output',
        '--show',
        '--animate',
        '--log-level', 'debug',
        '--dark-mode'
    ]):
        args = parse_args()
        
        assert args.config == "custom.yaml"
        assert args.format == "png"
        assert args.dpi == 600
        assert args.output == "custom_output"
        assert args.show
        assert args.animate
        assert args.log_level == "debug"
        assert args.dark_mode