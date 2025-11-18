"""
Configuration File Detection Module.

This module provides functionality to detect and analyze configuration files
commonly found in Python projects.

EDUCATIONAL NOTE - Why Config Files Matter:
Configuration files serve different purposes in development:
- .env: Environment variables (secrets, API keys)
- .gitignore: Files to exclude from version control
- .editorconfig: Code style consistency across editors
- pyproject.toml: Modern Python project configuration
- setup.cfg: Legacy Python project configuration
- pytest.ini, tox.ini: Testing configuration
- .python-version: Python version specification

Missing or misconfigured files can cause:
- Security issues (exposing secrets)
- Inconsistent code style
- Failed tests or builds
- Version compatibility problems
"""

from pathlib import Path
from typing import List, Dict, Set, Tuple


# Common configuration files in Python projects
COMMON_CONFIG_FILES = {
    # Version control
    ".gitignore": {
        "category": "version_control",
        "required": True,
        "description": "Git ignore patterns",
    },
    ".gitattributes": {
        "category": "version_control",
        "required": False,
        "description": "Git attributes for line endings and diffs",
    },

    # Python project configuration
    "pyproject.toml": {
        "category": "python_config",
        "required": False,
        "description": "Modern Python project configuration (PEP 518)",
    },
    "setup.py": {
        "category": "python_config",
        "required": False,
        "description": "Legacy Python package setup",
    },
    "setup.cfg": {
        "category": "python_config",
        "required": False,
        "description": "Python package metadata and tool configuration",
    },
    "MANIFEST.in": {
        "category": "python_config",
        "required": False,
        "description": "Package manifest for non-Python files",
    },

    # Dependency management
    "requirements.txt": {
        "category": "dependencies",
        "required": False,
        "description": "Python dependencies (pip)",
    },
    "requirements-dev.txt": {
        "category": "dependencies",
        "required": False,
        "description": "Development dependencies",
    },
    "Pipfile": {
        "category": "dependencies",
        "required": False,
        "description": "Pipenv dependency specification",
    },
    "Pipfile.lock": {
        "category": "dependencies",
        "required": False,
        "description": "Pipenv lock file",
    },
    "poetry.lock": {
        "category": "dependencies",
        "required": False,
        "description": "Poetry lock file",
    },

    # Environment
    ".env": {
        "category": "environment",
        "required": False,
        "description": "Environment variables (should not be committed!)",
    },
    ".env.example": {
        "category": "environment",
        "required": False,
        "description": "Example environment variables template",
    },

    # Python version
    ".python-version": {
        "category": "python_version",
        "required": False,
        "description": "Python version specification (pyenv)",
    },
    "runtime.txt": {
        "category": "python_version",
        "required": False,
        "description": "Python version for deployment platforms",
    },

    # Code quality
    ".editorconfig": {
        "category": "code_quality",
        "required": False,
        "description": "Editor configuration for consistent code style",
    },
    ".flake8": {
        "category": "code_quality",
        "required": False,
        "description": "Flake8 linter configuration",
    },
    ".pylintrc": {
        "category": "code_quality",
        "required": False,
        "description": "Pylint configuration",
    },
    "mypy.ini": {
        "category": "code_quality",
        "required": False,
        "description": "MyPy type checker configuration",
    },
    ".pre-commit-config.yaml": {
        "category": "code_quality",
        "required": False,
        "description": "Pre-commit hooks configuration",
    },

    # Testing
    "pytest.ini": {
        "category": "testing",
        "required": False,
        "description": "Pytest configuration",
    },
    "tox.ini": {
        "category": "testing",
        "required": False,
        "description": "Tox testing automation configuration",
    },
    ".coveragerc": {
        "category": "testing",
        "required": False,
        "description": "Coverage.py configuration",
    },

    # CI/CD
    ".travis.yml": {
        "category": "ci_cd",
        "required": False,
        "description": "Travis CI configuration",
    },
    ".gitlab-ci.yml": {
        "category": "ci_cd",
        "required": False,
        "description": "GitLab CI configuration",
    },
    "Jenkinsfile": {
        "category": "ci_cd",
        "required": False,
        "description": "Jenkins pipeline configuration",
    },

    # Docker
    "Dockerfile": {
        "category": "docker",
        "required": False,
        "description": "Docker image definition",
    },
    "docker-compose.yml": {
        "category": "docker",
        "required": False,
        "description": "Docker Compose configuration",
    },
    ".dockerignore": {
        "category": "docker",
        "required": False,
        "description": "Docker build ignore patterns",
    },

    # Documentation
    "README.md": {
        "category": "documentation",
        "required": True,
        "description": "Project documentation",
    },
    "LICENSE": {
        "category": "documentation",
        "required": False,
        "description": "Project license",
    },
    "CHANGELOG.md": {
        "category": "documentation",
        "required": False,
        "description": "Project changelog",
    },
    "CONTRIBUTING.md": {
        "category": "documentation",
        "required": False,
        "description": "Contribution guidelines",
    },
}


