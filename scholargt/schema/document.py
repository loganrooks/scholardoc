"""DocumentGT model for document-level ground truth.

Companion to PageGT: while PageGT captures per-page spatial annotations,
DocumentGT captures cross-page semantic elements, document metadata,
structural hierarchy (ToC, sections), layout registers (SFP-1), note
schemas, and citation style.

Together, PageGT + DocumentGT form the hybrid file scope where spatial data
lives per-page and semantic/structural data lives per-document.

v2.0.0 changes from v1.0.0:
- LayoutRegister added (SFP-1): named reading streams / column identities
- note_schemas added: document-level note numbering conventions
- citation_style added: document-level citation convention
- DocumentRelationships, FootnoteLink, CitationBibLink REMOVED
  (relationships now embedded in elements: Note.body_marker, Citation.bib_entry_id,
  CrossReference.target_section_id)
"""

from __future__ import annotations

import warnings
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from scholargt.schema.base import VerificationRecord
from scholargt.schema.formatting import FormattingAnnotation
from scholargt.schema.labels import CitationStyle
from scholargt.schema.semantic import NoteSchema, SemanticElement, ToCEntry
from scholargt.schema.version import SCHEMA_VERSION

# ---------- Supporting models ----------


class DocumentSource(BaseModel):
    """Document source metadata and bibliographic information."""

    pdf: str = Field(description="PDF filename or path")
    title: str | None = Field(default=None, description="Document title")
    author: str | None = Field(default=None, description="Primary author")
    translator: str | None = Field(
        default=None, description="Translator (if translated work)"
    )
    year: int | None = Field(default=None, description="Publication year")
    publisher: str | None = Field(default=None, description="Publisher name")
    isbn: str | None = Field(default=None, description="ISBN identifier")
    doi: str | None = Field(default=None, description="DOI identifier")
    document_type: (
        Literal["book", "article", "essay", "report", "translation", "other"]
        | None
    ) = Field(default=None, description="Document classification")


class DocumentStructure(BaseModel):
    """Document structural hierarchy: table of contents and section organization."""

    toc: list[ToCEntry] = Field(
        default_factory=list, description="Table of contents entries"
    )
    sections: list[str] = Field(
        default_factory=list,
        description="Section element IDs (referencing Section elements)",
    )
    front_matter: dict[str, Any] | None = Field(
        default=None, description="Front matter metadata (preface, dedication, etc.)"
    )
    back_matter: dict[str, Any] | None = Field(
        default=None,
        description="Back matter metadata (index, appendices, etc.)",
    )


class LayoutRegister(BaseModel):
    """A named reading stream or column in a multi-register document.

    Provides first-class identity for parallel text streams, commentary layers,
    bilingual columns, and multi-register layouts. Each register describes a
    distinct reading stream with its own author, language, text direction,
    and typographic conventions.

    Examples:
    - Talmud page: registers for Mishnah text, Gemara, Rashi commentary, Tosafot
    - Bilingual edition: registers for original language and translation
    - Critical edition: registers for main text, apparatus criticus, editor notes
    - Multi-column layout: registers for left_column, right_column
    """

    register_id: str = Field(
        description="Unique register identifier (e.g., 'hegel', 'genet', 'rashi')"
    )
    name: str = Field(description="Human-readable register name")
    author: str | None = Field(
        default=None, description="Author or attributed source"
    )
    language: str | None = Field(
        default=None, description="Primary BCP 47 language tag (e.g., 'he', 'de', 'ar')"
    )
    text_direction: Literal["ltr", "rtl"] | None = Field(
        default=None, description="Base text direction for this register"
    )
    position_convention: str | None = Field(
        default=None,
        description="Layout convention (e.g., 'left_column', 'upper_register')",
    )
    typeface_convention: str | None = Field(
        default=None,
        description="Expected typeface family (e.g., 'rashi_script', 'square_hebrew', 'serif_9pt')",
    )


# ---------- Main model ----------


class DocumentGT(BaseModel):
    """Document-level ground truth: the companion to page-level PageGT.

    Captures cross-page semantic elements, document metadata, structural
    hierarchy, layout registers (SFP-1), note schemas, and citation style.
    Forward-compatible via extra="allow".

    v2.0.0: DocumentRelationships, FootnoteLink, CitationBibLink removed.
    Relationships are now embedded in elements (Note.body_marker,
    Citation.bib_entry_id, CrossReference.target_section_id).
    """

    model_config = ConfigDict(extra="allow")

    schema_version: str = Field(
        default=SCHEMA_VERSION,
        description="Schema version for migration support",
    )
    document_id: str = Field(description="Unique document identifier")
    source: DocumentSource = Field(
        description="Document source metadata and bibliographic info"
    )
    page_range: tuple[int, int] | None = Field(
        default=None,
        description="(first_page, last_page) 0-based page indices",
    )
    elements: list[SemanticElement] = Field(
        default_factory=list,
        description="Cross-page semantic elements (discriminated union)",
    )
    formatting: list[FormattingAnnotation] = Field(
        default_factory=list,
        description="Text formatting annotations",
    )
    structure: DocumentStructure | None = Field(
        default=None, description="Document structure (ToC, sections)"
    )
    note_schemas: list[NoteSchema] = Field(
        default_factory=list,
        description="Document-level note numbering conventions",
    )
    citation_style: CitationStyle | None = Field(
        default=None, description="Document-level citation convention"
    )
    registers: list[LayoutRegister] = Field(
        default_factory=list,
        description="SFP-1: named reading streams / column identities",
    )
    config_profile: str | None = Field(
        default=None,
        description="Configuration profile used for annotation",
    )
    verifications: list[VerificationRecord] = Field(
        default_factory=list,
        description="Document-level verification records",
    )

    @model_validator(mode="after")
    def _validate_note_schema_uniqueness(self) -> DocumentGT:
        """Warn if note_schemas contain duplicate schema_id values.

        Uses warning rather than error because annotation may be in progress.
        """
        if self.note_schemas:
            ids = [ns.schema_id for ns in self.note_schemas]
            seen: set[str] = set()
            duplicates: list[str] = []
            for sid in ids:
                if sid in seen:
                    duplicates.append(sid)
                seen.add(sid)
            if duplicates:
                warnings.warn(
                    f"note_schemas contains duplicate schema_id values: {duplicates}",
                    UserWarning,
                    stacklevel=2,
                )
        return self
