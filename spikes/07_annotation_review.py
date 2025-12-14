#!/usr/bin/env python3
"""
Spike 07: Claude + Human Ground Truth Annotation Workflow

PURPOSE: Implement the hybrid annotation workflow where Claude proposes
         annotations and humans review/correct them.

WORKFLOW:
1. Claude analyzes PDF and proposes annotations (via agent)
2. This tool shows annotations needing review
3. Human confirms, corrects, or flags for expert
4. Corrections are saved back to annotation file
5. Summary statistics help track quality

RUN:
  # Step 1: Have Claude annotate a document (via Claude Code agent)
  # claude --agent ground-truth-annotator "Annotate spikes/sample_pdfs/kant.pdf"
  
  # Step 2: Review Claude's annotations
  uv run python spikes/07_annotation_review.py review annotations.yaml --pdf sample.pdf
  
  # Step 3: Validate final annotations
  uv run python spikes/07_annotation_review.py validate annotations.yaml
  
  # Step 4: Generate statistics
  uv run python spikes/07_annotation_review.py stats ground_truth/*.yaml

QUESTIONS ANSWERED:
1. How effective is Claude at initial annotation?
2. How much human review is actually needed?
3. What types of elements are hardest to annotate?
4. What's the time cost per document?
"""

import sys
import yaml
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Any
from collections import Counter
from datetime import datetime

try:
    import fitz
except ImportError:
    fitz = None
    print("Note: Install PyMuPDF for visual review: uv add pymupdf")


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class ReviewStats:
    """Statistics from a review session."""
    total_annotations: int = 0
    reviewed: int = 0
    confirmed: int = 0
    corrected: int = 0
    flagged_expert: int = 0
    skipped: int = 0
    by_type: dict = field(default_factory=dict)
    by_confidence: dict = field(default_factory=dict)
    time_minutes: float = 0


# ============================================================================
# Review Interface
# ============================================================================

