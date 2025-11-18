"""
Project Scanner Module.

This module orchestrates all detection modules to perform a complete
environment scan of a project directory.

EDUCATIONAL NOTE - Orchestration Pattern:
This module acts as a "controller" or "orchestrator" that:
1. Coordinates multiple detector modules
2. Aggregates their results into EnvironmentStatus
3. Provides a single entry point for scanning
4. Handles errors and edge cases

This is a common design pattern in software architecture,
separating concerns and making the system more maintainable.
"""

import sys
from pathlib import Path
from typing import Optional

from harmonizer.models import EnvironmentStatus, OSType, VenvType, IssueSeverity
from harmonizer.detectors.os_detector import detect_os_type, get_os_version
from harmonizer.detectors.python_detector import (
    detect_python_version,
    get_project_python_requirement,
    check_version_compatibility,
)
from harmonizer.detectors.venv_detector import detect_venv_type
from harmonizer.detectors.dependency_detector import scan_dependencies
from harmonizer.detectors.config_detector import (
    detect_config_files,
    detect_config_issues,
)
from harmonizer.detectors.quirks_detector import detect_platform_quirks
from harmonizer.utils.progress import ProgressReporter
from harmonizer.utils.logging_config import HarmonizerLogger
from harmonizer.utils.performance import get_global_monitor


