"""
Virtual Environment Detection Module.

This module provides functionality to detect various types of Python virtual
environments and their activation status.

EDUCATIONAL NOTE - Why Virtual Environments Matter:
Virtual environments isolate project dependencies to avoid conflicts:
- Different projects can use different versions of the same package
- System Python remains clean and stable
- Easier to reproduce project environments
- Prevents "works on my machine" problems

Common Virtual Environment Types:
1. virtualenv/venv: Standard Python virtual environments (lightweight)
2. conda: Anaconda/Miniconda (handles Python + non-Python packages)
3. pipenv: Combines pip and virtualenv with Pipfile
4. poetry: Modern dependency management with pyproject.toml
"""

import sys
import os
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple

from harmonizer.models import VenvType


def detect_venv_type() -> Dict[str, any]:
    """
    Detect virtual environment type and activation status.

    This function checks multiple indicators to determine what type of
    virtual environment (if any) is currently in use.

    Returns:
        Dictionary containing:
            - "type": VenvType enum value
            - "active": Boolean indicating if venv is active
            - "path": Path to virtual environment (if found)
            - "name": Name of the environment (if applicable)

    DETECTION METHODS:
    1. Environment Variables:
       - VIRTUAL_ENV: Set by venv/virtualenv
       - CONDA_DEFAULT_ENV/CONDA_PREFIX: Set by conda
       - PIPENV_ACTIVE: Set by pipenv
       - POETRY_ACTIVE: Set by poetry

    2. sys.prefix Comparison:
       - In an active venv, sys.prefix != sys.base_prefix

    3. Filesystem Inspection:
       - Look for common venv directory names (venv/, env/, .venv/)
       - Check for pyvenv.cfg, conda-meta/, Pipfile, pyproject.toml

    EDUCATIONAL NOTE - sys.prefix vs sys.base_prefix:
    - sys.prefix: Points to the current Python installation (could be venv)
    - sys.base_prefix: Points to the base Python installation (system Python)
    - If they differ, you're in a virtual environment!

    Example:
        >>> venv_info = detect_venv_type()
        >>> if venv_info["active"]:
        >>>     print(f"Active {venv_info['type'].value} at {venv_info['path']}")
        Active virtualenv at /home/user/project/venv
    """

    # Check for Conda environment
    conda_info = _detect_conda()
    if conda_info["detected"]:
        return {
            "type": VenvType.CONDA,
            "active": conda_info["active"],
            "path": conda_info["path"],
            "name": conda_info["name"],
        }

    # Check for Poetry environment
    poetry_info = _detect_poetry()
    if poetry_info["detected"]:
        return {
            "type": VenvType.POETRY,
            "active": poetry_info["active"],
            "path": poetry_info["path"],
            "name": None,
        }

    # Check for Pipenv environment
    pipenv_info = _detect_pipenv()
    if pipenv_info["detected"]:
        return {
            "type": VenvType.PIPENV,
            "active": pipenv_info["active"],
            "path": pipenv_info["path"],
            "name": None,
        }

    # Check for virtualenv/venv
    venv_info = _detect_virtualenv()
    if venv_info["detected"]:
        return {
            "type": VenvType.VIRTUALENV,
            "active": venv_info["active"],
            "path": venv_info["path"],
            "name": None,
        }

    # No virtual environment detected
    return {"type": VenvType.NONE, "active": False, "path": None, "name": None}