def detect_config_files(project_path: str) -> Dict[str, any]:
    """
    Detect configuration files in a project directory.

    Args:
        project_path: Path to the project directory

    Returns:
        Dictionary containing:
            - found: List of found config files
            - missing_required: List of missing required config files
            - missing_recommended: List of missing recommended config files
            - by_category: Config files organized by category

    EDUCATIONAL NOTE - Configuration Detection:
    We check for common configuration files that:
    1. Define project structure and metadata
    2. Manage dependencies
    3. Configure development tools
    4. Set up testing and CI/CD
    5. Specify Python version requirements

    This helps identify incomplete project setups.

    Example:
        >>> results = detect_config_files("/path/to/project")
        >>> print(f"Found: {results['found']}")
        Found: ['.gitignore', 'README.md', 'requirements.txt']
    """

    project = Path(project_path)

    found = []
    missing_required = []
    missing_recommended = []
    by_category = {}

    # Check each known config file
    for filename, info in COMMON_CONFIG_FILES.items():
        file_path = project / filename
        category = info["category"]

        # Initialize category if not exists
        if category not in by_category:
            by_category[category] = {"found": [], "missing": []}

        if file_path.exists():
            found.append(filename)
            by_category[category]["found"].append(filename)
        else:
            # File doesn't exist
            if info["required"]:
                missing_required.append(filename)
            else:
                missing_recommended.append(filename)

            by_category[category]["missing"].append(filename)

    # Also check for .github directory (GitHub Actions)
    github_dir = project / ".github"
    if github_dir.exists() and github_dir.is_dir():
        workflows_dir = github_dir / "workflows"
        if workflows_dir.exists():
            found.append(".github/workflows")
            if "ci_cd" not in by_category:
                by_category["ci_cd"] = {"found": [], "missing": []}
            by_category["ci_cd"]["found"].append(".github/workflows")

    return {
        "found": found,
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
        "by_category": by_category,
        "total_found": len(found),
        "total_missing": len(missing_required) + len(missing_recommended),
    }


def check_gitignore_completeness(project_path: str) -> Tuple[bool, List[str]]:
    """
    Check if .gitignore contains important Python patterns.

    Args:
        project_path: Path to the project directory

    Returns:
        Tuple of (is_complete, missing_patterns)

    EDUCATIONAL NOTE - .gitignore Patterns:
    A good Python .gitignore should include:
    - __pycache__/ (compiled Python files)
    - *.pyc, *.pyo, *.pyd (compiled bytecode)
    - .env (environment variables with secrets)
    - venv/, env/ (virtual environments)
    - .pytest_cache/ (test artifacts)
    - *.egg-info/ (package build artifacts)

    Missing these can lead to:
    - Bloated repositories
    - Exposed secrets
    - Platform-specific files in version control
    """

    important_patterns = [
        "__pycache__",
        "*.pyc",
        ".env",
        "venv/",
        "*.egg-info",
        ".pytest_cache",
    ]

    gitignore_path = Path(project_path) / ".gitignore"

    if not gitignore_path.exists():
        return False, important_patterns

    try:
        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read().lower()

        missing = []
        for pattern in important_patterns:
            # Check if pattern or similar variation exists
            pattern_lower = pattern.lower()
            if pattern_lower not in content:
                missing.append(pattern)

        is_complete = len(missing) == 0
        return is_complete, missing

    except (FileNotFoundError, PermissionError, UnicodeDecodeError):
        return False, important_patterns


def check_env_file_in_gitignore(project_path: str) -> bool:
    """
    Check if .env file exists but is properly ignored by git.

    Args:
        project_path: Path to the project directory

    Returns:
        True if .env is properly ignored, False if it's at risk

    EDUCATIONAL NOTE - .env File Security:
    .env files often contain sensitive information:
    - API keys
    - Database passwords
    - Secret tokens

    CRITICAL: .env files should ALWAYS be in .gitignore!

    If .env exists but isn't in .gitignore, secrets could be
    accidentally committed to version control and exposed publicly.

    SECURITY GOTCHA:
    Even if you add .env to .gitignore later, previously committed
    versions remain in git history! Use tools like git-filter-branch
    or BFG Repo-Cleaner to remove them from history if this happens.
    """

    project = Path(project_path)
    env_file = project / ".env"
    gitignore = project / ".gitignore"

    # If .env doesn't exist, no risk
    if not env_file.exists():
        return True

    # If .env exists but no .gitignore, that's a problem
    if not gitignore.exists():
        return False

    # Check if .gitignore contains .env pattern
    try:
        with open(gitignore, "r", encoding="utf-8") as f:
            content = f.read()
            return ".env" in content

    except (FileNotFoundError, PermissionError, UnicodeDecodeError):
        return False


