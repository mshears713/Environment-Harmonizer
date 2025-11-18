"""
Text Reporter Module.

This module generates human-readable text reports from EnvironmentStatus data.

EDUCATIONAL NOTE - Report Design Principles:
Good reports should be:
1. Clear: Easy to understand at a glance
2. Scannable: Important information stands out
3. Actionable: Tell users what to do about issues
4. Progressive: Show summary first, details on request
5. Consistent: Use predictable formatting

Text reports are for humans, so we prioritize readability over precision.
"""

from datetime import datetime
from typing import Optional
from harmonizer.models import EnvironmentStatus, IssueSeverity


class TextReporter:
    """
    Generate human-readable text reports from EnvironmentStatus.

    This class formats EnvironmentStatus data into a clear, well-organized
    text report suitable for terminal display or log files.

    EDUCATIONAL NOTE - Formatter Classes:
    We use a class instead of a simple function because:
    1. Configuration: Store formatting preferences (colors, width, etc.)
    2. Reusability: Create once, generate multiple reports
    3. Extensibility: Subclass for different text formats
    4. Testability: Easy to test with different configurations

    Example:
        >>> reporter = TextReporter(use_color=True)
        >>> report = reporter.generate(env_status)
        >>> print(report)

    Attributes:
        use_color: Whether to use ANSI color codes
        width: Maximum line width for formatting
    """

    def __init__(self, use_color: bool = True, width: int = 80):
        """
        Initialize the text reporter.

        Args:
            use_color: Enable ANSI color codes (default: True)
            width: Maximum line width (default: 80 characters)
        """

        self.use_color = use_color
        self.width = width

        # ANSI color codes (only used if use_color is True)
        self.colors = {
            "reset": "\033[0m" if use_color else "",
            "bold": "\033[1m" if use_color else "",
            "red": "\033[91m" if use_color else "",
            "yellow": "\033[93m" if use_color else "",
            "green": "\033[92m" if use_color else "",
            "blue": "\033[94m" if use_color else "",
            "cyan": "\033[96m" if use_color else "",
        }

    def generate(self, env_status: EnvironmentStatus) -> str:
        """
        Generate a complete text report from EnvironmentStatus.

        Args:
            env_status: Environment status data to report on

        Returns:
            Formatted text report as a string

        EDUCATIONAL NOTE - String Building:
        We build the report by accumulating lines in a list and joining
        them at the end. This is more efficient than string concatenation:

        SLOW:  report = report + line + "\\n"  # Creates new string each time
        FAST:  lines.append(line)              # Appends to list
               return "\\n".join(lines)        # Join once at end
        """

        lines = []

        # Header
        lines.extend(self._generate_header())

        # Project information
        lines.extend(self._generate_project_info(env_status))

        # OS Environment section
        lines.extend(self._generate_os_section(env_status))

        # Python Environment section
        lines.extend(self._generate_python_section(env_status))

        # Virtual Environment section
        lines.extend(self._generate_venv_section(env_status))

        # Dependencies section
        lines.extend(self._generate_dependencies_section(env_status))

        # Configuration Files section
        lines.extend(self._generate_config_section(env_status))

        # Issues section
        lines.extend(self._generate_issues_section(env_status))

        # Fixable Issues Highlight section
        lines.extend(self._generate_fixable_summary(env_status))

        # Footer with summary
        lines.extend(self._generate_footer(env_status))

        return "\n".join(lines)

    def _generate_header(self) -> list:
        """Generate report header."""

        lines = []
        separator = "=" * self.width

        lines.append(separator)
        lines.append(
            self._colorize("ENVIRONMENT HARMONIZER - Diagnostic Report", "bold")
        )
        lines.append(separator)
        lines.append("")

        return lines

    def _generate_project_info(self, env_status: EnvironmentStatus) -> list:
        """Generate project information section."""

        lines = []

        lines.append(f"Project Path: {env_status.project_path}")
        lines.append(f"Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        return lines

    def _generate_os_section(self, env_status: EnvironmentStatus) -> list:
        """Generate OS environment section."""

        lines = []

        lines.append(self._colorize("[OS ENVIRONMENT]", "bold"))
        lines.append(f"  Type: {env_status.os_type.value}")
        lines.append(f"  Version: {env_status.os_version}")
        lines.append("")

        return lines

    def _generate_python_section(self, env_status: EnvironmentStatus) -> list:
        """Generate Python environment section."""

        lines = []

        lines.append(self._colorize("[PYTHON ENVIRONMENT]", "bold"))
        lines.append(f"  Version: {env_status.python_version}")
        lines.append(f"  Executable: {env_status.python_executable}")
        lines.append("")

        return lines

    def _generate_venv_section(self, env_status: EnvironmentStatus) -> list:
        """Generate virtual environment section."""

        lines = []

        lines.append(self._colorize("[VIRTUAL ENVIRONMENT]", "bold"))
        lines.append(f"  Type: {env_status.venv_type.value}")

        # Color code active status
        if env_status.venv_active:
            active_text = self._colorize("Yes", "green")
        else:
            active_text = self._colorize("No", "yellow")

        lines.append(f"  Active: {active_text}")

        if env_status.venv_path:
            lines.append(f"  Path: {env_status.venv_path}")

        lines.append("")

        return lines

    def _generate_dependencies_section(self, env_status: EnvironmentStatus) -> list:
        """Generate dependencies section."""

        lines = []

        lines.append(self._colorize("[DEPENDENCIES]", "bold"))

        if env_status.requirements_file:
            lines.append(f"  Requirements File: {env_status.requirements_file}")
            lines.append(f"  Installed Packages: {len(env_status.installed_packages)}")

            if env_status.missing_packages:
                lines.append(
                    f"  Missing Packages: {self._colorize(str(len(env_status.missing_packages)), 'red')}"
                )
                # Show first few missing packages
                for pkg in env_status.missing_packages[:5]:
                    lines.append(f"    {self._colorize('✗', 'red')} {pkg}")
                if len(env_status.missing_packages) > 5:
                    lines.append(
                        f"    ... and {len(env_status.missing_packages) - 5} more"
                    )
            else:
                lines.append(
                    f"  {self._colorize('✓', 'green')} All dependencies installed"
                )
        else:
            lines.append(f"  {self._colorize('ℹ', 'blue')} No requirements file found")

        lines.append("")

        return lines

    def _generate_config_section(self, env_status: EnvironmentStatus) -> list:
        """Generate configuration files section."""

        lines = []

        lines.append(self._colorize("[CONFIGURATION FILES]", "bold"))

        if env_status.config_files:
            lines.append(f"  Found: {len(env_status.config_files)} files")
            # Show first few config files
            for config in sorted(env_status.config_files)[:10]:
                lines.append(f"    {self._colorize('✓', 'green')} {config}")
            if len(env_status.config_files) > 10:
                lines.append(f"    ... and {len(env_status.config_files) - 10} more")
        else:
            lines.append(f"  {self._colorize('ℹ', 'blue')} No config files detected")

        lines.append("")

        return lines

    def _generate_issues_section(self, env_status: EnvironmentStatus) -> list:
        """Generate detected issues section."""

        lines = []

        if not env_status.issues:
            lines.append(self._colorize("[NO ISSUES DETECTED]", "green", bold=True))
            lines.append(
                f"  {self._colorize('✓', 'green')} Environment appears to be properly configured"
            )
            lines.append("")
            return lines

        lines.append(
            self._colorize(
                f"[DETECTED ISSUES] ({len(env_status.issues)} total)", "bold"
            )
        )
        lines.append("")

        # Group issues by severity
        errors = [i for i in env_status.issues if i.severity == IssueSeverity.ERROR]
        warnings = [i for i in env_status.issues if i.severity == IssueSeverity.WARNING]
        infos = [i for i in env_status.issues if i.severity == IssueSeverity.INFO]

        # Show errors first (most important)
        for issue in errors:
            lines.extend(self._format_issue(issue, "ERROR", "red"))

        # Then warnings
        for issue in warnings:
            lines.extend(self._format_issue(issue, "WARNING", "yellow"))

        # Finally info
        for issue in infos:
            lines.extend(self._format_issue(issue, "INFO", "blue"))

        return lines

    def _format_issue(self, issue, severity_label: str, color: str) -> list:
        """
        Format a single issue for display.

        Args:
            issue: Issue object to format
            severity_label: Label text (ERROR, WARNING, INFO)
            color: Color name for the severity

        Returns:
            List of formatted lines for this issue
        """

        lines = []

        # Issue header with severity
        header = f"[{severity_label}] {issue.message}"
        lines.append(f"  {self._colorize(header, color, bold=True)}")

        # Category
        lines.append(f"    Category: {issue.category}")

        # Fixable status
        if issue.fixable:
            lines.append(f"    Fixable: {self._colorize('Yes', 'green')}")
            if issue.fix_command:
                lines.append(f"    Fix: {self._colorize(issue.fix_command, 'cyan')}")
        else:
            lines.append(f"    Fixable: No")

        lines.append("")

        return lines

    def _generate_fixable_summary(self, env_status: EnvironmentStatus) -> list:
        """
        Generate a prominent summary of fixable issues.

        This section appears after the detailed issues list and provides
        a quick reference for what can be automatically fixed.

        EDUCATIONAL NOTE - Actionable Reporting:
        Good reports not only identify problems but also clearly indicate
        what can be done about them. By grouping fixable issues together:
        1. Users quickly see what can be automated
        2. Clear call-to-action (run with --fix)
        3. Shows fix commands for manual execution if preferred
        """

        fixable_issues = env_status.get_fixable_issues()

        if not fixable_issues:
            return []

        lines = []
        separator = "-" * self.width

        lines.append(separator)
        lines.append(
            self._colorize(
                f"[FIXABLE ISSUES] - {len(fixable_issues)} issue(s) can be automatically fixed",
                "cyan",
                bold=True,
            )
        )
        lines.append("")

        # Group fixable issues by category for better organization
        by_category = {}
        for issue in fixable_issues:
            if issue.category not in by_category:
                by_category[issue.category] = []
            by_category[issue.category].append(issue)

        # Display fixable issues by category
        for category, issues in sorted(by_category.items()):
            category_name = category.replace("_", " ").title()
            lines.append(
                f"  {self._colorize('●', 'green')} {category_name} ({len(issues)} fix{'es' if len(issues) > 1 else ''}):"
            )

            for issue in issues:
                # Show the issue message
                severity_icon = {
                    IssueSeverity.ERROR: "✗",
                    IssueSeverity.WARNING: "⚠",
                    IssueSeverity.INFO: "ℹ",
                }.get(issue.severity, "•")

                lines.append(f"      {severity_icon} {issue.message}")

                # Show fix command if available
                if issue.fix_command:
                    lines.append(
                        f"        Fix: {self._colorize(issue.fix_command, 'cyan')}"
                    )

            lines.append("")

        # Call to action
        lines.append(
            self._colorize(
                "  💡 TIP: Run with --fix to apply all automated fixes", "cyan"
            )
        )
        lines.append(
            self._colorize(
                "  💡 TIP: Run with --fix --dry-run to preview changes first", "cyan"
            )
        )
        lines.append("")

        return lines

    def _generate_footer(self, env_status: EnvironmentStatus) -> list:
        """Generate report footer with summary."""

        lines = []
        separator = "=" * self.width

        lines.append(separator)

        if env_status.issues:
            summary = env_status.issue_summary()

            # Color-code summary based on severity
            summary_parts = []

            if summary["errors"] > 0:
                summary_parts.append(
                    self._colorize(f"{summary['errors']} error(s)", "red")
                )
            else:
                summary_parts.append(f"{summary['errors']} error(s)")

            if summary["warnings"] > 0:
                summary_parts.append(
                    self._colorize(f"{summary['warnings']} warning(s)", "yellow")
                )
            else:
                summary_parts.append(f"{summary['warnings']} warning(s)")

            if summary["info"] > 0:
                summary_parts.append(self._colorize(f"{summary['info']} info", "blue"))
            else:
                summary_parts.append(f"{summary['info']} info")

            lines.append(f"Summary: {', '.join(summary_parts)}")

            # Show fixable issues count
            fixable = len(env_status.get_fixable_issues())
            if fixable > 0:
                lines.append(
                    self._colorize(
                        f"Run with --fix to apply {fixable} automated fix(es)", "cyan"
                    )
                )
        else:
            lines.append(
                self._colorize(
                    "✓ No issues detected - environment is healthy!", "green"
                )
            )

        lines.append(separator)

        return lines

    def _colorize(self, text: str, color: str, bold: bool = False) -> str:
        """
        Apply ANSI color codes to text.

        Args:
            text: Text to colorize
            color: Color name (red, green, yellow, blue, cyan)
            bold: Whether to make text bold

        Returns:
            Text with ANSI color codes (if use_color is True)

        EDUCATIONAL NOTE - ANSI Color Codes:
        ANSI escape codes control terminal formatting:
        - \\033[91m - Red text
        - \\033[92m - Green text
        - \\033[1m - Bold text
        - \\033[0m - Reset formatting

        Not all terminals support colors, so we make it optional.
        """

        if not self.use_color:
            return text

        color_code = self.colors.get(color, "")
        bold_code = self.colors["bold"] if bold else ""
        reset = self.colors["reset"]

        return f"{bold_code}{color_code}{text}{reset}"


# Convenience function for quick report generation
def generate_text_report(
    env_status: EnvironmentStatus, use_color: bool = True, width: int = 80
) -> str:
    """
    Convenience function to generate a text report.

    Args:
        env_status: Environment status data
        use_color: Enable ANSI color codes
        width: Maximum line width

    Returns:
        Formatted text report

    Example:
        >>> report = generate_text_report(env_status)
        >>> print(report)
    """

    reporter = TextReporter(use_color=use_color, width=width)
    return reporter.generate(env_status)


# Example usage and testing
if __name__ == "__main__":
    """
    Test the text reporter module.
    """

    from harmonizer.models import OSType, VenvType, Issue

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
        missing_packages=["requests", "flask"],
    )

    # Add some test issues
    status.add_issue(
        IssueSeverity.ERROR,
        "dependency",
        "2 required packages not installed",
        fixable=True,
        fix_command="pip install -r requirements.txt",
    )

    status.add_issue(
        IssueSeverity.WARNING,
        "wsl_performance",
        "Project on Windows filesystem - slower I/O",
        fixable=False,
    )

    status.add_issue(
        IssueSeverity.INFO,
        "config",
        "Consider adding .editorconfig for consistent style",
        fixable=False,
    )

    # Generate and print report
    print("=" * 80)
    print("Text Reporter Module - Test Run")
    print("=" * 80)
    print()

    reporter = TextReporter(use_color=True)
    report = reporter.generate(status)
    print(report)