class ProjectScanner:
    """
    Main project scanner that orchestrates all detection modules.

    This class provides a high-level interface for scanning a project
    directory and generating a complete EnvironmentStatus report.

    EDUCATIONAL NOTE - Class vs Functions:
    We use a class here instead of plain functions because:
    1. State management: Store project_path and scan results
    2. Flexibility: Easy to add configuration options
    3. Extensibility: Subclasses can customize behavior
    4. Testing: Easy to mock and test

    Example:
        >>> scanner = ProjectScanner("/path/to/project")
        >>> status = scanner.scan()
        >>> print(f"Found {len(status.issues)} issues")

    Attributes:
        project_path: Path to the project being scanned
        verbose: Whether to print verbose output during scanning
    """

    def __init__(self, project_path: str = ".", verbose: bool = False, use_color: bool = True):
        """
        Initialize the project scanner.

        Args:
            project_path: Path to project directory (default: current directory)
            verbose: Enable verbose output during scanning
            use_color: Enable colored output (default: True)

        Raises:
            ValueError: If project_path doesn't exist or isn't a directory
        """

        self.project_path = Path(project_path).resolve()
        self.verbose = verbose
        self.progress = ProgressReporter(use_color=use_color, verbose=verbose)
        self.logger = HarmonizerLogger.get_logger(__name__)
        self.perf_monitor = get_global_monitor()

        # Validate project path
        if not self.project_path.exists():
            self.logger.error(f"Project path does not exist: {project_path}")
            raise ValueError(f"Project path does not exist: {project_path}")

        if not self.project_path.is_dir():
            self.logger.error(f"Project path is not a directory: {project_path}")
            raise ValueError(f"Project path is not a directory: {project_path}")

        self.logger.info(f"ProjectScanner initialized for: {self.project_path}")

    def scan(self, checks: Optional[list] = None) -> EnvironmentStatus:
        """
        Perform a complete environment scan.

        Args:
            checks: Optional list of specific checks to run
                   Options: ['os', 'python', 'venv', 'dependencies', 'config', 'quirks']
                   If None, runs all checks

        Returns:
            EnvironmentStatus object with complete scan results

        EDUCATIONAL NOTE - Modular Scanning:
        Each detection module is independent and can be run separately.
        This allows for:
        - Selective scanning (only run what you need)
        - Easier testing (test each module independently)
        - Better performance (skip expensive checks if not needed)
        - Clear separation of concerns
        """

        if checks is None:
            checks = ['os', 'python', 'venv', 'dependencies', 'config', 'quirks']

        # Initialize environment status with default values
        env_status = self._initialize_environment_status()

        # Run detection modules in logical order
        if 'os' in checks:
            self._scan_os(env_status)

        if 'python' in checks:
            self._scan_python(env_status)

        if 'venv' in checks:
            self._scan_venv(env_status)

        if 'dependencies' in checks:
            self._scan_dependencies(env_status)

        if 'config' in checks:
            self._scan_config(env_status)

        if 'quirks' in checks:
            self._scan_quirks(env_status)

        return env_status

    def _initialize_environment_status(self) -> EnvironmentStatus:
        """
        Initialize EnvironmentStatus with required fields.

        Returns:
            EnvironmentStatus object with default values
        """

        return EnvironmentStatus(
            os_type=OSType.UNKNOWN,
            os_version="Unknown",
            python_version="Unknown",
            python_executable=sys.executable,
            venv_type=VenvType.NONE,
            venv_active=False,
            project_path=str(self.project_path),
        )

    def _scan_os(self, env_status: EnvironmentStatus) -> None:
        """
        Scan operating system information.

        Updates env_status with:
        - os_type
        - os_version
        """

        self.progress.start_step("Detecting operating system")
        self.perf_monitor.start_timer("scan_os")
        self.logger.debug("Starting OS detection")

        try:
            env_status.os_type = detect_os_type()
            env_status.os_version = get_os_version()

            self.logger.info(f"Detected OS: {env_status.os_type.value} - {env_status.os_version}")
            self.progress.complete_step(f"OS: {env_status.os_type.value} ({env_status.os_version})")
            self.progress.verbose(f"OS Type: {env_status.os_type.value}")
            self.progress.verbose(f"OS Version: {env_status.os_version}")

        except Exception as e:
            self.logger.error(f"Error during OS detection: {e}", exc_info=True)
            raise
        finally:
            duration = self.perf_monitor.stop_timer("scan_os")
            self.logger.debug(f"OS detection completed in {duration:.3f}s" if duration else "OS detection timer not found")

    def _scan_python(self, env_status: EnvironmentStatus) -> None:
        """
        Scan Python environment information.

        Updates env_status with:
        - python_version
        - python_executable
        - Issues related to Python version mismatches
        """

        self.progress.start_step("Detecting Python version")

        py_info = detect_python_version()
        env_status.python_version = py_info["version"]
        env_status.python_executable = py_info["executable"]

        self.progress.complete_step(f"Python {env_status.python_version} detected")
        self.progress.verbose(f"Python Version: {env_status.python_version}")
        self.progress.verbose(f"Python Executable: {env_status.python_executable}")

        # Check for Python version compatibility
        required_version = get_project_python_requirement(str(self.project_path))
        if required_version:
            self.progress.verbose(f"Project requires Python {required_version}")

            compatible, issue = check_version_compatibility(
                env_status.python_version, required_version
            )

            if issue:
                env_status.issues.append(issue)
                self.progress.warning(f"Python version mismatch: current {env_status.python_version}, required {required_version}")

    def _scan_venv(self, env_status: EnvironmentStatus) -> None:
        """
        Scan virtual environment information.

        Updates env_status with:
        - venv_type
        - venv_active
        - venv_path
        - Issues related to inactive virtual environments
        """

        self.progress.start_step("Detecting virtual environment")

        venv_info = detect_venv_type()
        env_status.venv_type = venv_info["type"]
        env_status.venv_active = venv_info["active"]

        if venv_info.get("path"):
            env_status.venv_path = venv_info["path"]

        status_str = "active" if env_status.venv_active else "not active"
        self.progress.complete_step(f"Virtual Env: {env_status.venv_type.value} ({status_str})")
        self.progress.verbose(f"Venv Type: {env_status.venv_type.value}")
        self.progress.verbose(f"Venv Active: {env_status.venv_active}")
        if env_status.venv_path:
            self.progress.verbose(f"Venv Path: {env_status.venv_path}")

        # Check if virtual environment should be active but isn't
        if env_status.venv_type != VenvType.NONE and not env_status.venv_active:
            env_status.add_issue(
                IssueSeverity.WARNING,
                "venv",
                f"Virtual environment detected ({env_status.venv_type.value}) but not active",
                fixable=True,
                fix_command=f"Activate virtual environment at {venv_info.get('path', 'unknown')}",
            )
            self.progress.warning(f"Virtual environment is not active")

    def _scan_dependencies(self, env_status: EnvironmentStatus) -> None:
        """
        Scan project dependencies.

        Updates env_status with:
        - requirements_file
        - installed_packages
        - missing_packages
        - Issues related to missing dependencies
        """

        if self.verbose:
            print("Scanning dependencies...")

        dep_results = scan_dependencies(str(self.project_path))

        env_status.requirements_file = dep_results["requirements_file"]
        env_status.installed_packages = dep_results["installed_packages"]
        env_status.missing_packages = dep_results["missing_packages"]

        if self.verbose:
            if env_status.requirements_file:
                print(f"  Requirements file: {env_status.requirements_file}")
                print(f"  Required packages: {len(dep_results['required_packages'])}")
                print(f"  Installed packages: {len(env_status.installed_packages)}")
                print(f"  Missing packages: {len(env_status.missing_packages)}")
            else:
                print(f"  No requirements file found")

        # Add issues for missing packages
        if env_status.missing_packages:
            env_status.add_issue(
                IssueSeverity.ERROR,
                "dependency",
                f"{len(env_status.missing_packages)} required package(s) not installed: "
                f"{', '.join(env_status.missing_packages[:5])}",
                fixable=True,
                fix_command=f"pip install -r {env_status.requirements_file}"
                if env_status.requirements_file
                else None,
            )

            if self.verbose:
                print(f"  ✗ Missing packages: {', '.join(env_status.missing_packages[:5])}")

        elif not env_status.requirements_file:
            # No requirements file found - might be intentional or might be an issue
            env_status.add_issue(
                IssueSeverity.INFO,
                "dependency",
                "No dependency file found (requirements.txt, pyproject.toml, etc.)",
                fixable=False,
            )

    def _scan_config(self, env_status: EnvironmentStatus) -> None:
        """
        Scan configuration files.

        Updates env_status with:
        - config_files
        - Issues related to missing or problematic config files
        """

        if self.verbose:
            print("Scanning configuration files...")

        config_results = detect_config_files(str(self.project_path))
        env_status.config_files = config_results["found"]

        if self.verbose:
            print(f"  Found {len(env_status.config_files)} config files")

        # Add issues from config detection
        config_issues = detect_config_issues(str(self.project_path))

        for issue_dict in config_issues:
            severity_map = {
                "error": IssueSeverity.ERROR,
                "warning": IssueSeverity.WARNING,
                "info": IssueSeverity.INFO,
            }

            env_status.add_issue(
                severity_map[issue_dict["severity"]],
                issue_dict["category"],
                issue_dict["message"],
                fixable=False,
            )

            if self.verbose:
                print(f"  [{issue_dict['severity'].upper()}] {issue_dict['message']}")

        # Warn about missing required files
        if config_results["missing_required"]:
            env_status.add_issue(
                IssueSeverity.WARNING,
                "config",
                f"Missing required config files: {', '.join(config_results['missing_required'])}",
                fixable=False,
            )

    def _scan_quirks(self, env_status: EnvironmentStatus) -> None:
        """
        Scan for platform-specific quirks and issues.

        Updates env_status with:
        - Issues related to platform-specific quirks (WSL, Windows, etc.)
        """

        if self.verbose:
            print("Detecting platform-specific quirks...")

        quirk_issues = detect_platform_quirks(
            str(self.project_path), env_status.os_type
        )

        # Add quirk issues to environment status
        env_status.issues.extend(quirk_issues)

        if self.verbose and quirk_issues:
            print(f"  Found {len(quirk_issues)} platform-specific issues")