def get_recommended_config_files(project_path: str) -> List[Tuple[str, str]]:
    """
    Get recommended config files that should be added to the project.

    Args:
        project_path: Path to the project directory

    Returns:
        List of (filename, reason) tuples

    EDUCATIONAL NOTE - Progressive Configuration:
    Not all projects need all config files. Recommendations depend on:
    - Project size and complexity
    - Number of contributors
    - Whether it's a library or application
    - Deployment requirements

    We provide context-aware recommendations based on what's already present.
    """

    project = Path(project_path)
    recommendations = []

    # Check for .gitignore
    if not (project / ".gitignore").exists():
        recommendations.append(
            (".gitignore", "Prevents committing unwanted files to version control")
        )

    # Check for README.md
    if not (project / "README.md").exists():
        recommendations.append(
            ("README.md", "Essential documentation for understanding the project")
        )

    # Check for .editorconfig if multi-contributor project
    if not (project / ".editorconfig").exists():
        if (project / ".git").exists():  # Git repository
            recommendations.append(
                (".editorconfig", "Ensures consistent code style across different editors")
            )

    # Check for .env.example if .env exists
    if (project / ".env").exists() and not (project / ".env.example").exists():
        recommendations.append(
            (".env.example", "Template for required environment variables (without secrets)")
        )

    # Check for testing config if tests exist
    tests_dir = project / "tests"
    if tests_dir.exists() and not (project / "pytest.ini").exists():
        recommendations.append(
            ("pytest.ini", "Configure pytest behavior and test discovery")
        )

    # Check for pre-commit if git repo
    if (project / ".git").exists() and not (project / ".pre-commit-config.yaml").exists():
        recommendations.append(
            (".pre-commit-config.yaml", "Automated code quality checks before commits")
        )

    return recommendations


def detect_config_issues(project_path: str) -> List[Dict[str, str]]:
    """
    Detect configuration-related issues in the project.

    Args:
        project_path: Path to the project directory

    Returns:
        List of issue dictionaries with 'severity', 'message', 'category'

    EDUCATIONAL NOTE - Configuration Issues:
    Common configuration problems:
    1. Missing .gitignore (leads to bloated repos)
    2. .env not in .gitignore (security risk!)
    3. Missing .editorconfig (inconsistent code style)
    4. No requirements.txt (unclear dependencies)
    5. Missing README.md (poor documentation)
    """

    issues = []

    # Check for missing .gitignore
    if not (Path(project_path) / ".gitignore").exists():
        issues.append({
            "severity": "warning",
            "message": "No .gitignore file found - unwanted files may be committed",
            "category": "config",
        })
    else:
        # Check .gitignore completeness
        is_complete, missing = check_gitignore_completeness(project_path)
        if not is_complete:
            issues.append({
                "severity": "info",
                "message": f".gitignore missing important patterns: {', '.join(missing[:3])}",
                "category": "config",
            })

    # Check for .env security issue
    if not check_env_file_in_gitignore(project_path):
        issues.append({
            "severity": "error",
            "message": ".env file exists but is NOT in .gitignore - SECURITY RISK!",
            "category": "security",
        })

    # Check for missing README
    readme_files = ["README.md", "README.rst", "README.txt", "README"]
    has_readme = any((Path(project_path) / readme).exists() for readme in readme_files)

    if not has_readme:
        issues.append({
            "severity": "warning",
            "message": "No README file found - project lacks documentation",
            "category": "config",
        })

    # Check for dependency file
    dep_files = ["requirements.txt", "pyproject.toml", "Pipfile", "setup.py"]
    has_deps = any((Path(project_path) / dep).exists() for dep in dep_files)

    if not has_deps:
        issues.append({
            "severity": "warning",
            "message": "No dependency file found (requirements.txt, pyproject.toml, etc.)",
            "category": "config",
        })

    return issues


# Example usage and testing
if __name__ == "__main__":
    """
    Test the config file detection module.
    """

    print("=" * 60)
    print("Config File Detection Module - Test Run")
    print("=" * 60)

    # Test on current directory
    results = detect_config_files(".")

    print(f"\nFound Config Files: {results['total_found']}")
    for file in sorted(results['found']):
        print(f"  ✓ {file}")

    print(f"\nMissing Required Files: {len(results['missing_required'])}")
    for file in results['missing_required']:
        print(f"  ✗ {file}")

    print(f"\nConfiguration by Category:")
    for category, files in sorted(results['by_category'].items()):
        if files['found']:
            print(f"  {category}: {', '.join(files['found'])}")

    # Check for issues
    issues = detect_config_issues(".")
    if issues:
        print(f"\nConfiguration Issues: {len(issues)}")
        for issue in issues:
            print(f"  [{issue['severity'].upper()}] {issue['message']}")

    # Check recommendations
    recommendations = get_recommended_config_files(".")
    if recommendations:
        print(f"\nRecommended Files to Add:")
        for filename, reason in recommendations:
            print(f"  • {filename}: {reason}")

    print("\n" + "=" * 60)
