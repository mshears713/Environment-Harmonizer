"""
Progress Reporting Utilities.

This module provides progress indicators and colored output for the CLI,
improving user experience by showing what the tool is doing in real-time.

EDUCATIONAL NOTE - Why Progress Feedback Matters:
Users need to know what's happening during long-running operations:
1. Reduces uncertainty ("Is it frozen or working?")
2. Builds trust ("The tool is doing what I expect")
3. Provides context for failures ("It failed at X step")
4. Makes the tool feel responsive and professional

Good progress feedback should:
- Be clear and concise
- Show current action
- Indicate progress (where possible)
- Use visual cues (colors, symbols)
- Not overwhelm with too much detail
"""

import sys
from enum import Enum
from typing import Optional


class Color(Enum):
    """ANSI color codes for terminal output."""

    # Basic colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Styles
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


class ProgressReporter:
    """
    Progress reporter for CLI operations.

    Provides consistent formatting for progress messages, warnings, errors,
    and success indicators.

    EDUCATIONAL NOTE - Terminal Color Support:
    Not all terminals support ANSI color codes:
    - Most modern terminals (Unix, macOS Terminal, Windows Terminal) do
    - Old Windows cmd.exe (pre-Windows 10) doesn't
    - Piped output or redirected to files shouldn't have colors
    - CI/CD environments often don't support colors

    We detect color support and fall back gracefully.
    """

    def __init__(self, use_color: bool = True, verbose: bool = False):
        """
        Initialize progress reporter.

        Args:
            use_color: Whether to use ANSI color codes
            verbose: Whether to show verbose messages
        """
        self.use_color = use_color and self._supports_color()
        self.verbose = verbose
        self._current_step = None

    def _supports_color(self) -> bool:
        """
        Check if the terminal supports ANSI color codes.

        Returns:
            True if colors are supported, False otherwise

        EDUCATIONAL NOTE - Color Detection:
        We check several indicators:
        1. sys.stdout.isatty() - is output going to a terminal?
        2. TERM environment variable - what terminal type?
        3. Platform - Windows requires special handling

        If any check fails, we disable colors to avoid garbled output.
        """
        import os
        import platform

        # Not a TTY (output is redirected)
        if not sys.stdout.isatty():
            return False

        # Check for NO_COLOR environment variable (standard)
        if os.environ.get("NO_COLOR"):
            return False

        # Check TERM environment variable
        term = os.environ.get("TERM", "")
        if term == "dumb":
            return False

        # Windows special handling
        if platform.system() == "Windows":
            # Windows 10+ supports ANSI colors
            try:
                import ctypes

                kernel32 = ctypes.windll.kernel32
                # Enable ANSI escape sequence processing
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                return True
            except Exception:
                return False

        return True

    def _colorize(self, text: str, color: Color) -> str:
        """
        Apply color to text if colors are enabled.

        Args:
            text: Text to colorize
            color: Color enum value

        Returns:
            Colored text or plain text if colors disabled
        """
        if self.use_color:
            return f"{color.value}{text}{Color.RESET.value}"
        return text

    def start_step(self, step_name: str) -> None:
        """
        Indicate the start of a new step.

        Args:
            step_name: Name of the step being started

        Example:
            >>> reporter.start_step("Scanning for Python version")
            ⏳ Scanning for Python version...
        """
        self._current_step = step_name
        icon = "⏳" if self.use_color else "..."
        message = f"{icon} {step_name}..."
        print(self._colorize(message, Color.CYAN))

    def complete_step(self, message: Optional[str] = None) -> None:
        """
        Indicate successful completion of current step.

        Args:
            message: Optional success message (uses current step name if not provided)

        Example:
            >>> reporter.complete_step("Python 3.10.6 detected")
            ✓ Python 3.10.6 detected
        """
        if message is None:
            message = f"{self._current_step} complete"

        icon = "✓" if self.use_color else "[OK]"
        output = f"{icon} {message}"
        print(self._colorize(output, Color.GREEN))
        self._current_step = None

    def error(self, message: str) -> None:
        """
        Display an error message.

        Args:
            message: Error message to display

        Example:
            >>> reporter.error("Python version requirement not met")
            ✗ Python version requirement not met
        """
        icon = "✗" if self.use_color else "[ERROR]"
        output = f"{icon} {message}"
        print(self._colorize(output, Color.RED), file=sys.stderr)

    def warning(self, message: str) -> None:
        """
        Display a warning message.

        Args:
            message: Warning message to display

        Example:
            >>> reporter.warning("Virtual environment not activated")
            ⚠ Virtual environment not activated
        """
        icon = "⚠" if self.use_color else "[WARN]"
        output = f"{icon} {message}"
        print(self._colorize(output, Color.YELLOW))

    def info(self, message: str) -> None:
        """
        Display an informational message.

        Args:
            message: Info message to display

        Example:
            >>> reporter.info("Found requirements.txt")
            ℹ Found requirements.txt
        """
        icon = "ℹ" if self.use_color else "[INFO]"
        output = f"{icon} {message}"
        print(self._colorize(output, Color.BLUE))

    def verbose(self, message: str) -> None:
        """
        Display a verbose/debug message (only if verbose mode enabled).

        Args:
            message: Verbose message to display

        Example:
            >>> reporter.verbose("Checking /proc/version for WSL markers")
              DEBUG: Checking /proc/version for WSL markers
        """
        if self.verbose:
            output = f"  DEBUG: {message}"
            print(self._colorize(output, Color.DIM))

    def section(self, title: str) -> None:
        """
        Display a section header.

        Args:
            title: Section title

        Example:
            >>> reporter.section("Environment Detection")

            ═══ Environment Detection ═══
        """
        separator = "═" * len(title)
        header = f"\n{separator}\n{title}\n{separator}"
        print(self._colorize(header, Color.BOLD))

    def progress(self, current: int, total: int, item: str = "") -> None:
        """
        Display progress indicator.

        Args:
            current: Current item number
            total: Total number of items
            item: Optional description of current item

        Example:
            >>> reporter.progress(3, 10, "checking numpy")
            [3/10] checking numpy
        """
        item_str = f" {item}" if item else ""
        output = f"[{current}/{total}]{item_str}"
        print(self._colorize(output, Color.CYAN))

    def summary_line(
        self, label: str, value: str, severity: Optional[str] = None
    ) -> None:
        """
        Display a summary line with label and value.

        Args:
            label: Label for the value
            value: The value to display
            severity: Optional severity level (error, warning, info)

        Example:
            >>> reporter.summary_line("Python Version", "3.10.6", "info")
            Python Version: 3.10.6
        """
        # Choose color based on severity
        color = Color.WHITE
        if severity == "error":
            color = Color.RED
        elif severity == "warning":
            color = Color.YELLOW
        elif severity == "info":
            color = Color.CYAN

        output = f"{label}: {value}"
        print(self._colorize(output, color))


