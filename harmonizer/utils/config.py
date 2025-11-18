"""
Configuration Management Module.

This module provides functionality for loading and saving JSON configuration files
used by Environment Harmonizer.

EDUCATIONAL NOTE - Why JSON for Configuration?
JSON (JavaScript Object Notation) is chosen for configuration because:
- Human-readable and easy to edit
- Built-in Python support (json module in standard library)
- Language-agnostic (can be used by other tools)
- Strict syntax helps catch errors
- No code execution risk (unlike YAML or Python files)

Alternative formats considered:
- YAML: More readable but requires external library
- TOML: Modern but requires external library (tomli) before Python 3.11
- INI: Limited data types
- Python files: Security risk (code execution)
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


DEFAULT_CONFIG_FILENAME = ".harmonizer.json"


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.

    Args:
        config_path: Path to configuration file. If None, looks for default
                    config file in current directory.

    Returns:
        Dictionary containing configuration values

    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file contains invalid JSON
        PermissionError: If config file can't be read

    EDUCATIONAL NOTE - Default Parameters:
    Using Optional[str] = None allows the function to work with or without
    a specified path. This is a common pattern for optional configuration.

    Example:
        >>> config = load_config()  # Uses default location
        >>> config = load_config("/path/to/config.json")  # Custom location

    EDUCATIONAL NOTE - JSON Parsing:
    json.load() vs json.loads():
    - json.load(file_object): Reads from file object
    - json.loads(string): Parses JSON string

    We use json.load() here for efficiency (doesn't load entire file to string).
    """

    if config_path is None:
        config_path = DEFAULT_CONFIG_FILENAME

    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
            return config
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in configuration file {config_path}: {e.msg}",
            e.doc,
            e.pos,
        )


def save_config(config: Dict[str, Any], config_path: Optional[str] = None) -> None:
    """
    Save configuration to a JSON file.

    Args:
        config: Configuration dictionary to save
        config_path: Path to configuration file. If None, uses default location.

    Raises:
        PermissionError: If config file can't be written
        TypeError: If config contains non-JSON-serializable objects

    EDUCATIONAL NOTE - JSON Serialization:
    Not all Python objects can be serialized to JSON:
    - Serializable: dict, list, str, int, float, bool, None
    - Not serializable: custom objects, datetime, Path, sets, tuples (converted to lists)

    The indent parameter makes the JSON human-readable with proper formatting.
    Without it, everything would be on one line.

    Example:
        >>> config = {"check_python": True, "min_version": "3.8"}
        >>> save_config(config, "my_config.json")
    """

    if config_path is None:
        config_path = DEFAULT_CONFIG_FILENAME

    config_file = Path(config_path)

    # Create parent directories if they don't exist
    config_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(
                config,
                f,
                indent=2,  # 2-space indentation for readability
                sort_keys=True,  # Sort keys alphabetically
                ensure_ascii=False,  # Allow Unicode characters
            )
    except TypeError as e:
        raise TypeError(f"Configuration contains non-JSON-serializable object: {e}")


