"""
Python Version Detection Module.

This module provides functionality to detect Python interpreter versions
and compare them against project requirements.

EDUCATIONAL NOTE - Why Python Version Matters:
Different Python versions have different features and behaviors:
- Language features (f-strings in 3.6+, walrus operator in 3.8+, etc.)
- Standard library changes (pathlib improvements, new modules)
- Performance improvements
- Security updates
- Compatibility with dependencies

Projects often specify minimum Python versions to ensure:
- Required language features are available
- Dependencies can be installed
- Code runs with expected behavior
"""

import sys
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple

from harmonizer.models import Issue, IssueSeverity


def detect_python_version() -> Dict[str, str]:
    """
    Detect current Python interpreter version and executable path.

    This function gathers detailed information about the currently running
    Python interpreter.

    Returns:
        Dictionary containing:
            - "version": Python version string (e.g., "3.10.6")
            - "version_info": Detailed version tuple as string
            - "executable": Full path to Python executable
            - "implementation": Python implementation (CPython, PyPy, etc.)

    EDUCATIONAL NOTE - sys.version_info:
    sys.version_info is a named tuple with these fields:
    - major: Major version number (3 for Python 3.x)
    - minor: Minor version number (10 for Python 3.10)
    - micro: Micro/patch version number (6 for Python 3.10.6)
    - releaselevel: 'alpha', 'beta', 'candidate', or 'final'
    - serial: Serial number for pre-release versions

    Example:
        >>> info = detect_python_version()
        >>> print(f"Python {info['version']} at {info['executable']}")
        Python 3.10.6 at /usr/bin/python3
    """

    version_info = sys.version_info
    version_string = f"{version_info.major}.{version_info.minor}.{version_info.micro}"

    return {
        "version": version_string,
        "version_info": f"{version_info.major}.{version_info.minor}.{version_info.micro} "
        f"({version_info.releaselevel})",
        "executable": sys.executable,
        "implementation": sys.implementation.name,  # CPython, PyPy, etc.
    }


def get_project_python_requirement(project_path: str = ".") -> Optional[str]:
    """
    Detect the Python version requirement specified by the project.

    This function checks various common locations where projects specify
    their required Python version.

    Args:
        project_path: Path to the project directory (default: current directory)

    Returns:
        Required Python version string if found, None otherwise

    EDUCATIONAL NOTE - Project Python Version Specifications:
    Projects can specify Python versions in several files:
    1. .python-version: Used by pyenv and other version managers
    2. pyproject.toml: Modern Python projects (PEP 518)
    3. setup.py: Traditional packaging
    4. runtime.txt: Used by some deployment platforms
    5. .tool-versions: Used by asdf version manager

    We check these in order of specificity and reliability.

    Example .python-version:
        3.10.6

    Example pyproject.toml:
        [tool.poetry.dependencies]
        python = "^3.10"

    Example:
        >>> req = get_project_python_requirement("/path/to/project")
        >>> print(f"Project requires Python {req}")
        Project requires Python 3.10
    """

    project = Path(project_path)

    # Check .python-version (pyenv format)
    python_version_file = project / ".python-version"
    if python_version_file.exists():
        try:
            version = python_version_file.read_text().strip()
            if version:
                return version
        except (OSError, PermissionError):
            pass

    # Check runtime.txt (Heroku and other platforms)
    runtime_file = project / "runtime.txt"
    if runtime_file.exists():
        try:
            content = runtime_file.read_text().strip()
            # Format: "python-3.10.6"
            if content.startswith("python-"):
                return content.replace("python-", "")
        except (OSError, PermissionError):
            pass

    # Check pyproject.toml
    pyproject_file = project / "pyproject.toml"
    if pyproject_file.exists():
        version = _parse_python_version_from_pyproject(pyproject_file)
        if version:
            return version

    # Check setup.py
    setup_file = project / "setup.py"
    if setup_file.exists():
        version = _parse_python_version_from_setup(setup_file)
        if version:
            return version

    # Check .tool-versions (asdf)
    tool_versions_file = project / ".tool-versions"
    if tool_versions_file.exists():
        try:
            content = tool_versions_file.read_text()
            for line in content.splitlines():
                if line.strip().startswith("python"):
                    parts = line.split()
                    if len(parts) >= 2:
                        return parts[1]
        except (OSError, PermissionError):
            pass

    return None


