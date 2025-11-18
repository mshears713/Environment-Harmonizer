"""
Operating System Detection Module.

This module provides functionality to detect the operating system type and version,
with special handling for Windows Subsystem for Linux (WSL) environments.

EDUCATIONAL NOTE - Why OS Detection Matters:
Different operating systems have different behaviors that affect development:
- File path separators (/ vs \)
- Line endings (LF vs CRLF)
- Case sensitivity in filesystems
- Available system commands
- Environment variable conventions

WSL is particularly important to detect separately because it:
- Reports as Linux but has Windows interoperability features
- Can access both Linux and Windows filesystems
- May have different PATH configurations than native Linux
- Has unique behaviors around file permissions and executables
"""

import platform
import os
import subprocess
from typing import Tuple

from harmonizer.models import OSType


def detect_os_type() -> OSType:
    """
    Detect the operating system type with special WSL detection.

    This function uses multiple detection methods to accurately identify
    the operating system, with special care to distinguish WSL from native Linux.

    DETECTION STRATEGY:
    1. Use platform.system() for basic OS identification
    2. For Linux systems, check for WSL-specific markers:
       - /proc/version file containing "microsoft" (WSL kernel signature)
       - /proc/sys/kernel/osrelease containing "WSL"
       - WSLENV environment variable (set by WSL runtime)
    3. Return appropriate OSType enum value

    Returns:
        OSType: Detected operating system type

    EDUCATIONAL NOTE - Multiple Detection Methods:
    We use multiple detection methods because:
    1. /proc/version is the most reliable for WSL 1 & 2
    2. WSLENV environment variable provides quick detection
    3. Fallback methods ensure we catch edge cases
    4. Different WSL versions have different signatures

    Example:
        >>> os_type = detect_os_type()
        >>> print(f"Running on: {os_type.value}")
        Running on: wsl

    GOTCHAS:
    - /proc/version might not exist on all Linux systems
    - Users can unset WSLENV, making that check unreliable alone
    - WSL 1 and WSL 2 have slightly different kernel signatures
    - Docker containers on WSL might need special handling
    """

    system = platform.system()

    # WSL Detection (when platform reports Linux)
    if system == "Linux":
        # Method 1: Check /proc/version for Microsoft signature
        # This is the most reliable method for both WSL 1 and WSL 2
        try:
            with open("/proc/version", "r") as f:
                proc_version = f.read().lower()
                if "microsoft" in proc_version or "wsl" in proc_version:
                    return OSType.WSL
        except (FileNotFoundError, PermissionError):
            # /proc/version doesn't exist or can't be read
            # This is normal on some Linux systems, continue with other checks
            pass

        # Method 2: Check /proc/sys/kernel/osrelease for WSL marker
        try:
            with open("/proc/sys/kernel/osrelease", "r") as f:
                osrelease = f.read().lower()
                if "wsl" in osrelease or "microsoft" in osrelease:
                    return OSType.WSL
        except (FileNotFoundError, PermissionError):
            pass

        # Method 3: Check for WSLENV environment variable
        # This is set by the WSL runtime
        if "WSLENV" in os.environ or "WSL_DISTRO_NAME" in os.environ:
            return OSType.WSL

        # If none of the WSL markers found, it's native Linux
        return OSType.LINUX

    # Windows Native Detection
    elif system == "Windows":
        return OSType.WINDOWS_NATIVE

    # macOS Detection
    elif system == "Darwin":
        return OSType.MACOS

    # Unknown OS
    else:
        return OSType.UNKNOWN


def get_os_version() -> str:
    """
    Get the operating system version string.

    This function retrieves detailed version information about the OS,
    formatted in a human-readable way.

    Returns:
        str: OS version string (e.g., "Ubuntu 22.04.1 LTS", "Windows 10")

    EDUCATIONAL NOTE - Platform Module:
    Python's platform module provides cross-platform access to system information.
    Different methods are needed for different operating systems because they
    store version information differently.

    Example:
        >>> version = get_os_version()
        >>> print(f"OS Version: {version}")
        OS Version: Ubuntu 22.04.1 LTS

    GOTCHAS:
    - platform.version() returns different formats on different OSes
    - Linux distributions have various ways to report version
    - WSL reports the distribution version, not Windows version
    """

    os_type = detect_os_type()

    if os_type == OSType.WINDOWS_NATIVE:
        # Windows version detection
        # platform.version() gives build number, platform.release() gives version name
        return f"{platform.system()} {platform.release()} (Build {platform.version()})"

    elif os_type in (OSType.LINUX, OSType.WSL):
        # Linux/WSL version detection
        # Try to get distribution information from various sources
        version_info = _get_linux_distribution()

        if version_info:
            return version_info

        # Fallback to platform information
        return f"{platform.system()} {platform.release()}"

    elif os_type == OSType.MACOS:
        # macOS version detection
        return f"macOS {platform.mac_ver()[0]}"

    else:
        # Unknown OS - return basic platform info
        return f"{platform.system()} {platform.release()}"


