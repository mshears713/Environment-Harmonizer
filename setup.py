"""
Setup script for Environment Harmonizer.

This script configures the package for installation using pip.

EDUCATIONAL NOTE - setup.py:
setup.py is the traditional way to configure Python packages. It defines:
- Package metadata (name, version, author, etc.)
- Dependencies
- Entry points (CLI commands)
- Package data and resources

Modern alternative: pyproject.toml (PEP 518)
We use setup.py here for compatibility and educational clarity.

Installation methods:
    pip install .                # Install from current directory
    pip install -e .             # Install in development/editable mode
    python setup.py install      # Traditional installation (not recommended)
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read version from package
version = "0.1.0"

setup(
    # Package metadata
    name="environment-harmonizer",
    version=version,
    author="Environment Harmonizer Team",
    author_email="",
    description="A tool to detect and fix development environment inconsistencies",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/environment-harmonizer/environment-harmonizer",
    project_urls={
        "Bug Tracker": "https://github.com/environment-harmonizer/environment-harmonizer/issues",
        "Documentation": "https://github.com/environment-harmonizer/environment-harmonizer",
        "Source Code": "https://github.com/environment-harmonizer/environment-harmonizer",
    },
    # Package discovery
    packages=find_packages(exclude=["tests", "tests.*", "docs", "examples"]),
    # Python version requirement
    python_requires=">=3.7",
    # Dependencies
    install_requires=[
        # Using only standard library - no external dependencies!
    ],
    # Development dependencies (install with: pip install -e ".[dev]")
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.1.0",
            "mypy>=1.5.0",
        ],
    },
    # CLI entry points
    entry_points={
        "console_scripts": [
            "harmonizer=harmonizer.cli:main",
        ],
    },
    # Package classifiers (for PyPI)
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "Topic :: System :: Installation/Setup",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    # Keywords for PyPI search
    keywords="environment development tools python virtualenv conda diagnostics",
    # License
    license="MIT",
)
