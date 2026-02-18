"""Configuration system for ScholarGT annotation profiles.

Provides layered YAML config loading with three default profiles:
- extraction-eval: Text extraction quality evaluation
- layout-annotation: Visual layout detection
- full-scholarly: Comprehensive scholarly annotation

Usage:
    from scholargt.config import GTProfile, load_profile

    profile = load_profile("extraction-eval")
    if profile.is_label_enabled("spatial", "text_block"):
        ...
"""

from scholargt.config.loader import get_profiles_dir, list_profiles, load_profile
from scholargt.config.models import GTProfile, ProjectConfig, ValidationConfig

__all__ = [
    "GTProfile",
    "ProjectConfig",
    "ValidationConfig",
    "get_profiles_dir",
    "list_profiles",
    "load_profile",
]
