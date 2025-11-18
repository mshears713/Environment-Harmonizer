"""
Main entry point for the harmonizer package.

This module allows the package to be executed as a script using:
    python -m harmonizer

EDUCATIONAL NOTE - __main__.py:
When Python runs a package as a script with -m flag, it looks for and
executes the __main__.py file. This is the standard way to make Python
packages executable from the command line.

Examples:
    python -m harmonizer                    # Scan current directory
    python -m harmonizer /path/to/project   # Scan specific project
    python -m harmonizer --help             # Show help

This pattern is used by many Python tools:
- python -m pip install package
- python -m pytest tests/
- python -m http.server 8000
- python -m venv myenv

Why use __main__.py instead of a standalone script?
1. Keeps code organized within the package
2. Avoids import path issues
3. Follows Python packaging best practices
4. Makes the package pip-installable with entry points
"""

import sys
from harmonizer.cli import main

if __name__ == "__main__":
    """
    Entry point when module is executed directly.

    This simply delegates to the main() function in cli.py,
    passing along any command-line arguments and exiting with
    the appropriate exit code.
    """
    sys.exit(main())