def _get_linux_distribution() -> str:
    """
    Get Linux distribution name and version.

    This is an internal helper function that attempts to read distribution
    information from various standard locations in Linux systems.

    Returns:
        str: Distribution info (e.g., "Ubuntu 22.04.1 LTS") or empty string

    EDUCATIONAL NOTE - Linux Distribution Detection:
    Linux distributions store version info in different files:
    - /etc/os-release: Modern standard (systemd-based systems)
    - /etc/lsb-release: LSB (Linux Standard Base) systems
    - /etc/issue: Older fallback method

    We try these in order of reliability and detail.

    IMPLEMENTATION NOTE - Private Functions:
    The leading underscore (_) indicates this is an internal function
    not meant to be imported or used outside this module. This is a
    Python naming convention for private/internal functionality.
    """

    # Try /etc/os-release (modern standard)
    try:
        with open("/etc/os-release", "r") as f:
            lines = f.readlines()
            distro_info = {}

            for line in lines:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    # Remove quotes from value
                    distro_info[key] = value.strip('"')

            # Build version string from available information
            name = distro_info.get("PRETTY_NAME") or distro_info.get("NAME", "")
            if name:
                return name

            # Fallback: construct from NAME and VERSION
            version = distro_info.get("VERSION", "")
            if version:
                return f"{distro_info.get('NAME', 'Linux')} {version}"

    except (FileNotFoundError, PermissionError, ValueError):
        pass

    # Try /etc/lsb-release (LSB systems)
    try:
        with open("/etc/lsb-release", "r") as f:
            lines = f.readlines()
            lsb_info = {}

            for line in lines:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    lsb_info[key] = value.strip('"')

            description = lsb_info.get("DISTRIB_DESCRIPTION", "")
            if description:
                return description

    except (FileNotFoundError, PermissionError, ValueError):
        pass

    # Try using lsb_release command if available
    try:
        result = subprocess.run(
            ["lsb_release", "-d"],
            capture_output=True,
            text=True,
            timeout=2,
        )

        if result.returncode == 0:
            # Output format: "Description:\tUbuntu 22.04.1 LTS"
            output = result.stdout.strip()
            if ":" in output:
                return output.split(":", 1)[1].strip()

    except (subprocess.SubprocessError, FileNotFoundError):
        # lsb_release not available
        pass

    # No distribution information found
    return ""


def get_wsl_version() -> str:
    """
    Detect WSL version (WSL 1 or WSL 2).

    Returns:
        str: "WSL 1", "WSL 2", or "Unknown" if not WSL

    EDUCATIONAL NOTE - WSL 1 vs WSL 2:
    WSL 1: Translation layer, no actual Linux kernel, faster filesystem I/O for Windows files
    WSL 2: Real Linux kernel in lightweight VM, better Linux compatibility, slower Windows file access

    Detection method:
    - WSL 2: /proc/version contains "microsoft-standard" or higher kernel version
    - WSL 1: /proc/version contains "microsoft" but not "microsoft-standard"
    """

    os_type = detect_os_type()

    if os_type != OSType.WSL:
        return "Not WSL"

    try:
        with open("/proc/version", "r") as f:
            proc_version = f.read().lower()

            # WSL 2 has "microsoft-standard" in kernel version
            if "microsoft-standard" in proc_version:
                return "WSL 2"

            # WSL 1 has "microsoft" but not "microsoft-standard"
            if "microsoft" in proc_version:
                return "WSL 1"

    except (FileNotFoundError, PermissionError):
        pass

    return "Unknown WSL version"


def get_system_info() -> Tuple[OSType, str]:
    """
    Get both OS type and version in a single call.

    This is a convenience function that combines detect_os_type()
    and get_os_version() into a single call.

    Returns:
        Tuple[OSType, str]: (os_type, os_version)

    Example:
        >>> os_type, os_version = get_system_info()
        >>> print(f"{os_type.value}: {os_version}")
        wsl: Ubuntu 22.04.1 LTS
    """
    return detect_os_type(), get_os_version()


# Example usage and testing (only runs when module executed directly)
if __name__ == "__main__":
    """
    EDUCATIONAL NOTE - __name__ == "__main__":
    This block only runs when the script is executed directly,
    not when it's imported as a module. This is useful for:
    - Testing individual modules during development
    - Providing usage examples
    - Creating command-line utilities from library code
    """

    print("=" * 60)
    print("OS Detection Module - Test Run")
    print("=" * 60)

    os_type = detect_os_type()
    os_version = get_os_version()

    print(f"\nOS Type: {os_type.value}")
    print(f"OS Version: {os_version}")

    if os_type == OSType.WSL:
        wsl_version = get_wsl_version()
        print(f"WSL Version: {wsl_version}")

    print(f"\nPlatform Details:")
    print(f"  System: {platform.system()}")
    print(f"  Release: {platform.release()}")
    print(f"  Version: {platform.version()}")
    print(f"  Machine: {platform.machine()}")
    print(f"  Processor: {platform.processor()}")

    print("\n" + "=" * 60)
