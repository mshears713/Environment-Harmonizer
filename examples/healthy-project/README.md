# Healthy Project Example

This example demonstrates a well-configured Python project with no environment issues.

## Environment State

- **Virtual Environment**: Present and active (venv)
- **Python Version**: Compatible with requirements
- **Dependencies**: All installed
- **Configuration**: Proper setup

## Files

- `requirements.txt`: Project dependencies
- `.harmonizer.json`: Configuration file
- `main.py`: Sample application

## Expected Scan Results

When running `harmonizer` in this directory:

```
✓ No critical issues detected
✓ Virtual environment active
✓ All dependencies installed
✓ Python version compatible
```

## Usage

```bash
# Scan this project
harmonizer

# Should show all green/passing checks
# Exit code: 0 (success)
```

## What This Teaches

- What a healthy Python environment looks like
- Expected output when everything is configured correctly
- Baseline for comparing problematic environments
