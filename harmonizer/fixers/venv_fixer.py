"""
Virtual Environment Fixer Module.

This module provides automated fixes for virtual environment issues,
including creation and activation guidance.

EDUCATIONAL NOTE - Virtual Environment Activation Limitations:
One important limitation: we CANNOT directly activate a virtual environment
from within a running Python process. Here's why:

1. Activation modifies the current shell's environment variables
2. subprocess runs in a separate process - changes don't affect parent shell
3. Python can't modify its parent process's environment

What we CAN do:
- Create virtual environments
- Provide activation instructions
- Detect if activation is needed
- Verify virtual environment integrity

What we CANNOT do:
- Activate venv directly (user must run activation command)
- Modify parent shell's PATH
- Change environment variables of calling process

Solution: Provide clear instructions and activation commands for users.
"""

from pathlib import Path
from typing import List, Optional
import subprocess
import sys
import platform

from harmonizer.fixers.base_fixer import BaseFixer, FixResult
from harmonizer.models import EnvironmentStatus, VenvType, IssueSeverity
from harmonizer.utils.subprocess_utils import run_command_safe


class VenvFixer(BaseFixer):
    """
    Fixer for virtual environment issues.

    This fixer can:
    1. Create missing virtual environments
    2. Provide activation instructions
    3. Verify virtual environment integrity
    4. Suggest appropriate venv type based on project

    EDUCATIONAL NOTE - Choosing the Right Virtual Environment:
    Different project types benefit from different venv tools:

    - Standard Python projects: venv or virtualenv
      Simple, lightweight, built-in (Python 3.3+)

    - Data science/scientific computing: conda
      Handles non-Python dependencies (C libraries, system tools)

    - Modern Python applications: poetry
      Sophisticated dependency management, deterministic builds

    - Simple dependency management: pipenv
      Combines pip and virtualenv, uses Pipfile

    This fixer defaults to standard venv as it requires no external tools.
    """

    def can_fix(self) -> bool:
        """
        Check if there are virtual environment issues to fix.

        Returns:
            True if venv issues can be fixed
        """

        # Check if venv is missing or not active
        if self.env_status.venv_type == VenvType.NONE:
            return True

        if not self.env_status.venv_active:
            return True

        return False

    def _describe_fixes(self) -> None:
        """
        Describe what virtual environment fixes will be applied.
        """

        if self.env_status.venv_type == VenvType.NONE:
            print("  - Create a new virtual environment (venv)")
        elif not self.env_status.venv_active:
            print(
                f"  - Provide activation instructions for {self.env_status.venv_type.value}"
            )

    def _apply_fix_impl(self, dry_run: bool = False) -> List[FixResult]:
        """
        Apply virtual environment fixes.

        Args:
            dry_run: If True, preview changes without applying

        Returns:
            List of FixResult objects
        """

        results = []

        # Case 1: No virtual environment exists
        if self.env_status.venv_type == VenvType.NONE:
            result = self._create_venv(dry_run)
            results.append(result)

            # If creation succeeded, provide activation instructions
            if result.success:
                activation_result = self._provide_activation_instructions(
                    result.command or "venv", dry_run
                )
                results.append(activation_result)

        # Case 2: Virtual environment exists but not active
        elif not self.env_status.venv_active:
            venv_path = self.env_status.venv_path or self._find_venv_path()
            if venv_path:
                activation_result = self._provide_activation_instructions(
                    venv_path, dry_run
                )
                results.append(activation_result)
            else:
                results.append(
                    FixResult(
                        success=False,
                        message="Virtual environment detected but path not found",
                        dry_run=dry_run,
                    )
                )

        return results

    def _create_venv(self, dry_run: bool = False) -> FixResult:
        """
        Create a new virtual environment.

        Args:
            dry_run: If True, don't actually create the venv

        Returns:
            FixResult describing the outcome

        EDUCATIONAL NOTE - Virtual Environment Creation:
        Python 3.3+ includes venv module (built-in, no installation needed):
            python -m venv <directory>

        This creates:
        - bin/ or Scripts/ directory with Python executable
        - lib/ or Lib/ directory for installed packages
        - pyvenv.cfg configuration file

        Alternative (requires installation):
            virtualenv <directory>

        Virtualenv has more features but requires separate installation.
        We use venv for maximum compatibility.
        """

        project_path = Path(self.env_status.project_path)
        venv_path = project_path / "venv"

        # Check if venv directory already exists
        if venv_path.exists():
            return FixResult(
                success=False,
                message=f"Directory already exists: {venv_path}",
                dry_run=dry_run,
            )

        # Determine Python executable to use
        python_exe = self.env_status.python_executable or sys.executable

        # Create command
        command = [python_exe, "-m", "venv", str(venv_path)]

        if dry_run:
            return FixResult(
                success=True,
                message=f"Would create virtual environment at: {venv_path}",
                command=str(venv_path),
                dry_run=True,
            )

        # Actually create the venv
        self._log(f"Creating virtual environment at: {venv_path}")

        success, stdout, stderr = run_command_safe(command, timeout=60)

        if success:
            return FixResult(
                success=True,
                message=f"Created virtual environment at: {venv_path}",
                command=str(venv_path),
                dry_run=False,
            )
        else:
            error_msg = stderr.strip() if stderr else "Unknown error"
            return FixResult(
                success=False,
                message=f"Failed to create venv: {error_msg}",
                dry_run=False,
            )

    def _provide_activation_instructions(
        self, venv_path: str, dry_run: bool = False
    ) -> FixResult:
        """
        Provide instructions for activating the virtual environment.

        Args:
            venv_path: Path to virtual environment
            dry_run: If True, this is a dry-run

        Returns:
            FixResult with activation instructions

        EDUCATIONAL NOTE - Shell-Specific Activation:
        Different shells require different activation commands:

        Bash/Zsh (Linux, macOS, WSL):
            source venv/bin/activate

        Fish shell:
            source venv/bin/activate.fish

        Windows Command Prompt (cmd.exe):
            venv\\Scripts\\activate.bat

        Windows PowerShell:
            venv\\Scripts\\Activate.ps1
            (May require: Set-ExecutionPolicy RemoteSigned)

        The activation script modifies:
        - PATH: Prepends venv's bin/Scripts directory
        - VIRTUAL_ENV: Set to venv path
        - PS1: Modifies prompt to show venv is active
        """

        venv_dir = Path(venv_path)
        os_type = self.env_status.os_type.value

        # Determine activation command based on OS
        if "windows" in os_type.lower():
            # Windows native
            activation_cmd = f"{venv_dir}\\Scripts\\activate.bat"
            powershell_cmd = f"{venv_dir}\\Scripts\\Activate.ps1"
            instructions = f"""
To activate this virtual environment:

  Command Prompt (cmd.exe):
    {activation_cmd}

  PowerShell:
    {powershell_cmd}

  Note: If PowerShell shows execution policy error, run:
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
"""
        else:
            # Linux, macOS, WSL
            activation_cmd = f"source {venv_dir}/bin/activate"
            fish_cmd = f"source {venv_dir}/bin/activate.fish"
            instructions = f"""
To activate this virtual environment:

  Bash/Zsh:
    {activation_cmd}

  Fish shell:
    {fish_cmd}

After activation, your prompt will show (venv) and 'which python' will point to:
    {venv_dir}/bin/python
"""

        # Create the result
        message = "IMPORTANT: Virtual environment activation instructions"
        if not dry_run:
            # Print instructions immediately if not dry-run
            print("\n" + "=" * 70)
            print(instructions)
            print("=" * 70 + "\n")

        return FixResult(
            success=True,
            message=message + "\n" + instructions.strip(),
            command=activation_cmd,
            dry_run=dry_run,
        )

    def _find_venv_path(self) -> Optional[str]:
        """
        Try to find virtual environment path in project directory.

        Returns:
            Path to venv directory if found, None otherwise
        """

        project_path = Path(self.env_status.project_path)
        venv_candidates = ["venv", "env", ".venv", "virtualenv", ".env"]

        for candidate in venv_candidates:
            venv_dir = project_path / candidate
            if venv_dir.exists() and (venv_dir / "pyvenv.cfg").exists():
                return str(venv_dir)

        return None


# Example usage and testing
if __name__ == "__main__":
    """
    Test the VenvFixer module.
    """

    print("=" * 70)
    print("Virtual Environment Fixer - Test Run")
    print("=" * 70)

    # Create test environment status
    from harmonizer.models import OSType

    env_status = EnvironmentStatus(
        os_type=OSType.LINUX,
        os_version="Ubuntu 22.04",
        python_version="3.10.6",
        python_executable="/usr/bin/python3",
        venv_type=VenvType.NONE,
        venv_active=False,
        project_path=".",
    )

    env_status.add_issue(
        IssueSeverity.WARNING,
        "venv",
        "No virtual environment detected",
        fixable=True,
        fix_command="python -m venv venv",
    )

    # Test the fixer in dry-run mode
    fixer = VenvFixer(env_status, verbose=True, auto_yes=True)

    if fixer.can_fix():
        print("\nApplying fixes (dry-run):")
        results = fixer.apply_fixes(dry_run=True)

        for result in results:
            print(f"\n{result}")
            if result.message:
                print(result.message)

    print("\n" + "=" * 70)
