"""
Fallback Detection Module.

This module provides fallback detection mechanisms when the primary
detection methods fail or are unsupported.

EDUCATIONAL NOTE - Why Fallbacks Matter:
Software should degrade gracefully when encountering:
- Unsupported platforms (FreeBSD, Solaris, etc.)
- Missing system utilities (lsb_release, etc.)
- Restricted permissions (can't read /proc, etc.)
- Partial installations (Python without pip, etc.)

Good fallback strategies:
1. Try primary method first
2. If it fails, try alternative methods
3. If all fail, return partial/limited information
4. Never crash - return best-effort results
5. Log what methods were tried and why they failed
"""

import sys
import os
import platform
from typing import Dict, Any, Optional
from pathlib import Path

from harmonizer.models import OSType, VenvType
from harmonizer.utils.logging_config import HarmonizerLogger


logger = HarmonizerLogger.get_logger(__name__)


def fallback_os_detection() -> Dict[str, Any]:
    """
    Fallback OS detection when primary methods fail.

    Returns:
        Dictionary with OS information:
        - type: OSType enum value
        - version: Version string
        - confidence: Confidence level (low, medium, high)
        - method: Detection method used

    EDUCATIONAL NOTE - Platform Detection Hierarchy:
    Python's platform module provides cross-platform APIs:
    1. platform.system() - OS name (Windows, Linux, Darwin)
    2. platform.release() - Kernel version
    3. platform.version() - Full version string
    4. platform.uname() - All information

    These work everywhere Python runs, making them good fallbacks.
    """

    logger.info("Using fallback OS detection")

    result = {
        "type": OSType.UNKNOWN,
        "version": "Unknown",
        "confidence": "low",
        "method": "fallback",
    }

    try:
        system = platform.system()

        # Map platform.system() to OSType
        system_map = {
            "Windows": OSType.WINDOWS_NATIVE,
            "Darwin": OSType.MACOS,
            "Linux": OSType.LINUX,  # Can't distinguish WSL in fallback
        }

        result["type"] = system_map.get(system, OSType.UNKNOWN)
        result["confidence"] = "medium" if system in system_map else "low"

        # Get version information
        try:
            if system == "Windows":
                result["version"] = f"{platform.release()} (Build {platform.version()})"
            elif system == "Darwin":
                result["version"] = f"macOS {platform.mac_ver()[0]}"
            else:
                result["version"] = platform.release()

            result["confidence"] = "medium"

        except Exception as e:
            logger.warning(f"Could not get OS version: {e}")
            result["version"] = "Unknown"

        logger.info(f"Fallback OS detection: {result['type'].value} ({result['version']})")

    except Exception as e:
        logger.error(f"Fallback OS detection failed: {e}")

    return result


def fallback_python_detection() -> Dict[str, Any]:
    """
    Fallback Python version detection.

    Returns:
        Dictionary with Python information:
        - version: Version string
        - executable: Path to Python executable
        - implementation: Python implementation name
        - confidence: Confidence level

    EDUCATIONAL NOTE - sys Module:
    The sys module provides runtime information:
    - sys.version_info: Tuple of version components
    - sys.version: Human-readable version string
    - sys.executable: Path to Python interpreter
    - sys.implementation: Implementation details

    These are always available, making them perfect for fallback.
    """

    logger.info("Using fallback Python detection")

    version_info = sys.version_info
    version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"

    result = {
        "version": version_str,
        "executable": sys.executable or "unknown",
        "implementation": sys.implementation.name if hasattr(sys, 'implementation') else "unknown",
        "confidence": "high",  # sys module is always reliable
        "method": "sys_module",
    }

    logger.info(f"Fallback Python detection: {result['version']} at {result['executable']}")

    return result


def fallback_venv_detection() -> Dict[str, Any]:
    """
    Fallback virtual environment detection.

    Returns:
        Dictionary with virtual environment information:
        - type: VenvType enum value
        - active: Whether venv is active
        - path: Path to venv (if detected)
        - confidence: Confidence level

    EDUCATIONAL NOTE - Virtual Environment Detection:
    Virtual environments modify sys.prefix and sys.base_prefix:
    - sys.base_prefix: Installation prefix (system Python)
    - sys.prefix: Current prefix (venv if activated)
    - If they differ, a venv is active

    This works for:
    - venv (Python 3.3+)
    - virtualenv
    - Most venv implementations
    """

    logger.info("Using fallback venv detection")

    result = {
        "type": VenvType.NONE,
        "active": False,
        "path": None,
        "confidence": "medium",
        "method": "sys_prefix",
    }

    try:
        # Check if in a virtual environment
        in_venv = sys.prefix != sys.base_prefix

        if in_venv:
            result["active"] = True
            result["path"] = sys.prefix

            # Try to guess venv type from path
            venv_path = Path(sys.prefix)

            # Check for common venv indicators
            if (venv_path / "pyvenv.cfg").exists():
                result["type"] = VenvType.VIRTUALENV  # or VENV, hard to distinguish
            elif "conda" in str(venv_path).lower() or (venv_path / "conda-meta").exists():
                result["type"] = VenvType.CONDA
            elif ".poetry" in str(venv_path):
                result["type"] = VenvType.POETRY
            else:
                # Generic virtual environment
                result["type"] = VenvType.VIRTUALENV

            result["confidence"] = "medium"
            logger.info(f"Fallback venv detection: {result['type'].value} at {result['path']}")
        else:
            logger.info("Fallback venv detection: No virtual environment detected")

    except Exception as e:
        logger.error(f"Fallback venv detection failed: {e}")

    return result


