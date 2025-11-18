"""
Unit tests for dependency detection module.

This module tests dependency scanning functionality including:
- Parsing various dependency file formats
- Detecting missing packages
- Package version detection
- Installed package listing
"""

import unittest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

from harmonizer.detectors.dependency_detector import (
    scan_dependencies,
    parse_requirements_txt,
    parse_pyproject_toml,
    parse_setup_py,
    parse_pipfile,
    get_installed_packages,
    find_missing_packages,
    check_package_installed,
    get_package_version,
)


class TestRequirementsTxtParsing(unittest.TestCase):
    """Test cases for parsing requirements.txt files."""

    def test_parse_simple_requirements(self):
        """Test parsing simple package names."""
        content = """requests
flask
numpy
"""
        mock_file = mock_open(read_data=content)

        with patch('builtins.open', mock_file):
            result = parse_requirements_txt(Path("requirements.txt"))

        self.assertEqual(sorted(result), ['flask', 'numpy', 'requests'])

    def test_parse_requirements_with_versions(self):
        """Test parsing packages with version specifiers."""
        content = """requests==2.28.1
flask>=2.0.0
numpy~=1.23.0
pandas<2.0,>=1.4
"""
        mock_file = mock_open(read_data=content)

        with patch('builtins.open', mock_file):
            result = parse_requirements_txt(Path("requirements.txt"))

        self.assertEqual(sorted(result), ['flask', 'numpy', 'pandas', 'requests'])

    def test_parse_requirements_with_comments(self):
        """Test parsing requirements with comments and blank lines."""
        content = """# Web framework
flask>=2.0.0

# Data processing
pandas>=1.4.0  # For data analysis
numpy  # Required by pandas
"""
        mock_file = mock_open(read_data=content)

        with patch('builtins.open', mock_file):
            result = parse_requirements_txt(Path("requirements.txt"))

        self.assertEqual(sorted(result), ['flask', 'numpy', 'pandas'])

    def test_parse_requirements_with_extras(self):
        """Test parsing packages with extras."""
        content = """requests[security]>=2.28.0
flask[async]==2.0.0
"""
        mock_file = mock_open(read_data=content)

        with patch('builtins.open', mock_file):
            result = parse_requirements_txt(Path("requirements.txt"))

        self.assertEqual(sorted(result), ['flask', 'requests'])

    def test_parse_requirements_with_env_markers(self):
        """Test parsing packages with environment markers."""
        content = """requests>=2.28.0; python_version>='3.7'
numpy; sys_platform == 'linux'
"""
        mock_file = mock_open(read_data=content)

        with patch('builtins.open', mock_file):
            result = parse_requirements_txt(Path("requirements.txt"))

        self.assertEqual(sorted(result), ['numpy', 'requests'])

    def test_parse_requirements_file_not_found(self):
        """Test handling of missing requirements.txt."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            result = parse_requirements_txt(Path("requirements.txt"))

        self.assertEqual(result, [])


class TestPyprojectTomlParsing(unittest.TestCase):
    """Test cases for parsing pyproject.toml files."""

    def test_parse_poetry_dependencies(self):
        """Test parsing Poetry-style dependencies."""
        content = '''
[tool.poetry.dependencies]
python = "^3.10"
requests = "^2.28.0"
flask = ">=2.0.0"
numpy = "1.23.0"
'''
        mock_file = mock_open(read_data=content)

        with patch('builtins.open', mock_file):
            result = parse_pyproject_toml(Path("pyproject.toml"))

        # Should not include 'python' itself
        self.assertIn('requests', result)
        self.assertIn('flask', result)
        self.assertIn('numpy', result)
        self.assertNotIn('python', result)

    def test_parse_pep621_dependencies(self):
        """Test parsing PEP 621 style dependencies."""
        content = '''
[project]
name = "myproject"
dependencies = [
    "requests>=2.28.0",
    "flask>=2.0.0",
    "numpy>=1.23.0",
]
'''
        mock_file = mock_open(read_data=content)

        with patch('builtins.open', mock_file):
            result = parse_pyproject_toml(Path("pyproject.toml"))

        self.assertIn('requests', result)
        self.assertIn('flask', result)
        self.assertIn('numpy', result)

    def test_parse_pyproject_file_not_found(self):
        """Test handling of missing pyproject.toml."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            result = parse_pyproject_toml(Path("pyproject.toml"))

        self.assertEqual(result, [])


class TestSetupPyParsing(unittest.TestCase):
    """Test cases for parsing setup.py files."""

    def test_parse_setup_py_install_requires(self):
        """Test parsing setup.py install_requires."""
        content = '''
from setuptools import setup

setup(
    name="myproject",
    install_requires=[
        "requests>=2.28.0",
        "flask>=2.0.0",
        "numpy",
    ],
)
'''
        mock_file = mock_open(read_data=content)

        with patch('builtins.open', mock_file):
            result = parse_setup_py(Path("setup.py"))

        self.assertIn('requests', result)
        self.assertIn('flask', result)
        self.assertIn('numpy', result)

    def test_parse_setup_py_multiline(self):
        """Test parsing setup.py with multiline install_requires."""
        content = '''
setup(
    name="myproject",
    install_requires=[
        "requests>=2.28.0",
        "flask>=2.0.0",
        "numpy",
        "pandas",
    ],
)
'''
        mock_file = mock_open(read_data=content)

        with patch('builtins.open', mock_file):
            result = parse_setup_py(Path("setup.py"))

        self.assertIn('requests', result)
        self.assertIn('pandas', result)


