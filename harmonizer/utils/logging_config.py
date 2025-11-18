"""
Logging Configuration Module.

This module provides centralized logging configuration with rotating file logs
for debugging and troubleshooting.

EDUCATIONAL NOTE - Why Logging Matters:
Logging is essential for:
1. Debugging issues that users encounter
2. Understanding program behavior in production
3. Performance monitoring and optimization
4. Audit trails for automated operations
5. Troubleshooting environmental issues

Good logging should:
- Be configurable (level, format, output)
- Not impact performance significantly
- Rotate files to prevent disk space issues
- Include context (timestamps, module names, severity)
- Be searchable and parseable
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
import os


class HarmonizerLogger:
    """
    Centralized logger for Environment Harmonizer.

    Provides:
    - Console logging (with color support)
    - File logging with rotation
    - Configurable log levels
    - Module-specific loggers

    EDUCATIONAL NOTE - Logging Levels:
    Python's logging module uses 5 standard levels:
    - DEBUG (10): Detailed diagnostic information
    - INFO (20): General informational messages
    - WARNING (30): Warning messages (something unexpected but handled)
    - ERROR (40): Error messages (operation failed)
    - CRITICAL (50): Critical errors (program may crash)

    Each level includes all higher severity levels.
    Setting level to WARNING shows WARNING, ERROR, and CRITICAL.
    """

    _initialized = False
    _log_dir: Optional[Path] = None

    @classmethod
    def initialize(
        cls,
        log_level: str = "INFO",
        log_dir: Optional[str] = None,
        enable_file_logging: bool = True,
        enable_console_logging: bool = True,
        max_bytes: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 5,
    ) -> None:
        """
        Initialize the logging system.

        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Directory for log files (default: ~/.harmonizer/logs)
            enable_file_logging: Enable logging to files
            enable_console_logging: Enable logging to console
            max_bytes: Maximum size of each log file before rotation
            backup_count: Number of backup log files to keep

        EDUCATIONAL NOTE - Rotating File Handler:
        RotatingFileHandler automatically:
        1. Creates a new log file when current file reaches max_bytes
        2. Renames old files: app.log -> app.log.1 -> app.log.2, etc.
        3. Deletes oldest files when backup_count is exceeded
        4. Prevents logs from filling up disk space

        Example log rotation:
        app.log (current, 9 MB)
        app.log.1 (10 MB, yesterday)
        app.log.2 (10 MB, 2 days ago)
        ...
        app.log.5 (10 MB, 5 days ago) - oldest kept
        """

        if cls._initialized:
            return

        # Determine log directory
        if log_dir is None:
            # Default to user's home directory
            home = Path.home()
            cls._log_dir = home / ".harmonizer" / "logs"
        else:
            cls._log_dir = Path(log_dir)

        # Create log directory if it doesn't exist
        if enable_file_logging:
            cls._log_dir.mkdir(parents=True, exist_ok=True)

        # Convert log level string to logging constant
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)

        # Get root logger
        root_logger = logging.getLogger("harmonizer")
        root_logger.setLevel(numeric_level)

        # Remove existing handlers
        root_logger.handlers.clear()

        # Create formatters
        # Detailed format for file logs
        file_formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Simpler format for console
        console_formatter = logging.Formatter(
            fmt="[%(levelname)s] %(name)s - %(message)s"
        )

        # Add file handler with rotation
        if enable_file_logging:
            log_file = cls._log_dir / "harmonizer.log"
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)

        # Add console handler
        if enable_console_logging:
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setLevel(
                logging.WARNING
            )  # Only warnings and errors to console
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)

        cls._initialized = True

        # Log initialization
        root_logger.info(f"Logging initialized - Level: {log_level}")
        if enable_file_logging:
            root_logger.info(f"Log directory: {cls._log_dir}")

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get a logger for a specific module.

        Args:
            name: Name of the module (usually __name__)

        Returns:
            Logger instance configured for the module

        EDUCATIONAL NOTE - Logger Hierarchy:
        Loggers form a hierarchy based on their names using dots:
        - "harmonizer" (root)
          - "harmonizer.detectors" (parent)
            - "harmonizer.detectors.os_detector" (child)
            - "harmonizer.detectors.python_detector" (child)
          - "harmonizer.fixers" (parent)
            - "harmonizer.fixers.venv_fixer" (child)

        Child loggers inherit configuration from parents.
        This allows setting different levels for different parts of the app.

        Example:
            >>> logger = HarmonizerLogger.get_logger(__name__)
            >>> logger.info("Scanning started")
            >>> logger.debug("Checking /proc/version")
        """

        # Ensure logging is initialized
        if not cls._initialized:
            cls.initialize()

        return logging.getLogger(name)

    @classmethod
    def get_log_directory(cls) -> Optional[Path]:
        """
        Get the log directory path.

        Returns:
            Path to log directory or None if not initialized
        """
        return cls._log_dir

    @classmethod
    def cleanup_old_logs(cls, days: int = 30) -> int:
        """
        Delete log files older than specified days.

        Args:
            days: Delete logs older than this many days

        Returns:
            Number of files deleted

        EDUCATIONAL NOTE - Log Cleanup:
        Even with rotation, log files can accumulate over time.
        Periodic cleanup prevents:
        - Disk space exhaustion
        - Performance degradation (too many files)
        - Privacy concerns (old logs may contain sensitive data)

        Best practices:
        - Keep logs for debugging purposes (7-30 days)
        - Comply with data retention policies
        - Archive important logs before deletion
        """

        if cls._log_dir is None or not cls._log_dir.exists():
            return 0

        import time

        current_time = time.time()
        cutoff_time = current_time - (days * 24 * 60 * 60)  # Convert days to seconds

        deleted_count = 0
        for log_file in cls._log_dir.glob("*.log*"):
            try:
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    deleted_count += 1
            except (OSError, PermissionError):
                # Can't delete this file, skip it
                pass

        return deleted_count

    @classmethod
    def set_level(cls, level: str) -> None:
        """
        Change the logging level dynamically.

        Args:
            level: New logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

        EDUCATIONAL NOTE - Dynamic Log Levels:
        Changing log levels at runtime is useful for:
        - Increasing verbosity to debug issues
        - Reducing noise in production
        - Temporarily enabling debug mode

        Example:
            # Normal operation
            HarmonizerLogger.set_level("INFO")

            # Debug a specific issue
            HarmonizerLogger.set_level("DEBUG")
            # ... investigate issue ...
            HarmonizerLogger.set_level("INFO")
        """

        numeric_level = getattr(logging, level.upper(), logging.INFO)
        root_logger = logging.getLogger("harmonizer")
        root_logger.setLevel(numeric_level)

        # Update file handler level too
        for handler in root_logger.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                handler.setLevel(numeric_level)


