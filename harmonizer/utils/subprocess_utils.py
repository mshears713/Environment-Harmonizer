"""
Subprocess Utilities Module.

This module provides robust subprocess execution utilities with comprehensive
exception handling, timeout management, and error recovery.

EDUCATIONAL NOTE - Why Centralized Subprocess Handling:
Subprocess calls can fail in many ways:
- Command not found (FileNotFoundError)
- Timeout (TimeoutExpired)
- Permission denied (PermissionError)
- Process terminated (subprocess.SubprocessError)
- Network issues (for commands that require network)
- Resource exhaustion (out of memory, too many processes)

By centralizing subprocess handling, we:
1. Ensure consistent error handling across the codebase
2. Provide better error messages to users
3. Implement retry logic for transient failures
4. Add comprehensive logging for debugging
5. Handle platform-specific quirks in one place
"""

import subprocess
import sys
import time
from typing import Tuple, List, Optional, Callable
from enum import Enum


class SubprocessError(Exception):
    """Base exception for subprocess-related errors."""

    def __init__(self, message: str, command: List[str], returncode: Optional[int] = None):
        super().__init__(message)
        self.command = command
        self.returncode = returncode


class CommandNotFoundError(SubprocessError):
    """Raised when the command executable is not found."""
    pass


class CommandTimeoutError(SubprocessError):
    """Raised when the command times out."""
    pass


class CommandFailedError(SubprocessError):
    """Raised when the command returns non-zero exit code."""
    pass


def run_command(
    command: List[str],
    timeout: int = 30,
    capture_output: bool = True,
    text: bool = True,
    check: bool = False,
    retry_count: int = 0,
    retry_delay: float = 1.0,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
) -> subprocess.CompletedProcess:
    """
    Run a command with comprehensive error handling and retry logic.

    Args:
        command: Command and arguments as list
        timeout: Timeout in seconds (default: 30)
        capture_output: Whether to capture stdout/stderr (default: True)
        text: Whether to decode output as text (default: True)
        check: Whether to raise exception on non-zero exit (default: False)
        retry_count: Number of times to retry on failure (default: 0)
        retry_delay: Delay between retries in seconds (default: 1.0)
        on_retry: Optional callback function(attempt, exception) called before retry

    Returns:
        CompletedProcess object with returncode, stdout, stderr

    Raises:
        CommandNotFoundError: If command executable not found
        CommandTimeoutError: If command times out
        CommandFailedError: If command returns non-zero exit code (when check=True)
        SubprocessError: For other subprocess-related errors

    EDUCATIONAL NOTE - Retry Logic:
    Retrying failed operations is useful for:
    - Transient network failures
    - Temporary resource unavailability
    - Race conditions in system state

    But be careful:
    - Don't retry operations that modify state (idempotency matters)
    - Use exponential backoff for network operations
    - Set maximum retry limits to avoid infinite loops
    - Log retry attempts for debugging

    Example:
        >>> result = run_command(
        ...     ["python", "--version"],
        ...     timeout=5,
        ...     retry_count=2,
        ...     retry_delay=0.5
        ... )
        >>> print(result.stdout)
        Python 3.10.6
    """

    last_exception = None

    for attempt in range(retry_count + 1):
        try:
            result = subprocess.run(
                command,
                capture_output=capture_output,
                text=text,
                timeout=timeout,
                check=False,  # We handle exit codes manually
            )

            # Check exit code if requested
            if check and result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                raise CommandFailedError(
                    f"Command failed with exit code {result.returncode}: {error_msg}",
                    command=command,
                    returncode=result.returncode
                )

            return result

        except FileNotFoundError as e:
            # Command not found - don't retry this
            raise CommandNotFoundError(
                f"Command not found: {command[0]}",
                command=command
            ) from e

        except subprocess.TimeoutExpired as e:
            last_exception = CommandTimeoutError(
                f"Command timed out after {timeout} seconds",
                command=command
            )

        except PermissionError as e:
            # Permission denied - don't retry this
            raise SubprocessError(
                f"Permission denied executing command: {command[0]}",
                command=command
            ) from e

        except subprocess.SubprocessError as e:
            last_exception = SubprocessError(
                f"Subprocess error: {str(e)}",
                command=command
            )

        except Exception as e:
            last_exception = SubprocessError(
                f"Unexpected error running command: {str(e)}",
                command=command
            )

        # If we have more retries left, wait and try again
        if attempt < retry_count:
            if on_retry:
                on_retry(attempt + 1, last_exception)
            time.sleep(retry_delay)
        else:
            # No more retries, raise the last exception
            raise last_exception


