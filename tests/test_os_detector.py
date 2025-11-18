"""
Unit tests for OS detection module.

This module tests the OS detection functionality including:
- Operating system type detection (Linux, WSL, Windows, macOS)
- OS version detection
- WSL-specific version detection
- Distribution information parsing
"""

import unittest
from unittest.mock import patch, mock_open, MagicMock
import platform

from harmonizer.detectors.os_detector import (
    detect_os_type,
    get_os_version,
    get_wsl_version,
    get_system_info,
    _get_linux_distribution,
)
from harmonizer.models import OSType


class TestOSDetection(unittest.TestCase):
    """Test cases for OS type detection."""

    @patch("platform.system")
    def test_detect_windows_native(self, mock_system):
        """Test detection of Windows native OS."""
        mock_system.return_value = "Windows"
        result = detect_os_type()
        self.assertEqual(result, OSType.WINDOWS_NATIVE)

    @patch("platform.system")
    def test_detect_macos(self, mock_system):
        """Test detection of macOS."""
        mock_system.return_value = "Darwin"
        result = detect_os_type()
        self.assertEqual(result, OSType.MACOS)

    @patch("platform.system")
    @patch("builtins.open", new_callable=mock_open, read_data="microsoft")
    def test_detect_wsl_from_proc_version(self, mock_file, mock_system):
        """Test WSL detection via /proc/version."""
        mock_system.return_value = "Linux"
        result = detect_os_type()
        self.assertEqual(result, OSType.WSL)

    @patch("platform.system")
    @patch("builtins.open", side_effect=FileNotFoundError)
    @patch.dict("os.environ", {"WSLENV": "PATH/l"})
    def test_detect_wsl_from_env_var(self, mock_file, mock_system):
        """Test WSL detection via environment variable."""
        mock_system.return_value = "Linux"
        result = detect_os_type()
        self.assertEqual(result, OSType.WSL)

    @patch("platform.system")
    @patch("builtins.open", side_effect=FileNotFoundError)
    @patch.dict("os.environ", {}, clear=True)
    def test_detect_native_linux(self, mock_file, mock_system):
        """Test detection of native Linux (not WSL)."""
        mock_system.return_value = "Linux"
        result = detect_os_type()
        self.assertEqual(result, OSType.LINUX)

    @patch("platform.system")
    def test_detect_unknown_os(self, mock_system):
        """Test detection of unknown/unsupported OS."""
        mock_system.return_value = "FreeBSD"
        result = detect_os_type()
        self.assertEqual(result, OSType.UNKNOWN)


class TestOSVersion(unittest.TestCase):
    """Test cases for OS version detection."""

    @patch("harmonizer.detectors.os_detector.detect_os_type")
    @patch("platform.system")
    @patch("platform.release")
    @patch("platform.version")
    def test_get_windows_version(self, mock_ver, mock_rel, mock_sys, mock_os_type):
        """Test getting Windows version string."""
        mock_os_type.return_value = OSType.WINDOWS_NATIVE
        mock_sys.return_value = "Windows"
        mock_rel.return_value = "10"
        mock_ver.return_value = "10.0.19041"

        result = get_os_version()
        self.assertIn("Windows", result)
        self.assertIn("10", result)

    @patch("harmonizer.detectors.os_detector.detect_os_type")
    @patch("platform.mac_ver")
    def test_get_macos_version(self, mock_mac_ver, mock_os_type):
        """Test getting macOS version string."""
        mock_os_type.return_value = OSType.MACOS
        mock_mac_ver.return_value = ("12.5.1", ("", "", ""), "x86_64")

        result = get_os_version()
        self.assertIn("macOS", result)
        self.assertIn("12.5.1", result)

    @patch("harmonizer.detectors.os_detector.detect_os_type")
    @patch("harmonizer.detectors.os_detector._get_linux_distribution")
    def test_get_linux_version(self, mock_distro, mock_os_type):
        """Test getting Linux version string."""
        mock_os_type.return_value = OSType.LINUX
        mock_distro.return_value = "Ubuntu 22.04.1 LTS"

        result = get_os_version()
        self.assertEqual(result, "Ubuntu 22.04.1 LTS")

    @patch("harmonizer.detectors.os_detector.detect_os_type")
    @patch("harmonizer.detectors.os_detector._get_linux_distribution")
    @patch("platform.system")
    @patch("platform.release")
    def test_get_linux_version_fallback(
        self, mock_rel, mock_sys, mock_distro, mock_os_type
    ):
        """Test Linux version fallback when distribution info unavailable."""
        mock_os_type.return_value = OSType.LINUX
        mock_distro.return_value = ""
        mock_sys.return_value = "Linux"
        mock_rel.return_value = "5.15.0-58-generic"

        result = get_os_version()
        self.assertIn("Linux", result)
        self.assertIn("5.15", result)


