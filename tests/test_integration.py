"""
Integration tests for Environment Harmonizer.

This module tests the full end-to-end functionality of the tool,
including CLI interface, scanning, and reporting.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch
import sys

from harmonizer.scanners.project_scanner import ProjectScanner
from harmonizer.cli import create_parser, validate_arguments, run_scan
from harmonizer.models import OSType, VenvType, IssueSeverity


class TestProjectScanner(unittest.TestCase):
    """Integration tests for ProjectScanner."""

    def setUp(self):
        """Set up a temporary test project directory."""
        self.test_dir = tempfile.mkdtemp()
        self.test_project = Path(self.test_dir)

    def tearDown(self):
        """Clean up temporary test directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_scan_empty_project(self):
        """Test scanning an empty project directory."""
        scanner = ProjectScanner(str(self.test_project))
        env_status = scanner.scan()

        # Should detect OS and Python
        self.assertIsNotNone(env_status.os_type)
        self.assertIsNotNone(env_status.python_version)

        # Should have OS type that's not UNKNOWN
        self.assertNotEqual(env_status.os_type, OSType.UNKNOWN)

    def test_scan_project_with_requirements(self):
        """Test scanning a project with requirements.txt."""
        # Create a requirements.txt file
        req_file = self.test_project / "requirements.txt"
        req_file.write_text("requests==2.28.1\nflask>=2.0.0\n")

        scanner = ProjectScanner(str(self.test_project))
        env_status = scanner.scan()

        # Should detect requirements file
        self.assertIsNotNone(env_status.requirements_file)
        self.assertIn("requirements.txt", env_status.requirements_file)

        # Should detect required packages
        self.assertGreater(len(env_status.required_packages), 0)

    def test_scan_project_with_python_version(self):
        """Test scanning a project with .python-version file."""
        # Create a .python-version file
        py_version_file = self.test_project / ".python-version"
        py_version_file.write_text("3.10.6\n")

        scanner = ProjectScanner(str(self.test_project))
        env_status = scanner.scan()

        # Should detect Python version requirement
        self.assertIsNotNone(env_status.python_version)

    def test_scan_with_specific_checks(self):
        """Test scanning with specific check filters."""
        scanner = ProjectScanner(str(self.test_project))
        env_status = scanner.scan(checks=['os', 'python'])

        # Should have scanned these checks
        self.assertIsNotNone(env_status.os_type)
        self.assertIsNotNone(env_status.python_version)

    def test_scan_verbose_mode(self):
        """Test scanning in verbose mode."""
        scanner = ProjectScanner(str(self.test_project), verbose=True)
        env_status = scanner.scan()

        # Verbose mode should still produce valid results
        self.assertIsNotNone(env_status)
        self.assertIsNotNone(env_status.os_type)


class TestCLIArgumentParsing(unittest.TestCase):
    """Integration tests for CLI argument parsing."""

    def test_parser_default_args(self):
        """Test parser with default arguments."""
        parser = create_parser()
        args = parser.parse_args([])

        self.assertEqual(args.project_path, '.')
        self.assertFalse(args.json)
        self.assertFalse(args.verbose)
        self.assertFalse(args.fix)

    def test_parser_with_project_path(self):
        """Test parser with explicit project path."""
        parser = create_parser()
        args = parser.parse_args(['/path/to/project'])

        self.assertEqual(args.project_path, '/path/to/project')

    def test_parser_with_json_flag(self):
        """Test parser with JSON output flag."""
        parser = create_parser()
        args = parser.parse_args(['--json'])

        self.assertTrue(args.json)

    def test_parser_with_verbose_flag(self):
        """Test parser with verbose flag."""
        parser = create_parser()
        args = parser.parse_args(['-v'])

        self.assertTrue(args.verbose)

    def test_parser_with_fix_and_dry_run(self):
        """Test parser with fix and dry-run flags."""
        parser = create_parser()
        args = parser.parse_args(['--fix', '--dry-run'])

        self.assertTrue(args.fix)
        self.assertTrue(args.dry_run)

    def test_parser_with_check_filters(self):
        """Test parser with specific check filters."""
        parser = create_parser()
        args = parser.parse_args(['--check', 'os', '--check', 'python'])

        self.assertEqual(args.check, ['os', 'python'])


