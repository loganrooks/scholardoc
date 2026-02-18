"""Config loading with layered YAML merge for ScholarGT profiles.

Implements the layering strategy:
1. Load profiles/base.yaml (always)
2. If profile != "base", overlay profiles/{profile}.yaml
3. If project_config_path provided, apply ProjectConfig overrides:
   - Merge additional_* label sets into profile sets
   - Remove disabled_labels from all label sets
   - Override validation if provided

Manual YAML loading with PyYAML is used instead of pydantic-settings
YamlConfigSettingsSource because the custom merge logic (additionals,
disabled_labels) goes beyond simple source layering.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from scholargt.config.models import GTProfile, ProjectConfig

PROFILES_DIR = Path(__file__).parent / "profiles"


def get_profiles_dir() -> Path:
    """Return path to the built-in profiles directory."""
    return PROFILES_DIR


def list_profiles() -> list[str]:
    """List available profile names by scanning the profiles directory.

    Returns:
        Sorted list of profile names (without .yaml extension).
    """
    if not PROFILES_DIR.is_dir():
        return []
    return sorted(
        p.stem for p in PROFILES_DIR.glob("*.yaml") if p.is_file()
    )


def load_profile(
    profile_name: str = "base",
    project_config_path: Path | None = None,
) -> GTProfile:
    """Load a GT profile with layered YAML merging.

    Args:
        profile_name: Name of the built-in profile to load.
            One of: "base", "extraction-eval", "layout-annotation", "full-scholarly".
        project_config_path: Optional path to a project-level YAML config
            that adds/removes labels and overrides validation.

    Returns:
        A fully merged GTProfile instance.

    Raises:
        FileNotFoundError: If the named profile YAML file does not exist.
    """
    # Step 1: Load base.yaml
    base_path = PROFILES_DIR / "base.yaml"
    if not base_path.exists():
        msg = f"Base profile not found: {base_path}"
        raise FileNotFoundError(msg)

    with open(base_path) as f:
        config: dict = yaml.safe_load(f) or {}

    # Step 2: Layer named profile on top of base
    if profile_name != "base":
        profile_path = PROFILES_DIR / f"{profile_name}.yaml"
        if not profile_path.exists():
            msg = f"Profile not found: {profile_path}"
            raise FileNotFoundError(msg)

        with open(profile_path) as f:
            profile_data: dict = yaml.safe_load(f) or {}

        # Handle nested validation dict merge
        if "validation" in profile_data and "validation" in config:
            merged_validation = {**config["validation"], **profile_data["validation"]}
            config.update(profile_data)
            config["validation"] = merged_validation
        else:
            config.update(profile_data)

    # Step 3: Apply project-level overrides
    if project_config_path is not None:
        if not project_config_path.exists():
            msg = f"Project config not found: {project_config_path}"
            raise FileNotFoundError(msg)

        with open(project_config_path) as f:
            project_raw: dict = yaml.safe_load(f) or {}

        project_config = ProjectConfig.model_validate(project_raw)

        # Merge additional labels into profile sets
        _label_set_keys = {
            "additional_spatial_labels": "spatial_labels",
            "additional_semantic_types": "semantic_types",
            "additional_formatting_types": "formatting_types",
            "additional_document_types": "document_types",
        }
        for additional_key, target_key in _label_set_keys.items():
            additional = getattr(project_config, additional_key)
            if additional:
                existing = set(config.get(target_key, []))
                existing.update(additional)
                config[target_key] = list(existing)

        # Remove disabled labels from all label sets
        if project_config.disabled_labels:
            for label_key in [
                "spatial_labels",
                "semantic_types",
                "formatting_types",
                "document_types",
            ]:
                if label_key in config:
                    config[label_key] = [
                        lbl
                        for lbl in config[label_key]
                        if lbl not in project_config.disabled_labels
                    ]

        # Override validation if provided
        if project_config.validation is not None:
            existing_validation = config.get("validation", {})
            if isinstance(existing_validation, dict):
                existing_validation.update(
                    project_config.validation.model_dump(exclude_unset=True)
                )
                config["validation"] = existing_validation
            else:
                config["validation"] = project_config.validation.model_dump()

    # Step 4: Validate and return
    return GTProfile.model_validate(config)
