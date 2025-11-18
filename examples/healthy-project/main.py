"""
Sample application for healthy-project example.

This demonstrates a basic Python application in a well-configured environment.
"""

import sys
import platform


def main():
    """Main application entry point."""
    print("Hello from a healthy Python environment!")
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.system()}")

    # Simple functionality
    numbers = [1, 2, 3, 4, 5]
    total = sum(numbers)
    print(f"Sum of {numbers} = {total}")


if __name__ == "__main__":
    main()
