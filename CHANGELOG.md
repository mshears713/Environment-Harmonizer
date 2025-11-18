# Changelog

All notable changes to Environment Harmonizer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-18

### Added - Initial Release

#### Core Features
- **Environment Detection System**
  - OS type detection (Windows, WSL, Linux, macOS)
  - Python version detection and validation
  - Virtual environment detection (venv, virtualenv, conda, pipx)
  - Dependency scanning from requirements.txt and pyproject.toml
  - Configuration file detection and validation
  - Platform-specific quirks detection

#### Scanning Capabilities
- Comprehensive project environment scanning
- Selective check execution (--check flag)
- Check exclusion (--skip flag)
- Verbose diagnostic output
- Progress reporting during scans
- Performance monitoring and timing

#### Automated Fixes
- Virtual environment creation and activation guidance
- Missing dependency installation
- Configuration file updates and corrections
- Dry-run mode for safe preview (--dry-run)
- Interactive confirmation prompts
- Automatic mode with --yes flag

#### Reporting
- Human-readable text reports with color coding
- JSON output format for tool integration
- Severity-based issue classification (ERROR, WARNING, INFO)
- Detailed fix suggestions for each issue
- Export reports to files

#### CLI Interface
- Intuitive command-line argument parsing
- Comprehensive help messages with examples
- Multiple output formats (text, JSON)
- Configuration file support (.harmonizer.json)
- Configurable logging levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- File-based logging with rotation

#### Developer Experience
- Full programmatic API for integration
- Modular architecture with clear separation of concerns
- Extensive inline documentation and educational comments
- Unit tests for core detection modules
- Integration tests for end-to-end workflows
- Type hints throughout codebase

#### Documentation
- Comprehensive README with installation and usage guides
- API usage examples for programmatic access
- Troubleshooting section with common issues
- Example projects demonstrating various scenarios
- PyInstaller build instructions
- Contributing guidelines

### Technical Details

#### Architecture
- **Detectors**: Modular detection logic for each environment aspect
- **Scanners**: Orchestration of detection modules
- **Reporters**: Pluggable reporting formats (text, JSON)
- **Fixers**: Automated fix application with safety checks
- **Utils**: Shared utilities (logging, subprocess handling, cleanup)

#### Dependencies
- Zero external dependencies (uses Python standard library only)
- Compatible with Python 3.7+
- Cross-platform support (Windows, WSL, Linux, macOS)

#### Testing
- Unit tests for OS detection
- Unit tests for Python version detection
- Unit tests for dependency scanning
- Integration tests on sample projects
- Test coverage reporting with pytest-cov

#### Code Quality
- Black code formatting
- Flake8 linting compliance
- Type checking with mypy
- Comprehensive exception handling
- Input validation and error messages

### Known Limitations

- **Conda Environments**: Detection works, but automated fixes are limited
- **System Python**: Modifying system Python is not recommended or fully supported
- **Package Managers**: Limited support for Poetry and Pipenv (planned for future)
- **Network Operations**: Package installation requires internet connectivity
- **Platform Quirks**: Some issues are platform-specific and may not transfer

### Security

- No collection of user data or telemetry
- All operations are local to the scanned project
- Subprocess calls use safe parameter passing (no shell injection)
- Temporary files are cleaned up automatically
- Log files stored in user-specific directories

### Performance

- Fast scanning (typically <5 seconds for medium projects)
- Performance monitoring and bottleneck identification
- Efficient subprocess handling with timeouts
- Minimal memory footprint
- Incremental scanning (skip checks not needed)

### Educational Features

This release includes extensive educational content designed for beginner developers:
- Inline comments explaining core concepts
- CLI tooltips with contextual help
- Progressive disclosure of complex topics
- Real-world usage examples
- Detailed error messages with recovery suggestions

---

## [Unreleased]

### Planned Features

- Poetry and Pipenv support
- Docker environment detection
- Node.js/npm environment detection
- Database connection validation
- Environment variable validation
- Git repository status checking
- CI/CD integration helpers
- Web UI dashboard (optional)
- Plugin system for custom checks
- Configuration templates for common project types

### Under Consideration

- Remote environment scanning
- Team-wide configuration sharing
- Historical environment tracking
- Automated environment provisioning
- Integration with popular IDEs
- Shell completion scripts
- Man pages for CLI documentation

---

## Release Process

### Version Numbering

We follow Semantic Versioning (SemVer):
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backwards-compatible)
- **PATCH**: Bug fixes (backwards-compatible)

### Release Checklist

Before creating a release:
- [ ] All tests passing
- [ ] Code formatted with black
- [ ] Linting checks pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version number bumped in harmonizer/__init__.py
- [ ] Version number bumped in setup.py
- [ ] Examples tested
- [ ] README reviewed for accuracy

### Git Tags

Releases are tagged in the format: `vMAJOR.MINOR.PATCH`

Example:
```bash
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

---

## Contributing

We welcome contributions! See CONTRIBUTING.md for guidelines.

For questions or feedback:
- GitHub Issues: https://github.com/environment-harmonizer/environment-harmonizer/issues
- Discussions: https://github.com/environment-harmonizer/environment-harmonizer/discussions

---

**[0.1.0]**: Initial release - 2025-11-18
