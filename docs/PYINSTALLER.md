# Building Standalone Executables with PyInstaller

This guide explains how to create standalone executables of Environment Harmonizer using PyInstaller, allowing users to run the tool without installing Python or dependencies.

## Overview

PyInstaller bundles a Python application and all its dependencies into a single package, making it easy to distribute to users who may not have Python installed.

## Prerequisites

```bash
# Install PyInstaller
pip install pyinstaller

# Verify installation
pyinstaller --version
```

## Basic Build

### Build for Current Platform

```bash
# From the project root directory
pyinstaller --name harmonizer \
    --onefile \
    --console \
    harmonizer/cli.py

# The executable will be in: dist/harmonizer
```

### Build Options Explained

- `--name harmonizer`: Name of the executable
- `--onefile`: Bundle everything into a single executable file
- `--console`: Run as a console application (not GUI)
- `harmonizer/cli.py`: Entry point script

## Advanced Build Configuration

### Create a PyInstaller Spec File

```bash
# Generate spec file for customization
pyi-makespec --name harmonizer \
    --onefile \
    --console \
    harmonizer/cli.py

# Edit harmonizer.spec as needed, then build:
pyinstaller harmonizer.spec
```

### Sample harmonizer.spec

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['harmonizer/cli.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'harmonizer.detectors',
        'harmonizer.fixers',
        'harmonizer.reporters',
        'harmonizer.scanners',
        'harmonizer.utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='harmonizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

## Platform-Specific Builds

### Windows

```bash
# On Windows, build .exe
pyinstaller --name harmonizer.exe \
    --onefile \
    --console \
    harmonizer/cli.py

# Output: dist/harmonizer.exe
```

### Linux

```bash
# On Linux, build ELF binary
pyinstaller --name harmonizer \
    --onefile \
    --console \
    harmonizer/cli.py

# Output: dist/harmonizer
# Make executable:
chmod +x dist/harmonizer
```

### macOS

```bash
# On macOS, build Mach-O binary
pyinstaller --name harmonizer \
    --onefile \
    --console \
    harmonizer/cli.py

# Output: dist/harmonizer
# Make executable:
chmod +x dist/harmonizer
```

## Testing the Executable

```bash
# Run the built executable
./dist/harmonizer --help

# Test on a project
./dist/harmonizer /path/to/project

# Test all functionality
./dist/harmonizer --version
./dist/harmonizer --init-config
./dist/harmonizer --json
```

## Distribution

### Packaging for Distribution

```bash
# Create a release directory
mkdir -p release/harmonizer-v0.1.0-{platform}

# Copy executable
cp dist/harmonizer release/harmonizer-v0.1.0-linux/

# Copy documentation
cp README.md LICENSE release/harmonizer-v0.1.0-linux/

# Create archive
cd release
tar -czf harmonizer-v0.1.0-linux.tar.gz harmonizer-v0.1.0-linux/
# or
zip -r harmonizer-v0.1.0-windows.zip harmonizer-v0.1.0-windows/
```

### Release Checklist

- [ ] Test executable on clean system (without Python)
- [ ] Verify all CLI flags work
- [ ] Test scanning functionality
- [ ] Test fix functionality with --dry-run
- [ ] Check file permissions (Linux/macOS)
- [ ] Scan with antivirus (Windows)
- [ ] Create checksums (SHA256)
- [ ] Write release notes

### Generate Checksums

```bash
# Linux/macOS
shasum -a 256 dist/harmonizer > harmonizer.sha256

# Windows (PowerShell)
Get-FileHash dist/harmonizer.exe -Algorithm SHA256 > harmonizer.sha256
```

## Troubleshooting

### Issue: Import Errors

**Problem**: Module not found when running executable

**Solution**: Add hidden imports to spec file:
```python
hiddenimports=[
    'harmonizer.detectors.os_detector',
    'harmonizer.detectors.python_detector',
    # ... add other modules
]
```

### Issue: Executable Too Large

**Problem**: Executable file is very large (>50MB)

**Solutions**:
1. Use UPX compression:
   ```bash
   pyinstaller --upx-dir /path/to/upx harmonizer/cli.py
   ```

2. Exclude unnecessary modules:
   ```python
   excludes=['tkinter', 'matplotlib', 'test', 'unittest']
   ```

### Issue: Slow Startup

**Problem**: Executable takes long to start

**Solution**: Use `--onedir` instead of `--onefile`:
```bash
pyinstaller --name harmonizer --onedir harmonizer/cli.py
```
This creates a directory with the executable and dependencies, which starts faster.

### Issue: Antivirus False Positives

**Problem**: Antivirus flags executable as malware

**Solutions**:
1. Submit executable to antivirus vendors for whitelisting
2. Sign the executable with a code signing certificate
3. Include source code and build instructions with distribution

## Continuous Integration

### GitHub Actions Example

```yaml
name: Build Executables

on:
  release:
    types: [created]

jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    runs-on: ${{ matrix.os }}

    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install pyinstaller
      - name: Build executable
        run: |
          pyinstaller --name harmonizer --onefile harmonizer/cli.py
      - name: Upload artifact
        uses: actions/upload-artifact@v2
        with:
          name: harmonizer-${{ matrix.os }}
          path: dist/
```

## Limitations

- **Platform-specific**: Must build on each target platform
- **Size**: Bundled executables are larger than Python scripts
- **Updates**: Users must download new executable for updates
- **Performance**: Slightly slower startup due to unpacking

## Alternatives

- **zipapp**: Python's built-in single-file application builder (requires Python installed)
- **Docker**: Containerized distribution (cross-platform)
- **pip**: Traditional Python package installation

## Resources

- [PyInstaller Documentation](https://pyinstaller.org/)
- [PyInstaller GitHub](https://github.com/pyinstaller/pyinstaller)
- [Spec File Options](https://pyinstaller.org/en/stable/spec-files.html)

---

*Note: PyInstaller builds are optional. Most Python developers prefer using `pip install` for installation.*
