"""
Configuration File Fixer Module.

This module provides automated fixes for missing or outdated configuration files,
helping maintain best practices in Python projects.

EDUCATIONAL NOTE - Configuration Files in Python Projects:
Well-configured projects use various configuration files for different purposes:

Essential files:
- .gitignore: Prevent committing generated/sensitive files
- requirements.txt: Specify project dependencies
- README.md: Project documentation
- setup.py or pyproject.toml: Package metadata

Best practice files:
- .editorconfig: Consistent coding style across editors
- .flake8 or pyproject.toml: Linter configuration
- .pre-commit-config.yaml: Git pre-commit hooks
- .env.example: Template for environment variables

Why configuration matters:
1. Consistency: Same behavior across different environments
2. Collaboration: Team members use same settings
3. Automation: Tools work predictably
4. Documentation: Self-documenting project standards
"""

from pathlib import Path
from typing import List, Dict, Optional
import datetime

from harmonizer.fixers.base_fixer import BaseFixer, FixResult
from harmonizer.models import EnvironmentStatus


class ConfigFixer(BaseFixer):
    """
    Fixer for missing or outdated configuration files.

    This fixer can:
    1. Create missing .gitignore with Python-specific patterns
    2. Create template .editorconfig for consistent coding style
    3. Update outdated configuration files
    4. Suggest recommended configuration files

    EDUCATIONAL NOTE - When to Create Config Files Automatically:
    Automatic configuration creation should be conservative:

    SAFE to auto-create:
    - .gitignore: Prevents accidental commits (low risk)
    - .editorconfig: Just formatting preferences (low risk)

    CAREFUL with auto-creating:
    - .env: May contain secrets (ask first)
    - pyproject.toml: Complex configuration (may conflict)
    - CI/CD configs: Project-specific (provide templates)

    NEVER auto-create without permission:
    - Anything that modifies build process
    - Files that might overwrite existing work
    - Security-sensitive configurations
    """

    # Template configurations
    GITIGNORE_TEMPLATE = """# Python Environment Harmonizer - Generated .gitignore
# Generated on: {timestamp}

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environments
venv/
env/
ENV/
.venv
.env

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.hypothesis/

# Jupyter Notebook
.ipynb_checkpoints

# Environment variables
.env
.env.local

# Distribution / packaging
*.manifest
*.spec

# Logs
*.log
logs/

# Database
*.db
*.sqlite3
"""

    EDITORCONFIG_TEMPLATE = """# Environment Harmonizer - Generated .editorconfig
# Generated on: {timestamp}
# EditorConfig helps maintain consistent coding styles
# https://editorconfig.org

root = true

# Default settings for all files
[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

# Python files
[*.py]
indent_style = space
indent_size = 4
max_line_length = 100

# YAML files
[*.{yml,yaml}]
indent_style = space
indent_size = 2

# JSON files
[*.json]
indent_style = space
indent_size = 2

# Markdown
[*.md]
trim_trailing_whitespace = false

# Makefile
[Makefile]
indent_style = tab
"""

    def can_fix(self) -> bool:
        """
        Check if there are configuration file issues to fix.

        Returns:
            True if config files can be created or updated
        """

        project_path = Path(self.env_status.project_path)

        # Check for missing essential files
        essential_files = [".gitignore"]

        for file in essential_files:
            if not (project_path / file).exists():
                return True

        return False

    def _describe_fixes(self) -> None:
        """
        Describe what configuration fixes will be applied.
        """

        project_path = Path(self.env_status.project_path)

        missing_files = []

        if not (project_path / ".gitignore").exists():
            missing_files.append(".gitignore")

        if not (project_path / ".editorconfig").exists():
            missing_files.append(".editorconfig (optional)")

        if missing_files:
            print(f"  - Create missing configuration files:")
            for file in missing_files:
                print(f"      • {file}")

    def _apply_fix_impl(self, dry_run: bool = False) -> List[FixResult]:
        """
        Apply configuration file fixes.

        Args:
            dry_run: If True, preview changes without applying

        Returns:
            List of FixResult objects
        """

        results = []
        project_path = Path(self.env_status.project_path)

        # Create .gitignore if missing
        gitignore_path = project_path / ".gitignore"
        if not gitignore_path.exists():
            result = self._create_gitignore(gitignore_path, dry_run)
            results.append(result)

        # Offer to create .editorconfig if missing
        editorconfig_path = project_path / ".editorconfig"
        if not editorconfig_path.exists():
            result = self._create_editorconfig(editorconfig_path, dry_run)
            results.append(result)

        return results

    def _create_gitignore(
        self, gitignore_path: Path, dry_run: bool = False
    ) -> FixResult:
        """
        Create a .gitignore file with Python-specific patterns.

        Args:
            gitignore_path: Path where .gitignore should be created
            dry_run: If True, don't actually create the file

        Returns:
            FixResult describing the outcome

        EDUCATIONAL NOTE - .gitignore Patterns:
        .gitignore tells Git which files to ignore. Patterns can include:

        Wildcards:
            *.pyc           # All files ending in .pyc
            __pycache__/    # Directory and its contents
            *.py[cod]       # .pyc, .pyo, .pyd files

        Negation:
            !important.log  # Don't ignore this file

        Directory-specific:
            /build/         # Only in root
            **/logs/        # In any directory

        Why ignore files:
        - Build artifacts: Can be regenerated
        - Virtual environments: Large, project-specific
        - IDE settings: Personal preferences
        - Secrets: .env files with API keys
        - Cache files: Temporary data
        """

        if dry_run:
            return FixResult(
                success=True,
                message=f"Would create .gitignore at: {gitignore_path}",
                dry_run=True,
            )

        try:
            # Generate content with timestamp
            content = self.GITIGNORE_TEMPLATE.format(
                timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            # Write the file
            gitignore_path.write_text(content)

            self._log(f"Created .gitignore: {gitignore_path}")

            return FixResult(
                success=True,
                message=f"Created .gitignore with Python-specific patterns",
                command=str(gitignore_path),
                dry_run=False,
            )

        except (IOError, PermissionError) as e:
            return FixResult(
                success=False,
                message=f"Failed to create .gitignore: {str(e)}",
                dry_run=False,
            )

    def _create_editorconfig(
        self, editorconfig_path: Path, dry_run: bool = False
    ) -> FixResult:
        """
        Create an .editorconfig file for consistent coding style.

        Args:
            editorconfig_path: Path where .editorconfig should be created
            dry_run: If True, don't actually create the file

        Returns:
            FixResult describing the outcome

        EDUCATIONAL NOTE - EditorConfig:
        EditorConfig helps maintain consistent coding styles across
        different editors and IDEs. It's supported by:
        - VS Code (with extension)
        - PyCharm/IntelliJ (native)
        - Sublime Text (with plugin)
        - Vim/Emacs (with plugins)
        - Many others

        Common settings:
        - indent_style: space or tab
        - indent_size: number of columns
        - end_of_line: lf, cr, or crlf
        - charset: utf-8, latin1, etc.
        - trim_trailing_whitespace: true or false
        - insert_final_newline: true or false

        Benefits:
        - Consistent formatting across team
        - Reduces diff noise from formatting changes
        - No need to configure each editor manually
        - Works with any editor that has support
        """

        if dry_run:
            return FixResult(
                success=True,
                message=f"Would create .editorconfig at: {editorconfig_path}",
                dry_run=True,
            )

        try:
            # Generate content with timestamp
            content = self.EDITORCONFIG_TEMPLATE.format(
                timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            # Write the file
            editorconfig_path.write_text(content)

            self._log(f"Created .editorconfig: {editorconfig_path}")

            return FixResult(
                success=True,
                message=f"Created .editorconfig for consistent coding style",
                command=str(editorconfig_path),
                dry_run=False,
            )

        except (IOError, PermissionError) as e:
            return FixResult(
                success=False,
                message=f"Failed to create .editorconfig: {str(e)}",
                dry_run=False,
            )


# Example usage and testing
if __name__ == "__main__":
    """
    Test the ConfigFixer module.
    """

    print("=" * 70)
    print("Configuration Fixer - Test Run")
    print("=" * 70)

    # Create test environment status
    from harmonizer.models import OSType, VenvType, IssueSeverity

    env_status = EnvironmentStatus(
        os_type=OSType.LINUX,
        os_version="Ubuntu 22.04",
        python_version="3.10.6",
        python_executable="/usr/bin/python3",
        venv_type=VenvType.VIRTUALENV,
        venv_active=True,
        project_path=".",
    )

    env_status.add_issue(
        IssueSeverity.INFO,
        "config",
        "Missing .gitignore file",
        fixable=True,
        fix_command="Create .gitignore",
    )

    # Test the fixer in dry-run mode
    fixer = ConfigFixer(env_status, verbose=True, auto_yes=True)

    if fixer.can_fix():
        print("\nApplying fixes (dry-run):")
        results = fixer.apply_fixes(dry_run=True)

        for result in results:
            print(f"\n{result}")

    print("\n" + "=" * 70)
