# Environment Harmonizer

[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Development Status](https://img.shields.io/badge/status-alpha-orange.svg)](https://github.com/environment-harmonizer/environment-harmonizer)

**Environment Harmonizer** is a command-line and programmatic tool designed to scan a project directory and analyze the developer's environment to ensure consistency, predictability, and readiness for coding. It detects key environment characteristics such as whether the system is Windows native or WSL (Windows Subsystem for Linux), Python version mismatches, the state and type of Python virtual environments (virtualenv, conda, pip, pipx), missing dependencies, system-level quirks, and outdated configuration files. The tool generates a clear, summarized diagnostic report describing the “state of the world” within the project environment and offers optional automated environment harmonization to fix common issues.

This project is valuable because environment inconsistencies are a frequent source of developer frustration and bugs, especially across multiple collaborators or when returning to projects after some time. The tool acts as a "dev-environment butler" that ensures everything aligns before development begins, improving developer ergonomics and productivity.

**Key learning outcomes for users building or using this project include:**
- Programmatic detection of OS environment differences and Python interpreter versions
- Management and inspection of Python virtual environments in various configurations
- Building user-friendly CLI tools with detailed diagnostic output and optional corrective actions
- Designing modular code with both CLI and programmatic API accessibility

It is designed with beginners in mind, with a manageable medium complexity scope focused on diagnosing and harmonizing common environment issues without deeply changing system internals. The expected development timeline is 2–3 weeks.

---

## Quick Start

```bash
# Install
pip install -e .

# Scan current directory
harmonizer

# Preview fixes
harmonizer --fix --dry-run

# Apply fixes
harmonizer --fix

# Output as JSON
harmonizer --json --output report.json
```

---

## Installation

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/environment-harmonizer/environment-harmonizer.git
cd environment-harmonizer

# Create and activate a virtual environment (recommended)
python -m venv env
source env/bin/activate  # On Windows: .\env\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies (for testing and linting)
pip install -e ".[dev]"
```

### From PyPI (Coming Soon)

```bash
pip install environment-harmonizer
```

### Requirements

- **Python 3.7 or later**
- No external dependencies required (uses standard library only)
- Works on Windows, WSL, Linux, and macOS

---

## Usage

### Basic Usage

**Scan the current directory:**
```bash
harmonizer
```

**Scan a specific project:**
```bash
harmonizer /path/to/project
```

**Verbose output with detailed diagnostics:**
```bash
harmonizer --verbose
```

### Output Formats

**Human-readable report (default):**
```bash
harmonizer
```

**JSON output for integration with other tools:**
```bash
harmonizer --json
```

**Save report to file:**
```bash
harmonizer --output report.txt
harmonizer --json --output report.json
```

**Disable colored output:**
```bash
harmonizer --no-color
```

### Selective Scanning

**Run specific checks only:**
```bash
# Check only Python version and virtual environment
harmonizer --check python --check venv

# Available checks: os, python, venv, dependencies, config, quirks
```

**Skip specific checks:**
```bash
# Skip dependency and config checks
harmonizer --skip dependencies --skip config
```

### Automated Fixes

**Preview fixes without applying (recommended first step):**
```bash
harmonizer --fix --dry-run
```

**Apply fixes interactively (prompts for confirmation):**
```bash
harmonizer --fix
```

**Apply all fixes automatically (use with caution):**
```bash
harmonizer --fix --yes
```

### Configuration

**Create a default configuration file:**
```bash
harmonizer --init-config
```

This creates `.harmonizer.json` in the current directory with default settings.

**Use a custom configuration file:**
```bash
harmonizer --config /path/to/config.json
```

**Adjust logging level:**
```bash
harmonizer --log-level DEBUG
# Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
# Logs are written to ~/.harmonizer/logs/
```

### Common Workflows

**First-time project setup:**
```bash
# 1. Scan to identify issues
harmonizer

# 2. Preview what fixes would do
harmonizer --fix --dry-run

# 3. Apply fixes
harmonizer --fix

# 4. Verify environment is harmonized
harmonizer
```

**Daily development check:**
```bash
# Quick check before starting work
harmonizer --skip quirks
```

**CI/CD integration:**
```bash
# Generate JSON report for parsing
harmonizer --json --output environment-report.json

# Exit code: 0 if no errors, 1 if errors found
```

## Testing

### Running Tests

The project includes comprehensive unit and integration tests:

```bash
# Install development dependencies (if not already installed)
pip install -e ".[dev]"

# Run all tests
pytest

# Run tests with coverage report
pytest --cov=harmonizer --cov-report=html

# Run specific test files
pytest tests/test_os_detector.py
pytest tests/test_python_detector.py
pytest tests/test_dependency_detector.py

# Run integration tests
pytest tests/test_integration.py

# Run with verbose output
pytest -v

# Run with detailed output including print statements
pytest -v -s
```

### Test Coverage

The test suite covers:
- **OS Detection**: Windows vs WSL vs Linux vs macOS detection
- **Python Version Detection**: Interpreter version parsing and validation
- **Virtual Environment Detection**: virtualenv, conda, venv, pipx
- **Dependency Scanning**: requirements.txt and pyproject.toml parsing
- **Integration Tests**: Full scan workflows on sample projects

### Linting and Code Quality

```bash
# Code formatting with black
black harmonizer/ tests/

# Lint with flake8
flake8 harmonizer/ tests/

# Type checking with mypy
mypy harmonizer/

# Run all quality checks
black --check harmonizer/ tests/ && flake8 harmonizer/ tests/ && mypy harmonizer/
```

---

## Programmatic API Usage

Environment Harmonizer can be used programmatically in your Python scripts:

```python
from harmonizer.scanners.project_scanner import ProjectScanner
from harmonizer.reporters.text_reporter import TextReporter
from harmonizer.reporters.json_reporter import JSONReporter

# Scan a project directory
scanner = ProjectScanner("/path/to/project", verbose=True)
env_status = scanner.scan()

# Generate a text report
text_reporter = TextReporter(use_color=True)
report = text_reporter.generate(env_status)
print(report)

# Generate a JSON report
json_reporter = JSONReporter(indent=2)
json_report = json_reporter.generate(env_status)
print(json_report)

# Access specific information
print(f"OS Type: {env_status.os_type}")
print(f"Python Version: {env_status.python_version}")
print(f"Virtual Environment: {env_status.venv_type}")
print(f"Issues Found: {len(env_status.issues)}")

# Check for specific issue types
has_errors = env_status.has_errors()
has_warnings = env_status.has_warnings()

# Apply fixes programmatically
from harmonizer.fixers import VenvFixer, DependencyFixer, ConfigFixer

venv_fixer = VenvFixer(env_status, verbose=True, auto_yes=False)
if venv_fixer.can_fix():
    results = venv_fixer.apply_fixes(dry_run=False)
    for result in results:
        print(f"{'✓' if result.success else '✗'} {result.message}")
```

### Advanced API Examples

```python
# Run selective checks
scanner = ProjectScanner("/path/to/project")
env_status = scanner.scan(checks=["python", "venv", "dependencies"])

# Custom reporting
from harmonizer.models import IssueSeverity

critical_issues = [
    issue for issue in env_status.issues
    if issue.severity == IssueSeverity.ERROR
]

for issue in critical_issues:
    print(f"[{issue.category}] {issue.message}")
    if issue.fix_suggestion:
        print(f"  Fix: {issue.fix_suggestion}")

# Access detection results directly
from harmonizer.detectors.os_detector import detect_os_type
from harmonizer.detectors.python_detector import detect_python_version
from harmonizer.detectors.venv_detector import detect_venv_type

os_type = detect_os_type()
python_version = detect_python_version()
venv_info = detect_venv_type("/path/to/project")

print(f"OS: {os_type}, Python: {python_version}, Venv: {venv_info.venv_type}")
```

---

## Troubleshooting

### Common Issues

**Issue: "harmonizer: command not found"**

Solution:
```bash
# Make sure the package is installed
pip install -e .

# Verify installation
pip list | grep environment-harmonizer

# Check if the entry point is in your PATH
which harmonizer  # Linux/macOS
where harmonizer  # Windows
```

**Issue: "Permission denied" when scanning directory**

Solution:
```bash
# Check directory permissions
ls -la /path/to/project

# Run with appropriate permissions or change directory ownership
sudo chown -R $USER:$USER /path/to/project
```

**Issue: Fixes not being applied**

Solution:
```bash
# 1. Use dry-run to see what would happen
harmonizer --fix --dry-run

# 2. Check logs for detailed error messages
harmonizer --log-level DEBUG --fix

# 3. View log files
cat ~/.harmonizer/logs/harmonizer.log
```

**Issue: Virtual environment not detected**

Solution:
```bash
# Ensure you're in the project directory
cd /path/to/project

# Check if venv exists
ls -la env/ .venv/ venv/

# Manually activate and scan
source env/bin/activate  # Linux/macOS
# or
.\env\Scripts\activate  # Windows
harmonizer --verbose
```

**Issue: Dependency scanning not working**

Solution:
```bash
# Verify requirements.txt or pyproject.toml exists
ls -la requirements.txt pyproject.toml

# Check file format
cat requirements.txt

# Run with verbose output to see what's detected
harmonizer --verbose --check dependencies
```

**Issue: WSL detection incorrect**

Solution:
```bash
# Check WSL environment variables
echo $WSL_DISTRO_NAME
cat /proc/version

# Force specific check
harmonizer --check os --verbose
```

### Getting Help

**View detailed logs:**
```bash
# Set log level to DEBUG
harmonizer --log-level DEBUG

# Logs are stored in:
# Linux/macOS: ~/.harmonizer/logs/
# Windows: %USERPROFILE%\.harmonizer\logs\
```

**Report an issue:**
- GitHub Issues: https://github.com/environment-harmonizer/environment-harmonizer/issues
- Include: OS type, Python version, command run, error message, and relevant logs

**Configuration troubleshooting:**
```bash
# Create fresh config
harmonizer --init-config

# Validate config file
python -m json.tool .harmonizer.json
```

---

## Known Limitations

- **Conda environments**: Detection works, but fixes for conda environments are limited
- **System Python**: Modifying system Python is not recommended and not fully supported
- **Network dependencies**: Package installation requires internet connectivity
- **Platform-specific**: Some quirks are platform-specific and may not transfer across OS types
- **Poetry/Pipenv**: Limited support for modern Python package managers (planned for future versions)

---

## Contributing

Contributions are welcome! This project is designed to be beginner-friendly.

### Development Setup

```bash
# Clone and setup
git clone https://github.com/environment-harmonizer/environment-harmonizer.git
cd environment-harmonizer
python -m venv env
source env/bin/activate
pip install -e ".[dev]"

# Make changes
# ...

# Run tests
pytest

# Format code
black harmonizer/ tests/

# Create pull request
```

### Guidelines

- Follow existing code style (PEP 8, with black formatting)
- Add tests for new features
- Update documentation
- Include educational comments for beginner developers

---

## License

This project is licensed under the MIT License. See LICENSE file for details.

---

## Teaching Goals

### Learning Goals

- **Detect and differentiate OS environments programmatically (Windows vs WSL):** Learn how to query system characteristics and identify platform-specific conditions critical for cross-platform compatibility.
- **Inspect Python interpreter versions and virtual environments:** Understand how to query Python versions and recognize different virtual environment types (virtualenv, conda, pip, pipx).
- **Build a command-line interface with clear diagnostic output:** Gain experience constructing user-friendly CLI tools that communicate complex environment states simply and effectively.
- **Design optional automated corrective actions:** Develop skills to automate fixes safely and optionally based on diagnostics.
- **Create a programmatic API alongside CLI usage:** Learn how to provide modular usability and integrate functionality with other tools or scripts.

### Technical Goals

- Implement environment detection logic to distinguish Windows native and WSL environments.
- Develop scanning capabilities to identify Python versions, virtual environments, and missing dependencies within a given project directory.
- Build a CLI that prints summarized diagnostic reports highlighting environment inconsistencies.
- Add optional automated fixes to harmonize typical environment misconfigurations (e.g., virtual environment activation, outdated configs).

### Priority Notes

- The project scope focuses on detecting and reporting environment states with straightforward corrective actions.
- Complex dependency resolution or deep system configuration changes are out of scope.
- The tool must support Windows and WSL environments primarily and leverage minimal external dependencies.
- Suitable for beginner developers with some guidance.

---

## Technology Stack

- **Frontend:** None (CLI-only)  
  Chosen to simplify interaction focusing on terminal-based use, avoiding web or GUI overhead. A CLI input/output format aligns with typical developer workflows.  

- **Backend:** Python CLI tool  
  Python provides access to rich system and environment libraries, allowing direct inspection of Python-specific environments and OS detection logic. Python’s ease of scripting also fits the beginner-friendly and quick development timeline.  

- **Storage:** JSON files  
  Chosen for storing configuration and diagnostic reports due to human readability, easy parsing, and support in Python’s standard library.  

- **Special Libraries:** `argparse`, `pathlib`, `json`, `platform`, `subprocess`  
  These standard libraries provide core functionality for argument parsing, filesystem interaction, data serialization, platform detection, and running external commands, minimizing external dependencies and easing installation and portability.

**Alternatives Considered:**
- Alternatives such as YAML for configuration or third-party libraries for CLI (like `click`) were considered but deferred to keep external dependencies minimal and the learning curve reasonable.
- Cross-platform GUI frameworks were avoided due to complexity and less direct relevance to command-line environments.

**Framework Rationale:**  
This stack balances beginner accessibility and technical relevance to environment management, leveraging Python’s rich standard library and familiarity. It simplifies installation and usage while aligning directly with the project goals of environment detection and automated fixes.

---

## Architecture Overview

**High-Level Description:**  
The Environment Harmonizer operates as a command-line tool and optional programmatic API. It performs the following key functions:  
- Scans the target project directory for Python interpreter details, virtual environments, and configuration files.  
- Detects OS environment characteristics distinguishing Windows native from WSL.  
- Identifies missing dependencies and environment inconsistencies.  
- Compiles the gathered data into an `EnvironmentStatus` data structure.  
- Generates a human-readable or JSON-formatted diagnostic report summarizing the environment's “state of the world.”  
- Optionally applies automated fixes to harmonize detected issues.

The architecture separates detection logic, scanning processes, reporting, and fix application into modular components. The CLI layer parses user arguments, invokes scanners, and handles output display, while the programmatic API exposes scanning and fixing functions for integration.

```
+-----------------------+      +-----------------------------+
| Command Line Interface | ---> | Environment Scanner Module  |
| (argparse entry point) |      | (OS detection, Python version,
+-----------------------+      |  virtual env detection,
                                |  dependency scanning)       |
                                +-------------+---------------+
                                              |
                                              v
                                +-----------------------------+
                                | EnvironmentStatus Data Model |
                                +-------------+---------------+
                                              |
                                              v
                                +-----------------------------+
                                | Diagnostic Report Generator  |
                                +-----------------------------+
                                              |
                                              v
                                +-----------------------------+
                                | Automated Fix Module (opt.) |
                                +-----------------------------+
```

---

## Implementation Plan

### Phase 1: Foundations & Setup

**Overview:**  
Establish the project repository, basic environment, and foundational detection logic that sets up the core data structures and OS/Python environment recognition.

**Steps:**

#### Step 1: Initialize project repository with README and .gitignore
- Initialize Git repo with essential files.
- Provide inline README template comments and beginner-friendly tooltips illustrating standard README content and purpose.

#### Step 2: Set up Python virtual environment and base dependencies
- Create a Python virtual environment for the project.
- Document environment isolation importance in CLI help and README tooltips with practical examples.

#### Step 3: Create main program entry point script
- Set up the entry script connecting modules.
- Embed comments and tooltips showing flow between modules and interactive minimal examples.

#### Step 4: Define EnvironmentStatus dataclass for storing analysis results
- Declare a Python dataclass to hold scan results.
- Annotate with comments comparing dataclasses vs traditional classes.
- Add CLI tooltip explaining purpose for simplified data handling.

#### Step 5: Implement OS environment detection function
- Detect Windows vs WSL using platform and environment variables.
- Provide inline comments and CLI help illustrating detection logic and differences.

#### Step 6: Implement Python interpreter version detection
- Detect current Python interpreter versions with parsing.
- Add tooltips on why version congruence matters for compatibility.

#### Step 7: Implement virtual environment type detection logic
- Detect virtualenv, conda, pip, pipx environments.
- Add explanations and CLI help comparing virtual environment types.

#### Step 8: Create configuration loading and saving module
- Manage reading/writing JSON configuration files.
- Embed sample configs and explanations in CLI help.

#### Step 9: Implement initial CLI argument parsing
- Use `argparse` for basic command-line flags.
- Add detailed CLI help messages with usage examples.

#### Step 10: Combine detection functions into EnvironmentStatus creation
- Aggregate all detection steps into a single environment status builder.
- Add CLI tooltips demonstrating collected data summary.

---

### Phase 2: Core Functionality & Basic Integration

**Overview:**  
Enhance scanning to identify dependencies and configs, track issues, and produce clearly formatted diagnostic reports in CLI and JSON.

**Steps:**

#### Step 11: Implement scanning for outdated or missing Python dependencies
- Scan project `requirements.txt` or `pyproject.toml` and detect unmet dependencies.
- CLI help shows detected missing dependencies and example commands to list.

#### Step 12: Detect presence and status of common virtual environment config files
- Identify config files like `.env`, `conda.yml`, `pipx` config presence.
- CLI tooltips explain importance and impact of config file status.

#### Step 13: Augment EnvironmentStatus with detected issues list
- Track all detected environment issues in a structured list.
- Interactive CLI hints explain issue types with example messages.

#### Step 14: Create function to build summarized diagnostic report string
- Design formatted multi-section diagnostic report.
- CLI help with sample report output explaining each section.

#### Step 15: Implement CLI output to display formatted diagnostic report
- Print formatted report with color coding.
- Inline guidance on reading the report effectively.

#### Step 16: Add flag for JSON report output
- Support `--json` output option for integration with other tools.
- CLI documentation shows JSON example side-by-side with text reports.

#### Step 17: Implement basic command-line help and usage message
- Enhance `--help` flag with comprehensive command usage description.
- Interactive CLI examples illustrate common flag usage scenarios.

#### Step 18: Add detection logic for Python version mismatches
- Check if project Python version requirements match the detected interpreter.
- Document version mismatch implications with example output.

#### Step 19: Implement detection of WSL vs Windows peculiarities as issues
- Flag known quirks or limitations in either environment.
- Add help section describing common platform-specific issues.

#### Step 20: Refactor scanning code for clarity and modularity
- Clean and modularize scanning logic.
- CLI tooltip demonstrates maintenance advantages with before/after code snapshots.

---

### Phase 3: Additional Features & Refinements

**Overview:**  
Add enhanced detection (pipx), skeleton for automated fixes with safe dry-run mode, and improve diagnostic robustness and reporting detail.

**Steps:**

#### Step 21: Implement pipx virtual environment detection and reporting
- Detect pipx-managed packages and environments.
- CLI tooltips explain pipx usage and example detection outputs.

#### Step 22: Add automated fix function skeleton with dry-run mode
- Provide framework for fixes with dry-run that previews changes without applying.
- CLI descriptions clarify dry-run behavior vs actual fixes.

#### Step 23: Implement automatic activation of missing virtual environment
- Attempt to activate virtual environment when missing or inactive.
- CLI tooltips describe activation procedures and fallback handling.

#### Step 24: Add automatic installation for missing Python dependencies
- Automate installing detected missing packages.
- CLI prompts confirm installations with success/failure feedback.

#### Step 25: Implement correction for outdated configuration files
- Detect and update outdated configs to recommended standards.
- Include before/after config snapshots and warnings about config impact.

#### Step 26: Add CLI `--fix` flag triggering automatic fixes application
- Enable users to run diagnoses with optional fix application using `--fix`.
- Interactive CLI confirms intention and warns about automatic changes.

#### Step 27: Handle edge cases for projects without any configuration files
- Gracefully handle absence of config files with user messaging.
- CLI tips suggest next steps in missing config scenarios.

#### Step 28: Implement inspection of system PATH differences in WSL vs Windows
- Analyze system PATH to detect discrepancies impacting behavior.
- CLI help shows sample PATH outputs and explain key differences.

#### Step 29: Improve virtual environment detection robustness with subprocess checks
- Use subprocess calls for robust verification of environment status.
- CLI hints cover error handling during subprocess invocation.

#### Step 30: Refine report generation to highlight fixable issues and severity
- Tag issues by severity and fixability.
- Use color coding to convey importance within reports.

---

### Phase 4: Polish, Testing & Optimization

**Overview:**  
Improve robustness and user experience by adding exception handling, unit and integration tests, enhanced UI feedback, logging, performance measurement, and input validation.

**Steps:**

#### Step 31: Add exception handling for all subprocess calls
- Catch common subprocess errors gracefully.
- Provide clear CLI error messages with recovery suggestions.

#### Step 32: Implement unit tests for OS and Python version detection
- Write tests validating platform and Python detection logic.
- CLI test command summarizes coverage and results.

#### Step 33: Implement unit tests for dependency scanning functions
- Test dependency scanning outcomes with expected passes/fails.
- CLI-accessible test reports demonstrate result interpretation.

#### Step 34: Add integration test executing full CLI scan on sample test project
- Test end-to-end scan flow on sample projects.
- Logs accessible from CLI show full diagnostic pipeline.

#### Step 35: Improve CLI user interface with progress messages and coloring
- Add dynamic feedback on scanning progress.
- Document color conventions used to signal statuses.

#### Step 36: Implement logging with rotating file logs for debug purposes
- Log internal events with rotating file handler.
- Help section shows how to locate and interpret logs.

#### Step 37: Add time measurement to optimize slow scanning steps
- Measure durations for scanning phases.
- CLI tips identify bottlenecks and potential optimizations.

#### Step 38: Add command-line input validation and error messages
- Validate CLI inputs and provide interactive error guidance.
- Show example invalid inputs with helpful error feedback.

#### Step 39: Implement fallback scanning for unsupported OS environments
- Provide fallback scanning modes for unsupported OS.
- Explain limitations with clear CLI messaging.

#### Step 40: Add cleanup functionality for temporary files or subprocess leftovers
- Remove temporary files post-run.
- Confirm cleanup success with progress notifications.

---

### Phase 5: Documentation, Examples & Deployment Preparation

**Overview:**  
Finalize documentation, add usage examples, prepare package for distribution, and ensure quality with testing and release notes.

**Steps:**

#### Step 41: Write user guide README sections on installation and usage
- Compose detailed installation and usage instructions.
- Embed tooltips and example command snippets.

#### Step 42: Add examples folder with sample project directories and expected reports
- Provide sample projects illustrating various environment states.
- Include annotated READMEs explaining each example.

#### Step 43: Write API usage examples for programmatic access
- Document API functions with runnable code snippets.
- Add tooltips illustrating modular usage scenarios.

#### Step 44: Create setup.py for packaging the tool as a pip-installable package
- Write packaging script with versioning.
- README explains `pip install` usage.

#### Step 45: Write testing instructions and add badges to README
- Add a testing guide and sample test commands.
- Include build and test status badges with explanations.

#### Step 46: Add final code formatting and linting compliance
- Enforce style guidelines and linting.
- Document benefits and sample CLI commands.

#### Step 47: Prepare a binary executable with PyInstaller (optional)
- Document packaging steps to create executable.
- Add troubleshooting tips and usage examples.

#### Step 48: Add troubleshooting section to documentation
- Provide detailed troubleshooting guidance.
- Link CLI help to docs with error code explanations.

#### Step 49: Prepare release notes summarizing features and limitations
- Draft release notes highlighting features and known limitations.
- Provide interactive CLI access to release notes.

#### Step 50: Tag and create the first Git release
- Tag stable version and create GitHub release.
- Document release process with sample commands.

---

## Global Teaching Notes

Design the program as an interactive educational tool embedding just-in-time learning to guide beginners through environment diagnostics and tooling. Include pervasive inline comments and CLI tooltips explaining core concepts contextually with example outputs. Implement rich CLI help features with progressive disclosure to scaffold understanding of environment detection, reporting, and fixes. Emphasize clear, user-friendly messaging in reports and corrective actions to build user confidence with a learn-by-doing approach. Every feature doubles as an instructional resource aligned with the stated learning goals.

---

## Setup Instructions

1. **Python Version:**  
   Ensure Python 3.7 or later is installed.

2. **Virtual Environment Setup:**  
   - Create a new virtual environment:  
     ```bash
     python -m venv env
     ```  
   - Activate the environment:  
     - Windows: `.\env\Scripts\activate`  
     - Linux/WSL: `source env/bin/activate`

3. **Install Dependencies:**  
   Use pip to install required dependencies (standard libraries primarily):  
   ```bash
   pip install -r requirements.txt
   ```  
   *(If requirements.txt exists; otherwise dependencies are all standard.)*

4. **Configuration Files:**  
   Place any project-specific configuration files such as `requirements.txt`, `.env`, or `conda.yml` in the project root for scanning.

5. **Initial Project Structure:**  
   ```
   /environment-harmonizer
     ├── env/           # Python virtual environment (local dev)
     ├── examples/      # Sample projects and reports
     ├── harmonizer/    # Main source code
     ├── tests/         # Unit and integration tests
     ├── README.md
     ├── setup.py
     └── requirements.txt
   ```

---

## Development Workflow

- Approach phases sequentially, completing each phase’s steps before proceeding.
- Begin by setting up the repository and basic detection logic (Phase 1).
- Build core scanning and reporting features (Phase 2).
- Add automated fixes and polish detection (Phase 3).
- Harden with tests, input validation, logging, and user-interface improvements (Phase 4).
- Finalize documentation, examples, packaging, and release preparations (Phase 5).

**Testing Strategy:**  
- Write unit tests for core detection and scanning functions.
- Perform integration tests against sample projects.
- Use CLI commands to run tests and view logging/debug info.

**Debugging Tips:**  
- Enable verbose logging via CLI flags.
- Check log files in the designated log directory for subprocess errors.
- Use the dry-run mode for fixes to preview changes without applying.

**Iteration and Refinement:**  
- Continuously refactor scanning modules for clarity.
- Collect user feedback on reports and messaging.
- Update teaching aids based on developer questions or confusion.

---

## Success Metrics

- **Functional Completeness:**  
  All key detection features—OS type, Python versions, virtual environments, dependencies, config files—are implemented and integrated.

- **Learning Objectives Met:**  
  Code, documentation, and CLI help embed teaching points per learning goals.

- **Quality Criteria:**  
  Robust exception handling, well-structured modular code, responsive CLI UX with color output and progress indicators.

- **Testing Coverage:**  
  Adequate unit and integration tests covering core logic with clear pass/fail reporting.

- **User-Friendliness:**  
  Diagnostic reports are clear, comprehensive, and actionable. Fixes work correctly and safely with user confirmation.

---

## Next Steps After Completion

- **Extensions or Enhancements:**  
  Add support for additional environment managers or package ecosystems (e.g., Poetry, npm). Expand automated fix capabilities.

- **Related Projects to Try:**  
  Build a cross-language environment harmonizer. Create GUI dashboard displaying environment health.

- **Skills to Practice Next:**  
  Deepen knowledge of OS internals, containerized environment detection, advanced CLI UX design.

- **Portfolio Presentation Tips:**  
  Demonstrate the tool with recorded CLI demo. Explain teaching design choices and user interactions. Highlight problem-solving for environment inconsistency challenges.

---

# End of Document
