"""
Dependency Detection Module.

This module provides functionality to scan for Python dependencies and detect
missing or outdated packages in a project.

EDUCATIONAL NOTE - Why Dependency Detection Matters:
Managing dependencies is crucial for project reproducibility and collaboration:
- requirements.txt: Simple list of packages (pip freeze format)
- pyproject.toml: Modern Python packaging standard (PEP 518)
- setup.py: Legacy packaging format
- Pipfile: Used by pipenv for dependency management

Missing dependencies cause:
- Import errors when running code
- Silent failures in untested code paths
- Environment inconsistencies between developers
- Deployment issues in production
"""

import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import re

from harmonizer.utils.subprocess_utils import run_command_safe


def scan_dependencies(project_path: str) -> Dict[str, any]:
    """
    Scan for missing or outdated dependencies in a project.

    This function checks for various dependency file formats and determines
    which packages are required but not installed.

    DETECTION STRATEGY:
    1. Look for requirements.txt (most common)
    2. Look for pyproject.toml (modern standard)
    3. Look for setup.py (legacy packaging)
    4. Look for Pipfile (pipenv)
    5. Parse each file found and extract package requirements
    6. Check which packages are installed
    7. Identify missing packages

    Args:
        project_path: Path to the project directory to scan

    Returns:
        Dictionary containing:
            - requirements_file: Path to requirements file (if found)
            - required_packages: List of required package names
            - installed_packages: List of currently installed packages
            - missing_packages: List of required but missing packages
            - extra_packages: List of installed but not required packages

    EDUCATIONAL NOTE - Dependency File Formats:
    - requirements.txt: Simple format, one package per line
      Example: requests==2.28.1
               flask>=2.0.0
    - pyproject.toml: TOML format with [tool.poetry.dependencies] or [project.dependencies]
    - Pipfile: TOML-like format used by pipenv
    - setup.py: Python code, look for install_requires

    Example:
        >>> results = scan_dependencies("/path/to/project")
        >>> print(f"Missing: {results['missing_packages']}")
        Missing: ['requests', 'flask']
    """

    project = Path(project_path)
    results = {
        "requirements_file": None,
        "required_packages": [],
        "installed_packages": [],
        "missing_packages": [],
        "extra_packages": [],
    }

    # Get installed packages
    results["installed_packages"] = get_installed_packages()

    # Check for requirements.txt
    req_txt = project / "requirements.txt"
    if req_txt.exists():
        results["requirements_file"] = str(req_txt)
        results["required_packages"] = parse_requirements_txt(req_txt)
        results["missing_packages"] = find_missing_packages(
            results["required_packages"], results["installed_packages"]
        )
        return results

    # Check for pyproject.toml
    pyproject = project / "pyproject.toml"
    if pyproject.exists():
        results["requirements_file"] = str(pyproject)
        results["required_packages"] = parse_pyproject_toml(pyproject)
        results["missing_packages"] = find_missing_packages(
            results["required_packages"], results["installed_packages"]
        )
        return results

    # Check for setup.py
    setup_py = project / "setup.py"
    if setup_py.exists():
        results["requirements_file"] = str(setup_py)
        results["required_packages"] = parse_setup_py(setup_py)
        results["missing_packages"] = find_missing_packages(
            results["required_packages"], results["installed_packages"]
        )
        return results

    # Check for Pipfile
    pipfile = project / "Pipfile"
    if pipfile.exists():
        results["requirements_file"] = str(pipfile)
        results["required_packages"] = parse_pipfile(pipfile)
        results["missing_packages"] = find_missing_packages(
            results["required_packages"], results["installed_packages"]
        )
        return results

    # No dependency file found
    return results


