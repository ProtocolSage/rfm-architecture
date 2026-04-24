"""Recursive Fractal Mind – public package surface."""
import logging

from rfm.core.logging_config import StructuredLogger

# Register StructuredLogger as the default logger class before any getLogger()
# call elsewhere in the rfm package. Replaces the runtime __class__ mutation
# formerly done inside get_logger() / configure_logging().
logging.setLoggerClass(StructuredLogger)

from importlib.metadata import version  # type: ignore  # noqa: E402

__all__ = ["core", "viz", "config", "main", "cli"]

try:
    __version__: str = version("rfm_architecture")
except Exception:
    __version__: str = "0.2.0"  # Fallback version