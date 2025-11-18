# Claude.md - Environment Harmonizer Development Guide

## Project Overview

**Environment Harmonizer** is a Python-based CLI and programmatic tool that scans project directories to analyze and harmonize developer environments. It detects environment inconsistencies, Python version mismatches, virtual environment states, missing dependencies, and OS-specific quirks (Windows vs WSL).

### Core Purpose
The tool acts as a "dev-environment butler" ensuring consistency, predictability, and readiness before coding begins. It improves developer ergonomics and reduces environment-related frustrations and bugs.

### Target Audience
- Beginner developers learning about environment management
- Teams collaborating across different platforms
- Developers returning to projects after time away

### Complexity Level
Medium complexity, designed for 2-3 weeks of development with educational focus.

---

## Architecture & Design Principles

### High-Level Architecture

```
┌───────────────────────────┐
│  Command Line Interface   │
│  (argparse entry point)   │
└────────────┬──────────────┘
             │
             ▼
┌───────────────────────────────────┐
│  Environment Scanner Module       │
│  - OS Detection                   │
│  - Python Version Detection       │
│  - Virtual Env Detection          │
│  - Dependency Scanning            │
└────────────┬──────────────────────┘
             │
             ▼
┌───────────────────────────────────┐
│  EnvironmentStatus Data Model     │
│  (Centralized state storage)      │
└────────────┬──────────────────────┘
             │
             ▼
┌───────────────────────────────────┐
│  Diagnostic Report Generator      │
│  - Text format                    │
│  - JSON format                    │
└────────────┬──────────────────────┘
             │
             ▼
┌───────────────────────────────────┐
│  Automated Fix Module (optional)  │
│  - Dry-run mode                   │
│  - Safe fix application           │
└───────────────────────────────────┘
```

### Design Principles

1. **Modularity**: Separate concerns into distinct modules (detection, scanning, reporting, fixing)
2. **Dual Interface**: Support both CLI and programmatic API usage
3. **Safety First**: All automated fixes should have dry-run mode and user confirmation
4. **Educational**: Embed teaching aids throughout (inline comments, CLI tooltips, examples)
5. **Standard Library First**: Minimize external dependencies for portability
6. **Progressive Disclosure**: CLI help provides information appropriate to user's context

---

## Technology Stack

### Core Technologies
- **Language**: Python 3.7+
- **CLI Framework**: `argparse` (standard library)
- **Data Format**: JSON (for config and reports)

### Standard Libraries Used
- `argparse`: Command-line argument parsing
- `pathlib`: Modern filesystem path handling
- `json`: Configuration and report serialization
- `platform`: OS and system detection
- `subprocess`: External command execution
- `dataclasses`: Structured data modeling (Python 3.7+)
- `sys`: System-specific parameters and functions
- `os`: Operating system interfaces
- `typing`: Type hints for better code clarity

### Optional Libraries (Future)
- `colorama`: Cross-platform colored terminal output
- `click`: Alternative CLI framework (considered but deferred)
- `pytest`: Testing framework
- `PyInstaller`: Binary executable creation

### Why This Stack?
- **Beginner-friendly**: Uses familiar Python standard library
- **Portable**: Minimal dependencies reduce installation friction
- **Educational**: Standard library teaches core Python concepts
- **Quick development**: Aligns with 2-3 week timeline

---

## Project Structure

### Recommended Directory Layout

```
environment-harmonizer/
├── .git/                       # Git repository
├── .gitignore                  # Git ignore patterns
├── README.md                   # User-facing documentation
├── claude.md                   # This file - AI assistant guide
├── setup.py                    # Package installation script
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Development dependencies
│
├── harmonizer/                 # Main source code package
│   ├── __init__.py            # Package initialization
│   ├── __main__.py            # CLI entry point
│   ├── cli.py                 # Command-line interface logic
│   ├── models.py              # Data models (EnvironmentStatus)
│   ├── detectors/             # Detection modules
│   │   ├── __init__.py
│   │   ├── os_detector.py     # Windows vs WSL detection
│   │   ├── python_detector.py # Python version detection
│   │   ├── venv_detector.py   # Virtual environment detection
│   │   └── dependency_detector.py # Dependency scanning
│   ├── scanners/              # Scanning logic
│   │   ├── __init__.py
│   │   ├── project_scanner.py # Main scanning orchestration
│   │   └── config_scanner.py  # Configuration file scanning
│   ├── reporters/             # Report generation
│   │   ├── __init__.py
│   │   ├── text_reporter.py   # Human-readable reports
│   │   └── json_reporter.py   # JSON format reports
│   ├── fixers/                # Automated fix modules
│   │   ├── __init__.py
│   │   ├── base_fixer.py      # Base fixer class
│   │   ├── venv_fixer.py      # Virtual environment fixes
│   │   └── dependency_fixer.py # Dependency installation
│   └── utils/                 # Utility functions
│       ├── __init__.py
│       ├── logger.py          # Logging configuration
│       └── validators.py      # Input validation
│
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── test_detectors/
│   ├── test_scanners/
│   ├── test_reporters/
│   ├── test_fixers/
│   └── fixtures/              # Test fixtures and sample projects
│
├── examples/                  # Example projects for testing
│   ├── sample_project_1/      # Clean environment example
│   ├── sample_project_2/      # Missing dependencies example
│   └── sample_project_3/      # Version mismatch example
│
├── docs/                      # Additional documentation
│   ├── user_guide.md
│   ├── api_reference.md
│   └── troubleshooting.md
│
└── logs/                      # Runtime logs (gitignored)
```

