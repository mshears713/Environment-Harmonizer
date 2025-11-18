"""
JSON Reporter Module.

This module generates machine-readable JSON reports from EnvironmentStatus data.

EDUCATIONAL NOTE - JSON Reports vs Text Reports:
JSON reports are designed for machines, not humans:
- Parseable: Easy for other programs to read
- Structured: Hierarchical data with types preserved
- Complete: Include all data without formatting for readability
- Portable: Language-independent format

Use cases for JSON reports:
1. CI/CD pipelines (automated checks)
2. Integration with other tools
3. Web dashboards
4. Automated monitoring
5. Historical tracking and analysis
"""

import json
from datetime import datetime
from dataclasses import asdict
from typing import Dict, Any

from harmonizer.models import EnvironmentStatus


class JSONReporter:
    """
    Generate machine-readable JSON reports from EnvironmentStatus.

    This class converts EnvironmentStatus data into a well-structured
    JSON format suitable for automated processing and tool integration.

    EDUCATIONAL NOTE - JSON Serialization:
    Python's json module can't directly serialize:
    - Dataclasses (need to convert to dict)
    - Enums (need to extract .value)
    - Paths (need to convert to string)
    - Datetime objects (need to format as ISO string)

    We handle all these conversions to produce clean JSON.

    Example:
        >>> reporter = JSONReporter(indent=2)
        >>> json_str = reporter.generate(env_status)
        >>> data = json.loads(json_str)
        >>> print(data['python']['version'])

    Attributes:
        indent: Number of spaces for JSON indentation (None for compact)
        include_metadata: Whether to include scan metadata
    """

    def __init__(self, indent: int = 2, include_metadata: bool = True):
        """
        Initialize the JSON reporter.

        Args:
            indent: Spaces for indentation (None for compact JSON)
            include_metadata: Include scan timestamp and other metadata
        """

        self.indent = indent
        self.include_metadata = include_metadata

    def generate(self, env_status: EnvironmentStatus) -> str:
        """
        Generate a complete JSON report from EnvironmentStatus.

        Args:
            env_status: Environment status data to report on

        Returns:
            JSON string representation of the environment status

        EDUCATIONAL NOTE - JSON Structure:
        We organize the JSON into logical sections:
        - metadata: Scan information
        - os: Operating system details
        - python: Python environment details
        - virtual_environment: Venv information
        - dependencies: Package information
        - config: Configuration files
        - issues: Detected problems
        - summary: High-level statistics

        This structure is more intuitive than flat key-value pairs.
        """

        data = self._build_data_structure(env_status)

        # Convert to JSON string
        return json.dumps(data, indent=self.indent, ensure_ascii=False)

    def generate_dict(self, env_status: EnvironmentStatus) -> Dict[str, Any]:
        """
        Generate a Python dictionary instead of JSON string.

        This is useful when you want to manipulate the data before
        converting to JSON, or when passing to other Python code.

        Args:
            env_status: Environment status data

        Returns:
            Dictionary representation of environment status
        """

        return self._build_data_structure(env_status)

    def _build_data_structure(self, env_status: EnvironmentStatus) -> Dict[str, Any]:
        """
        Build the complete data structure for JSON serialization.

        Args:
            env_status: Environment status data

        Returns:
            Dictionary ready for JSON serialization
        """

        data = {}

        # Metadata section
        if self.include_metadata:
            data["metadata"] = {
                "scan_time": datetime.now().isoformat(),
                "reporter_version": "1.0.0",
                "format_version": "1.0",
            }

        # Project information
        data["project"] = {
            "path": env_status.project_path,
        }

        # OS section
        data["os"] = {
            "type": env_status.os_type.value,
            "version": env_status.os_version,
        }

        # Python section
        data["python"] = {
            "version": env_status.python_version,
            "executable": env_status.python_executable,
        }

        # Virtual environment section
        data["virtual_environment"] = {
            "type": env_status.venv_type.value,
            "active": env_status.venv_active,
            "path": env_status.venv_path,
        }

        # Dependencies section
        data["dependencies"] = {
            "requirements_file": env_status.requirements_file,
            "total_installed": len(env_status.installed_packages),
            "total_missing": len(env_status.missing_packages),
            "installed_packages": sorted(env_status.installed_packages),
            "missing_packages": sorted(env_status.missing_packages),
        }

        # Configuration files section
        data["config_files"] = {
            "total": len(env_status.config_files),
            "files": sorted(env_status.config_files),
        }

        # Issues section
        data["issues"] = {
            "total": len(env_status.issues),
            "items": [self._serialize_issue(issue) for issue in env_status.issues],
        }

        # Summary section
        summary = env_status.issue_summary()
        data["summary"] = {
            "total_issues": len(env_status.issues),
            "errors": summary["errors"],
            "warnings": summary["warnings"],
            "info": summary["info"],
            "fixable_issues": len(env_status.get_fixable_issues()),
            "has_errors": env_status.has_errors(),
            "has_warnings": env_status.has_warnings(),
        }

        return data

    def _serialize_issue(self, issue) -> Dict[str, Any]:
        """
        Serialize a single Issue object to a dictionary.

        Args:
            issue: Issue object to serialize

        Returns:
            Dictionary representation of the issue
        """

        return {
            "severity": issue.severity.value,
            "category": issue.category,
            "message": issue.message,
            "fixable": issue.fixable,
            "fix_command": issue.fix_command,
        }