def _parse_python_version_from_pyproject(pyproject_path: Path) -> Optional[str]:
    """
    Parse Python version requirement from pyproject.toml.

    Args:
        pyproject_path: Path to pyproject.toml file

    Returns:
        Python version requirement string or None

    EDUCATIONAL NOTE - TOML Parsing:
    We use simple string parsing here to avoid adding toml/tomli dependency.
    In production code, you might use:
    - tomli (Python < 3.11)
    - tomllib (Python 3.11+, standard library)

    This simplified parser looks for patterns like:
    - python = "^3.10"
    - python = ">=3.10,<4.0"
    - requires-python = ">=3.10"
    """

    try:
        content = pyproject_path.read_text()

        # Look for common patterns
        for line in content.splitlines():
            line = line.strip()

            # Poetry format: python = "^3.10" or python = ">=3.10"
            if line.startswith("python") and "=" in line:
                # Extract version from quotes
                if '"' in line:
                    version_part = line.split('"')[1]
                elif "'" in line:
                    version_part = line.split("'")[1]
                else:
                    continue

                # Clean up common version specifiers
                version_part = (
                    version_part.replace("^", "")
                    .replace("~", "")
                    .replace(">=", "")
                    .split(",")[0]
                    .strip()
                )

                if version_part and version_part[0].isdigit():
                    return version_part

            # PEP 621 format: requires-python = ">=3.10"
            if "requires-python" in line and "=" in line:
                if '"' in line:
                    version_part = line.split('"')[1]
                elif "'" in line:
                    version_part = line.split("'")[1]
                else:
                    continue

                version_part = version_part.replace(">=", "").split(",")[0].strip()

                if version_part and version_part[0].isdigit():
                    return version_part

    except (OSError, PermissionError):
        pass

    return None


def _parse_python_version_from_setup(setup_path: Path) -> Optional[str]:
    """
    Parse Python version requirement from setup.py.

    Args:
        setup_path: Path to setup.py file

    Returns:
        Python version requirement string or None

    EDUCATIONAL NOTE - Parsing setup.py:
    setup.py files typically use python_requires parameter:
        setup(
            name="myproject",
            python_requires=">=3.10",
            ...
        )

    We parse this with simple string matching to avoid executing setup.py
    (which could be a security risk).
    """

    try:
        content = setup_path.read_text()

        # Look for python_requires parameter
        for line in content.splitlines():
            line = line.strip()

            if "python_requires" in line and "=" in line:
                # Extract version from quotes
                if '"' in line:
                    version_part = line.split('"')[1]
                elif "'" in line:
                    version_part = line.split("'")[1]
                else:
                    continue

                # Clean up version specifier
                version_part = version_part.replace(">=", "").split(",")[0].strip()

                if version_part and version_part[0].isdigit():
                    return version_part

    except (OSError, PermissionError):
        pass

    return None


