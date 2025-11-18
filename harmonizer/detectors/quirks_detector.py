"""
Platform Quirks Detection Module.

This module detects platform-specific quirks and issues, particularly
focusing on WSL (Windows Subsystem for Linux) vs Windows Native differences.

EDUCATIONAL NOTE - Why Platform Quirks Matter:
Different platforms have subtle behavioral differences that can cause issues:
- File path separators (/ vs \)
- Line ending conventions (LF vs CRLF)
- Case sensitivity (Linux is case-sensitive, Windows is not)
- File permissions and executable bits
- PATH environment variable handling
- Symbolic link support

WSL is particularly tricky because it's Linux running on Windows:
- Can access both Windows (/mnt/c/) and Linux filesystems
- Different performance characteristics for each
- Mixed line endings can cause git issues
- PATH pollution from Windows programs
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from harmonizer.models import OSType, Issue, IssueSeverity
from harmonizer.detectors.os_detector import detect_os_type
from harmonizer.utils.subprocess_utils import run_command_safe


def detect_platform_quirks(project_path: str, os_type: OSType) -> List[Issue]:
    """
    Detect platform-specific quirks and potential issues.

    Args:
        project_path: Path to the project directory
        os_type: Detected operating system type

    Returns:
        List of Issue objects describing platform quirks

    EDUCATIONAL NOTE - Quirk Detection Strategy:
    We check for common platform-specific issues:
    1. WSL-specific quirks (if on WSL)
    2. Windows-specific quirks (if on Windows)
    3. Path-related issues
    4. Line ending issues
    5. Permission issues
    6. Cross-platform compatibility issues

    Example:
        >>> issues = detect_platform_quirks("/path/to/project", OSType.WSL)
        >>> for issue in issues:
        ...     print(f"{issue.severity.value}: {issue.message}")
    """

    issues = []

    if os_type == OSType.WSL:
        issues.extend(_detect_wsl_quirks(project_path))
    elif os_type == OSType.WINDOWS_NATIVE:
        issues.extend(_detect_windows_quirks(project_path))
    elif os_type == OSType.LINUX:
        issues.extend(_detect_linux_quirks(project_path))

    # Common cross-platform checks
    issues.extend(_detect_path_quirks(project_path, os_type))

    return issues


def _detect_wsl_quirks(project_path: str) -> List[Issue]:
    """
    Detect WSL-specific quirks and issues.

    Returns:
        List of Issue objects

    EDUCATIONAL NOTE - Common WSL Issues:
    1. Project on Windows filesystem (/mnt/c/) - slower I/O
    2. Line ending issues (git autocrlf)
    3. PATH pollution from Windows programs
    4. File permission issues
    5. Mixed case sensitivity
    """

    issues = []
    project = Path(project_path).resolve()

    # Check if project is on Windows filesystem (/mnt/c/, /mnt/d/, etc.)
    if str(project).startswith("/mnt/"):
        drive_letter = str(project).split("/")[2]
        issues.append(
            Issue(
                severity=IssueSeverity.WARNING,
                category="wsl_performance",
                message=f"Project is on Windows filesystem (/mnt/{drive_letter}/) - "
                        "Consider moving to Linux filesystem for better performance",
                fixable=False,
                fix_command=None,
            )
        )

        # Additional note about file operations
        issues.append(
            Issue(
                severity=IssueSeverity.INFO,
                category="wsl_performance",
                message="File I/O operations are significantly slower on Windows filesystem from WSL. "
                        "Git operations, npm/pip installs, and file watches may be slow.",
                fixable=False,
            )
        )

    # Check for Windows path separators in Python files
    windows_path_issue = _check_for_windows_paths(project)
    if windows_path_issue:
        issues.append(windows_path_issue)

    # Check git line ending configuration
    git_crlf_issue = _check_git_line_endings(project)
    if git_crlf_issue:
        issues.append(git_crlf_issue)

    # Check for PATH pollution
    path_pollution_issue = _check_wsl_path_pollution()
    if path_pollution_issue:
        issues.append(path_pollution_issue)

    # Check for WSL interop issues
    interop_issue = _check_wsl_interop()
    if interop_issue:
        issues.append(interop_issue)

    return issues


def _detect_windows_quirks(project_path: str) -> List[Issue]:
    """
    Detect Windows-specific quirks and issues.

    Returns:
        List of Issue objects

    EDUCATIONAL NOTE - Common Windows Issues:
    1. Long path limitations (MAX_PATH = 260 characters)
    2. Case-insensitive filesystem
    3. Reserved filenames (CON, PRN, AUX, etc.)
    4. Backslash path separators
    5. Different executable extensions (.exe, .bat, .cmd)
    """

    issues = []
    project = Path(project_path).resolve()

    # Check for long paths (Windows MAX_PATH limitation)
    if len(str(project)) > 200:  # Warn at 200, limit is usually 260
        issues.append(
            Issue(
                severity=IssueSeverity.WARNING,
                category="windows_path",
                message=f"Project path is long ({len(str(project))} characters) - "
                        "Windows has a 260 character limit. Enable long path support in registry.",
                fixable=False,
            )
        )

    # Check for Unix-style paths in code (common mistake on Windows)
    unix_path_issue = _check_for_unix_paths(project)
    if unix_path_issue:
        issues.append(unix_path_issue)

    # Check for case sensitivity issues
    case_issue = _check_case_sensitivity_issues(project)
    if case_issue:
        issues.append(case_issue)

    return issues


def _detect_linux_quirks(project_path: str) -> List[Issue]:
    """
    Detect Linux-specific quirks and issues.

    Returns:
        List of Issue objects
    """

    issues = []

    # Check for Windows-specific files that won't work on Linux
    windows_files = [".bat", ".cmd", ".ps1"]
    project = Path(project_path)

    found_windows_files = []
    for pattern in windows_files:
        found = list(project.glob(f"**/*{pattern}"))
        if found:
            found_windows_files.extend([f.name for f in found])

    if found_windows_files:
        issues.append(
            Issue(
                severity=IssueSeverity.INFO,
                category="cross_platform",
                message=f"Found Windows-specific files: {', '.join(found_windows_files[:5])}. "
                        "These won't execute on Linux.",
                fixable=False,
            )
        )

    return issues


def _detect_path_quirks(project_path: str, os_type: OSType) -> List[Issue]:
    """
    Detect path-related quirks across platforms.

    Returns:
        List of Issue objects
    """

    issues = []
    project = Path(project_path)

    # Check for spaces in project path
    if " " in str(project):
        issues.append(
            Issue(
                severity=IssueSeverity.INFO,
                category="path",
                message="Project path contains spaces - some tools may have issues. "
                        "Consider using underscores or hyphens instead.",
                fixable=False,
            )
        )

    # Check for non-ASCII characters in path
    try:
        str(project).encode("ascii")
    except UnicodeEncodeError:
        issues.append(
            Issue(
                severity=IssueSeverity.WARNING,
                category="path",
                message="Project path contains non-ASCII characters - "
                        "may cause issues with some tools.",
                fixable=False,
            )
        )

    return issues


def _check_for_windows_paths(project_path: Path) -> Optional[Issue]:
    """
    Check for Windows-style path separators in Python files.

    This is a common issue when developing on Windows then deploying to Linux.
    """

    # Look for backslash path separators in Python files
    python_files = list(project_path.glob("**/*.py"))

    files_with_backslashes = []
    for py_file in python_files[:50]:  # Check first 50 files
        try:
            content = py_file.read_text(encoding="utf-8")
            # Look for patterns like "C:\\" or "path\\to\\file"
            if "\\\\" in content or (": \\" in content and "C:" in content):
                files_with_backslashes.append(py_file.name)
        except (UnicodeDecodeError, PermissionError):
            continue

    if files_with_backslashes:
        return Issue(
            severity=IssueSeverity.WARNING,
            category="cross_platform",
            message=f"Found Windows path separators (backslashes) in Python files: "
                    f"{', '.join(files_with_backslashes[:3])}. "
                    f"Use pathlib.Path or forward slashes for cross-platform compatibility.",
            fixable=False,
        )

    return None


def _check_for_unix_paths(project_path: Path) -> Optional[Issue]:
    """
    Check for Unix-style paths hardcoded in files (issue on Windows).
    """

    python_files = list(project_path.glob("**/*.py"))

    files_with_unix_paths = []
    for py_file in python_files[:50]:  # Check first 50 files
        try:
            content = py_file.read_text(encoding="utf-8")
            # Look for patterns like "/home/" or "/usr/"
            if '"/home/' in content or '"/usr/' in content or '"/var/' in content:
                files_with_unix_paths.append(py_file.name)
        except (UnicodeDecodeError, PermissionError):
            continue

    if files_with_unix_paths:
        return Issue(
            severity=IssueSeverity.INFO,
            category="cross_platform",
            message=f"Found Unix-style paths in Python files: "
                    f"{', '.join(files_with_unix_paths[:3])}. "
                    f"Use pathlib.Path for cross-platform compatibility.",
            fixable=False,
        )

    return None


def _check_git_line_endings(project_path: Path) -> Optional[Issue]:
    """
    Check git autocrlf configuration for line endings.

    EDUCATIONAL NOTE - Git Line Endings:
    - core.autocrlf=true: Convert LF to CRLF on checkout (Windows)
    - core.autocrlf=input: Convert CRLF to LF on commit (Linux/Mac)
    - core.autocrlf=false: No conversion

    In WSL, autocrlf=true can cause issues because WSL is Linux-based
    and expects LF line endings.
    """

    git_dir = project_path / ".git"
    if not git_dir.exists():
        return None  # Not a git repository

    # Note: run_command_safe doesn't support cwd parameter, so we need to use a workaround
    import os
    old_cwd = os.getcwd()
    try:
        os.chdir(str(project_path))
        success, stdout, _ = run_command_safe(
            ["git", "config", "--get", "core.autocrlf"],
            timeout=2
        )

        if success:
            autocrlf_value = stdout.strip().lower()

            if autocrlf_value == "true":
                return Issue(
                    severity=IssueSeverity.WARNING,
                    category="git_config",
                    message="git core.autocrlf is set to 'true' in WSL - "
                            "this can cause line ending issues. "
                            "Recommended: 'input' or 'false' for WSL.",
                    fixable=True,
                    fix_command="git config --global core.autocrlf input",
                )
    finally:
        os.chdir(old_cwd)

    return None


def analyze_path_env() -> Dict[str, any]:
    """
    Analyze the PATH environment variable in detail.

    Returns:
        Dictionary with PATH analysis including:
        - total_entries: Number of PATH entries
        - linux_paths: List of Linux paths
        - windows_paths: List of Windows paths
        - duplicates: List of duplicate entries
        - non_existent: List of paths that don't exist
        - windows_executables_found: List of Windows .exe in PATH

    EDUCATIONAL NOTE - PATH Environment Variable:
    PATH tells the shell where to look for executables. In WSL:
    - Linux paths: /usr/bin, /usr/local/bin, etc.
    - Windows paths: /mnt/c/Windows, /mnt/c/Program Files, etc.

    Order matters! First match wins, so:
    - /usr/bin/python before /mnt/c/Python/python.exe → uses Linux Python
    - /mnt/c/Python before /usr/bin → uses Windows Python (BAD in WSL!)
    """

    path = os.environ.get("PATH", "")
    entries = path.split(":")

    linux_paths = []
    windows_paths = []
    duplicates = []
    non_existent = []
    seen = set()

    for entry in entries:
        # Check for duplicates
        if entry in seen:
            duplicates.append(entry)
        else:
            seen.add(entry)

        # Classify as Linux or Windows path
        if entry.startswith("/mnt/"):
            windows_paths.append(entry)
        else:
            linux_paths.append(entry)

        # Check if path exists
        if not Path(entry).exists():
            non_existent.append(entry)

    # Find common Windows executables in PATH
    windows_executables = []
    for wp in windows_paths[:10]:  # Check first 10 Windows paths
        wp_path = Path(wp)
        if wp_path.exists():
            exe_files = list(wp_path.glob("*.exe"))
            for exe in exe_files[:5]:  # First 5 exe files
                windows_executables.append(f"{exe.name} in {wp}")

    return {
        "total_entries": len(entries),
        "linux_paths": linux_paths,
        "windows_paths": windows_paths,
        "duplicates": duplicates,
        "non_existent": non_existent,
        "windows_executables_found": windows_executables[:10],
        "linux_first": len(linux_paths) > 0 and (not windows_paths or linux_paths[0] < windows_paths[0] if windows_paths else True),
    }


def _check_wsl_path_pollution() -> Optional[Issue]:
    """
    Check if Windows programs are polluting the WSL PATH.

    EDUCATIONAL NOTE - WSL PATH Pollution:
    By default, WSL adds Windows PATH to Linux PATH, which means:
    - Windows executables are accessible from WSL
    - Can cause confusion (which python? Windows or Linux?)
    - Can slow down command resolution
    - May cause "command not found" after running

    You can disable this with /etc/wsl.conf:
    [interop]
    appendWindowsPath = false
    """

    path_analysis = analyze_path_env()

    windows_paths = path_analysis["windows_paths"]
    total_entries = path_analysis["total_entries"]

    if len(windows_paths) > 5:
        windows_percentage = (len(windows_paths) / total_entries * 100) if total_entries > 0 else 0

        details = f"WSL PATH contains {len(windows_paths)} Windows paths " \
                  f"({windows_percentage:.1f}% of {total_entries} total entries)"

        # Check if Windows paths come before Linux paths (problematic)
        if windows_paths and path_analysis["linux_paths"]:
            first_windows_idx = next((i for i, p in enumerate(os.environ.get("PATH", "").split(":")) if p.startswith("/mnt/")), None)
            first_linux_idx = next((i for i, p in enumerate(os.environ.get("PATH", "").split(":")) if not p.startswith("/mnt/")), None)

            if first_windows_idx is not None and first_linux_idx is not None and first_windows_idx < first_linux_idx:
                details += ". WARNING: Windows paths appear BEFORE Linux paths - may use Windows executables instead of Linux!"

        return Issue(
            severity=IssueSeverity.INFO,
            category="wsl_path",
            message=f"{details}. Consider disabling Windows PATH in /etc/wsl.conf for cleaner environment",
            fixable=False,
        )

    return None


def _check_wsl_interop() -> Optional[Issue]:
    """
    Check WSL interop settings that may affect development.
    """

    # Check if Windows interop is enabled
    wslenv = os.environ.get("WSLENV", "")

    # If WSLENV is set, interop is enabled
    if wslenv:
        return Issue(
            severity=IssueSeverity.INFO,
            category="wsl_interop",
            message="WSL interop is enabled - Windows programs can be called from Linux. "
                    "Be aware of which environment your commands run in.",
            fixable=False,
        )

    return None


def _check_case_sensitivity_issues(project_path: Path) -> Optional[Issue]:
    """
    Check for potential case sensitivity issues.

    Windows is case-insensitive but preserves case.
    Linux is case-sensitive.

    This can cause issues when:
    - File.py and file.py exist (okay on Windows, same file on Linux)
    - Imports use different case than filename
    """

    # Check if there are files that differ only in case
    files_by_lower = {}
    all_files = list(project_path.glob("**/*"))

    case_conflicts = []

    for file in all_files:
        if file.is_file():
            lower_name = file.name.lower()
            if lower_name in files_by_lower:
                # Found a potential conflict
                if files_by_lower[lower_name].name != file.name:
                    case_conflicts.append(
                        (files_by_lower[lower_name].name, file.name)
                    )
            else:
                files_by_lower[lower_name] = file

    if case_conflicts:
        conflict_examples = [f"{a} vs {b}" for a, b in case_conflicts[:3]]
        return Issue(
            severity=IssueSeverity.WARNING,
            category="cross_platform",
            message=f"Found files that differ only in case: {', '.join(conflict_examples)}. "
                    "This will cause issues on case-sensitive filesystems (Linux/Mac).",
            fixable=False,
        )

    return None


def get_platform_recommendations(os_type: OSType) -> List[str]:
    """
    Get platform-specific development recommendations.

    Args:
        os_type: Detected operating system type

    Returns:
        List of recommendation strings

    EDUCATIONAL NOTE - Platform Best Practices:
    Different platforms have different best practices for development:
    - WSL: Keep projects on Linux filesystem, use Linux tools
    - Windows: Enable long paths, use pathlib for paths
    - Linux: Be aware of case sensitivity
    - All: Use .gitattributes for line endings
    """

    recommendations = []

    if os_type == OSType.WSL:
        recommendations.extend([
            "Keep project files on Linux filesystem (~/projects) not Windows (/mnt/c/)",
            "Use Linux versions of tools (node, python) not Windows versions",
            "Configure git: core.autocrlf=input for proper line endings",
            "Consider disabling Windows PATH in /etc/wsl.conf for cleaner environment",
        ])
    elif os_type == OSType.WINDOWS_NATIVE:
        recommendations.extend([
            "Use pathlib.Path for cross-platform file paths",
            "Enable long path support in Windows registry or Group Policy",
            "Use forward slashes (/) even on Windows for compatibility",
            "Configure git: core.autocrlf=true for Windows line endings",
        ])
    elif os_type == OSType.LINUX:
        recommendations.extend([
            "Be aware of case sensitivity - File.py != file.py",
            "Use .gitattributes to enforce line endings for cross-platform projects",
            "Make shell scripts executable with chmod +x",
        ])

    # Universal recommendations
    recommendations.extend([
        "Use .editorconfig to enforce consistent code style",
        "Add .gitattributes for line ending consistency",
        "Test on multiple platforms if project is cross-platform",
    ])

    return recommendations


# Example usage and testing
if __name__ == "__main__":
    """
    Test the platform quirks detection module.
    """

    print("=" * 60)
    print("Platform Quirks Detection Module - Test Run")
    print("=" * 60)

    os_type = detect_os_type()
    print(f"\nDetected OS: {os_type.value}")

    # Detect quirks in current directory
    issues = detect_platform_quirks(".", os_type)

    if issues:
        print(f"\nDetected Platform Issues: {len(issues)}")
        for issue in issues:
            print(f"\n[{issue.severity.value.upper()}] {issue.category}")
            print(f"  {issue.message}")
            if issue.fixable and issue.fix_command:
                print(f"  Fix: {issue.fix_command}")
    else:
        print("\n✓ No platform-specific issues detected")

    # Show recommendations
    recommendations = get_platform_recommendations(os_type)
    print(f"\nPlatform-Specific Recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")

    print("\n" + "=" * 60)
