"""
Automated fix modules.

This package contains fixers that can automatically resolve detected
environment issues with user confirmation.

EDUCATIONAL NOTE - Fixer Architecture:
The fixer system is designed with safety and user control in mind:

1. BaseFixer: Abstract base class providing dry-run, confirmation, and safe execution
2. Concrete Fixers: Specific fixers for different types of issues
   - VenvFixer: Virtual environment activation and creation
   - DependencyFixer: Installing missing packages
   - ConfigFixer: Updating configuration files

All fixers support:
- Dry-run mode: Preview changes without applying
- User confirmation: Ask before making changes
- Detailed feedback: Show what was done and why
- Error handling: Gracefully handle failures
"""

from harmonizer.fixers.base_fixer import BaseFixer, FixResult
from harmonizer.fixers.venv_fixer import VenvFixer
from harmonizer.fixers.dependency_fixer import DependencyFixer
from harmonizer.fixers.config_fixer import ConfigFixer

__all__ = [
    "BaseFixer",
    "FixResult",
    "VenvFixer",
    "DependencyFixer",
    "ConfigFixer",
]