def run_command_safe(
    command: List[str],
    timeout: int = 30,
    default_output: str = "",
    capture_output: bool = True,
    text: bool = True,
) -> Tuple[bool, str, str]:
    """
    Run a command safely, never raising exceptions.

    This is a convenience wrapper that catches all exceptions and returns
    success/failure status instead. Useful when you want to handle errors
    inline without try/except blocks.

    Args:
        command: Command and arguments as list
        timeout: Timeout in seconds
        default_output: Default output to return on failure
        capture_output: Whether to capture stdout/stderr
        text: Whether to decode output as text

    Returns:
        Tuple of (success, stdout, stderr)
        - success: True if command succeeded, False otherwise
        - stdout: Standard output (or default_output on failure)
        - stderr: Standard error (or error message on exception)

    EDUCATIONAL NOTE - Exception vs Error Handling:
    Sometimes exceptions aren't the best error handling mechanism:
    - For expected failures (like checking if a command exists)
    - When you need to continue regardless of failure
    - When exceptions would clutter the code with try/except

    In these cases, returning status codes is cleaner.

    Example:
        >>> success, output, error = run_command_safe(["which", "python"])
        >>> if success:
        ...     print(f"Python found at: {output.strip()}")
        ... else:
        ...     print(f"Python not found: {error}")
    """

    try:
        result = subprocess.run(
            command,
            capture_output=capture_output,
            text=text,
            timeout=timeout,
            check=False,
        )

        if result.returncode == 0:
            return True, result.stdout, result.stderr
        else:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            return False, default_output, error_msg

    except FileNotFoundError:
        return False, default_output, f"Command not found: {command[0]}"

    except subprocess.TimeoutExpired:
        return False, default_output, f"Command timed out after {timeout} seconds"

    except PermissionError:
        return False, default_output, f"Permission denied executing: {command[0]}"

    except subprocess.SubprocessError as e:
        return False, default_output, f"Subprocess error: {str(e)}"

    except Exception as e:
        return False, default_output, f"Unexpected error: {str(e)}"


def check_command_exists(command: str, timeout: int = 2) -> bool:
    """
    Check if a command exists and is executable.

    Args:
        command: Name of command to check (e.g., "git", "python3")
        timeout: Timeout for the check in seconds

    Returns:
        True if command exists and is executable, False otherwise

    EDUCATIONAL NOTE - Command Existence Checking:
    Different methods to check if a command exists:

    1. Using 'which' (Unix) or 'where' (Windows):
       - Portable across platforms
       - Checks PATH environment variable
       - Verifies executability

    2. Using shutil.which (Python 3.3+):
       - Pure Python, no subprocess needed
       - Platform-independent
       - Recommended for most cases

    3. Try to run the command with --version:
       - Most reliable (proves command works)
       - Slower (actually executes)
       - May have side effects

    We use method 1 for compatibility.

    Example:
        >>> if check_command_exists("git"):
        ...     print("Git is installed")
        >>> if not check_command_exists("docker"):
        ...     print("Docker is not installed")
    """

    # Use platform-appropriate command
    import sys
    check_cmd = "where" if sys.platform == "win32" else "which"

    success, _, _ = run_command_safe(
        [check_cmd, command],
        timeout=timeout
    )

    return success


