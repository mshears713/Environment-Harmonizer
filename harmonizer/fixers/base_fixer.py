"""
Base Fixer Module.

This module provides the base class for all automated fix modules,
including dry-run support, user confirmation, and safe fix application.

EDUCATIONAL NOTE - Safe Automation Principles:
When building tools that modify the user's environment, safety is paramount:

1. DRY-RUN FIRST: Always allow users to preview changes before applying
2. EXPLICIT CONSENT: Ask for confirmation before making changes
3. REVERSIBILITY: Provide undo capability or backup when possible
4. MINIMAL SCOPE: Only fix what was explicitly detected as an issue
5. CLEAR FEEDBACK: Inform users what was changed and why
6. ERROR HANDLING: Gracefully handle failures without leaving system in bad state

Bad automation that doesn't follow these principles can:
- Break working environments
- Delete important files or configurations
- Install unwanted packages
- Create difficult-to-debug issues

Good automation should make users feel in control, not anxious.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import subprocess
import sys

from harmonizer.models import EnvironmentStatus, Issue, IssueSeverity
from harmonizer.utils.subprocess_utils import run_command_safe


class FixResult:
    """
    Result of a fix operation.

    Attributes:
        success: Whether the fix was successful
        message: Human-readable description of what happened
        command: The command that was executed (if any)
        dry_run: Whether this was a dry-run (no actual changes)
    """

    def __init__(
        self,
        success: bool,
        message: str,
        command: Optional[str] = None,
        dry_run: bool = False,
    ):
        self.success = success
        self.message = message
        self.command = command
        self.dry_run = dry_run

    def __repr__(self) -> str:
        status = (
            "DRY-RUN" if self.dry_run else ("SUCCESS" if self.success else "FAILED")
        )
        return f"FixResult({status}: {self.message})"


class BaseFixer(ABC):
    """
    Abstract base class for all fixer modules.

    This class provides the framework for implementing automated fixes
    with dry-run support, user confirmation, and safe execution.

    EDUCATIONAL NOTE - Abstract Base Classes (ABC):
    Abstract base classes define a contract that subclasses must implement.
    They're useful for:
    1. Enforcing consistent interfaces across related classes
    2. Preventing instantiation of incomplete classes
    3. Providing shared functionality in base methods
    4. Self-documenting code (shows what methods are required)

    Usage:
        class MyFixer(BaseFixer):
            def can_fix(self, env_status):
                return True  # Implement logic

            def _apply_fix_impl(self, env_status, dry_run):
                # Implement actual fix
                return FixResult(success=True, message="Fixed!")

    Attributes:
        env_status: EnvironmentStatus object containing scan results
        verbose: Whether to output detailed information
        auto_yes: Whether to skip confirmation prompts
    """

    def __init__(
        self,
        env_status: EnvironmentStatus,
        verbose: bool = False,
        auto_yes: bool = False,
    ):
        """
        Initialize the fixer.

        Args:
            env_status: Environment status from scanning
            verbose: Enable verbose output
            auto_yes: Automatically answer yes to prompts
        """
        self.env_status = env_status
        self.verbose = verbose
        self.auto_yes = auto_yes

    @abstractmethod
    def can_fix(self) -> bool:
        """
        Determine if this fixer can fix issues in the current environment.

        Returns:
            True if this fixer has applicable fixes, False otherwise

        EDUCATIONAL NOTE - Abstract Methods:
        Abstract methods MUST be implemented by subclasses. This ensures
        every fixer explicitly states whether it can fix anything.

        Implementation should check env_status for relevant issues.
        """
        pass

    @abstractmethod
    def _apply_fix_impl(self, dry_run: bool = False) -> List[FixResult]:
        """
        Internal method to apply fixes. Must be implemented by subclasses.

        Args:
            dry_run: If True, don't make actual changes (preview only)

        Returns:
            List of FixResult objects describing what was done

        EDUCATIONAL NOTE - Implementation Methods:
        We use _apply_fix_impl (with underscore prefix) as the internal
        implementation, while apply_fixes() is the public interface.
        This separation allows the base class to handle common concerns
        (confirmation, error handling) while subclasses focus on the
        specific fix logic.
        """
        pass

    def apply_fixes(self, dry_run: bool = False) -> List[FixResult]:
        """
        Apply all applicable fixes.

        This is the main public method for applying fixes. It handles:
        1. Checking if fixes are applicable
        2. User confirmation (if not auto_yes)
        3. Calling the implementation
        4. Error handling

        Args:
            dry_run: If True, preview changes without applying them

        Returns:
            List of FixResult objects

        EDUCATIONAL NOTE - Template Method Pattern:
        This method implements the "template method" design pattern:
        - The base class defines the overall algorithm (check, confirm, apply)
        - Subclasses fill in specific steps (can_fix, _apply_fix_impl)
        - Common logic is reused, specific logic is customized
        """

        # Check if this fixer can fix anything
        if not self.can_fix():
            return [
                FixResult(
                    success=False,
                    message=f"{self.__class__.__name__}: No applicable fixes",
                    dry_run=dry_run,
                )
            ]

        # Get user confirmation if not auto_yes and not dry_run
        if not dry_run and not self.auto_yes:
            if not self._confirm_fixes():
                return [
                    FixResult(
                        success=False,
                        message=f"{self.__class__.__name__}: User cancelled",
                        dry_run=False,
                    )
                ]

        # Apply fixes
        try:
            return self._apply_fix_impl(dry_run=dry_run)
        except Exception as e:
            return [
                FixResult(
                    success=False,
                    message=f"{self.__class__.__name__}: Error: {str(e)}",
                    dry_run=dry_run,
                )
            ]

    def _confirm_fixes(self) -> bool:
        """
        Ask user for confirmation before applying fixes.

        Returns:
            True if user confirms, False otherwise

        EDUCATIONAL NOTE - User Confirmation:
        Always ask before making changes unless explicitly told not to.
        Clear communication about what will change builds user trust.
        """

        print(f"\n{self.__class__.__name__} wants to make the following changes:")
        self._describe_fixes()

        response = input("\nApply these fixes? [y/N]: ").strip().lower()
        return response in ["y", "yes"]

    def _describe_fixes(self) -> None:
        """
        Describe what fixes will be applied.

        Subclasses can override this to provide detailed descriptions.
        """
        print(f"  - Apply automated fixes for detected issues")

    def _run_command(
        self, command: List[str], description: str, dry_run: bool = False
    ) -> Tuple[bool, str]:
        """
        Run a command safely with dry-run support.

        Args:
            command: Command and arguments as list
            description: Human-readable description
            dry_run: If True, don't actually run the command

        Returns:
            Tuple of (success, output_message)

        EDUCATIONAL NOTE - Safe Command Execution:
        Running external commands safely requires:
        1. Using list form instead of shell=True (prevents injection)
        2. Setting timeouts to prevent hanging
        3. Capturing output for feedback
        4. Handling errors gracefully
        5. Supporting dry-run for preview

        Example:
            success, msg = self._run_command(
                ["pip", "install", "requests"],
                "Install requests package",
                dry_run=False
            )
        """

        if dry_run:
            cmd_str = " ".join(command)
            return True, f"[DRY-RUN] Would run: {cmd_str}"

        if self.verbose:
            print(f"  Running: {' '.join(command)}")

        # Use the improved subprocess utilities for better error handling
        success, stdout, stderr = run_command_safe(
            command, timeout=300, capture_output=True, text=True  # 5 minute timeout
        )

        if success:
            return True, f"{description}: Success"
        else:
            error_msg = stderr.strip() if stderr else "Unknown error"
            return False, f"{description}: Failed - {error_msg}"

    def _log(self, message: str, level: str = "INFO") -> None:
        """
        Log a message if verbose mode is enabled.

        Args:
            message: Message to log
            level: Log level (INFO, WARNING, ERROR)
        """
        if self.verbose:
            print(f"  [{level}] {message}")

    def get_fixable_issues(self) -> List[Issue]:
        """
        Get all fixable issues from environment status.

        Returns:
            List of issues that are marked as fixable
        """
        return [issue for issue in self.env_status.issues if issue.fixable]

    def get_python_executable(self) -> str:
        """
        Get the appropriate Python executable to use for commands.

        Returns:
            Path to Python executable

        EDUCATIONAL NOTE - Python Executable Selection:
        We need to be careful about which Python to use:
        - sys.executable: The currently running Python
        - env_status.python_executable: The detected project Python
        - venv Python: The virtual environment's Python

        Using the wrong Python can install packages in the wrong environment!
        """

        # If a venv is active, use that Python
        if self.env_status.venv_active and self.env_status.venv_path:
            venv_python = self._get_venv_python(self.env_status.venv_path)
            if venv_python:
                return venv_python

        # Otherwise use detected Python
        return self.env_status.python_executable or sys.executable

    def _get_venv_python(self, venv_path: str) -> Optional[str]:
        """
        Get Python executable from virtual environment path.

        Args:
            venv_path: Path to virtual environment

        Returns:
            Path to Python executable or None
        """

        venv_dir = Path(venv_path)

        # Unix-like systems
        unix_python = venv_dir / "bin" / "python3"
        if unix_python.exists():
            return str(unix_python)

        unix_python_alt = venv_dir / "bin" / "python"
        if unix_python_alt.exists():
            return str(unix_python_alt)

        # Windows
        windows_python = venv_dir / "Scripts" / "python.exe"
        if windows_python.exists():
            return str(windows_python)

        return None


# Example usage and testing
if __name__ == "__main__":
    """
    Demonstrate base fixer functionality.
    """

    # Create a simple concrete fixer for testing
    class TestFixer(BaseFixer):
        def can_fix(self) -> bool:
            return True

        def _apply_fix_impl(self, dry_run: bool = False) -> List[FixResult]:
            return [
                FixResult(
                    success=True,
                    message="Test fix applied successfully",
                    dry_run=dry_run,
                )
            ]

    print("=" * 60)
    print("Base Fixer Module - Test Run")
    print("=" * 60)

    # Create dummy environment status
    from harmonizer.models import OSType, VenvType

    env_status = EnvironmentStatus(
        os_type=OSType.LINUX,
        os_version="Ubuntu 22.04",
        python_version="3.10.6",
        python_executable="/usr/bin/python3",
        venv_type=VenvType.NONE,
        venv_active=False,
        project_path=".",
    )

    # Test the fixer
    fixer = TestFixer(env_status, verbose=True, auto_yes=True)

    print("\nTesting dry-run:")
    results = fixer.apply_fixes(dry_run=True)
    for result in results:
        print(f"  {result}")

    print("\n" + "=" * 60)
