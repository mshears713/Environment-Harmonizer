"""
Unit tests for Python version detection module.

This module tests the Python version detection functionality including:
- Current Python version detection
- Project Python requirements detection
- Version compatibility checking
- Parsing version specifications from various file formats
"""

import unittest
from unittest.mock import patch, mock_open, MagicMock
import sys
from pathlib import Path

from harmonizer.detectors.python_detector import (
    detect_python_version,
    get_project_python_requirement,
    check_version_compatibility,
    get_python_info_summary,
    _parse_python_version_from_pyproject,
    _parse_python_version_from_setup,
)
from harmonizer.models import IssueSeverity


class TestPythonVersionDetection(unittest.TestCase):
    """Test cases for Python version detection."""

    @patch('sys.version_info', (3, 10, 6, 'final', 0))
    @patch('sys.executable', '/usr/bin/python3')
    @patch('sys.implementation')
    def test_detect_python_version(self, mock_impl):
        """Test detecting current Python version."""
        mock_impl.name = 'cpython'

        result = detect_python_version()

        self.assertEqual(result['version'], '3.10.6')
        self.assertIn('3.10.6', result['version_info'])
        self.assertEqual(result['executable'], '/usr/bin/python3')
        self.assertEqual(result['implementation'], 'cpython')

    @patch('sys.version_info', (3, 11, 0, 'final', 0))
    @patch('sys.executable', '/opt/python3.11/bin/python3')
    @patch('sys.implementation')
    def test_detect_python_version_311(self, mock_impl):
        """Test detecting Python 3.11."""
        mock_impl.name = 'cpython'

        result = detect_python_version()

        self.assertEqual(result['version'], '3.11.0')
        self.assertEqual(result['implementation'], 'cpython')


class TestProjectPythonRequirement(unittest.TestCase):
    """Test cases for detecting project Python requirements."""

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_python_version_file(self, mock_read, mock_exists):
        """Test reading .python-version file."""
        mock_exists.return_value = True
        mock_read.return_value = "3.10.6\n"

        result = get_project_python_requirement(".")

        self.assertEqual(result, "3.10.6")

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_runtime_txt(self, mock_read, mock_exists):
        """Test reading runtime.txt file."""
        def exists_side_effect(self):
            # .python-version doesn't exist, runtime.txt does
            return self.name == 'runtime.txt'

        with patch.object(Path, 'exists', exists_side_effect):
            mock_read.return_value = "python-3.10.6"

            result = get_project_python_requirement(".")

            self.assertEqual(result, "3.10.6")

    @patch('pathlib.Path.exists', return_value=False)
    def test_no_python_requirement(self, mock_exists):
        """Test when no Python requirement file exists."""
        result = get_project_python_requirement(".")

        self.assertIsNone(result)


class TestPyprojectParsing(unittest.TestCase):
    """Test cases for parsing pyproject.toml files."""

    def test_parse_poetry_format(self):
        """Test parsing Poetry-style pyproject.toml."""
        content = '''
[tool.poetry.dependencies]
python = "^3.10"
requests = "^2.28.0"
'''
        mock_file = mock_open(read_data=content)

        with patch('builtins.open', mock_file):
            from pathlib import Path
            result = _parse_python_version_from_pyproject(Path("pyproject.toml"))

        self.assertEqual(result, "3.10")

    def test_parse_pep621_format(self):
        """Test parsing PEP 621 format pyproject.toml."""
        content = '''
[project]
name = "myproject"
requires-python = ">=3.10"
dependencies = [
    "requests>=2.28.0",
]
'''
        mock_file = mock_open(read_data=content)

        with patch('builtins.open', mock_file):
            from pathlib import Path
            result = _parse_python_version_from_pyproject(Path("pyproject.toml"))

        self.assertEqual(result, "3.10")

    def test_parse_pyproject_with_version_range(self):
        """Test parsing pyproject.toml with version range."""
        content = '''
[tool.poetry.dependencies]
python = ">=3.9,<4.0"
'''
        mock_file = mock_open(read_data=content)

        with patch('builtins.open', mock_file):
            from pathlib import Path
            result = _parse_python_version_from_pyproject(Path("pyproject.toml"))

        self.assertEqual(result, "3.9")

    def test_parse_pyproject_file_not_found(self):
        """Test handling of missing pyproject.toml."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            from pathlib import Path
            result = _parse_python_version_from_pyproject(Path("pyproject.toml"))

        self.assertIsNone(result)


class TestSetupPyParsing(unittest.TestCase):
    """Test cases for parsing setup.py files."""

    def test_parse_setup_py(self):
        """Test parsing setup.py with python_requires."""
        content = '''
from setuptools import setup

setup(
    name="myproject",
    version="1.0.0",
    python_requires=">=3.10",
    install_requires=[
        "requests>=2.28.0",
    ],
)
'''
        mock_file = mock_open(read_data=content)

        with patch('builtins.open', mock_file):
            from pathlib import Path
            result = _parse_python_version_from_setup(Path("setup.py"))

        self.assertEqual(result, "3.10")

    def test_parse_setup_py_with_range(self):
        """Test parsing setup.py with version range."""
        content = '''
setup(
    name="myproject",
    python_requires=">=3.8,<4",
)
'''
        mock_file = mock_open(read_data=content)

        with patch('builtins.open', mock_file):
            from pathlib import Path
            result = _parse_python_version_from_setup(Path("setup.py"))

        self.assertEqual(result, "3.8")

    def test_parse_setup_py_file_not_found(self):
        """Test handling of missing setup.py."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            from pathlib import Path
            result = _parse_python_version_from_setup(Path("setup.py"))

        self.assertIsNone(result)