### File Purposes

- **harmonizer/__main__.py**: Entry point allowing `python -m harmonizer`
- **harmonizer/cli.py**: Argument parsing and CLI flow control
- **harmonizer/models.py**: EnvironmentStatus dataclass and related models
- **detectors/**: Individual detection modules for each aspect
- **scanners/**: Orchestrate detections and aggregate results
- **reporters/**: Generate different report formats
- **fixers/**: Apply automated corrections
- **utils/**: Cross-cutting concerns (logging, validation)

---

## Core Data Models

### EnvironmentStatus Dataclass

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

class OSType(Enum):
    WINDOWS_NATIVE = "windows_native"
    WSL = "wsl"
    LINUX = "linux"
    MACOS = "macos"
    UNKNOWN = "unknown"

class VenvType(Enum):
    VIRTUALENV = "virtualenv"
    CONDA = "conda"
    PIPENV = "pipenv"
    POETRY = "poetry"
    NONE = "none"

class IssueSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

@dataclass
class Issue:
    """Represents a detected environment issue"""
    severity: IssueSeverity
    category: str  # e.g., "python_version", "dependency", "config"
    message: str
    fixable: bool = False
    fix_command: Optional[str] = None

@dataclass
class EnvironmentStatus:
    """Main data structure holding all environment scan results"""

    # OS Information
    os_type: OSType
    os_version: str

    # Python Information
    python_version: str
    python_executable: str

    # Virtual Environment
    venv_type: VenvType
    venv_active: bool
    venv_path: Optional[str] = None

    # Project Information
    project_path: str
    config_files: List[str] = field(default_factory=list)

    # Dependencies
    requirements_file: Optional[str] = None
    installed_packages: List[str] = field(default_factory=list)
    missing_packages: List[str] = field(default_factory=list)

    # Issues
    issues: List[Issue] = field(default_factory=list)

    # System Information
    path_variables: Dict[str, str] = field(default_factory=dict)
    environment_variables: Dict[str, str] = field(default_factory=dict)
```

---

## Implementation Phases

### Phase 1: Foundations & Setup (Steps 1-10)
**Goal**: Establish project structure and basic detection capabilities

**Key Deliverables**:
- Git repository with .gitignore and README
- Python virtual environment setup
- Main entry point script
- EnvironmentStatus dataclass
- OS detection (Windows vs WSL)
- Python version detection
- Virtual environment type detection
- Configuration loading/saving
- Basic CLI argument parsing
- Integration of detection functions

**Educational Focus**:
- Teach dataclasses vs traditional classes
- Platform detection techniques
- Virtual environment concepts

### Phase 2: Core Functionality (Steps 11-20)
**Goal**: Implement scanning, issue detection, and reporting

**Key Deliverables**:
- Dependency scanning (requirements.txt, pyproject.toml)
- Config file detection
- Issue tracking in EnvironmentStatus
- Formatted diagnostic report generation
- CLI text output with formatting
- JSON report output option
- Enhanced help messages
- Python version mismatch detection
- WSL vs Windows quirk detection
- Code refactoring for modularity

**Educational Focus**:
- Dependency management concepts
- Report formatting techniques
- Cross-platform compatibility issues

### Phase 3: Advanced Features (Steps 21-30)
**Goal**: Add automated fixes and enhanced detection

**Key Deliverables**:
- Pipx detection
- Automated fix framework with dry-run
- Virtual environment activation fixes
- Automatic dependency installation
- Config file updating
- `--fix` CLI flag
- Edge case handling (no config files)
- System PATH analysis
- Robust subprocess-based detection
- Issue severity and fixability tagging

**Educational Focus**:
- Safe automation practices
- Subprocess management
- Error handling patterns

### Phase 4: Polish & Testing (Steps 31-40)
**Goal**: Harden reliability and improve UX

**Key Deliverables**:
- Exception handling for subprocess calls
- Unit tests (OS detection, Python detection, dependency scanning)
- Integration tests (full CLI scan)
- Progress messages and colored output
- Rotating file logs
- Performance measurement
- Input validation
- Fallback scanning for unsupported OS
- Temporary file cleanup

**Educational Focus**:
- Testing strategies
- Logging best practices
- Performance optimization

### Phase 5: Documentation & Release (Steps 41-50)
**Goal**: Prepare for distribution and end-user adoption

**Key Deliverables**:
- User guide (installation, usage)
- Example projects with reports
- API usage documentation
- setup.py for pip installation
- Testing instructions and badges
- Code formatting/linting
- PyInstaller binary (optional)
- Troubleshooting documentation
- Release notes
- Git release tag (v1.0.0)

**Educational Focus**:
- Documentation best practices
- Package distribution
- Release management

---

## Key Detection Strategies

### OS Detection (Windows vs WSL)

```python
import platform
import os
import subprocess

def detect_os_type():
    """
    Detect operating system type with special handling for WSL.

    WSL Detection Strategy:
    1. Check for /proc/version containing "microsoft" (WSL 1 & 2)
    2. Check for /proc/sys/kernel/osrelease containing "WSL"
    3. Check WSLENV environment variable
    4. Fallback to platform.system()
    """

    # WSL Detection
    if platform.system() == "Linux":
        # Method 1: Check /proc/version
        try:
            with open("/proc/version", "r") as f:
                if "microsoft" in f.read().lower():
                    return OSType.WSL
        except FileNotFoundError:
            pass

        # Method 2: Check for WSLENV
        if "WSLENV" in os.environ:
            return OSType.WSL

        return OSType.LINUX

    # Windows Native
    elif platform.system() == "Windows":
        return OSType.WINDOWS_NATIVE

    # macOS
    elif platform.system() == "Darwin":
        return OSType.MACOS

    return OSType.UNKNOWN
```

### Virtual Environment Detection

```python
import os
import sys
from pathlib import Path

def detect_venv_type():
    """
    Detect virtual environment type and activation status.

    Detection Methods:
    1. VIRTUAL_ENV environment variable (virtualenv, venv)
    2. CONDA_DEFAULT_ENV or CONDA_PREFIX (conda)
    3. PIPENV_ACTIVE (pipenv)
    4. POETRY_ACTIVE (poetry)
    5. sys.prefix vs sys.base_prefix difference
    """

    # Check environment variables
    if "VIRTUAL_ENV" in os.environ:
        venv_path = os.environ["VIRTUAL_ENV"]
        return VenvType.VIRTUALENV, True, venv_path

    if "CONDA_DEFAULT_ENV" in os.environ or "CONDA_PREFIX" in os.environ:
        conda_path = os.environ.get("CONDA_PREFIX", "")
        return VenvType.CONDA, True, conda_path

    if "PIPENV_ACTIVE" in os.environ:
        return VenvType.PIPENV, True, None

    # Check sys.prefix (works for venv module)
    if sys.prefix != sys.base_prefix:
        return VenvType.VIRTUALENV, True, sys.prefix

    # Check for local venv directories
    project_path = Path.cwd()
    venv_candidates = ["venv", "env", ".venv", "virtualenv"]

    for candidate in venv_candidates:
        venv_dir = project_path / candidate
        if venv_dir.exists() and (venv_dir / "pyvenv.cfg").exists():
            return VenvType.VIRTUALENV, False, str(venv_dir)

    return VenvType.NONE, False, None
```

### Python Version Detection

```python
import sys
import subprocess
from pathlib import Path

def detect_python_version():
    """
    Detect Python version information.

    Returns:
    - Current interpreter version
    - Interpreter executable path
    - Project's required version (if specified)
    """

    current_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    executable = sys.executable

    # Check for .python-version file
    python_version_file = Path.cwd() / ".python-version"
    required_version = None

    if python_version_file.exists():
        required_version = python_version_file.read_text().strip()

    # Check pyproject.toml for python version requirement
    pyproject_file = Path.cwd() / "pyproject.toml"
    if pyproject_file.exists() and not required_version:
        # Parse pyproject.toml for python version
        # This is simplified - would use toml library in practice
        content = pyproject_file.read_text()
        if "python" in content:
            # Extract version requirement
            pass

    return {
        "current": current_version,
        "executable": executable,
        "required": required_version
    }
```

### Dependency Scanning

```python
from pathlib import Path
import subprocess

def scan_dependencies(project_path):
    """
    Scan for missing or outdated dependencies.

    Checks:
    1. requirements.txt
    2. pyproject.toml
    3. setup.py
    4. Pipfile
    """

    project = Path(project_path)
    requirements_file = None
    missing_packages = []

    # Check for requirements.txt
    req_txt = project / "requirements.txt"
    if req_txt.exists():
        requirements_file = str(req_txt)
        missing_packages = check_requirements_txt(req_txt)

    # Check for pyproject.toml
    pyproject = project / "pyproject.toml"
    if pyproject.exists() and not requirements_file:
        requirements_file = str(pyproject)
        # Parse and check dependencies

    return {
        "requirements_file": requirements_file,
        "missing_packages": missing_packages
    }

def check_requirements_txt(req_file):
    """Check which packages from requirements.txt are not installed."""
    missing = []

    with open(req_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Parse package name (handle ==, >=, etc.)
            package = line.split("==")[0].split(">=")[0].split("<=")[0].strip()

            # Check if installed
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "show", package],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode != 0:
                    missing.append(package)
            except subprocess.TimeoutExpired:
                pass

    return missing
```

---

## CLI Design

### Command Structure

```bash
# Basic scan (text output)
python -m harmonizer

# Scan specific directory
python -m harmonizer /path/to/project

# JSON output
python -m harmonizer --json

# Apply fixes (dry-run first)
python -m harmonizer --fix --dry-run

# Apply fixes for real
python -m harmonizer --fix

# Verbose output with logging
python -m harmonizer --verbose

# Specific checks only
python -m harmonizer --check python --check venv
```

### Argument Specification

```python
import argparse

def create_parser():
    """Create CLI argument parser with comprehensive help."""

    parser = argparse.ArgumentParser(
        prog="harmonizer",
        description="Environment Harmonizer - Detect and fix environment inconsistencies",
        epilog="For more information, visit: https://github.com/yourrepo/environment-harmonizer"
    )

    parser.add_argument(
        "project_path",
        nargs="?",
        default=".",
        help="Path to project directory to scan (default: current directory)"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output report in JSON format instead of text"
    )

    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically apply fixes to detected issues"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what fixes would be applied without actually applying them"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output with detailed logging"
    )

    parser.add_argument(
        "--check",
        action="append",
        choices=["os", "python", "venv", "dependencies", "config"],
        help="Run specific checks only (can be specified multiple times)"
    )

    parser.add_argument(
        "--output", "-o",
        help="Write report to file instead of stdout"
    )

    return parser
```

### Report Format Examples

#### Text Report
```
================================================================================
ENVIRONMENT HARMONIZER - Diagnostic Report
================================================================================

Project Path: /home/user/myproject
Scan Time: 2025-01-15 14:30:22

[OS ENVIRONMENT]
  Type: WSL (Windows Subsystem for Linux)
  Version: Ubuntu 22.04.1 LTS
  Status: ✓ OK

[PYTHON ENVIRONMENT]
  Version: 3.10.6
  Executable: /home/user/myproject/venv/bin/python
  Required: 3.10.x
  Status: ✓ OK

[VIRTUAL ENVIRONMENT]
  Type: virtualenv
  Active: Yes
  Path: /home/user/myproject/venv
  Status: ✓ OK

[DEPENDENCIES]
  Requirements File: requirements.txt
  Total Packages: 15
  Missing Packages: 2
    ⚠ requests (required by requirements.txt)
    ⚠ pytest (required by requirements.txt)
  Status: ⚠ WARNING

[CONFIGURATION FILES]
  Found: .env, .gitignore, pyproject.toml
  Missing: .editorconfig (recommended)
  Status: ℹ INFO

[DETECTED ISSUES] (3 total)

  [ERROR] Missing dependencies
    2 required packages are not installed
    Fixable: Yes
    Fix: pip install -r requirements.txt

  [WARNING] WSL path handling
    Project path contains Windows-style path separators
    Fixable: No
    Recommendation: Use Unix-style paths in WSL

  [INFO] No .editorconfig found
    Consider adding .editorconfig for consistent code style
    Fixable: No

================================================================================
Summary: 1 error, 1 warning, 1 info
Run with --fix to apply automated fixes
================================================================================
```

#### JSON Report
```json
{
  "scan_time": "2025-01-15T14:30:22",
  "project_path": "/home/user/myproject",
  "os": {
    "type": "wsl",
    "version": "Ubuntu 22.04.1 LTS"
  },
  "python": {
    "version": "3.10.6",
    "executable": "/home/user/myproject/venv/bin/python",
    "required": "3.10.x",
    "version_match": true
  },
  "virtual_environment": {
    "type": "virtualenv",
    "active": true,
    "path": "/home/user/myproject/venv"
  },
  "dependencies": {
    "requirements_file": "requirements.txt",
    "total_packages": 15,
    "missing_packages": ["requests", "pytest"]
  },
  "config_files": {
    "found": [".env", ".gitignore", "pyproject.toml"],
    "missing": [".editorconfig"]
  },
  "issues": [
    {
      "severity": "error",
      "category": "dependency",
      "message": "2 required packages are not installed",
      "fixable": true,
      "fix_command": "pip install -r requirements.txt"
    },
    {
      "severity": "warning",
      "category": "os",
      "message": "Project path contains Windows-style path separators",
      "fixable": false,
      "recommendation": "Use Unix-style paths in WSL"
    },
    {
      "severity": "info",
      "category": "config",
      "message": "No .editorconfig found",
      "fixable": false
    }
  ],
  "summary": {
    "total_issues": 3,
    "errors": 1,
    "warnings": 1,
    "info": 1
  }
}
```

---

## Testing Strategy

### Unit Tests

**Test Coverage Areas**:
1. OS detection across platforms
2. Python version parsing and comparison
3. Virtual environment type detection
4. Dependency scanning logic
5. Configuration file detection
6. Issue classification and severity
7. Report generation (text and JSON)
8. Fix application logic

**Example Test Structure**:

```python
# tests/test_detectors/test_os_detector.py
import unittest
from unittest.mock import patch, mock_open
from harmonizer.detectors.os_detector import detect_os_type, OSType

class TestOSDetector(unittest.TestCase):

    @patch('platform.system')
    def test_detect_windows_native(self, mock_system):
        """Test Windows native detection"""
        mock_system.return_value = "Windows"
        result = detect_os_type()
        self.assertEqual(result, OSType.WINDOWS_NATIVE)

    @patch('platform.system')
    @patch('os.environ', {"WSLENV": "some_value"})
    def test_detect_wsl_via_env_var(self, mock_system):
        """Test WSL detection via WSLENV environment variable"""
        mock_system.return_value = "Linux"
        result = detect_os_type()
        self.assertEqual(result, OSType.WSL)

    @patch('platform.system')
    @patch('builtins.open', mock_open(read_data="linux version microsoft"))
    def test_detect_wsl_via_proc_version(self, mock_system):
        """Test WSL detection via /proc/version"""
        mock_system.return_value = "Linux"
        result = detect_os_type()
        self.assertEqual(result, OSType.WSL)
```

### Integration Tests

**Test Scenarios**:
1. Full scan on clean project
2. Full scan on project with missing dependencies
3. Full scan on project with version mismatch
4. Fix application with dry-run
5. Fix application with actual changes
6. JSON output validation
7. CLI argument parsing

**Example Integration Test**:

```python
# tests/test_integration.py
import unittest
import subprocess
import json
from pathlib import Path

class TestFullScan(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.test_project = Path(__file__).parent / "fixtures" / "sample_project_1"

    def test_full_scan_json_output(self):
        """Test complete scan with JSON output"""
        result = subprocess.run(
            ["python", "-m", "harmonizer", str(self.test_project), "--json"],
            capture_output=True,
            text=True
        )

        self.assertEqual(result.returncode, 0)

        # Validate JSON output
        report = json.loads(result.stdout)
        self.assertIn("project_path", report)
        self.assertIn("os", report)
        self.assertIn("python", report)
        self.assertIn("issues", report)
```

### Test Fixtures

Create sample projects for testing:

```
tests/fixtures/
├── sample_project_1/       # Clean environment
│   ├── requirements.txt
│   ├── .python-version
│   └── venv/
├── sample_project_2/       # Missing dependencies
│   ├── requirements.txt    # Lists packages not installed
│   └── setup.py
└── sample_project_3/       # Version mismatch
    ├── .python-version     # Specifies different Python version
    └── requirements.txt
```

---

## Coding Standards

### Style Guide
- Follow PEP 8 Python style guide
- Use type hints for all function signatures
- Maximum line length: 100 characters
- Use docstrings for all modules, classes, and functions (Google style)

### Naming Conventions
- Modules: lowercase_with_underscores
- Classes: PascalCase
- Functions/Methods: lowercase_with_underscores
- Constants: UPPERCASE_WITH_UNDERSCORES
- Private members: _leading_underscore

### Documentation Standards

```python
def detect_virtual_environment(project_path: str) -> Dict[str, Any]:
    """
    Detect virtual environment type and status in a project.

    This function examines the project directory and environment variables
    to determine if a virtual environment is present and active. It supports
    detection of virtualenv, conda, pipenv, and poetry environments.

    Args:
        project_path: Absolute path to the project directory to scan

    Returns:
        Dictionary containing:
            - venv_type: Type of virtual environment (VenvType enum)
            - active: Boolean indicating if environment is currently active
            - path: Absolute path to virtual environment directory (if found)

    Raises:
        ValueError: If project_path does not exist or is not a directory

    Example:
        >>> result = detect_virtual_environment("/home/user/myproject")
        >>> print(result["venv_type"])
        VenvType.VIRTUALENV
        >>> print(result["active"])
        True

    Note:
        This function does not activate virtual environments, only detects them.
        For activation, see the venv_fixer module.
    """
    pass
```

### Error Handling

```python
# Always provide context in exceptions
raise ValueError(f"Project path does not exist: {project_path}")

# Catch specific exceptions
try:
    result = subprocess.run(cmd, capture_output=True, timeout=5)
except subprocess.TimeoutExpired:
    logger.warning(f"Command timed out: {cmd}")
except subprocess.SubprocessError as e:
    logger.error(f"Subprocess failed: {e}")

# Use logging for non-critical errors
logger.warning("Could not detect conda environment, skipping")

# Provide helpful error messages
if not requirements_file.exists():
    print(f"❌ Requirements file not found: {requirements_file}")
    print("💡 Tip: Create requirements.txt with: pip freeze > requirements.txt")
```

---

## Common Development Tasks

### Running the Tool

```bash
# From source (development)
python -m harmonizer

# After installation
harmonizer

# With specific options
python -m harmonizer /path/to/project --verbose --json
```

### Running Tests

```bash
# All tests
python -m pytest tests/

# Specific test file
python -m pytest tests/test_detectors/test_os_detector.py

# With coverage
python -m pytest --cov=harmonizer --cov-report=html tests/

# Verbose output
python -m pytest -v tests/
```

### Code Formatting

```bash
# Format with black
black harmonizer/ tests/

# Check with flake8
flake8 harmonizer/ tests/

# Type checking with mypy
mypy harmonizer/
```

### Building Distribution

```bash
# Build source distribution
python setup.py sdist

# Build wheel
python setup.py bdist_wheel

# Install locally in development mode
pip install -e .
```

---

## Debugging Tips

### Enable Verbose Logging

```python
# harmonizer/utils/logger.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(verbose=False):
    """Configure logging with optional verbose mode."""

    level = logging.DEBUG if verbose else logging.INFO

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        "logs/harmonizer.log",
        maxBytes=10_000_000,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)

    # Formatting
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Root logger configuration
    logger = logging.getLogger("harmonizer")
    logger.setLevel(level)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
```

### Common Issues & Solutions

**Issue**: Virtual environment not detected
- Check VIRTUAL_ENV environment variable
- Verify venv directory has pyvenv.cfg file
- Ensure sys.prefix != sys.base_prefix

**Issue**: Subprocess commands failing
- Check command availability with `which` or `where`
- Verify PATH environment variable
- Use absolute paths for executables

**Issue**: WSL detection not working
- Check /proc/version file exists and is readable
- Verify WSLENV environment variable
- Test with known WSL environment

**Issue**: Permission errors on Windows
- Run with appropriate permissions
- Check file/directory ownership
- Verify antivirus isn't blocking

---

## Educational Features

### Inline Comments Strategy

Every detection function should include:
1. **What**: Brief description of what the code does
2. **Why**: Explanation of why this approach is used
3. **How**: Step-by-step breakdown of the logic
4. **Gotchas**: Common pitfalls or edge cases

Example:
```python
def detect_os_type():
    """
    Detect the operating system type with WSL support.

    WHAT: Identifies whether code is running on Windows native, WSL, Linux, or macOS

    WHY: Different OS environments have different behaviors, especially WSL which
         reports as Linux but has Windows interop features. We need to distinguish
         these to provide accurate diagnostics.

    HOW:
    1. Use platform.system() for basic OS detection
    2. If Linux, check for WSL-specific markers:
       - /proc/version containing "microsoft" (WSL kernel signature)
       - WSLENV environment variable (set by WSL runtime)
    3. Return appropriate OSType enum value

    GOTCHAS:
    - WSL 1 and WSL 2 have slightly different signatures
    - /proc/version might not exist on all Linux systems
    - WSLENV can be unset even in WSL if user modified environment
    """
    pass
```

### CLI Tooltips and Help

Include educational content in help messages:

```python
parser.add_argument(
    "--fix",
    action="store_true",
    help="""
    Automatically apply fixes to detected issues.

    This flag enables the automated fix mode, which will attempt to resolve
    environment inconsistencies such as:
    - Installing missing dependencies from requirements.txt
    - Activating virtual environments
    - Updating outdated configuration files

    SAFETY: Always use --dry-run first to preview changes before applying.

    EXAMPLE:
      harmonizer --fix --dry-run    # Preview fixes
      harmonizer --fix              # Apply fixes

    TIP: Some fixes require confirmation and cannot be fully automated.
    """
)
```

### Progressive Disclosure

Provide different levels of information based on verbosity:

```python
# Normal mode
print("✓ Virtual environment detected")

# Verbose mode
if verbose:
    print("✓ Virtual environment detected")
    print(f"  Type: {venv_type.value}")
    print(f"  Path: {venv_path}")
    print(f"  Active: {venv_active}")
    print(f"  Detection method: VIRTUAL_ENV environment variable")
```

---

## Security Considerations

### Safe Subprocess Execution

```python
# GOOD: Use list form, avoid shell=True
subprocess.run(["pip", "install", package_name], shell=False)

# BAD: String form with shell=True (command injection risk)
subprocess.run(f"pip install {package_name}", shell=True)

# GOOD: Validate input before using in commands
def install_package(package_name):
    if not is_valid_package_name(package_name):
        raise ValueError(f"Invalid package name: {package_name}")

    subprocess.run(["pip", "install", package_name])

def is_valid_package_name(name):
    """Validate package name to prevent injection."""
    import re
    # Allow alphanumeric, dash, underscore, dot
    return bool(re.match(r'^[a-zA-Z0-9._-]+$', name))
```

### Path Traversal Prevention

```python
from pathlib import Path

def safe_project_path(user_path):
    """Resolve and validate project path to prevent traversal attacks."""

    # Resolve to absolute path
    path = Path(user_path).resolve()

    # Validate it's a directory
    if not path.is_dir():
        raise ValueError(f"Not a directory: {path}")

    # Optional: Ensure it's within allowed directories
    # allowed_base = Path.home()
    # if not path.is_relative_to(allowed_base):
    #     raise ValueError(f"Path outside allowed directory: {path}")

    return path
```

### File Operations Safety

```python
# Always use context managers for file operations
with open(config_file, "r") as f:
    data = json.load(f)

# Check file permissions before reading sensitive files
import stat

def safe_read_config(config_path):
    """Read configuration file with permission checks."""

    path = Path(config_path)

    # Check file permissions (warn if world-readable)
    mode = path.stat().st_mode
    if mode & stat.S_IROTH:
        logger.warning(f"Config file is world-readable: {config_path}")

    with open(path, "r") as f:
        return json.load(f)
```

---

## Performance Optimization

### Subprocess Timeouts

```python
# Always use timeouts to prevent hanging
try:
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=5  # 5 second timeout
    )
except subprocess.TimeoutExpired:
    logger.warning(f"Command timed out: {cmd}")
    return None
```

### Caching Results

```python
from functools import lru_cache

@lru_cache(maxsize=1)
def detect_os_type():
    """Cache OS detection result (doesn't change during execution)."""
    # ... detection logic ...
    pass

# Clear cache if needed
detect_os_type.cache_clear()
```

### Lazy Loading

```python
class EnvironmentScanner:
    def __init__(self, project_path):
        self.project_path = project_path
        self._python_info = None
        self._venv_info = None

    @property
    def python_info(self):
        """Lazy load Python information only when accessed."""
        if self._python_info is None:
            self._python_info = detect_python_version()
        return self._python_info
```

---

## Troubleshooting

### Common Development Issues

**Import Errors**
```bash
# Ensure package is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/environment-harmonizer"

# Or install in development mode
pip install -e .
```

**Tests Not Discovering**
```bash
# Ensure __init__.py files exist in test directories
touch tests/__init__.py
touch tests/test_detectors/__init__.py

# Run pytest with explicit path
pytest tests/
```

**Virtual Environment Issues**
```bash
# Recreate virtual environment
rm -rf venv/
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements-dev.txt
```

**Permission Errors**
```bash
# On Linux/WSL, ensure log directory is writable
mkdir -p logs/
chmod 755 logs/

# On Windows, run as administrator if needed
```

### Debugging Checklist

1. **Environment Setup**
   - [ ] Python version is 3.7+
   - [ ] Virtual environment is activated
   - [ ] All dependencies are installed
   - [ ] PYTHONPATH includes project root

2. **Code Issues**
   - [ ] All imports are correct
   - [ ] Type hints are valid
   - [ ] Docstrings are present
   - [ ] Error handling is in place

3. **Testing Issues**
   - [ ] Test fixtures are available
   - [ ] Mock objects are configured correctly
   - [ ] Test isolation is maintained
   - [ ] Cleanup is performed after tests

4. **Runtime Issues**
   - [ ] Logging is enabled and working
   - [ ] File permissions are correct
   - [ ] Subprocess commands are available
   - [ ] Timeouts are reasonable

---

## API Usage Examples

### Programmatic Usage

```python
# example_usage.py
from harmonizer.scanners.project_scanner import ProjectScanner
from harmonizer.reporters.text_reporter import TextReporter
from harmonizer.reporters.json_reporter import JSONReporter
from pathlib import Path

def scan_project(project_path):
    """Example: Scan a project programmatically."""

    # Create scanner
    scanner = ProjectScanner(project_path)

    # Run scan
    env_status = scanner.scan()

    # Generate text report
    text_reporter = TextReporter(env_status)
    print(text_reporter.generate())

    # Or JSON report
    json_reporter = JSONReporter(env_status)
    report_data = json_reporter.generate()

    # Save to file
    output_file = Path("environment_report.json")
    output_file.write_text(json.dumps(report_data, indent=2))

    return env_status

def apply_fixes(env_status):
    """Example: Apply automated fixes."""
    from harmonizer.fixers.venv_fixer import VenvFixer
    from harmonizer.fixers.dependency_fixer import DependencyFixer

    # Apply virtual environment fixes
    venv_fixer = VenvFixer(env_status)
    venv_fixer.apply_fixes(dry_run=True)  # Preview first
    venv_fixer.apply_fixes(dry_run=False)  # Apply

    # Apply dependency fixes
    dep_fixer = DependencyFixer(env_status)
    dep_fixer.apply_fixes(dry_run=False)

# Usage
if __name__ == "__main__":
    project = Path("/path/to/project")
    env_status = scan_project(project)

    if env_status.issues:
        print(f"\nFound {len(env_status.issues)} issues")
        apply_fixes(env_status)
```

---

## Git Workflow

### Branch Strategy
- `main`: Stable releases only
- `develop`: Integration branch for features
- `feature/*`: Individual feature branches
- `bugfix/*`: Bug fix branches

### Commit Message Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: feat, fix, docs, style, refactor, test, chore

Example:
```
feat(detectors): Add pipx virtual environment detection

Implement detection for pipx-installed packages and environments.
This includes checking for PIPX_HOME environment variable and
scanning the pipx venvs directory.

Closes #123
```

### Development Branch
Currently working on: `claude/init-project-setup-01Ga3BCL8LG5YKnMhmzT4AS3`

---

## Current Status

**Project Stage**: Phase 1 - Initial Setup
**Current Step**: Creating project structure and documentation

**Next Steps**:
1. Create initial project structure (harmonizer/ directory)
2. Set up .gitignore for Python project
3. Create requirements.txt and requirements-dev.txt
4. Implement EnvironmentStatus dataclass
5. Begin OS detection module

---

## Quick Reference

### Key Files
- `harmonizer/__main__.py` - CLI entry point
- `harmonizer/models.py` - Data models
- `harmonizer/cli.py` - Argument parsing
- `detectors/os_detector.py` - OS detection
- `detectors/python_detector.py` - Python version detection
- `detectors/venv_detector.py` - Virtual environment detection

### Key Commands
```bash
# Run tool
python -m harmonizer

# Run tests
pytest tests/

# Format code
black harmonizer/ tests/

# Type check
mypy harmonizer/

# Install dev mode
pip install -e .
```

### Key Concepts
- **EnvironmentStatus**: Central data structure holding scan results
- **Detectors**: Modules that detect specific environment aspects
- **Scanners**: Orchestrate detectors and aggregate results
- **Reporters**: Generate output in different formats
- **Fixers**: Apply automated corrections to issues

---

## Additional Resources

### Python Documentation
- [argparse](https://docs.python.org/3/library/argparse.html)
- [pathlib](https://docs.python.org/3/library/pathlib.html)
- [subprocess](https://docs.python.org/3/library/subprocess.html)
- [dataclasses](https://docs.python.org/3/library/dataclasses.html)

### Testing Resources
- [pytest documentation](https://docs.pytest.org/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

### Style Guides
- [PEP 8](https://pep8.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)

---

## Notes for AI Assistant

When implementing features:
1. **Always** refer to the phase and step number from README.md
2. **Follow** the educational focus - include teaching comments
3. **Implement** both CLI and programmatic interfaces
4. **Add** comprehensive error handling
5. **Write** tests alongside implementation
6. **Update** this document as architecture evolves
7. **Maintain** type hints and docstrings
8. **Consider** cross-platform compatibility (Windows, WSL, Linux, macOS)

Remember: This project is designed to teach beginners about environment management. Every piece of code should be clear, well-documented, and educational.

---

**Last Updated**: 2025-01-15
**Document Version**: 1.0.0
**Project Phase**: Phase 1 - Foundations & Setup
