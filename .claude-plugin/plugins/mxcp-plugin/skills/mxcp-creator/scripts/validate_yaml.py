#!/usr/bin/env python3
"""
YAML Validation Script for MXCP Files

Validates YAML files against their corresponding JSON schemas.
Automatically detects the file type and applies the appropriate schema.

Usage:
    python validate_yaml.py <path-to-yaml-file>
    python validate_yaml.py --all  # Validate all YAML files in project templates
"""

import json
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

try:
    import yaml
    from jsonschema import Draft7Validator, RefResolver, ValidationError
except ImportError:
    print("Error: Required packages not installed.")
    print("Please install: pip install pyyaml jsonschema")
    sys.exit(1)


class YAMLValidator:
    """Validates MXCP YAML files against JSON schemas."""

    def __init__(self, schemas_dir: Path):
        self.schemas_dir = schemas_dir
        self.schemas = self._load_schemas()

    def _load_schemas(self) -> Dict[str, dict]:
        """Load all JSON schemas from the schemas directory."""
        schemas = {}
        for schema_file in self.schemas_dir.glob("*-schema-*.json"):
            with open(schema_file, "r") as f:
                schema_name = schema_file.stem
                schemas[schema_name] = json.load(f)
        return schemas

    def _detect_yaml_type(self, yaml_data: dict, file_path: Path) -> Optional[str]:
        """Detect the type of YAML file based on its content and filename."""
        filename = file_path.name.lower()

        # Check for mxcp-site.yml
        if filename == "mxcp-site.yml":
            return "mxcp-site-schema-1"

        # Check for config.yml
        if filename == "config.yml":
            return "mxcp-config-schema-1"

        # Check for mxcp version field (required in all MXCP files)
        if "mxcp" not in yaml_data:
            return None

        # Detect by top-level keys
        if "tool" in yaml_data:
            return "tool-schema-1"
        elif "resource" in yaml_data:
            return "resource-schema-1"
        elif "prompt" in yaml_data:
            return "prompt-schema-1"
        elif "suite" in yaml_data and "tests" in yaml_data:
            return "eval-schema-1"
        elif "project" in yaml_data:
            return "mxcp-site-schema-1"
        elif "projects" in yaml_data:
            return "mxcp-config-schema-1"

        return None

    def validate_file(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate a single YAML file.

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Load YAML file
            with open(file_path, "r") as f:
                yaml_data = yaml.safe_load(f)

            if yaml_data is None:
                return False, "Empty YAML file"

            # Detect YAML type
            schema_name = self._detect_yaml_type(yaml_data, file_path)
            if schema_name is None:
                return False, "Could not detect YAML file type (missing 'mxcp' field or unknown structure)"

            if schema_name not in self.schemas:
                return False, f"Schema '{schema_name}' not found in schemas directory"

            schema = self.schemas[schema_name]

            # Create resolver for $ref resolution
            schema_uri = f"file://{self.schemas_dir.resolve()}/"
            resolver = RefResolver(schema_uri, schema)

            # Validate
            validator = Draft7Validator(schema, resolver=resolver)
            errors = list(validator.iter_errors(yaml_data))

            if errors:
                error_messages = []
                for error in errors:
                    path = " -> ".join(str(p) for p in error.path) if error.path else "root"
                    error_messages.append(f"  At {path}: {error.message}")
                return False, "\n".join(error_messages)

            return True, None

        except yaml.YAMLError as e:
            return False, f"YAML parsing error: {e}"
        except Exception as e:
            return False, f"Unexpected error: {e}"

    def _should_skip_file(self, file_path: Path) -> bool:
        """Determine if a file should be skipped during validation."""
        # Skip files in virtual environments
        if ".venv" in file_path.parts or "venv" in file_path.parts:
            return True

        # Skip dbt-specific configuration files (not MXCP files)
        dbt_files = {"dbt_project.yml", "profiles.yml", "sample_profiles.yml", "packages.yml"}
        if file_path.name in dbt_files:
            return True

        # Skip dbt model schema files (sources.yml, schema.yml in models/)
        if file_path.name in {"sources.yml", "schema.yml"} and "models" in file_path.parts:
            return True

        # Skip seed schema files
        if file_path.name == "schema.yml" and "seeds" in file_path.parts:
            return True

        return False

    def validate_directory(self, directory: Path, pattern: str = "**/*.yml") -> Dict[str, Tuple[bool, Optional[str]]]:
        """
        Validate all YAML files in a directory.

        Returns:
            Dictionary mapping file paths to validation results
        """
        results = {}
        yaml_files = list(directory.glob(pattern))

        # Also check for .yaml extension
        yaml_files.extend(directory.glob(pattern.replace(".yml", ".yaml")))

        for yaml_file in yaml_files:
            if not self._should_skip_file(yaml_file):
                results[str(yaml_file)] = self.validate_file(yaml_file)

        return results


def main():
    # Determine base directory (assume script is in mxcp-creator/scripts/)
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent
    schemas_dir = base_dir / "assets" / "schemas"

    if not schemas_dir.exists():
        print(f"Error: Schemas directory not found at {schemas_dir}")
        sys.exit(1)

    validator = YAMLValidator(schemas_dir)

    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python validate_yaml.py <path-to-yaml-file>")
        print("       python validate_yaml.py --all")
        sys.exit(1)

    if sys.argv[1] == "--all":
        # Validate all YAML files in project templates
        templates_dir = base_dir / "assets" / "project-templates"
        if not templates_dir.exists():
            print(f"Error: Project templates directory not found at {templates_dir}")
            sys.exit(1)

        print(f"Validating all YAML files in {templates_dir}...")
        print("-" * 80)

        results = validator.validate_directory(templates_dir)

        # Print results
        valid_count = 0
        invalid_count = 0

        for file_path, (is_valid, error_msg) in results.items():
            rel_path = Path(file_path).relative_to(base_dir)
            if is_valid:
                print(f"✓ {rel_path}")
                valid_count += 1
            else:
                print(f"✗ {rel_path}")
                print(f"  Error: {error_msg}")
                print()
                invalid_count += 1

        print("-" * 80)
        print(f"Results: {valid_count} valid, {invalid_count} invalid")

        if invalid_count > 0:
            sys.exit(1)

    else:
        # Validate single file
        file_path = Path(sys.argv[1])
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            sys.exit(1)

        print(f"Validating {file_path}...")
        is_valid, error_msg = validator.validate_file(file_path)

        if is_valid:
            print("✓ Valid")
        else:
            print(f"✗ Invalid")
            print(f"Error: {error_msg}")
            sys.exit(1)


if __name__ == "__main__":
    main()
