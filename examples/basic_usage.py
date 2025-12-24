#!/usr/bin/env python3
"""
Basic ScholarDoc Usage Example

This example demonstrates the core workflow:
1. Convert a PDF to ScholarDocument
2. Query the document structure
3. Generate RAG chunks with metadata
4. Export to different formats
5. Save and load documents
"""

from pathlib import Path

from scholardoc import convert
from scholardoc.config import ConversionConfig
from scholardoc.models import ChunkStrategy


def main():
    # ─────────────────────────────────────────────────────────────────────────
    # 1. Basic Conversion
    # ─────────────────────────────────────────────────────────────────────────

    # Convert a PDF with default settings
    doc = convert("path/to/document.pdf")

    print(f"Converted: {doc.metadata.title}")
    print(f"  Pages: {len(doc.pages)}")
    print(f"  Sections: {len(doc.sections)}")
    print(f"  Text length: {len(doc.text):,} characters")

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Custom Configuration
    # ─────────────────────────────────────────────────────────────────────────

    config = ConversionConfig(
        extract_structure=True,  # Enable section detection
        normalize_whitespace=True,  # Clean up spacing
        rejoin_hyphenated=True,  # Fix line-break hyphenation
        detect_ocr_errors=True,  # Flag potential OCR errors
    )

    doc = convert("path/to/document.pdf", config=config)

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Query Document Structure
    # ─────────────────────────────────────────────────────────────────────────

    # Find which page contains a position
    page = doc.page_for_position(5000)
    if page:
        print(f"Position 5000 is on page {page.label}")

    # Get section at a position
    section = doc.section_for_position(5000)
    if section:
        print(f"  In section: {section.title}")

    # Get text range with context
    text_slice = doc.text_range(5000, 5500)
    print(f"  Text: {text_slice[:100]}...")

    # Find footnotes in a range
    footnotes = doc.footnotes_in_range(0, 10000)
    for ref, note in footnotes:
        print(f"  Footnote {ref.marker} at position {ref.position}: {note.text[:50]}...")

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Generate RAG Chunks
    # ─────────────────────────────────────────────────────────────────────────

    # Semantic chunking (respects paragraph boundaries)
    for chunk in doc.to_rag_chunks(strategy=ChunkStrategy.SEMANTIC, max_tokens=512):
        print(f"Chunk {chunk.chunk_index}: {chunk.citation}")
        print(f"  Pages: {chunk.page_labels}")
        print(f"  Section: {chunk.section}")
        print(f"  Text: {chunk.text[:100]}...")
        print(f"  Footnotes in chunk: {len(chunk.footnote_refs)}")

        # Each chunk has everything needed for RAG + citation
        # - chunk.text: clean text for embedding
        # - chunk.citation: "Author, Title, p. 64-65"
        # - chunk.page_labels, chunk.section: for filtering
        break  # Just show first chunk

    # Other chunking strategies
    # - ChunkStrategy.PAGE: one chunk per page
    # - ChunkStrategy.SECTION: one chunk per section
    # - ChunkStrategy.FIXED_SIZE: fixed token count with overlap

    # ─────────────────────────────────────────────────────────────────────────
    # 5. Export to Formats
    # ─────────────────────────────────────────────────────────────────────────

    # Plain text (ready for embedding)
    plain = doc.to_plain_text()  # noqa: F841

    # Markdown with footnotes
    markdown = doc.to_markdown(include_footnotes=True)  # noqa: F841

    # Markdown with page markers
    markdown_pages = doc.to_markdown(  # noqa: F841
        include_footnotes=True,
        include_page_markers=True,
        page_marker_style="comment",  # <!-- p. 64 -->
    )

    # ─────────────────────────────────────────────────────────────────────────
    # 6. Persistence
    # ─────────────────────────────────────────────────────────────────────────

    # Save to JSON format (human-readable, good for small docs)
    doc.save("output/document.scholardoc")

    # Save to SQLite format (better for large docs, random access)
    doc.save_sqlite("output/document.scholardb")

    # Load back
    from scholardoc.models import ScholarDocument

    loaded_json = ScholarDocument.load("output/document.scholardoc")
    loaded_sqlite = ScholarDocument.load_sqlite("output/document.scholardb")

    print(f"Loaded {len(loaded_json.text):,} characters from JSON")
    print(f"Loaded {len(loaded_sqlite.text):,} characters from SQLite")


def batch_conversion_example():
    """Convert multiple documents at once."""
    from scholardoc import convert_batch

    pdf_dir = Path("pdfs/")
    pdfs = list(pdf_dir.glob("*.pdf"))

    # Convert all PDFs, continuing on errors
    results = convert_batch(pdfs, on_error="skip")

    for path, doc in results.items():
        if doc is not None:
            print(f"{path.name}: {len(doc.pages)} pages")
            doc.save(f"output/{path.stem}.scholardoc")
        else:
            print(f"{path.name}: FAILED")


def rag_pipeline_example():
    """Example: Building a RAG index from multiple documents."""
    from scholardoc import convert
    from scholardoc.models import ChunkStrategy

    # This would integrate with your vector DB
    # (chromadb, pinecone, qdrant, etc.)

    documents = ["book1.pdf", "book2.pdf", "book3.pdf"]

    all_chunks = []
    for doc_path in documents:
        doc = convert(doc_path)

        for chunk in doc.to_rag_chunks(
            strategy=ChunkStrategy.SEMANTIC,
            max_tokens=512,
            overlap=50,
        ):
            # Metadata for filtering and citation
            metadata = {
                "doc_title": chunk.doc_title,
                "doc_author": chunk.doc_author,
                "pages": chunk.page_labels,
                "section": chunk.section,
                "citation": chunk.citation,
                "source_path": chunk.source_path,
            }

            all_chunks.append(
                {
                    "id": f"{doc_path}_{chunk.chunk_id}",
                    "text": chunk.text,
                    "metadata": metadata,
                }
            )

    print(f"Generated {len(all_chunks)} chunks for RAG index")

    # Now you would:
    # 1. Embed each chunk.text
    # 2. Store in vector DB with metadata
    # 3. Query returns chunks with citation info


if __name__ == "__main__":
    # Note: These examples use placeholder paths.
    # Replace with actual PDF paths to run.
    print("ScholarDoc Usage Examples")
    print("=" * 50)
    print("\nSee the code for detailed examples of:")
    print("  - Basic conversion")
    print("  - Custom configuration")
    print("  - Document queries")
    print("  - RAG chunk generation")
    print("  - Export formats")
    print("  - Persistence (JSON/SQLite)")
    print("  - Batch processing")
    print("  - RAG pipeline integration")