def get_command_version(
    command: str,
    version_arg: str = "--version",
    timeout: int = 5
) -> Optional[str]:
    """
    Get the version of a command.

    Args:
        command: Command name (e.g., "python", "git")
        version_arg: Argument to get version (default: "--version")
        timeout: Timeout in seconds

    Returns:
        Version string if successful, None otherwise

    EDUCATIONAL NOTE - Version Detection:
    Most command-line tools support --version or -V flags:
    - python --version -> "Python 3.10.6"
    - git --version -> "git version 2.34.1"
    - node --version -> "v16.14.0"

    But conventions vary:
    - Some use -v (verbose) instead of --version
    - Some print to stderr instead of stdout
    - Some exit with non-zero code even on success

    Always check both stdout and stderr for version info.

    Example:
        >>> version = get_command_version("python3")
        >>> print(version)
        Python 3.10.6
    """

    success, stdout, stderr = run_command_safe(
        [command, version_arg],
        timeout=timeout
    )

    # Check both stdout and stderr (some commands print version to stderr)
    version_output = (stdout or stderr).strip()

    if version_output:
        return version_output

    return None


def kill_process_tree(pid: int, including_parent: bool = True) -> bool:
    """
    Kill a process and all its children.

    Args:
        pid: Process ID to kill
        including_parent: Whether to kill the parent process too

    Returns:
        True if successful, False otherwise

    EDUCATIONAL NOTE - Process Termination:
    Killing processes requires care:
    1. Always try graceful termination (SIGTERM) before force (SIGKILL)
    2. Kill child processes first to prevent orphans
    3. Handle platform differences (Windows vs Unix signals)
    4. Check permissions (may need elevated privileges)

    Process trees can be complex:
    - Parent spawns child processes
    - Children may spawn grandchildren
    - Some processes may be unkillable (system processes)

    This is useful for cleanup when subprocess spawns multiple processes.
    """

    try:
        import psutil

        parent = psutil.Process(pid)
        children = parent.children(recursive=True)

        # Terminate children first
        for child in children:
            try:
                child.terminate()
            except psutil.NoSuchProcess:
                pass

        # Wait for children to terminate
        gone, alive = psutil.wait_procs(children, timeout=3)

        # Force kill any remaining children
        for child in alive:
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass

        # Kill parent if requested
        if including_parent:
            try:
                parent.terminate()
                parent.wait(timeout=3)
            except psutil.TimeoutExpired:
                parent.kill()

        return True

    except ImportError:
        # psutil not available, fall back to simple kill
        import os
        import signal

        try:
            if sys.platform == "win32":
                # Windows doesn't have signal.SIGTERM
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=False)
            else:
                os.kill(pid, signal.SIGTERM)
            return True
        except Exception:
            return False

    except Exception:
        return False


# Example usage and testing
if __name__ == "__main__":
    """
    Test the subprocess utilities module.
    """

    print("=" * 70)
    print("Subprocess Utilities Module - Test Run")
    print("=" * 70)

    # Test 1: Simple command execution
    print("\nTest 1: Run simple command")
    try:
        result = run_command(["python3", "--version"], timeout=5)
        print(f"  Success: {result.stdout.strip()}")
    except SubprocessError as e:
        print(f"  Failed: {e}")

    # Test 2: Command existence check
    print("\nTest 2: Check command existence")
    for cmd in ["python3", "git", "nonexistent-command-12345"]:
        exists = check_command_exists(cmd)
        print(f"  {cmd}: {'Found' if exists else 'Not found'}")

    # Test 3: Get command version
    print("\nTest 3: Get command versions")
    for cmd in ["python3", "git"]:
        version = get_command_version(cmd)
        if version:
            print(f"  {cmd}: {version}")
        else:
            print(f"  {cmd}: Version not available")

    # Test 4: Safe command execution
    print("\nTest 4: Safe command execution")
    success, output, error = run_command_safe(["echo", "Hello, World!"])
    print(f"  Success: {success}")
    print(f"  Output: {output.strip()}")

    # Test 5: Timeout handling
    print("\nTest 5: Timeout handling")
    try:
        # Try to run a command with very short timeout
        result = run_command(["python3", "-c", "import time; time.sleep(10)"], timeout=1)
        print(f"  Completed: {result.returncode}")
    except CommandTimeoutError as e:
        print(f"  Timed out (expected): {e}")

    print("\n" + "=" * 70)