class TestVersionCompatibility(unittest.TestCase):
    """Test cases for version compatibility checking."""

    def test_compatible_versions_exact_match(self):
        """Test compatible versions with exact match."""
        compatible, issue = check_version_compatibility("3.10.6", "3.10.6")

        self.assertTrue(compatible)
        self.assertIsNone(issue)

    def test_compatible_versions_higher_minor(self):
        """Test compatible versions with higher minor version."""
        compatible, issue = check_version_compatibility("3.11.0", "3.10")

        self.assertTrue(compatible)
        self.assertIsNone(issue)

    def test_compatible_versions_higher_micro(self):
        """Test compatible versions with higher micro version."""
        compatible, issue = check_version_compatibility("3.10.8", "3.10.6")

        self.assertTrue(compatible)
        self.assertIsNone(issue)

    def test_incompatible_versions_lower_minor(self):
        """Test incompatible versions with lower minor version."""
        compatible, issue = check_version_compatibility("3.9.0", "3.10")

        self.assertFalse(compatible)
        self.assertIsNotNone(issue)
        self.assertEqual(issue.severity, IssueSeverity.ERROR)
        self.assertIn("version mismatch", issue.message.lower())

    def test_incompatible_versions_lower_major(self):
        """Test incompatible versions with lower major version."""
        compatible, issue = check_version_compatibility("2.7.18", "3.10")

        self.assertFalse(compatible)
        self.assertIsNotNone(issue)
        self.assertEqual(issue.severity, IssueSeverity.ERROR)

    def test_version_parsing_error(self):
        """Test handling of version parsing errors."""
        compatible, issue = check_version_compatibility("3.10.6", "invalid.version")

        self.assertTrue(compatible)  # Allows to proceed
        self.assertIsNotNone(issue)
        self.assertEqual(issue.severity, IssueSeverity.WARNING)
        self.assertIn("parse", issue.message.lower())

    def test_version_comparison_different_lengths(self):
        """Test version comparison with different length version strings."""
        compatible, issue = check_version_compatibility("3.10", "3.10.6")

        self.assertTrue(compatible)
        self.assertIsNone(issue)


class TestPythonInfoSummary(unittest.TestCase):
    """Test cases for comprehensive Python info summary."""

    @patch('harmonizer.detectors.python_detector.detect_python_version')
    @patch('harmonizer.detectors.python_detector.get_project_python_requirement')
    def test_summary_with_no_requirement(self, mock_req, mock_detect):
        """Test summary when no project requirement exists."""
        mock_detect.return_value = {
            'version': '3.10.6',
            'version_info': '3.10.6 (final)',
            'executable': '/usr/bin/python3',
            'implementation': 'cpython',
        }
        mock_req.return_value = None

        result = get_python_info_summary(".")

        self.assertEqual(result['current']['version'], '3.10.6')
        self.assertIsNone(result['required'])
        self.assertTrue(result['compatible'])
        self.assertIsNone(result['issue'])

    @patch('harmonizer.detectors.python_detector.detect_python_version')
    @patch('harmonizer.detectors.python_detector.get_project_python_requirement')
    def test_summary_with_compatible_requirement(self, mock_req, mock_detect):
        """Test summary with compatible requirement."""
        mock_detect.return_value = {
            'version': '3.10.6',
            'version_info': '3.10.6 (final)',
            'executable': '/usr/bin/python3',
            'implementation': 'cpython',
        }
        mock_req.return_value = "3.10"

        result = get_python_info_summary(".")

        self.assertEqual(result['current']['version'], '3.10.6')
        self.assertEqual(result['required'], '3.10')
        self.assertTrue(result['compatible'])
        self.assertIsNone(result['issue'])

    @patch('harmonizer.detectors.python_detector.detect_python_version')
    @patch('harmonizer.detectors.python_detector.get_project_python_requirement')
    def test_summary_with_incompatible_requirement(self, mock_req, mock_detect):
        """Test summary with incompatible requirement."""
        mock_detect.return_value = {
            'version': '3.9.0',
            'version_info': '3.9.0 (final)',
            'executable': '/usr/bin/python3',
            'implementation': 'cpython',
        }
        mock_req.return_value = "3.10"

        result = get_python_info_summary(".")

        self.assertEqual(result['current']['version'], '3.9.0')
        self.assertEqual(result['required'], '3.10')
        self.assertFalse(result['compatible'])
        self.assertIsNotNone(result['issue'])
        self.assertEqual(result['issue'].severity, IssueSeverity.ERROR)


if __name__ == '__main__':
    unittest.main()
