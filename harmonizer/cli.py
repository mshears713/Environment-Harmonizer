"""
Command-Line Interface Module.

This module provides the CLI interface for Environment Harmonizer,
including argument parsing and command execution.

EDUCATIONAL NOTE - CLI Design Principles:
A good CLI should be:
1. Intuitive: Common operations should be simple
2. Discoverable: Help messages guide users
3. Consistent: Similar patterns for similar operations
4. Flexible: Support both simple and advanced use cases
5. Informative: Provide clear feedback and error messages
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from harmonizer import __version__
from harmonizer.models import EnvironmentStatus, OSType, VenvType, IssueSeverity
from harmonizer.detectors.os_detector import detect_os_type, get_os_version
from harmonizer.detectors.python_detector import detect_python_version, get_project_python_requirement, check_version_compatibility
from harmonizer.detectors.venv_detector import detect_venv_type
from harmonizer.utils.config import load_config_or_default, get_default_config


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser.

    Returns:
        Configured ArgumentParser instance

    EDUCATIONAL NOTE - argparse Basics:
    argparse is Python's standard library for building CLIs. Key concepts:
    - parser: Main ArgumentParser object
    - argument: Command-line parameter (positional or optional)
    - action: What to do when argument is encountered
    - help: Description shown in --help output

    Common argument types:
    - Positional: Required by position (e.g., "harmonizer PROJECT_PATH")
    - Optional: Start with - or -- (e.g., "--verbose")
    - Flags: Store True/False (e.g., "--json" stores True)
    - Valued: Take a value (e.g., "--output FILE")
    """

    parser = argparse.ArgumentParser(
        prog="harmonizer",
        description="""
        Environment Harmonizer - Detect and fix development environment issues.

        This tool scans your project directory to identify environment inconsistencies
        such as Python version mismatches, missing dependencies, inactive virtual
        environments, and platform-specific quirks.
        """,
        epilog="""
        Examples:
          # Scan current directory
          harmonizer

          # Scan specific project
          harmonizer /path/to/project

          # Output as JSON
          harmonizer --json

          # Preview fixes without applying
          harmonizer --fix --dry-run

          # Apply fixes
          harmonizer --fix

        For more information, visit: https://github.com/environment-harmonizer
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Version
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show program version and exit",
    )

    # Project path (positional argument)
    parser.add_argument(
        "project_path",
        nargs="?",  # Optional positional argument
        default=".",
        help="Path to project directory to scan (default: current directory)",
    )

    # Output options
    output_group = parser.add_argument_group("output options")

    output_group.add_argument(
        "--json",
        action="store_true",
        help="""
        Output diagnostic report in JSON format instead of human-readable text.
        Useful for integration with other tools and scripts.
        """,
    )

    output_group.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="""
        Enable verbose output with detailed diagnostic information.
        Shows detection methods, intermediate results, and debugging info.
        """,
    )

    output_group.add_argument(
        "--output",
        "-o",
        metavar="FILE",
        help="""
        Write diagnostic report to specified file instead of stdout.
        Format is determined by --json flag.
        """,
    )

    output_group.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output (useful for logging and piping)",
    )

    # Scanning options
    scan_group = parser.add_argument_group("scanning options")

    scan_group.add_argument(
        "--check",
        action="append",
        choices=["os", "python", "venv", "dependencies", "config"],
        metavar="CHECK",
        help="""
        Run specific checks only (can be specified multiple times).
        Choices: os, python, venv, dependencies, config
        Example: --check python --check venv
        """,
    )

    scan_group.add_argument(
        "--skip",
        action="append",
        choices=["os", "python", "venv", "dependencies", "config"],
        metavar="CHECK",
        help="""
        Skip specific checks (can be specified multiple times).
        Choices: os, python, venv, dependencies, config
        """,
    )

    # Fix options
    fix_group = parser.add_argument_group("fix options")

    fix_group.add_argument(
        "--fix",
        action="store_true",
        help="""
        Automatically apply fixes to detected issues.

        SAFETY: This will modify your environment by:
        - Installing missing dependencies
        - Activating virtual environments
        - Updating configuration files

        RECOMMENDATION: Always use --dry-run first to preview changes!
        """,
    )

    fix_group.add_argument(
        "--dry-run",
        action="store_true",
        help="""
        Show what fixes would be applied without actually applying them.
        This is a safe way to preview automatic fixes before running them.
        Must be used with --fix flag.
        """,
    )

    fix_group.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="""
        Automatically answer yes to all fix confirmation prompts.
        Use with caution! Recommended to use --dry-run first.
        """,
    )

    # Configuration
    config_group = parser.add_argument_group("configuration")

    config_group.add_argument(
        "--config",
        metavar="FILE",
        help="""
        Path to configuration file (default: .harmonizer.json).
        Configuration file can specify default scanning and fix options.
        """,
    )

    config_group.add_argument(
        "--init-config",
        action="store_true",
        help="""
        Create a default configuration file in the current directory.
        This generates .harmonizer.json with all default settings.
        """,
    )

    return parser


def validate_arguments(args: argparse.Namespace) -> None:
    """
    Validate parsed arguments for logical consistency.

    Args:
        args: Parsed arguments from argparse

    Raises:
        ValueError: If arguments are logically inconsistent

    EDUCATIONAL NOTE - Argument Validation:
    argparse handles basic validation (type, choices), but can't check
    logical dependencies between arguments. We handle that here:
    - --dry-run requires --fix
    - Can't use both --check and --skip
    - Project path must exist and be a directory
    """

    # Validate dry-run requires fix
    if args.dry_run and not args.fix:
        raise ValueError("--dry-run requires --fix flag")

    # Validate check and skip aren't used together
    if args.check and args.skip:
        raise ValueError("Cannot use both --check and --skip")

    # Validate project path exists
    project_path = Path(args.project_path)
    if not project_path.exists():
        raise ValueError(f"Project path does not exist: {args.project_path}")

    if not project_path.is_dir():
        raise ValueError(f"Project path is not a directory: {args.project_path}")


def run_scan(args: argparse.Namespace) -> EnvironmentStatus:
    """
    Run environment scan based on provided arguments.

    Args:
        args: Parsed command-line arguments

    Returns:
        EnvironmentStatus object with scan results

    EDUCATIONAL NOTE - Scan Orchestration:
    This function coordinates all the detector modules:
    1. Check which scans to run (based on --check/--skip)
    2. Run each enabled detector
    3. Aggregate results into EnvironmentStatus
    4. Return completed status object

    This is the "controller" in an MVC-like pattern.
    """

    # Determine which checks to run
    checks_to_run = _determine_checks(args)

    if args.verbose:
        print(f"Running checks: {', '.join(checks_to_run)}")

    # Initialize environment status with required fields
    # We'll populate these from detectors
    os_type = OSType.UNKNOWN
    os_version = "Unknown"
    python_version = "Unknown"
    python_executable = sys.executable
    venv_type = VenvType.NONE
    venv_active = False

    # Run OS detection
    if "os" in checks_to_run:
        if args.verbose:
            print("Detecting operating system...")
        os_type = detect_os_type()
        os_version = get_os_version()

    # Run Python detection
    if "python" in checks_to_run:
        if args.verbose:
            print("Detecting Python version...")
        py_info = detect_python_version()
        python_version = py_info["version"]
        python_executable = py_info["executable"]

    # Run virtual environment detection
    if "venv" in checks_to_run:
        if args.verbose:
            print("Detecting virtual environment...")
        venv_info = detect_venv_type()
        venv_type = venv_info["type"]
        venv_active = venv_info["active"]

    # Create EnvironmentStatus object
    env_status = EnvironmentStatus(
        os_type=os_type,
        os_version=os_version,
        python_version=python_version,
        python_executable=python_executable,
        venv_type=venv_type,
        venv_active=venv_active,
        project_path=str(Path(args.project_path).resolve()),
    )

    # Add venv path if detected
    if venv_info.get("path"):
        env_status.venv_path = venv_info["path"]

    # Check Python version compatibility
    if "python" in checks_to_run:
        required_version = get_project_python_requirement(args.project_path)
        if required_version:
            compatible, issue = check_version_compatibility(
                python_version, required_version
            )
            if issue:
                env_status.issues.append(issue)

    # Check if virtual environment should be active but isn't
    if "venv" in checks_to_run:
        if venv_type != VenvType.NONE and not venv_active:
            env_status.add_issue(
                IssueSeverity.WARNING,
                "venv",
                f"Virtual environment detected ({venv_type.value}) but not active",
                fixable=True,
                fix_command=f"Activate virtual environment at {venv_info.get('path', 'unknown')}",
            )

    return env_status


def _determine_checks(args: argparse.Namespace) -> List[str]:
    """
    Determine which checks to run based on --check and --skip flags.

    Args:
        args: Parsed arguments

    Returns:
        List of check names to run

    EDUCATIONAL NOTE - Set Operations:
    We use Python sets for efficient inclusion/exclusion:
    - Start with all possible checks
    - If --check specified, keep only those
    - If --skip specified, remove those
    - Convert back to list for iteration
    """

    all_checks = {"os", "python", "venv", "dependencies", "config"}

    if args.check:
        # Only run specified checks
        return list(set(args.check))

    if args.skip:
        # Run all except skipped
        return list(all_checks - set(args.skip))

    # Run all checks by default
    return list(all_checks)


def display_results(env_status: EnvironmentStatus, args: argparse.Namespace) -> None:
    """
    Display scan results based on output format.

    Args:
        env_status: Environment status to display
        args: Parsed arguments (contains output format options)

    EDUCATIONAL NOTE - Output Formatting:
    Different output formats serve different purposes:
    - Text: Human-readable, good for terminal use
    - JSON: Machine-readable, good for automation
    - Colored: Enhanced readability in terminals
    - Plain: Compatible with logs and pipes
    """

    if args.json:
        _display_json(env_status, args)
    else:
        _display_text(env_status, args)


def _display_text(env_status: EnvironmentStatus, args: argparse.Namespace) -> None:
    """
    Display results in human-readable text format.
    """

    output_lines = []

    # Header
    output_lines.append("=" * 80)
    output_lines.append("ENVIRONMENT HARMONIZER - Diagnostic Report")
    output_lines.append("=" * 80)
    output_lines.append("")

    # Project info
    output_lines.append(f"Project Path: {env_status.project_path}")
    output_lines.append("")

    # OS info
    output_lines.append("[OS ENVIRONMENT]")
    output_lines.append(f"  Type: {env_status.os_type.value}")
    output_lines.append(f"  Version: {env_status.os_version}")
    output_lines.append("")

    # Python info
    output_lines.append("[PYTHON ENVIRONMENT]")
    output_lines.append(f"  Version: {env_status.python_version}")
    output_lines.append(f"  Executable: {env_status.python_executable}")
    output_lines.append("")

    # Virtual environment info
    output_lines.append("[VIRTUAL ENVIRONMENT]")
    output_lines.append(f"  Type: {env_status.venv_type.value}")
    output_lines.append(f"  Active: {'Yes' if env_status.venv_active else 'No'}")
    if env_status.venv_path:
        output_lines.append(f"  Path: {env_status.venv_path}")
    output_lines.append("")

    # Issues
    if env_status.issues:
        output_lines.append(f"[DETECTED ISSUES] ({len(env_status.issues)} total)")
        output_lines.append("")

        for issue in env_status.issues:
            severity_symbol = {
                IssueSeverity.ERROR: "✗",
                IssueSeverity.WARNING: "⚠",
                IssueSeverity.INFO: "ℹ",
            }
            symbol = severity_symbol.get(issue.severity, "•")

            output_lines.append(f"  [{issue.severity.value.upper()}] {issue.message}")
            if issue.fixable:
                output_lines.append(f"    Fixable: Yes")
                if issue.fix_command:
                    output_lines.append(f"    Fix: {issue.fix_command}")
            else:
                output_lines.append(f"    Fixable: No")
            output_lines.append("")

        # Summary
        summary = env_status.issue_summary()
        output_lines.append("=" * 80)
        output_lines.append(
            f"Summary: {summary['errors']} error(s), "
            f"{summary['warnings']} warning(s), {summary['info']} info"
        )

        fixable = len(env_status.get_fixable_issues())
        if fixable > 0:
            output_lines.append(f"Run with --fix to apply {fixable} automated fix(es)")
    else:
        output_lines.append("[NO ISSUES DETECTED]")
        output_lines.append("  ✓ Environment appears to be properly configured")

    output_lines.append("=" * 80)

    # Output to file or stdout
    output_text = "\n".join(output_lines)

    if args.output:
        Path(args.output).write_text(output_text)
        print(f"Report written to: {args.output}")
    else:
        print(output_text)


def _display_json(env_status: EnvironmentStatus, args: argparse.Namespace) -> None:
    """
    Display results in JSON format.
    """

    import json
    from dataclasses import asdict

    # Convert dataclass to dict (handling enums)
    status_dict = asdict(env_status)

    # Convert enums to their string values
    status_dict["os_type"] = env_status.os_type.value
    status_dict["venv_type"] = env_status.venv_type.value

    # Convert issues
    status_dict["issues"] = [
        {
            "severity": issue.severity.value,
            "category": issue.category,
            "message": issue.message,
            "fixable": issue.fixable,
            "fix_command": issue.fix_command,
        }
        for issue in env_status.issues
    ]

    # Add summary
    status_dict["summary"] = env_status.issue_summary()

    json_output = json.dumps(status_dict, indent=2)

    if args.output:
        Path(args.output).write_text(json_output)
        print(f"JSON report written to: {args.output}")
    else:
        print(json_output)


def main(argv: Optional[List[str]] = None) -> int:
    """
    Main entry point for the CLI.

    Args:
        argv: Command-line arguments (defaults to sys.argv)

    Returns:
        Exit code (0 for success, non-zero for error)

    EDUCATIONAL NOTE - Exit Codes:
    Unix convention for exit codes:
    - 0: Success
    - 1: General error
    - 2: Misuse of command
    - Other: Application-specific errors
    """

    parser = create_parser()
    args = parser.parse_args(argv)

    try:
        # Validate arguments
        validate_arguments(args)

        # Handle --init-config
        if args.init_config:
            from harmonizer.utils.config import create_default_config_file

            create_default_config_file()
            return 0

        # Run scan
        env_status = run_scan(args)

        # Display results
        display_results(env_status, args)

        # Return exit code based on issues
        if env_status.has_errors():
            return 1  # Exit with error if errors found

        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2  # Argument validation error

    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130  # Standard exit code for SIGINT

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