def check_version_compatibility(
    current_version: str, required_version: str
) -> Tuple[bool, Optional[Issue]]:
    """
    Check if current Python version meets project requirements.

    Args:
        current_version: Current Python version (e.g., "3.10.6")
        required_version: Required Python version (e.g., "3.10" or "3.10.0")

    Returns:
        Tuple of (is_compatible, issue)
        - is_compatible: True if version meets requirements
        - issue: Issue object if incompatible, None if compatible

    EDUCATIONAL NOTE - Version Comparison:
    We compare versions component by component (major.minor.micro).
    This is simpler than full version specifier parsing but handles
    the most common cases.

    For full version specifier support, consider using:
    - packaging.version.parse() from the packaging library

    Example:
        >>> compatible, issue = check_version_compatibility("3.10.6", "3.10")
        >>> print(f"Compatible: {compatible}")
        Compatible: True

        >>> compatible, issue = check_version_compatibility("3.9.0", "3.10")
        >>> print(f"Compatible: {compatible}")
        Compatible: False
        >>> print(issue.message)
        Python version mismatch: current 3.9.0, required 3.10+
    """

    try:
        # Parse version strings into tuples of integers
        current_parts = [int(x) for x in current_version.split(".")]
        required_parts = [int(x) for x in required_version.split(".")]

        # Pad shorter version to same length
        max_len = max(len(current_parts), len(required_parts))
        current_parts.extend([0] * (max_len - len(current_parts)))
        required_parts.extend([0] * (max_len - len(required_parts)))

        # Compare versions
        if current_parts >= required_parts:
            return True, None
        else:
            issue = Issue(
                severity=IssueSeverity.ERROR,
                category="python_version",
                message=f"Python version mismatch: current {current_version}, "
                f"required {required_version}+",
                fixable=False,
            )
            return False, issue

    except (ValueError, AttributeError):
        # Version parsing failed - create warning
        issue = Issue(
            severity=IssueSeverity.WARNING,
            category="python_version",
            message=f"Could not parse Python version requirement: {required_version}",
            fixable=False,
        )
        return True, issue  # Allow to proceed but with warning


def get_python_info_summary(project_path: str = ".") -> Dict[str, any]:
    """
    Get comprehensive Python environment information.

    This is a convenience function that combines all Python detection
    functionality into a single call.

    Args:
        project_path: Path to project directory

    Returns:
        Dictionary containing:
            - current: Current Python version info
            - required: Required Python version (if specified)
            - compatible: Whether versions are compatible
            - issue: Issue object if there's a problem

    Example:
        >>> info = get_python_info_summary("/path/to/project")
        >>> print(f"Python {info['current']['version']}")
        >>> if info['required']:
        >>>     print(f"Required: {info['required']}")
        >>>     print(f"Compatible: {info['compatible']}")
    """

    current_info = detect_python_version()
    required_version = get_project_python_requirement(project_path)

    result = {
        "current": current_info,
        "required": required_version,
        "compatible": True,
        "issue": None,
    }

    if required_version:
        compatible, issue = check_version_compatibility(
            current_info["version"], required_version
        )
        result["compatible"] = compatible
        result["issue"] = issue

    return result


# Example usage and testing
if __name__ == "__main__":
    """
    Test the Python detection module.
    """

    print("=" * 60)
    print("Python Detection Module - Test Run")
    print("=" * 60)

    # Detect current Python version
    py_info = detect_python_version()
    print(f"\nCurrent Python:")
    print(f"  Version: {py_info['version']}")
    print(f"  Version Info: {py_info['version_info']}")
    print(f"  Executable: {py_info['executable']}")
    print(f"  Implementation: {py_info['implementation']}")

    # Check for project requirements
    required = get_project_python_requirement(".")
    if required:
        print(f"\nProject Requirement:")
        print(f"  Required Version: {required}")

        compatible, issue = check_version_compatibility(py_info["version"], required)
        print(f"  Compatible: {compatible}")
        if issue:
            print(f"  Issue: {issue.message}")
    else:
        print(f"\nNo Python version requirement found in project")

    # Full summary
    print(f"\n" + "=" * 60)
    print("Full Summary:")
    print("=" * 60)
    summary = get_python_info_summary(".")
    print(f"Current: {summary['current']['version']}")
    print(f"Required: {summary['required'] or 'Not specified'}")
    print(f"Compatible: {summary['compatible']}")
    if summary['issue']:
        print(f"Issue: {summary['issue'].message}")

    print("\n" + "=" * 60)