class TestLinuxDistribution(unittest.TestCase):
    """Test cases for Linux distribution detection."""

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="""
NAME="Ubuntu"
VERSION="22.04.1 LTS (Jammy Jellyfish)"
PRETTY_NAME="Ubuntu 22.04.1 LTS"
""",
    )
    def test_parse_os_release(self, mock_file):
        """Test parsing /etc/os-release file."""
        result = _get_linux_distribution()
        self.assertEqual(result, "Ubuntu 22.04.1 LTS")

    @patch(
        "builtins.open",
        side_effect=[
            FileNotFoundError,
            mock_open(
                read_data="""
DISTRIB_DESCRIPTION="Ubuntu 22.04.1 LTS"
"""
            ).return_value,
        ],
    )
    def test_parse_lsb_release_file(self, mock_file):
        """Test parsing /etc/lsb-release file."""
        result = _get_linux_distribution()
        self.assertEqual(result, "Ubuntu 22.04.1 LTS")

    @patch("builtins.open", side_effect=FileNotFoundError)
    @patch("harmonizer.utils.subprocess_utils.run_command_safe")
    def test_use_lsb_release_command(self, mock_run, mock_file):
        """Test using lsb_release command."""
        mock_run.return_value = (True, "Description:\tUbuntu 22.04.1 LTS\n", "")

        result = _get_linux_distribution()
        self.assertEqual(result, "Ubuntu 22.04.1 LTS")

    @patch("builtins.open", side_effect=FileNotFoundError)
    @patch("harmonizer.utils.subprocess_utils.run_command_safe")
    def test_no_distribution_info(self, mock_run, mock_file):
        """Test when no distribution information is available."""
        mock_run.return_value = (False, "", "Command not found")

        result = _get_linux_distribution()
        self.assertEqual(result, "")


class TestWSLVersion(unittest.TestCase):
    """Test cases for WSL version detection."""

    @patch("harmonizer.detectors.os_detector.detect_os_type")
    def test_not_wsl(self, mock_os_type):
        """Test WSL version detection when not on WSL."""
        mock_os_type.return_value = OSType.LINUX

        result = get_wsl_version()
        self.assertEqual(result, "Not WSL")

    @patch("harmonizer.detectors.os_detector.detect_os_type")
    @patch("builtins.open", new_callable=mock_open, read_data="microsoft-standard-WSL2")
    def test_detect_wsl2(self, mock_file, mock_os_type):
        """Test detection of WSL 2."""
        mock_os_type.return_value = OSType.WSL

        result = get_wsl_version()
        self.assertEqual(result, "WSL 2")

    @patch("harmonizer.detectors.os_detector.detect_os_type")
    @patch("builtins.open", new_callable=mock_open, read_data="microsoft-WSL")
    def test_detect_wsl1(self, mock_file, mock_os_type):
        """Test detection of WSL 1."""
        mock_os_type.return_value = OSType.WSL

        result = get_wsl_version()
        self.assertEqual(result, "WSL 1")

    @patch("harmonizer.detectors.os_detector.detect_os_type")
    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_unknown_wsl_version(self, mock_file, mock_os_type):
        """Test when WSL version cannot be determined."""
        mock_os_type.return_value = OSType.WSL

        result = get_wsl_version()
        self.assertEqual(result, "Unknown WSL version")


class TestSystemInfo(unittest.TestCase):
    """Test cases for combined system info retrieval."""

    @patch("harmonizer.detectors.os_detector.detect_os_type")
    @patch("harmonizer.detectors.os_detector.get_os_version")
    def test_get_system_info(self, mock_version, mock_os_type):
        """Test getting combined OS type and version."""
        mock_os_type.return_value = OSType.LINUX
        mock_version.return_value = "Ubuntu 22.04.1 LTS"

        os_type, os_version = get_system_info()

        self.assertEqual(os_type, OSType.LINUX)
        self.assertEqual(os_version, "Ubuntu 22.04.1 LTS")


if __name__ == "__main__":
    unittest.main()