def create_performance_logger() -> logging.Logger:
    """
    Create a specialized logger for performance measurements.

    Returns:
        Logger configured for performance logging

    EDUCATIONAL NOTE - Specialized Loggers:
    Different aspects of the application may need different logging:
    - Performance logs: Timing information, bottlenecks
    - Security logs: Authentication, authorization
    - Audit logs: What actions were taken
    - Error logs: Failures and exceptions

    Specialized loggers can:
    - Write to different files
    - Use different formats
    - Have different retention policies
    """

    logger = logging.getLogger("harmonizer.performance")

    # Don't propagate to parent logger (avoid duplicate messages)
    logger.propagate = False

    # Create performance-specific handler if not already added
    if not logger.handlers:
        log_dir = HarmonizerLogger.get_log_directory()
        if log_dir:
            perf_file = log_dir / "performance.log"
            handler = logging.handlers.RotatingFileHandler(
                perf_file,
                maxBytes=5 * 1024 * 1024,  # 5 MB
                backupCount=3,
            )

            # Performance logs use a specific format
            formatter = logging.Formatter(
                fmt="%(asctime)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S.%f",
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

    return logger


# Context manager for timing operations
class LogTimer:
    """
    Context manager for timing operations with automatic logging.

    EDUCATIONAL NOTE - Context Managers:
    Context managers implement __enter__ and __exit__ methods.
    They're used with the 'with' statement for resource management:
    - Automatic setup and cleanup
    - Exception safety
    - Clean, readable code

    Common use cases:
    - File handling (open/close)
    - Lock acquisition/release
    - Timing operations
    - Database transactions

    Example:
        >>> with LogTimer("database_query", logger):
        ...     result = db.execute(query)
        [INFO] database_query started
        [INFO] database_query completed in 0.123s
    """

    def __init__(self, operation: str, logger: logging.Logger):
        """
        Initialize timer for an operation.

        Args:
            operation: Name of the operation being timed
            logger: Logger to use for timing messages
        """
        self.operation = operation
        self.logger = logger
        self.start_time = None

    def __enter__(self):
        """Start timing when entering context."""
        import time

        self.start_time = time.perf_counter()
        self.logger.debug(f"{self.operation} started")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Log elapsed time when exiting context."""
        import time

        elapsed = time.perf_counter() - self.start_time
        self.logger.info(f"{self.operation} completed in {elapsed:.3f}s")
        return False  # Don't suppress exceptions


# Example usage and testing
if __name__ == "__main__":
    """
    Test the logging configuration module.
    """

    print("Testing Logging Configuration")
    print("=" * 60)

    # Initialize logging
    HarmonizerLogger.initialize(
        log_level="DEBUG",
        enable_file_logging=True,
        enable_console_logging=True,
    )

    print(f"Log directory: {HarmonizerLogger.get_log_directory()}")

    # Get module-specific loggers
    main_logger = HarmonizerLogger.get_logger("harmonizer.main")
    detector_logger = HarmonizerLogger.get_logger("harmonizer.detectors.os_detector")

    # Test different log levels
    main_logger.debug("This is a debug message")
    main_logger.info("This is an info message")
    main_logger.warning("This is a warning message")
    main_logger.error("This is an error message")
    main_logger.critical("This is a critical message")

    # Test performance logger
    perf_logger = create_performance_logger()

    # Test timer context manager
    import time

    with LogTimer("example_operation", main_logger):
        time.sleep(0.1)

    # Test changing log level
    print("\nChanging log level to WARNING...")
    HarmonizerLogger.set_level("WARNING")

    main_logger.debug("This debug won't show")
    main_logger.info("This info won't show")
    main_logger.warning("This warning will show")

    print("\n" + "=" * 60)
    print(f"Check log files in: {HarmonizerLogger.get_log_directory()}")