class TestCLIValidation(unittest.TestCase):
    """Integration tests for CLI argument validation."""

    def setUp(self):
        """Set up a temporary test directory."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary test directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_validate_valid_project_path(self):
        """Test validation with valid project path."""
        parser = create_parser()
        args = parser.parse_args([self.test_dir])

        # Should not raise
        try:
            validate_arguments(args)
        except ValueError:
            self.fail("validate_arguments raised ValueError unexpectedly")

    def test_validate_nonexistent_path(self):
        """Test validation with non-existent path."""
        parser = create_parser()
        args = parser.parse_args(['/nonexistent/path/12345'])

        with self.assertRaises(ValueError) as context:
            validate_arguments(args)

        self.assertIn("does not exist", str(context.exception))

    def test_validate_dry_run_without_fix(self):
        """Test validation fails when dry-run without fix."""
        parser = create_parser()
        args = parser.parse_args(['--dry-run'])

        with self.assertRaises(ValueError) as context:
            validate_arguments(args)

        self.assertIn("--dry-run requires --fix", str(context.exception))

    def test_validate_check_and_skip_together(self):
        """Test validation fails when both check and skip specified."""
        parser = create_parser()
        args = parser.parse_args(['--check', 'os', '--skip', 'python'])

        with self.assertRaises(ValueError) as context:
            validate_arguments(args)

        self.assertIn("Cannot use both --check and --skip", str(context.exception))


class TestCLIScan(unittest.TestCase):
    """Integration tests for CLI scanning."""

    def setUp(self):
        """Set up a temporary test project directory."""
        self.test_dir = tempfile.mkdtemp()
        self.test_project = Path(self.test_dir)

    def tearDown(self):
        """Clean up temporary test directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_run_scan_basic(self):
        """Test running a basic scan through CLI."""
        parser = create_parser()
        args = parser.parse_args([self.test_dir])

        env_status = run_scan(args)

        # Should complete successfully
        self.assertIsNotNone(env_status)
        self.assertIsNotNone(env_status.os_type)
        self.assertIsNotNone(env_status.python_version)

    def test_run_scan_with_requirements(self):
        """Test running scan on project with requirements."""
        # Create requirements.txt
        req_file = self.test_project / "requirements.txt"
        req_file.write_text("requests\nflask\n")

        parser = create_parser()
        args = parser.parse_args([self.test_dir])

        env_status = run_scan(args)

        # Should detect requirements
        self.assertIsNotNone(env_status.requirements_file)
        self.assertGreater(len(env_status.required_packages), 0)

    def test_run_scan_verbose(self):
        """Test running scan in verbose mode."""
        parser = create_parser()
        args = parser.parse_args([self.test_dir, '-v'])

        # Should complete without errors
        env_status = run_scan(args)
        self.assertIsNotNone(env_status)


class TestEnvironmentStatusModel(unittest.TestCase):
    """Integration tests for EnvironmentStatus data model."""

    def test_create_environment_status(self):
        """Test creating a basic EnvironmentStatus."""
        from harmonizer.models import EnvironmentStatus

        env = EnvironmentStatus(
            os_type=OSType.LINUX,
            os_version="Ubuntu 22.04",
            python_version="3.10.6",
            python_executable="/usr/bin/python3",
            venv_type=VenvType.NONE,
            venv_active=False,
            project_path=".",
        )

        self.assertEqual(env.os_type, OSType.LINUX)
        self.assertEqual(env.python_version, "3.10.6")
        self.assertEqual(env.venv_type, VenvType.NONE)

    def test_add_issues_to_environment_status(self):
        """Test adding issues to EnvironmentStatus."""
        from harmonizer.models import EnvironmentStatus

        env = EnvironmentStatus(
            os_type=OSType.LINUX,
            os_version="Ubuntu 22.04",
            python_version="3.10.6",
            python_executable="/usr/bin/python3",
            venv_type=VenvType.NONE,
            venv_active=False,
            project_path=".",
        )

        env.add_issue(
            severity=IssueSeverity.ERROR,
            category="test",
            message="Test error message",
            fixable=False
        )

        self.assertEqual(len(env.issues), 1)
        self.assertEqual(env.issues[0].severity, IssueSeverity.ERROR)
        self.assertEqual(env.issues[0].category, "test")

    def test_has_errors_method(self):
        """Test has_errors method."""
        from harmonizer.models import EnvironmentStatus

        env = EnvironmentStatus(
            os_type=OSType.LINUX,
            os_version="Ubuntu 22.04",
            python_version="3.10.6",
            python_executable="/usr/bin/python3",
            venv_type=VenvType.NONE,
            venv_active=False,
            project_path=".",
        )

        # No errors initially
        self.assertFalse(env.has_errors())

        # Add a warning
        env.add_issue(
            severity=IssueSeverity.WARNING,
            category="test",
            message="Test warning",
            fixable=False
        )
        self.assertFalse(env.has_errors())

        # Add an error
        env.add_issue(
            severity=IssueSeverity.ERROR,
            category="test",
            message="Test error",
            fixable=False
        )
        self.assertTrue(env.has_errors())


if __name__ == '__main__':
    unittest.main()
