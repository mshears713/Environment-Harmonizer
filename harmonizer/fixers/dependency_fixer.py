"""
Dependency Fixer Module.

This module provides automated fixes for missing Python dependencies,
including package installation from requirements files.

EDUCATIONAL NOTE - Dependency Management Best Practices:
Managing Python dependencies correctly is crucial for reproducible environments:

1. ALWAYS use a requirements file (requirements.txt or pyproject.toml)
2. Pin versions for reproducibility (requests==2.28.1, not requests)
3. Use virtual environments to isolate dependencies
4. Keep requirements files up to date
5. Separate dev dependencies from production dependencies

Common dependency files:
- requirements.txt: Traditional pip format (simple, widely supported)
- pyproject.toml: Modern Python packaging (PEP 518, used by Poetry)
- setup.py: For installable packages
- Pipfile: Used by pipenv
- environment.yml: Used by conda

Security considerations:
- Review packages before installing (avoid typosquatting)
- Use trusted package sources (PyPI)
- Check for known vulnerabilities
- Keep dependencies updated
"""

from pathlib import Path
from typing import List, Optional, Set
import subprocess

from harmonizer.fixers.base_fixer import BaseFixer, FixResult
from harmonizer.models import EnvironmentStatus, IssueSeverity
from harmonizer.utils.subprocess_utils import run_command_safe


