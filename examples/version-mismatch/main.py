"""
Sample application using Python 3.9+ features.

This demonstrates version-specific syntax and features.
"""

import sys
from typing import Optional


def greet(name: str) -> str:
    """Greet a person by name.

    Uses modern type hints available in Python 3.9+
    """
    # Python 3.9+ allows using dict instead of Dict from typing
    user_data: dict[str, str] = {"name": name, "greeting": f"Hello, {name}!"}

    return user_data["greeting"]


def check_python_version() -> None:
    """Check if Python version meets requirements."""
    version = sys.version_info

    print(f"Python version: {version.major}.{version.minor}.{version.micro}")

    if version >= (3, 9):
        print("✓ Python version is compatible (>=3.9)")
    else:
        print("✗ Python version too old! Requires >=3.9")
        print(f"  Current: {version.major}.{version.minor}")
        print("  Please upgrade Python")


def main():
    """Main application entry point."""
    check_python_version()

    # Use the greeting function
    message = greet("Developer")
    print(message)

    # Demonstrate Python 3.9+ features
    # Union types with | operator (Python 3.10+)
    # Uncomment to test with Python 3.10+:
    # def process(value: int | str) -> str:
    #     return str(value)


if __name__ == "__main__":
    main()
