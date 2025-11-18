# Python Version Mismatch Example

This example demonstrates a project with Python version compatibility issues.

## Environment State

- **Virtual Environment**: Present
- **Python Version**: May not match project requirements
- **Dependencies**: Compatible with different Python version
- **Configuration**: Specifies Python 3.9+ requirement

## Files

- `requirements.txt`: Includes Python version requirement
- `pyproject.toml`: Specifies required Python version
- `main.py`: Uses features from specific Python version

## Expected Scan Results

When running with incompatible Python version:

```
⚠ Python version mismatch detected

Current Python: 3.8.10
Required: >=3.9.0

Recommendation: Upgrade Python or use a compatible version
```

## Usage

```bash
# Scan to detect version issues
harmonizer

# Check Python version
python --version

# View detailed version information
harmonizer --verbose --check python
```

## What This Teaches

- How harmonizer detects Python version requirements
- Reading version specs from requirements.txt and pyproject.toml
- Importance of Python version compatibility
- Using python version managers (pyenv, conda)

## Resolution Strategies

1. **Upgrade Python**:
   ```bash
   # Using pyenv
   pyenv install 3.11
   pyenv local 3.11
   ```

2. **Use conda**:
   ```bash
   conda create -n myproject python=3.11
   conda activate myproject
   ```

3. **Modify requirements**:
   - Update version requirements if compatible with lower versions
   - Remove version-specific features from code

## Testing Different Versions

```bash
# Check current Python version
python --version

# Scan with harmonizer
harmonizer --check python

# Try with different Python interpreters
python3.9 -m harmonizer .
python3.11 -m harmonizer .
```
