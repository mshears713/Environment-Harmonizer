"""
Cleanup Utilities Module.

This module provides utilities for cleaning up temporary files,
cache directories, and other artifacts created during scanning.

EDUCATIONAL NOTE - Why Cleanup Matters:
Applications should clean up after themselves:
1. Prevent disk space exhaustion
2. Remove sensitive temporary data
3. Avoid leftover processes
4. Maintain system hygiene
5. Good citizenship on shared systems

Cleanup strategies:
- Use context managers for automatic cleanup
- Register cleanup handlers (atexit, signal handlers)
- Clean up even when errors occur (try/finally)
- Log what was cleaned up
- Handle cleanup failures gracefully
"""

import os
import shutil
import tempfile
import atexit
import signal
from pathlib import Path
from typing import List, Optional, Set
import time

from harmonizer.utils.logging_config import HarmonizerLogger


logger = HarmonizerLogger.get_logger(__name__)


class CleanupManager:
    """
    Manager for tracking and cleaning up temporary resources.

    This class tracks:
    - Temporary files created
    - Temporary directories created
    - Cache files to clean
    - Resources that need cleanup on exit

    EDUCATIONAL NOTE - Resource Management:
    Proper resource management prevents:
    - Memory leaks
    - File handle exhaustion
    - Disk space issues
    - Zombie processes

    Best practices:
    - Track all resources
    - Clean up in reverse order of creation
    - Use try/finally or context managers
    - Handle cleanup failures
    """

    def __init__(self, auto_cleanup: bool = True):
        """
        Initialize the cleanup manager.

        Args:
            auto_cleanup: If True, automatically cleanup on exit
        """
        self.temp_files: Set[Path] = set()
        self.temp_dirs: Set[Path] = set()
        self.cache_files: Set[Path] = set()
        self.auto_cleanup = auto_cleanup

        if auto_cleanup:
            # Register cleanup function to run on exit
            atexit.register(self.cleanup_all)

            # Also cleanup on SIGTERM (graceful shutdown)
            try:
                signal.signal(signal.SIGTERM, self._signal_handler)
            except (ValueError, OSError):
                # Signal handling not available (Windows, etc.)
                pass

        logger.debug("CleanupManager initialized")

    def _signal_handler(self, signum, frame):
        """Handle signals by cleaning up before exit."""
        logger.info(f"Received signal {signum}, cleaning up")
        self.cleanup_all()

    def register_temp_file(self, file_path: Path) -> Path:
        """
        Register a temporary file for cleanup.

        Args:
            file_path: Path to temporary file

        Returns:
            Same path (for chaining)

        Example:
            >>> cleanup = CleanupManager()
            >>> temp_file = cleanup.register_temp_file(Path("/tmp/test.txt"))
            >>> # File will be deleted on cleanup
        """
        self.temp_files.add(file_path)
        logger.debug(f"Registered temp file: {file_path}")
        return file_path

    def register_temp_dir(self, dir_path: Path) -> Path:
        """
        Register a temporary directory for cleanup.

        Args:
            dir_path: Path to temporary directory

        Returns:
            Same path (for chaining)
        """
        self.temp_dirs.add(dir_path)
        logger.debug(f"Registered temp dir: {dir_path}")
        return dir_path

    def register_cache_file(self, file_path: Path) -> Path:
        """
        Register a cache file for cleanup.

        Args:
            file_path: Path to cache file

        Returns:
            Same path (for chaining)

        EDUCATIONAL NOTE - Caching:
        Cache files improve performance but:
        - Take up disk space
        - Can become stale
        - May contain sensitive data

        Clean up:
        - Old cache files (>N days)
        - On user request (--clear-cache)
        - When disk space is low
        """
        self.cache_files.add(file_path)
        logger.debug(f"Registered cache file: {file_path}")
        return file_path

    def cleanup_temp_files(self) -> int:
        """
        Clean up all registered temporary files.

        Returns:
            Number of files successfully deleted
        """
        cleaned = 0

        for file_path in list(self.temp_files):
            try:
                if file_path.exists():
                    file_path.unlink()
                    logger.debug(f"Deleted temp file: {file_path}")
                    cleaned += 1
                self.temp_files.remove(file_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file {file_path}: {e}")

        return cleaned

    def cleanup_temp_dirs(self) -> int:
        """
        Clean up all registered temporary directories.

        Returns:
            Number of directories successfully deleted

        EDUCATIONAL NOTE - Directory Deletion:
        Deleting directories requires:
        1. Recursively delete all contents first
        2. Then delete the directory itself
        3. Handle permission errors
        4. Handle files in use
        5. Handle symbolic links carefully

        shutil.rmtree() handles most of this automatically.
        """
        cleaned = 0

        for dir_path in list(self.temp_dirs):
            try:
                if dir_path.exists():
                    shutil.rmtree(dir_path)
                    logger.debug(f"Deleted temp dir: {dir_path}")
                    cleaned += 1
                self.temp_dirs.remove(dir_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp dir {dir_path}: {e}")

        return cleaned

    def cleanup_cache_files(self, max_age_days: Optional[int] = None) -> int:
        """
        Clean up cache files, optionally filtering by age.

        Args:
            max_age_days: If specified, only delete files older than this many days

        Returns:
            Number of cache files deleted
        """
        cleaned = 0
        current_time = time.time()

        for file_path in list(self.cache_files):
            try:
                if not file_path.exists():
                    self.cache_files.remove(file_path)
                    continue

                # Check age if specified
                if max_age_days is not None:
                    file_age_days = (current_time - file_path.stat().st_mtime) / (24 * 3600)
                    if file_age_days < max_age_days:
                        continue

                file_path.unlink()
                logger.debug(f"Deleted cache file: {file_path}")
                self.cache_files.remove(file_path)
                cleaned += 1

            except Exception as e:
                logger.warning(f"Failed to delete cache file {file_path}: {e}")

        return cleaned

    def cleanup_all(self) -> Dict[str, int]:
        """
        Clean up all registered resources.

        Returns:
            Dictionary with cleanup statistics:
            - temp_files: Number of temp files deleted
            - temp_dirs: Number of temp dirs deleted
            - cache_files: Number of cache files deleted
        """
        logger.info("Starting cleanup of all resources")

        stats = {
            "temp_files": self.cleanup_temp_files(),
            "temp_dirs": self.cleanup_temp_dirs(),
            "cache_files": self.cleanup_cache_files(),
        }

        total = sum(stats.values())
        logger.info(f"Cleanup complete: {total} items removed")

        return stats

    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about tracked resources.

        Returns:
            Dictionary with resource counts
        """
        return {
            "temp_files": len(self.temp_files),
            "temp_dirs": len(self.temp_dirs),
            "cache_files": len(self.cache_files),
        }


# Global cleanup manager instance
_global_cleanup_manager: Optional[CleanupManager] = None


def get_cleanup_manager() -> CleanupManager:
    """
    Get the global cleanup manager instance.

    Returns:
        Global CleanupManager instance
    """
    global _global_cleanup_manager
    if _global_cleanup_manager is None:
        _global_cleanup_manager = CleanupManager(auto_cleanup=True)
    return _global_cleanup_manager


def create_temp_file(suffix: str = "", prefix: str = "harmonizer_") -> Path:
    """
    Create a temporary file that will be automatically cleaned up.

    Args:
        suffix: File suffix (e.g., ".txt")
        prefix: File prefix

    Returns:
        Path to the temporary file

    EDUCATIONAL NOTE - Temporary Files:
    tempfile.mkstemp() creates secure temporary files:
    - Random names (prevents guessing)
    - Proper permissions (owner read/write only)
    - Atomic creation (no race conditions)
    - Platform-appropriate temp directory

    Always clean up temp files when done!

    Example:
        >>> temp_file = create_temp_file(suffix=".json")
        >>> temp_file.write_text('{"test": true}')
        >>> # File will be auto-cleaned on exit
    """
    cleanup_mgr = get_cleanup_manager()

    # Create temporary file
    fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
    os.close(fd)  # Close file descriptor, we just need the path

    temp_file = Path(temp_path)
    cleanup_mgr.register_temp_file(temp_file)

    logger.debug(f"Created temp file: {temp_file}")
    return temp_file


def create_temp_dir(suffix: str = "", prefix: str = "harmonizer_") -> Path:
    """
    Create a temporary directory that will be automatically cleaned up.

    Args:
        suffix: Directory suffix
        prefix: Directory prefix

    Returns:
        Path to the temporary directory

    Example:
        >>> temp_dir = create_temp_dir()
        >>> (temp_dir / "test.txt").write_text("test")
        >>> # Directory and contents will be auto-cleaned on exit
    """
    cleanup_mgr = get_cleanup_manager()

    temp_dir = Path(tempfile.mkdtemp(suffix=suffix, prefix=prefix))
    cleanup_mgr.register_temp_dir(temp_dir)

    logger.debug(f"Created temp dir: {temp_dir}")
    return temp_dir


def cleanup_harmonizer_cache(max_age_days: int = 30) -> int:
    """
    Clean up old Environment Harmonizer cache files.

    Args:
        max_age_days: Delete cache files older than this many days

    Returns:
        Number of cache files deleted

    EDUCATIONAL NOTE - Cache Location:
    Cache files are typically stored in:
    - Linux/macOS: ~/.cache/harmonizer/ or ~/.harmonizer/cache/
    - Windows: %LOCALAPPDATA%\\harmonizer\\cache\\

    Following platform conventions makes cleanup easier
    and respects user expectations.
    """
    logger.info(f"Cleaning up cache files older than {max_age_days} days")

    deleted_count = 0

    # Common cache locations
    cache_dirs = []

    # User cache directory
    home = Path.home()
    cache_dirs.append(home / ".cache" / "harmonizer")
    cache_dirs.append(home / ".harmonizer" / "cache")

    # Windows cache
    if os.name == "nt":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            cache_dirs.append(Path(local_app_data) / "harmonizer" / "cache")

    # Clean each cache directory
    for cache_dir in cache_dirs:
        if not cache_dir.exists():
            continue

        try:
            current_time = time.time()
            cutoff_time = current_time - (max_age_days * 24 * 3600)

            for cache_file in cache_dir.rglob("*"):
                if not cache_file.is_file():
                    continue

                try:
                    if cache_file.stat().st_mtime < cutoff_time:
                        cache_file.unlink()
                        deleted_count += 1
                        logger.debug(f"Deleted old cache file: {cache_file}")
                except Exception as e:
                    logger.warning(f"Failed to delete cache file {cache_file}: {e}")

        except Exception as e:
            logger.error(f"Failed to clean cache directory {cache_dir}: {e}")

    logger.info(f"Deleted {deleted_count} old cache files")
    return deleted_count


# Context manager for temporary directory
class TemporaryDirectory:
    """
    Context manager for a temporary directory with automatic cleanup.

    EDUCATIONAL NOTE - Context Managers:
    Context managers provide automatic setup and teardown:

    with TemporaryDirectory() as temp_dir:
        # Use temp_dir
        pass
    # temp_dir is automatically deleted here

    This is safer than manual cleanup because:
    - Cleanup happens even if exceptions occur
    - Can't forget to clean up
    - Code is more readable

    Example:
        >>> with TemporaryDirectory() as temp_dir:
        ...     config_file = temp_dir / "config.json"
        ...     config_file.write_text("{}")
        ...     # Use config_file
        ... # temp_dir and all contents are deleted here
    """

    def __init__(self, suffix: str = "", prefix: str = "harmonizer_"):
        """
        Initialize temporary directory context manager.

        Args:
            suffix: Directory suffix
            prefix: Directory prefix
        """
        self.suffix = suffix
        self.prefix = prefix
        self.temp_dir: Optional[Path] = None

    def __enter__(self) -> Path:
        """Create temporary directory on entering context."""
        self.temp_dir = Path(tempfile.mkdtemp(suffix=self.suffix, prefix=self.prefix))
        logger.debug(f"Created temporary directory: {self.temp_dir}")
        return self.temp_dir

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up temporary directory on exiting context."""
        if self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
                logger.debug(f"Cleaned up temporary directory: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary directory: {e}")
        return False  # Don't suppress exceptions


# Example usage and testing
if __name__ == "__main__":
    """
    Test cleanup utilities.
    """

    print("=" * 70)
    print("Cleanup Utilities - Test Run")
    print("=" * 70)

    # Test cleanup manager
    cleanup_mgr = CleanupManager(auto_cleanup=False)

    # Create some temp files
    print("\nCreating temporary resources...")
    temp_file1 = create_temp_file(suffix=".txt")
    temp_file1.write_text("Test content")
    print(f"Created: {temp_file1}")

    temp_dir1 = create_temp_dir()
    (temp_dir1 / "test.txt").write_text("Test")
    print(f"Created: {temp_dir1}")

    # Show stats
    print("\nResource stats:")
    stats = cleanup_mgr.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Clean up
    print("\nCleaning up...")
    cleanup_stats = cleanup_mgr.cleanup_all()
    for key, value in cleanup_stats.items():
        print(f"  {key}: {value} deleted")

    # Test context manager
    print("\nTesting TemporaryDirectory context manager...")
    with TemporaryDirectory() as temp_dir:
        test_file = temp_dir / "test.txt"
        test_file.write_text("Context manager test")
        print(f"Created in context: {temp_dir}")
        print(f"Exists in context: {temp_dir.exists()}")

    print(f"Exists after context: {temp_dir.exists()}")

    print("\n" + "=" * 70)
