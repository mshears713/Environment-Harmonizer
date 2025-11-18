"""
Environment Harmonizer - A Python environment diagnostic and harmonization tool.

This package provides tools to detect, analyze, and fix environment inconsistencies
across different platforms (Windows, WSL, Linux, macOS) and Python configurations.

Core Modules:
    - models: Data structures for environment status
    - detectors: Detection logic for OS, Python, virtual environments, dependencies
    - scanners: Orchestration of detection modules
    - reporters: Report generation in various formats
    - fixers: Automated fix application
    - utils: Utility functions and helpers

Author: Environment Harmonizer Team
License: MIT
"""

__version__ = "0.1.0"
__author__ = "Environment Harmonizer Team"
__license__ = "MIT"

# Expose key components for easy importing
from harmonizer.models import EnvironmentStatus, OSType, VenvType, IssueSeverity, Issue

__all__ = [
    "EnvironmentStatus",
    "OSType",
    "VenvType",
    "IssueSeverity",
    "Issue",
    "__version__",
]
