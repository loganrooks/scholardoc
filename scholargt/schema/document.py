"""DocumentGT model for document-level ground truth.

Companion to PageGT: while PageGT captures per-page spatial annotations,
DocumentGT captures cross-page semantic elements, document metadata,
structural hierarchy (ToC, sections), and inter-element relationships
(footnote-content links, citation-bibliography links).

Together, PageGT + DocumentGT form the hybrid file scope where spatial data
lives per-page and semantic/structural data lives per-document.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from scholargt.schema.base import VerificationRecord
from scholargt.schema.formatting import FormattingAnnotation
from scholargt.schema.semantic import SemanticElement, ToCEntry
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


class FootnoteLink(BaseModel):
    """Link between a footnote marker and its content element."""

    marker_id: str = Field(description="Element ID of the marker location")
    content_id: str = Field(description="Element ID of the content element")
    link_type: Literal["footnote", "endnote"] = Field(
        default="footnote", description="Type of note link"
    )


class CitationBibLink(BaseModel):
    """Link between an in-text citation and its bibliography entry."""

    citation_id: str = Field(description="Element ID of the citation")
    bib_entry_id: str = Field(
        description="Element ID of the bibliography entry"
    )


class DocumentRelationships(BaseModel):
    """Cross-element relationships within a document.

    Links between footnote markers and content, citations and bibliography
    entries, and cross-reference element IDs.
    """

    footnote_links: list[FootnoteLink] = Field(
        default_factory=list,
        description="Footnote/endnote marker-to-content links",
    )
    citation_bib_links: list[CitationBibLink] = Field(
        default_factory=list,
        description="Citation-to-bibliography entry links",
    )
    cross_refs: list[str] = Field(
        default_factory=list,
        description="Cross-reference element IDs",
    )


# ---------- Main model ----------


class DocumentGT(BaseModel):
    """Document-level ground truth: the companion to page-level PageGT.

    Captures cross-page semantic elements, document metadata, structural
    hierarchy, and inter-element relationships. Forward-compatible via
    extra="allow".
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
    relationships: DocumentRelationships | None = Field(
        default=None,
        description="Inter-element relationships",
    )
    config_profile: str | None = Field(
        default=None,
        description="Configuration profile used for annotation",
    )
    verifications: list[VerificationRecord] = Field(
        default_factory=list,
        description="Document-level verification records",
    )