def load_annotations(path: str) -> dict:
    """Load annotations from YAML file."""
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def save_annotations(annotations: dict, path: str):
    """Save annotations to YAML file."""
    with open(path, 'w') as f:
        yaml.dump(annotations, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def get_items_needing_review(annotations: dict) -> list[dict]:
    """Extract all annotation items that need human review."""
    items = []
    
    for page in annotations.get('pages', []):
        page_idx = page.get('index', 0)
        
        # Check page number
        pn = page.get('page_number', {})
        if pn and (pn.get('needs_review') or pn.get('confidence', 1) < 0.8):
            items.append({
                'type': 'page_number',
                'page_index': page_idx,
                'data': pn,
                'path': f"pages[{page_idx}].page_number"
            })
        
        # Check regions
        for i, region in enumerate(page.get('regions', [])):
            if region.get('needs_review') or region.get('confidence', 1) < 0.8:
                items.append({
                    'type': region.get('type', 'unknown'),
                    'page_index': page_idx,
                    'data': region,
                    'path': f"pages[{page_idx}].regions[{i}]"
                })
    
    return items


def get_random_sample(annotations: dict, n: int = 20) -> list[dict]:
    """Get random sample of high-confidence items for spot-checking."""
    import random
    
    items = []
    for page in annotations.get('pages', []):
        page_idx = page.get('index', 0)
        
        pn = page.get('page_number', {})
        if pn and pn.get('confidence', 0) >= 0.8 and not pn.get('needs_review'):
            items.append({
                'type': 'page_number',
                'page_index': page_idx,
                'data': pn,
                'path': f"pages[{page_idx}].page_number",
                'sample_type': 'spot_check'
            })
        
        for i, region in enumerate(page.get('regions', [])):
            if region.get('confidence', 0) >= 0.8 and not region.get('needs_review'):
                items.append({
                    'type': region.get('type', 'unknown'),
                    'page_index': page_idx,
                    'data': region,
                    'path': f"pages[{page_idx}].regions[{i}]",
                    'sample_type': 'spot_check'
                })
    
    return random.sample(items, min(n, len(items)))


def display_item_for_review(item: dict, pdf_doc=None):
    """Display an annotation item for human review."""
    print(f"\n{'='*60}")
    print(f"TYPE: {item['type'].upper()}")
    print(f"PAGE: {item['page_index']}")
    print(f"PATH: {item['path']}")
    if item.get('sample_type'):
        print(f"(Spot-check sample)")
    print(f"{'='*60}")
    
    data = item['data']
    
    # Show the annotation details
    print(f"\nConfidence: {data.get('confidence', 'N/A')}")
    
    if item['type'] == 'page_number':
        print(f"Value: {data.get('value')}")
        print(f"Format: {data.get('format')}")
        print(f"Position: {data.get('position')}")
    elif item['type'] in ('heading', 'title'):
        print(f"Level: {data.get('level', 'N/A')}")
        print(f"Text: {data.get('text', 'N/A')}")
    elif item['type'] in ('footnote_marker', 'footnote_content'):
        print(f"Marker: {data.get('marker', 'N/A')}")
        print(f"Links to: {data.get('links_to', data.get('id', 'N/A'))}")
        if data.get('text_preview'):
            print(f"Preview: {data.get('text_preview')[:100]}...")
    else:
        # Generic display
        for key, value in data.items():
            if key not in ('bbox', 'confidence', 'needs_review'):
                print(f"{key}: {value}")
    
    if data.get('bbox'):
        print(f"BBox: {data['bbox']}")
    
    if data.get('notes'):
        print(f"\nNotes from Claude: {data['notes']}")
    
    # If we have the PDF and PyMuPDF, show context
    if pdf_doc and data.get('bbox'):
        try:
            page = pdf_doc[item['page_index']]
            # Extract text from that region
            bbox = data['bbox']
            rect = fitz.Rect(
                bbox[0] * page.rect.width,
                bbox[1] * page.rect.height,
                bbox[2] * page.rect.width,
                bbox[3] * page.rect.height
            )
            text = page.get_text("text", clip=rect)
            print(f"\nExtracted text from region:\n{text[:200]}")
        except Exception as e:
            print(f"\n(Could not extract text: {e})")


def prompt_for_decision() -> tuple[str, Optional[dict]]:
    """Prompt user for review decision."""
    print("\nActions:")
    print("  [c] Confirm - annotation is correct")
    print("  [e] Edit - correct the annotation")
    print("  [f] Flag - needs expert review")
    print("  [s] Skip - review later")
    print("  [q] Quit - save and exit")
    
    while True:
        choice = input("\nDecision: ").strip().lower()
        
        if choice == 'c':
            return 'confirm', None
        elif choice == 'e':
            correction = prompt_for_correction()
            return 'correct', correction
        elif choice == 'f':
            reason = input("Reason for expert review: ").strip()
            return 'flag', {'expert_review_reason': reason}
        elif choice == 's':
            return 'skip', None
        elif choice == 'q':
            return 'quit', None
        else:
            print("Invalid choice. Use c/e/f/s/q")


def prompt_for_correction() -> dict:
    """Prompt user to provide corrections."""
    print("\nEnter corrections (press Enter to keep current value):")
    corrections = {}
    
    # Common fields to correct
    fields = [
        ('value', 'Value'),
        ('format', 'Format'),
        ('level', 'Level'),
        ('text', 'Text'),
        ('type', 'Type'),
    ]
    
    for field_name, display_name in fields:
        new_value = input(f"  {display_name}: ").strip()
        if new_value:
            # Try to parse as int if it looks like one
            if new_value.isdigit():
                new_value = int(new_value)
            corrections[field_name] = new_value
    
    notes = input("  Notes (optional): ").strip()
    if notes:
        corrections['correction_notes'] = notes
    
    return corrections


def apply_decision(annotations: dict, item: dict, decision: str, correction: Optional[dict]):
    """Apply a review decision to the annotations."""
    # Navigate to the item in the annotations structure
    path_parts = item['path'].replace(']', '').replace('[', '.').split('.')
    
    obj = annotations
    for part in path_parts[:-1]:
        if part.isdigit():
            obj = obj[int(part)]
        else:
            obj = obj[part]
    
    final_key = path_parts[-1]
    if final_key.isdigit():
        target = obj[int(final_key)]
    else:
        target = obj[final_key]
    
    # Apply the decision
    if decision == 'confirm':
        target['needs_review'] = False
        target['verified'] = True
        target['verified_at'] = datetime.now().isoformat()
    elif decision == 'correct':
        for key, value in correction.items():
            target[key] = value
        target['needs_review'] = False
        target['verified'] = True
        target['corrected'] = True
        target['verified_at'] = datetime.now().isoformat()
    elif decision == 'flag':
        target['needs_expert_review'] = True
        if correction:
            target['expert_review_reason'] = correction.get('expert_review_reason', '')


def review_annotations(annotations_path: str, pdf_path: Optional[str] = None):
    """Interactive review of annotations."""
    annotations = load_annotations(annotations_path)
    
    # Load PDF if available
    pdf_doc = None
    if pdf_path and fitz:
        pdf_doc = fitz.open(pdf_path)
    
    # Get items needing review
    review_items = get_items_needing_review(annotations)
    spot_check_items = get_random_sample(annotations, n=10)
    
    all_items = review_items + spot_check_items
    
    print(f"\n{'='*60}")
    print("ANNOTATION REVIEW SESSION")
    print(f"{'='*60}")
    print(f"Items needing review: {len(review_items)}")
    print(f"Spot-check samples: {len(spot_check_items)}")
    print(f"Total to review: {len(all_items)}")
    
    # Statistics
    stats = ReviewStats(total_annotations=len(all_items))
    start_time = datetime.now()
    
    # Review loop
    for i, item in enumerate(all_items):
        print(f"\n[{i+1}/{len(all_items)}]")
        display_item_for_review(item, pdf_doc)
        
        decision, correction = prompt_for_decision()
        
        if decision == 'quit':
            break
        
        stats.reviewed += 1
        
        if decision == 'confirm':
            stats.confirmed += 1
        elif decision == 'correct':
            stats.corrected += 1
        elif decision == 'flag':
            stats.flagged_expert += 1
        else:
            stats.skipped += 1
        
        # Track by type
        stats.by_type[item['type']] = stats.by_type.get(item['type'], 0) + 1
        
        # Apply decision
        if decision in ('confirm', 'correct', 'flag'):
            apply_decision(annotations, item, decision, correction)
    
    # Calculate time
    stats.time_minutes = (datetime.now() - start_time).total_seconds() / 60
    
    # Save updated annotations
    save_annotations(annotations, annotations_path)
    print(f"\nSaved to: {annotations_path}")
    
    # Print summary
    print(f"\n{'='*60}")
    print("REVIEW SESSION SUMMARY")
    print(f"{'='*60}")
    print(f"Reviewed: {stats.reviewed}/{stats.total_annotations}")
    print(f"Confirmed: {stats.confirmed}")
    print(f"Corrected: {stats.corrected}")
    print(f"Flagged for expert: {stats.flagged_expert}")
    print(f"Skipped: {stats.skipped}")
    print(f"Time: {stats.time_minutes:.1f} minutes")
    
    if stats.reviewed > 0:
        print(f"\nCorrection rate: {stats.corrected/stats.reviewed*100:.1f}%")
        print(f"(Lower is better - means Claude's annotations were accurate)")
    
    if pdf_doc:
        pdf_doc.close()


# ============================================================================
# Validation
# ============================================================================

def validate_annotations(annotations_path: str):
    """Validate annotation file for consistency and completeness."""
    annotations = load_annotations(annotations_path)
    
    print(f"\n{'='*60}")
    print(f"VALIDATING: {annotations_path}")
    print(f"{'='*60}\n")
    
    issues = []
    warnings = []
    
    # Check document metadata
    doc = annotations.get('document', {})
    if not doc.get('title'):
        warnings.append("Missing document title")
    if not doc.get('id'):
        warnings.append("Missing document ID")
    
    pages = annotations.get('pages', [])
    print(f"Pages annotated: {len(pages)}")
    
    # Check page number sequence
    page_numbers = []
    for page in pages:
        pn = page.get('page_number', {})
        if pn.get('value'):
            page_numbers.append((page['index'], pn['value'], pn.get('format')))
    
    print(f"Pages with numbers: {len(page_numbers)}")
    
    # Check for sequence breaks
    prev_arabic = None
    for idx, value, fmt in page_numbers:
        if fmt == 'arabic':
            try:
                num = int(value)
                if prev_arabic is not None:
                    if num != prev_arabic + 1 and num != 1:  # Allow reset to 1
                        warnings.append(f"Page number jump: {prev_arabic} → {num} at page index {idx}")
                prev_arabic = num
            except ValueError:
                issues.append(f"Invalid arabic number '{value}' at page index {idx}")
    
    # Check regions
    region_counts = Counter()
    needs_review_count = 0
    needs_expert_count = 0
    verified_count = 0
    
    for page in pages:
        for region in page.get('regions', []):
            region_counts[region.get('type', 'unknown')] += 1
            if region.get('needs_review'):
                needs_review_count += 1
            if region.get('needs_expert_review'):
                needs_expert_count += 1
            if region.get('verified'):
                verified_count += 1
    
    print(f"\nRegion counts by type:")
    for rtype, count in region_counts.most_common():
        print(f"  {rtype}: {count}")
    
    print(f"\nReview status:")
    print(f"  Verified: {verified_count}")
    print(f"  Needs review: {needs_review_count}")
    print(f"  Needs expert: {needs_expert_count}")
    
    # Check footnote linkage
    markers = []
    contents = []
    for page in pages:
        for region in page.get('regions', []):
            if region.get('type') == 'footnote_marker':
                markers.append(region.get('links_to'))
            if region.get('type') == 'footnote_content':
                contents.append(region.get('id'))
    
    unlinked_markers = set(markers) - set(contents) - {None}
    unlinked_contents = set(contents) - set(markers) - {None}
    
    if unlinked_markers:
        issues.append(f"Footnote markers without content: {unlinked_markers}")
    if unlinked_contents:
        warnings.append(f"Footnote content without markers: {unlinked_contents}")
    
    # Report
    print(f"\n{'='*60}")
    if issues:
        print("ISSUES (should fix):")
        for issue in issues:
            print(f"  ✗ {issue}")
    
    if warnings:
        print("\nWARNINGS (review):")
        for warning in warnings:
            print(f"  ⚠ {warning}")
    
    if not issues and not warnings:
        print("✓ No issues found")
    
    # Overall quality score
    total_regions = sum(region_counts.values())
    if total_regions > 0:
        quality_score = verified_count / total_regions * 100
        print(f"\nQuality score: {quality_score:.1f}% verified")


# ============================================================================
# Statistics
# ============================================================================

def corpus_statistics(paths: list[str]):
    """Generate statistics across multiple annotation files."""
    
    print(f"\n{'='*60}")
    print("CORPUS STATISTICS")
    print(f"{'='*60}\n")
    
    total_pages = 0
    total_regions = 0
    region_counts = Counter()
    confidence_sum = 0
    confidence_count = 0
    verified_count = 0
    corrected_count = 0
    
    doc_stats = []
    
    for path in paths:
        try:
            annotations = load_annotations(path)
            
            pages = annotations.get('pages', [])
            regions = sum(len(p.get('regions', [])) for p in pages)
            
            doc_verified = 0
            doc_corrected = 0
            
            for page in pages:
                for region in page.get('regions', []):
                    region_counts[region.get('type', 'unknown')] += 1
                    
                    conf = region.get('confidence')
                    if conf is not None:
                        confidence_sum += conf
                        confidence_count += 1
                    
                    if region.get('verified'):
                        verified_count += 1
                        doc_verified += 1
                    if region.get('corrected'):
                        corrected_count += 1
                        doc_corrected += 1
            
            total_pages += len(pages)
            total_regions += regions
            
            doc_stats.append({
                'path': path,
                'pages': len(pages),
                'regions': regions,
                'verified': doc_verified,
                'corrected': doc_corrected,
            })
            
        except Exception as e:
            print(f"Error loading {path}: {e}")
    
    print(f"Documents: {len(doc_stats)}")
    print(f"Total pages: {total_pages}")
    print(f"Total regions: {total_regions}")
    
    print(f"\nRegions by type:")
    for rtype, count in region_counts.most_common():
        print(f"  {rtype}: {count}")
    
    if confidence_count > 0:
        print(f"\nAverage confidence: {confidence_sum/confidence_count:.2f}")
    
    print(f"\nVerification status:")
    print(f"  Verified: {verified_count} ({verified_count/total_regions*100:.1f}%)")
    print(f"  Corrected: {corrected_count} ({corrected_count/total_regions*100:.1f}%)")
    
    if corrected_count > 0 and verified_count > 0:
        accuracy = (verified_count - corrected_count) / verified_count * 100
        print(f"\nClaude annotation accuracy: {accuracy:.1f}%")
        print("(% of verified items that didn't need correction)")
    
    print(f"\nPer-document breakdown:")
    print(f"{'Document':<40} {'Pages':>6} {'Regions':>8} {'Verified':>8} {'Corrected':>10}")
    print("-" * 80)
    for doc in doc_stats:
        name = Path(doc['path']).stem[:38]
        print(f"{name:<40} {doc['pages']:>6} {doc['regions']:>8} {doc['verified']:>8} {doc['corrected']:>10}")


# ============================================================================
# Main
# ============================================================================

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nCommands:")
        print("  review <annotations.yaml> [--pdf <file.pdf>]  - Interactive review")
        print("  validate <annotations.yaml>                   - Validate annotations")
        print("  stats <annotations1.yaml> [annotations2.yaml] - Corpus statistics")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'review':
        if len(sys.argv) < 3:
            print("Usage: review <annotations.yaml> [--pdf <file.pdf>]")
            sys.exit(1)
        
        annotations_path = sys.argv[2]
        pdf_path = None
        
        if '--pdf' in sys.argv:
            pdf_idx = sys.argv.index('--pdf')
            if pdf_idx + 1 < len(sys.argv):
                pdf_path = sys.argv[pdf_idx + 1]
        
        review_annotations(annotations_path, pdf_path)
        
    elif command == 'validate':
        if len(sys.argv) < 3:
            print("Usage: validate <annotations.yaml>")
            sys.exit(1)
        validate_annotations(sys.argv[2])
        
    elif command == 'stats':
        if len(sys.argv) < 3:
            print("Usage: stats <annotations1.yaml> [annotations2.yaml] ...")
            sys.exit(1)
        corpus_statistics(sys.argv[2:])
        
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