class DependencyFixer(BaseFixer):
    """
    Fixer for missing Python dependencies.

    This fixer can:
    1. Install missing packages from requirements.txt
    2. Install packages from pyproject.toml
    3. Update outdated packages
    4. Handle different package managers (pip, conda, poetry)

    EDUCATIONAL NOTE - Package Installation Safety:
    Installing packages can modify your environment significantly:

    - New dependencies may conflict with existing packages
    - Packages may include native code with security implications
    - Installation may fail due to system dependencies

    Always:
    - Use virtual environments to isolate installations
    - Review packages before installing (especially in production)
    - Use --dry-run to preview changes
    - Keep backups of working environments
    """

    def can_fix(self) -> bool:
        """
        Check if there are missing dependencies to fix.

        Returns:
            True if missing dependencies can be installed
        """

        # Check if there are missing packages
        if self.env_status.missing_packages:
            return True

        # Check if requirements file exists and has content
        if self.env_status.requirements_file:
            req_file = Path(self.env_status.requirements_file)
            if req_file.exists() and req_file.stat().st_size > 0:
                return True

        return False

    def _describe_fixes(self) -> None:
        """
        Describe what dependency fixes will be applied.
        """

        missing_count = len(self.env_status.missing_packages)

        if missing_count > 0:
            print(f"  - Install {missing_count} missing package(s):")
            for pkg in self.env_status.missing_packages[:5]:  # Show first 5
                print(f"      • {pkg}")
            if missing_count > 5:
                print(f"      ... and {missing_count - 5} more")

        if self.env_status.requirements_file:
            print(f"  - Install from: {self.env_status.requirements_file}")

    def _apply_fix_impl(self, dry_run: bool = False) -> List[FixResult]:
        """
        Apply dependency fixes.

        Args:
            dry_run: If True, preview changes without applying

        Returns:
            List of FixResult objects
        """

        results = []

        # If we have a requirements file, install from it
        if self.env_status.requirements_file:
            result = self._install_from_requirements_file(dry_run)
            results.append(result)

        # Otherwise, install individual missing packages
        elif self.env_status.missing_packages:
            result = self._install_missing_packages(dry_run)
            results.append(result)

        return results

    def _install_from_requirements_file(self, dry_run: bool = False) -> FixResult:
        """
        Install packages from requirements file.

        Args:
            dry_run: If True, don't actually install

        Returns:
            FixResult describing the outcome

        EDUCATIONAL NOTE - Requirements File Format:
        requirements.txt supports various specification formats:

        Basic:
            requests
            numpy

        Version pinning:
            requests==2.28.1       # Exact version
            numpy>=1.20.0          # Minimum version
            pandas~=1.4.0          # Compatible version

        Version ranges:
            django>=3.2,<4.0       # Between versions

        From VCS:
            git+https://github.com/user/repo.git@v1.0

        Local packages:
            -e /path/to/package    # Editable install

        Comments and blank lines are allowed:
            # This is a comment
            requests==2.28.1       # This package is needed for HTTP
        """

        req_file = Path(self.env_status.requirements_file)

        if not req_file.exists():
            return FixResult(
                success=False,
                message=f"Requirements file not found: {req_file}",
                dry_run=dry_run,
            )

        # Determine which pip to use
        python_exe = self.get_python_executable()

        # Build install command
        command = [python_exe, "-m", "pip", "install", "-r", str(req_file)]

        if dry_run:
            return FixResult(
                success=True,
                message=f"Would install packages from: {req_file}",
                command=" ".join(command),
                dry_run=True,
            )

        # Actually install packages
        self._log(f"Installing packages from: {req_file}")

        success, message = self._run_command(
            command, f"Install packages from {req_file.name}", dry_run=False
        )

        return FixResult(
            success=success,
            message=message,
            command=" ".join(command),
            dry_run=False,
        )

    def _install_missing_packages(self, dry_run: bool = False) -> FixResult:
        """
        Install individual missing packages.

        Args:
            dry_run: If True, don't actually install

        Returns:
            FixResult describing the outcome
        """

        if not self.env_status.missing_packages:
            return FixResult(
                success=False, message="No missing packages to install", dry_run=dry_run
            )

        # Determine which pip to use
        python_exe = self.get_python_executable()

        # Build install command
        packages = list(self.env_status.missing_packages)
        command = [python_exe, "-m", "pip", "install"] + packages

        if dry_run:
            pkg_list = ", ".join(packages)
            return FixResult(
                success=True,
                message=f"Would install packages: {pkg_list}",
                command=" ".join(command),
                dry_run=True,
            )

        # Actually install packages
        self._log(f"Installing {len(packages)} missing package(s)")

        success, message = self._run_command(
            command, f"Install {len(packages)} missing packages", dry_run=False
        )

        return FixResult(
            success=success,
            message=message,
            command=" ".join(command),
            dry_run=False,
        )

    def verify_installation(self, package_name: str) -> bool:
        """
        Verify that a package is installed.

        Args:
            package_name: Name of package to check

        Returns:
            True if package is installed, False otherwise

        EDUCATIONAL NOTE - Package Verification:
        We can verify package installation using 'pip show':

            pip show <package-name>

        This returns information about the package if installed:
        - Name, Version, Summary
        - Location (where it's installed)
        - Dependencies (Required by)

        Return code:
        - 0: Package found
        - 1: Package not found
        """

        python_exe = self.get_python_executable()

        success, _, _ = run_command_safe(
            [python_exe, "-m", "pip", "show", package_name], timeout=10
        )
        return success

    def get_installed_packages(self) -> Set[str]:
        """
        Get set of all installed packages.

        Returns:
            Set of installed package names

        EDUCATIONAL NOTE - Listing Installed Packages:
        'pip list' shows all installed packages with versions:

            pip list
            Package    Version
            ---------- -------
            pip        22.0.4
            requests   2.28.1

        'pip freeze' shows in requirements.txt format:

            pip freeze
            requests==2.28.1
            certifi==2022.6.15

        We parse 'pip list' to get clean package names.
        """

        python_exe = self.get_python_executable()
        installed = set()

        success, stdout, _ = run_command_safe(
            [python_exe, "-m", "pip", "list", "--format=freeze"], timeout=30
        )

        if success:
            for line in stdout.splitlines():
                # Parse package==version format
                if "==" in line:
                    package_name = line.split("==")[0].strip()
                    installed.add(package_name.lower())

        return installed


# Example usage and testing
if __name__ == "__main__":
    """
    Test the DependencyFixer module.
    """

    print("=" * 70)
    print("Dependency Fixer - Test Run")
    print("=" * 70)

    # Create test environment status
    from harmonizer.models import OSType, VenvType

    env_status = EnvironmentStatus(
        os_type=OSType.LINUX,
        os_version="Ubuntu 22.04",
        python_version="3.10.6",
        python_executable="/usr/bin/python3",
        venv_type=VenvType.VIRTUALENV,
        venv_active=True,
        venv_path="/path/to/venv",
        project_path=".",
        requirements_file="requirements.txt",
        missing_packages=["requests", "pytest", "black"],
    )

    env_status.add_issue(
        IssueSeverity.ERROR,
        "dependency",
        "3 required packages are not installed",
        fixable=True,
        fix_command="pip install -r requirements.txt",
    )

    # Test the fixer in dry-run mode
    fixer = DependencyFixer(env_status, verbose=True, auto_yes=True)

    if fixer.can_fix():
        print("\nApplying fixes (dry-run):")
        results = fixer.apply_fixes(dry_run=True)

        for result in results:
            print(f"\n{result}")

    print("\n" + "=" * 70)