# Convenience function for quick JSON generation
def generate_json_report(
    env_status: EnvironmentStatus,
    indent: int = 2,
    include_metadata: bool = True
) -> str:
    """
    Convenience function to generate a JSON report.

    Args:
        env_status: Environment status data
        indent: Spaces for indentation (None for compact)
        include_metadata: Include scan metadata

    Returns:
        JSON string

    Example:
        >>> json_str = generate_json_report(env_status)
        >>> # Save to file
        >>> with open('report.json', 'w') as f:
        ...     f.write(json_str)
    """

    reporter = JSONReporter(indent=indent, include_metadata=include_metadata)
    return reporter.generate(env_status)


def generate_json_dict(
    env_status: EnvironmentStatus,
    include_metadata: bool = True
) -> Dict[str, Any]:
    """
    Convenience function to generate a JSON-compatible dictionary.

    Args:
        env_status: Environment status data
        include_metadata: Include scan metadata

    Returns:
        Dictionary ready for JSON serialization

    Example:
        >>> data = generate_json_dict(env_status)
        >>> print(data['python']['version'])
        3.10.6
    """

    reporter = JSONReporter(include_metadata=include_metadata)
    return reporter.generate_dict(env_status)


# Example usage and testing
if __name__ == "__main__":
    """
    Test the JSON reporter module.
    """

    from harmonizer.models import OSType, VenvType, IssueSeverity, Issue

    # Create a sample EnvironmentStatus for testing
    status = EnvironmentStatus(
        os_type=OSType.WSL,
        os_version="Ubuntu 22.04.1 LTS",
        python_version="3.10.6",
        python_executable="/usr/bin/python3",
        venv_type=VenvType.VIRTUALENV,
        venv_active=True,
        venv_path="/home/user/project/venv",
        project_path="/home/user/project",
        config_files=[".gitignore", "README.md", "requirements.txt", "setup.py"],
        requirements_file="requirements.txt",
        installed_packages=["numpy", "pandas", "matplotlib"],
        missing_packages=["requests", "flask"],
    )

    # Add some test issues
    status.add_issue(
        IssueSeverity.ERROR,
        "dependency",
        "2 required packages not installed",
        fixable=True,
        fix_command="pip install -r requirements.txt"
    )

    status.add_issue(
        IssueSeverity.WARNING,
        "wsl_performance",
        "Project on Windows filesystem - slower I/O",
        fixable=False
    )

    status.add_issue(
        IssueSeverity.INFO,
        "config",
        "Consider adding .editorconfig for consistent style",
        fixable=False
    )

    print("=" * 80)
    print("JSON Reporter Module - Test Run")
    print("=" * 80)
    print()

    # Test JSON string generation
    print("1. Formatted JSON Report:")
    print("-" * 80)
    reporter = JSONReporter(indent=2)
    json_str = reporter.generate(status)
    print(json_str)

    print()
    print("=" * 80)
    print()

    # Test compact JSON
    print("2. Compact JSON (no indentation):")
    print("-" * 80)
    compact_json = JSONReporter(indent=None).generate(status)
    print(compact_json[:200] + "...")  # Show first 200 chars

    print()
    print("=" * 80)
    print()

    # Test dictionary generation
    print("3. Dictionary Generation:")
    print("-" * 80)
    data = reporter.generate_dict(status)
    print(f"Python Version: {data['python']['version']}")
    print(f"Total Issues: {data['summary']['total_issues']}")
    print(f"Errors: {data['summary']['errors']}")
    print(f"Warnings: {data['summary']['warnings']}")
    print(f"Missing Packages: {data['dependencies']['missing_packages']}")

    print()
    print("=" * 80)