def parse_requirements_txt(req_file: Path) -> List[str]:
    """
    Parse requirements.txt file and extract package names.

    Args:
        req_file: Path to requirements.txt file

    Returns:
        List of package names (without version specifiers)

    EDUCATIONAL NOTE - Requirements.txt Format:
    The requirements.txt format supports:
    - Simple names: requests
    - Version specifiers: requests==2.28.1, flask>=2.0.0
    - Comments: # This is a comment
    - Blank lines
    - Git URLs: git+https://github.com/user/repo.git
    - Local paths: ./local-package
    - Environment markers: requests; python_version>='3.7'

    We extract just the package name, ignoring version specifiers.
    """

    packages = []

    try:
        with open(req_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                # Skip -r (include other requirements files) and -e (editable installs)
                if line.startswith("-r") or line.startswith("-e"):
                    continue

                # Skip git URLs (for now)
                if line.startswith("git+"):
                    continue

                # Handle environment markers (e.g., "requests; python_version>='3.7'")
                if ";" in line:
                    line = line.split(";")[0].strip()

                # Extract package name (before version specifiers)
                # Handle: ==, >=, <=, >, <, ~=, !=
                package = re.split(r"[=<>!~]", line)[0].strip()

                # Handle extras (e.g., "requests[security]")
                if "[" in package:
                    package = package.split("[")[0].strip()

                if package:
                    packages.append(package)

    except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
        # File can't be read, return empty list
        pass

    return packages


def parse_pyproject_toml(pyproject_file: Path) -> List[str]:
    """
    Parse pyproject.toml file and extract dependencies.

    Args:
        pyproject_file: Path to pyproject.toml file

    Returns:
        List of package names

    EDUCATIONAL NOTE - pyproject.toml:
    PEP 518 introduced pyproject.toml as a standard configuration file.
    Different tools use different sections:
    - Poetry: [tool.poetry.dependencies]
    - Setuptools: [project.dependencies]
    - Flit: [project.dependencies]

    We attempt to parse all common formats.

    NOTE: This is a simple parser. For production use, consider using
    the 'toml' or 'tomli' library for robust TOML parsing.
    """

    packages = []

    try:
        with open(pyproject_file, "r", encoding="utf-8") as f:
            content = f.read()

            # Simple pattern matching (not a full TOML parser)
            # Look for dependencies sections

            # Pattern for Poetry: package = "^1.2.3" or package = { version = "^1.2.3" }
            poetry_deps = re.findall(
                r'^\s*([a-zA-Z0-9_-]+)\s*=\s*["\'{]', content, re.MULTILINE
            )

            # Pattern for PEP 621: dependencies = ["package>=1.0", ...]
            pep621_match = re.search(
                r"dependencies\s*=\s*\[(.*?)\]", content, re.DOTALL
            )

            if pep621_match:
                # Parse the list of dependencies
                deps_str = pep621_match.group(1)
                # Extract package names from quoted strings
                dep_packages = re.findall(r'["\']([a-zA-Z0-9_-]+)', deps_str)
                packages.extend(dep_packages)
            elif poetry_deps:
                # Filter out common Poetry configuration keys
                excluded = {
                    "python",
                    "version",
                    "description",
                    "authors",
                    "readme",
                    "homepage",
                    "repository",
                    "documentation",
                    "keywords",
                    "classifiers",
                    "license",
                }
                packages.extend(
                    [pkg for pkg in poetry_deps if pkg.lower() not in excluded]
                )

    except (FileNotFoundError, PermissionError, UnicodeDecodeError):
        pass

    return list(set(packages))  # Remove duplicates


def parse_setup_py(setup_file: Path) -> List[str]:
    """
    Parse setup.py file and extract dependencies from install_requires.

    Args:
        setup_file: Path to setup.py file

    Returns:
        List of package names

    EDUCATIONAL NOTE - setup.py Parsing:
    setup.py is executable Python code, which makes it dangerous to parse
    by execution. We use regex pattern matching instead to extract the
    install_requires list without executing the code.

    This is safer but less accurate than executing the file.
    For production use, consider using ast module to parse Python safely.

    SECURITY NOTE:
    Never use exec() or eval() on untrusted setup.py files!
    Always use static analysis (regex, ast) instead.
    """

    packages = []

    try:
        with open(setup_file, "r", encoding="utf-8") as f:
            content = f.read()

            # Look for install_requires=[...]
            match = re.search(r"install_requires\s*=\s*\[(.*?)\]", content, re.DOTALL)

            if match:
                requires_str = match.group(1)
                # Extract package names from quoted strings
                package_matches = re.findall(r'["\']([a-zA-Z0-9_-]+)', requires_str)
                packages.extend(package_matches)

    except (FileNotFoundError, PermissionError, UnicodeDecodeError):
        pass

    return packages


def parse_pipfile(pipfile: Path) -> List[str]:
    """
    Parse Pipfile and extract dependencies.

    Args:
        pipfile: Path to Pipfile

    Returns:
        List of package names

    EDUCATIONAL NOTE - Pipfile:
    Pipfile is used by pipenv for dependency management.
    It uses TOML-like syntax with [packages] and [dev-packages] sections.

    Example Pipfile:
        [packages]
        requests = "*"
        flask = ">=2.0.0"

        [dev-packages]
        pytest = "*"
    """

    packages = []

    try:
        with open(pipfile, "r", encoding="utf-8") as f:
            content = f.read()

            # Look for [packages] section
            packages_match = re.search(r"\[packages\](.*?)(?:\[|$)", content, re.DOTALL)

            if packages_match:
                packages_str = packages_match.group(1)
                # Extract package names (before = sign)
                package_names = re.findall(
                    r"^([a-zA-Z0-9_-]+)\s*=", packages_str, re.MULTILINE
                )
                packages.extend(package_names)

    except (FileNotFoundError, PermissionError, UnicodeDecodeError):
        pass

    return packages


def get_installed_packages() -> List[str]:
    """
    Get list of currently installed Python packages.

    Returns:
        List of installed package names (lowercase)

    EDUCATIONAL NOTE - Package Detection:
    We use 'pip list' to get installed packages because:
    1. It's cross-platform and reliable
    2. Works with all virtual environment types
    3. Doesn't require importing pkg_resources (slower)

    Alternative methods:
    - pkg_resources.working_set (slower, requires setuptools)
    - importlib.metadata.distributions() (Python 3.8+, faster)

    GOTCHAS:
    - Package names are case-insensitive in Python
    - Some packages have different import names vs package names
      (e.g., package: Pillow, import: PIL)
    """

    packages = []

    # Run pip list --format=freeze to get package names
    success, stdout, _ = run_command_safe(
        [sys.executable, "-m", "pip", "list", "--format=freeze"], timeout=10
    )

    if success:
        for line in stdout.splitlines():
            line = line.strip()
            if line and "==" in line:
                # Extract package name (before ==)
                package = line.split("==")[0].strip().lower()
                packages.append(package)
    else:
        # If pip list fails, try using importlib.metadata (Python 3.8+)
        try:
            from importlib import metadata

            packages = [dist.name.lower() for dist in metadata.distributions()]
        except ImportError:
            # Fallback: return empty list
            pass

    return packages


def find_missing_packages(required: List[str], installed: List[str]) -> List[str]:
    """
    Find packages that are required but not installed.

    Args:
        required: List of required package names
        installed: List of installed package names

    Returns:
        List of missing package names

    EDUCATIONAL NOTE - Set Operations:
    We use set operations for efficient comparison:
    - Convert lists to sets
    - Use set difference (required - installed)
    - Convert back to list

    This is O(n) time complexity vs O(n²) for nested loops.

    GOTCHAS:
    - Package names are case-insensitive
    - Some packages have aliases (numpy vs numpy-base)
    - We normalize to lowercase for comparison
    """

    # Normalize to lowercase for case-insensitive comparison
    required_set = {pkg.lower() for pkg in required}
    installed_set = {pkg.lower() for pkg in installed}

    # Find missing packages
    missing = required_set - installed_set

    return sorted(list(missing))


def check_package_installed(package_name: str) -> bool:
    """
    Check if a specific package is installed.

    Args:
        package_name: Name of the package to check

    Returns:
        True if package is installed, False otherwise

    EDUCATIONAL NOTE - Individual Package Check:
    For checking a single package, 'pip show' is more efficient than
    'pip list' because it exits early once the package is found.

    This is useful for targeted checks during fix operations.
    """

    success, _, _ = run_command_safe(
        [sys.executable, "-m", "pip", "show", package_name], timeout=5
    )
    return success


def get_package_version(package_name: str) -> Optional[str]:
    """
    Get the installed version of a package.

    Args:
        package_name: Name of the package

    Returns:
        Version string if installed, None if not installed

    Example:
        >>> version = get_package_version("requests")
        >>> print(version)
        2.28.1
    """

    success, stdout, _ = run_command_safe(
        [sys.executable, "-m", "pip", "show", package_name], timeout=5
    )

    if success:
        # Parse output for Version: line
        for line in stdout.splitlines():
            if line.startswith("Version:"):
                return line.split(":", 1)[1].strip()

    return None


# Example usage and testing
if __name__ == "__main__":
    """
    Test the dependency detection module.
    """

    print("=" * 60)
    print("Dependency Detection Module - Test Run")
    print("=" * 60)

    # Test on current directory
    results = scan_dependencies(".")

    print(f"\nRequirements File: {results['requirements_file']}")
    print(f"Required Packages: {len(results['required_packages'])}")
    if results["required_packages"]:
        print(f"  {', '.join(results['required_packages'][:10])}")
        if len(results["required_packages"]) > 10:
            print(f"  ... and {len(results['required_packages']) - 10} more")

    print(f"\nInstalled Packages: {len(results['installed_packages'])}")
    print(f"Missing Packages: {len(results['missing_packages'])}")
    if results["missing_packages"]:
        print(f"  {', '.join(results['missing_packages'])}")

    print("\n" + "=" * 60)
