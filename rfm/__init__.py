"""Recursive Fractal Mind – public package surface."""
from importlib.metadata import version  # type: ignore
__all__ = ["core", "viz", "config", "main", "cli"]

try:
    __version__: str = version("rfm_architecture")
except:
    __version__: str = "0.2.0"  # Fallback version