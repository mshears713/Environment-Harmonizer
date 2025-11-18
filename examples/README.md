# Environment Harmonizer Examples

This directory contains sample projects demonstrating various environment states and how Environment Harmonizer detects and reports them.

## Example Projects

### 1. healthy-project
A well-configured project with:
- Active virtual environment
- All dependencies installed
- Proper configuration files
- Python version matches requirements

**Expected Result**: No errors, all checks pass

```bash
cd healthy-project
harmonizer
```

### 2. missing-deps
A project with missing Python dependencies:
- Virtual environment exists
- requirements.txt present
- Some dependencies not installed

**Expected Result**: Dependency errors reported, fix available

```bash
cd missing-deps
harmonizer
harmonizer --fix --dry-run  # Preview fixes
```

### 3. no-venv
A project without a virtual environment:
- No venv directory
- Dependencies listed in requirements.txt
- Configuration files present

**Expected Result**: Virtual environment warning, recommendation to create one

```bash
cd no-venv
harmonizer
harmonizer --fix --dry-run  # Preview venv creation
```

### 4. version-mismatch
A project with Python version requirements not matching current interpreter:
- Specifies Python 3.9+ in requirements
- May be running on different version
- Virtual environment present

**Expected Result**: Python version mismatch warning

```bash
cd version-mismatch
harmonizer
```

## Running All Examples

To test all examples sequentially:

```bash
# From the examples directory
for dir in healthy-project missing-deps no-venv version-mismatch; do
    echo "=== Testing $dir ==="
    cd $dir
    harmonizer
    echo ""
    cd ..
done
```

## Example Reports

Each example directory contains:
- **README.md**: Description of the environment state
- **expected-report.txt**: Sample output from harmonizer
- **expected-report.json**: Sample JSON output
- Project files (requirements.txt, etc.)

## Using Examples for Testing

These examples are useful for:
- Understanding how harmonizer detects different issues
- Testing fixes with `--fix --dry-run`
- Learning how to interpret diagnostic reports
- Integration testing during development

## Creating Your Own Examples

To create a new example:

1. Create a directory under `examples/`
2. Add project files (requirements.txt, etc.)
3. Add a README.md explaining the scenario
4. Run harmonizer to generate expected output
5. Document the expected behavior

Example:
```bash
mkdir examples/my-example
cd examples/my-example
# Create project files...
harmonizer --output expected-report.txt
harmonizer --json --output expected-report.json
```
