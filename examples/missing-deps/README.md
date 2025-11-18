# Missing Dependencies Example

This example demonstrates a project with missing Python dependencies.

## Environment State

- **Virtual Environment**: Present
- **Python Version**: Compatible
- **Dependencies**: MISSING - not all installed
- **Configuration**: requirements.txt exists but packages not installed

## Files

- `requirements.txt`: Lists required packages (some not installed)
- `main.py`: Application that imports missing packages

## Expected Scan Results

When running `harmonizer` in this directory:

```
✗ Missing dependencies detected
  - requests (required in requirements.txt)
  - click (required in requirements.txt)

Suggested fix: pip install -r requirements.txt
```

## Usage

```bash
# Scan to detect missing dependencies
harmonizer

# Preview the fix
harmonizer --fix --dry-run

# Apply the fix (install missing packages)
harmonizer --fix
```

## What This Teaches

- How harmonizer detects missing dependencies
- Difference between requirements.txt and installed packages
- Using --fix to automatically install dependencies
- Importance of keeping dependencies in sync
