"""
Performance Monitoring Module.

This module provides utilities for measuring and optimizing performance
of scanning operations.

EDUCATIONAL NOTE - Why Performance Matters:
For a diagnostic tool, performance is important because:
1. Users expect quick feedback
2. Slow scans frustrate users
3. Performance issues hide real problems
4. Good performance enables frequent use

Performance optimization should focus on:
- Measuring what actually matters to users
- Identifying real bottlenecks (not premature optimization)
- Balancing speed vs accuracy
- Providing feedback during slow operations
"""

import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from functools import wraps
import statistics


@dataclass
class TimingResult:
    """
    Result of a timed operation.

    Attributes:
        operation: Name of the operation
        duration: Time taken in seconds
        timestamp: When the operation started
        metadata: Additional context about the operation
    """

    operation: str
    duration: float
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"{self.operation}: {self.duration:.3f}s"


class PerformanceMonitor:
    """
    Monitor and report on performance of operations.

    This class provides:
    - Timing individual operations
    - Collecting statistics across multiple runs
    - Identifying slow operations
    - Generating performance reports

    EDUCATIONAL NOTE - Performance Profiling:
    There are different levels of performance analysis:
    1. Wall-clock time: Total real-world time (what users experience)
    2. CPU time: Actual CPU processing time
    3. Memory usage: RAM consumption
    4. I/O time: Disk and network operations

    We focus on wall-clock time because it's what users care about.
    For deeper analysis, use Python's cProfile or memory_profiler.
    """

    def __init__(self):
        """Initialize the performance monitor."""
        self.timings: List[TimingResult] = []
        self._active_timers: Dict[str, float] = {}

    def start_timer(self, operation: str) -> None:
        """
        Start timing an operation.

        Args:
            operation: Name of the operation to time

        Example:
            >>> monitor = PerformanceMonitor()
            >>> monitor.start_timer("scan_dependencies")
            >>> # ... do work ...
            >>> monitor.stop_timer("scan_dependencies")
        """
        self._active_timers[operation] = time.perf_counter()

    def stop_timer(self, operation: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[float]:
        """
        Stop timing an operation and record the result.

        Args:
            operation: Name of the operation (must match start_timer call)
            metadata: Optional additional context about the operation

        Returns:
            Duration in seconds, or None if timer wasn't started

        EDUCATIONAL NOTE - time.perf_counter():
        Python provides several timing functions:
        - time.time(): System clock time (can go backwards!)
        - time.perf_counter(): High-resolution performance counter
        - time.process_time(): CPU time only (excludes sleep)

        perf_counter() is best for measuring elapsed time because:
        - High resolution (nanoseconds on most systems)
        - Monotonic (never goes backwards)
        - Includes sleep time (matches user experience)
        """

        if operation not in self._active_timers:
            return None

        start_time = self._active_timers.pop(operation)
        duration = time.perf_counter() - start_time

        result = TimingResult(
            operation=operation,
            duration=duration,
            metadata=metadata or {},
        )

        self.timings.append(result)
        return duration

    def get_statistics(self, operation: Optional[str] = None) -> Dict[str, float]:
        """
        Get statistical summary of timing data.

        Args:
            operation: If specified, only include this operation
                      If None, include all operations

        Returns:
            Dictionary with statistical measures:
            - count: Number of measurements
            - mean: Average time
            - median: Middle value
            - min: Fastest time
            - max: Slowest time
            - stdev: Standard deviation (if multiple measurements)

        EDUCATIONAL NOTE - Performance Statistics:
        Different statistics tell us different things:
        - Mean: Overall average performance
        - Median: Typical performance (not skewed by outliers)
        - Min: Best-case performance
        - Max: Worst-case performance
        - StdDev: Consistency (low = consistent, high = variable)

        Example:
            >>> stats = monitor.get_statistics("scan_os")
            >>> print(f"Average: {stats['mean']:.3f}s")
            >>> print(f"Range: {stats['min']:.3f}s - {stats['max']:.3f}s")
        """

        # Filter timings if operation specified
        if operation:
            relevant_timings = [t for t in self.timings if t.operation == operation]
        else:
            relevant_timings = self.timings

        if not relevant_timings:
            return {}

        durations = [t.duration for t in relevant_timings]

        stats = {
            "count": len(durations),
            "mean": statistics.mean(durations),
            "median": statistics.median(durations),
            "min": min(durations),
            "max": max(durations),
        }

        # Standard deviation requires at least 2 samples
        if len(durations) >= 2:
            stats["stdev"] = statistics.stdev(durations)

        return stats

    def get_slowest_operations(self, n: int = 5) -> List[TimingResult]:
        """
        Get the N slowest operations.

        Args:
            n: Number of slowest operations to return

        Returns:
            List of TimingResult objects, sorted by duration (slowest first)

        EDUCATIONAL NOTE - Performance Bottlenecks:
        The slowest operations are often the best candidates for optimization.
        However, consider:
        - Frequency: A slow but rare operation may not matter
        - User impact: Operations users wait for matter most
        - Optimization cost: Some operations can't be sped up much

        Use this to identify where to focus optimization efforts.
        """

        sorted_timings = sorted(self.timings, key=lambda t: t.duration, reverse=True)
        return sorted_timings[:n]

    def get_operations_by_category(self) -> Dict[str, List[TimingResult]]:
        """
        Group timing results by operation name.

        Returns:
            Dictionary mapping operation names to their timing results

        Example:
            >>> by_category = monitor.get_operations_by_category()
            >>> for op_name, timings in by_category.items():
            ...     print(f"{op_name}: {len(timings)} runs")
        """

        categories: Dict[str, List[TimingResult]] = {}

        for timing in self.timings:
            if timing.operation not in categories:
                categories[timing.operation] = []
            categories[timing.operation].append(timing)

        return categories

    def generate_report(self) -> str:
        """
        Generate a human-readable performance report.

        Returns:
            Formatted string with performance statistics

        EDUCATIONAL NOTE - Performance Reporting:
        Good performance reports should:
        - Highlight important information
        - Be easy to scan visually
        - Include context (number of runs, time range)
        - Identify problems (slowest operations)
        - Suggest actions (what to optimize)
        """

        if not self.timings:
            return "No performance data collected."

        lines = []
        lines.append("=" * 70)
        lines.append("PERFORMANCE REPORT")
        lines.append("=" * 70)

        # Overall statistics
        total_time = sum(t.duration for t in self.timings)
        lines.append(f"\nTotal operations: {len(self.timings)}")
        lines.append(f"Total time: {total_time:.3f}s")

        # Per-operation statistics
        lines.append("\n" + "-" * 70)
        lines.append("OPERATIONS SUMMARY")
        lines.append("-" * 70)

        by_category = self.get_operations_by_category()

        for operation, timings in sorted(by_category.items()):
            stats = self.get_statistics(operation)
            lines.append(f"\n{operation}:")
            lines.append(f"  Runs: {stats['count']}")
            lines.append(f"  Mean: {stats['mean']:.3f}s")
            lines.append(f"  Range: {stats['min']:.3f}s - {stats['max']:.3f}s")

        # Slowest operations
        lines.append("\n" + "-" * 70)
        lines.append("SLOWEST OPERATIONS")
        lines.append("-" * 70)

        slowest = self.get_slowest_operations(5)
        for i, timing in enumerate(slowest, 1):
            lines.append(f"{i}. {timing}")

        lines.append("\n" + "=" * 70)

        return "\n".join(lines)

    def reset(self) -> None:
        """
        Clear all collected timing data.

        Useful for:
        - Starting fresh measurements
        - Memory management (if running for long periods)
        - Testing different scenarios
        """
        self.timings.clear()
        self._active_timers.clear()


def timed(operation_name: Optional[str] = None):
    """
    Decorator for automatically timing functions.

    Args:
        operation_name: Name to use for the operation (defaults to function name)

    Returns:
        Decorated function that records timing

    EDUCATIONAL NOTE - Decorators:
    Decorators are a powerful Python feature that wraps functions
    to add behavior without modifying the original code:

    @decorator
    def function():
        pass

    Is equivalent to:
        function = decorator(function)

    Common uses:
    - Timing/profiling (@timed)
    - Authentication (@login_required)
    - Caching (@lru_cache)
    - Validation (@validate_input)

    Example:
        >>> @timed("process_data")
        ... def process_large_dataset(data):
        ...     # ... processing ...
        ...     return result
        >>> result = process_large_dataset(my_data)
        [INFO] process_data completed in 1.234s
    """

    def decorator(func: Callable) -> Callable:
        op_name = operation_name or func.__name__

        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start

                # Log timing if logger is available
                try:
                    from harmonizer.utils.logging_config import HarmonizerLogger
                    logger = HarmonizerLogger.get_logger("harmonizer.performance")
                    logger.info(f"{op_name} completed in {duration:.3f}s")
                except ImportError:
                    pass

        return wrapper

    return decorator


# Global performance monitor instance
_global_monitor: Optional[PerformanceMonitor] = None


def get_global_monitor() -> PerformanceMonitor:
    """
    Get the global performance monitor instance.

    Returns:
        Global PerformanceMonitor instance

    EDUCATIONAL NOTE - Singleton Pattern:
    The singleton pattern ensures only one instance of a class exists.
    Useful for:
    - Global state (like performance monitoring)
    - Resource management (database connections)
    - Configuration
    - Logging

    We use a simple global variable here. For thread-safety,
    consider using threading.Lock.
    """

    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


# Example usage and testing
if __name__ == "__main__":
    """
    Test the performance monitoring module.
    """

    print("Testing Performance Monitoring")
    print("=" * 70)

    monitor = PerformanceMonitor()

    # Simulate some operations
    import random

    for _ in range(5):
        monitor.start_timer("scan_os")
        time.sleep(random.uniform(0.01, 0.05))
        monitor.stop_timer("scan_os")

    for _ in range(3):
        monitor.start_timer("scan_python")
        time.sleep(random.uniform(0.02, 0.08))
        monitor.stop_timer("scan_python")

    for _ in range(2):
        monitor.start_timer("scan_dependencies")
        time.sleep(random.uniform(0.05, 0.15))
        monitor.stop_timer("scan_dependencies")

    # Generate report
    print(monitor.generate_report())

    # Test decorator
    print("\nTesting decorator:")

    @timed("example_function")
    def example_operation():
        time.sleep(0.1)
        return "Done"

    result = example_operation()
    print(f"Result: {result}")

    print("\n" + "=" * 70)
