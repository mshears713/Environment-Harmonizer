"""
Detection modules for environment analysis.

This package contains specialized detectors for different aspects of the
development environment:
    - os_detector: Operating system type and version detection
    - python_detector: Python interpreter version detection
    - venv_detector: Virtual environment type and status detection
    - dependency_detector: Dependency scanning and validation
"""

from harmonizer.detectors.os_detector import detect_os_type, get_os_version
from harmonizer.detectors.python_detector import detect_python_version
from harmonizer.detectors.venv_detector import detect_venv_type

__all__ = [
    "detect_os_type",
    "get_os_version",
    "detect_python_version",
    "detect_venv_type",
]