def load_config_or_default(
    config_path: Optional[str] = None, default_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Load configuration file, or return default if file doesn't exist.

    This is a convenience function that handles the common case of wanting
    to use a config file if it exists, but fall back to defaults if it doesn't.

    Args:
        config_path: Path to configuration file
        default_config: Default configuration to use if file doesn't exist

    Returns:
        Configuration dictionary (from file or defaults)

    EDUCATIONAL NOTE - Error Handling Patterns:
    This function demonstrates a common pattern:
    1. Try to load configuration from file
    2. If file doesn't exist, return defaults
    3. If file exists but is invalid, raise error (don't silently use defaults)

    This ensures users know when their config file is broken.

    Example:
        >>> defaults = {"verbose": False, "check_all": True}
        >>> config = load_config_or_default(default_config=defaults)
        >>> # Will use file if it exists, otherwise defaults
    """

    if default_config is None:
        default_config = get_default_config()

    try:
        return load_config(config_path)
    except FileNotFoundError:
        # File doesn't exist, use defaults
        return default_config
    except (json.JSONDecodeError, PermissionError):
        # File exists but is invalid or can't be read
        # Re-raise these errors - user needs to know
        raise


def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration values.

    Returns:
        Dictionary containing default configuration

    EDUCATIONAL NOTE - Configuration Defaults:
    Centralizing defaults in one function:
    - Makes it easy to see all default values
    - Ensures consistency across the application
    - Simplifies testing (can mock this function)
    - Documents expected configuration structure

    Example:
        >>> defaults = get_default_config()
        >>> print(defaults["verbose"])
        False
    """

    return {
        # Scanning options
        "scan_os": True,
        "scan_python": True,
        "scan_venv": True,
        "scan_dependencies": True,
        "scan_config_files": True,
        # Output options
        "verbose": False,
        "json_output": False,
        "color_output": True,
        # Fix options
        "auto_fix": False,
        "dry_run": False,
        "confirm_fixes": True,
        # Advanced options
        "timeout": 5,  # Timeout for subprocess commands in seconds
        "follow_symlinks": False,
        "max_depth": 3,  # Maximum directory depth for scanning
    }


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration structure and values.

    Args:
        config: Configuration dictionary to validate

    Returns:
        True if valid, raises ValueError if invalid

    Raises:
        ValueError: If configuration is invalid

    EDUCATIONAL NOTE - Configuration Validation:
    Validating configuration early prevents confusing errors later.
    Check for:
    1. Required keys are present
    2. Values are correct types
    3. Values are in valid ranges
    4. Dependencies between options are satisfied

    Example:
        >>> config = {"verbose": "yes"}  # Should be bool
        >>> validate_config(config)
        ValueError: verbose must be boolean, got str
    """

    defaults = get_default_config()

    # Check each known config key
    for key, default_value in defaults.items():
        if key in config:
            value = config[key]
            expected_type = type(default_value)

            # Type checking
            if not isinstance(value, expected_type):
                raise ValueError(
                    f"Configuration key '{key}' must be {expected_type.__name__}, "
                    f"got {type(value).__name__}"
                )

    # Specific value range checks
    if "timeout" in config:
        if config["timeout"] <= 0:
            raise ValueError("timeout must be positive")

    if "max_depth" in config:
        if config["max_depth"] < 0:
            raise ValueError("max_depth must be non-negative")

    # Logical dependency checks
    if config.get("auto_fix") and config.get("dry_run"):
        raise ValueError("Cannot use both auto_fix and dry_run together")

    return True


def merge_configs(
    base_config: Dict[str, Any], override_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge two configuration dictionaries.

    Values in override_config take precedence over base_config.

    Args:
        base_config: Base configuration dictionary
        override_config: Configuration values to override

    Returns:
        Merged configuration dictionary

    EDUCATIONAL NOTE - Dictionary Merging:
    Python 3.9+ supports | operator for dictionary merging:
        merged = base | override

    For Python 3.5-3.8, we use:
        merged = {**base, **override}

    Both create a new dictionary (don't modify originals).

    Example:
        >>> base = {"a": 1, "b": 2}
        >>> override = {"b": 3, "c": 4}
        >>> merged = merge_configs(base, override)
        >>> print(merged)
        {"a": 1, "b": 3, "c": 4}
    """

    # Create a copy of base config
    merged = base_config.copy()

    # Update with override values
    merged.update(override_config)

    return merged


def create_default_config_file(config_path: Optional[str] = None) -> None:
    """
    Create a default configuration file.

    Args:
        config_path: Path where to create config file. If None, uses default.

    EDUCATIONAL NOTE - Configuration File Creation:
    This is useful for:
    - First-time setup
    - Resetting to defaults
    - Generating example configuration
    - CLI --init-config command

    Example:
        >>> create_default_config_file()
        # Creates .harmonizer.json with default values
    """

    if config_path is None:
        config_path = DEFAULT_CONFIG_FILENAME

    config = get_default_config()
    save_config(config, config_path)

    print(f"Created default configuration file: {config_path}")


# Example usage and testing
if __name__ == "__main__":
    """
    Test the configuration module.
    """

    print("=" * 60)
    print("Configuration Module - Test Run")
    print("=" * 60)

    # Get default configuration
    print("\nDefault Configuration:")
    print("-" * 60)
    default_config = get_default_config()
    print(json.dumps(default_config, indent=2))

    # Test validation
    print("\nTesting Configuration Validation:")
    print("-" * 60)

    try:
        validate_config(default_config)
        print("✓ Default configuration is valid")
    except ValueError as e:
        print(f"✗ Validation error: {e}")

    # Test invalid config
    print("\nTesting Invalid Configuration:")
    print("-" * 60)
    invalid_config = {"verbose": "yes"}  # Should be bool
    try:
        validate_config(invalid_config)
        print("✗ Validation should have failed!")
    except ValueError as e:
        print(f"✓ Caught validation error (expected): {e}")

    # Test config merging
    print("\nTesting Configuration Merging:")
    print("-" * 60)
    base = {"a": 1, "b": 2, "c": 3}
    override = {"b": 20, "d": 40}
    merged = merge_configs(base, override)
    print(f"Base: {base}")
    print(f"Override: {override}")
    print(f"Merged: {merged}")

    print("\n" + "=" * 60)