class TestPipfileParsing(unittest.TestCase):
    """Test cases for parsing Pipfile."""

    def test_parse_pipfile_packages(self):
        """Test parsing Pipfile packages section."""
        content = '''
[packages]
requests = "*"
flask = ">=2.0.0"
numpy = "==1.23.0"

[dev-packages]
pytest = "*"
'''
        mock_file = mock_open(read_data=content)

        with patch('builtins.open', mock_file):
            result = parse_pipfile(Path("Pipfile"))

        self.assertIn('requests', result)
        self.assertIn('flask', result)
        self.assertIn('numpy', result)
        # Should not include dev-packages
        self.assertNotIn('pytest', result)


class TestInstalledPackages(unittest.TestCase):
    """Test cases for getting installed packages."""

    @patch('harmonizer.utils.subprocess_utils.run_command_safe')
    def test_get_installed_packages_success(self, mock_run):
        """Test getting list of installed packages."""
        mock_run.return_value = (True, """requests==2.28.1
flask==2.0.3
numpy==1.23.5
""", "")

        result = get_installed_packages()

        self.assertIn('requests', result)
        self.assertIn('flask', result)
        self.assertIn('numpy', result)
        self.assertEqual(len(result), 3)

    @patch('harmonizer.utils.subprocess_utils.run_command_safe')
    def test_get_installed_packages_failure(self, mock_run):
        """Test handling of pip list failure."""
        mock_run.return_value = (False, "", "pip not found")

        result = get_installed_packages()

        # Should return empty list on failure
        self.assertEqual(result, [])

    @patch('harmonizer.utils.subprocess_utils.run_command_safe')
    def test_get_installed_packages_empty(self, mock_run):
        """Test with no packages installed."""
        mock_run.return_value = (True, "", "")

        result = get_installed_packages()

        self.assertEqual(result, [])


class TestMissingPackages(unittest.TestCase):
    """Test cases for finding missing packages."""

    def test_find_missing_packages_some_missing(self):
        """Test finding missing packages when some are not installed."""
        required = ['requests', 'flask', 'numpy', 'pandas']
        installed = ['requests', 'numpy']

        result = find_missing_packages(required, installed)

        self.assertEqual(sorted(result), ['flask', 'pandas'])

    def test_find_missing_packages_all_installed(self):
        """Test when all required packages are installed."""
        required = ['requests', 'flask']
        installed = ['requests', 'flask', 'numpy']

        result = find_missing_packages(required, installed)

        self.assertEqual(result, [])

    def test_find_missing_packages_none_installed(self):
        """Test when no required packages are installed."""
        required = ['requests', 'flask', 'numpy']
        installed = []

        result = find_missing_packages(required, installed)

        self.assertEqual(sorted(result), ['flask', 'numpy', 'requests'])

    def test_find_missing_packages_case_insensitive(self):
        """Test that package comparison is case-insensitive."""
        required = ['Requests', 'Flask', 'NumPy']
        installed = ['requests', 'flask', 'numpy']

        result = find_missing_packages(required, installed)

        self.assertEqual(result, [])


class TestPackageChecks(unittest.TestCase):
    """Test cases for individual package checks."""

    @patch('harmonizer.utils.subprocess_utils.run_command_safe')
    def test_check_package_installed_yes(self, mock_run):
        """Test checking if a package is installed (yes)."""
        mock_run.return_value = (True, "Name: requests\nVersion: 2.28.1\n", "")

        result = check_package_installed('requests')

        self.assertTrue(result)

    @patch('harmonizer.utils.subprocess_utils.run_command_safe')
    def test_check_package_installed_no(self, mock_run):
        """Test checking if a package is installed (no)."""
        mock_run.return_value = (False, "", "Package not found")

        result = check_package_installed('nonexistent-package')

        self.assertFalse(result)

    @patch('harmonizer.utils.subprocess_utils.run_command_safe')
    def test_get_package_version_found(self, mock_run):
        """Test getting version of installed package."""
        mock_run.return_value = (True, """Name: requests
Version: 2.28.1
Summary: HTTP library
""", "")

        result = get_package_version('requests')

        self.assertEqual(result, '2.28.1')

    @patch('harmonizer.utils.subprocess_utils.run_command_safe')
    def test_get_package_version_not_found(self, mock_run):
        """Test getting version of non-existent package."""
        mock_run.return_value = (False, "", "Package not found")

        result = get_package_version('nonexistent')

        self.assertIsNone(result)


class TestScanDependencies(unittest.TestCase):
    """Test cases for comprehensive dependency scanning."""

    @patch('harmonizer.detectors.dependency_detector.get_installed_packages')
    @patch('harmonizer.detectors.dependency_detector.parse_requirements_txt')
    @patch('pathlib.Path.exists')
    def test_scan_with_requirements_txt(self, mock_exists, mock_parse, mock_installed):
        """Test scanning with requirements.txt."""
        mock_exists.return_value = True
        mock_parse.return_value = ['requests', 'flask', 'numpy']
        mock_installed.return_value = ['requests', 'flask']

        result = scan_dependencies(".")

        self.assertIn('requirements.txt', result['requirements_file'])
        self.assertEqual(sorted(result['required_packages']), ['flask', 'numpy', 'requests'])
        self.assertEqual(sorted(result['missing_packages']), ['numpy'])

    @patch('harmonizer.detectors.dependency_detector.get_installed_packages')
    @patch('pathlib.Path.exists')
    def test_scan_no_requirements_file(self, mock_exists, mock_installed):
        """Test scanning when no requirements file exists."""
        mock_exists.return_value = False
        mock_installed.return_value = ['requests', 'flask']

        result = scan_dependencies(".")

        self.assertIsNone(result['requirements_file'])
        self.assertEqual(result['required_packages'], [])
        self.assertEqual(result['missing_packages'], [])


if __name__ == '__main__':
    unittest.main()