# Convenience function for quick scanning
def scan_project(
    project_path: str = ".", verbose: bool = False, checks: Optional[list] = None
) -> EnvironmentStatus:
    """
    Convenience function to scan a project directory.

    This is a simpler interface for one-off scans without creating
    a ProjectScanner instance.

    Args:
        project_path: Path to project directory (default: current directory)
        verbose: Enable verbose output
        checks: Optional list of specific checks to run

    Returns:
        EnvironmentStatus object with scan results

    EDUCATIONAL NOTE - Convenience Functions:
    We provide both a class-based interface (ProjectScanner) and
    a function-based interface (scan_project) to accommodate different
    use cases:
    - Class: Better for repeated scans, configuration, testing
    - Function: Simpler for one-off scans, scripting

    This is a common pattern in API design: provide both low-level
    and high-level interfaces.

    Example:
        >>> # Simple function-based usage
        >>> status = scan_project()
        >>>
        >>> # Class-based usage with more control
        >>> scanner = ProjectScanner(verbose=True)
        >>> status = scanner.scan(checks=['python', 'venv'])
    """

    scanner = ProjectScanner(project_path, verbose=verbose)
    return scanner.scan(checks=checks)


# Example usage and testing
if __name__ == "__main__":
    """
    Test the project scanner module.
    """

    print("=" * 80)
    print("Project Scanner Module - Test Run")
    print("=" * 80)
    print()

    # Scan current directory with verbose output
    try:
        status = scan_project(".", verbose=True)

        print()
        print("=" * 80)
        print("SCAN COMPLETE")
        print("=" * 80)
        print()

        # Print summary
        print(f"Project: {status.project_path}")
        print(f"OS: {status.os_type.value} ({status.os_version})")
        print(f"Python: {status.python_version}")
        print(f"Virtual Environment: {status.venv_type.value} (Active: {status.venv_active})")
        print(f"Config Files: {len(status.config_files)}")

        if status.requirements_file:
            print(f"Dependencies: {len(status.installed_packages)} installed, "
                  f"{len(status.missing_packages)} missing")

        # Print issues
        if status.issues:
            print()
            print(f"Issues Found: {len(status.issues)}")
            summary = status.issue_summary()
            print(f"  Errors: {summary['errors']}")
            print(f"  Warnings: {summary['warnings']}")
            print(f"  Info: {summary['info']}")

            print()
            print("Top Issues:")
            for issue in status.issues[:5]:
                print(f"  [{issue.severity.value.upper()}] {issue.message}")

        else:
            print()
            print("✓ No issues detected!")

    except Exception as e:
        print(f"Error during scan: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 80)
