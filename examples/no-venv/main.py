"""
Sample application that should run in a virtual environment.

Running without a venv is not recommended for production projects.
"""

import sys
import os


def main():
    """Main application entry point."""
    print("Application running without virtual environment")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")

    # Check if in venv
    in_venv = hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )

    if in_venv:
        print("✓ Running in virtual environment")
    else:
        print("⚠ NOT running in virtual environment!")
        print("  Recommendation: Create and activate a venv")


if __name__ == "__main__":
    main()
