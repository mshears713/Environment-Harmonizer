# No Virtual Environment Example

This example demonstrates a project without a virtual environment.

## Environment State

- **Virtual Environment**: NOT PRESENT
- **Python Version**: Using system Python
- **Dependencies**: Listed but should be in venv
- **Configuration**: Needs venv setup

## Files

- `requirements.txt`: Project dependencies
- `main.py`: Sample application
- **Missing**: No venv/, env/, or .venv/ directory

## Expected Scan Results

When running `harmonizer` in this directory:

```
⚠ No virtual environment detected

Detected environment: None
Recommended: Create a virtual environment to isolate dependencies

Suggested fix:
  python -m venv env
  source env/bin/activate  # Linux/macOS
  # or
  .\env\Scripts\activate  # Windows
  pip install -r requirements.txt
```

## Usage

```bash
# Scan to detect missing venv
harmonizer

# Preview venv creation
harmonizer --fix --dry-run

# Create and activate venv (manual step may be required)
harmonizer --fix
```

## What This Teaches

- Why virtual environments are important
- How harmonizer detects missing venvs
- Different venv types (venv, virtualenv, conda)
- Best practices for dependency isolation

## Manual Setup

To manually create a virtual environment:

```bash
# Create venv
python -m venv env

# Activate it
source env/bin/activate  # Linux/macOS
# or
.\env\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Now scan again
harmonizer
```
