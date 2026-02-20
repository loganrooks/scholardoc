"""Configuration models for ScholarGT annotation profiles.

GTProfile defines which spatial labels, semantic types, formatting types,
document section types, citation formats, reference systems, note placements,
and script variants are active for a given annotation project. ValidationConfig
controls what is required during GT validation.

Projects customize annotation scope via layered YAML configs:
base.yaml -> profile.yaml -> project.yaml
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from scholargt.schema.version import SCHEMA_VERSION


class ValidationConfig(BaseModel):
    """Validation requirements for a GT profile.

    Controls what is required when validating GT annotations.
    Different profiles have different requirements -- e.g., layout-annotation
    requires bbox but not text, while extraction-eval requires text.
    """

    require_reading_order: bool = False
    require_text: bool = False
    require_bbox: bool = True
    confidence_threshold: float = Field(default=0.8, ge=0.0, le=1.0)


class GTProfile(BaseModel):
    """Configuration profile defining active annotation types and validation.

    A GTProfile captures which labels from the universal superset are active
    for a specific use case. The three default profiles are:
    - extraction-eval: Text extraction quality evaluation
    - layout-annotation: Visual layout detection (IoU, mAP)
    - full-scholarly: Comprehensive scholarly annotation

    Profiles are loaded from layered YAML files via the config loader.

    v2.0.0: Added citation_formats, reference_systems, note_placements,
    script_variants categories. Renamed document_types to document_section_types.
    Updated defaults to use note_area/note (not footnote_area/footnote).
    """

    model_config = ConfigDict(extra="allow")

    name: str = "base"
    description: str = ""
    inherits: str | None = None
    schema_version: str = SCHEMA_VERSION

    spatial_labels: set[str] = Field(
        default_factory=lambda: {
            "text_block",
            "note_area",
            "page_header",
            "page_footer",
            "page_number",
            "section_header",
        }
    )
    semantic_types: set[str] = Field(
        default_factory=lambda: {"note", "citation"}
    )
    formatting_types: set[str] = Field(default_factory=set)
    document_section_types: set[str] = Field(default_factory=lambda: {"metadata"})
    citation_formats: set[str] = Field(default_factory=set)
    reference_systems: set[str] = Field(default_factory=set)
    note_placements: set[str] = Field(default_factory=set)
    script_variants: set[str] = Field(default_factory=set)

    validation: ValidationConfig = Field(default_factory=ValidationConfig)

    def is_label_enabled(self, category: str, label: str) -> bool:
        """Check if a specific label is active in this profile.

        Args:
            category: One of "spatial", "semantic", "formatting",
                "document_section", "citation_format", "reference_system",
                "note_placement", "script_variant".
            label: The label string to check (e.g., "text_block", "note").

        Returns:
            True if the label is in the corresponding category set.
        """
        category_map = {
            "spatial": self.spatial_labels,
            "semantic": self.semantic_types,
            "formatting": self.formatting_types,
            "document_section": self.document_section_types,
            "citation_format": self.citation_formats,
            "reference_system": self.reference_systems,
            "note_placement": self.note_placements,
            "script_variant": self.script_variants,
        }
        labels = category_map.get(category, set())
        return label in labels

    def enabled_labels(self) -> dict[str, set[str]]:
        """Return all enabled labels grouped by category.

        Returns:
            Dict mapping category names to sets of enabled label strings.
        """
        return {
            "spatial": set(self.spatial_labels),
            "semantic": set(self.semantic_types),
            "formatting": set(self.formatting_types),
            "document_section": set(self.document_section_types),
            "citation_format": set(self.citation_formats),
            "reference_system": set(self.reference_systems),
            "note_placement": set(self.note_placements),
            "script_variant": set(self.script_variants),
        }


class ProjectConfig(BaseModel):
    """Project-level configuration for customizing a GT profile.

    Projects can extend a default profile by adding custom label types
    and disabling labels not relevant to their corpus.

    Example project.yaml:
        profile: full-scholarly
        additional_semantic_types:
          - custom_philosophy_label
        disabled_labels:
          - formula
        validation:
          confidence_threshold: 0.85
    """

    profile: str = "base"
    additional_spatial_labels: set[str] = Field(default_factory=set)
    additional_semantic_types: set[str] = Field(default_factory=set)
    additional_formatting_types: set[str] = Field(default_factory=set)
    additional_document_section_types: set[str] = Field(default_factory=set)
    additional_citation_formats: set[str] = Field(default_factory=set)
    additional_reference_systems: set[str] = Field(default_factory=set)
    additional_note_placements: set[str] = Field(default_factory=set)
    additional_script_variants: set[str] = Field(default_factory=set)
    disabled_labels: set[str] = Field(default_factory=set)
    validation: ValidationConfig | None = None