def fallback_dependency_scan(project_path: str) -> Dict[str, Any]:
    """
    Fallback dependency scanning.

    Args:
        project_path: Path to project directory

    Returns:
        Dictionary with dependency information:
        - requirements_file: Path to requirements file (if found)
        - has_requirements: Whether requirements files exist
        - confidence: Confidence level

    EDUCATIONAL NOTE - File-Based Detection:
    When we can't run pip or other tools, we can still:
    - Check if requirements files exist
    - Count lines in requirements files
    - Detect file types

    This provides partial information even when full scanning fails.
    """

    logger.info(f"Using fallback dependency scan for: {project_path}")

    result = {
        "requirements_file": None,
        "has_requirements": False,
        "confidence": "low",
        "method": "file_existence",
    }

    try:
        project = Path(project_path)

        # Check for common dependency files
        dependency_files = [
            "requirements.txt",
            "pyproject.toml",
            "setup.py",
            "Pipfile",
            "environment.yml",
        ]

        for filename in dependency_files:
            file_path = project / filename
            if file_path.exists():
                result["requirements_file"] = str(file_path)
                result["has_requirements"] = True
                result["confidence"] = "medium"

                logger.info(f"Found requirements file: {filename}")
                break

        if not result["has_requirements"]:
            logger.info("No requirements files found in fallback scan")

    except Exception as e:
        logger.error(f"Fallback dependency scan failed: {e}")

    return result


def safe_detection(primary_func, fallback_func, operation_name: str, *args, **kwargs):
    """
    Wrapper to try primary detection with fallback on failure.

    Args:
        primary_func: Primary detection function to try
        fallback_func: Fallback function to use if primary fails
        operation_name: Name of the operation (for logging)
        *args, **kwargs: Arguments to pass to both functions

    Returns:
        Result from primary function, or fallback if primary fails

    EDUCATIONAL NOTE - Try-Fallback Pattern:
    This pattern is useful for graceful degradation:
    1. Try the best/preferred method
    2. If it fails, try alternative methods
    3. If all fail, return minimal but valid data
    4. Always log what happened for debugging

    This makes software more robust and user-friendly.

    Example:
        >>> result = safe_detection(
        ...     detect_os_type,
        ...     fallback_os_detection,
        ...     "OS detection"
        ... )
    """

    logger.debug(f"Attempting primary {operation_name}")

    try:
        result = primary_func(*args, **kwargs)
        logger.debug(f"Primary {operation_name} succeeded")
        return result

    except Exception as e:
        logger.warning(f"Primary {operation_name} failed: {e}")
        logger.info(f"Falling back to alternative {operation_name}")

        try:
            result = fallback_func(*args, **kwargs)
            logger.info(f"Fallback {operation_name} succeeded")
            return result

        except Exception as fallback_error:
            logger.error(f"Fallback {operation_name} also failed: {fallback_error}")
            # Return minimal result rather than crashing
            return {
                "error": str(fallback_error),
                "confidence": "none",
                "method": "failed",
            }


def get_minimal_environment_info() -> Dict[str, Any]:
    """
    Get minimal environment information that should work anywhere.

    Returns:
        Dictionary with basic environment info:
        - python_version: Python version
        - python_executable: Path to Python
        - platform: Platform name
        - architecture: CPU architecture

    EDUCATIONAL NOTE - Guaranteed Information:
    Some information is always available in Python:
    - sys.version_info: Python version
    - sys.executable: Python executable path
    - platform.machine(): CPU architecture
    - os.name: Basic OS name

    This minimal set works on any Python installation,
    making it useful as a last resort.
    """

    logger.info("Getting minimal environment information")

    try:
        return {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "python_executable": sys.executable,
            "platform": platform.system(),
            "architecture": platform.machine(),
            "os_name": os.name,
            "confidence": "high",
            "method": "minimal_builtin",
        }

    except Exception as e:
        logger.error(f"Even minimal detection failed: {e}")
        # Return absolute minimal information
        return {
            "python_version": "unknown",
            "python_executable": "unknown",
            "platform": "unknown",
            "error": str(e),
        }


# Example usage and testing
if __name__ == "__main__":
    """
    Test fallback detection mechanisms.
    """

    print("=" * 70)
    print("Fallback Detection Module - Test Run")
    print("=" * 70)

    # Test OS detection
    print("\nOS Detection (fallback):")
    os_info = fallback_os_detection()
    for key, value in os_info.items():
        print(f"  {key}: {value}")

    # Test Python detection
    print("\nPython Detection (fallback):")
    python_info = fallback_python_detection()
    for key, value in python_info.items():
        print(f"  {key}: {value}")

    # Test venv detection
    print("\nVenv Detection (fallback):")
    venv_info = fallback_venv_detection()
    for key, value in venv_info.items():
        print(f"  {key}: {value}")

    # Test dependency scan
    print("\nDependency Scan (fallback):")
    dep_info = fallback_dependency_scan(".")
    for key, value in dep_info.items():
        print(f"  {key}: {value}")

    # Test minimal info
    print("\nMinimal Environment Info:")
    minimal_info = get_minimal_environment_info()
    for key, value in minimal_info.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 70)