def _detect_conda() -> Dict[str, any]:
    """
    Detect Conda virtual environment.

    Returns:
        Dictionary with detection results

    EDUCATIONAL NOTE - Conda Environments:
    Conda is more than a Python virtual environment - it's a full package
    manager that can handle non-Python dependencies (C libraries, system tools).

    Conda sets these environment variables:
    - CONDA_DEFAULT_ENV: Name of active environment
    - CONDA_PREFIX: Path to active environment
    - CONDA_PYTHON_EXE: Path to conda's Python executable

    Conda environments contain a conda-meta/ directory with package metadata.
    """

    conda_env = os.environ.get("CONDA_DEFAULT_ENV")
    conda_prefix = os.environ.get("CONDA_PREFIX")

    if conda_env or conda_prefix:
        return {
            "detected": True,
            "active": True,
            "path": conda_prefix,
            "name": conda_env,
        }

    # Check if we're in a conda environment but variables aren't set
    # Look for conda-meta directory in sys.prefix
    conda_meta = Path(sys.prefix) / "conda-meta"
    if conda_meta.exists():
        return {
            "detected": True,
            "active": True,
            "path": sys.prefix,
            "name": Path(sys.prefix).name,
        }

    # Check for conda installation (inactive)
    try:
        result = subprocess.run(
            ["conda", "env", "list"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if result.returncode == 0:
            # Conda is installed but no environment is active
            return {"detected": False, "active": False, "path": None, "name": None}
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    return {"detected": False, "active": False, "path": None, "name": None}


def _detect_poetry() -> Dict[str, any]:
    """
    Detect Poetry virtual environment.

    Returns:
        Dictionary with detection results

    EDUCATIONAL NOTE - Poetry:
    Poetry is a modern dependency management tool that:
    - Uses pyproject.toml for configuration (PEP 518)
    - Automatically creates and manages virtual environments
    - Provides deterministic dependency resolution
    - Simplifies package publishing

    Poetry creates venvs in a central location or in the project directory
    depending on configuration.
    """

    # Check for POETRY_ACTIVE environment variable
    if os.environ.get("POETRY_ACTIVE") == "1":
        return {
            "detected": True,
            "active": True,
            "path": sys.prefix,
            "name": None,
        }

    # Check if current directory has pyproject.toml with Poetry config
    pyproject = Path.cwd() / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text()
            if "[tool.poetry]" in content:
                # Poetry project found, check if venv is active
                if sys.prefix != sys.base_prefix:
                    # We're in some venv - could be Poetry's
                    # Check if venv path contains project name (Poetry convention)
                    project_name = Path.cwd().name
                    if project_name.lower() in Path(sys.prefix).name.lower():
                        return {
                            "detected": True,
                            "active": True,
                            "path": sys.prefix,
                            "name": None,
                        }

                # Poetry project but venv not active
                return {"detected": False, "active": False, "path": None, "name": None}
        except (OSError, PermissionError):
            pass

    return {"detected": False, "active": False, "path": None, "name": None}


def _detect_pipenv() -> Dict[str, any]:
    """
    Detect Pipenv virtual environment.

    Returns:
        Dictionary with detection results

    EDUCATIONAL NOTE - Pipenv:
    Pipenv combines pip and virtualenv, using:
    - Pipfile: High-level dependency specification
    - Pipfile.lock: Locked dependencies for reproducibility

    Pipenv creates virtual environments in a central location by default,
    with names based on the project path hash.
    """

    # Check for PIPENV_ACTIVE environment variable
    if os.environ.get("PIPENV_ACTIVE") == "1":
        return {
            "detected": True,
            "active": True,
            "path": sys.prefix,
            "name": None,
        }

    # Check if current directory has Pipfile
    pipfile = Path.cwd() / "Pipfile"
    if pipfile.exists():
        # Pipfile found, check if venv is active
        if sys.prefix != sys.base_prefix:
            # We're in some venv - could be Pipenv's
            return {
                "detected": True,
                "active": True,
                "path": sys.prefix,
                "name": None,
            }

        # Pipfile exists but venv not active
        return {"detected": False, "active": False, "path": None, "name": None}

    return {"detected": False, "active": False, "path": None, "name": None}


def _detect_virtualenv() -> Dict[str, any]:
    """
    Detect standard virtualenv/venv.

    Returns:
        Dictionary with detection results

    EDUCATIONAL NOTE - virtualenv vs venv:
    - venv: Built into Python 3.3+ (python -m venv)
    - virtualenv: Third-party tool with more features

    Both create similar directory structures with:
    - bin/ (or Scripts/ on Windows): Executables including Python
    - lib/: Python packages
    - pyvenv.cfg: Configuration file

    Detection Strategy:
    1. Check VIRTUAL_ENV environment variable (set when activated)
    2. Compare sys.prefix with sys.base_prefix (differ when in venv)
    3. Look for common venv directory names in project
    4. Check for pyvenv.cfg file
    """

    # Check VIRTUAL_ENV environment variable
    virtual_env = os.environ.get("VIRTUAL_ENV")
    if virtual_env:
        return {
            "detected": True,
            "active": True,
            "path": virtual_env,
            "name": None,
        }

    # Check sys.prefix vs sys.base_prefix
    if sys.prefix != sys.base_prefix:
        return {
            "detected": True,
            "active": True,
            "path": sys.prefix,
            "name": None,
        }

    # Check for common venv directories in current project
    project_path = Path.cwd()
    venv_candidates = ["venv", "env", ".venv", "virtualenv", ".env"]

    for candidate in venv_candidates:
        venv_dir = project_path / candidate
        pyvenv_cfg = venv_dir / "pyvenv.cfg"

        if pyvenv_cfg.exists():
            return {
                "detected": True,
                "active": False,  # Not activated
                "path": str(venv_dir),
                "name": None,
            }

    return {"detected": False, "active": False, "path": None, "name": None}


def find_venv_in_directory(directory: str = ".") -> Optional[Path]:
    """
    Search for a virtual environment in the specified directory.

    Args:
        directory: Directory to search (default: current directory)

    Returns:
        Path to virtual environment if found, None otherwise

    EDUCATIONAL NOTE - Filesystem Search:
    This function performs a filesystem search for virtual environment
    indicators. It's useful when:
    - No environment is currently activated
    - You want to find all venvs in a project
    - Scanning projects without activating them

    Example:
        >>> venv_path = find_venv_in_directory("/path/to/project")
        >>> if venv_path:
        >>>     print(f"Found venv at: {venv_path}")
    """

    search_path = Path(directory)

    # Common venv directory names
    venv_names = ["venv", "env", ".venv", "virtualenv", ".env"]

    # Check direct children first
    for venv_name in venv_names:
        venv_dir = search_path / venv_name

        # Check for pyvenv.cfg (definitive indicator)
        if (venv_dir / "pyvenv.cfg").exists():
            return venv_dir

        # Check for conda-meta (Conda environment)
        if (venv_dir / "conda-meta").exists():
            return venv_dir

    # Check for Poetry/Pipenv project markers
    if (search_path / "pyproject.toml").exists():
        # Poetry creates venvs elsewhere, return marker
        return search_path / "pyproject.toml"

    if (search_path / "Pipfile").exists():
        # Pipenv creates venvs elsewhere, return marker
        return search_path / "Pipfile"

    return None


def get_venv_python_executable(venv_path: str) -> Optional[str]:
    """
    Get the path to the Python executable within a virtual environment.

    Args:
        venv_path: Path to virtual environment directory

    Returns:
        Path to Python executable if found, None otherwise

    EDUCATIONAL NOTE - Virtual Environment Structure:
    Virtual environments have different structures on different platforms:

    Linux/macOS:
        venv/
        ├── bin/
        │   ├── python      (symlink to python3)
        │   ├── python3     (actual executable)
        │   ├── pip
        │   └── activate
        └── lib/

    Windows:
        venv/
        ├── Scripts/
        │   ├── python.exe
        │   ├── pip.exe
        │   └── activate.bat
        └── Lib/

    Example:
        >>> python_exe = get_venv_python_executable("/path/to/venv")
        >>> print(f"Python: {python_exe}")
        Python: /path/to/venv/bin/python3
    """

    venv_dir = Path(venv_path)

    # Unix-like systems (Linux, macOS, WSL)
    unix_python = venv_dir / "bin" / "python3"
    if unix_python.exists():
        return str(unix_python)

    unix_python_alt = venv_dir / "bin" / "python"
    if unix_python_alt.exists():
        return str(unix_python_alt)

    # Windows
    windows_python = venv_dir / "Scripts" / "python.exe"
    if windows_python.exists():
        return str(windows_python)

    return None


def get_venv_activation_command(
    venv_path: str, shell: str = "bash"
) -> Optional[str]:
    """
    Get the command to activate a virtual environment.

    Args:
        venv_path: Path to virtual environment directory
        shell: Shell type (bash, zsh, fish, powershell, cmd)

    Returns:
        Activation command string or None

    EDUCATIONAL NOTE - Virtual Environment Activation:
    Activating a virtual environment modifies your shell to:
    1. Prepend venv's bin/ directory to PATH
    2. Set VIRTUAL_ENV environment variable
    3. Modify shell prompt to show venv is active

    Different shells have different activation scripts:
    - bash/zsh: source venv/bin/activate
    - fish: source venv/bin/activate.fish
    - PowerShell: venv\\Scripts\\Activate.ps1
    - cmd.exe: venv\\Scripts\\activate.bat

    Example:
        >>> cmd = get_venv_activation_command("/path/to/venv", "bash")
        >>> print(f"Run: {cmd}")
        Run: source /path/to/venv/bin/activate
    """

    venv_dir = Path(venv_path)

    activation_scripts = {
        "bash": venv_dir / "bin" / "activate",
        "zsh": venv_dir / "bin" / "activate",
        "fish": venv_dir / "bin" / "activate.fish",
        "powershell": venv_dir / "Scripts" / "Activate.ps1",
        "cmd": venv_dir / "Scripts" / "activate.bat",
    }

    script = activation_scripts.get(shell.lower())
    if script and script.exists():
        if shell.lower() in ["bash", "zsh"]:
            return f"source {script}"
        elif shell.lower() == "fish":
            return f"source {script}"
        elif shell.lower() == "powershell":
            return str(script)
        elif shell.lower() == "cmd":
            return str(script)

    return None


# Example usage and testing
if __name__ == "__main__":
    """
    Test the virtual environment detection module.
    """

    print("=" * 60)
    print("Virtual Environment Detection Module - Test Run")
    print("=" * 60)

    # Detect current venv
    venv_info = detect_venv_type()
    print(f"\nVirtual Environment:")
    print(f"  Type: {venv_info['type'].value}")
    print(f"  Active: {venv_info['active']}")
    print(f"  Path: {venv_info['path'] or 'N/A'}")
    print(f"  Name: {venv_info['name'] or 'N/A'}")

    # Check sys.prefix information
    print(f"\nPython Prefix Information:")
    print(f"  sys.prefix: {sys.prefix}")
    print(f"  sys.base_prefix: {sys.base_prefix}")
    print(f"  In venv: {sys.prefix != sys.base_prefix}")

    # Search for venv in current directory
    print(f"\nSearching for venv in current directory...")
    venv_path = find_venv_in_directory(".")
    if venv_path:
        print(f"  Found: {venv_path}")

        python_exe = get_venv_python_executable(str(venv_path))
        if python_exe:
            print(f"  Python: {python_exe}")

        bash_cmd = get_venv_activation_command(str(venv_path), "bash")
        if bash_cmd:
            print(f"  Activate (bash): {bash_cmd}")
    else:
        print(f"  No venv found")

    print("\n" + "=" * 60)
