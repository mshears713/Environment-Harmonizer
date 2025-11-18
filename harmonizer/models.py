"""
Data models for Environment Harmonizer.

This module defines the core data structures used throughout the application,
including enumerations for OS types, virtual environment types, and issue severity,
as well as the main EnvironmentStatus dataclass that holds all scan results.

EDUCATIONAL NOTE - Why Dataclasses?
Dataclasses (introduced in Python 3.7) provide a clean, concise way to create
classes that are primarily used to store data. Compared to traditional classes:
- Automatic __init__, __repr__, __eq__ methods
- Type hints for better IDE support and type checking
- Less boilerplate code
- Immutable option with frozen=True
- Default values and field factories

Example:
    Traditional class:
        class Person:
            def __init__(self, name, age):
                self.name = name
                self.age = age

    Dataclass equivalent:
        @dataclass
        class Person:
            name: str
            age: int
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class OSType(Enum):
    """
    Operating system types supported by Environment Harmonizer.

    EDUCATIONAL NOTE - Why Enums?
    Enums provide type-safe constants that are more maintainable than string
    literals. They prevent typos, enable autocomplete, and make code self-documenting.

    WSL (Windows Subsystem for Linux) is detected separately from native Linux
    because it has unique characteristics that affect environment behavior:
    - Interoperability with Windows filesystem
    - Different PATH handling
    - Mixed line endings (CRLF vs LF)
    """

    WINDOWS_NATIVE = "windows_native"
    WSL = "wsl"
    LINUX = "linux"
    MACOS = "macos"
    UNKNOWN = "unknown"


class VenvType(Enum):
    """
    Virtual environment types that can be detected.

    EDUCATIONAL NOTE - Virtual Environment Types:
    - virtualenv/venv: Standard Python virtual environments (lightweight)
    - conda: Anaconda/Miniconda environments (includes non-Python packages)
    - pipenv: Combines pip and virtualenv with Pipfile for dependency management
    - poetry: Modern dependency management with pyproject.toml
    - pipx: Installs Python CLI tools in isolated environments (one tool per venv)
    - none: No virtual environment detected
    """

    VIRTUALENV = "virtualenv"
    CONDA = "conda"
    PIPENV = "pipenv"
    POETRY = "poetry"
    PIPX = "pipx"
    NONE = "none"


class IssueSeverity(Enum):
    """
    Severity levels for detected environment issues.

    EDUCATIONAL NOTE - Issue Classification:
    - INFO: Informational messages, best practices, recommendations
    - WARNING: Issues that might cause problems but aren't critical
    - ERROR: Critical issues that will likely prevent proper operation
    """

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class Issue:
    """
    Represents a single detected environment issue.

    This class encapsulates all information about a detected problem,
    including its severity, category, description, and potential fixes.

    Attributes:
        severity: How critical the issue is (INFO, WARNING, ERROR)
        category: Issue category (e.g., "python_version", "dependency", "config")
        message: Human-readable description of the issue
        fixable: Whether this issue can be automatically fixed
        fix_command: Optional command to fix the issue (if fixable)

    EDUCATIONAL NOTE - Optional Types:
    Optional[str] means the value can be either a string or None.
    This is equivalent to Union[str, None] and helps with type checking.

    Example:
        issue = Issue(
            severity=IssueSeverity.ERROR,
            category="dependency",
            message="Missing package: requests",
            fixable=True,
            fix_command="pip install requests"
        )
    """

    severity: IssueSeverity
    category: str
    message: str
    fixable: bool = False
    fix_command: Optional[str] = None


@dataclass
class EnvironmentStatus:
    """
    Main data structure holding all environment scan results.

    This dataclass serves as the central repository for all detected environment
    information. It's populated by various detector modules and consumed by
    reporters and fixers.

    EDUCATIONAL NOTE - Field Factories:
    The field(default_factory=list) pattern is used instead of mutable defaults
    like [] to avoid sharing the same list instance across different objects.
    This is a Python best practice to prevent subtle bugs.

    CORRECT:   items: List[str] = field(default_factory=list)
    INCORRECT: items: List[str] = []  # All instances would share same list!

    Attributes:
        OS Information:
            os_type: Detected operating system type
            os_version: OS version string

        Python Information:
            python_version: Python interpreter version (e.g., "3.10.6")
            python_executable: Full path to Python executable

        Virtual Environment:
            venv_type: Type of virtual environment detected
            venv_active: Whether a virtual environment is currently active
            venv_path: Path to virtual environment directory (if found)

        Project Information:
            project_path: Path to scanned project directory
            config_files: List of detected configuration files

        Dependencies:
            requirements_file: Path to requirements file (if found)
            installed_packages: List of installed package names
            missing_packages: List of required but missing packages

        Issues:
            issues: List of detected environment issues

        System Information:
            path_variables: Relevant PATH components
            environment_variables: Relevant environment variables

    Example:
        status = EnvironmentStatus(
            os_type=OSType.WSL,
            os_version="Ubuntu 22.04",
            python_version="3.10.6",
            python_executable="/usr/bin/python3",
            venv_type=VenvType.VIRTUALENV,
            venv_active=True,
            project_path="/home/user/myproject"
        )
    """

    # OS Information (required fields)
    os_type: OSType
    os_version: str

    # Python Information (required fields)
    python_version: str
    python_executable: str

    # Virtual Environment (required fields)
    venv_type: VenvType
    venv_active: bool
    venv_path: Optional[str] = None

    # Project Information (required field)
    project_path: str = "."

    # Configuration Files (optional, defaults to empty list)
    config_files: List[str] = field(default_factory=list)

    # Dependencies (optional fields)
    requirements_file: Optional[str] = None
    installed_packages: List[str] = field(default_factory=list)
    missing_packages: List[str] = field(default_factory=list)

    # Issues (defaults to empty list)
    issues: List[Issue] = field(default_factory=list)

    # System Information (optional, defaults to empty dicts)
    path_variables: Dict[str, str] = field(default_factory=dict)
    environment_variables: Dict[str, str] = field(default_factory=dict)

    def add_issue(
        self,
        severity: IssueSeverity,
        category: str,
        message: str,
        fixable: bool = False,
        fix_command: Optional[str] = None,
    ) -> None:
        """
        Add a new issue to the environment status.

        This is a convenience method to add issues without directly
        manipulating the issues list.

        Args:
            severity: Issue severity level
            category: Issue category
            message: Human-readable description
            fixable: Whether the issue can be automatically fixed
            fix_command: Optional command to fix the issue

        Example:
            status.add_issue(
                IssueSeverity.WARNING,
                "python_version",
                "Python 3.9 detected, but project requires 3.10+",
                fixable=False
            )
        """
        issue = Issue(
            severity=severity,
            category=category,
            message=message,
            fixable=fixable,
            fix_command=fix_command,
        )
        self.issues.append(issue)

    def has_errors(self) -> bool:
        """
        Check if any ERROR-level issues are present.

        Returns:
            True if at least one ERROR issue exists, False otherwise
        """
        return any(issue.severity == IssueSeverity.ERROR for issue in self.issues)

    def has_warnings(self) -> bool:
        """
        Check if any WARNING-level issues are present.

        Returns:
            True if at least one WARNING issue exists, False otherwise
        """
        return any(issue.severity == IssueSeverity.WARNING for issue in self.issues)

    def get_fixable_issues(self) -> List[Issue]:
        """
        Get all issues that can be automatically fixed.

        Returns:
            List of fixable issues

        EDUCATIONAL NOTE - List Comprehensions:
        List comprehensions provide a concise way to filter and transform lists.
        This is more Pythonic than using traditional for loops with append().

        Traditional approach:
            fixable = []
            for issue in self.issues:
                if issue.fixable:
                    fixable.append(issue)

        Pythonic approach (used here):
            fixable = [issue for issue in self.issues if issue.fixable]
        """
        return [issue for issue in self.issues if issue.fixable]

    def issue_summary(self) -> Dict[str, int]:
        """
        Get a summary count of issues by severity.

        Returns:
            Dictionary with counts: {"errors": 2, "warnings": 3, "info": 1}
        """
        summary = {"errors": 0, "warnings": 0, "info": 0}

        for issue in self.issues:
            if issue.severity == IssueSeverity.ERROR:
                summary["errors"] += 1
            elif issue.severity == IssueSeverity.WARNING:
                summary["warnings"] += 1
            elif issue.severity == IssueSeverity.INFO:
                summary["info"] += 1

        return summary