def create_spinner(message: str = "Processing"):
    """
    Create a simple spinner for long-running operations.

    Args:
        message: Message to display with spinner

    Returns:
        Context manager that displays spinner

    EDUCATIONAL NOTE - Spinners:
    Spinners provide visual feedback for operations without discrete progress.
    They're useful when:
    - Operation duration is unknown
    - Progress can't be measured
    - User needs to know something is happening

    Implementation uses a context manager for clean setup/teardown.

    Example:
        >>> with create_spinner("Downloading package"):
        ...     time.sleep(2)  # Long operation
        ⠋ Downloading package...
    """
    import threading
    import time

    class Spinner:
        def __init__(self, message: str):
            self.message = message
            self.spinning = False
            self.thread = None
            self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
            self.frame_index = 0

        def _spin(self):
            while self.spinning:
                frame = self.frames[self.frame_index % len(self.frames)]
                sys.stdout.write(f"\r{frame} {self.message}...")
                sys.stdout.flush()
                self.frame_index += 1
                time.sleep(0.1)
            sys.stdout.write("\r" + " " * (len(self.message) + 10) + "\r")
            sys.stdout.flush()

        def __enter__(self):
            self.spinning = True
            self.thread = threading.Thread(target=self._spin)
            self.thread.start()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.spinning = False
            if self.thread:
                self.thread.join()

    return Spinner(message)


# Example usage and testing
if __name__ == "__main__":
    """
    Test the progress reporting utilities.
    """

    print("Testing Progress Reporter")
    print("=" * 60)

    reporter = ProgressReporter(use_color=True, verbose=True)

    # Test section header
    reporter.section("Environment Scan")

    # Test step progression
    reporter.start_step("Detecting operating system")
    import time

    time.sleep(0.5)
    reporter.complete_step("Detected Linux (Ubuntu 22.04)")

    reporter.start_step("Detecting Python version")
    time.sleep(0.5)
    reporter.complete_step("Python 3.10.6 detected")

    # Test different message types
    reporter.info("Found requirements.txt with 5 packages")
    reporter.warning("Virtual environment not activated")
    reporter.verbose("Checking /etc/os-release for distribution info")

    # Test summary lines
    print("\n" + "─" * 60)
    reporter.summary_line("OS Type", "Linux", "info")
    reporter.summary_line("Python Version", "3.10.6", "info")
    reporter.summary_line("Virtual Env", "Not activated", "warning")
    reporter.summary_line("Missing Packages", "3", "error")

    # Test progress indicator
    print("\n" + "─" * 60)
    for i in range(1, 6):
        reporter.progress(i, 5, f"package-{i}")
        time.sleep(0.2)

    # Test spinner
    print("\n" + "─" * 60)
    with create_spinner("Testing spinner"):
        time.sleep(2)

    reporter.complete_step("All tests completed")

    print("\n" + "=" * 60)
