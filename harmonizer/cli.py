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
from harmonizer.scanners.project_scanner import ProjectScanner
from harmonizer.reporters.text_reporter import TextReporter
from harmonizer.reporters.json_reporter import JSONReporter
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
        choices=["os", "python", "venv", "dependencies", "config", "quirks"],
        metavar="CHECK",
        help="""
        Run specific checks only (can be specified multiple times).
        Choices: os, python, venv, dependencies, config, quirks
        Example: --check python --check venv
        """,
    )

    scan_group.add_argument(
        "--skip",
        action="append",
        choices=["os", "python", "venv", "dependencies", "config", "quirks"],
        metavar="CHECK",
        help="""
        Skip specific checks (can be specified multiple times).
        Choices: os, python, venv, dependencies, config, quirks
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

    config_group.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="""
        Set logging level (default: INFO).
        DEBUG shows detailed diagnostic information.
        Logs are written to ~/.harmonizer/logs/
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
    This function now uses the ProjectScanner class to coordinate
    all detection modules. This provides better separation of concerns
    and makes the CLI focused on argument handling rather than
    detection logic.
    """

    # Determine which checks to run
    checks_to_run = _determine_checks(args)

    # Create scanner with verbose option
    scanner = ProjectScanner(args.project_path, verbose=args.verbose)

    # Run scan with specified checks
    env_status = scanner.scan(checks=checks_to_run)

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

    all_checks = {"os", "python", "venv", "dependencies", "config", "quirks"}

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
    We now use dedicated reporter classes for generating output:
    - TextReporter: Human-readable reports with color
    - JSONReporter: Machine-readable structured data

    This separation makes it easy to add new output formats
    (HTML, XML, etc.) without modifying the CLI logic.
    """

    if args.json:
        _display_json(env_status, args)
    else:
        _display_text(env_status, args)


def _display_text(env_status: EnvironmentStatus, args: argparse.Namespace) -> None:
    """
    Display results in human-readable text format using TextReporter.
    """

    # Create text reporter with color settings
    use_color = not args.no_color
    reporter = TextReporter(use_color=use_color, width=80)

    # Generate report
    report_text = reporter.generate(env_status)

    # Output to file or stdout
    if args.output:
        Path(args.output).write_text(report_text)
        print(f"Report written to: {args.output}")
    else:
        print(report_text)


def _display_json(env_status: EnvironmentStatus, args: argparse.Namespace) -> None:
    """
    Display results in JSON format using JSONReporter.
    """

    # Create JSON reporter
    reporter = JSONReporter(indent=2, include_metadata=True)

    # Generate JSON report
    json_output = reporter.generate(env_status)

    # Output to file or stdout
    if args.output:
        Path(args.output).write_text(json_output)
        print(f"JSON report written to: {args.output}")
    else:
        print(json_output)


def apply_fixes(env_status: EnvironmentStatus, args: argparse.Namespace) -> List:
    """
    Apply automated fixes to detected issues.

    Args:
        env_status: Environment status with detected issues
        args: Parsed arguments (contains fix options)

    Returns:
        List of FixResult objects from all fixers

    EDUCATIONAL NOTE - Fix Orchestration:
    Fixes are applied in a specific order to handle dependencies:
    1. Configuration files (needed for other operations)
    2. Virtual environment (needed for package installation)
    3. Dependencies (require active venv)

    Each fixer checks if it can fix anything before running.
    The --dry-run flag is passed through to all fixers.
    """

    from harmonizer.fixers import VenvFixer, DependencyFixer, ConfigFixer

    all_results = []
    dry_run = args.dry_run
    auto_yes = args.yes

    if dry_run:
        print("\n" + "=" * 70)
        print("DRY-RUN MODE: Previewing fixes without applying changes")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("APPLYING FIXES")
        print("=" * 70)

    # Order matters: configs -> venv -> dependencies
    fixer_classes = [
        ("Configuration", ConfigFixer),
        ("Virtual Environment", VenvFixer),
        ("Dependencies", DependencyFixer),
    ]

    for name, FixerClass in fixer_classes:
        fixer = FixerClass(env_status, verbose=args.verbose, auto_yes=auto_yes)

        if fixer.can_fix():
            print(f"\n[{name} Fixer]")
            results = fixer.apply_fixes(dry_run=dry_run)
            all_results.extend(results)
        elif args.verbose:
            print(f"\n[{name} Fixer]")
            print(f"  No applicable fixes")

    return all_results


def display_fix_results(fix_results: List, args: argparse.Namespace) -> None:
    """
    Display results of fix operations.

    Args:
        fix_results: List of FixResult objects
        args: Parsed arguments

    EDUCATIONAL NOTE - User Feedback:
    After running fixes, users need to know:
    1. What succeeded and what failed
    2. What they need to do manually
    3. Whether it's safe to proceed

    We provide:
    - Summary of all fixes attempted
    - Success/failure for each fix
    - Manual steps if needed (e.g., venv activation)
    """

    print("\n" + "=" * 70)
    print("FIX RESULTS SUMMARY")
    print("=" * 70)

    if not fix_results:
        print("\nNo fixes were applied.")
        return

    # Count successes and failures
    successes = [r for r in fix_results if r.success]
    failures = [r for r in fix_results if not r.success]

    # Display successful fixes
    if successes:
        print(f"\n✓ Successful fixes ({len(successes)}):")
        for result in successes:
            status = "[DRY-RUN] " if result.dry_run else ""
            print(f"  {status}✓ {result.message}")

    # Display failed fixes
    if failures:
        print(f"\n✗ Failed fixes ({len(failures)}):")
        for result in failures:
            print(f"  ✗ {result.message}")

    # Summary
    print("\n" + "-" * 70)
    print(f"Total: {len(successes)} succeeded, {len(failures)} failed")

    if args.dry_run:
        print("\nThis was a DRY-RUN. No actual changes were made.")
        print("Run without --dry-run to apply these fixes.")
    else:
        print("\nFixes have been applied.")
        print("Re-run the scan to verify the environment is now harmonized.")

    print("=" * 70)


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

    # Initialize logging early
    from harmonizer.utils.logging_config import HarmonizerLogger

    HarmonizerLogger.initialize(
        log_level=args.log_level if hasattr(args, 'log_level') else "INFO",
        enable_file_logging=True,
        enable_console_logging=False,  # We handle console output separately
    )

    logger = HarmonizerLogger.get_logger(__name__)
    logger.info(f"Environment Harmonizer started - Version {__version__}")
    logger.debug(f"Arguments: {vars(args)}")

    try:
        # Validate arguments
        validate_arguments(args)

        # Handle --init-config
        if args.init_config:
            from harmonizer.utils.config import create_default_config_file

            create_default_config_file()
            logger.info("Configuration file created successfully")
            return 0

        # Run scan
        logger.info(f"Starting scan of: {args.project_path}")
        env_status = run_scan(args)

        # Display results
        display_results(env_status, args)

        # Apply fixes if --fix flag is set
        if args.fix:
            logger.info(f"Applying fixes (dry_run={args.dry_run})")
            fix_results = apply_fixes(env_status, args)

            # Display fix results
            display_fix_results(fix_results, args)

        # Return exit code based on issues
        if env_status.has_errors():
            logger.warning(f"Scan completed with errors")
            return 1  # Exit with error if errors found

        logger.info("Scan completed successfully")
        return 0

    except ValueError as e:
        logger.error(f"Argument validation error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 2  # Argument validation error

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        print("\nInterrupted by user", file=sys.stderr)
        return 130  # Standard exit code for SIGINT

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"Unexpected error: {e}", file=sys.stderr)
        if hasattr(args, 'verbose') and args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
